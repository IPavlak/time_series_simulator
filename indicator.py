from tokenize import Number
from typing import Any, Dict, List, Callable
from numbers import Number
import numpy as np
import pandas as pd

from visualizations import DataSourceInteraface

class ParamNames:
    # PRICE_TYPE = 'Price Type'
    PERSIST = 'Persist'

class SystemIndicator(DataSourceInteraface):
    ''' System indicator is a wrapper around User indicator which provides all neccessary 
        methods for indicator to be integrated in simulation '''

    def __init__(self, on_calculate_func=None, parameters: Dict = {}):
        
        self.on_calculate = on_calculate_func
        self.parameters = parameters
        self.input_data = []
        self.data = []
        self.last_data_size = 0

    def set_on_calculate_function(self, on_calculate_function: Callable[[Any], List[Number]]):
        self.on_calculate = on_calculate_function

    def set_parameters(self, parameters: Dict):
        self.parameters = parameters

    def set_input_data(self, input_data):
        self.input_data = input_data
        self.data = np.zeros((len(input_data), 1))
        self.data[:] = np.NaN

    def reset_last_data(self, idx):
        for i in range(idx, idx-self.last_data_size, -1):
            self.data[i] = np.NaN


    # TODO: FrameData
    def calculate(self, idx, curr_candle=None):
        if not self.parameters.get(ParamNames.PERSIST, True):
            self.reset_last_data(idx-1)
        input_data = self.input_data.iloc[0:idx+1]
        # reverse order - first in list is latest data
        input_data = input_data.iloc[::-1]
        
        output_data = self.on_calculate(input_data)
        for i in range(len(output_data)):
            self.data[idx-i] = output_data[i]
        
        self.last_data_size = len(output_data)


    def get_data(self, start: int, end: int) -> list:
        ''' Overloaded interface function '''
        return self.data[start : end+1]
