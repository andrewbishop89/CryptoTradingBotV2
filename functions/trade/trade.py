#!/usr/bin/python3
#
# trade.py: contains all the functions involving the process of making trades
# and verifying they are valid.
#
# Andrew Bishop
# 2021/11/13
#


from pprint import pprint, pformat
import datetime
import os
import threading
import logging
from random import randint


# ----------------------------------functions-----------------------------------

# PARAM
# RETURN
def request_order(payload={}):
    order_request = send_signed_request('POST', '/api/v3/order', payload)
    try:
        now = convert_time(time.time())
        logger.info(
            f"Creating {payload['symbol'].upper()} {payload['type'].replace('_', ' ')} {payload['side'].upper()} order at {now} ({normalize_time(now)}).")
    except KeyError:
        logger.info("Creating Purchase Order")
    return order_request

# PARAM symbol(str): symbol of coin to buy
# PARAM quote_quantity(float): quote quantity to buy
# PARAM quantity(float): quantity to buy
# RETURN (int): order id of buy trade
# RETURN (float): profit quantity
def buy_trade(symbol: str, quote_quantity: float = 0, quantity: float = 0):
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
        logger.warning(
            f"\n{trade_receipt['code']} {trade_receipt['msg']}\n{pformat(buy_payload)}\n{pformat(trade_receipt)}", exc_info=True)
    profit_quantity = get_profit_quantity(symbol, desired_quantity)
    try:
        order_id = trade_receipt['orderId']
    except KeyError:
        logger.error(f"ERROR Could not find buy order ID.", exc_info=True)
        return None, profit_quantity
    else:
        return order_id, profit_quantity

# PARAM symbol(str): symbol of coin to sell
# PARAM quote_quantity(float): quote quantity to sell
# PARAM quantity(float): quantity to sell
# RETURN (int): order id of sell trade
# RETURN (float): profit quantty


def sell_trade(symbol: str, quote_quantity: float = 0, quantity: float = 0):
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
        logger.critical(
            f"\n{trade_receipt['code']} {trade_receipt['msg']}\n{pformat(sell_payload)}\n{pformat(trade_receipt)}", exc_info=True)
    profit_quantity = get_profit_quantity(symbol, desired_quantity)
    try:
        order_id = trade_receipt['orderId']
    except KeyError:
        logger.error(f"ERROR Could not find sell order ID.", exc_info=True)
        return None, profit_quantity
    else:
        return order_id, profit_quantity


def get_profit_quantity(symbol, buy_quantity):
    # need to do this because there is 0.1% fee on trade
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
    price = float(get_current_price(symbol=symbol))
    payment_symbol = get_payment_symbol(symbol)
    payment = float(account_info([payment_symbol])[payment_symbol])
    if trade_quote_qty > payment:
        logger.error(
            f"ERROR {symbol} Desired quote quantity (${trade_quote_qty}) is greater than current balance (${round(payment, 2)}).")
        return -1
    else:
        return float(validate_quantity(symbol, float(trade_quote_qty/price)))


def get_current_price(symbol):
    response = send_public_request('/api/v3/ticker/price', {"symbol": symbol})
    try:
        current_price = float(response["price"])
    except KeyError:
        logger.warning(
            f"Key Error: Could not retrieve current price. Retrying in 60s.\n{pformat(response)}")
        time.sleep(randint(30, 90))
        return get_current_price(symbol)
    else:
        return current_price


def get_payment_symbol(symbol):
    if symbol.endswith("USDT"):
        return "USDT"
    elif symbol.endswith("BNB"):
        return "BNB"
    else:
        logger.error(f"{symbol} is invalid. Need 'USDT' or 'BNB' as payment.")
        raise ValueError


def validate_quantity(symbol, quantity):
    minQty, maxQty = trade_min_max_quantity(symbol)
    step = trade_step_size(symbol)
    quantity -= quantity % float(step)
    current_price = get_current_price(symbol)
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
    payment_symbol = get_payment_symbol(symbol)
    if notional > float(account_balance(payment_symbol)):
        logger.error(
            f"ERROR Account has insufficient balance.\n\tHave: {float(account_balance(payment_symbol))}\n\tNeed: {notional}")
        return -1

    return round(quantity, precision-1)


def get_minimum_notional(symbol):
    filters = exchange_information(symbol=symbol)['filters']
    for filter in filters:
        if filter['filterType'] == 'MIN_NOTIONAL':
            minNotional = filter['minNotional']
    return float(minNotional)


def get_minimum_cut(symbol):
    payment_symbol = get_payment_symbol(symbol)
    balance = float(account_balance(payment_symbol))
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


def my_trades(symbol: str) -> list:
    """
    Description:
        Returns list of trades for that symbol.
    Args:
        symbol (str): symbol of trades to list
    Returns:
        list: list of trades for that symbol.
    """
    payload = {'symbol': symbol}
    return send_signed_request('GET', '/api/v3/myTrades', payload)


def get_cummulative_quote_quantity(symbol: str, trade_id) -> float:
    """
    Description:
        Returns cummulative quote quantity of the trade specified by the trade id
    Args:
        symbol (str): symbol of trade
        trade_id: trade id of trade to parse
    Returns:
        float: cummulative quote quantity of trade specified by trade id
    """
    return float(get_order(symbol, str(trade_id))["cummulativeQuoteQty"])


def account_balance(symbol):
    try:
        return float(account_info([symbol])[symbol])
    except KeyError:
        return 0


def normalize_time(ts):
    if len(str(int(ts))) != 10:
        ts = convert_time(ts)
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


# PARAM thread(threading.Thread): thread object for trade loop
# PARAM symbol(str): string of symbol to be traded
#RETURN (none)
def start_trade(thread: threading.Thread, symbol: str):
    # get all active thread names
    thread_names = [t.name for t in threading.enumerate()]
    count = 1
    for name in thread_names:  # find avaible thread name
        if symbol in name:
            count += 1
    thread_name = f"Thread-{symbol}-{count}"
    if thread_name in thread_names:  # raise error if error in name
        logger.error(f"Two threads have same name.")
        raise ValueError
    thread.name = thread_name  # assign name to thread
    thread.start()  # start trade loop thread

    return
