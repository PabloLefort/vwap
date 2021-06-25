import logging

from kafka import KafkaConsumer
from json import loads


logging.basicConfig(format='%(asctime)s - [%(name)s] [%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('VWAP Consumer')


btc_usd_consumer = KafkaConsumer(
    'BTCUSD',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    #group_id='my-group-id',
    value_deserializer=lambda x: loads(x.decode('utf-8'))
)

for event in btc_usd_consumer:
    event_data = event.value
    logger.info('Received new event %s', event_data)
