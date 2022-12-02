from numbers import Number
from typing import List
from trader import SystemTrader, OrderStatus, OrderType

dependencies = {
    #'indicator_name': {'indicator': 'indicator_module', 'parameters': {}}
}

parameters = {
    'param1': 'default_value1',
    'visualization': { 'COLOR': 'Red', 'STYLE': 'Dashed' }
}

class TraderExample(SystemTrader):
    
    # def initialize(self, data) -> List[Number]: #optional
    #     return [data.Close[0]]

    def calculate(self, data):
        print(data.Close[0])
        if data.Close[0] > 1.1350 and len(self.orders) == 0:
            order = self.create_order(OrderType.BUY, 1.1300, 1.365)
            print("creating order - ", order)