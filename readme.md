CryptoTradingBotV2 Notes

The most recent model for this program is Method 2. This model uses 1 hour and 
5 minute interval candles and exponential moving averages for it's criteria to 
buy into a trade.

The program starts by running the method_2.py file. The main idea of the method
is that it cycles through a loop forever (or until a keyboard interrupt) and 
checks the current candles to know whether to buy in or not.

The program is multithreaded and thread safe. It is a work in progress but is 
fully functioning. Whenever I have free time I will spend time optimizing it.

Optimizations for the future can be seen in the method_2.py TODOs list at the 
start of the file.

The cryptocurrency exchange is Binance. The program communicates with Binance 
through public and signed API requests where the signed requests are encrypted 
using SHA256. A WebSocket subscription is used for the data collection through 
Binance.