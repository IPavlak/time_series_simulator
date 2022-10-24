from collections import OrderedDict
from copy import deepcopy
from typing import Dict
from uuid import uuid4
from inspect import getmembers, isclass

import pandas as pd

import data_manager as dm
from utils import *
from indicator import SystemIndicator

class IndicatorDef:
    indicator_class = None
    parameters_def = {}
    dependencies = {}

class IndicatorHandler:
    ''' IndicatorHandler is a class that takes care of all indicators '''

    def __init__(self):
        self.data = dm.data
        self.data_idx = 0
        self.indicators = OrderedDict()

    # TODO: check for circular dependencies
    def add_indicator(self, indicator_name: str, indicator_module: str, indicator_parameters: Dict, init_frame_idx):
        print("[IndicatorHandler] Adding indicator '{}' from {}".format(indicator_name, indicator_module))

        indicator_def = self._get_indicator_def(indicator_module)
        default_parameters = deepcopy(indicator_def.parameters_def)
        
        # update default parameters with given parameters 
        indicator_def.parameters_def.update(indicator_parameters)
        indicator_parameters = indicator_def.parameters_def

        # if number of parameters have increased, that means that some parameters were not declared beforehand (invalid)
        if len(indicator_parameters) > len(default_parameters):
            raise ValueError("[IndicatorHandler] Invalid parameters: ", set(indicator_parameters) - set(default_parameters))

        depedency_indicators = []
        for dependency_name, dependency in indicator_def.dependencies.items():
            # TODO: try catch in case dependency is missing required fields
            dependency_indicator = self.add_indicator(dependency_name, dependency['indicator'], dependency['parameters'], init_frame_idx)
            depedency_indicators.append( dependency_indicator )

        indicator = indicator_def.indicator_class(indicator_name, indicator_parameters)
        indicator.set_depending_indicators(depedency_indicators)
        indicator.init(init_frame_idx)

        self.indicators[str(uuid4())] = indicator

        return indicator

    def update(self, framedata):
        self.data_idx = framedata.core_data_idx
        input_data = self.data[0:self.data_idx]

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
            input_data = self.data[self.data_idx : self.data_idx+1].append(input_data[::-1], ignore_index=True)

        for indicator in self.indicators.values():
            indicator.update(input_data, self.data_idx)


    def _get_indicator_def(self, indicator_module_name: str):
        indicator_module = import_module(indicator_module_name) #importlib.import_module = __import__('indicators', globals(), locals()) #indicator_module_name) #TODO: Obsidian
        indicator_def = IndicatorDef()
        for name, value in getmembers(indicator_module):
            if name == 'dependencies':
                indicator_def.dependencies = value
            elif name == 'parameters':
                indicator_def.parameters_def = value
            if isclass(value) and value is not SystemIndicator and issubclass(value, SystemIndicator):
                indicator_def.indicator_class = value

        return indicator_def
