import asyncio
import logging
import time

from copra.websocket import Channel, Client
from decimal import Decimal
from kafka import KafkaProducer


logging.basicConfig(format='%(asctime)s - [%(name)s] [%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger('VWAP Engine')

#time.sleep(10)  # Wait to Kafka topics
#producer = KafkaProducer(
#    bootstrap_servers=['localhost:9092'],
#    value_serializer=lambda x: dumps(x).encode('utf-8')
#)
MAX_DATA_POINTS = 200


class VWAPChannel(Channel):

    def __init__(self, product_id):
        super().__init__('matches', product_id)
        self.product_id = product_id
        self.data_points = {}
        self.total_volume = 0
        self.total_price = 0
        self.data_points_count = 0
        self.vwap = 0

    def add_data_point(self, data_point):
        # Push newest data point
        self.data_points[self.data_points_count] = data_point

        # Always update volume with newest data point
        self.total_volume += data_point['size']
        self.total_price += data_point['price']

        if self.data_points_count >= MAX_DATA_POINTS:
            drop_data_point_index = self.data_points_count - MAX_DATA_POINTS

            # Update volume, price and drop oldest data point
            self.total_volume -= self.data_points[drop_data_point_index]['size']
            self.total_price -= self.data_points[drop_data_point_index]['price']
            del self.data_points[drop_data_point_index]

        self.data_points_count += 1

        # Recalculate vwap
        self.vwap = self._calculate_vwap(data_point['size'])
        #producer.send(self.product_id, value={'vwap': self.vwap, 'datapoint': data_point})
        logger.info('[%s] vwap: %s', self.product_id, self.vwap)

    def get_product_id(self):
        return self.product_id

    def _calculate_vwap(self, size):
        return ((size * self.total_price) / self.total_volume).quantize(Decimal('0.01'))


class VWAPClient(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._channels = {}
        for c in args[1]:
            self._channels[c.get_product_id()] = c

    def on_message(self, message):
        product_id = message.get('product_id')
        price = message.get('price')
        size = message.get('size')

        if product_id and price and size:
            price = Decimal(message.get('price'))
            size = Decimal(message.get('size'))
            data_point = {'price': price, 'size': size}

            channel = self._channels[product_id]
            channel.add_data_point(data_point)
        else:
            logger.warning('Dropping empty message')


loop = asyncio.get_event_loop()
channels = [VWAPChannel('BTC-USD'), VWAPChannel('ETH-BTC'), VWAPChannel('ETH-USD')]
ws = VWAPClient(loop, channels)

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(ws.close())
    loop.close()
