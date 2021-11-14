#!/usr/bin/python3
#
# trade.py: contains all the functions involving the process of making trades 
# and verifying they are valid.
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
from parameters import *
from setup import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

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
            f"{RED}{trade_receipt['code']}{WHITE} {trade_receipt['msg']} \
                \n{RED}")
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
            f"{RED}{trade_receipt['code']}{WHITE} {trade_receipt['msg']} \
                \n{RED}")
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
            print(f"{RED}ERROR {WHITE}{symbol} Percentage cut ({percentage_cut*100}%) is less than minimum ({round(minimum_cut*100, 2)}%). Cannot afford right now.")
            print(RED)
            raise ValueError
        payment_symbol = symbol[-4:]
        payment = float(account_info([payment_symbol])[payment_symbol])
        quantity = round(percentage_cut*payment/price, trade_precision(symbol))
        validated_quantity = validate_quantity(symbol, quantity)
        return float(validated_quantity)
    else:
        return get_hardcoded_quantity(symbol, set_price)
