from tokenize import Number
from typing import Any, Dict, List, Callable
from numbers import Number
import numpy as np
import pandas as pd

from visualizations import DataSourceInteraface
from utils import *

class ParamNames:
    # PRICE_TYPE = 'Price Type'
    PERSIST = 'Persist'

class SystemIndicator(DataSourceInteraface):
    ''' System indicator is a wrapper around User indicator which provides all neccessary 
        methods for indicator to be integrated in simulation '''

    def __init__(self, on_calculate_func=None, parameters: Dict = {}):
        
        self.on_calculate = on_calculate_func
        self.parameters = parameters
        self.input_data = [] # TODO: refactor names
        self.data = []
        self.data_idx = 0
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

    def calculate(self, framedata):
        if framedata.reset:
            self.data_idx = get_idx_from_time(self.input_data, framedata.time, 'LESS_OR_EQUAL')
            self._calculate()
        else:
            last_time = self.input_data.Date[self.data_idx]
            step = 0
            if last_time < framedata.time: step = 1
            elif last_time > framedata.time: step = -1
            self.data_idx += step

            while (step > 0 and self.input_data.Date[self.data_idx] <= framedata.time) or \
                  (step < 0 and self.input_data.Date[self.data_idx] >= framedata.time):
                self._calculate()
                self.data_idx += step
            self.data_idx -= step
            

    def _calculate(self):
        if not self.parameters.get(ParamNames.PERSIST, True):
            self.reset_last_data(self.data_idx)
        
        input_data = self.input_data.iloc[0:self.data_idx+1]
        # reverse order - first in list is latest data
        input_data = input_data.iloc[::-1]
        
        output_data = self.on_calculate(input_data)
        for i in range(len(output_data)):
            self.data[self.data_idx-i] = output_data[i]
        
        self.last_data_size = len(output_data)


    def get_data(self, time, n=1) -> list:
        ''' Overloaded interface function '''
        last_time = self.input_data.Date[self.data_idx]
        step = 0
        if last_time < time: step = 1
        elif last_time > time: step = -1
        data_idx = self.data_idx + step

        while (step > 0 and self.input_data.Date[data_idx] <= time) or \
                (step < 0 and self.input_data.Date[data_idx] >= time):
            data_idx += step
        data_idx -= step

        return self.data[data_idx-n+1 : data_idx+1]
