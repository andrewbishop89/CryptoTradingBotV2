"""

"""

from dataclasses import dataclass
from typing import Dict

from classes.config import MethodType, MethodInfo
from classes.trade import TradeType, TradeSide, TradeInfo 
from api.api import API
from functions.setup.setup import convert_time, retrieve_keys
from functions.trade.trade import get_profit_quantity, get_desired_quantity, normalize_time


@dataclass
class TradeAPI:
    """

    """
    trade_type: TradeType


    def __post_init__(self):
        base_url = "https://api.binance.com"
        api_key, api_secret = retrieve_keys(self.trade_type)

        self._api = API(api_key, api_secret, base_url)


    def _request_order(self, payload={}):
        """

        """
        order_request = self._api.send_signed_request('POST', '/api/v3/order', payload)
        try:
            now = convert_time(time.time())
            logger.info(
                f"Creating {payload['symbol'].upper()} {payload['type'].replace('_', ' ')} {payload['side'].upper()} order at {now} ({normalize_time(now)}).")
        except KeyError:
            logger.info("Creating Purchase Order")
        return order_request

        
    def buy_trade(self, symbol: str, quote_quantity: float = 0, quantity: float = 0):
        """

        """
        desired_quantity = get_desired_quantity(symbol=symbol, set_price=quote_quantity) if (not quantity) else quantity
        buy_payload = {
            'symbol':       symbol,
            'side':         'BUY',
            'type':         'MARKET',
            'quantity':     desired_quantity,
        }
        # trade_receipt = _request_order(buy_payload)
        return self._request_order(buy_payload)
        # TODO lower this sleep if possible
        time.sleep(5) 

        # TODO move order logs to csv file
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


    def sell_trade(self, symbol: str, quote_quantity: float = 0, quantity: float = 0):
        """

        """
        desired_quantity = quantity if (not quote_quantity) else get_desired_quantity(symbol=symbol, set_price=quote_quantity)
        sell_payload = {
            'symbol':       symbol,
            'side':         'SELL',
            'type':         'MARKET',
            'quantity':     desired_quantity,
        }
        # trade_receipt = _request_order(sell_payload)
        return self._request_order(sell_payload) 
        # TODO lower this sleep if possible
        time.sleep(5)

        # TODO move order logs to csv file
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

