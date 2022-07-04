import pandas as pd
import time
import pyupbit


# ----------------- functions -----------------------

'''
ohclv: candle data
standard_date
    -1: today(now)
    -2: yesterday / before
'''


def get_RSI(ohlcv, period, standard_date):
    ohlcv["close"] = ohlcv["close"]
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return float(pd.Series(100 - (100 / (1 + RS)), name="RSI").iloc[standard_date])


def get_MA(ohclv, period, standard_date):
    close = ohclv["close"]
    ma = close.rolling(period).mean()
    return float(ma[standard_date])


'''
interval: interval(day, week, minute5 ...)
top: top volume money stocks
'''


def get_top_coin_list(interval, top):
    print("------------------ Get Top Coin List Start ---------------")
    tickers = pyupbit.get_tickers("KRW")
    dic_coin_money = dict()

    for ticker in tickers:
        try:
            day_candle = pyupbit.get_ohlcv(ticker, interval)
            volume_money = (day_candle['close'][-1] * day_candle['volume']
                            [-1]) + (day_candle['close'][-2] * day_candle['volume'][-2])

            dic_coin_money[ticker] = volume_money

            print(ticker, dic_coin_money[ticker])
            time.sleep(0.05)

        except Exception as e:
            print("exception:", e)

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
    in_coin_ok = False
    for coin_ticker in coin_list:
        if coin_ticker == ticker:
            in_coin_ok = True
            break

    return in_coin_ok


def get_revenue_rate(balances, Ticker):
    revenue_rate = 0.0
    for value in balances:
        try:
            real_ticker = value['unit_currency'] + "-" + value['currency']
            if ticker == real_ticker:
                time.sleep(0.02)

                # 현재 가격을 가져옵니다.
                nowPrice = pyupbit.get_current_price(real_ticker)

                # 수익율을 구해서 넣어줍니다
                revenue_rate = (float(
                    nowPrice) - float(value['avg_buy_price'])) * 100.0 / float(value['avg_buy_price'])
                break

        except Exception as e:
            print("GetRevenueRate error:", e)

    return revenue_rate

# Return sum of total buy amounts


def get_coin_now_money(balances, ticker):
    coin_money = 0.0
    for value in balances:
        real_ticker = value["unit_currency"] + "-" + value["currency"]
        if ticker == real_ticker:
            coin_money = float(value["avg_buy_price"]) * \
                float(value['balance'])
            break

    return coin_money

# Check buy success


def is_has_coin(balances, ticker):
    has_coin = False
    for value in balances:
        real_ticker = value['unit_currency'] + "-" + value['currency']
        if ticker == real_ticker:
            has_coin = True
    return has_coin


def get_has_coin_cnt(balances):
    coin_cnt = 0
    for value in balances:
        avg_buy_price = float(value["avg_buy_price"])
        if avg_buy_price != 0:
            coin_cnt += 1
    return coin_cnt


def get_total_money(balances):
    total = 0.0
    for value in balances:
        ticker = value["currency"]

        if ticker == "KRW":
            total += float(value["balance"])
        else:
            total += (float(value["avg_buy_price"]) * float(value["balance"]))
    return total


def get_total_real_money(balances):
    total = 0.0
    for value in balances:
        ticker = value["currency"]

        if ticker == "KRW":
            total += float(value["balance"])
        else:
            avg_buy_price = float(value["avg_buy_price"])
            if avg_buy_price != 0:
                real_ticker = value["unit_currency"] + "-" + value["currency"]
                time.sleep(0.05)
                now_price = pyupbit.get_current_price(real_ticker)
                total += (float(value["avg_buy_price"])
                          * float(value["balance"]))
    return total
