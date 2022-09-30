import pandas as pd

'''
This class takes care of data menagement, it also serves as a wrapper around a library used for data processing.
Only this class is dependant on data structure and framework used to process data
'''
class DataManager:
    def __init__(self, data=None):
        self.data = data

    def load_data(self, file: str, index_col=0) -> None:
        self.data = pd.read_csv(file, index_col=index_col, parse_dates=True)
        # use plain integer index
        self.data = self.data.reset_index(drop=False)

    '''
    Dereference operator - []
    When dereferencing a single data point or data frame, it passes down real data implementation from library,
    since it should be used as normal int, float, datetime or some other data type
    '''
    def __getitem__(self, item):
        if type(item) == int and type(self.data) != pd.DataFrame:
            return self.data[item]
        elif type(item) == int and type(self.data) == pd.DataFrame:
            return self.data.iloc[item]
        else:
            return DataManager(self.data[item])

    '''
    Property operator - .
    '''
    def __getattr__(self, key):
        if key == 'index':
            return self.data.__getattr__(key).values
        else:
            return self.data.__getattr__(key)

data = DataManager()