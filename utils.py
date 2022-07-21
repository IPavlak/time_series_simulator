class FrameData:
    ''' Index of current candle - core data is data used by core simulator '''
    core_data_idx = 0
    ''' Time of the current candle '''
    time = None
    ''' Current candle '''
    curr_candle = None
    ''' 
    Reset flag - if true there has been a change in simulation config, 
    we should start time series simulation from starting time again
    '''
    reset = True

class Candle:
    def __init__(self, Date, Open, High, Low, Close):
        self.Date = Date
        self.Open = Open
        self.High = High
        self.Low = Low
        self.Close = Close
        

def get_idx_from_time(data, time, op='EQUAL'):
    ''' 
    Get row index from given data and time - this function is costly so it should not be frequently used.
    Data should be pandas DataFrame with 'Date' as one of the columns
    op parameter can be EQUAL, GREATER_OR_EQUAL or LESS_OR_EQUAL - to search for appropriate idx
    '''
    if op == 'EQUAL':
        return data[data['Date'] == time].index.values[0]
    elif op == 'GREATER_OR_EQUAL':
        return data[data['Date'] >= time].index.values[0]
    elif op == 'LESS_OR_EQUAL':
        return data[data['Date'] <= time].index.values[-1]
    else:
        raise ValueError('op parameter value must be one of the following: '
        '[\'EQUAL\', \'GREATER_OR_EQUAL\', \'LESS_OR_EQUAL\'')