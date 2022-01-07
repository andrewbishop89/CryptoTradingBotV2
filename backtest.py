#!/usr/bin/python3
#
# backtest.py: contains all the functions for backtesting.
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
import sys
import threading
from method_1 import trade_loop_1
import pync
import os
from multiprocessing import Pool
import multiprocessing
from datetime import date

from data_collection import *
from market import *
from trade import *
from parameters import *

#----------------------------------functions-----------------------------------

def backtest_trade_loop_1(
    symbol,
    klines,
    stop_loss):
    
    buy_price = current_price_f(klines[0]['c'])
    start_time = klines[0]['t']

    max_price = buy_price
    stop_price = buy_price*(1-stop_loss)
    
    for backtest_index in range(len(klines)):
        klines = klines.iloc[backtest_index]
        current_price = klines.iloc[backtest_index]['c']
        current_high = klines.iloc[backtest_index]['h']
        
        max_price = max(max_price, current_high)
        
        if (current_price < stop_price): # if below stop loss take losses
            sell_price = stop_price
            profit = get_profit(buy_price, sell_price, paper=True)
            end_time = klines.iloc[backtest_index]['t']
            
            date_today = date.today()
            file_path = os.path.join("logs", "backtest_logs", f"{date_today}.csv")
            if not os.path.isfile(file_path):
                with open(file_path, 'w') as f:
                    f.write("profit,symbol,buy_in_gain,interval,stop_loss," + \
                        "buy_price,sell_price,start_time,end_time")
            
            add_row_to_csv(
                file_path = os.path.join("logs", "backtest_logs", \
                    f"{date_today}.csv"), 
                data = [
                        profit,
                        symbol,
                        buy_in_gain,
                        "1m",
                        stop_loss,
                        buy_price, 
                        sell_price, 
                        start_time, 
                        end_time
                    ])
            
            return

        
        #top value - 'stop_loss' percent of buy in price
        stop_price = max_price - buy_price*stop_loss
  
  
  
  
        
    lock_1_flag = False
    lock_2_flag = False
    while True:
        if not lock_1_flag: #if lock 1 task not done yet
            if not locks['current_trades'].locked(): #wait until lock is open
                #lock and remove symbol from current trades
                locks['current_trades'].acquire()
                current_trades.remove(symbol) 
                locks['current_trades'].release()
                lock_1_flag = True #flag is true to mark task is completed
        if not lock_2_flag: #if lock 2 task not done yet
            if not locks['profits_file'].locked(): #wait until lock is open
                #lock and add profit data to profits file 
                locks['profits_file'].acquire()
                add_row_to_csv(
                    file_path = os.path.join("logs", "profits.csv"), 
                    data = [
                        profit,
                        symbol,
                        buy_in_gain,
                        interval,
                        stop_loss,
                        buy_price, 
                        sell_price, 
                        start_time, 
                        end_time
                    ])
                locks['profits_file'].release()
                lock_2_flag = True  # flag is true to mark task is completed
        if (lock_1_flag and lock_2_flag): #if both locked tasks are done
            break #break to finish trade cycle

    return

def backtest_symbols(amount: int=30, limit: int=1000) -> list:
    """
    Description:
        Finds and downloads the last 'limit' candles of the top 'amount' 
        symbols for backtesting.
    Args:
        amount (int, optional): amount of symbols to return (defaults to 30)
        limit (int, optional): amount of candles to download (defaults to 1000)
    Returns:
        list: list of top 'amount' symbols
    """
    gainers = top_gainers()
    top_symbols = list(gainers.head(amount).index)
    with Pool(processes=os.cpu_count()) as p:
        p.starmap(download_for_backtest, 
            [(symbol, '1m', limit) for symbol in top_symbols])
        
    return top_symbols


def backtest_1(symbol: str, gain: float, ratio: float, 
        file_lock: bool, coin_lock: bool): 
    
    klines = get_saved_klines(symbol, "1m", historical=True)
    for backtest_index in range(4, len(klines)): #main backtest loop
        
        #only analyze last 5 candles
        last_klines = klines.iloc[backtest_index-5:backtest_index] 
        for index in range(1,5):
            try:
                #if bearish candle, skip this index
                if (last_klines.iloc[-index]['c'] < \
                    last_klines.iloc[-index]['o']): 
                    continue
            except IndexError: #incase coin has less than 5 candles
                break
            else:
                gain = last_klines.iloc[-1]['c']/ \
                    last_klines.iloc[-index]['o']
                max_gain = max(gain, max_gain)
                if (gain > (1+buy_in_gain/100)):
                    trade_loop_1(
                        klines.iloc[backtest_index:], 
                        stop_loss=gain/ratio)
                    backtest_index += 5
    
    return


def init_backtest_1(buy_in_gains: list=None, risk_reward_ratios: list=None, 
        symbols: list=None):
    
    """TODO"""

    file_lock = multiprocessing.Lock() #lock for writing to logs file
    
    symbol_locks = {} #for reading candles from each coins file
    for symbol in symbols:
        symbol_locks[symbol] = multiprocessing.Lock()

    #cycle through all combinations for input parameters
    backtest_parameter_combinations = []
    for gain in buy_in_gains: 
        for ratio in risk_reward_ratios:
            #WARNING to avoid concurrency problems, symbols must be iterated through last here
            for symbol in symbols: 
                backtest_parameter_combinations.append((symbol, gain, ratio, 
                    file_lock))
                
    process_count = min(os.cpu_count(), len(symbols))
    with Pool(processes=process_count) as p:
        p.starmap(backtest_1, backtest_parameter_combinations)
                    
    print("Backtesting Complete")


    
    
    #Parameters
    global buy_in_gain
    global current_trades
    
    #gain required in 5 minute period for buy in
    buy_in_gain = buy_in_gain_param  
    interval = '1m' #candle interval used in analysis
    paper_flag = True #if true than using paper money, else using real money
    current_trades = [] #list of symbols that are currently being traded
    terminal_width = 1 if (len(sys.argv) > 1) else \
        os.get_terminal_size().columns #width of terminal window
    cron_flag = (len(sys.argv) > 1)
    
    locks = { #locks for thread synchronization
        'current_trades': multiprocessing.Lock(),
        'profits_file': multiprocessing.Lock(),
    }
    
    print(f"{GREY}STARTING PROGRAM{WHITE}\nBuy-in Gain: {buy_in_gain}%\n" + 
        f"Paper: {paper_flag}\n") if (not cron_flag) else None
    
    # MAIN LOOP
    while True:
        try: #try-except for handling loss of internet connection
        
            #find coins to trade
            top_coins = top_gainers(buy_in_gain)
            max_gain = 1
            
            #copying list to prevent collisions
            locks['current_trades'].acquire() 
            current_trades_copy = current_trades.copy()
            locks['current_trades'].release()
            
            #if coin already being traded, skip it
            for coin in current_trades_copy:
                if coin in top_coins:
                    top_coins.drop(coin)
            del current_trades_copy
            
            for coin in top_coins.index:
                init_coin(coin, interval) #if new coin, create file for data
                klines = download_to_csv(coin, interval, 5) #download candles
                
                last_klines = klines.tail(5) #only analyze last 5 candles
                for index in range(1,5):
                    try:
                        #if bearish candle, skip this index
                        if (last_klines.iloc[-index]['c'] < \
                            last_klines.iloc[-index]['o']): 
                            continue
                    except IndexError: #incase coin has less than 5 candles
                        break
                    else:
                        gain = last_klines.iloc[-1]['c']/ \
                            last_klines.iloc[-index]['o']
                        max_gain = max(gain, max_gain)
                        if (gain > (1+buy_in_gain/100)):
                            print(f"{GREY}CRITERIA ACHIEVED{WHITE} buying " +
                                f"into {coin}.") if (not cron_flag) else None
                            #add coin to current trades
                            locks['current_trades'].acquire()
                            current_trades.append(coin)
                            locks['current_trades'].release()
                            #creating trade loop thread for coin
                            start_trade(
                                thread=threading.Thread(
                                    target=backtest_trade_loop_1,
                                    args=[
                                        locks,
                                        coin,
                                        interval,
                                        paper_flag,
                                        buy_in_gain,
                                        risk_reward_ratio]),
                                symbol=coin)
                            
                            break
            
            #print current program status (statistics)
            current_string = format_string_padding(
                f"Number of Coins: {len(top_coins)}",
                terminal_width=terminal_width)
            current_string += format_string_padding(
                f" Last Max Gain: {round(max_gain*100-100,2)}%",
                terminal_width=terminal_width)
            current_string += format_string_padding(
                f" Thread Count: {threading.active_count()}",
                terminal_width=terminal_width)
            #subtract 8*3600 to convert from UTC to GMT-8 time
            current_string += format_string_padding(
                f" Time: {get_time(time.time()-8*3600)}",
                terminal_width=terminal_width)
            print(current_string) if (not cron_flag) else None

            #change sleep time depending on last measure max gain
            if (max_gain > buy_in_gain*0.9):
                time.sleep(30)
            elif (max_gain > buy_in_gain*0.7):
                time.sleep(60)
            elif (max_gain > buy_in_gain*0.5):
                time.sleep(90)
            elif (max_gain > buy_in_gain*0.3):
                time.sleep(120)
            else:
                time.sleep(240)
            
        #incase a network connection error is raised
        except (requests.ConnectionError, requests.Timeout) as exception:
            lost_connection_sleep(300, terminal_width=terminal_width)


#------------------------------------main--------------------------------------

if __name__ == '__main__':
    
    # ---- Backtest Parameters ----
    
    #minimum multiplier to buy in at
    backtest_buy_in_gains = [4, 5, 8, 10, 15]
    #risk to reward ratios for stop loss calculations
    backtest_risk_reward_ratios = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, \
        2.5, 3]
    #number of coins to backtest
    backtest_symbols_amount = 10
    #number of candles for each coin to backtest
    backtest_klines_limit = 5_000
    
    pync.notify(f"Starting Backtesting " +
        f"({len(backtest_buy_in_gains)*len(backtest_risk_reward_ratios)}).", 
        title="CryptoBotV2") #notification for program start
    threading.current_thread().name = "Thread-MAIN" #rename main thread
    
    try:
        init_backtest_1( #init and prepare all variables for backtest
            buy_in_gains=backtest_buy_in_gains,
            risk_reward_ratios=backtest_risk_reward_ratios,
            klines=backtest_klines(backtest_symbols_amount, 
                backtest_klines_limit))
        
    except KeyboardInterrupt: #incase of keyboard interrupts during execution
        print(f"\n{GREY}STATUS {WHITE}Finishing Program. Thread Count: " + 
              f"{threading.active_count()}")
        sys.exit()
    finally: #notify user that program is ending
        pync.notify(f"Ending Main of Program (Backtesting)", 
            title="CryptoBotV2")
