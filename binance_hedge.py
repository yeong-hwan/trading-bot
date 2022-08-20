# -------- libraries ---------
import ccxt
import time
import pprint
import json
# -------- import key & functions & alert ---------
import encrypt_key
import original_key
import bf
import line_alert
import traceback


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

balance = binance.fetch_balance(params={"type": "future"})

tickers = binance.fetch_tickers()
invest_rate = 0.2
coin_cnt = 5

message_status = ""

print("---------------------------------------------")
message_status += "\n\n--------------------------------------\n"

line_alert.send_message("binance_hedge running")
# --------------- ccxt substitution -------------------------


def create_limit_buy_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'limit', 'buy', amount, price, params)


def create_limit_sell_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'limit', 'sell', amount, price, params)


def create_market_buy_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'market', 'buy', amount, price, params)


def create_market_sell_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'limit', 'sell', amount, price, params)


# ----------------- json control ---------------------
print("---------------------------------------------")


break_through_list = list()

break_through_file_path = "/var/trading-bot/break_through_list.json"
try:
    with open(break_through_file_path, 'r') as json_file:
        break_through_list = json.load(json_file)

except Exception as e:
    print("| Exception by First | break_through")

    message_status += "| Exception by First | break_through\n"


change_value_dict = dict()

change_value_file_path = "/var/trading-bot/change_value_dict.json"
try:
    with open(change_value_file_path, 'r') as json_file:
        change_value_dict = json.load(json_file)

except Exception as e:
    print("| Exception by First | change_value")

    message_status += "| Exception by First | change_value\n"

balance = binance.fetch_balance(params={"type": "future"})
time.sleep(0.1)

# ------------------ setting options ----------------------
set_leverage = 3
top_coin_list = bf.get_top_coin_list(binance, coin_cnt+2)

time.sleep(0.1)

# -------------- time monitor ---------------------
# print(time_info)

# if want to execute bot, server time = set time - 9
time_info = time.gmtime()
hour_server = time_info.tm_hour
minute = time_info.tm_min

mid_day_server = "AM"
if hour_server >= 12:
    hour_server -= 12
    mid_day_server = "PM"

hour_kst = hour_server + 9

mid_day_kst = mid_day_server
if hour_kst >= 12:
    hour_kst -= 12
    if mid_day_server == "PM":
        mid_day_kst = "AM"
    else:
        mid_day_kst = "PM"

print("---------------------------------------------\n|")
message_status += "--------------------------------------\n"

print(f"| Server time | {hour_server} {mid_day_server} : {minute}")
print(f"| KST (UTC+9) | {hour_kst} {mid_day_kst} : {minute}\n|")
message_status += f"|\n| Server time | {hour_server} {mid_day_server} : {minute}\n"
message_status += f"| KST (UTC+9) | {hour_kst} {mid_day_kst} : {minute}\n|\n"

print("| -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|")
message_status += "| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|\n"

exchange_rate = bf.get_usd_krw()
total_money_usd = float(balance['USDT']['total'])
total_money_krw = total_money_usd * exchange_rate
used_money = float(balance['USDT']['used'])
free_money = float(balance['USDT']['free'])
total_usd = format(total_money_usd, ',')
total_krw = format(total_money_krw, ',')

print("| Total USD:", total_usd, "$")
print("| Total KRW:", total_krw, "₩")
print("| Exchange Rate:", exchange_rate, "$")
print("| Positioned:", used_money, "$")
print("| Remainder:", free_money, "$", "\n|")
message_status += f"| Total USD: {total_usd} $\n"
message_status += f"| Total KRW: {total_krw} ₩\n"
message_status += f"| Exchange Rate: {exchange_rate} $\n"
message_status += f"| Positioned: {used_money} $\n"
message_status += f"| Remainder: {free_money} $\n|\n"

print("| -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|")
message_status += "| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|\n"

print("| Leverage:", set_leverage, "\n|")
message_status += f"| Leverage: {set_leverage}\n|\n"

print("---------------------------------------------\n")
message_status += "--------------------------------------\n"

# -------------------- line alert -------------------------
try:
    if minute == 0 and mid_day_kst == "PM" and hour_kst <= 11:
        line_alert.send_message(message_status)
except Exception as e:
    print("Exception:", e)


try:
    # except btc, eth
    top_coin_list.remove("BTC/USDT")
    top_coin_list.remove("ETH/USDT")
except Exception as e:
    print("Exception", e)


# ------------------- working part ------------------------
ticker_order = 1

for ticker in tickers:
    try:
        if "/USDT" in ticker:
            target_coin_ticker = ticker
            message_ticker = ""

            # break trought positioned OR top coin list
            if bf.check_coin_in_list(break_through_list, ticker) == True or bf.check_coin_in_list(top_coin_list, ticker) == True:
                time.sleep(0.2)

                print(f"{ticker_order}.")
                message_ticker += f"\n\n{ticker_order}.\n"

                ticker_order += 1

                print("-------", "target_coin_ticker:",
                      target_coin_ticker, "-------\n|")

                message_ticker += f"--------- {target_coin_ticker} ---------\n|\n"

                target_coin_symbol = ticker.replace("/", "")
                time.sleep(0.05)

                get_min_amount_tuple = bf.get_min_amount(
                    binance, target_coin_ticker)

                minimum_amount = get_min_amount_tuple[0]
                message_ticker += get_min_amount_tuple[1]

                print("|\n| -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|")
                print("| minimum_amount:", minimum_amount, "EA")
                message_ticker += "|\n| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|\n"
                message_ticker += f"| minimum_amount: {minimum_amount} EA\n"

                # print("|", balance['USDT'], "\n|")

                leverage = 0

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)

                max_amount = float(binance.amount_to_precision(target_coin_ticker, bf.get_amount(
                    float(balance['USDT']['total']), coin_price, invest_rate / coin_cnt))) * set_leverage

                # first enter 2
                # DCA 2, 4, 8, 16
                # 1/15 enter

                buy_amount = max_amount / 15.0
                buy_amount = float(binance.amount_to_precision(
                    target_coin_ticker, buy_amount))

                # round
                buy_amount = round(buy_amount, 5)
                minimum_amount = round(minimum_amount, 5)
                max_amount = round(max_amount, 5)

                if buy_amount < minimum_amount:
                    buy_amount = minimum_amount

                print("| maximum_amount:", max_amount, "EA")
                message_ticker += f"| maximum_amount: {max_amount} EA\n"

                print("| buy_amount:", buy_amount, "EA\n|")
                message_ticker += f"| buy_amount: {buy_amount} EA\n|\n"

                max_DCA_amount = max_amount - buy_amount

                amt_long, amt_short = 0, 0
                entry_price_long, entry_price_short = 0, 0

                isolated = True

                if max_amount == 0:
                    line_alert.send_message("pass by max_amount is zero")
                    continue

                # short position
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'SHORT':
                        amt_short = float(position["positionAmt"])
                        entry_price_short = float(position['entryPrice'])
                        leverage = float(position['leverage'])
                        isolated = position['isolated']
                        break

                # long position
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'LONG':
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

                # break through case
                if bf.check_coin_in_list(break_through_list, ticker) == True:

                    # no position
                    if abs(amt_short) == 0 and abs(amt_long) == 0:
                        binance.cancel_all_orders(target_coin_ticker)
                        time.sleep(0.1)

                        break_through_list.remove(target_coin_ticker)

                        with open(break_through_file_path, 'w') as outfile:
                            json.dump(break_through_list, outfile)

                        # line_alert.send_message(
                        #     "RSI Divergence End:" + target_coin_ticker)

                    # readjustment average price
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

#
#
#

                # -------------------- buy logic ----------------------
                # not positioned in break through list
                else:
                    # logic period: 5m
                    if minute % 5 == 0:
                        candle_5m = bf.get_ohlcv(
                            binance, target_coin_ticker, '5m')

                        change_value = (
                            float(candle_5m['high'][-2]) - float(candle_5m['low'][-2])) * 0.5

                        if change_value < coin_price * 0.0025:
                            change_value = coin_price * 0.0025

                        # high point
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

                        high_point_1 = round(high_point_1, 5)
                        high_value_1 = round(high_value_1, 5)
                        high_point_2 = round(high_point_2, 5)
                        high_value_2 = round(high_value_2, 5)

                        print("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
                        print(
                            f"| high_point_1 X: {high_point_1} | high_value_1 Y: {high_value_1}")
                        print(
                            f"| high_point_2 X: {high_point_2} | high_value_2 Y: {high_value_2}")

                        message_ticker += "| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n"
                        message_ticker += f"| high_point_1 X: {high_point_1}\n| high_value_1 Y: {high_value_1}\n"
                        message_ticker += f"| high_point_2 X: {high_point_2}\n| high_value_2 Y: {high_value_2}\n"

                        is_long_divergence = False

                        # valid when find two points
                        if high_point_1 != 0 and high_point_2 != 0:
                            if abs(amt_long) == 0 and candle_5m['close'][-(high_point_1)] < candle_5m['close'][-(high_point_2)] and len(break_through_list) < coin_cnt:
                                if high_value_1 <= 35.0 or high_value_2 <= 35.0:
                                    is_long_divergence = True

                        print(f"| Long_divergence: {is_long_divergence}")
                        message_ticker += f"| Long_divergence: {is_long_divergence}\n"

                        # low point
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

                        low_point_1 = round(low_point_1, 5)
                        low_value_1 = round(low_value_1, 5)
                        low_point_2 = round(low_point_2, 5)
                        low_value_2 = round(low_value_2, 5)

                        print("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
                        print(
                            f"| low_point_1 X: {low_point_1} | low_value_1 Y: {low_value_1}")
                        print(
                            f"| low_point_2 X: {low_point_2} | low_value_2 Y: {low_value_2}")

                        message_ticker += "| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n"
                        message_ticker += f"| low_point_1 X: {low_point_1}\n| low_value_1 Y: {low_value_1}\n"
                        message_ticker += f"| low_point_2 X: {low_point_2}\n| low_value_2 Y: {low_value_2}\n"

                        is_short_divergence = False

                        # valid when find two points
                        if low_point_1 != 0 and low_point_2 != 0:
                            if abs(amt_long) == 0 and candle_5m['close'][-(low_point_1)] < candle_5m['close'][-(low_point_2)] and len(break_through_list) < coin_cnt:
                                if low_value_1 >= 65.0 or low_value_2 >= 65.0:
                                    is_short_divergence = True

                        print(f"| Short_divergence: {is_short_divergence}")
                        message_ticker += f"| Short_divergence: {is_short_divergence}\n"

                        line_alert.send_message(
                            f"\n\n| {target_coin_ticker}\n| Short: {is_short_divergence}\n| Long: {is_long_divergence}")
#
#
#

                    # -------------------- sell logic ----------------------
                        # long position chance
                        if is_long_divergence == True and is_short_divergence == False:

                            # should delete
                            line_alert.send_message("long position chance")

                            params = {
                                'positionSide': 'LONG'
                            }
                            data = binance.create_market_buy_order(
                                target_coin_ticker, buy_amount, params)

                            target_price = data['price'] + change_value

                            print(binance.create_limit_sell_order(
                                target_coin_ticker, data['amount'], target_price, params))

                            line_alert.send_message("476")
                            total_DCA_amt = 0
                            DCA_amt = buy_amount

                            print("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
                            print("| DCA_amt:", DCA_amt)

                            i = 1

                            line_data = None

                            line_alert.send_message(
                                f"{total_DCA_amt} {DCA_amt} {max_DCA_amount}")

                            while total_DCA_amt + DCA_amt <= max_DCA_amount:
                                line_alert.send_message("DCA_491")

                                print("| -------", i, "Grid", "------")

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

                                line_alert.send_message(line_data)

                                total_DCA_amt += DCA_amt

                                i += 1
                                time.sleep(0.1)

                            line_alert.send_message("513")

                            stop_price = line_data['price'] - \
                                (change_value * 2.0)
                            try:
                                bf.set_stop_loss_long_price(
                                    binance, target_coin_ticker, stop_price, False)
                            except Exception as e:
                                line_alert.send_message(
                                    "Long Exception: " + str(e))

                            line_alert.send_message("524")

                            change_value_dict[target_coin_ticker] = change_value

                            line_alert.send_message("528")

                            with open(change_value_file_path, 'w') as outfile:
                                json.dump(change_value_dict, outfile)

                            line_alert.send_message("533")

                            break_through_list.append(target_coin_ticker)

                            line_alert.send_message("537")

                            with open(break_through_file_path, 'w') as outfile:
                                json.dump(break_through_list, outfile)

                            line_alert.send_message("542")

                            line_alert.send_message("RSI Divergence Start Long : " + target_coin_ticker + " X : " + str(
                                high_point_1) + "|" + str(high_value_1) + ", Y : " + str(high_point_2) + "|" + str(high_value_2))

                            balance = binance.fetch_balance(
                                params={"type": "future"})

                        # short position chance
                        if is_short_divergence == True and is_long_divergence == False:

                            # should delete
                            line_alert.send_message("short position chance")

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

                            print("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
                            print("| DCA_amt:", DCA_amt)

                            i = 1

                            line_data = None

                            line_alert.send_message(
                                f"{total_DCA_amt} {DCA_amt} {max_DCA_amount}")

                            while total_DCA_amt + DCA_amt <= max_DCA_amount:

                                print("| -------", i, "Grid", "------")

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

                            break_through_list.append(target_coin_ticker)

                            with open(break_through_file_path, 'w') as outfile:
                                json.dump(break_through_list, outfile)

                            change_value_dict[target_coin_ticker] = change_value

                            with open(change_value_file_path, 'w') as outfile:
                                json.dump(change_value_dict, outfile)

                            line_alert.send_message("RSI Divergence Start Short : " + target_coin_ticker + " X : " + str(
                                low_point_1) + "|" + str(low_value_1) + ", Y : " + str(low_point_2) + "|" + str(low_value_2))

                            balance = binance.fetch_balance(
                                params={"type": "future"})

                print("--------------------------------------------\n")
                message_ticker += "--------------------------------------\n"

                # try:
                #     if mid_day_kst == "PM" and minute == 0 and hour_kst <= 11:
                #         line_alert.send_message(message_ticker)
                # except Exception as e:
                #     print("Exception:", e)

    except Exception as e:
        print("Exception:", e)
        line_alert.send_message("Exception: " + str(e))
        line_alert.send_message(traceback.format_exc())
