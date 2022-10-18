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

    def __init__(self, name="indicator", parameters: Dict = {}):
        
        self.name = name
        self.set_parameters(parameters)
        self.data = dm.data
        self.data_idx = 0
        self.output = []
        self.last_output_size = 0
        self.init_executed = False
        self.depending_indicators = None

    def __getitem__(self, item):
        if type(item) != int:
            print("[{}][SytemIndicator] Unsupported subscript type: {} (only integer is allowed.".format(self.name, type(item)))
        else:
            return self.output[self.data_idx - item]

    def set_parameters(self, parameters: Dict):
        self.parameters = parameters
        for name, value in self.parameters:
            # TODO: check if param name already exists
            setattr(self, name, value)

    # TODO: Obsidian
    def set_depending_indicators(self, indicators: List):
        self.depending_indicators = indicators
        for indicator in self.depending_indicators:
            # TODO: check if indicator name already exists
            setattr(self, indicator.name, indicator)


    def init(self, init_idx, n=100):
        if not hasattr(self, 'initialize'):
            print("[{}][SystemIndicator] Initialization called, but init function not provided".format(self.name))
            return

        self.output = np.zeros((self.data.shape[0], 1))
        self.output[:] = np.NaN
        
        init_start_idx = max(1, init_idx-n)
        for index in range(init_start_idx, init_idx+1):
            input_data = self.data[0:index+1]
            # reverse order - first in list is latest data
            input_data.reverse()
            output = self.initialize(input_data)
            for i in range(len(output)):
                self.output[index-i] = output[i]

        self.data_idx = init_idx
        self.init_executed = True

    def reset_last_output(self, idx):
        for i in range(idx, idx-self.last_output_size, -1):
            self.output[i] = np.NaN

    def update(self, input_data, data_idx):
        if hasattr(self, 'initialize') and not self.init_executed:
            print("[{}][SystemIndicator] Init function provided but unused, cannot proceed.".format(self.name))
            return
        self.data_idx = data_idx

        if not self.parameters.get(ParamNames.PERSIST, True):
            self.reset_last_output(self.data_idx)
        
        output = self.calculate(input_data)
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


    # User functions - initialize is not obligatory function, if it is not defines it won't be used
    # def initialize(self):
    #     pass
    def calculate(self, data):
        print("[{}][SystemIndicator] Calculate function not provided, cannot proceed." % self.name)
