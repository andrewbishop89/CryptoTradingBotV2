#!/usr/bin/python3
#
# trade.py: contains all the functions involving the process of making trades 
# and verifying they are valid.
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
from pprint import pprint, pformat
import datetime
import os

from parameters import *
from api import *
from setup import *
from data_collection import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#
#
def request_order(payload={}):
    order_request = send_signed_request('POST', '/api/v3/order', payload)
    try:
        now = convert_time(time.time())
        print(
            f"Creating {payload['symbol'].upper()} \
                {payload['type'].replace('_', ' ')} \
                {payload['side'].upper()} order at \
                {now} ({normalize_time(now)}).")
    except KeyError:
        print("Creating purchase order.")
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
        print(
            f"{RED}{trade_receipt['code']}{WHITE} {trade_receipt['msg']}")
        pprint(buy_payload)
        print(RED)
        raise ValueError
    while True:
        try:
            order_id = trade_receipt['orderId']
            print(f"\tBuy Order ID:\t{order_id}")
            break
        except KeyError:
            print(f"{RED}ERROR {WHITE}Could not find buy order ID.")
        time.sleep(2)
    return order_id, get_profit_quantity(symbol, desired_quantity)

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
        print(
            f"{RED}{trade_receipt['code']}{WHITE} {trade_receipt['msg']}")
        pprint(sell_payload)
        print(RED)
        raise ValueError
    while True:
        try:
            order_id = trade_receipt['orderId']
            print(f"\tSell Order ID:\t{order_id}")
            break
        except KeyError:
            print(f"{RED}ERROR {WHITE}Could not find sell order ID.")
        time.sleep(2)
    return order_id, get_profit_quantity(symbol, desired_quantity)


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
            print(f"{RED}ERROR {WHITE}{symbol} Percentage cut \
                ({percentage_cut*100}%) is less than minimum \
                ({round(minimum_cut*100, 2)}%). Cannot afford right now.")
            print(RED)
            raise ValueError
        payment_symbol = symbol[-4:]
        payment = float(account_info([payment_symbol])[payment_symbol])
        quantity = round(percentage_cut*payment/price, trade_precision(symbol))
        validated_quantity = validate_quantity(symbol, quantity)
        return float(validated_quantity)
    else:
        return get_hardcoded_quantity(symbol, set_price)


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
        print(f"{RED}ERROR {WHITE}{symbol} Desired quote quantity \
            (${trade_quote_qty}) is greater than current balance \
            (${round(payment, 2)}).")
        return -1
    else:
        return validate_quantity(symbol, float(trade_quote_qty/price))


def current_price_f(symbol):
    return float(get_klines(symbol=symbol, limit='1').iloc[-1]['c'])


def validate_quantity(symbol, quantity):
    minQty, maxQty = trade_min_max_quantity(symbol)
    step = trade_step_size(symbol)
    quantity -= quantity % float(step)
    current_price = current_price_f(symbol)
    minNotional = get_minimum_notional(symbol)
    precision = int(trade_precision(symbol))
    if quantity > float(maxQty):
        print(f"{BLUE}NOTE {WHITE}Using maximum quantity {maxQty}.")
        return maxQty
    if quantity < float(minQty):
        print(f"{RED}ERROR {WHITE}Desired quantity is below minimum quantity.")
        return -1
    notional = float(quantity*current_price)
    if notional < minNotional:
        print(f"{RED}ERROR {WHITE}Order criteria is below the minimum \
            notional.")
        return -1
    if notional > float(account_balance('USDT')):
        print(f"{RED}ERROR {WHITE}Account has insufficient balance.\n\tHave: \
            {float(account_balance('USDT'))}\n\tNeed: {notional}")
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
            print(f"{RED}ERROR {WHITE}Could not find last order quantity.")


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
    return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
