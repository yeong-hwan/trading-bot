# ---------------- library -------------------------
import pyupbit
import time
import uf


access = "JW7G0hr9xnBWpejlquZkEW78db0GXX1ROrPgK6ws"
secret = "tWLOFowynAXsT5UitsM4tPPuL1uIxrMNtYThIDZj"
upbit = pyupbit.Upbit(access, secret)

# ---------------------- variables --------------------------
top_coin_list = uf.get_top_coin_list("week", 10)
except_coin_list = ["KRW-DOGE"]
my_coin_list = []
tickers = pyupbit.get_tickers("KRW")
balances = upbit.get_balances()

'''
total_money: 총 원금
total_real_money: 총 평가금액
total_revenue: 수익율
'''

# total_money = get_total_money(balances)
total_money = 0
total_real_money = uf.get_total_real_money(balances)
total_revenue = 0
if total_money != 0:
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
print("--------------- STATUS ---------------")
print(balances)
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
    # --------------------- coin selection --------------------
    try:
        if uf.check_coin_in_list(top_coin_list, ticker) == False:
            continue
        if uf.check_coin_in_list(except_coin_list, ticker) == True:
            continue
        if uf.check_coin_in_list(my_coin_list, ticker) == False:
            continue
        print(ticker, "is target")

        time.sleep(0.05)

        # -------------------- variables -----------------------
        day_candle_60 = pyupbit.get_ohlcv(ticker, interval="minute60")
        rsi60_min_before = uf.get_RSI(day_candle_60, 14, -2)
        rsi60_min_now = uf.get_RSI(day_candle_60, 14, -1)

        time.sleep(0.05)

        revenue_rate = uf.get_revenue_rate(balances, ticker)
        print(ticker, ", RSI :", rsi60_min_before, " -> ", rsi60_min_now)
        print("revenue_rate : ", revenue_rate)

        # get KRW balance
        won_balance = float(upbit.get_balance("KRW"))

        if uf.is_has_coin(balances, ticker) == True:
            now_coin_total_money = uf.get_coin_now_money(balances, ticker)

            # ----------------- sell logic ---------------------------
            if rsi60_min_now >= 70 and revenue_rate >= 1.0:
                volume = upbit.get_balance(ticker)
                time.sleep(0.05)

                if now_coin_total_money < coin_max_money / 4.0:
                    print(upbit.sell_market_order(ticker, volume))
                else:
                    print(upbit.sell_market_order(ticker, volume / 2.0))

            # stop loss
            if won_balance < after_enter_money and revenue_rate <= -10.0:
                print(upbit.sell_market_order(ticker, volume / 2.0))

            # ----------------- buy logic ----------------------------
            total_rate = now_coin_total_money / coin_max_money * 100.0

            if rsi60_min_before <= 30.0 and rsi60_min_now > 30.0 and uf.get_has_coin_cnt(balances) < max_coin_cnt:
                if total_rate <= 50.0:
                    time.sleep(0.05)
                    print(upbit.buy_market_order(ticker, after_enter_money))
                else:
                    if revenue_rate <= -5.0:
                        time.sleep(0.05)
                        print(upbit.buy_market_order(
                            ticker, after_enter_money))
        else:
            print("not_on_my_hand")
            # if rsi60_min_now <= 30.0 and get_has_coin_cnt(balances) < max_coin_cnt:

            if rsi60_min_before <= 30.0 and rsi60_min_now > 30.0 and uf.get_has_coin_cnt(balances) < max_coin_cnt:
                time.sleep(0.05)
                print(upbit.buy_market_order(ticker, first_enter_money))

    except Exception as e:
        print(e)


print("----------------------------------------")
