import ccxt
import time
import pandas as pd
import pprint
import bf

access = "Zd2awwadeB2BFrxvs3tLQixrpVtkM8PfvvCVZAHeaF1RSYWckSOdUfJvwt6elXeF"
secret = "9pumuiCRihNdUTY7BO2d0sRZrBaeII7oERqNe7kDpqKoL9pVDVLQlMSsLFqZ4CGb"

binance = ccxt.binance(config={
    'apiKey': access,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

target_coin_ticker = "BTC/USDT"
target_coin_symbol = "BTCUSDT"

btc = binance.fetch_ticker(target_coin_ticker)
btc_price = btc['close']

pprint.pprint(btc)

balance = binance.fetch_balance(params={"type": "future"})
time.sleep(0.1)

# taker_short
# binance.create_market_sell_order(target_coin_ticker, 0.001)

# taker_long
# binance.create_market_buy_order(target_coin_ticker, 0.001)

# maker_short
# binance.create_limit_sell_order(target_coin_ticker, 0.001, btc_price)

# maker_long
# binance.create_limit_buy_order(target_coin_ticker, 0.001, btc_price)

# ------------------- setting ------------------------
'''
entry_price: average buy price
amt: amount of position
'''

amt = 0
entry_price = 0
leverage = 1
unrealized_profit = 0


for position in balance['info']['positions']:
    if position['symbol'] == target_coin_symbol:
        leverage = float(position['leverage'])
        entry_price = float(position['entryPrice'])
        unrealized_profit = float(position['unrealizedProfit'])
        amt = float(position['positionAmt'])
        break

# set leverage -> 3
try:
    print(binance.fapiPrivate_post_leverage(
        {'symbol': target_coin_symbol, 'leverage': 3}))
except Exception as e:
    print("error:", e)

# --------------------------------------------
coin_price = bf.get_coin_current_price(binance, target_coin_ticker)
max_amount_for_buy = round(bf.get_amount(
    float(balance['USDT']['total']), coin_price, 0.1), 3) * leverage


# short to long (sell position)
abs_amt = abs(amt)

if amt == 0:
    print("NO POSITION")
else:
    if amt < 0:
        print("SHORT POSITION")
    else:
        print("LONG POSITION")

# long sell
entry_price_long = entry_price * 1.001
# short sell
entry_price_short = entry_price * 0.999


# ------------------ status -------------------
print("---------------- indicators info ----------------")
min_candle_15 = bf.get_ohlcv(binance, target_coin_ticker, '15m')
print("Price:", min_candle_15['close'][-3], "->",
      min_candle_15['close'][-2], "->", min_candle_15['close'][-1])
print("5_day_MA:", bf.get_MA(min_candle_15, 5, -3), "->",
      bf.get_MA(min_candle_15, 5, -2), "->", bf.get_MA(min_candle_15, 5, -1))
print("RSI_14:", bf.get_RSI(min_candle_15, 14, -3), "->",
      bf.get_RSI(min_candle_15, 14, -2), "->", bf.get_RSI(min_candle_15, 14, -1))

print("---------------- balance info ----------------")
print(balance['USDT'])
print("total_balance:", float(balance['USDT']['total']))
print("used_money:", float(balance['USDT']['used']))
print("remain_money:", float(balance['USDT']['free']))

print("---------------- position info ----------------")
print("amt:", amt)
print("entry_price:", entry_price)
print("leverage:", leverage)
print("unrealized_profit:", unrealized_profit)
