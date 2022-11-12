"""

"""

from dataclasses import dataclass
from typing import Dict

from classes.config import MethodType, MethodConfig 
from classes.trade import TradeType, TradeSide, TradeInfo 
from api.general_api import API
from functions.setup.setup import convert_time, retrieve_keys
from functions.trade.trade import get_profit_quantity, normalize_time

@dataclass
class MethodAPI:
    """

    """
    method_cfg = MethodConfig

    


class TradeAPI:
    """

    """
    def __init__(self, method_type):
        self._method_type = method_type

        base_url = "https://api.binance.com"
        api_key, api_secret = retrieve_keys()

        self._api = API(api_key, api_secret, base_url)


    # ----------------------------------------------------------
    #                     Trade Functions
    # ----------------------------------------------------------

    def _trade(self, symbol, quote_quantity, trade_type: TradeType, trade_side: TradeSide) -> Dict[str, str]:
        desired_quantity = self.get_desired_quantity(symbol, quote_quantity)
        trade_payload = {
            'symbol':       symbol,
            'side':         trade_side.value,
            'type':         trade_type.value.upper(),
            'quantity':     desired_quantity
        }
        order = self._api.send_signed_request('POST', '/api/v3/order', trade_payload)

        assert "orderId" not in order.keys(), f"Could not find order id in {trade_side.value} order request response.\n{order}"

        return order


    def market_buy(self, symbol: str, quote_quantity: float):
        return self._trade(symbol, quote_quantity, TradeType.MARKET, TradeSide.BUY)


    def market_sell(self, symbol: str, quote_quantity: float):
        return self._trade(symbol, quote_quantity, TradeType.MARKET, TradeSide.SELL) 


    # ----------------------------------------------------------
    #                     Main API Functions
    # ----------------------------------------------------------

    def get_order(self, symbol: str, orderId: str) -> Dict[str, str]:
        """

        """
        payload = {
            'symbol': symbol,
            'orderId': orderId,
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

