# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2022/8/3 10:21
# @Author : Meng

from coin_tools import *


def get_coin_his_data(exchange, symbol, time_interval, start_time=None, end_time=None, path=None):
    """
    获取历史数据
    """
    # =====开始循环抓取数据
    df_list = []
    if start_time is None:
        start_time = '2020-01-01 00:00:00'
    if end_time is None:
        end_time = pd.to_datetime(start_time) + timedelta(days=1)
    start_time_since = exchange.parse8601(start_time)
    end_time_since = exchange.parse8601(end_time)
    # 循环获取历史数据
    all_kline_data = []
    while True:
        # okex的v5接口比较特殊，另外处理
        if exchange.name == 'OKEX':
            params = {
                'instId': symbol,
                'bar': time_interval,
                'after': end_time_since,
                'limit': '100'
            }
            # 获取K线使
            kline_data = exchange.public_get_market_history_candles(params=params)['data']
            if kline_data:
                end_time_since = kline_data[-1][0]  # 更新since，为下次循环做准备
                all_kline_data += kline_data
                if int(kline_data[-1][0]) < int(start_time_since):
                    break
        else:
            df = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_interval, since=start_time_since, limit=2000)
            # 整理数据
            df = pd.DataFrame(df, dtype=float)  # 将数据转换为dataframe
            df['candle_begin_time'] = pd.to_datetime(df[0], unit='ms')  # 整理时间
            # 合并数据
            df_list.append(df)
            # 新的since
            t = pd.to_datetime(df.iloc[-1][0], unit='ms')
            print('%s:' % symbol, t, ' --> fetch')
            start_time_since = exchange.parse8601(str(t))
            # 判断是否挑出循环
            if t >= pd.to_datetime(end_time) or df.shape[0] <= 1:
                print('%s:' % symbol, ' --> success fetch all !')
                break
            # 抓取间隔需要暂停2s，防止抓取过于频繁
            time.sleep(2)
    # 对数据进行整理
    df = pd.concat(df_list, ignore_index=True)
    df.rename(columns={0: 'MTS', 1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume'}, inplace=True)
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms') + timedelta(hours=8)
    df = df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]
    # 选取数据时间段
    # df = df[df['candle_begin_time'].dt.date == pd.to_datetime(start_time).date()]
    # 去重、排序
    df.drop_duplicates(subset=['candle_begin_time'], keep='last', inplace=True)
    df.sort_values('candle_begin_time', inplace=True)
    df.reset_index(drop=True, inplace=True)
    # =====保存数据到文件
    if df.shape[0] > 0 and path is not None:
        # 创建交易所文件夹
        path = os.path.join(path, exchange.id)
        if os.path.exists(path) is False:
            os.mkdir(path)
        # 创建spot文件夹
        path = os.path.join(path, 'spot')
        if os.path.exists(path) is False:
            os.mkdir(path)
        # 创建日期文件夹
        path = os.path.join(path, str(pd.to_datetime(start_time).date()) + '_' + str(pd.to_datetime(end_time).date()))
        if os.path.exists(path) is False:
            os.mkdir(path)
        # 拼接文件目录
        file_name = '_'.join([symbol.replace('/', '-'), time_interval]) + '.csv'
        path = os.path.join(path, file_name)
        print('%s:' % symbol, ' --> save to ', path)
        # 储存文件
        df.to_csv(path, index=False)
    return df


def get_coins_his_data(exchange, symbol_list, time_interval, start_time=None, end_time=None, path=None):
    """
    获取多个coin历史数据
    """
    if start_time is None:
        start_time = '2020-01-01 00:00:00'
    if end_time is None:
        end_time = pd.to_datetime(start_time) + timedelta(days=1)
    for coin in symbol_list:
        get_coin_his_data(exchange, coin, time_interval, start_time, end_time, path)
        print('%s: %s - %s fetch %s data success!' % (coin,
                                                      str(pd.to_datetime(start_time).date()),
                                                      str(pd.to_datetime(end_time).date()),
                                                      time_interval))


def get_coin_now_data(exchange, symbol, time_interval):
    """
    获取实时数据
    """
    # ===对火币的limit做特殊处理
    limit = None
    if 'huobi' in exchange.id:
        limit = 2000
    # =====获取最新数据
    data = exchange.fetch_ohlcv(symbol=symbol, timeframe=time_interval, limit=limit)
    # =====整理数据
    df = pd.DataFrame(data, dtype=float)  # 将数据转换为dataframe
    df.rename(columns={0: 'MTS', 1: 'open', 2: 'high',
                       3: 'low', 4: 'close', 5: 'volume'}, inplace=True)  # 重命名
    df['candle_begin_time'] = pd.to_datetime(df['MTS'], unit='ms')  # 整理时间
    df['candle_begin_time_GMT8'] = df['candle_begin_time'] + timedelta(hours=8)  # 北京时间
    return df[['candle_begin_time_GMT8', 'open', 'high', 'low', 'close', 'volume']]


def get_all_symbol_list(exchange):
    """
    获取某交易所所有symbol
    """
    market = exchange.load_markets()
    market = pd.DataFrame(market).T
    return list(market['symbol'])


def get_all_data(start_time=None, end_time=None):
    """
    获取所有数据
    """
    if start_time is None:
        start_time = '2020-03-18 00:00:00'
    if end_time is None:
        end_time = pd.to_datetime(start_time) + timedelta(days=1)
    error_list = []
    # 遍历交易所
    for exchange in [ccxt.huobipro(), ccxt.binance()]:
        symbol_list = get_all_symbol_list(exchange)
        # 遍历交易对
        for symbol in symbol_list:
            if symbol.endswith('/USDT') is False:
                continue
            # 遍历时间周期
            for time_interval in ['5m', '15m']:
                print(exchange.id, symbol, time_interval)
                # 抓取数据并且保存
                try:
                    get_coin_his_data(exchange=exchange, symbol=symbol, time_interval=time_interval,
                                      start_time=start_time, end_time=end_time, path=r"D:\coinbase\coin_data")
                except Exception as e:
                    print(e)
                    error_list.append('_'.join([exchange.id, symbol, time_interval]))


def get_tickers(exchange):
    """
    获取实时数据
    """
    if exchange.has['fetchTickers']:
        data = exchange.fetch_tickers()
        df = pd.DataFrame(data, dtype=float).T
        return df
    else:
        return None


if __name__ == '__main__':
    # =====设定参数
    ex_ba = ccxt.binance()
    ex_okx = ccxt.okex5()  # huobipro, binance, okex5，使用huobi需要增加limit=2000，XRP-USDT-200327
    # huobipro, binance, okex5，使用huobi需要增加limit=2000，XRP-USDT-200327
    sy_list = ['BTC/USDT', 'ETH/USDT', 'EOS/USDT', 'LTC/USDT', 'DOGE/USDT']
    time = '15m'  # 其他可以尝试的值：'1m', '5m', '15m', '30m', '1H', '2H', '1D', '1W', '1M', '1Y'
    start = '2020-01-01 00:00:00'
    end = '2022-08-03 00:00:00'
    # 作业1： 抓取币安历史数据
    get_coins_his_data(exchange=ex_ba, symbol_list=sy_list, time_interval=time,
                       start_time=start, end_time=end,
                       path=r"D:\coinbase\coin_data")
    # 作业2：实时收集okx数据
    get_tickers(ex_okx).to_csv(r"D:\coinbase\coin_data\okex5\tickers.csv")
