"""

"""

from enum import Enum
from dataclasses import dataclass



# ----------------------------------------------------------
#                      Enum Classes 
# ----------------------------------------------------------

class TradeSide(Enum):
    """

    """
    BUY = "buy"
    SELL = "sell"


class TradeType(Enum):
    """

    """
    MARKET = "market"
    LIMIT = "limit"


# ----------------------------------------------------------
#                       Dataclasses 
# ----------------------------------------------------------

@dataclass
class OpenTrade:
    """

    """
    buy_price = float  
    profit_price = float
    stop_price = float
    sell_quantity = float
    

@dataclass
class TradeInfo:
    """

    """
    trade_side: TradeSide 
    trade_type: TradeType

