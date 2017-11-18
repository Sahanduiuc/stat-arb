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
import os.path
import csv
import xlsxwriter

parser = argparse.ArgumentParser(description='market analyzer for input currency pairs (tsym, fsym)')
parser.add_argument('fsym', action="store", type=str)
parser.add_argument('tsym', action="store", type=str)
parser.add_argument('start_date', action="store", type=str)
parser.add_argument('end_date', action="store", type=str)
parser.add_argument('upload', action="store", type=str)
args = parser.parse_args()


""" 
from IPython import get_ipython
get_ipython().run_line_magic('matplotlib', 'inline')

%matplotlib inline
grey = .6, .6, .6
"""
pp = pprint.PrettyPrinter()

 
#define time period
start_date = str(args.start_date)
end_date = str(args.end_date)

# define a pair
fsym = str(args.fsym).upper() #"BCH"
tsym = str(args.tsym).upper() #"ETH"
#fsym = "BCH"
#tsym = "ETH"
 
#get all market data
url = "https://www.cryptocompare.com/api/data/coinsnapshot/?fsym=" + \
       fsym + "&tsym=" + tsym
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
dic = json.loads(soup.prettify())
pp.pprint(dic)


#get exchange names
market = []
d = dic['Data']['Exchanges']  # a list
for i in range(len(d)):
    market.append(d[i]['MARKET'])
    pp.pprint(market[-1])


#get volume data for each exchange
vol = []
d = dic['Data']['Exchanges']  # a list
for i in range(len(d)):
    vol.append([d[i]['MARKET'], round(float(d[i]['VOLUME24HOUR']),2)])
 
# sort a list of sublists according to 2nd item in a sublist
vol = sorted(vol, key=lambda x: -x[1])
 
# Cryptocurrency Markets according to Volume traded within last 24 hours
for e in vol:
    print("%10s%15.2f" % (e[0], e[1]))

# Select Top 10 Cryptocurrency Markets
markets = [e[0] for e in vol][0:10]
#print(markets)

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



# if a variable 'cp' exists, delete it
if ('cp' in globals()) or ('cp' in locals()): del cp
 
# download daily OHLC price-series for ETH/USD for a given 'market'
# extract close-price (cp)
 

print("%s/%s" % (fsym, tsym))
for market in markets:
    print("%12s... " % market, end="")
    df = fetchCryptoOHLC_byExchange(fsym, tsym, market)
    ts = df[(df.index > start_date) & (df.index <= end_date)]["close"]
    ts.name = market

    if ('cp' in globals()) or ('cp' in locals()):
        if(ts.size == days_between(start_date, end_date)):
            cp = pd.concat([cp, ts], axis=1, ignore_index=False)
    else:
        cp = pd.DataFrame(ts)
    print("downloaded")


#Average Spread Estimation for parity among different Markets
dist = []
for i in range(cp.shape[1]):
    for j in range(i):
        if(i != j):
            x = np.array(cp.iloc[:,i], dtype=np.float32)
            y = np.array(cp.iloc[:,j], dtype=np.float32)
            diff = np.abs(x-y)
            avg = np.mean(diff)
            std = np.std(diff, ddof=1)
            dist.append([cp.columns[i], cp.columns[j], avg, std])
 
dist = sorted(dist, key=lambda x: -x[2])


#Print results to stdin, txt, csv
scriptpath = os.path.dirname(__file__)
filename = str(fsym) + str(tsym) + "-" + str(start_date) + "--" + str(end_date)
fn = os.path.join(scriptpath, "./stat-results/"+filename)
fnn = open(fn,'w+')

print("%10s%10s%10s%10s\n" % ("Coin1", "Coin2", "Mean", "Std Dev"))
print("%10s%10s%10s%10s" % ("Coin1,", "Coin2,", "Mean,", "Std Dev,"), file=fnn)
for e in dist:
    print("%10s %10s %10.9f %10.9f" % (e[0], e[1], e[2], e[3]))
    print("%10s, %10s, %10.9f, %10.9f," % (e[0], e[1], e[2], e[3]), file=fnn)
fnn.close()

#.txt -> .csv
with open(fn, 'r') as in_file:
    stripped = (line.strip() for line in in_file)
    lines = (line.split(",") for line in stripped if line)
    with open(fn+".csv", 'w') as out_file:
        writer = csv.writer(out_file)
        #writer.writerow(('title', 'intro'))
        writer.writerows(lines)

#.csv -> .xlsx
fn_csv = fn + ".csv"
f_csv = pd.read_csv(fn_csv)
writer = pd.ExcelWriter(fn + '.xlsx', engine='xlsxwriter')
f_csv.to_excel(writer, sheet_name='result', index=False)
writer.save()

#upload to gdrive
if(args.upload):
    upld = "gdrive upload -p 1eB4sV3_q5_Xtztqx2GUCGAnWtm1P8JzH " + fn + ".xlsx" 
    os.system(upld)

#gdrive upload -p 1eB4sV3_q5_Xtztqx2GUCGAnWtm1P8JzH /home/uad/Programming/cryptocurrency/arbitrage/stat-arb/stat-results/ETHUSD-2017-06-01--2017-11-05.xlsx

