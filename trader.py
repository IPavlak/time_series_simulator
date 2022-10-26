from copy import deepcopy
from typing import Dict, List
from numbers import Number
from enum import Enum
from uuid import uuid4
import numpy as np
import pandas as pd

import data_manager as dm
from visualizations import DataSourceInteraface
from utils import *

class CommonParams:
    class VisualizationParams:
        TYPE = 'Line'
        COLOR = 'Blue'

    # PRICE_TYPE = 'Price Type'
    PERSIST = True
    visualization = VisualizationParams()

class OrderType(Enum):
    UNDEFINED = -1
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5

class OrderStatus(Enum):
    UNINITIALIZED = -1
    PENDING = 0
    ACTIVE = 1
    CLOSED = 2

# TODO: Obsidian
class Order:
    id = -1
    type = OrderType(-1)
    price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    open_time = None
    close_time = None
    close_price = 0.0
    status = OrderStatus(-1)

    @property
    def profit(self):
        return self.close_price - self.price

class SystemTrader(DataSourceInteraface):
    ''' System indicator is a wrapper around User indicator which provides all neccessary 
        methods for indicator to be integrated in simulation '''

    def __init__(self, name="indicator", parameters: Dict = {}):
        
        self.parameters = CommonParams()
        self.set_parameters(parameters)
        self.name = name
        self.data = dm.data
        self.data_idx = 0
        self.current_price = 0.0
        self.current_time = None
        self.depending_indicators = None

        self.orders = {} #(id, Order)
        self.spread = 0.0

    @property
    def closed_orders(self):
        return {id: order for id, order in self.orders.items() if order.status == OrderStatus.CLOSED}
    
    @property
    def active_orders(self):
        return {id: order for id, order in self.orders.items() if order.status == OrderStatus.ACTIVE}

    @property
    def pending_orders(self):
        return {id: order for id, order in self.orders.items() if order.status == OrderStatus.PENDING}

    def set_parameters(self, parameters: Dict):
        update_from_dict(self.parameters, parameters)
        for name, value in parameters.items():
            # TODO: check if param name already exists - hasattr
            setattr(self, name, value)

    # TODO: Obsidian
    def set_depending_indicators(self, indicators: List):
        self.depending_indicators = indicators
        for indicator in self.depending_indicators:
            # TODO: check if indicator name already exists
            setattr(self, indicator.name, indicator)


    def create_order(self, order_type, stop_loss, take_profit, strike_price=None):
        if not self._are_order_params_valid(self.current_price, order_type, stop_loss, take_profit, strike_price):
            print("[{}][SystemTrader] Order parameters are not valid, disregarding order: "
                  "(order type: {}, current price: {}, stop loss: {}, take profit: {}, strike price: {})",  \
                    order_type, self.current_price, stop_loss, take_profit, strike_price)
            return Order()
        
        order = Order()
        order.id = int(uuid4())
        order.type = order_type
        order.stop_loss = stop_loss
        order.take_profit = take_profit
        order.open_time = self.current_time
        
        if order_type == OrderType.BUY:
            order.price = self.current_price + self.spread
            order.status = OrderStatus.ACTIVE
        elif order_type == OrderType.SELL:
            order.price = self.current_price - self.spread
            order.status = OrderStatus.ACTIVE
        else:
            order.status = OrderStatus.PENDING
            order.price = strike_price

        self.orders[order.id] = order
        return deepcopy(order)

    # def close_order(self, id):
    #     order = self.orders[id]
    #     if order.status == OrderStatus.PENDING:
    #         pass

    def _update_orders(self):
        for order in self.active_orders:
            if self._is_stop_loss_reached(self.current_price, order) or self._is_take_profit_reached(self.current_price, order):
                order.close_price = self.current_price
                order.close_time = self.current_time
                order.status = OrderStatus.CLOSED
        
        for order in self.pending_orders:
            if self._is_strike_price_reached(self.current_price, order):
                order.open_time = self.current_time
                order.status = OrderStatus.ACTIVE


    def _are_order_params_valid(self, price, order_type, stop_loss, take_profit, strike_price):
        if order_type == OrderType.BUY:
            return stop_loss < price - self.spread and take_profit > price + self.spread

        elif order_type == OrderType.SELL:
            return stop_loss > price + self.spread and take_profit < price - self.spread

        elif order_type == OrderType.BUY_LIMIT and strike_price is not None:
            return price > strike_price and stop_loss < strike_price - self.spread and take_profit > strike_price + self.spread

        elif order_type == OrderType.SELL_LIMIT and strike_price is not None:
            return price < strike_price and stop_loss > strike_price + self.spread and take_profit < strike_price - self.spread

        elif order_type == OrderType.BUY_STOP and strike_price is not None:
            return price < strike_price and stop_loss < strike_price - self.spread and take_profit > strike_price + self.spread

        elif order_type == OrderType.SELL_STOP and strike_price is not None:
            return price > strike_price and stop_loss > strike_price + self.spread and take_profit < strike_price - self.spread
        
        else:
            return False
        
    def _is_stop_loss_reached(self, price, order):
        if order.type == OrderType.BUY or order.type == OrderType.BUY_LIMIT or order.type == OrderType.BUY_STOP:
            return price <= order.stop_loss
        else:
            return price >= order.stop_loss

    def _is_take_profit_reached(self, price, order):
        if order.type == OrderType.BUY or order.type == OrderType.BUY_LIMIT or order.type == OrderType.BUY_STOP:
            return price >= order.take_profit
        else:
            return price <= order.take_profit

    def _is_strike_price_reached(self, price, order):
        if order.type == OrderType.BUY_LIMIT or order.type == OrderType.BUY_STOP:
            return price <= order.price - self.spread
        else:
            return price >= order.price + self.spread

    # TODO: when needed
    def init(self, init_idx, n=1):
        init_start_idx = max(1, init_idx-n)
        for index in range(init_start_idx, init_idx+1):
            input_data = self.data[0:index+1]
            # reverse order - first in list is latest data
            input_data.reverse()
            self.initialize(input_data)

        self.data_idx = init_idx

    def update(self, input_data, data_idx):
        self.data_idx = data_idx
        self.current_price = input_data.Close[0]
        self.current_time = input_data.Time[0]
        self._update_orders()
        self.calculate(input_data)


    # TODO:
    def get_data(self, time, n=1) -> list:
        ''' Overloaded interface function for getting reader ouput data - data for visualization'''
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


    # User functions - initialize is not obligatory function, if it is not defined default will be used
    def initialize(self, data):
        pass
    
    def calculate(self, data) -> List[Number]:
        print("[{}][SystemTrader] Calculate function not provided, cannot proceed." % self.name)
