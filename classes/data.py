"""

"""

from enum import Enum
from dataclasses import dataclass



# ----------------------------------------------------------
#                      Enum Classes 
# ----------------------------------------------------------

class KlineInterval(Enum):
    """
    Value is integer for amount of seconds the interval is.
    """
    _4h = 60 * 60 * 4
    _1h = 60 * 60
    _30m = 60 * 30
    _15m = 60 * 15
    _5m = 60 * 5
    _1m = 60


# ----------------------------------------------------------
#                       Dataclasses 
# ----------------------------------------------------------

