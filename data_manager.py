import pandas as pd

'''
This class takes care of data menagement, it also serves as a wrapper around a library used for data processing.
Only this class is dependant on data structure and framework used to process data
'''
class DataManager:
    def __init__(self, data=None):
        self.data = data
        self.data_file = ""

    def load_data(self, file: str, index_col=0) -> None:
        if (self.data_file != file):
            self.data = pd.read_csv(file, index_col=index_col, parse_dates=True)
            self.data_file = file
            # use plain integer index => in order to remove time gaps and easier plot of indicators
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

    '''
    Operators
    '''
    def __eq__(self, other):
        return self.data == other
    def __lt__(self, other):
        return self.data < other
    def __gt__(self, other):
        return self.data > other
    def __le__(self, other):
        return self.data <= other
    def __ge__(self, other):
        return self.data >= other
    def __ne__(self, other):
        return self.data != other

    def __len__(self):
        return self.data.shape[0]

    def reverse(self):
        self.data = self.data[::-1]
        self.data.reset_index(inplace=True, drop=True)

'''
This class is used as interface to access data in user code
It is a wrapper around pandas DataFrame, current candle is a DataFrame with a single entry
'''
class DataView:
    def __init__(self, dataframe, current_candle = None):
        self.dataframe = dataframe
        self.current_candle = current_candle

    def __getitem__(self, item):
        if type(item) == int:
            if self.current_candle is None:
                return self.dataframe.iloc[item]    
            elif item == 0:
                return self.current_candle
            else:
                return self.dataframe.iloc[item-1]
        elif type(item) == slice:
            if self.current_candle is None:
                return DataView(self.dataframe[item])
            elif item.start == 0:
                return DataView(self.dataframe[item.start+1:item.stop], self.current_candle)
            else:
                return DataView(self.dataframe[item])
        else:
            raise TypeError("Invalid argument type.")


data = DataManager()
tick_data = DataManager()

if __name__ == '__main__':
    data_file = 'data/EURUSD/EURUSD60.csv'
    data.load_data(data_file)
    time = data.data.loc[data.data['Date'] >= '2019-1-3 00:00'].iloc[0].Date