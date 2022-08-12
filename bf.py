import pandas as pd
import time
import pprint
# ----------------- binance functions -----------------------


'''
ohclv: candle data
standard_date
    -1: today(now)
    -2: yesterday / before
'''

# --------------- ccxt substitution -------------------------


def create_limit_buy_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'limit', 'buy', amount, price, params)


def create_limit_sell_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'limit', 'sell', amount, price, params)


def create_market_buy_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'market', 'buy', amount, price, params)


def create_market_sell_order(self, symbol, amount, price, params={}):
    return self.create_order(symbol, 'limit', 'sell', amount, price, params)


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


# period: (1d,4h,1h,15m,10m,1m ...)
def get_ohlcv(binance, ticker, period):
    btc_ohlcv = binance.fetch_ohlcv(ticker, period)
    ohlcv = pd.DataFrame(btc_ohlcv, columns=[
                         'datetime', 'open', 'high', 'low', 'close', 'volume'])
    ohlcv['datetime'] = pd.to_datetime(ohlcv['datetime'], unit='ms')
    ohlcv.set_index('datetime', inplace=True)
    return ohlcv


def get_BB(ohlcv, period, st):
    dic_bb = dict()

    close = ohlcv["close"]

    ma = close.rolling(period).mean()
    sdddev = close.rolling(period).std()

    dic_bb['ma'] = float(ma[st])
    dic_bb['upper'] = float(ma[st]) + 2.0*float(sdddev[st])
    dic_bb['lower'] = float(ma[st]) - 2.0*float(sdddev[st])

    return dic_bb


def get_IC(ohlcv, st):

    high_prices = ohlcv['high']
    close_prices = ohlcv['close']
    low_prices = ohlcv['low']

    nine_period_high = ohlcv['high'].shift(-2-st).rolling(window=9).max()
    nine_period_low = ohlcv['low'].shift(-2-st).rolling(window=9).min()
    ohlcv['conversion'] = (nine_period_high + nine_period_low) / 2

    period26_high = high_prices.shift(-2-st).rolling(window=26).max()
    period26_low = low_prices.shift(-2-st).rolling(window=26).min()
    ohlcv['base'] = (period26_high + period26_low) / 2

    ohlcv['sunhang_span_a'] = (
        (ohlcv['conversion'] + ohlcv['base']) / 2).shift(26)

    period52_high = high_prices.shift(-2-st).rolling(window=52).max()
    period52_low = low_prices.shift(-2-st).rolling(window=52).min()
    ohlcv['sunhang_span_b'] = ((period52_high + period52_low) / 2).shift(26)

    ohlcv['huhang_span'] = close_prices.shift(-26)

    nine_period_high_real = ohlcv['high'].rolling(window=9).max()
    nine_period_low_real = ohlcv['low'].rolling(window=9).min()
    ohlcv['conversion'] = (nine_period_high_real + nine_period_low_real) / 2

    period26_high_real = high_prices.rolling(window=26).max()
    period26_low_real = low_prices.rolling(window=26).min()
    ohlcv['base'] = (period26_high_real + period26_low_real) / 2

    dic_ic = dict()

    dic_ic['conversion'] = ohlcv['conversion'].iloc[st]
    dic_ic['base'] = ohlcv['base'].iloc[st]
    dic_ic['huhang_span'] = ohlcv['huhang_span'].iloc[-27]
    dic_ic['sunhang_span_a'] = ohlcv['sunhang_span_a'].iloc[-1]
    dic_ic['sunhang_span_b'] = ohlcv['sunhang_span_b'].iloc[-1]

    return dic_ic


def get_MACD(ohlcv, st):
    macd_short, macd_long, macd_signal = 12, 26, 9

    ohlcv["MACD_short"] = ohlcv["close"].ewm(span=macd_short).mean()
    ohlcv["MACD_long"] = ohlcv["close"].ewm(span=macd_long).mean()
    ohlcv["MACD"] = ohlcv["MACD_short"] - ohlcv["MACD_long"]
    ohlcv["MACD_signal"] = ohlcv["MACD"].ewm(span=macd_signal).mean()

    dic_macd = dict()

    dic_macd['macd'] = ohlcv["MACD"].iloc[st]
    dic_macd['macd_siginal'] = ohlcv["MACD_signal"].iloc[st]
    dic_macd['ocl'] = dic_macd['macd'] - dic_macd['macd_siginal']

    return dic_macd


def get_stoch(ohlcv, period, st):
    dic_stoch = dict()

    ndays_high = ohlcv['high'].rolling(window=period, min_periods=1).max()
    ndays_low = ohlcv['low'].rolling(window=period, min_periods=1).min()
    fast_k = (ohlcv['close'] - ndays_low)/(ndays_high - ndays_low)*100
    slow_d = fast_k.rolling(window=3, min_periods=1).mean()

    dic_stoch['fast_k'] = fast_k.iloc[st]
    dic_stoch['slow_d'] = slow_d.iloc[st]

    return dic_stoch

# cut_rate: (1.0: -100% clearing, 0.1: -10% stop loss)


def set_stop_loss(binance, ticker, cut_rate, Rest=True):

    if Rest == True:
        time.sleep(0.1)

    orders = binance.fetch_orders(ticker)

    StopLossOk = False
    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market':
            # print(order)
            StopLossOk = True
            break

    if StopLossOk == False:

        if Rest == True:
            time.sleep(10.0)

        balance = binance.fetch_balance(params={"type": "future"})

        if Rest == True:
            time.sleep(0.1)

        amt = 0
        entryPrice = 0
        leverage = 0
        for posi in balance['info']['positions']:
            if posi['symbol'] == ticker.replace("/", ""):
                entryPrice = float(posi['entryPrice'])
                amt = float(posi['positionAmt'])
                leverage = float(posi['leverage'])

        side = "sell"
        if amt < 0:
            side = "buy"

        danger_rate = ((100.0 / leverage) * cut_rate) * 1.0

        stopPrice = entryPrice * (1.0 - danger_rate*0.01)

        if amt < 0:
            stopPrice = entryPrice * (1.0 + danger_rate*0.01)

        params = {
            'stopPrice': stopPrice,
            'closePosition': True
        }

        print("side:", side, "   stopPrice:",
              stopPrice, "   entryPrice:", entryPrice)
        print(binance.create_order(ticker, 'STOP_MARKET',
              side, abs(amt), stopPrice, params))

        print("------ STOPLOSS SETTING DONE ------")


def set_stop_loss_price(binance, ticker, stop_price, Rest=True):

    if Rest == True:
        time.sleep(0.1)

    orders = binance.fetch_orders(ticker)

    StopLossOk = False
    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market':
            # print(order)
            StopLossOk = True
            break

    if StopLossOk == False:

        if Rest == True:
            time.sleep(10.0)

        balance = binance.fetch_balance(params={"type": "future"})

        if Rest == True:
            time.sleep(0.1)

        amt = 0
        entryPrice = 0

        for posi in balance['info']['positions']:
            if posi['symbol'] == ticker.replace("/", ""):
                entryPrice = float(posi['entryPrice'])
                amt = float(posi['positionAmt'])

        side = "sell"
        if amt < 0:
            side = "buy"

        params = {
            'stopPrice': stop_price,
            'closePosition': True
        }

        print("side:", side, "   stopPrice:",
              stop_price, "   entryPrice:", entryPrice)
        print(binance.create_order(ticker, 'STOP_MARKET',
              side, abs(amt), stop_price, params))

        print("------ STOPLOSS SETTING DONE ------")

# amount for buying


def get_amount(usdt, coin_price, rate):

    target = usdt * rate

    amount = target / coin_price
    # at least 0.001 coin for trading
    if amount < 0.001:
        amount = 0.001

    #print("amout", amout)
    return amount


def get_coin_current_price(binance, ticker):
    coin_info = binance.fetch_ticker(ticker)
    coin_price = coin_info['last']  # coin_info['close'] == coin_info['last']

    return coin_price


def exist_order_side(binance, ticker, Side):
    # 주문 정보를 읽어온다.
    orders = binance.fetch_orders(ticker)

    exist_flag = False
    for order in orders:
        if order['status'] == "open" and order['side'] == Side:
            exist_flag = True

    return exist_flag


# 거래대금 폭발 여부 첫번째: 캔들 정보, 두번째: 이전 5개의 평균 거래량보다 몇 배 이상 큰지
# 이전 캔들이 그 이전 캔들 5개의 평균 거래금액보다 몇 배이상 크면 거래량 폭발로 인지하고 True return
# 현재 캔들[-1]은 막 시작했으므로 이전 캔들[-2]을 봐야 함
def is_volume_explode(ohlcv, st):

    result = False
    try:
        avg_volume = (float(ohlcv['volume'][-3]) + float(ohlcv['volume'][-4]) + float(
            ohlcv['volume'][-5]) + float(ohlcv['volume'][-6]) + float(ohlcv['volume'][-7])) / 5.0
        if avg_volume * st < float(ohlcv['volume'][-2]):
            result = True
    except Exception as e:
        print("IsVolumePung ---:", e)

    return result


def get_positioned_coin_cnt(binance):

    balances = binance.fetch_balance(params={"type": "future"})
    time.sleep(0.1)

    tickers = binance.fetch_tickers()

    coin_cnt = 0
    for ticker in tickers:

        if "/USDT" in ticker:
            target_coin_symbol = ticker.replace("/", "")

            amt = 0
            for position in balances['info']['positions']:
                if position['symbol'] == target_coin_symbol:
                    amt = float(position['positionAmt'])
                    break

            if amt != 0:
                coin_cnt += 1

    return coin_cnt


def get_top_coin_list(binance, top):
    # print("--------------Get Top Coin List Start-------------------")

    # 선물 마켓에서 거래중인 코인을 가져옵니다.
    tickers = binance.fetch_tickers()
    # pprint.pprint(tickers)

    dic_coin_money = dict()
    # 모든 선물 거래가능한 코인을 가져온다.
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

    # print("--------------GetTopCoinList End-------------------")

    return coin_list


# 해당되는 리스트안에 해당 코인이 있는지 여부를 리턴
def check_coin_in_list(coin_list, ticker):
    coin_in_list = False
    for coin_ticker in coin_list:
        if coin_ticker == ticker:
            coin_in_list = True
            break

    return coin_in_list


# 트레일링 스탑 함수
# https://blog.naver.com/zhanggo2/222664158175
def create_trailing_sell_order(binance, ticker, amount, activation_price=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activation_price == None:
        # activate from current price
        params = {
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'activationPrice': activation_price,
            'callbackRate': rate
        }

    print(binance.create_order(
        ticker, 'TRAILING_STOP_MARKET', 'sell', amount, None, params))


def create_trailing_buy_order(binance, ticker, amount, activation_price=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activation_price == None:
        # activate from current price
        params = {
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'activationPrice': activation_price,
            'callbackRate': rate
        }

    print(binance.create_order(
        ticker, 'TRAILING_STOP_MARKET', 'buy', amount, None, params))


# 트레일링 스탑 함수 for hedge
# https://blog.naver.com/zacra/222662884649

def create_trailing_sell_order_long(binance, ticker, amount, activation_price=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activation_price == None:
        # activate from current price
        params = {
            'positionSide': 'LONG',
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'positionSide': 'LONG',
            'activationPrice': activation_price,
            'callbackRate': rate
        }

    print(binance.create_order(
        ticker, 'TRAILING_STOP_MARKET', 'sell', amount, None, params))


def create_trailing_buy_order_short(binance, ticker, amount, activation_price=None, rate=0.2):
    # rate range min 0.1, max 5 (%) from binance rule
    if rate < 0.1:
        rate = 0.1
    elif rate > 5:
        rate = 5

    if activation_price == None:
        # activate from current price
        params = {
            'positionSide': 'SHORT',
            'callbackRate': rate
        }
    else:
        # given activationprice
        params = {
            'positionSide': 'SHORT',
            'activationPrice': activation_price,
            'callbackRate': rate
        }

    print(binance.create_order(
        ticker, 'TRAILING_STOP_MARKET', 'buy', amount, None, params))


# 최소 주문 단위 금액 구하는 함수
# https://blog.naver.com/zhanggo2/222722244744
def get_min_amount(binance, ticker):
    limit_values = binance.markets[ticker]['limits']

    min_amount = limit_values['amount']['min']
    min_cost = limit_values['cost']['min']
    min_price = limit_values['price']['min']

    coin_info = binance.fetch_ticker(ticker)
    coin_price = coin_info['last']

    print("| min_cost: ", min_cost)
    print("| min_amount: ", min_amount)
    print("| min_price: ", min_price, "$")
    print("| Coin_price: ", coin_price, "$")

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
    return minimum_amount


# 현재 평가금액
def get_total_real_money(balance):
    return float(balance['info']['totalWalletBalance']) + float(balance['info']['totalUnrealizedProfit'])


# 코인의 평가 금액
def get_coin_real_money(balance, ticker, position_side):

    money = 0

    for posi in balance['info']['positions']:
        if posi['symbol'] == ticker.replace("/", "") and posi['positionSide'] == position_side:
            money = float(posi['initialMargin']) + \
                float(posi['unrealizedProfit'])
            break

    return money

# ------------------------------------------------------------------------


# -------------------------- Hedge functions ----------------------------


def set_stop_loss_long(binance, ticker, cut_rate, Rest=True):

    if Rest == True:
        time.sleep(0.1)
    orders = binance.fetch_orders(ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "LONG":
            binance.cancel_order(order['id'], ticker)

            break

    if Rest == True:
        time.sleep(2.0)

    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)

    amt_b = 0
    entryPrice_b = 0
    leverage = 0

    for posi in balance['info']['positions']:
        if posi['symbol'] == ticker.replace("/", "") and posi['positionSide'] == 'LONG':

            amt_b = float(posi['positionAmt'])
            entryPrice_b = float(posi['entryPrice'])
            leverage = float(posi['leverage'])
            break

    side = "sell"

    danger_rate = ((100.0 / leverage) * cut_rate) * 1.0

    stopPrice = entryPrice_b * (1.0 - danger_rate*0.01)

    params = {
        'positionSide': 'LONG',
        'stopPrice': stopPrice,
        'closePosition': True
    }

    print("side:", side, "   stopPrice:",
          stopPrice, "   entryPrice:", entryPrice_b)

    print(binance.create_order(ticker, 'STOP_MARKET',
          side, abs(amt_b), stopPrice, params))

    print("####STOPLOSS SETTING DONE ######################")


def set_stop_loss_short(binance, ticker, cut_rate, Rest=True):

    if Rest == True:
        time.sleep(0.1)
    orders = binance.fetch_orders(ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "SHORT":
            binance.cancel_order(order['id'], ticker)

    if Rest == True:
        time.sleep(2.0)

    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)

    amt_s = 0
    entryPrice_s = 0
    leverage = 0

    for posi in balance['info']['positions']:
        if posi['symbol'] == ticker.replace("/", "") and posi['positionSide'] == 'SHORT':

            amt_s = float(posi['positionAmt'])
            entryPrice_s = float(posi['entryPrice'])
            leverage = float(posi['leverage'])

            break

    side = "buy"

    danger_rate = ((100.0 / leverage) * cut_rate) * 1.0

    stopPrice = entryPrice_s * (1.0 + danger_rate*0.01)

    params = {
        'positionSide': 'SHORT',
        'stopPrice': stopPrice,
        'closePosition': True
    }

    print("side:", side, "   stopPrice:",
          stopPrice, "   entryPrice:", entryPrice_s)

    print(binance.create_order(ticker, 'STOP_MARKET',
          side, abs(amt_s), stopPrice, params))

    print("####STOPLOSS SETTING DONE ######################")


def set_stop_loss_long_price(binance, ticker, stop_price, Rest=True):

    if Rest == True:
        time.sleep(0.1)
    orders = binance.fetch_orders(ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "LONG":
            binance.cancel_order(order['id'], ticker)

            break

    if Rest == True:
        time.sleep(2.0)

    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)

    amt_b = 0
    entryPrice_b = 0

    for posi in balance['info']['positions']:
        if posi['symbol'] == ticker.replace("/", "") and posi['positionSide'] == 'LONG':

            amt_b = float(posi['positionAmt'])
            entryPrice_b = float(posi['entryPrice'])
            break

    side = "sell"

    params = {
        'positionSide': 'LONG',
        'stopPrice': stop_price,
        'closePosition': True
    }

    print("side:", side, "   stopPrice:",
          stop_price, "   entryPrice:", entryPrice_b)

    print(binance.create_order(ticker, 'STOP_MARKET',
          side, abs(amt_b), stop_price, params))

    print("####STOPLOSS SETTING DONE ######################")


def set_stop_loss_short_price(binance, ticker, stop_price, Rest=True):

    if Rest == True:
        time.sleep(0.1)
    orders = binance.fetch_orders(ticker)

    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market' and order['info']['positionSide'] == "SHORT":
            binance.cancel_order(order['id'], ticker)

    if Rest == True:
        time.sleep(2.0)

    balance = binance.fetch_balance(params={"type": "future"})
    if Rest == True:
        time.sleep(0.1)

    amt_s = 0
    entryPrice_s = 0

    for posi in balance['info']['positions']:
        if posi['symbol'] == ticker.replace("/", "") and posi['positionSide'] == 'SHORT':

            amt_s = float(posi['positionAmt'])
            entryPrice_s = float(posi['entryPrice'])

            break

    side = "buy"

    params = {
        'positionSide': 'SHORT',
        'stopPrice': stop_price,
        'closePosition': True
    }

    print("side:", side, "   stopPrice:",
          stop_price, "   entryPrice:", entryPrice_s)

    print(binance.create_order(ticker, 'STOP_MARKET',
          side, abs(amt_s), stop_price, params))

    print("####STOPLOSS SETTING DONE ######################")
