def backtest_all(symbols: List):
    """
    Description:
        Backtests all symbols listed for method 2.
    Args:
        symbols (List): all symbols to be backtested.
    """
    print("Backtest Symbols:")
    for s in symbols:
        print(f"\t{s}")
    print("\n\nStarting Backtest.")
    with Pool(10) as p:
        net_profit = sum(p.map(backtest_method_2, symbols))
    print(f"\nNet Profit: ".rjust(25) + f"{GREEN if (net_profit > 0) else RED}{round(net_profit*100,2)}%{WHITE}\n")
