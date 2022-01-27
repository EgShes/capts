import pickle
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from struct import unpack
from typing import Any, List, MutableMapping, Optional, Tuple, Union

from redis import Redis


class NotExisted(Exception):
    pass


def chunk_bytes(binary: bytes, chunksize: int) -> Tuple[bytes]:
    len_binary = len(binary)

    if len_binary <= chunksize:
        format_chunks = [str(len_binary)]
    else:
        format_chunks = [str(chunksize)] * (len_binary // chunksize)
        remainder = len_binary % chunksize
        if remainder:
            format_chunks.append(str(remainder))

    format_chunks = [elem + "s" for elem in format_chunks]
    format_chunks = ">" + "".join(format_chunks)

    splitted = unpack(format_chunks, binary)

    return splitted


def join_chunks(chunks: Union[Tuple[bytes, ...], List[bytes]]) -> bytes:
    return b"".join(chunks)


class Storage(MutableMapping, ABC):
    """Интерфейс для внешнего храненилища данных в вычислительном графе.

    Для передачи данных в вычислительном графе между узлами следует использовать одну из реализаций этого класса.
    Реализует интерфейс питоновского словаря.
    Сериалазция/десереализация -- по дефолту pickle.

    !! ВАЖНО !!
    Хранилище представляет интерфейс словаря, но по способу хранения объектов не является словарем.
    Для сохранения/записи значений в хранилище следует использовать явно операцию присваивания.

    >>> storage[some_list_key].append(1)  # не сохранит в хранилище расширенный cписок
    >>> storage[some_list_key] += [1]     # сохранит
    """

    def __init__(self, namespace: str):
        self.namespace = None
        self.set_namespace(namespace)

    default_serialize = pickle.dumps
    default_deserialize = pickle.loads

    def __setitem__(self, key: str, value: Any):
        if not isinstance(key, str):
            raise TypeError(f"Only `str` available for `key`. Got {type(key)}")
        bytes_value = self.default_serialize(value)
        return self._write_bytes(bytes_value, key)

    def __getitem__(self, key: str):
        if not isinstance(key, str):
            raise TypeError(f"Only `str` available for `key`. Got {type(key)}")
        bytes_value = self._read_bytes(key)
        return self.default_deserialize(bytes_value)

    def get_data_from_kaluga(self, *args, **kwargs) -> Any:
        """ "Специальный метод для чтения из хранилища вне рабочего кластера.
        Используется для чтения входящих запросов на обработку.
        """
        raise NotImplementedError

    def send_data_to_kaluga(self, *args, **kwargs) -> Any:
        """ "Специальный метод для записи в хранилище вне рабочего кластера.
        Используется для ответа на входящие запросы на обработку."""
        raise NotImplementedError

    def __str__(self):
        return f"{self.__class__.__name__}(namespace='{str(self.namespace)}', {str(dict(self.items()))})"

    @abstractmethod
    def __delitem__(self, key: str):
        ...

    @abstractmethod
    def __len__(self):
        ...

    @abstractmethod
    def __iter__(self):
        ...

    @abstractmethod
    def set_namespace(self, namespace: str):
        ...

    @abstractmethod
    def _write_bytes(self, obj: bytes, key: Optional[str] = None) -> str:
        ...

    @abstractmethod
    def _read_bytes(self, key: str) -> bytes:
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    @staticmethod
    def _generate_key(namespace: str = "") -> str:
        return str(Path(namespace) / str(uuid.uuid4()))


class RedisStorage(Storage):
    def __init__(self, dsn: Optional[str] = None, namespace: str = "namespace", chunksize: int = 2 ** 28, ttl: int = 0, **kwargs):
        params = {"health_check_interval": 30, "socket_keepalive": True}
        kwargs.update(params)

        if dsn:
            self.redis = Redis.from_url(dsn, **kwargs)
        else:
            self.redis = Redis(**kwargs)

        self.chunksize = chunksize
        self.registry_name = "RedisStorageRegistry"
        self.chunks_suffix = "chunks"
        self.ttl = ttl
        super().__init__(namespace)

    def set_namespace(self, namespace: str):
        self.namespace = namespace

    def _get_registry_name(self):
        return f"{self.namespace}|{self.registry_name}"

    def _get_chunksname(self, key: str):
        return f"{self.namespace}|{key}|{self.chunks_suffix}"

    def _write_by_chunks(self, obj: bytes, key: str):
        chunks_tuple = chunk_bytes(obj, self.chunksize)
        registry = self._get_registry_name()
        name = self._get_chunksname(key)
        with self.redis.pipeline() as pipe:
            pipe.delete(name)
            for chunk in chunks_tuple:
                pipe.rpush(name, chunk)
            pipe.hset(registry, key, 1)  # dummy value 1. Only for key existing
            if self.ttl > 0:
                pipe.expire(key, self.ttl)
            pipe.execute()

    def _read_by_chunks(self, key: str):
        name = self._get_chunksname(key)
        chunks_tuple = self.redis.lrange(name, 0, -1)
        return join_chunks(chunks_tuple)

    def __delitem__(self, key: str):
        registry = self._get_registry_name()
        name = self._get_chunksname(key)

        with self.redis.pipeline() as pipe:
            pipe.delete(name)
            pipe.hdel(registry, key)
            pipe.execute()

    def _read_bytes(self, key: str) -> bytes:
        if not self.exists(key):
            raise KeyError(
                f"There is no key '{key}' in {self.__class__.__name__} with namespace '{str(self.namespace)}'"
            )
        return self._read_by_chunks(key)

    def _write_bytes(self, obj: bytes, key: Optional[str] = None) -> str:
        key = key or self._generate_key()
        self._write_by_chunks(obj, key)
        return key

    def exists(self, key: str) -> bool:
        return self.redis.hexists(self._get_registry_name(), key)

    def __len__(self):
        return len(list(self.__iter__()))

    def __iter__(self):
        keys = sorted([key.decode("utf-8") for key in self.redis.hkeys(self._get_registry_name())])
        return iter(keys)
