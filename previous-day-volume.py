from config import *
import pandas as pd
import alpaca_trade_api as alpaca
import requests, datetime

t0 = datetime.datetime.now()
r = requests.get(alpaca_base_url + '/v2/assets', headers=alpaca_headers)
assets = pd.DataFrame(r.json())
active = assets[assets.status.eq('active')]
activeTradable = active[active.tradable.eq(True)]
activeTradableUS = activeTradable.loc[activeTradable['class']=='us_equity']
activeTradableUS = activeTradableUS.loc[activeTradableUS['exchange']=='NASDAQ']
alp = alpaca.REST(alpaca_API_KEY, alpaca_SECRET_KEY, api_version='v2')

lastDayBars = pd.DataFrame()
while not activeTradableUS.empty:
    # have to split the assets to chunks of 200 rows max and get the assets last daily bar
    symbols = activeTradableUS['symbol'][:200]
    activeTradableUS = activeTradableUS.iloc[200:]
    barset = alp.get_barset(symbols, timeframe='day', limit=1, start=None, end=None, after=None, until=None)
    barsetSerie = pd.Series(barset)

    for index, value in barsetSerie.iteritems():
        lastDayBars =  lastDayBars.append(pd.DataFrame(data=[[value[0].t, index, value[0].o, value[0].c, value[0].h, value[0].l, value[0].v]],
                                                                   columns=['time', 'symbol','open', 'close', 'high', 'low', 'volume']))

lastDayBars = lastDayBars.sort_values(by=['volume'], ascending=False)
lastDayBars.to_csv('lastDayBars_{}.csv'.format(datetime.datetime.now().strftime("%Y-%m-%d")))
#print(lastDayBars)

print('total execution time = {}'.format(datetime.datetime.now() - t0))