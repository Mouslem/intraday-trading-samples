from config import *
import requests, json
import threading, time, datetime
import alpaca_trade_api as tradeapi
from twelvedata import TDClient
import pandas as pd
from sqlalchemy import create_engine
import concurrent.futures


class smaStrategy:
    def __init__(self, symbols=['INO', 'BIOC', 'AMD', 'QQQ', 'SQQQ', 'HTBX', 'AAPL', 'TRNX', 'MSFT', 'CZR']):
        self.alpaca = tradeapi.REST(alpaca_API_KEY, alpaca_SECRET_KEY, alpaca_base_url, 'v2')
        self.td = TDClient(apikey=twelvedata_api_key)
        self.symbols = symbols
        self.blacklist = set()
        self.outputsize = 2  # number of previous bars // see twelvedata indicators
        self.qty = 10  # number of shares to be executed evry transaction /// will have to adjust this
        self.sqlconn = None

    def run(self):
        # First, cancel any existing orders so they don't impact our buying power.
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)

        # Wait for market to open.
        print("Waiting for market to open...")
        tAMO = threading.Thread(target=self.awaitMarketOpen)
        tAMO.start()
        tAMO.join()
        print("Market opened.")

        self.sqlconn = create_engine('sqlite:///smaDataFrame{}.db'.format(time.strftime("%d-%b-%Y")), echo=False)
        # Fetch the indicators every minute, making necessary trades ///only rsi and gain>0.1% for now.
        while self.alpaca.get_clock().is_open:
            df = self.butchTimeSeries()
            print('============================== New Cycle ============================================')
            print('current time = {}'.format(datetime.datetime.now()))
            print('-------------------------------------------------------------------------------------')
            print(df)
            print('-------------------------------------------------------------------------------------')
            dfSymSig = df[['symbol', 'signal']].drop_duplicates(keep='first')
            shortSymbols = dfSymSig[dfSymSig['signal'] == 'sell']['symbol'].tolist()
            longSymbols = dfSymSig[dfSymSig['signal'] == 'buy']['symbol'].tolist()
            respSell = []
            respBuy = []
            self.sendBatchOrder(self.qty, shortSymbols, 'sell', respSell)
            self.sendBatchOrder(self.qty, longSymbols, 'buy', respBuy)
            print('-------------- Cycle ended, Next update in 60 seconds --------------------------------')
            df.to_sql('Candle Sticks', con=self.sqlconn, if_exists='append')
            print('\n')
            print('\n')
            print('\n')
            time.sleep(60)

        print('Market closed for today')

    # Wait for market to open.
    def awaitMarketOpen(self):
        isOpen = self.alpaca.get_clock().is_open
        while (not isOpen):
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            print(str(timeToOpen) + " minutes til market open.")
            time.sleep(60)
            isOpen = self.alpaca.get_clock().is_open

    # time series for butch symbols : list of symbols [sym1, sm2, ...., symN]
    def butchTimeSeries(self):
        df = pd.DataFrame()
        # with concurrent.futures.ProcessPoolExecutor as executor:
        for symbol in self.symbols:
            # ts = [executor.submit(self.td.time_series, symbol=symbol, interval='1min', outputsize=self.outputsize,) for symbol in self.symbols]
            ts = self.td.time_series(symbol=symbol, interval='1min', outputsize=self.outputsize)
            # only sma5, sma8 and sma13 for the moment
            indicators = ts.with_sma(time_period=5).with_sma(time_period=8).with_sma(time_period=13).as_pandas()
            indicators['symbol'] = symbol
            print(indicators)
            if not indicators.empty and indicators['sma1'][0] > indicators['sma2'][0] \
                    and indicators['sma1'][-1] < indicators['sma2'][-1] \
                    and indicators['sma1'][0] > indicators['sma3'][0]:
                indicators['signal'] = 'buy'
            elif not indicators.empty and indicators['sma1'][0] < indicators['sma2'][0] \
                    and indicators['sma1'][-1] > indicators['sma2'][-1] \
                    and indicators['sma2'][0] > indicators['sma3'][0]:
                indicators['signal'] = 'sell'
            else:
                indicators['signal'] = None
            df = df.append(indicators)
        return df

    # Submit a batch order that returns completed and uncompleted orders.
    def sendBatchOrder(self, qty, stocks, side, resp):
        executed = []
        incomplete = []
        for stock in stocks:
            if (self.blacklist.isdisjoint({stock})):
                respSO = []
                tSubmitOrder = threading.Thread(target=self.submitOrder, args=[qty, stock, side, respSO])
                tSubmitOrder.start()
                tSubmitOrder.join()
                # if(not respSO[0]):
                #    # Stock order did not go through, add it to incomplete.
                #    incomplete.append(stock)
                # else:
                #    executed.append(stock)
                # respSO.clear()
            resp.append([executed, incomplete])

    # Submit an order if buy or sell conditions are met.
    def submitOrder(self, qty, stock, side, resp):
        position = requests.get(alpaca_base_url + '/v2/positions/' + stock, headers=alpaca_headers)
        # Submit buy order only if ownes less than 5*qty shares in the portfolio
        if ('buy' in side and (position.status_code == 404 or float(position.json()['qty']) < (self.qty * 5))):
            try:
                self.alpaca.submit_order(stock, qty, side, "market", "day")
                print("Market order of | " + str(qty) + " " + stock + " " + side + " | completed.")
                resp.append(True)
            except:
                print("Order of | " + str(qty) + " " + stock + " " + side + " | did not go through.")
                resp.append(False)
        # Sell only if we own the asset and the profit is higher than 0.1%
        elif ('sell' in side and (
                position.status_code == 200 and float(position.json()['unrealized_plpc']) > (0.1 / 100))):
            try:
                self.alpaca.submit_order(stock, qty, side, "market", "day")
                print("Market order of | " + str(qty) + " " + stock + " " + side + " | completed.")
                resp.append(True)
            except:
                print("Order of | " + str(qty) + " " + stock + " " + side + " | did not go through.")
                resp.append(False)
        else:
            print("Order of | " + str(qty) + " " + stock + " " + side + " | not completed.")
            resp.append(True)


t0 = time.perf_counter()

rsis = smaStrategy()
rsis.run()

#df = rsis.butchTimeSeries()
#print(df)



print('total exec time = {}'.format(time.perf_counter() - t0))
