#!/usr/bin/python3
#
# trade.py: contains all the functions involving the process of making trades 
# and verifying they are valid.
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
from pprint import pprint, pformat
import datetime
import os
import threading
import logging

from constants.parameters import *
from helper_functions.api import *
from helper_functions.setup import *
from helper_functions.data_collection import *

logger = logging.getLogger("main")

#----------------------------------functions-----------------------------------

# PARAM
# RETURN
def request_order(payload={}):
    order_request = send_signed_request('POST', '/api/v3/order', payload)
    try:
        now = convert_time(time.time())
        logger.info(f"Creating {payload['symbol'].upper()} {payload['type'].replace('_', ' ')} {payload['side'].upper()} order at {now} ({normalize_time(now)}).")
    except KeyError:
        logger.info("Creating Purchase Order")
    return order_request


#PARAM symbol(str): symbol of coin to buy
#PARAM quote_quantity(float): quote quantity to buy
#PARAM quantity(float): quantity to buy
#RETURN (int): order id of buy trade
#RETURN (float): profit quantity
def buy_trade(symbol: str, quote_quantity: float=0, quantity: float=0):
    desired_quantity = get_desired_quantity(
        symbol=symbol, 
        set_price=quote_quantity) if (not quantity) else quantity
    buy_payload = {
        'symbol':       symbol,
        'side':         'BUY',
        'type':         'MARKET',
        'quantity':     desired_quantity,
    }
    trade_receipt = request_order(buy_payload)
    time.sleep(5)
    with open('logs/orders.txt', 'a') as f:
        f.write(f"TIME: {convert_time(time.time())} - \
            {normalize_time(convert_time(time.time()))}\n$ ======== BUY ORDER \
            ======== $\nProposed:\n{pformat(buy_payload)}\nActual:\n \
            {pformat(trade_receipt)}\n\n")
    if 'code' in list(trade_receipt.keys()):
        logger.warning(f"\n{trade_receipt['code']} {trade_receipt['msg']}\n{pformat(buy_payload)}\n{pformat(trade_receipt)}", exc_info=True)
    profit_quantity = get_profit_quantity(symbol, desired_quantity)
    try:
        order_id = trade_receipt['orderId']
    except KeyError:
        logger.error(f"ERROR Could not find buy order ID.", exc_info=True)
        return None, profit_quantity
    else:
        return order_id, profit_quantity
#PARAM symbol(str): symbol of coin to sell
#PARAM quote_quantity(float): quote quantity to sell
#PARAM quantity(float): quantity to sell
#RETURN (int): order id of sell trade
#RETURN (float): profit quantty
def sell_trade(symbol: str, quote_quantity: float=0, quantity: float=0):
    desired_quantity = quantity if (not quote_quantity) else \
        get_desired_quantity(symbol=symbol, set_price=quote_quantity)
    sell_payload = {
        'symbol':       symbol,
        'side':         'SELL',
        'type':         'MARKET',
        'quantity':     desired_quantity,
    }
    trade_receipt = request_order(sell_payload)
    time.sleep(5)
    with open(os.path.join('logs', 'orders.txt'), 'a') as f:
        f.write(f"TIME: {convert_time(time.time())} - \
            {normalize_time(convert_time(time.time()))}\n$ ======== SELL \
            ORDER ======== $\nProposed:\n{pformat(sell_payload)}\nActual: \
            \n{pformat(trade_receipt)}\n\n")
    if 'code' in list(trade_receipt.keys()):
        logger.critical(f"\n{trade_receipt['code']} {trade_receipt['msg']}\n{pformat(sell_payload)}\n{pformat(trade_receipt)}", exc_info=True)
    profit_quantity = get_profit_quantity(symbol, desired_quantity)
    try:
        order_id = trade_receipt['orderId']
    except KeyError:
        logger.error(f"ERROR Could not find sell order ID.", exc_info=True)
        return None, profit_quantity
    else:
        return order_id, profit_quantity


#PARAM symbol(str): symbol of quantity to trade
#PARAM percentage_cut(float): percentage of bank account to trade
#PARAM set_price(float): exact price to trade
def get_desired_quantity(
    symbol: str, 
    percentage_cut: float=0.04, 
    set_price: float=-1):
    
    if set_price == -1:
        
        price = float(current_price_f(symbol))
        minimum_cut = get_minimum_cut(symbol)
        if percentage_cut < minimum_cut:
            logger.error(f"ERROR {symbol} Percentage cut ({percentage_cut*100}%) is less than minimum ({round(minimum_cut*100, 2)}%). Cannot afford right now.")
            raise ValueError
        payment_symbol = symbol[-4:]
        payment = float(account_info([payment_symbol])[payment_symbol])
        quantity = round(percentage_cut*payment/price, trade_precision(symbol))
        validated_quantity = validate_quantity(symbol, quantity)
        return float(validated_quantity)
    else:
        return float(get_hardcoded_quantity(symbol, set_price))


def get_profit_quantity(symbol, buy_quantity):
    # NOTE need to do this because there is 0.1% fee on trade
    profit_quantity = buy_quantity*(1 - (0.1/100))
    profit_quantity -= profit_quantity % trade_step_size(symbol)
    precision = int(trade_precision(symbol))
    return round(profit_quantity, precision-1)


def trade_precision(symbol):
    return exchange_information(symbol=symbol)['baseAssetPrecision']


def trade_step_size(symbol):
    filters = exchange_information(symbol=symbol)['filters']
    for item in filters:
        if 'stepSize' in item.keys():
            return float(item['stepSize'])


def trade_min_max_quantity(symbol):
    filters = exchange_information(symbol=symbol)['filters']
    for item in filters:
        if 'stepSize' in item.keys():
            return float(item['minQty']), float(item['maxQty'])

def exchange_information(symbol=-1):
    response = send_public_request('/api/v3/exchangeInfo')
    if symbol == -1:
        return response
    else:
        for item in response['symbols']:
            if item['symbol'] == symbol:
                return item


def get_hardcoded_quantity(symbol, trade_quote_qty):
    price = float(current_price_f(symbol=symbol))
    payment_symbol = symbol[-4:]
    payment = float(account_info([payment_symbol])[payment_symbol])
    if trade_quote_qty > payment:
        logger.error(f"ERROR {symbol} Desired quote quantity (${trade_quote_qty}) is greater than current balance (${round(payment, 2)}).")
        return -1
    else:
        return float(validate_quantity(symbol, float(trade_quote_qty/price)))


def current_price_f(symbol):
    response = send_public_request('/api/v3/ticker/price')
    for item in response:
        if item['symbol'] == symbol:
            return item['price']
    return float(get_klines(symbol=symbol, limit='1').iloc[-1]['c'])


def validate_quantity(symbol, quantity):
    minQty, maxQty = trade_min_max_quantity(symbol)
    step = trade_step_size(symbol)
    quantity -= quantity % float(step)
    current_price = current_price_f(symbol)
    minNotional = get_minimum_notional(symbol)
    precision = int(trade_precision(symbol))
    if quantity > float(maxQty):
        logger.info(f"Using maximum quantity {maxQty}.")
        return maxQty
    if quantity < float(minQty):
        logger.error(f"ERROR Desired quantity is below minimum quantity.")
        return -1
    notional = float(quantity)*float(current_price)
    if notional < minNotional:
        logger.error(f"ERROR Order criteria is below the minimum notional.")
        return -1
    if notional > float(account_balance('USDT')):
        logger.error(f"ERROR Account has insufficient balance.\n\tHave: {float(account_balance('USDT'))}\n\tNeed: {notional}")
        return -1

    return round(quantity, precision-1)


def get_minimum_notional(symbol):
    filters = exchange_information(symbol=symbol)['filters']
    for filter in filters:
        if filter['filterType'] == 'MIN_NOTIONAL':
            minNotional = filter['minNotional']
    return float(minNotional)


def get_minimum_cut(symbol):
    balance = float(account_balance('USDT'))
    minimum_notional = get_minimum_notional(symbol)
    minimum_cut = minimum_notional/balance
    return minimum_cut


def last_order_quantity(symbol, orderId):
    while True:
        try:
            quantity = float(get_order(symbol, orderId)['executedQty'])
            return quantity
        except KeyError:
            logger.error(f"Could not find last order quantity.", exc_info=True)


def account_info(specific_data=None):
    # returns dictionary of all the crypto the account holds
    if (specific_data == None):
        specific_data = []
    data = {}
    account = send_signed_request('GET', '/api/v3/account')
    balances = account['balances']
    for balance in balances:
        if float(balance['free']) != 0.0:
            if specific_data:
                if balance['asset'] in specific_data:
                    data[balance['asset']] = balance['free']
            else:
                data[balance['asset']] = balance['free']
    return data


def get_order(symbol, orderId):
    payload = {
        'symbol': symbol,
        'orderId': orderId,
    }
    return send_signed_request('GET', '/api/v3/order', payload)


def account_balance(symbol):
    try:
        return float(account_info([symbol])[symbol])
    except KeyError:
        return 0


def normalize_time(ts):
    if len(str(int(ts))) != 10:
        ts = convert_time(ts)
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


#PARAM thread(threading.Thread): thread object for trade loop
#PARAM symbol(str): string of symbol to be traded
#RETURN (none)
def start_trade(thread: threading.Thread, symbol: str):
    #get all active thread names
    thread_names = [t.name for t in threading.enumerate()]
    count = 1
    for name in thread_names: #find avaible thread name
        if symbol in name:
            count += 1
    thread_name = f"Thread-{symbol}-{count}"
    if thread_name in thread_names: #raise error if error in name
        logger.error(f"Two threads have same name.")
        raise ValueError
    thread.name = thread_name #assign name to thread
    thread.start() #start trade loop thread
    
    return
