from config import *
from twelvedata import TDClient
import pandas as pd
import time, concurrent.futures



def indicators(symbol):
    ts = td.time_series(symbol=symbol, interval='1min', outputsize=3)
    ind = ts.with_sma(time_period=5).with_sma(time_period=8).with_sma(time_period=13).as_pandas()
    ind['symbol'] = symbol
    return ind

t0 = time.perf_counter()

symbols=['INO', 'BIOC', 'AMD', 'QQQ', 'SQQQ', 'HTBX', 'AAPL', 'TRNX', 'MSFT', 'CZR']
td = TDClient(apikey=twelvedata_api_key)
#print(indicators(symbols[0]))
#print(indicators(symbols[1]))
#print(indicators(symbols[2]))
#print(indicators(symbols[3]))
#print(indicators(symbols[4]))
#print(indicators(symbols[5]))
#print(indicators(symbols[6]))
#print(indicators(symbols[7]))
#print(indicators(symbols[8]))
#print(indicators(symbols[9]))

with concurrent.futures.ThreadPoolExecutor() as executor:
    results = [executor.submit(indicators, symbol) for symbol in symbols]

for result in results:
    print(result)

print('total exec time = {}'.format(time.perf_counter() - t0))