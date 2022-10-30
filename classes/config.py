"""

"""

from enum import Enum
from dataclasses import dataclass


# ----------------------------------------------------------
#                      Enum Classes 
# ----------------------------------------------------------

class MethodType(Enum):
    """
    An enum for the method type
    """
    REAL = 0
    PAPER = 1


# ----------------------------------------------------------
#                       Dataclasses 
# ----------------------------------------------------------

@dataclass
class MethodConfig:
    """

    """
    type = MethodType 
    symbol = str
    quote_quantity = float


@dataclass
class MethodInfo:
    """

    """
    profit_percent = float
    stop_percent = float
    

# TODO add different class for backtesting
