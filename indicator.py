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

    def __init__(self, on_calculate_func=None, parameters: Dict = {}, on_init_function=None):
        
        self.on_calculate = on_calculate_func
        self.on_init = on_init_function
        self.parameters = parameters
        self.input_data = dm.data # TODO: refactor names
        self.data = []
        self.data_idx = 0
        self.last_data_size = 0
        self.init_executed = False

    def set_on_calculate_function(self, on_calculate_function: Callable[[Any], List[Number]]):
        self.on_calculate = on_calculate_function

    def set_on_init_function(self, on_init_function: Callable[[Any], List[Number]]):
        self.on_init = on_init_function

    def set_parameters(self, parameters: Dict):
        self.parameters = parameters

    def init(self, init_idx, n=100):
        if self.on_init is None:
            print("[SystemIndicator] Initialization called, but init function not provided")
            return

        self.data = np.zeros((self.input_data.shape[0], 1))
        self.data[:] = np.NaN
        
        init_start_idx = max(1, init_idx-n)
        for index in range(init_start_idx, init_idx+1):
            input_data = self.input_data[0:index+1]
            # reverse order - first in list is latest data
            input_data.reverse()
            output_data = self.on_init(input_data)
            for i in range(len(output_data)):
                self.data[index-i] = output_data[i]

        self.data_idx = init_idx
        self.init_executed = True

    def reset_last_data(self, idx):
        for i in range(idx, idx-self.last_data_size, -1):
            self.data[i] = np.NaN

    def calculate(self, framedata):
        if self.on_init is not None and not self.init_executed:
            print("[SystemIndicator] Init function provided but unused, cannot proceed")
            return
        
        self.data_idx = framedata.core_data_idx

        input_data = self.input_data[0:self.data_idx]

        # TODO: BENCHMARK
        if framedata.curr_candle is not None:
            current_candle = pd.DataFrame({'Date':  framedata.curr_candle.Date,
                                           'Open':  framedata.curr_candle.Open,
                                           'High':  framedata.curr_candle.High,
                                           'Low':   framedata.curr_candle.Low,
                                           'Close': framedata.curr_candle.Close},  index=[0])
            # add current candle to input data at index=0 and reset indexes
            input_data = current_candle.append(input_data[::-1], ignore_index=True)
        else:
            # slicing is faster than getting single data frame - flag as dependant on data structure
            input_data = self.input_data[self.data_idx : self.data_idx+1].append(input_data[::-1], ignore_index=True)

        self._calculate(input_data)
   

    def _calculate(self, input_data):
        if not self.parameters.get(ParamNames.PERSIST, True):
            self.reset_last_data(self.data_idx)
        
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
