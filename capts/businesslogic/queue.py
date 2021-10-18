import os
from itertools import count
from time import sleep

import pika
from pika import URLParameters
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
from pika.exceptions import AMQPConnectionError
from pydantic import BaseModel

from capts.config import RABBIT_URL


class Config:
    EXCHANGE = os.environ.get('EXCHANGE', 'exchange')
    EXCHANGE_DEAD_LETTER = os.environ.get('EXCHANGE_DEAD_LETTER', 'exchange-dead-letter')
    FNS_QUEUE = os.environ.get('FNS_QUEUE', 'fns-queue')
    ALCO_QUEUE = os.environ.get('ALCO_QUEUE', 'alco-queue')
    FNS_QUEUE_ROUTING_KEY = 'fns'
    ALCO_QUEUE_ROUTING_KEY = 'alco'


def send_object(
    channel: BlockingChannel, app_model: BaseModel, exchange: str, routing_key: str
):
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=app_model.json(by_alias=True, exclude_unset=True),
        properties=pika.BasicProperties(delivery_mode=2),
    )


class MessagePublisher:

    def __init__(self, channel: BlockingChannel, exchange: str, routing_key: str):
        self._channel = channel
        self._exchange = exchange
        self._routing_key = routing_key

    def publish_message(self, object_: BaseModel):
        send_object(channel=self._channel, app_model=object_, exchange=self._exchange, routing_key=self._routing_key)


def init_exchange(channel: BlockingChannel, exchange: str, type_: str):
    channel.exchange_declare(
        exchange=exchange,
        durable=True,
        exchange_type=type_,
    )


def init_queue(channel: BlockingChannel, exchange: str, exchange_dead_letter: str, queue: str, routing_key: str):
    arguments = {
        "x-dead-letter-exchange": "dead-letter",
        "x-dead-letter-routing-key": queue,
    }

    channel.queue_declare(
        queue=queue,
        durable=True,
        arguments=arguments,
    )
    channel.queue_bind(
        exchange=exchange,
        queue=queue,
        routing_key=routing_key,
    )

    dead_letter_queue = f"{queue}-dead-letter"
    channel.queue_declare(
        queue=dead_letter_queue,
        durable=True,
    )
    channel.queue_bind(
        exchange=exchange_dead_letter,
        queue=dead_letter_queue,
        routing_key=queue,
    )


def init_channel(
    connection: BlockingConnection,
    exchange: str,
    exchange_dead_letter,
    fns_queue: str,
    fns_routing_key: str,
    alco_queue: str,
    alco_routing_key: str,
):
    channel = connection.channel()
    init_exchange(channel, exchange, 'direct')
    init_exchange(channel, exchange_dead_letter, 'direct')

    init_queue(channel, exchange, exchange_dead_letter, fns_queue, fns_routing_key)
    init_queue(channel, exchange, exchange_dead_letter, alco_queue, alco_routing_key)

    return channel

MAX_ATTEMPTS = 10
for attempt in count():
    try:
        connection = BlockingConnection(URLParameters(RABBIT_URL))
        break
    except AMQPConnectionError:
        sleep(1)
    if attempt == MAX_ATTEMPTS:
        raise AMQPConnectionError(f'Could not connect to {RABBIT_URL}')

channel = init_channel(
    connection=connection,
    exchange=Config.EXCHANGE,
    exchange_dead_letter=Config.EXCHANGE_DEAD_LETTER,
    fns_queue=Config.FNS_QUEUE,
    fns_routing_key=Config.FNS_QUEUE_ROUTING_KEY,
    alco_queue=Config.ALCO_QUEUE,
    alco_routing_key=Config.ALCO_QUEUE_ROUTING_KEY,
)
fns_message_publisher = MessagePublisher(channel, Config.EXCHANGE, Config.FNS_QUEUE_ROUTING_KEY)
alco_message_publisher = MessagePublisher(channel, Config.EXCHANGE, Config.ALCO_QUEUE_ROUTING_KEY)
