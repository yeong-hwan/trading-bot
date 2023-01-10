import pandas as pd
import time
import pprint
import requests
import json
import line_alert
import numpy as np
from datetime import datetime
import ta
import pandas_ta

pd.set_option('display.max_rows', None)

'''
ohclv: candle data
standard_date
    -1: today(now)
    -2: yesterday / before
'''

# ----------------------- supertrend functions ----------------------------


def cross_over(candle_close_current, candle_close_before, supertrend_line):
    cross_over_check = False

    if (candle_close_current > supertrend_line) & (candle_close_before < supertrend_line):
        cross_over_check = True

    return cross_over_check


def cross_under(candle_close_current, candle_close_before, supertrend_line):
    cross_under_check = False

    if (candle_close_current < supertrend_line) & (candle_close_before > supertrend_line):
        cross_under_check = True

    return cross_under_check


def get_supertrend_cloud(candle, candle_type, btc=False):

    candle_close_series = candle['close']

    # current : endded[-1], before : endded[-2]
    candle_close_current = candle_close_series[-2]
    candle_close_before = candle_close_series[-3]

    period_1, multi_1, period_2, multi_2 = 0, 0, 0, 0
    supertrend_line_1, supertrend_line_2 = 0, 0

    # ---------------- variables setting --------------------
    if candle_type == "5m":
        period_1, multi_1, period_2, multi_2 = 6, 10, 10, 6

    elif btc == True and candle_type == "4h":
        period_1, multi_1, period_2, multi_2 = 4, 2.4, 4, 4.8

    elif candle_type == "4h":
        period_1, multi_1, period_2, multi_2 = 10, 3, 10, 6

    #

    supertrend_1 = pandas_ta.supertrend(
        high=candle['high'], low=candle['low'], close=candle['close'], period=period_1, multiplier=multi_1)
    supertrend_line_1 = supertrend_1.iloc[-1][0]

    supertrend_2 = pandas_ta.supertrend(
        high=candle['high'], low=candle['low'], close=candle['close'], period=period_2, multiplier=multi_2)
    supertrend_line_2 = supertrend_2.iloc[-1][0]

    long_condition = (cross_over(candle_close_current, candle_close_before, supertrend_line_1)
                      and candle_close_current > supertrend_line_2) \
        or (cross_over(candle_close_current, candle_close_before, supertrend_line_2)
            and candle_close_current > supertrend_line_1)

    if (cross_over(candle_close_current, candle_close_before, supertrend_line_1)
            and candle_close_current > supertrend_line_2):
        line_alert.send_message("long_1")

    if (cross_over(candle_close_current, candle_close_before, supertrend_line_2)
            and candle_close_current > supertrend_line_1):
        line_alert.send_message("long_2")

    short_condition = (cross_under(candle_close_current, candle_close_before, supertrend_line_1)
                       and candle_close_current < supertrend_line_2) \
        or (cross_under(candle_close_current, candle_close_before, supertrend_line_2)
            and candle_close_current < supertrend_line_1)

    if (cross_under(candle_close_current, candle_close_before, supertrend_line_1)
            and candle_close_current < supertrend_line_2):
        line_alert.send_message("short_1")

    if (cross_under(candle_close_current, candle_close_before, supertrend_line_2)
            and candle_close_current < supertrend_line_1):
        line_alert.send_message("short_2")

    cloud_condition = (cross_under(candle_close_current, candle_close_before, supertrend_line_1)
                       and candle_close_current > supertrend_line_2) \
        or (cross_over(candle_close_current, candle_close_before, supertrend_line_1)
            and candle_close_current < supertrend_line_2) \
        or (cross_under(candle_close_current, candle_close_before, supertrend_line_2)
            and candle_close_current > supertrend_line_1) \
        or (cross_over(candle_close_current, candle_close_before, supertrend_line_2)
            and candle_close_current < supertrend_line_1)

    return long_condition, short_condition, cloud_condition, supertrend_line_1, supertrend_line_2


# ------------------ binance functions ---------------------

# period: (1d,4h,1h,15m,10m,1m ...)
def get_ohlcv(binance, ticker, period):
    btc_ohlcv = binance.fetch_ohlcv(ticker, period)
    ohlcv = pd.DataFrame(btc_ohlcv, columns=[
                         'datetime', 'open', 'high', 'low', 'close', 'volume'])
    ohlcv['datetime'] = pd.to_datetime(ohlcv['datetime'], unit='ms')
    ohlcv.set_index('datetime', inplace=True)
    return ohlcv


def get_amount(usdt, coin_price, rate):

    target = usdt * rate

    amount = target / coin_price
    # at least 0.001 coin for trading
    # line_alert.send_message(f"1 {amount}")

    if amount < 0.001:
        amount = 0.001
    # line_alert.send_message(f"2 {amount}")

    return amount


def get_coin_current_price(binance, ticker):
    coin_info = binance.fetch_ticker(ticker)
    coin_price = coin_info['last']  # coin_info['close'] == coin_info['last']

    return coin_price


# ------------------ balance functions ----------------------

def get_usd_krw():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
    exchange = requests.get(url, headers=headers).json()
    return exchange[0]['basePrice']


def get_top_coin_list(binance, top):

    tickers = binance.fetch_tickers()
    dic_coin_money = dict()
    # pprint.pprint(tickers)

    for ticker in tickers:

        try:
            if "/USDT" in ticker:
                # print(ticker, "----- \n",
                #   tickers[ticker]['baseVolume'] * tickers[ticker]['close'])

                dic_coin_money[ticker] = tickers[ticker]['baseVolume'] * \
                    tickers[ticker]['close']

        except Exception as e:
            print("---:", e)

    dic_sorted_coin_money = sorted(
        dic_coin_money.items(), key=lambda x: x[1], reverse=True)

    coin_list = list()
    cnt = 0
    for coin_data in dic_sorted_coin_money:
        # print("####-------------", coin_data[0], coin_data[1])
        cnt += 1
        if cnt <= top:
            coin_list.append(coin_data[0])
        else:
            break

    return coin_list


def check_coin_in_list(coin_list, ticker):
    coin_in_list = False
    for coin_ticker in coin_list:
        if coin_ticker == ticker:
            coin_in_list = True
            break

    return coin_in_list


# https://blog.naver.com/zhanggo2/222722244744
def get_min_amount(binance, ticker):
    limit_values = binance.markets[ticker]['limits']

    min_amount = limit_values['amount']['min']
    min_cost = limit_values['cost']['min']
    min_price = limit_values['price']['min']

    coin_info = binance.fetch_ticker(ticker)
    coin_price = coin_info['last']

    print(f"| Coin_price : {coin_price} $")
    # print(f"| min_cost : {min_cost} $ -> min_amount")
    # print(f"| min_amount : {min_amount} EA")
    # print(f"| min_price : {min_price} $")

    # get mininum unit price to be able to order
    if min_price < coin_price:
        min_price = coin_price

    # order cost = price * amount
    min_order_cost = min_price * min_amount

    num_min_amount = 1

    if min_cost is not None and min_order_cost < min_cost:
        # if order cost is smaller than min cost
        # increase the order cost bigger than min cost
        # by the multiple number of minimum amount
        while min_order_cost < min_cost:
            num_min_amount += 1
            min_order_cost = min_price * (num_min_amount * min_amount)

    minimum_amount = num_min_amount * min_amount
    return (min_cost, minimum_amount)

# ------------------------------------------------------------------------
