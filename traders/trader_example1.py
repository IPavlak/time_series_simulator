from numbers import Number
from typing import List
from trader import SystemTrader, OrderStatus, OrderType

dependencies = {
    #'indicator_name': {'indicator': 'indicator_module', 'parameters': {}}
}

parameters = {
    'param1': 'default_value1',
    'visualization': [
        { 'COLOR': 'Blue', 'STYLE': 'Dashed' }, # BUY
        { 'COLOR': 'Red', 'STYLE': 'Dashed' }   # SELL
    ]
}

class TraderExample(SystemTrader):
    
    # def initialize(self, data) -> List[Number]: #optional
    #     return [data.Close[0]]

    def calculate(self, data):
        # print(data[0].Close)
        if data[0].Close > 1.1350 and len(self.orders) == 0:
            order = self.create_order(OrderType.BUY, 1.1342, 2.1365)
            print("creating order - ", order)
        elif data[0].Close > 1.14 and len(self.orders) < 2:
            order = self.create_order(OrderType.SELL, 1.143, 1.132)
            print("creating order - ", order)