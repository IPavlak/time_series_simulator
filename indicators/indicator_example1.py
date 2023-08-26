from numbers import Number
from typing import List
from indicator import SystemIndicator

dependencies = {
    #'indicator_name': {'indicator': 'indicator_module', 'parameters': {}}
}

parameters = {
    'param1': 'default_value1',
    # 'visualization': { 'COLOR': 'Blue' }
}

class IndicatorExample(SystemIndicator):
    
    def initialize(self, data) -> List[Number]: #optional
        return [data.Close[0]]

    def calculate(self, data) -> List[Number]:
        print(self.param1)
        return [data.iloc[0].Close]