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
import pync
import os

from data_collection import *
from market import *
from trade import *
from parameters import *

#----------------------------------functions-----------------------------------

def backtest_trade_loop_1(
    locks: dict, 
    symbol: str, 
    interval: str, 
    paper_flag: bool,
    stop_loss: float):
    """
    Description: 
        Initiates a trade cycle (buys & waits til sold) for the specified 
        currency.
    Args:
        locks (dict): lock for making changes to current trades list
        symbol (str): symbol of currency to trade
        interval (str): symbol of currency to trade
        paper_flag (bool): interval of klines to be used for analysis 
        stop_loss (float): to indicate whether to use real or paper money
    Return: 
        None
    """
    if (not paper_flag):
        buy_id, sell_quantity = buy_trade(symbol, 15) #buy in
    
    buy_price = current_price_f(symbol)
    print(f"{GREY}BUY PRICE{WHITE}: {buy_price}") if (not cron_flag) else None
    start_time = time.time()
    print(f"Start: {get_time(start_time-8*3600)} - {start_time}\n") if \
        (not cron_flag) else None

    max_price = buy_price
    stop_price = buy_price*(1-stop_loss)
    
    while True:
        try:
            klines = download_to_csv(symbol, interval)
            current_price = klines.iloc[-1]['c']
            current_high = klines.iloc[-1]['h']
            
            max_price = max(max_price, current_high)
            
            if (current_price < stop_price): # if below stop loss take losses
                if (not paper_flag):
                    sell_trade(symbol, quantity=sell_quantity)
                sell_price = current_price_f(symbol)
                profit = get_profit(buy_price, sell_price, paper=paper_flag)
                profit_color = GREEN if profit > 0 else RED
                print(f"{profit_color}CRITERIA ACHIEVED{WHITE} selling " + \
                    f"{symbol}.") if (not cron_flag) else None
                print(f"{GREY}SELL PRICE{WHITE}: {sell_price}") if \
                    (not cron_flag) else None
                end_time = time.time()
                print(f"End: {get_time(end_time-8*3600)} - {end_time}\n", \
                      end='\r') if (not cron_flag) else None
                print(f"{profit_color}PROFIT{WHITE}: {profit}%\n") if \
                    (not cron_flag) else None
                break
            
            #top value - 'stop_loss' percent of buy in price
            stop_price = max_price - buy_price*stop_loss
            time.sleep(30)
            
        #incase loss of network during trade
        except (requests.ConnectionError, requests.Timeout) as exception:
            lost_connection_sleep(60, 1 if (len(sys.argv) > 1) else \
                os.get_terminal_size().columns) #sleep for 60 seconds
        
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


def run_method(buy_in_gain_param: float, risk_reward_ratio: float, 
               backtest_flag: bool=False):
    """
    Description: 
        Runs Method 1 with specified parameters.
    Args:
        buy_in_gain_param (float): gain required for trade buy in
        risk_reward_ratio (float): risk to reward ratio for calculating 
        stop loss
        backtest_flag (bool=False): true if backtesting false otherwise
    Returns: 
        None
    """
def init_backtest_1(buy_in_gains: list=None, risk_reward_ratios: list=None, 
    
    #Parameters
    global buy_in_gain
    global current_trades
    global cron_flag #true if running from crontab (only print certain lines)
    
    #gain required in 5 minute period for buy in
    buy_in_gain = buy_in_gain_param  
    interval = '1m' #candle interval used in analysis
    paper_flag = True #if true than using paper money, else using real money
    current_trades = [] #list of symbols that are currently being traded
    terminal_width = 1 if (len(sys.argv) > 1) else \
        os.get_terminal_size().columns #width of terminal window
    cron_flag = (len(sys.argv) > 1)
    
    locks = { #locks for thread synchronization
        'current_trades': threading.Lock(),
        'profits_file': threading.Lock(),
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
                                    target=trade_loop,
                                    args=[
                                        locks,
                                        coin,
                                        interval,
                                        paper_flag,
                                        buy_in_gain/risk_reward_ratio]),
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

if __name__ == '__main__': #only run main when running this file as main
    
    buy_in_gains = [10]
    risk_reward_ratios = [1]
    
    pync.notify(f"Buy-In Gain: {','.join([str(g) for g in buy_in_gains])}%", 
                title="Starting CryptoBotV2")
    threading.current_thread().name = "Thread-MAIN"
    
    try:
        for gain in buy_in_gains:
            for risk_reward_ratio in risk_reward_ratios:
                run_method(buy_in_gain_param=gain, stop_loss=risk_reward_ratio)
    except KeyboardInterrupt:
        print(f"\n{GREY}STATUS {WHITE}Finishing Program. Thread Count: " + 
              f"{threading.active_count()}") if (not cron_flag) else None
        sys.exit()
    finally:
        pync.notify(f"Ending Main of Program", title="Finishing CryptoBotV2")
