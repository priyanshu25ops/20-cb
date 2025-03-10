import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, IntParameter

class SampleStrategy(IStrategy):
    max_open_trades = 1  
    max_open_trades_per_pair = 1  
    max_open_trades_per_pair_and_market = 1  
    max_open_trades_per_market = 1  
    
    INTERFACE_VERSION = 3
    can_short: bool = True  
    
    # Strategy Configuration
    minimal_roi = {"0": 0.1}  #
    stoploss = -0.10  
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count: int = 20  # Needs 20 candles 

    # Hyperparameters
    lookback_period = IntParameter(10, 30, default=20, space="buy", optimize=True)
    trailing_lookback = IntParameter(2, 5, default=3, space="buy", optimize=True)
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
      
       
        dataframe['highest_high'] = dataframe['high'].shift(1).rolling(window=self.lookback_period.value).max()
        
        
        dataframe['lowest_low'] = dataframe['low'].shift(1).rolling(window=self.lookback_period.value).min()
        
        
        dataframe['trailing_stop'] = dataframe['low'].rolling(window=self.trailing_lookback.value).min()
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter long when current candle breaks highest high of previous 20 candles
        Enter short when current candle breaks lowest low of previous 20 candles
        """
       
        dataframe.loc[
            (dataframe['high'] > dataframe['highest_high']) &  # Breakout condition 
            (dataframe['volume'] > 0),  
        ] = 1
        
        # Short entry condition: 
        dataframe.loc[
            (dataframe['low'] < dataframe['lowest_low']) &  # Breakdown condition 
            (dataframe['volume'] > 0), 
            'enter_short'
        ] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Implement trailing stop-loss based on the highest high of the last 3 candles for shorts
        Exit long if price falls below trailing stop
        Exit short if price rises above trailing stop
        """
        dataframe['exit_long'] = 0.0  
        dataframe['exit_short'] = 0.0  
        
     
        trailing_stop_level_long = None
        trailing_stop_level_short = None
        
        for i in range(len(dataframe)):
           
            if dataframe.loc[i, 'enter_long'] == 1:
              
                trailing_stop_level_long = dataframe.loc[i, 'trailing_stop']
            
          
            if trailing_stop_level_long is not None:
                trailing_stop_level_long = max(trailing_stop_level_long, dataframe.loc[i, 'trailing_stop'])
                
                
                if dataframe.loc[i, 'low'] < trailing_stop_level_long:
                    dataframe.loc[i, 'exit_long'] = 1.0  
                    trailing_stop_level_long = None  
            
          
            if dataframe.loc[i, 'enter_short'] == 1:
               
                trailing_stop_level_short = dataframe.loc[i, 'highest_high']
            
          
            if trailing_stop_level_short is not None:
                trailing_stop_level_short = min(trailing_stop_level_short, dataframe.loc[i, 'highest_high'])
                
             
                if dataframe.loc[i, 'high'] > trailing_stop_level_short:
                    dataframe.loc[i, 'exit_short'] = 1.0  
                    trailing_stop_level_short = None
                    
        return dataframe
