import pyupbit
import time

access = "JW7G0hr9xnBWpejlquZkEW78db0GXX1ROrPgK6ws"
secret = "tWLOFowynAXsT5UitsM4tPPuL1uIxrMNtYThIDZj"
upbit = pyupbit.Upbit(access, secret)

# market_price_buy
# coins = pyupbit.get_tickers(fiat="KRW")

# for coin in coins:
#     print(coin, pyupbit.get_current_price(coin))
#     time.sleep(0.1)

#     if coin == "KRW-BTC" or coin == "KRW-TRX":
#         print(upbit. buy_market_order(coin, 10000))  # print return error log
#         print("Buy Done", coin)

# market_price_sell
# btc_balance = upbit.get_balance("KRW-BTC")
# print(upbit.sell_market_order("KRW-BTC", btc_balance))

btc_target_price = pyupbit.get_current_price("KRW-BTC")

btc_target_price *= 0.99
my_won = 10000

print(upbit.sell_limit_order(
    "KRW-BTC", pyupbit.get_tick_size(btc_target_price), my_won / btc_target_price))

# balances lookup
my_balances = upbit.get_balances()
print(my_balances)

for coin_balance in my_balances:
    ticker = coin_balance['currency']
    if ticker == "KRW":
        continue
    print(ticker, coin_balance['balance'], coin_balance['avg_buy_price'])
    avg_price = float(coin_balance['avg_buy_price'])

    now_price = pyupbit.get_current_price("KRW-" + ticker)
    print("now_price:", now_price, "avg_price:", avg_price)

    # revenue_rate
    revenue_rate = (
        now_price - avg_price) / avg_price * 100.0
    print("revene_rate:", revenue_rate)

    if revenue_rate >= 1.7:
        print("sell working")
        print(upbit.sell_limite_order()
              "KRW-" + ticker, pyupbit.get_tick_size(now_price * 1.002))
        # get_tick_size mediate tick unit
