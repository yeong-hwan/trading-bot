# ------- library --------
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

# ------------------------------------------------------------------------

# Contents
# 1. Supertrend functions
# 2. Binance functions
# 3. Balance functions

# ------------------------------------------------------------------------

#
#
#

# ----------------------- Supertrend functions ---------------------------


def get_cross_over(candle_close_current, candle_close_before, supertrend_line):
    cross_over_check = False

    if (candle_close_current > supertrend_line) & (candle_close_before < supertrend_line):
        cross_over_check = True

    return cross_over_check


def get_cross_under(candle_close_current, candle_close_before, supertrend_line):
    cross_under_check = False

    if (candle_close_current < supertrend_line) & (candle_close_before > supertrend_line):
        cross_under_check = True

    return cross_under_check


def get_side(candle_close_current, st_1, st_2):
    result = ""

    if ((candle_close_current < st_1) & (candle_close_current > st_2)) or ((candle_close_current > st_1) & (candle_close_current < st_2)):
        result = "cloud"

    if (candle_close_current > st_1) & (candle_close_current > st_2):
        result = "upside"

    if (candle_close_current < st_1) & (candle_close_current < st_2):
        result = "downside"

    return result


def get_state(state_before, state_current):
    state_now = ""

    if state_before == "cloud" and state_current == "cloud":
        state_now = "C"
    elif state_before == "upside" and state_current == "upside":
        state_now = "L"
    elif state_before == "downside" and state_current == "downside":
        state_now = "S"

    if state_before == "cloud" and state_current == "upside":
        state_now = "Crossover Out"
    elif state_before == "cloud" and state_current == "downside":
        state_now = "Crossunder Out"
    elif state_before == "upside" and state_current == "cloud":
        state_now = "Crossunder In"
    elif state_before == "downside" and state_current == "cloud":
        state_now = "Crossover In"

    if state_before == "upside" and state_current == "downside":
        state_now = "Big Short"
    elif state_before == "downside" and state_current == "upside":
        state_now = "Big Long"

    return state_now


def get_supertrend_cloud(candle, candle_type, btc=False):

    candle_close_series = candle['close']

    # current : endded[-1], before : endded[-2]
    # candle_close_current = candle_close_series[-2]
    # candle_close_before = candle_close_series[-3]

    period_1, multi_1, period_2, multi_2 = 0, 0, 0, 0
    supertrend_line_1, supertrend_line_2 = 0, 0

    long_condition, short_condition, cloud_condition = False, False, False

    # variable setting
    if candle_type == "5m":
        period_1, multi_1, period_2, multi_2 = 6, 10, 10, 6

    elif btc == True and candle_type == "4h":
        period_1, multi_1, period_2, multi_2 = 4, 2.4, 4, 4.8

    elif candle_type == "4h":
        period_1, multi_1, period_2, multi_2 = 10, 3, 10, 6

    # -3
    state_current = ""

    # -4
    state_before = ""

    for i in range(3, 5):
        supertrend_1 = pandas_ta.supertrend(
            high=candle['high'], low=candle['low'], close=candle['close'], period=period_1, multiplier=multi_1)
        supertrend_line_1 = supertrend_1.iloc[-i][0]

        supertrend_2 = pandas_ta.supertrend(
            high=candle['high'], low=candle['low'], close=candle['close'], period=period_2, multiplier=multi_2)
        supertrend_line_2 = supertrend_2.iloc[-i][0]

        state_at_i = get_side(candle_close_series[-i],
                              supertrend_line_1, supertrend_line_2)

        if i == 3:
            state_current = state_at_i
        elif i == 4:
            state_before = state_at_i

    state = get_state(state_before, state_current)

    if state[-2:] == "In":
        cloud_condition = True
    elif state == "Crossover Out":
        long_condition = True
    elif state == "Crossunder Out":
        short_condition = True

    elif state[:3] == "Big":
        cloud_condition = True
        position_side = state[4:]

        if position_side == "Long":
            long_condition = True
        elif position_side == "Short":
            short_condition = True

    return long_condition, short_condition, cloud_condition, supertrend_line_1, supertrend_line_2, state

# ---------------------------------------------------------------------------

#
#
#

# ----------------------- Binance functions ---------------------------------

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

# ------------------------------------------------------------------------

#
#
#

# ------------------------ Balance functions -----------------------------


def get_usd_krw():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
    exchange = requests.get(url, headers=headers).json()
    return exchange[0]['basePrice']


def get_top_coin_list(binance, top):

    tickers = binance.fetch_tickers()
    dic_coin_money = dict()

    for ticker in tickers:

        try:
            if "/USDT" in ticker:

                dic_coin_money[ticker] = tickers[ticker]['baseVolume'] * \
                    tickers[ticker]['close']

        except Exception as e:
            print("---:", e)

    dic_sorted_coin_money = sorted(
        dic_coin_money.items(), key=lambda x: x[1], reverse=True)

    coin_list = list()
    cnt = 0
    for coin_data in dic_sorted_coin_money:
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

    multiple_cnt = 1

    if min_cost is not None and min_order_cost < min_cost:
        # if min_order_cost is smaller than min cost
        # increase the min_order_cost bigger than min cost
        # by the multiple multiple_cnt of minimum amount
        while min_order_cost < min_cost:
            multiple_cnt += 1
            min_order_cost = min_price * (multiple_cnt * min_amount)

    minimum_amount = multiple_cnt * min_amount
    return (min_order_cost, minimum_amount)

# ------------------------------------------------------------------------
