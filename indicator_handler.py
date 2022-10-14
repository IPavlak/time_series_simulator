from collections import OrderedDict

import pandas as pd

import data_manager as dm
from indicator import SystemIndicator

class IndicatorHandler:
    ''' IndicatorHandler is a class that takes care of all indicators '''

    def __init__(self):
        self.data = dm.data
        self.data_idx = 0
        self.indicators = OrderedDict()

    def add_indicator(self, indicator: SystemIndicator, dependencies, init_frame_idx):
        # TODO: add all dependencies and initialize them
        self.indicators[indicator.name] = indicator  #  TODO: use unique ID for each indicator != indicator.name ==> maybe use sortedList instead of SortedDict (we never need to catch indicator by key, only by order of insertion)
        # TODO: set all depencies to indicator
        indicator.init(init_frame_idx)

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
            indicator.calculate(input_data, self.data_idx)
