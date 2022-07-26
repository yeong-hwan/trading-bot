# -------- libraries ---------
import ccxt
import time
import pandas as pd
import pprint
import json
# -------- import key & functions & alert ---------
import encrypt_key
import original_key
import bf
import line_alert

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


tickers = binance.fetch_tickers()
invest_rate = 0.2
coin_cnt = 5.0

# ----------------- json control ---------------------
break_through_list = list()

break_through_file_path = "/var/trading-bot/break_through_list.json"
try:
    with open(break_through_file_path, 'r') as json_file:
        break_through_list = json.load(json_file)

except Exception as e:
    print("Exception by First")


change_value_dict = dict()

change_value_file_path = "/var/trading-bot/change_value_dict.json"
try:
    with open(change_value_file_path, 'r') as json_file:
        change_value_dict = json.load(json_file)

except Exception as e:
    print("Exception by First")


balance = binance.fetch_balance(params={"type": "future"})
time.sleep(0.1)


set_leverage = 10
# -------------- time & line alert ---------------------
#

# print(time_info)
# print(line_alert.send_message("Binance Trading Bot Working"))

# if want to execute bot, server time = set time - 9

top_coin_list = bf.get_top_coin_list(binance, 10)

# ---- trading for except btc, eth ----
# try:
#     top_coin_list.remove("BTC/USDT")
#     top_coin_list.remove("ETH/USDT")
# except Exception as e:
#     print("Exception", e)

balance = binance.fetch_balance(params={"type": "future"})
time.sleep(0.1)

time_info = time.gmtime()
hour = time_info.tm_hour
minute = time_info.tm_min
print(hour, minute)
# ------------------- working part ------------------------
for ticker in tickers:

    try:
        if "/USDT" in ticker:
            target_coin_ticker = ticker

            # top coin list OR break trought positioned
            if bf.check_coin_in_list(top_coin_list, ticker) == True or bf.check_coin_in_list(break_through_list, ticker) == True:
                time.sleep(0.2)
                print("target_coin_ticker:", target_coin_ticker)

                target_coin_symbol = ticker.replace("/", "")
                time.sleep(0.05)

                minimum_amount = bf.get_min_amount(binance, target_coin_ticker)
                print("minimum_amount:", minimum_amount)

                print(balance['USDT'])
                print("Total Money:", float(balance['USDT']['total']))
                print("Remain Money:", float(balance['USDT']['free']))

                leverage = 0

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)
                max_amount = float(binance.amount_to_precision(target_coin_ticker, bf.get_amount(
                    float(balance['USDT']['total']), coin_price, invest_rate / coin_cnt))) * set_leverage

                print("max_amount:", max_amount)

                # first enter 2
                # DCA 2, 4, 8, 16
                # 1/15 enter

                buy_amount = max_amount / 15.0
                buy_amount = float(binance.amount_to_precision(
                    target_coin_ticker, buy_amount))

                if buy_amount < minimum_amount:
                    buy_amount = minimum_amount

                print("buy_amount:", buy_amount)

                max_DCA_amount = max_amount - buy_amount

                amt_long, amt_short = 0, 0
                entry_price_long, entry_price_short = 0, 0

                isolated = True

                # short position
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'SHORT':
                        print(position)
                        amt_short = float(position["positionAmt"])
                        entry_price_short = float(position['entryPrice'])
                        leverage = float(position['leverage'])
                        isolated = position['isolated']
                        break

                # lon position
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'LONG':
                        print(position)
                        amt_long = float(position["positionAmt"])
                        entry_price_long = float(position['entryPrice'])
                        leverage = float(position['leverage'])
                        isolated = position['isolated']
                        break

                # --------- leverage & isloate setting -----------
                if leverage != set_leverage:
                    try:
                        print(binance.fapiPrivate_post_leverage(
                            {'symbol': target_coin_symbol, 'leverage': set_leverage}))
                    except Exception as e:
                        print("Exception:", e)

                if isolated == False:
                    try:
                        print(binance.fapiPrivate_post_margintype(
                            {'symbol': target_coin_symbol, 'marginType': 'ISOLATED'}))
                    except Exception as e:
                        print("Exception:", e)

                if bf.check_coin_in_list(break_through_list, ticker) == True:
                    # no position
                    if abs(amt_short) == 0 and abs(amt_long) == 0:
                        binance.cancel_all_orders(target_coin_ticker)
                        time.sleep(0.1)

                        break_through_list.remove(target_coin_ticker)

                        with open(break_through_file_path, 'w') as outfile:
                            json.dump(break_through_list, outfile)

                        line_alert.send_message(
                            "RSI Divergence End:" + target_coin_ticker)

                    # average price readjustment
                    else:
                        orders = binance.fetch_orders(target_coin_ticker)

                        if abs(amt_long) > 0:
                            target_price = entry_price_long + \
                                (change_value_dict[target_coin_ticker] * 1.0)

                            for order in orders:
                                # take profit condition
                                if order['status'] == "open" and order['info']['positionSide'] == "LONG" and order['side'] == "sell" and order['type'] == "limit":

                                    # average price changed case
                                    if float(order['price']) != float(binance.price_to_precision(target_coin_ticker, target_price)):
                                        binance.cancel_order(
                                            order['id'], target_coin_ticker)
                                        time.sleep(0.1)

                                        params = {
                                            'positionSide': 'LONG'
                                        }
                                        print(binance.create_limit_sell_order(
                                            target_coin_ticker, abs(amt_long), target_price, params))

                        if abs(amt_short) > 0:
                            target_price = entry_price_short - \
                                (change_value_dict[target_coin_ticker] * 1.0)

                            for order in orders:
                                # take profit condition
                                if order['status'] == "open" and order['info']['positionSide'] == "SHORT" and order['side'] == "buy" and order['type'] == "limit":

                                    # average price changed case
                                    if float(order['price']) != float(binance.price_to_precision(target_coin_ticker, target_price)):
                                        binance.cancel_order(
                                            order['id'], target_coin_ticker)
                                        time.sleep(0.1)

                                        params = {
                                            'positionSide': 'SHORT'
                                        }
                                        print(binance.create_limit_buy_order(
                                            target_coin_ticker, abs(amt_short), target_price, params))

                else:
                    # logic period: 5m
                    if minute & 5 == 0:
                        candle_5m = bf.get_ohlcv(
                            binance, target_coin_ticker, '5m')

                        change_value = (
                            float(candle_5m['high'][-2]) - float(candle_5m['low'][-2])) * 0.5

                        if change_value < coin_price * 0.0025:
                            change_value = coin_price * 0.0025

                        high_point_1, high_point_2 = 0, 0
                        high_value_1, high_value_2 = 0, 0

                        now_rsi = bf.get_RSI(candle_5m, 14, -1)

                        for idx in range(3, 20):
                            left_rsi = bf.get_RSI(candle_5m, 14, -(idx-1))
                            mid_rsi = bf.get_RSI(candle_5m, 14, -(idx))
                            right_rsi = bf.get_RSI(candle_5m, 14, -(idx+1))

                            # V sahpe point
                            if left_rsi > mid_rsi < right_rsi:
                                # non setting
                                if high_point_1 == 0:
                                    if now_rsi > mid_rsi:
                                        high_point_1 = idx
                                        high_value_1 = mid_rsi

                                # setted
                                else:
                                    # non setting
                                    if high_point_2 == 0:
                                        if high_value_1 > mid_rsi:
                                            high_point_2 = idx
                                            high_value_2 = mid_rsi

                                            # we find two point for drawing trend line
                                            break

                        print("high_point_1 X:", high_point_1,
                              "high_value_1 Y:", high_value_1)
                        print("high_point_2 X:", high_point_2,
                              "high_value_2 Y:", high_value_2)

                        is_long_divergence = False

                        # valid when find two points
                        if high_point_1 != 0 and high_point_2 != 0:
                            if abs(amt_long) == 0 and candle_5m['close'][-(high_point_1)] < candle_5m['close'][-(high_point_2)] and len(break_through_list) < coin_cnt:
                                if high_value_1 <= 35.0 or high_value_2 <= 35.0:
                                    is_long_divergence = True

                        low_point_1, low_point_2 = 0, 0
                        low_value_1, low_value_2 = 0, 0

                        for idx in range(3, 20):
                            left_rsi = bf.get_RSI(candle_5m, 14, -(idx-1))
                            mid_rsi = bf.get_RSI(candle_5m, 14, -(idx))
                            right_rsi = bf.get_RSI(candle_5m, 14, -(idx+1))

                            # ^ sahpe point
                            if left_rsi < mid_rsi > right_rsi:
                                # non setting
                                if low_point_1 == 0:
                                    if now_rsi < mid_rsi:
                                        low_point_1 = idx
                                        low_value_1 = mid_rsi

                                # setted
                                else:
                                    # non setting
                                    if low_point_2 == 0:
                                        if low_value_1 < mid_rsi:
                                            low_point_2 = idx
                                            low_value_2 = mid_rsi

                                            # we find two point for drawing trend line
                                            break

                        print("low_point_1 X:", low_point_1,
                              "low_value_1 Y:", low_value_1)
                        print("low_point_2 X:", low_point_2,
                              "low_value_2 Y:", low_value_2)

                        is_short_divergence = False

                        # valid when find two points
                        if low_point_1 != 0 and low_point_2 != 0:
                            if abs(amt_long) == 0 and candle_5m['close'][-(low_point_1)] < candle_5m['close'][-(low_point_2)] and len(break_through_list) < coin_cnt:
                                if high_value_1 >= 65.0 or high_value_2 >= 65.0:
                                    is_short_divergence = True

                        # long position chance
                        if is_long_divergence == True and is_short_divergence == False:
                            params = {
                                'positionSide': 'LONG'
                            }
                            data = binance.create_market_buy_order(
                                target_coin_ticker, buy_amount, params)

                            target_price = data['price'] + change_value
                            print(binance.create_limit_sell_order(
                                target_coin_ticker, data['amount'], target_price, params))

                            total_DCA_amt = 0
                            DCA_amt = buy_amount

                            print("DCA_amt:", DCA_amt)

                            i = 1

                            line_data = None

                            while total_DCA_amt + DCA_amt <= max_DCA_amount:
                                print("-------", i, "Grid", "------")

                                # DCA_amt down -> more grid
                                DCA_amt *= 2.0

                                # change_value * 2.0 -> grid distance
                                DCA_price = data['price'] - \
                                    ((change_value * 2.0) * float(i))

                                params = {
                                    'positionSide': 'LONG'
                                }

                                line_data = binance.create_limit_buy_order(
                                    target_coin_ticker, DCA_amt, DCA_price, params)

                                total_DCA_amt += DCA_amt

                                i += 1
                                time.sleep(0.1)

                            stop_price = line_data['price'] - \
                                (change_value * 2.0)
                            bf.set_stop_loss_long_price(
                                binance, target_coin_ticker, stop_price, False)

                            change_value_dict[target_coin_ticker] = change_value

                            with open(change_value_file_path, 'w') as outfile:
                                json.dump(change_value_dict, outfile)

                            break_through_list.append(target_coin_ticker)

                            with open(break_through_file_path, 'w') as outfile:
                                json.dump(break_through_list, outfile)

                            line_alert.send_message("RSI Divergence Start Long : " + target_coin_ticker + " X : " + str(
                                high_point_1) + "|" + str(high_value_1) + ", Y : " + str(high_point_2) + "|" + str(high_value_2))

                            balance = binance.fetch_balance(
                                params={"type": "future"})

                        # short position chance
                        if is_short_divergence == True and is_long_divergence == False:
                            params = {
                                'positionSide': 'SHORT'
                            }
                            data = binance.create_market_sell_order(
                                target_coin_ticker, buy_amount, params)

                            target_price = data['price'] - change_value
                            print(binance.create_limit_buy_order(
                                target_coin_ticker, data['amount'], target_price, params))

                            total_DCA_amt = 0
                            DCA_amt = buy_amount

                            print("DCA_amt:", DCA_amt)

                            i = 1

                            line_data = None

                            while total_DCA_amt + DCA_amt <= max_DCA_amount:
                                print("-------", i, "Grid", "------")

                                # DCA_amt down -> more grid
                                DCA_amt *= 2.0

                                # change_value * 2.0 -> grid distance
                                DCA_price = data['price'] + \
                                    ((change_value * 2.0) * float(i))

                                params = {
                                    'positionSide': 'SHORT'
                                }

                                line_data = binance.create_limit_sell_order(
                                    target_coin_ticker, DCA_amt, DCA_price, params)

                                total_DCA_amt += DCA_amt

                                i += 1
                                time.sleep(0.1)

                            stop_price = line_data['price'] + \
                                (change_value * 2.0)
                            bf.set_stop_loss_short_price(
                                binance, target_coin_ticker, stop_price, False)

                            change_value_dict[target_coin_ticker] = change_value

                            with open(change_value_file_path, 'w') as outfile:
                                json.dump(change_value_dict, outfile)

                            break_through_list.append(target_coin_ticker)

                            with open(break_through_file_path, 'w') as outfile:
                                json.dump(break_through_list, outfile)

                            line_alert.send_message("RSI Divergence Start Short : " + target_coin_ticker + " X : " + str(
                                low_point_1) + "|" + str(low_value_1) + ", Y : " + str(low_point_2) + "|" + str(lowh_value_2))

                            balance = binance.fetch_balance(
                                params={"type": "future"})

    except Exception as e:
        print("Exception:", e)
