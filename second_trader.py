#!/usr/bin/python3
#
# second_trader.py
#
# Andrew Bishop
# 2022/08/03
#

from multiprocessing import Pool
from typing import Callable, Tuple, List, Any, Dict
from helper_functions.analysis import *
from helper_functions.data_collection import download_recent_klines
from helper_functions.trade import buy_trade, get_current_price, sell_trade
from multiprocessing import Pool, current_process
from dataclasses import dataclass
import logging
import time
import json
import websockets
from websockets.client import WebSocketClientProtocol
import asyncio
import os
import importlib
from enum import Enum
import pandas as pd
from rich.pretty import pprint
from rich.progress import Progress
from rich.console import Console
import random

from ta.trend import ema_indicator
from ta.trend import sma_indicator

print = Console().print


class RunType(Enum):
	"""

	"""
	real = 0
	paper = 1
	backtest = 2


class TradeState(Enum):
	"""Contains the current state of the trade cycle."""
	buy = 0			# no active trade, looking to buy in
	sell = 1		# active trade, looking to sell out
	wait = 2		# if other trades are active, wait


def format_kline(kline: dict) -> pd.DataFrame:
	"""
	Converts kline from dict to dataframe.

	:param dict kline: dictionary of kline to be formatted
	:return pd.DataFrame: formatted kline dataframe
	"""
	df = pd.DataFrame(data={
		'time': [int(time.time())],
		'open': [float(kline['o'])],
		'close': [float(kline['c'])],
		'high': [float(kline['h'])],
		'low': [float(kline['l'])],
		'number': [float(kline['n'])],
		'volume': [float(kline['v'])]})
	return df.set_index('time')


@dataclass
class Data:
	klines: pd.DataFrame

	def __getitem__(self, symbol):	# TODO add return type
		return self.klines.loc[symbol]

	def display(self, symbol, interval) -> None:
		print(f"{symbol} {interval}")
		pprint(self[symbol][interval])
		print()

	def display_all(self) -> None:
		symbols = self.klines.index
		intervals = self.klines.columns

		for symbol in symbols:
			for interval in intervals:
				print(f"{symbol} {interval}")
				pprint(self[symbol][interval])
				print()

	def EMA(self, symbol: str, interval: str, window: int) -> float:
		ema_klines = self[symbol][interval]
		assert len(
			ema_klines) >= window, f"ERROR Only have {len(ema_klines)} klines stored, need {window} for EMA calculation."
		ema_value = ema_indicator(
			ema_klines.iloc[-window:]["close"], window=window).values[-1]
		return ema_value

	def SMA(self, symbol: str, interval: str, window: int) -> float:
		sma_klines = self[symbol][interval]
		assert len(
			sma_klines) >= window, f"ERROR Only have {len(sma_klines)} klines stored, need {window} for SMA calculation."
		sma_value = sma_indicator(
			sma_klines.iloc[-window:]["close"], window=window).values[-1]
		return sma_value


async def async_main(symbol: str) -> None:

	# PARAMETERS
	interval = "1m"
	limit = 5

	# connect stream symbol
	ws_path = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
	print(f'Connecting "{symbol} {interval}" data stream...')
	data_stream = await websockets.connect(ws_path)

	# wait for klines to load
	tmp_klines = format_kline(json.loads(await data_stream.recv())['k'])
	# with Progress() as progress:
	#	task = progress.add_task("[blue]Downloading Klines[/]...", total=limit-1)

	#	while not progress.finished:
	#		tmp_klines = pd.concat([tmp_klines, format_kline(json.loads(await data_stream.recv())['k'])])
	#		progress.update(task, advance=1)
			
	while len(tmp_klines) < limit:
		tmp_klines = pd.concat([tmp_klines, format_kline(json.loads(await data_stream.recv())['k'])])
		

	assert len(
		tmp_klines) == limit, f"ERROR {len(tmp_klines)} stored but need {limit}."

	klines = pd.DataFrame(tmp_klines)
	# data = Data(pd.DataFrame({ interval: { symbol: tmp_klines } }))

	trade_state = TradeState.buy

	TSP_factor = 1 - (1 / 100)
	print(f"Starting trade loop for {symbol}...")
	
	time.sleep(15)
	# -------- TRADE LOOP --------
	while True:

		# -------- BUY STAGE --------
		if trade_state == TradeState.buy:

			# -------- DOWNLOAD DATA --------
			klines = pd.concat([klines.iloc[1:, :], format_kline(json.loads(await data_stream.recv())['k'])])
			assert len(klines) == limit, f"ERROR {len(klines)} stored but need {limit}."

			def bull_flag(klines: pd.DataFrame) -> bool:
				lows = klines.loc[:, 'low'].values
				highs = klines.loc[:, 'high'].values
				close_4 = klines.loc[:, 'close'].values[4]
					
				criteria_1 = (lows[0] < lows[1]) and (lows[0] < lows[2]) and (lows[0] < lows[3])
				criteria_2 = (highs[1] > highs[2]) and (highs[2] > highs[3])
				criteria_3 = (close_4 > highs[3])
				
				print(f"{symbol}".ljust(10) + f"- {'[green]PASS[/]' if criteria_1 else '[red]FAIL[/]'} {'[green]PASS[/]' if criteria_2 else '[red]FAIL[/]'} {'[green]PASS[/]' if criteria_3 else '[red]FAIL[/]'} @{int(time.time())}")
				return (criteria_1 and criteria_2 and criteria_3)

			if bull_flag(klines):
				buy_price = get_current_price(symbol)
				trailing_stop_price = buy_price * TSP_factor
				trade_state = TradeState.sell
				break
		
		# -------- SELL STAGE --------
		if trade_state == TradeState.sell:
			
			# -------- DOWNLOAD DATA --------
			current_kline = format_kline(json.loads(await data_stream.recv())['k'])['close']
			current_price = current_kline['close']
			current_high = current_kline['high']
			
			if current_price < trailing_stop_price:
				sell_price = current_price
				trade_state = TradeState.wait
				break

			if current_high * TSP_factor > trailing_stop_price:
				trailing_stop_price = trailing_stop_price * TSP_factor
				continue
					
		# -------- LOG STAGE --------
		if trade_state == TradeState.wait:
			profit = (sell_price/buy_price-1)*100
			print(f"{symbol} [{'green' if profit > 0 else 'red'}]PROFIT[/]:\t {profit}")
			with open("second_logs.log", "a") as f:
				f.write(f"{symbol} PROFIT:\t {profit}\t@{int(time.time())}")
				
			trade_state = TradeState.buy
			continue
		
def main(symbol):
	asyncio.run(async_main(symbol))
	

if __name__ == "__main__":
	
	symbols = [
		"BTCUSDT", 
		"ETHUSDT", 
		"ADAUSDT", 
		"TRXUSDT", 
		"XMRUSDT",
		"CAKEUSDT",
		"BNBUSDT",
		"SOLUSDT",
		"XRPUSDT",
		"LTCUSDT",		  
	]

	with Pool(10) as pool:
		pool.map(main, symbols)
