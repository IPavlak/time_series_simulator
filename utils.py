from importlib import util

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
        return data[data['Date'] == time].index[0]
    elif op == 'GREATER_OR_EQUAL':
        return data[data['Date'] >= time].index[0]
    elif op == 'LESS_OR_EQUAL':
        return data[data['Date'] <= time].index[-1]
    else:
        raise ValueError('op parameter value must be one of the following: '
        '[\'EQUAL\', \'GREATER_OR_EQUAL\', \'LESS_OR_EQUAL\'')

def get_idx_from_time(time, data, curr_idx):
    last_time = data.Date[curr_idx]
    step = 0
    if last_time < time: step = 1
    elif last_time > time: step = -1
    data_idx = curr_idx + step

    while (step > 0 and data.Date[data_idx] <= time) or \
          (step < 0 and data.Date[data_idx] >= time):
        data_idx += step
    data_idx -= step

    return data_idx

def import_module(module: str):
    from os.path import abspath

    if module.endswith('.py'):
        module = abspath(module)
        module_name = module.split('/')[-1].rstrip('.py')
        spec = util.spec_from_file_location(module_name, module)
    else:
        spec = util.find_spec(module)

    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def to_dict(obj):
        d = {}
        for member in dir(obj):
            if not callable(getattr(obj, member)) and not member.startswith('__'):
                value = getattr(obj, member)
                if isinstance(value, dict):
                    d[member] = to_dict(value)
                else:
                    d[member] = value
        return d
    
def update_from_dict(obj, d):
    for key, value in d.items():
        if hasattr(obj, key):
            member = getattr(obj, key)
            if isinstance(member, dict):
                member.update(value)
            elif member.__class__.__module__ == 'builtins':
                setattr(obj, key, value)
            elif isinstance(value, dict):
                update_from_dict(member, value)
            else:
                raise ValueError("Cannot parse from '{}' to '{}' (field name: '{}')".format(type(value), member, key))