#!/usr/bin/python3
#
# method_framework.py: contains all objects to create a new method.
#
# Andrew Bishop
# 2022/05/30
#

# modules imported
from dataclasses import dataclass
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
from methods.method_2.method_2_func import *

logger = logging.getLogger("main")

#----------------------------------functions-----------------------------------

@dataclass
class MethodLock:
    """Contains all locks for a method."""
    file_lock = threading.Thread()

@dataclass
class Parameters:
    """Contains all parameters for a method."""
    symbol: str
    intervals: list
    windows: list # ascending order
    trade_active: bool # local flag, true when local trade is active
    
    kwargs: dict
    
@dataclass
class Data:
    """Contains all candle information"""
    symbol: str
    locks: MethodLock
    klines: pd.Series = None
    
    def update(self):
        # cycle through all intervals and update candles
        for interval in self.klines.index:
            self.klines[interval] = update_klines(self.symbol, interval, self.locks.file_lock)

@dataclass
class Method:
    """Contains functions to run a method as well as all parameters for the method."""
    parameters: Parameters
    locks: MethodLock
    trade_start: function
    trade_end: function
    
    def main(self):
        
        # connect all websockets needed for method
        for interval in self.parameters.intervals:
            connect_websocket(symbol=self.symbol, interval=interval, 
                file_lock=self.locks.file_lock, limit=max(self.parameters.windows))
            
        data = Data(self.parameters.symbol, self.locks)
        
        # main trade loop
        while True:
            # Update Data Stage
            data.update()
            # Buy In Stage
            if self.parameters.trade_active:
                self.trade_start(self.data, self.parameters, self.locks)
            # Sell Out Stage
            elif not self.parameters.trade_active:
                self.trade_end(self.data, self.parameters, self.locks)
            
            # Sleep
            time.sleep(self.parameters.sleep_time)
    
    symbol: str
    locks: MethodLock
    risk_multiplier: float  # risk factor for take profit on each trade
    profit_split_ratio: float  # amount of profit split and sold on each take profit
    args: list
    kwargs: dict
    low_w: int = 8  # short EMA window
    mid_w: int = 13  # medium EMA window
    high_w: int = 21  # long EMA window
    min_profit: float = 0.25  # smallest potential profit percent
    # bool for real money or paper money
    real_money: bool = ("real" in sys.argv)
    sleep_time: int = 2  # amount of time waited inbetween each loop
    trade_quote_qty: float = None  # amount of money traded per trade


@dataclass
class Parameters:  # containing the trade data for each live trade
    # Pre Trade Data
    symbol: str

    # During Trade Data
    buy_price: float
    profit_price: float
    stop_price: float
    std_5m: float
    volume_24h: float
    volume_rel: float
    price_24h: float
    buy_time: int

    # Post Trade Data
    profit: float
    sell_price: float
    sell_time: int
    side: str
    real: bool


@dataclass
class Trade:
    data: Data
    parameters: Parameters

    def buy(self):
        return

    def sell(self):
        return
    

def main(symbols: list, trade_quote_qty: float = None):
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
    locks = {
        "active_trade": threading.Lock(),
        "profit_file": threading.Lock()
    }

    symbols = list(symbols)
    if "real" in sys.argv:
        logger.critical("Starting REAL trading program.")
    logger.info(f"Number of Coins Listed: {len(symbols)}")

    for symbol in symbols:
        if symbol[-4:] != "USDT":
            logger.debug(f"Skipping {symbol}.")
            symbols.remove(symbol)
            continue
        threads_list += [threading.Thread(target=live_method_2,
                                          args=[symbol, trade_quote_qty, locks])]
        threads_list[-1].name = f"{symbol}-Thread"
        threads_list[-1].start()
        logger.debug(f"Starting {threads_list[-1].name}.")
        time.sleep(2)

    time.sleep(30)
    thread_count = threading.active_count()
    while True:
        current_count = threading.active_count()
        time_now = datetime.utcfromtimestamp(
            time.time()-7*3600).strftime('%H:%M')
        if current_count != thread_count:
            for t in threads_list:
                if not t.is_alive():
                    logger.warning(
                        f"{t.name} is not responding. Active Thread Count: {threading.active_count()}")
                    threads_list.remove(t)
                    break
        elif ("00" in time_now) or ("01" in time_now):
            logger.info(
                f"Hourly Update. Thread Count: {threading.active_count()}")

        time.sleep(2*60)


def live_method_2(
        symbol: str,
        trade_quote_qty: float,
        locks: list):
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
    min_profit = 0.60

    # lock for accessing kline data files
    data_lock_1h = threading.Lock()
    data_lock_5m = threading.Lock()

    # connect 1h and 5m websockets
    data_thread_1h = connect_websocket(
        symbol, "1h", data_lock_1h, limit=high_w)
    data_thread_5m = connect_websocket(
        symbol, "5m", data_lock_5m, limit=high_w)

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
            time_now = datetime.utcfromtimestamp(
                time.time()-7*3600).strftime('%H:%M')
            if time_now == "11:59":
                time.sleep(60)
                # lock here to prevent all new websockets from being started at the same time
                locks["profit_file"].acquire()
                data_thread_1h = connect_websocket(
                    symbol, "1h", data_lock_1h, limit=high_w)
                data_thread_5m = connect_websocket(
                    symbol, "5m", data_lock_5m, limit=high_w)
                time.sleep(2)
                locks["profit_file"].release()

            # risk multiplier
            risk_multiplier = 1
            # profit split ratio
            profit_split_ratio = 0

            # if data threads die, restart them
            if not data_thread_1h.is_alive():
                logger.info(f"Restarting {symbol}/1h Websocket.")
                data_thread_1h = connect_websocket(
                    symbol, "1h", data_lock_1h, limit=high_w)
            if not data_thread_5m.is_alive():
                logger.info(f"Restarting {symbol}/5m Websocket.")
                data_thread_5m = connect_websocket(
                    symbol, "5m", data_lock_5m, limit=high_w)

            # restart loop if there is a trade currently running on different thread
            if locks["active_trade"].locked() and (not trade_active):
                time.sleep(20)
                continue

            if (not init_flag):
                time.sleep(2)
            else:
                init_flag = False  # continue to next line for first iteration

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
                        logger.error(
                            f"ERROR Terminating Thread. Long Klines: {len(long_klines)}, Need: {high_w}", exc_info=True)
                        raise IndexError
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
                        logger.error(
                            f"ERROR Terminating Thread. Short Klines: {len(short_klines)}, Need: {high_w}", exc_info=True)
                        raise IndexError
                    break

            # calculate long EMA values
            long_EMAs = pd.DataFrame([
                EMA(long_klines['c'], low_w),
                EMA(long_klines['c'], mid_w),
                EMA(long_klines['c'], high_w)
            ], index=[low_w, mid_w, high_w])

            # calculate short EMA values
            short_EMAs = pd.DataFrame([
                EMA(short_klines['c'], low_w),
                EMA(short_klines['c'], mid_w),
                EMA(short_klines['c'], high_w)
            ], index=[low_w, mid_w, high_w])

            # ================================================================
            # ================================================================
            #                         BUYING STAGE
            # ================================================================
            # ================================================================

            current_kline = short_klines.iloc[-1]  # current candle
            current_price = current_kline['c']  # current price

            # SKIP BUYING STAGE IF ALREADY BOUGHT IN
            if (not trade_active):

                # Criteria 1: 1h -> 8 EMA > 21 EMA)
                criteria_1 = (long_EMAs.loc[8, high_w-1]
                              > long_EMAs.loc[21, high_w-1])
                if not criteria_1:
                    continue
                # Criteria 2: 5m -> 8 EMA > 13 EMA > 21 EMA
                criteria_2 = (short_EMAs.loc[8, high_w-1] > short_EMAs.loc[13, high_w-1]) and (
                    short_EMAs.loc[13, high_w-1] > short_EMAs.loc[21, high_w-1])
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
                criteria_5 = (current_kline['l'] >
                              short_EMAs.loc[21, high_w-1])
                if not criteria_5:
                    continue
                # Criteria 6: potential profit must be greater than min profit difference of 1h EMA over buy price
                buy_price = float(current_price_f(symbol))
                stop_price = min(short_klines.loc[high_w-5:high_w-1, 'l'])
                percent_profit = buy_price/stop_price-1
                if not (percent_profit*100 > min_profit):
                    continue

                # save 1h difference
                difference_1h = (
                    long_EMAs.loc[low_w, high_w-1] - long_EMAs.loc[high_w, high_w-1]) / buy_price * 100
                # check for active trade in other thread
                if locks["active_trade"].locked():
                    continue

                # if using real money for trade
                if real_money:
                    balance = account_balance("USDT")
                    # 12 is smallest possible trade if not specified
                    min_balance = 12 if (
                        not trade_quote_qty) else trade_quote_qty
                    # use full balance if quote quantity not specified
                    if (not trade_quote_qty):
                        trade_quote_qty = balance
                    # dont buy in if balance is too small for trade and continue
                    if (balance < min_balance):
                        logging.warning(
                            f"Insufficient Balance for Buy-In. Have: {balance}, Need: {min_balance}")
                        time.sleep(20)
                        continue

                # recheck for active trade in other thread
                if locks["active_trade"].locked():
                    continue
                # start active trade in this thread
                locks["active_trade"].acquire()
                # buy into trade
                if real_money:
                    buy_id, profit_quantity = buy_trade(
                        symbol=symbol, quote_quantity=trade_quote_qty)
                buy_time = int(time.time()-7*3600)
                # activate flag because trade is active in this thread
                trade_active = True

                # calcualte profit price
                profit_price = buy_price*(1+percent_profit*risk_multiplier)

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
                volume_rel = round(volume_rel.sum()*48/volume_24h*100, 2)
                # 24h price change percent
                price_24h = float(ticker['priceChangePercent'])
                # max price
                max_price = current_price
                # min price
                min_price = current_price
                # log data
                if real_money:
                    logger.info(f"BUY ID: {buy_id}")
                logger.info(
                    f"PRICE: {round(buy_price,4)} - STOP PRICE: {round(stop_price,4)} - PROFIT PRICE: {round(profit_price,4)} - PROFIT %: {round(percent_profit*risk_multiplier*100,2)}%")
                continue

            # ================================================================
            # ================================================================
            #                         SELLING STAGE
            # ================================================================
            # ================================================================

            # SKIP SELLING STAGE IF HAVE NOT BOUGHT IN YET
            if trade_active:

                logger.debug(
                    f"{symbol} CURRENT PRICE: {current_price}, {round((profit_price/current_price-1)*100, 2)}, {round((stop_price/current_price-1)*100, 2)}")
                # update max price
                max_price = max(max_price, float(current_kline['h']))
                # update min price
                min_price = min(min_price, float(current_kline['l']))

                # only when new candle after buy is opened
                if time_now > (int(buy_time) + 5*60):
                    # update max profit percent
                    max_profit = round((max_price/buy_price-1)*100, 4)
                    # update max stop percent
                    max_stop = round((buy_price/min_price-1)*100, 4)

                # ------------------------- STOP LOSS ------------------------
                if (current_price < stop_price):  # if stop loss is reached
                    profit = (-percent_profit) if (profit_index < 2) else 0
                    locks["active_trade"].release()
                    trade_active = False
                    logger.info(
                        f"{symbol} LOSS: {'{:.4f}'.format(profit*100)}%")

                    if real_money:
                        # sell out of trade (stop loss)
                        sell_id = sell_trade(
                            symbol=symbol, quantity=profit_quantity)[0]
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
                            max_profit,
                            max_stop,
                            locks["profit_file"],
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
                        split_profit = profit * \
                            ((1 - profit_split_ratio) / profit_index)
                        if (split_profit > min_profit):
                            profit = split_profit
                        else:
                            locks["active_trade"].release()
                            trade_active = False
                    else:
                        locks["active_trade"].release()
                        trade_active = False

                    if real_money:
                        profit_quantity *= (1 - profit_split_ratio)
                        # sell out of trade (take profit)
                        sell_id = sell_trade(
                            symbol=symbol, quantity=profit_quantity)[0]
                        logger.info(f"SELL ID: {sell_id}")
                        # if not profit split ratio then trade is done
                        if not profit_split_ratio:
                            # release lock and set local trade flag to false
                            locks["active_trade"].release()
                            trade_active = False

                    #display_profit(symbol, profit_index, profit)
                    logger.info(
                        f"{symbol} PROFIT {profit_index}: {'{:.4f}'.format(profit*100)}%")

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
                        max_profit,
                        max_stop,
                        locks["profit_file"],
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
        logger.error(
            f"Runtime Error. Need to unlock lock. Sleeping for 20.", exc_info=True)
        time.sleep(20)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error. Sleeping for 20.", exc_info=True)
        time.sleep(20)
    except Exception as e:
        logger.error(
            f"ERROR In {threading.current_thread().name}.", exc_info=True)
        if real_money:
            pync.notify(threading.current_thread().name, title="ERROR")
        raise e
