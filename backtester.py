#http://www.quantatrisk.com/2017/11/07/earning-money-cryptocurrency-statistical-arbitrage-python/
import numpy as np
import pandas as pd
from scipy import stats
from matplotlib import pyplot as plt
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests

import pprint
import argparse

parser = argparse.ArgumentParser(description='market analyzer for input currency pairs (tsym, fsym)')
parser.add_argument('fsym', action="store", type=str)
parser.add_argument('tsym', action="store", type=str)
parser.add_argument('market1', action="store", type=str)
parser.add_argument('market2', action="store", type=str)
parser.add_argument('start_date', action="store", type=str)
parser.add_argument('end_date', action="store", type=str)
args = parser.parse_args()


def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

def fetchCryptoOHLC_byExchange(fsym, tsym, exchange):
    # a function fetches a crypto OHLC price-series for fsym/tsym and stores
    # it in a pandas DataFrame; uses specific Exchange as provided
    # src: https://www.cryptocompare.com/api/

    cols = ['date', 'timestamp', 'open', 'high', 'low', 'close']
    lst = ['time', 'open', 'high', 'low', 'close']

    timestamp_today = datetime.today().timestamp()
    curr_timestamp = timestamp_today

    for j in range(2):
        df = pd.DataFrame(columns=cols)
        url = "https://min-api.cryptocompare.com/data/histoday?fsym=" + fsym + \
              "&tsym=" + tsym + "&toTs=" + str(int(curr_timestamp)) + \
              "&limit=2000" + "&e=" + exchange
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        dic = json.loads(soup.prettify())

        for i in range(1, 2001):
            tmp = []
            for e in enumerate(lst):
                x = e[0]
                y = dic['Data'][i][e[1]]
                if(x == 0):
                    # timestamp-to-date
                    td = datetime.fromtimestamp(int(y)).strftime('%Y-%m-%d')
                    tmp.append(td)  #(str(timestamp2date(y)))
                tmp.append(y)
            if(np.sum(tmp[-4::]) > 0):
                df.loc[len(df)] = np.array(tmp)
        df.index = pd.to_datetime(df.date)
        df.drop('date', axis=1, inplace=True)
        curr_timestamp = int(df.iloc[0][0])

        if(j == 0):
            df0 = df.copy()
        else:
            data = pd.concat([df, df0], axis=0)

    return data.astype(np.float64)

#Statistical Arbitrage Trading Strategy
market1 = str(args.market1)#"HitBTC"
market2 = str(args.market2)#"BitTrex"

fsym = str(args.fsym).upper() #"BCH"
tsym = str(args.tsym).upper() #"ETH"

start_date = str(args.start_date)
end_date = str(args.end_date)


df1 = fetchCryptoOHLC_byExchange(fsym, tsym, market1)
df2 = fetchCryptoOHLC_byExchange(fsym, tsym, market2)

# trim
df1 = df1[(df1.index > start_date) & (df1.index <= end_date)]
df2 = df2[(df2.index > start_date) & (df2.index <= end_date)]

# checkpoint
print(df1.close.shape[0], df2.close.shape[0])  # both sizes must be equal

# plotting
plt.figure(figsize=(20,10))
plt.plot(df1.close, '.-', label=market1)
plt.plot(df2.close, '.-', label=market2)
plt.legend(loc=2)
plt.title(fsym, fontsize=12)
plt.ylabel(tsym, fontsize=12)
plt.grid()
plt.show()


# Backtesting Stat Arb trading strategy for ETH/USD at Exmo and Kraken
#  cryptocurrency exchanges
# initial parameters

investment = 10000  # USD
account1, account2 = investment/2, investment/2  # USD
position = 0.5*(investment/2)  # USD

roi = []
ac1 = [account1]
ac2 = [account2]
money = []
trade_pnl = []
pnl_exch1 = []
pnl_exch2 = []

trade = False
n = df1.close.shape[0]  # number of data points

# running the backtest
for i in range(n):
    p1 = float(df1.close.iloc[i])
    p2 = float(df2.close.iloc[i])
    if(p1 > p2):
        asset1 = "SHORT"
        asset2 = "LONG"
        if(trade == False):
            open_p1 = p1  # open prices
            open_p2 = p2
            open_asset1 = asset1
            open_asset2 = asset2
            trade = True
            print("new traded opened")
            new_trade = False
        elif(asset1 == open_asset1):
            new_trade = False  # flag
        elif(asset1 == open_asset2):
            new_trade = True   # flag

    elif(p2 > p1):
        asset1 = "LONG"
        asset2 = "SHORT"
        if(trade == False):
            open_p1 = p1  # open prices
            open_p2 = p2
            open_asset1 = asset1
            open_asset2 = asset2
            trade = True
            print("new traded opened")
            new_trade = False
        elif(asset1 == open_asset1):
            new_trade = False  # flag
        elif(asset1 == open_asset2):
            new_trade = True   # flag

    if(i == 0):
        print(df1.close.iloc[i], df2.close.iloc[i], \
              asset1, asset2, trade, "----first trade info")
    else:
        if(new_trade):

            # close current position
            if(open_asset1 == "SHORT"):
                # PnL of both trades
                pnl_asset1 = open_p1/p1 - 1
                pnl_asset2 = p2/open_p2 -1
                pnl_exch1.append(pnl_asset1)
                pnl_exch2.append(pnl_asset2)
                print(open_p1, p1, open_p2, p2, open_asset1, \
                      open_asset2, pnl_asset1, pnl_asset2)
                # update both accounts
                account1 = account1 + position*pnl_asset1
                account2 = account2 + position*pnl_asset2
                print("accounts [USD] = ", account1, account2)
                if((account1 <=0) or (account2 <=0)):
                    print("--trading halted")
                    break
                # return on investment (ROI)
                total = account1 + account2
                roi.append(total/investment-1)
                ac1.append(account1)
                ac2.append(account2)
                money.append(total)
                print("ROI = ", roi[-1])
                print("trade closed\n")
                trade = False
 
                # open a new trade
                if(asset1 == "SHORT"):
                    open_p1 = p1
                    open_p2 = p2
                    open_asset1 = asset1
                    open_asset2 = asset2
                else:
                    open_p1 = p1
                    open_p2 = p2
                    open_asset1 = asset1
                    open_asset2 = asset2
                trade = True
                print("new trade opened", asset1, asset2, \
                      open_p1, open_p2)

            # close current position
            if(open_asset1 == "LONG"):
                # PnL of both trades
                pnl_asset1 = p1/open_p1 -1
                pnl_asset2 = open_p2/p2 - 1
                pnl_exch1.append(pnl_asset1)
                pnl_exch2.append(pnl_asset2)
                print(open_p1, p1, open_p2, p2, open_asset1, \
                      open_asset2, pnl_asset1, pnl_asset2)
                # update both accounts
                account1 = account1 + position*pnl_asset1
                account2 = account2 + position*pnl_asset2
                print("accounts [USD] = ", account1, account2)
                if((account1 <=0) or (account2 <=0)):
                    print("--trading halted")
                    break
                # return on investment (ROI)
                total = account1 + account2
                roi.append(total/investment-1)
                ac1.append(account1)
                ac2.append(account2)
                money.append(total)
                trade_pnl.append(pnl_asset1+pnl_asset2)
                print("ROI = ", roi[-1])
                print("trade closed\n")
                trade = False

                # open a new trade
                if(open_asset1 == "SHORT"):
                    open_p1 = p1
                    open_p2 = p2
                    open_asset1 = asset1
                    open_asset2 = asset2
                else:
                    open_p1 = p1
                    open_p2 = p2
                    open_asset1 = asset1
                    open_asset2 = asset2
                new_trade = False
                trade = True
                print("new trade opened:", asset1, asset2, \
                      open_p1, open_p2)

        else:
            print("   ",df1.close.iloc[i], df2.close.iloc[i], \
                  asset1, asset2)
