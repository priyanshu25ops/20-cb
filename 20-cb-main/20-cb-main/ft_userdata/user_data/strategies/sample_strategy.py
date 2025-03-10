import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter

class SampleStrategy(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = False
    
   
    minimal_roi = {"0": 0.04}
    stoploss = -0.10
    timeframe = "5m"
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 20  

    lookback_period = IntParameter(10, 30, default=20, space="buy", optimize=True)
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate the rolling highest high for the lookback period
        """
        # Calculate highest high of previous 20 candles (excluding current candle)
        dataframe['highest_high'] = dataframe['high'].shift(1).rolling(window=self.lookback_period.value).max()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter long when current candle breaks highest high of previous 20 candles
        """
        dataframe.loc[
            (dataframe['high'] > dataframe['highest_high']) &  
            (dataframe['volume'] > 0),  
            'enter_long'
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Implements multi-level exit strategy with risk-reward ratios
        """
        dataframe['exit_long'] = 0.0
        
        for i in range(len(dataframe)):
            if dataframe.iloc[i].enter_long:
                entry_price = dataframe.iloc[i].close
                stop_loss = dataframe.iloc[i].low  # SL at entry candle's low
                
               
                rr_levels = {
                    2: 0.3,  # 30% at 1:2 RR
                    4: 0.3,  # 30% at 1:4 RR
                    10: 0.4  # 40% at 1:10 RR
                }
                
               
                exited = False
                for rr, portion in rr_levels.items():
                    exit_price = entry_price + (entry_price - stop_loss) * rr
                   
                    for j in range(i+1, len(dataframe)):
                        if dataframe.iloc[j].high >= exit_price:
                            dataframe.iat[j, dataframe.columns.get_loc('exit_long')] += portion
                            exited = True
                            break
                            
               
                if not exited and dataframe.iloc[-1].exit_long == 0:
                    dataframe.iat[-1, dataframe.columns.get_loc('exit_long')] = 1.0
                    
        return dataframe