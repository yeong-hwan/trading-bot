# ---------------- library -------------------------
from aem import con
from numpy import float_power, real
import pyupbit
import time
import pandas as pd
from regex import P

access = "JW7G0hr9xnBWpejlquZkEW78db0GXX1ROrPgK6ws"
secret = "tWLOFowynAXsT5UitsM4tPPuL1uIxrMNtYThIDZj"
upbit = pyupbit.Upbit(access, secret)

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
    print("------------------ Returned Top Coin List ---------------")

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


# ---------------------- variables --------------------------
top_coin_list = get_top_coin_list("week", 10)
danger_coin_list = ["KRW-DOGE"]
my_coin_list = []
tickers = pyupbit.get_tickers("KRW")
balances = upbit.get_balances()

'''
total_money: 총 원금
total_real_money: 총 평가금액
total_revenue: 수익율
'''

total_money = get_total_money(balances)
total_real_money = get_total_real_money(balances)
total_revenue = (total_real_money - total_money) * 100.0 / total_money

'''
max_coin_cnt: 매수할 총 코인 개수
coin_max_money: 코인당 매수 최대금액
first_rate: 초기 투자 종목별 원금 10 %
after_rate: 추가 매수 비율 5%
'''

max_coin_cnt = 5.0
coin_max_money = total_money / max_coin_cnt
first_rate = 10.0
after_rate = 5.0
first_enter_money = coin_max_money / 100.0 * first_rate
after_enter_money = coin_max_money / 100.0 * after_rate

# ------------------- status ----------------------------
print("--------------- BTC BOT WORKING ---------------")
print("Total Money : ", total_money)
print("Total Real Money : ", total_real_money)
print("Total Revenue : ", total_revenue)
print("------------------------------------------------")
print("Coin Max Money : ", coin_max_money)
print("First Enter Money : ", first_enter_money)
print("After Enter Money : ", after_enter_money)
print("------------------------------------------------")

# ------------------- working part ----------------------------
for ticker in tickers:
    try:
        if check_coin_in_list(top_coin_list, ticker) == False:
            continue
        if check_coin_in_list(danger_coin_list, ticker) == True:
            continue
        if check_coin_in_list(my_coin_list, ticker) == False:
            continue
        print(ticker, "is target")
    except Exception as e:
        print(e)

    time.sleep(0.05)

    day_candle_60 = pyupbit.get_ohlcv(ticker, interval="minute60")
    rsi60_min_before = get_RSI(day_candle_60, 14, -2)
    rsi60_min_now = get_RSI(day_candle_60, 14, -1)

    revenu_rate = get_revenue_rate(balances, ticker)
    print(ticker, ", RSI :", rsi60_min_before, " -> ", rsi60_min_now)
    print("revenu_rate : ", revenu_rate)

    # 보유하고 있는 코인들
    if is_has_coin(balances, ticker) == True:
        print("has_coin")
    # 매수하기 전인 코인들
    else:
        print("not_on_my_hand")

    # if rsi60_min_now <= 30.0 and revenu_rate < -5.0:
        # 분할 매수


print("----------------------------------------")
