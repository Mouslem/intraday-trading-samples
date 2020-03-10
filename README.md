# intraday-trading-samples
Some basic intraday trading strategis [Credits :TwelveData for bars & Indicators, Alpaca Markets Paper]

SMA Strategy
- Applied on a set of 10 stocks (Symbols List)
- SMA : Simple Moving Average
- SMAX, X = Average Window Size
- This strategie implements rules of SMA5, SMA8 and SMA13 (5, 8, 13) for intraday trading
- Rule(1) LastSMA5 > LastSMA8
- Rule(2) PreviousSMA5 < PreviousSMA8
- Rule(3) LastSMA5 > LastSMA20
- Rule(4) LastSMA5 < LastSMA8
- Rule(5) PreviousSMA5 > Previous SMA8
- Rule(6) LastSMA8 > LastSMA13
- Buy (Long) if : (1) & (2) & (3) & have no/less than 50 shares in the portfolio
- Sell (Short) if : (4) & (5) & (6) & Profit/Loss higher than 1%
- Else : Do nothing (None)
- The strtegie loops every 1 minute till the market close
- If Market is closed, wait till opens
