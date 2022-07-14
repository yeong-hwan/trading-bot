# -------- libraries ---------
import ccxt
import time
import pandas as pd
import pprint
# -------- import key & functions ---------
import encrypt_key
import original_key
import bf

# ---------- key decoding ---------------
simple_en_decrypt = original_key.simple_en_decrypt(encrypt_key.encrypt_key)
binance_access = simple_en_decrypt.decrypt(original_key.access)
binance_secret = simple_en_decrypt.decrypt(original_key.secret)

binance = ccxt.binance(config={
    'apiKey': binance_access,
    'secret': binance_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

target_coin_ticker = "BTC/USDT"
target_coin_symbol = "BTCUSDT"

btc = binance.fetch_ticker(target_coin_ticker)
coin_price = btc['close']

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

# ---------------- variables ------------------

min_candle_15 = bf.get_ohlcv(binance, target_coin_ticker, '15m')
ma5_before_2 = bf.get_MA(min_candle_15, 5, -4)
ma5_before_1 = bf.get_MA(min_candle_15, 5, -3)
ma5_now = bf.get_MA(min_candle_15, 5, -2)

ma20_now = bf.get_MA(min_candle_15, 20, -2)

rsi_14 = bf.get_RSI(min_candle_15, 14, -1)


# --------------- working part ----------------------
coin_price = bf.get_coin_current_price(binance, target_coin_ticker)

# rate 0.1 -> 10%
max_amount = round(bf.get_amount(
    float(balance['USDT']['total']), coin_price, 0.5), 3) * leverage
one_percent_amount = max_amount / 100.0
first_amount = one_percent_amount * 5.0

"""
DCA: 5 -> 10 -> 20 -> 40 -> 80
"""

# short to long (sell position)
abs_amt = abs(amt)
target_rate = 0.001
target_revenue_rate = target_rate * 100.0

# no position -> taking position
if amt == 0:
    print("NO POSITION")

    # short position
    if ma5_now > ma20_now and ma5_before_2 < ma5_before_1 and ma5_before_1 > ma5_now and rsi_14 >= 35.0:
        print("----- sell / short -----")

        binance.cancel_all_orders(target_coin_ticker)
        time.sleep(0.1)

        coin_price = bf.get_coin_current_price(binance, target_coin_ticker)
        print(binance.create_limit_sell_order(
            target_coin_ticker, first_amount, coin_price))

    # long position
    if ma5_now < ma20_now and ma5_before_2 > ma5_before_1 and ma5_before_1 < ma5_now and rsi_14 <= 65.0:
        print("----- buy / long -----")

        binance.cancel_all_orders(target_coin_ticker)
        time.sleep(0.1)

        coin_price = bf.get_coin_current_price(binance, target_coin_ticker)
        print(binance.create_limit_buy_order(
            target_coin_ticker, first_amount, coin_price))

    bf.set_stop_loss(binance, target_coin_ticker, 0.5)

# after taking position
else:
    buy_percent = abs_amt / one_percent_amount
    print("Buy Percent:", buy_percent)

    # long position revenue_rate
    revenue_rate = (coin_price - entry_price) / entry_price * 100.0

    # short position revenue_rate
    if amt < 0:
        revenue_rate *= -1

    # leverage revenue(profit) rate
    leverage_revenue_rate = revenue_rate * leverage
    print("Revenue Rate:", revenue_rate,
          "Real Revenue Rate:", leverage_revenue_rate)

    # threshold rate for loss cut
    loss_cut_rate = -5.0
    leverage_loss_cut_rate = loss_cut_rate * leverage
    print("Loss Cut Rate:", loss_cut_rate,
          "Real Loss Cut Rate:", leverage_loss_cut_rate)

    # threshold rate for scale
    after_enter_rate = -1.0

    if buy_percent <= 5.0:
        after_enter_rate = -0.5
    elif buy_percent <= 10.0:
        after_enter_amount = -1.0
    elif buy_percent <= 20.0:
        after_enter_amount = -2.0
    elif buy_percent <= 40.0:
        after_enter_amount = -3.0
    elif buy_percent <= 80.0:
        after_enter_rate = -5.0

    leverage_loss_cut_rate = after_enter_rate * leverage
    print("After Enter Rate:", after_enter_rate,
          " Real After Enter Rate:", leverage_loss_cut_rate)

# -----------------------------------------------------------------------------------------
    # short position
    if amt < 0:
        # chance for switch to long position
        if ma5_now < ma20_now and ma5_before_2 > ma5_before_1 and ma5_before_1 < ma5_now:
            # close short & take long
            if revenue_rate >= target_revenue_rate:
                binance.cancel_all_orders(target_coin_ticker)
                time.sleep(0.1)

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)

                print(binance.create_limit_buy_order(
                    target_coin_ticker, first_amount + abs_amt, coin_price))

            bf.set_stop_loss(binance, target_coin_ticker, 0.5)

        # still short has upper hand
        if ma5_now > ma20_now and ma5_before_2 < ma5_before_1 and ma5_before_1 > ma5_now:

            after_enter_amount = abs_amt

            if max_amount < abs_amt + after_enter_amount:
                after_enter_amount = max_amount - abs_amt

            if revenue_rate <= after_enter_rate and max_amount >= abs_amt + after_enter_amount:
                binance.cancel_all_orders(target_coin_ticker)
                time.sleep(0.1)

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)

                # increase short position
                print(binance.create_limit_sell_order(
                    target_coin_ticker, after_enter_amount, coin_price))

            bf.set_stop_loss(binance, target_coin_ticker, 0.5)

        # stop loss
        if revenue_rate <= loss_cut_rate and buy_percent >= 90.0:
            binance.cancel_all_orders(target_coin_ticker)
            time.sleep(0.1)

            coin_price = bf.get_coin_current_price(
                binance, target_coin_ticker)

            print(binance.create_limit_buy_order(
                target_coin_ticker, abs_amt / 2.0, coin_price))

        bf.set_stop_loss(binance, target_coin_ticker, 0.5)

# ----------------------------------------------------------------------------------------
    # long position
    else:
        if ma5_now > ma20_now and ma5_before_2 < ma5_before_1 and ma5_before_1 > ma5_now:
            # close long & take short
            if revenue_rate >= target_revenue_rate:
                binance.cancel_all_orders(target_coin_ticker)
                time.sleep(0.1)

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)

                print(binance.create_limit_sell_order(
                    target_coin_ticker, first_amount + abs_amt, coin_price))

            bf.set_stop_loss(binance, target_coin_ticker, 0.5)

        # still long has upper hand
        if ma5_now < ma20_now and ma5_before_2 > ma5_before_1 and ma5_before_1 < ma5_now:
            after_enter_amount = abs_amt

            if max_amount < abs_amt + after_enter_amount:
                after_enter_amount = max_amount - abs_amt

            if revenue_rate <= after_enter_rate and max_amount >= abs_amt + after_enter_amount:
                binance.cancel_all_orders(target_coin_ticker)
                time.sleep(0.1)

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)

                # increase long position
                print(binance.create_limit_buy_order(
                    target_coin_ticker, after_enter_amount, coin_price))

            bf.set_stop_loss(binance, target_coin_ticker, 0.5)

        # stop loss
        if revenue_rate <= loss_cut_rate and buy_percent >= 90.0:
            binance.cancel_all_orders(target_coin_ticker)
            time.sleep(0.1)

            coin_price = bf.get_coin_current_price(
                binance, target_coin_ticker)

            print(binance.create_limit_sell_order(
                target_coin_ticker, abs_amt / 2.0, coin_price))

        bf.set_stop_loss(binance, target_coin_ticker, 0.5)

bf.set_stop_loss(binance, target_coin_ticker, 0.5)


# long sell
entry_price_long = entry_price * 1.001
# short sell
entry_price_short = entry_price * 0.999


# ------------------ status -------------------
print("---------------- indicators info ----------------")
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
