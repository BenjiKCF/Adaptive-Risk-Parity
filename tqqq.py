from datetime import datetime, date
import math
import numpy as np
import time
import sys
import requests


if len(sys.argv) == 1:
    calculation_mode = False
    
else:
    calculation_mode = True
    shares = sys.argv[1].split(',')
    shares = [float(i) for i in shares]
    
symbols = ['TQQQ', 'TMF']
num_trading_days_per_year = 252
window_size = 20
date_format = "%Y-%m-%d"
end_timestamp = int(time.time())
start_timestamp = int(end_timestamp - (1.4 * (window_size + 1) + 4) * 86400)


def get_volatility_and_performance(symbol):
    download_url = "https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&crumb=a7pcO//zvcW".format(symbol, start_timestamp, end_timestamp)
    lines = requests.get(download_url, cookies={'B': 'chjes25epq9b6&b=3&s=18'}).text.strip().split('\n')
    assert lines[0].split(',')[0] == 'Date'
    assert lines[0].split(',')[4] == 'Close'
    prices = []
    for line in lines[1:]:
        prices.append(float(line.split(',')[4]))
    #print(download_url)
    last_price = prices[-1]
    prices.reverse()
    volatilities_in_window = []

    for i in range(window_size):
        volatilities_in_window.append(math.log(prices[i] / prices[i+1]))
        
    most_recent_date = datetime.strptime(lines[-1].split(',')[0], date_format).date()
    assert (date.today() - most_recent_date).days <= 4, "today is {}, most recent trading day is {}".format(date.today(), most_recent_date)

    return np.std(volatilities_in_window, ddof = 1) * np.sqrt(num_trading_days_per_year), prices[0] / prices[window_size] - 1.0, last_price

volatilities = []
performances = []
sum_inverse_volatility = 0.0
for symbol in symbols:
    volatility, performance, last_price = get_volatility_and_performance(symbol)
    sum_inverse_volatility += 1 / volatility
    volatilities.append(volatility)
    performances.append(performance)

if calculation_mode == False:
    print ("Portfolio: {}, as of {} (window size is {} days)".format(str(symbols), date.today().strftime('%Y-%m-%d'), window_size))
    for i in range(len(symbols)):
        print ('{} allocation ratio: {:.2f}% (anualized volatility: {:.2f}%, performance: {:.2f}%)'.format(symbols[i], float(100 / (volatilities[i] * sum_inverse_volatility)), float(volatilities[i] * 100), float(performances[i] * 100)))
        
        
if calculation_mode == True:
    dicts = {}
    #shares = [177, 425]
    for i in range(len(symbols)):
        dicts[symbols[i]] = shares[i]


    amounts = []
    for i in range(len(symbols)):
        symbol = symbols[i]
        volatility, performance, last_price = get_volatility_and_performance(symbol)
        amount = last_price * dicts[symbol]
        amounts.append(amount)


    print ("Portfolio: {}, as of {} (window size is {} days)".format(str(symbols), date.today().strftime('%Y-%m-%d'), window_size))

    for i in range(len(symbols)):
        symbol = symbols[i]
        volatility, performance, last_price = get_volatility_and_performance(symbol)
        amount = last_price * dicts[symbol]
        current_ratio = amount/sum(amounts)*100
        target_ratio  = float(100/(volatilities[i]*sum_inverse_volatility))
        print("Current {} allocation ratio: {:.2f}%, amount: {:.2f}".format(symbol, current_ratio, amount))
        print("Target {} allocation ratio: {:.2f}%, amount: {:.2f}".format(symbol, target_ratio, amounts[i]/current_ratio*target_ratio))
        diff = amount-(amounts[i]/current_ratio*target_ratio)
        if  diff> 0:
            print("Sell ${:.2f} or {:.2f} shares of {}".format(diff, diff/last_price, symbol))
        else:
            print("Buy ${:.2f} or {:.2f} shares of {}".format(abs(diff), abs(diff/last_price), symbol))
        print('\n')