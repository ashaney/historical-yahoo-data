"""
Code that grabs historcial data for a ticker from Yahoo! Finance
It uses code from https://github.com/bradlucas/get-yahoo-quotes-python
to assist with crumbs and cookies

MIT License
"""

import re, sys, time, requests, pickle
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib import style

# inputs
print("This tool will graph stock performance for you.\n" \
"The earliest date you can use right now is 01/01/1970.\n" \
"For the S&P 500, use '%5EGSPC'\n")

symbol = input("Type the ticker (e.g. MSFT): ") or "MSFT"
yesterday = datetime.today() - timedelta(days=1)
d = "{:%m%d%Y}".format(yesterday)
startDate = input("Type the start date (MMDDYYYY): ") or "01011970"
endDate = input("Type the end date (MMDDYYYY): ") or d
pattern = '%m%d%Y'
epoch1 = str(int(time.mktime(time.strptime(startDate, pattern))))
epoch2 = str(int(time.mktime(time.strptime(endDate, pattern))))

# crumb and cookie
def split_crumb_store(v):
    return v.split(':')[2].strip('"')

def find_crumb_store(lines):
    # Looking for
    # ,"CrumbStore":{"crumb":"9q.A4D1c.b9
    for l in lines:
        if re.findall(r'CrumbStore', l):
            return l
    print("Did not find CrumbStore")

def get_cookie_value(r):
    return {'B': r.cookies['B']}

# get the data
def get_page_data(symbol):
    page_url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)
    r = requests.get(page_url)
    cookie = get_cookie_value(r)

    # Code to replace possible \u002F value
    # ,"CrumbStore":{"crumb":"FWP\u002F5EFll3U"
    # FWP\u002F5EFll3U
    lines = r.content.decode('unicode-escape').strip(). replace('}', '\n')
    return cookie, lines.split('\n')

def get_cookie_crumb(symbol):
    cookie, lines = get_page_data(symbol)
    crumb = split_crumb_store(find_crumb_store(lines))
    return cookie, crumb

def get_data(symbol, startDate, endDate, cookie, crumb):
    filename = '%s.csv' % (symbol)
    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (symbol, epoch1, epoch2, crumb)
    r = requests.get(url, cookies=cookie, stream=True)
    with open (filename, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

# download the quotes
def download_quotes(symbol):
    start_date = epoch1
    end_date = epoch2
    cookie, crumb = get_cookie_crumb(symbol)
    get_data(symbol, start_date, end_date, cookie, crumb)

download_quotes(symbol)

# clean up the data and graph
style.use('fivethirtyeight')
plotblue = '#008fd5'
plotred = '#fc4f30'
plotyellow = '#e5ae38'
plotgreen = '#6d904f'
color_five = '#8b8b8b'

def stock_data():
    df = pd.read_csv(symbol+'.csv')
    df['Date'] = pd.to_datetime(df['Date'], errors = 'coerce')
    df = df.copy([['Date', 'Adj Close']])
    df.rename(columns={'Adj Close':symbol}, inplace=True)
    df[symbol] = (df[symbol]-df[symbol][0]) / df[symbol][0] * 100.0
    df = df.reset_index().set_index('Date').resample('1D').mean()
    df = df.resample('M').mean()
    df = df[symbol]
    return df

s_data = stock_data()
s_data.dropna(inplace=True)

fig = plt.figure()
ax1 = plt.subplot2grid((1,1), (0,0))

s_data.plot(color=plotblue, ax=ax1, legend=True, linewidth=2, label='%s' % (symbol))

plt.show()