#!/usr/bin/python3
#
# method_2.py: contains functions for method 2 of crypto bot version 2.
#
# Andrew Bishop
# 2022/02/28
#

# modules imported
import sys
import threading
import pync
import time
import os
import logging
from multiprocessing import Pool
from pprint import pprint, pformat

from helper_functions.data_collection import *
from helper_functions.market import *
from helper_functions.trade import *
from helper_functions.analysis import *
from helper_functions.websocket_func import *
from constants.parameters import *
from methods.method_2.method_2_backtest import *
from methods.method_2.method_2_classes import *
from methods.method_2.method_2_func import *

logger = logging.getLogger("main")

#------------------------------------TODOs-------------------------------------

# TODO: add end of trade check to see if trade criterias are still met, then don't sell if they are

# TODO: minimize requests to API by saving to file and use locks

# TODO: FIX MAJOR BUG: if there is an error in buy trade and the transaction does not go through, trade locks will be held in locked mode forever

# TODO: modify main so that multiple parameters can trade at the same time. To do this also need to add multiple profit files for each method. Perhaps name each method based on parameters.

# TODO: make orders log file write to csv file

# TODO: improve system to not trade when trade is active (fix criticals popping up)

# TODO: add daily email notifications with logs of profits, criticals, errors, warnings and other important informtaion

# TODO: plot matplotlib graph when bought in and show updating candles with horizontal lines at stop, profit and buy points. Have it update as time goes on and close the window when the trade is done.

# TODO: implement automated staking into program (probably need to use kraken)

# TODO: implement cli into program for more terminal options

# TODO: replace all print statements with logger statements

# TODO: implement dataclasses in

# TODO: calculate S&P 500 for crypto coins and use historical data to see how the coin would have performed.

# TODO: convert setup functions so that different assets can be traded other than USDT. (ie. BNB, BTC, ETH, etc.)

# TODO: implement UI

# TODO: implement multiple parameters can be traded at a time

# TODO: implement database structure for data?

# TODO: add trades.csv and run similar to profits.csv so that if the program crashes you can still see if there was an existing trade and then continue with it

# TODO: rewrite main so that multiple parameters for live trading can be run at once, need async websocket connection for data

# TODO: change threading lock to dictionary full of all threading locks

# TODO: create a Trade class that contains all trade information (to make it easier to pass the information around)

# TODO: for log profits, send Trade (class/dataclass) with all attributes instead of 10 arguments alone

# TODO: add check to see if there are any new coins in top gainers that can have new threads created for them

# TODO: add stop loss check to see if it is outside one standard deviation of the last hour, if so, make that the stop loss

# TODO: add dynamic stop loss that changes to maximum - stop loss percent and changes as price changes

#----------------------------------functions-----------------------------------

def main(symbols: list, trade_quote_qty: float=None):
    """
    Description:
        Starts all the threads for the main function of method 2.
    Args:
        symbols (list): symbols to trade in main.
        trade_quote_qty (float, optional): amount of money (USD) to risk on each trade. Defaults to None.
    """
    threading.current_thread.name = "MAIN-Thread"
    threads_list = []
    
    # delete old live data
    delete_old_data()
    # dictionary of all locks
    method_lock = MethodLock(fake=(("fake" in sys.argv) and not ("real" in sys.argv)))
    
    symbols = list(symbols)
    if "real" in sys.argv:
        logger.critical("Starting REAL trading program.")
    elif "fake" in sys.argv:
        logger.critical("Starting UNLIMITED trading program.")
    logger.info(f"Number of Coins Listed: {len(symbols)}")
    
    for symbol in symbols:
        if symbol[-4:] != "USDT":
            logger.debug(f"Skipping {symbol}.")
            symbols.remove(symbol)
            continue
        threads_list += [threading.Thread(target=live_method_2, args=[symbol, trade_quote_qty, method_lock], daemon=True)]
        threads_list[-1].name = f"{symbol}-Thread"
        threads_list[-1].start()
        logger.debug(f"Starting {threads_list[-1].name}.")
        time.sleep(2)
    
    time.sleep(30)
    thread_count = threading.active_count()
    while True:
        current_count = threading.active_count()
        time_now = datetime.utcfromtimestamp(time.time()-7*3600).strftime('%H:%M')
        if current_count != thread_count:
            for t in threads_list:
                if not t.is_alive():
                    logger.warning(f"{t.name} is not responding. Active Thread Count: {threading.active_count()}")
                    threads_list.remove(t)
                    break
        elif (":59" in time_now) or (":00" in time_now):
            logger.info(f"Hourly Update. Thread Count: {threading.active_count()}")
                    
        time.sleep(2*60)

def live_method_2(
        symbol: str, 
        trade_quote_qty: float, 
        method_lock: MethodLock):
    """
    Description:
        Runs method 2 with live candles. To sell entire balance on each trade 
        pass None as parameter for trade_quote_qty. Otherwise, for a set price 
        pass the set price.
    Args:
        symbol (str): coin to trade
        trade_quote_qty (float): amount of money to trade per trade
        locks (list): list of all threading locks
        logger (logging.Logger): 
    Raises:
        e: any error during main event loop.
    """

    # real money flag
    real_money = ("real" in sys.argv)

    # EMA windows
    low_w = 8
    mid_w = 13
    high_w = 21
    
    # minimum profit % for trade
    min_profit = 0.65
    
    # lock for accessing kline data files
    data_lock_1h = threading.Lock()
    data_lock_5m = threading.Lock()
    
    # connect 1h and 5m websockets
    data_thread_1h = connect_websocket(symbol, "1h", data_lock_1h, limit=high_w)
    data_thread_5m = connect_websocket(symbol, "5m", data_lock_5m, limit=high_w)
    
    time.sleep(5)
    
    while data_lock_1h.locked() or data_lock_5m.locked():
        time.sleep(1)
    
    # indicates whether trade is active in the current thread (locally)
    trade_active = False
    # indicates whether the program is just starting
    init_flag = True 
    
    # start backtest loop
    try:
        while True:
            
            # ================================================================
            # ================================================================
            #                       INITIALIZATION STAGE
            # ================================================================
            # ================================================================
        
            # allow stream to reset after 24h
            time_now = datetime.utcfromtimestamp(time.time()-7*3600).strftime('%H:%M')
            if time_now == "11:30":
                # lock here to prevent all new websockets from being started at the same time
                method_lock.profit_file.acquire()
                data_thread_1h = connect_websocket(symbol, "1h", data_lock_1h, limit=high_w)
                data_thread_5m = connect_websocket(symbol, "5m", data_lock_5m, limit=high_w)        
                time.sleep(2)
                method_lock.profit_file.release()
            
            # risk multiplier
            risk_multiplier = 1
            # profit split ratio
            profit_split_ratio = 0
            
            # if data threads die, restart them
            if not data_thread_1h.is_alive():
                logger.info(f"Restarting {symbol}/1h Websocket.")
                data_thread_1h = connect_websocket(symbol, "1h", data_lock_1h, limit=high_w)
            if not data_thread_5m.is_alive():
                logger.info(f"Restarting {symbol}/5m Websocket.")
                data_thread_5m = connect_websocket(symbol, "5m", data_lock_5m, limit=high_w)
                  
            # restart loop if there is a trade currently running on different thread
            if method_lock.active_trade.locked() and (not trade_active):
                time.sleep(20)
                continue
                  
            if (not init_flag):
                time.sleep(2)
            else:
                init_flag = False #continue to next line for first iteration
                
            # ================================================================
            # ================================================================
            #                     DOWNLOADING DATA STAGE
            # ================================================================
            # ================================================================
            
            # download 1h klines, only download 1h if no currently active trade
            # (dont need 1h for active_trade)
            while True and (not trade_active):
                try:
                    long_klines = update_klines(symbol, "1h", data_lock_1h)
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Could Not Download 1h {symbol}.")
                    time.sleep(15)
                else:
                    if len(long_klines) < high_w:
                        logger.error(f"Not Enough 1h Klines. Terminating Thread. Short Klines: {len(short_klines)}, Need: {high_w}", exc_info=True)
                        return
                    break

            # download 5m klines
            while True:
                try:
                    short_klines = update_klines(symbol, "5m", data_lock_5m)
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Could Not Download 5m {symbol}.")
                    time.sleep(15)
                else:
                    if len(short_klines) < high_w:
                        logger.error(f"Not Enough 5m Klines. Terminating Thread. Short Klines: {len(short_klines)}, Need: {high_w}", exc_info=True)
                        return
                    break
            
            # calculate long EMA values
            long_EMAs = pd.DataFrame([
                EMA(long_klines['c'], low_w),
                EMA(long_klines['c'], mid_w),
                EMA(long_klines['c'], high_w)
                ], index = [low_w, mid_w, high_w])
            
            # calculate short EMA values
            short_EMAs = pd.DataFrame([
                EMA(short_klines['c'], low_w),
                EMA(short_klines['c'], mid_w),
                EMA(short_klines['c'], high_w)
                ], index = [low_w, mid_w, high_w])
            
            # ================================================================
            # ================================================================
            #                         BUYING STAGE
            # ================================================================
            # ================================================================
            
            current_kline = short_klines.iloc[-1] # current candle
            current_price = current_kline['c'] # current price
            
            # SKIP BUYING STAGE IF ALREADY BOUGHT IN
            if (not trade_active):
                
                # Criteria 1: 1h -> 8 EMA > 21 EMA)
                criteria_1 = (long_EMAs.loc[8, high_w-1] > long_EMAs.loc[21, high_w-1])
                if not criteria_1:
                    continue
                # Criteria 2: 5m -> 8 EMA > 13 EMA > 21 EMA
                criteria_2 = (short_EMAs.loc[8, high_w-1] > short_EMAs.loc[13, high_w-1]) and (short_EMAs.loc[13, high_w-1] > short_EMAs.loc[21, high_w-1])
                if not criteria_2:
                    continue
                # Criteria 3: 5m -> price > 8 EMA (last kline)
                criteria_3 = (current_kline['h'] > short_EMAs.loc[8, high_w-2])
                if not criteria_3:
                    continue
                # Criteria 4: 5m -> price < 8 EMA (current kline)
                criteria_4 = (current_kline['l'] < short_EMAs.loc[8, high_w-1])
                if not criteria_4:
                    continue
                # Criteria 5: 5m -> low > 21 EMA (current kline)
                criteria_5 = (current_kline['l'] > short_EMAs.loc[21, high_w-1])
                if not criteria_5:
                    continue
                # Criteria 6: potential profit must be greater than min profit difference of 1h EMA over buy price
                buy_price = float(get_current_price(symbol))
                stop_price = min(short_klines.loc[high_w-5:high_w-1,'l'])
                percent_profit = buy_price/stop_price-1
                if not (percent_profit*100 > min_profit):
                    continue
                
                # save 1h difference
                difference_1h = (long_EMAs.loc[low_w, high_w-1] - long_EMAs.loc[high_w, high_w-1]) / buy_price * 100
                # check for active trade in other thread
                if method_lock.active_trade.locked():
                    continue
                
                # if using real money for trade
                if real_money:
                    balance = account_balance("USDT")
                    # 12 is smallest possible trade if not specified
                    min_balance = 12 if (not trade_quote_qty) else trade_quote_qty
                    # use full balance if quote quantity not specified
                    if (not trade_quote_qty):
                        trade_quote_qty = balance
                    # dont buy in if balance is too small for trade and continue
                    if (balance < min_balance):
                        logging.warning(f"Insufficient Balance for Buy-In. Have: {round(balance, 4)}, Need: {min_balance}. Waiting for 20s.")
                        time.sleep(20)
                        continue

                # wait for 30 if cannot acquire lock then continue
                if not method_lock.active_trade.acquire(timeout=30):
                    continue
                
                # buy into trade
                if real_money:
                    buy_id, profit_quantity = buy_trade(symbol=symbol, quote_quantity=trade_quote_qty)
                buy_time = int(time.time()-7*3600)
                # activate flag because trade is active in this thread
                trade_active = True
                
                # calcualte profit price
                profit_price = buy_price*(1+percent_profit*risk_multiplier)
                # calculate stop price
                stop_price = buy_price*(1-percent_profit)
                
                # ------------------- RECORD ALL TRADE DATA ------------------
                
                # index for which take profits have been reached
                profit_index = 1
                # short window closing candle values
                short_closing = short_klines.loc[:, 'c']
                # standard deviation of last 15 short values
                std_5m = short_closing[high_w-15:high_w-1].std()
                # 24h daily ticker
                ticker = daily_ticker_24hr(symbol)
                # 24h volume
                volume_24h = float(ticker['volume'])
                # relative volume
                volume_rel = short_klines.loc[:, 'v'].iloc[-6:]
                volume_rel = round(volume_rel.sum()*48/volume_24h*100,2)
                # 24h price change percent
                price_24h = float(ticker['priceChangePercent'])
                # max price
                max_price = current_price
                # min price
                min_price = current_price
                # log data
                if real_money:
                    logger.info(f"BUY ID: {buy_id}")
                logger.info(f"PRICE: {round(buy_price,4)} - STOP PRICE: {round(stop_price,4)} - PROFIT PRICE: {round(profit_price,4)} - PROFIT %: {round(percent_profit*risk_multiplier*100,2)}%")
                continue
            
            # ================================================================
            # ================================================================
            #                         SELLING STAGE
            # ================================================================
            # ================================================================

            # SKIP SELLING STAGE IF HAVE NOT BOUGHT IN YET
            if trade_active:
                
                logger.debug(f"{symbol} CURRENT PRICE: {current_price}, {round((profit_price/current_price-1)*100, 2)}, {round((stop_price/current_price-1)*100, 2)}")
                # update max price
                max_price = max(max_price, float(current_kline['h']))
                # update min price
                min_price = min(min_price, float(current_kline['l']))

                # ------------------------- STOP LOSS ------------------------
                if (current_price < stop_price): # if stop loss is reached
                    profit = ((current_price / buy_price) - 1) if (profit_index < 2) else 0
                    logger.info(f"{symbol} LOSS: {'{:.4f}'.format(profit*100)}%")

                    if real_money:
                        # sell out of trade (stop loss)
                        sell_id = sell_trade(symbol=symbol, quantity=profit_quantity)[0]
                        logger.info(f"SELL ID: {sell_id}")

                    if (profit_index < 2):
                        log_profits(
                            "{:.4f}".format(profit*100), 
                            symbol, 
                            buy_price, 
                            current_price,
                            buy_time, 
                            int(time.time()-7*3600), 
                            "S", 
                            profit_split_ratio, 
                            "{:.4f}".format(std_5m), 
                            "{:.4f}".format(difference_1h), 
                            price_24h,
                            volume_24h,
                            volume_rel,
                            risk_multiplier,
                            min_price,
                            max_price,
                            round((max_price/buy_price-1)*100, 4),
                            round(abs(min_price/buy_price-1)*100, 4),
                            round(percent_profit*100,4),
                            method_lock.profit_file, 
                            real=real_money)
                    continue

                # ------------------------ TAKE PROFIT -----------------------
                elif (current_price > profit_price):
                    # divide by profit index because quantity decays each time
                    profit = (current_price / buy_price) - 1
                    
                    # divide new profit by ratio and index
                    if profit_split_ratio:    
                        # if proposed profit for profit split is lower than 
                        # min, sell all quantity
                        split_profit = profit*((1 - profit_split_ratio) / profit_index)
                        if (split_profit > min_profit):
                            profit = split_profit
                        else:
                            method_lock.active_trade.release()
                            trade_active = False
                    else:
                        method_lock.active_trade.release()
                        trade_active = False

                    if real_money:
                        profit_quantity *= (1 - profit_split_ratio)
                        # sell out of trade (take profit)
                        sell_id = sell_trade(symbol=symbol, quantity=profit_quantity)[0]
                        logger.info(f"SELL ID: {sell_id}")
                        # if not profit split ratio then trade is done
                        if not profit_split_ratio:
                            # release lock and set local trade flag to false
                            method_lock.active_trade.release()
                            trade_active = False

                    #display_profit(symbol, profit_index, profit)
                    logger.info(f"{symbol} PROFIT {profit_index}: {'{:.4f}'.format(profit*100)}%")

                    log_profits(
                        "{:.4f}".format(profit*100), 
                        symbol, 
                        buy_price, 
                        current_price, 
                        buy_time, 
                        int(time.time()-7*3600), 
                        f"P{profit_index}",
                        profit_split_ratio, 
                        "{:.4f}".format(std_5m), 
                        "{:.4f}".format(difference_1h), 
                        price_24h,
                        volume_24h,
                        volume_rel,
                        risk_multiplier,
                        min_price,
                        max_price,
                        round((max_price/buy_price-1)*100, 4),
                        round(abs(min_price/buy_price-1)*100, 4),
                        round(percent_profit*100, 4),
                        method_lock.profit_file, 
                        real=real_money)

                    if profit_split_ratio:
                        # new stop is original buy price
                        stop_price = buy_price 
                        # new buy is og profit price
                        buy_price = profit_price 
                        # new profit is new buy + percent profit
                        profit_price = buy_price * (1 + percent_profit)
                        # increment profit index
                        profit_index += 1
                        
    except RuntimeError as e:
        logger.warning(f"Runtime Error. Need to unlock lock. Retrying in 20s.", exc_info=True)
        time.sleep(20)
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"Connection Error. Retrying in 20s.", exc_info=True)
        time.sleep(20)
    except Exception as e:
        logger.error(f"Exception raised in thread. Thread Count: {threading.active_count()}", exc_info=True)
        if real_money:
            pync.notify(threading.current_thread().name, title="ERROR")
        raise e