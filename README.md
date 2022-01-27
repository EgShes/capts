# capts

## Deployment

### Weights

Download weights from [here](https://disk.yandex.ru/d/-YHfkL3KZGFmYA) and put it in the project root in `weights` folder

### Prod

```
cd docker-compose
cp envs/prod .env
DOCKER_BUILDKIT=1 docker-compose -f prod.yml up
```

### Dev

```
cd docker-compose
cp envs/dev .env
DOCKER_BUILDKIT=1 docker-compose -f prod.yml -f dev.overrride.yml up
```

### Documentation

Interactive API documentation is available at `/docs` endpoint
