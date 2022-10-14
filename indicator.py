from typing import Any, Dict, List, Callable
from numbers import Number
import numpy as np
import pandas as pd

import data_manager as dm
from visualizations import DataSourceInteraface
from utils import *

class ParamNames:
    # PRICE_TYPE = 'Price Type'
    PERSIST = 'Persist'

class SystemIndicator(DataSourceInteraface):
    ''' System indicator is a wrapper around User indicator which provides all neccessary 
        methods for indicator to be integrated in simulation '''

    def __init__(self, name="indicator", on_calculate_func=None, parameters: Dict = {}, on_init_function=None):
        
        self.name = name
        self.on_calculate = on_calculate_func
        self.on_init = on_init_function
        self.parameters = parameters
        self.data = dm.data
        self.data_idx = 0
        self.output = []
        self.last_output_size = 0
        self.init_executed = False
        self.depending_indicators = None

    def __getitem__(self, item):
        if type(item) != int:
            print("[{}][SytemIndicator] Unsupported subscript type: {} (only integer is allowed." % (self.name, type(item)))
        else:
            return self.output[self.data_idx - item]

    def set_on_calculate_function(self, on_calculate_function: Callable[[Any], List[Number]]):
        self.on_calculate = on_calculate_function

    def set_on_init_function(self, on_init_function: Callable[[Any], List[Number]]):
        self.on_init = on_init_function

    def set_parameters(self, parameters: Dict):
        self.parameters = parameters

    # TODO: Obsidian
    def set_depending_indicators(self, indicators: Dict):
        self.depending_indicators = indicators
        for indicator_name, indicator in self.depending_indicators.items():
            setattr(self, indicator_name, indicator)


    def init(self, init_idx, n=100):
        if self.on_init is None:
            print("[{}][SystemIndicator] Initialization called, but init function not provided" % self.name)
            return

        self.output = np.zeros((self.data.shape[0], 1))
        self.output[:] = np.NaN
        
        init_start_idx = max(1, init_idx-n)
        for index in range(init_start_idx, init_idx+1):
            input_data = self.data[0:index+1]
            # reverse order - first in list is latest data
            input_data.reverse()
            output = self.on_init(input_data)
            for i in range(len(output)):
                self.output[index-i] = output[i]

        self.data_idx = init_idx
        self.init_executed = True

    def reset_last_output(self, idx):
        for i in range(idx, idx-self.last_output_size, -1):
            self.output[i] = np.NaN

    def calculate(self, input_data, data_idx):
        if self.on_init is not None and not self.init_executed:
            print("[{}][SystemIndicator] Init function provided but unused, cannot proceed." % self.name)
            return
        self.data_idx = data_idx

        if not self.parameters.get(ParamNames.PERSIST, True):
            self.reset_last_output(self.data_idx)
        
        output = self.on_calculate(input_data)
        for i in range(len(output)):
            self.output[self.data_idx-i] = output[i]
        
        self.last_output_size = len(output)


    def get_data(self, time, n=1) -> list:
        ''' Overloaded interface function for getting indicator ouput data '''
        last_time = self.data.Date[self.data_idx]
        step = 0
        if last_time < time: step = 1
        elif last_time > time: step = -1
        data_idx = self.data_idx + step

        while (step > 0 and self.data.Date[data_idx] <= time) or \
              (step < 0 and self.data.Date[data_idx] >= time):
            data_idx += step
        data_idx -= step

        return self.output[data_idx-n+1 : data_idx+1]
