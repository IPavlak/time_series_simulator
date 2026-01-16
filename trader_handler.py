from collections import OrderedDict
from copy import deepcopy
from typing import Dict
from uuid import uuid4
from inspect import getmembers, isclass

import pandas as pd

import data_manager as dm
from utils import *
from trader import SystemTrader

class TraderDef:
    trader_class = None
    parameters_def = {}
    dependencies = {}

class TraderHandler:
    ''' TraderHandler is a class that takes care of all traders '''

    def __init__(self, indicator_handler, start_balance=10000.0):
        self.data = dm.data
        self.data_idx = 0
        self.start_balance = start_balance
        self.traders = OrderedDict()
        self.indicator_handler = indicator_handler

    # TODO: check for circular dependencies
    def add_trader(self, trader_name: str, trader_module: str, trader_parameters: Dict, init_frame_idx):
        print("[TraderHandler] Adding trader '{}' from {}".format(trader_name, trader_module))

        trader_def = self._get_trader_def(trader_module)
        default_parameters = deepcopy(trader_def.parameters_def)
        
        # update default parameters with given parameters 
        trader_def.parameters_def.update(trader_parameters)
        trader_parameters = trader_def.parameters_def

        # if number of parameters have increased, that means that some parameters were not declared beforehand (invalid)
        if len(trader_parameters) > len(default_parameters):
            raise ValueError("[TraderHandler] Invalid parameters: ", set(trader_parameters) - set(default_parameters))

        depedency_indicators = []
        for dependency_name, dependency in trader_def.dependencies.items():
            # TODO: try catch in case dependency is missing required fields
            dependency_indicator = self.indicator_handler.add_indicator(dependency_name, dependency['indicator'], dependency['parameters'], init_frame_idx)
            depedency_indicators.append( dependency_indicator )

        trader = trader_def.trader_class(trader_name, trader_parameters)
        trader.set_depending_indicators(depedency_indicators)
        trader.init(init_frame_idx)

        self.traders[str(uuid4())] = trader

        return trader

    def update(self, framedata):
        self.data_idx = framedata.core_data_idx
        input_data = self.data[0:self.data_idx+1]
        input_data.reverse()

        # TODO: BENCHMARK
        if framedata.curr_candle is not None:
            current_candle = pd.DataFrame({'Date':  framedata.curr_candle.Date,
                                           'Open':  framedata.curr_candle.Open,
                                           'High':  framedata.curr_candle.High,
                                           'Low':   framedata.curr_candle.Low,
                                           'Close': framedata.curr_candle.Close},  index=[0])
            # add current candle to input data at index=0
            input_data = dm.DataView(input_data[1::], current_candle)
        else:
            input_data = dm.DataView(input_data)

        for trader in self.traders.values():
            trader.update(input_data, self.data_idx)


    def get_balance(self, data_idx, trader_name = None):
        balance = self.start_balance
        if trader_name is None:
            for trader in self.traders.values():
                balance += trader.get_profit(data_idx)
        else:
            for trader in self.traders.values():
                if trader.name == trader_name:
                    balance += trader.get_profit(data_idx)
        return balance

    def _get_trader_def(self, trader_module_name: str):
        trader_module = import_module(trader_module_name)
        trader_def = TraderDef()
        for name, value in getmembers(trader_module):
            if name == 'dependencies':
                trader_def.dependencies = value
            elif name == 'parameters':
                trader_def.parameters_def = value
            if isclass(value) and value is not SystemTrader and issubclass(value, SystemTrader):
                trader_def.trader_class = value

        return trader_def
