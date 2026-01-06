from copy import deepcopy
# from time import time
from typing import Dict, List
from functools import total_ordering
from enum import Enum
from uuid import uuid4
import numpy as np
import pandas as pd

import data_manager as dm
from visualizations import DataSourceInteraface, VisualizationParams
from utils import *

class CommonParams:
    # PRICE_TYPE = 'Price Type'
    PERSIST = True
    visualization = [VisualizationParams()]

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
    DELETED = 3

# TODO: Obsidian
@total_ordering
class Order:
    id = -1
    type = OrderType(-1)
    open_price = 0.0
    stop_loss = 0.0
    take_profit = 0.0
    open_time = None
    close_time = None
    close_price = 0.0
    status = OrderStatus(-1)

    @property
    def profit(self):
        return self.close_price - self.open_price

    def __lt__(self, other):
        if other.status == OrderStatus.ACTIVE:
            if self.status != OrderStatus.ACTIVE:
                return True
            else:
                return self.open_time < other.open_time
        else:
            return self.close_time < other.close_time

    def __eq__(self, other):
        return self.id == other.id
    
class TraderOrderDataSourceWrapper(DataSourceInteraface):
    def __init__(self, trader, order_types: List[OrderType]):
        self.trader = trader
        self.order_types = order_types
        self.data = trader.data

    def get_data(self, time, n=1) -> np.ndarray:
        ''' Overloaded interface function for getting reader ouput data - data for visualization'''
        output = np.full(shape=[n, len(self.trader.orders)], fill_value=np.nan)

        orders_num = 0
        for order in self.trader.orders.values():

            if order.status == OrderStatus.UNINITIALIZED or order.status == OrderStatus.DELETED:
                continue

            if order.type not in self.order_types:
                continue

            if order.status == OrderStatus.PENDING:

                data_idx = get_idx_from_time_and_hint(time, self.data, self.trader.data_idx)
                for idx in range(data_idx-n+1, data_idx+1):
                    output[idx, orders_num] = order.open_price
            else:

                close_price = self.trader.current_price if order.status == OrderStatus.ACTIVE else order.close_price
                close_time = self.trader.current_time if order.status == OrderStatus.ACTIVE else order.close_time
                
                data_idx = get_idx_from_time_and_hint(time, self.data, self.trader.data_idx)
                time_unit = pd.Timedelta(self.data.Date[data_idx] - self.data.Date[data_idx-1]).total_seconds()
                open_idx = self.trader.data_idx - int(pd.Timedelta(self.data.Date[data_idx] - order.open_time).total_seconds() / time_unit) # best guess
                open_idx = get_idx_from_time_and_hint(order.open_time, self.data, open_idx)
                close_idx = self.trader.data_idx - int(pd.Timedelta(self.data.Date[data_idx] - close_time).total_seconds() / time_unit) # best guess
                close_idx = get_idx_from_time_and_hint(close_time, self.data, close_idx)
                N = max(1, close_idx - open_idx)

                if data_idx - close_idx > n:
                    continue

                for idx in range(data_idx-n+1, data_idx+1):
                    if open_idx <= idx <= close_idx:
                        output[idx - (data_idx-n+1), orders_num] = order.open_price + (idx - open_idx)/N * (close_price - order.open_price)

            orders_num += 1

        output = output[:, :orders_num]
        return output


class SystemTrader():
    ''' System trader is a wrapper around User trader which provides all neccessary 
        methods for trader to be integrated in simulation '''

    def __init__(self, name="trader", parameters: Dict = {}):
        
        self.parameters = CommonParams()
        self.set_parameters(parameters)
        # TODO: check vis params validity
        self.name = name
        self.data = dm.data
        self.data_idx = 0
        self.current_price = 0.0
        self.current_time = None
        self.depending_indicators = None

        self.orders = {} #(id, Order)
        self.spread = 0.0

        self.buy_orders_data_source = TraderOrderDataSourceWrapper(self, [OrderType.BUY])
        self.sell_orders_data_source = TraderOrderDataSourceWrapper(self, [OrderType.SELL])
        self.buy_pend_orders_data_source = TraderOrderDataSourceWrapper(self, [OrderType.BUY_LIMIT, OrderType.BUY_STOP])
        self.sell_pend_orders_data_source = TraderOrderDataSourceWrapper(self, [OrderType.SELL_LIMIT, OrderType.SELL_STOP])

    @property
    def closed_orders(self):
        return [order for order in self.orders.values() if order.status == OrderStatus.CLOSED]
    
    @property
    def active_orders(self):
        return [order for order in self.orders.values() if order.status == OrderStatus.ACTIVE]

    @property
    def pending_orders(self):
        return [order for order in self.orders.values() if order.status == OrderStatus.PENDING]

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

    def get_buy_vis_params(self):
        return [self.parameters.visualization[0]]
    
    def get_sell_vis_params(self):
        return [self.parameters.visualization[1]]


    def create_order(self, order_type, stop_loss, take_profit, strike_price=None):
        if not self._are_order_params_valid(self.current_price, order_type, stop_loss, take_profit, strike_price):
            print("[{}][SystemTrader] Order parameters are not valid, disregarding order: "
                  "(order type: {}, current price: {}, stop loss: {}, take profit: {}, strike price: {})".format(
                    self.name, order_type, self.current_price, stop_loss, take_profit, strike_price))
            return Order()
        
        order = Order()
        order.id = int(uuid4())
        order.type = order_type
        order.stop_loss = stop_loss
        order.take_profit = take_profit
        order.open_time = self.current_time
        
        if order_type == OrderType.BUY:
            order.open_price = self.current_price + self.spread
            order.status = OrderStatus.ACTIVE
        elif order_type == OrderType.SELL:
            order.open_price = self.current_price - self.spread
            order.status = OrderStatus.ACTIVE
        else:
            order.status = OrderStatus.PENDING
            order.open_price = strike_price

        self.orders[order.id] = order
        return deepcopy(order)

    def close_order(self, id):
        order = self.orders[id]
        if order.status == OrderStatus.UNINITIALIZED:
            print("[{}][SystemTrader] Trying to close uninitialized order: id='{}'".format(self.name, id))
        elif order.status == OrderStatus.DELETED:
             print("[{}][SystemTrader] Trying to close deleted order: id='{}'".format(self.name, id))
        elif order.status == OrderStatus.CLOSED:
            print("[{}][SystemTrader] Trying to close already closed order: id='{}'".format(self.name, id))
        elif order.status == OrderStatus.PENDING:
            order.close_price = order.open_price
            order.close_time = self.current_time
            order.status = OrderStatus.DELETED
        else:
            order.close_price = self.current_price
            order.close_time = self.current_time
            order.status = OrderStatus.CLOSED

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
            return price <= order.open_price - self.spread
        else:
            return price >= order.open_price + self.spread

    def get_last_order(self):
        time = None
        last_order = Order()
        for order in self.orders.values():
            if time is None or order.status == OrderStatus.CLOSED and time > order.close_time:
                time = order.close_time
                last_order = order
            elif time is None or order.status == OrderStatus.ACTIVE and time > order.open_time:
                time = order.open_time
                last_order = order
        return last_order

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
        print("trader update")
        time = input_data.Date[0]
        if self.current_time is None or time > self.current_time:
            self.data_idx = data_idx
            self.current_price = input_data.Close[0]
            self.current_time = time
            self._update_orders()
            self.calculate(input_data)


    # User functions - initialize is not obligatory function, if it is not defined default will be used
    def initialize(self, data):
        pass
    
    def calculate(self, data):
        pass

class SystemTraderBuy(SystemTrader, DataSourceInteraface):
    def __init__(self, name="trader", parameters: Dict = {}):
        super().__init__(name, parameters)
