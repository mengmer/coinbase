"""
《邢不行-2020新版|Python数字货币量化投资课程》
无需编程基础，助教答疑服务，专属策略网站，一旦加入，永续更新。
课程详细介绍：https://quantclass.cn/crypto/class
邢不行微信: xbx9025
本程序作者: 邢不行

# 课程内容
择时策略实盘需要的signal
"""
import pandas as pd
import random

pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 1000)


# 将None作为信号返回
def real_signal_none(df, now_pos, avg_price, para):
    """
    发出空交易信号
    :param df:
    :param now_pos:
    :param avg_price:
    :param para:
    :return:
    """

    return None


# 随机生成交易信号
def real_signal_random(df, now_pos, avg_price, para):
    """
    随机发出交易信号
    :param df:
    :param now_pos:
    :param avg_price:
    :param para:
    :return:
    """

    r = random.random()
    # return 1
    if r <= 0.25:
        return -1
    elif r <= 0.5:
        return -1
    elif r <= 0.75:
        return -1
    else:
        return None


# 布林策略实盘交易信号
def real_signal_simple_bolling(df, now_pos, avg_price, para=[200, 2]):
    """
    实盘产生布林线策略信号的函数，和历史回测函数相比，计算速度更快。
    布林线中轨：n天收盘价的移动平均线
    布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
    布林线上轨：n天收盘价的移动平均线 - m * n天收盘价的标准差
    当收盘价由下向上穿过上轨的时候，做多；然后由上向下穿过中轨的时候，平仓。
    当收盘价由上向下穿过下轨的时候，做空；然后由下向上穿过中轨的时候，平仓。
    :param df:  原始数据
    :param para:  参数，[n, m]
    :return:
    """

    # ===策略参数
    # n代表取平均线和标准差的参数
    # m代表标准差的倍数
    n = int(para[0])
    m = para[1]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].rolling(n).mean()  # 此处只计算最后几行的均线值，因为没有加min_period参数
    median = df.iloc[-1]['median']
    median2 = df.iloc[-2]['median']
    # 计算标准差
    df['std'] = df['close'].rolling(n).std(ddof=0)  # ddof代表标准差自由度，只计算最后几行的均线值，因为没有加min_period参数
    std = df.iloc[-1]['std']
    std2 = df.iloc[-2]['std']
    # 计算上轨、下轨道
    upper = median + m * std
    lower = median - m * std
    upper2 = median2 + m * std2
    lower2 = median2 - m * std2

    # ===寻找交易信号
    signal = None
    close = df.iloc[-1]['close']
    close2 = df.iloc[-2]['close']
    # 找出做多信号
    if (close > upper) and (close2 <= upper2):
        signal = 1
    # 找出做空信号
    elif (close < lower) and (close2 >= lower2):
        signal = -1
    # 找出做多平仓信号
    elif (close < median) and (close2 >= median2):
        signal = 0
    # 找出做空平仓信号
    elif (close > median) and (close2 <= median2):
        signal = 0

    return signal


def bolling_new(df, now_pos, avg_price, para=[200, 2, 0.01]):
    # ===策略参数
    n = int(para[0])
    m = para[1]
    p = para[2]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度
    df['upper'] = df['median'] + m * df['std']
    df['lower'] = df['median'] - m * df['std']
    df['bias'] = abs(df['close'] / df['median'] - 1)

    # ===计算信号
    # 找出做多信号
    condition1 = df['close'] > df['upper']  # 当前K线的收盘价 > 上轨
    condition2 = df['close'].shift(1) <= df['upper'].shift(1)  # 之前K线的收盘价 <= 上轨
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # 找出做多平仓信号
    condition1 = df['close'] < df['median']  # 当前K线的收盘价 < 中轨
    condition2 = df['close'].shift(1) >= df['median'].shift(1)  # 之前K线的收盘价 >= 中轨
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 找出做空信号
    condition1 = df['close'] < df['lower']  # 当前K线的收盘价 < 下轨
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)  # 之前K线的收盘价 >= 下轨
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # 找出做空平仓信号
    condition1 = df['close'] > df['median']  # 当前K线的收盘价 > 中轨
    condition2 = df['close'].shift(1) <= df['median'].shift(1)  # 之前K线的收盘价 <= 中轨
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 修改开仓信号
    df['signal2'] = df['signal']
    df['signal2'].fillna(method='ffill', inplace=True)
    df.loc[df['signal'] != 0, 'signal'] = None
    condition1 = df['signal2'] == 1
    condition2 = df['signal2'] == -1
    df.loc[(condition1 | condition2) & (df['bias'] <= p), 'signal'] = df['signal2']

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # ===删除无关变量
    df.drop(['median', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)
    # df.to_csv('b.csv')
    # df['signal'].fillna(method='ffill', inplace=True)
    return df.iloc[-1]['signal']


def bolling_new_ema_pingjuncha_stopEarly(df, now_pos, avg_price, para=[200, 2, 0.01]):  # 改进布林

    """
    不使用std，而使用平均差作为上下轨计算标准
    将ma 换为更平滑的ema
    加入止盈代码，使用短周期和长周期的价差做参考，低于最低价差则说明趋势反转，止盈。
    :param df:
    :param para:
    :return:
    """

    # ===策略参数
    n = int(para[0])
    m = para[1]
    p = para[2]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].ewm(span=n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['cha'] = abs(df['close'] - df['median'])
    # 计算平均差
    df['ping_jun_cha'] = df['cha'].rolling(n, min_periods=1).mean()

    # 计算上轨、下轨道
    df['upper'] = df['median'] + m * df['ping_jun_cha']
    df['lower'] = df['median'] - m * df['ping_jun_cha']
    df['bias'] = abs(df['close'] / df['median'] - 1)

    # n周期close 最高价
    df['close_upper1'] = df['close'].rolling(window=n).max().shift()
    # n周期前n周期 close 最高价
    df['close_upper2'] = df['close'].rolling(window=n).max().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_upper'] = df['close_upper1'] - df['close_upper2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_upper_max'] = df['diff_close_upper'].rolling(window=n).max().shift()
    df['diff_close_upper_min'] = df['diff_close_upper'].rolling(window=n).min().shift()

    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    # condition1 = df['diff_close_upper'] < df['diff_close_upper_min']

    # n周期close 最高价
    df['close_lower1'] = df['close'].rolling(window=n).min().shift()
    # n周期前n周期 close 最高价
    df['close_lower2'] = df['close'].rolling(window=n).min().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_lower'] = df['close_lower1'] - df['close_lower2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_lower_max'] = df['diff_close_lower'].rolling(window=n).max().shift()
    df['diff_close_lower_min'] = df['diff_close_lower'].rolling(window=n).min().shift()

    # ===计算信号
    # 找出做多信号
    condition1 = df['close'] > df['upper']  # 当前K线的收盘价 > 上轨
    condition2 = df['close'].shift(1) <= df['upper'].shift(1)  # 之前K线的收盘价 <= 上轨
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # 找出做多平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_upper'] < df['diff_close_upper_min']
    # 当前价格破上轨
    condition2 = df['close'] <= df['upper']
    # 前一周期的价格在上轨之上
    condition3 = df['close'].shift() >= df['upper'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 0

    condition1 = df['close'] < df['median']  # 当前K线的收盘价 < 中轨
    condition2 = df['close'].shift(1) >= df['median'].shift(1)  # 之前K线的收盘价 >= 中轨
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 找出做空信号
    condition1 = df['close'] < df['lower']  # 当前K线的收盘价 < 下轨
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)  # 之前K线的收盘价 >= 下轨
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # 找出做空平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_lower'] > df['diff_close_lower_max']
    # 当前价格破下轨
    condition2 = df['close'] >= df['lower']
    # 前一周期的价格在下轨之下
    condition3 = df['close'].shift() <= df['lower'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_short'] = 0

    condition1 = df['close'] > df['median']  # 当前K线的收盘价 > 中轨
    condition2 = df['close'].shift(1) <= df['median'].shift(1)  # 之前K线的收盘价 <= 中轨
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 修改开仓信号
    df['signal2'] = df['signal']
    df['signal2'].fillna(method='ffill', inplace=True)
    df.loc[df['signal'] != 0, 'signal'] = None
    condition1 = df['signal2'] == 1
    condition2 = df['signal2'] == -1
    df.loc[(condition1 | condition2) & (df['bias'] <= p), 'signal'] = df['signal2']

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # ===删除无关变量
    df.drop(['median', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)
    # df.to_csv('b.csv')
    # df['signal'].fillna(method='ffill', inplace=True)
    return df.iloc[-1]['signal']


def bolling_new_ema_pingjuncha_stopEarly_only(df, now_pos, avg_price, para=[200, 2, 0.01]):  # 改进布林

    """
    不使用std，而使用平均差作为上下轨计算标准
    将ma 换为更平滑的ema
    止盈代码
    无中线止损

    :param df:
    :param para:
    :return:
    """

    # ===策略参数
    n = int(para[0])
    m = para[1]
    p = para[2]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].ewm(span=n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['cha'] = abs(df['close'] - df['median'])
    # 计算平均差
    df['ping_jun_cha'] = df['cha'].rolling(n, min_periods=1).mean()

    # 计算上轨、下轨道
    df['upper'] = df['median'] + m * df['ping_jun_cha']
    df['lower'] = df['median'] - m * df['ping_jun_cha']
    df['bias'] = abs(df['close'] / df['median'] - 1)

    # n周期close 最高价
    df['close_upper1'] = df['close'].rolling(window=n).max().shift()
    # n周期前n周期 close 最高价
    df['close_upper2'] = df['close'].rolling(window=n).max().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_upper'] = df['close_upper1'] - df['close_upper2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_upper_max'] = df['diff_close_upper'].rolling(window=n).max().shift()
    df['diff_close_upper_min'] = df['diff_close_upper'].rolling(window=n).min().shift()

    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    # condition1 = df['diff_close_upper'] < df['diff_close_upper_min']

    # n周期close 最高价
    df['close_lower1'] = df['close'].rolling(window=n).min().shift()
    # n周期前n周期 close 最高价
    df['close_lower2'] = df['close'].rolling(window=n).min().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_lower'] = df['close_lower1'] - df['close_lower2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_lower_max'] = df['diff_close_lower'].rolling(window=n).max().shift()
    df['diff_close_lower_min'] = df['diff_close_lower'].rolling(window=n).min().shift()

    # ===计算信号
    # 找出做多信号
    condition1 = df['close'] > df['upper']  # 当前K线的收盘价 > 上轨
    condition2 = df['close'].shift(1) <= df['upper'].shift(1)  # 之前K线的收盘价 <= 上轨
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # 找出做多平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_upper'] < df['diff_close_upper_min']
    # 当前价格破上轨
    condition2 = df['close'] <= df['upper']
    # 前一周期的价格在上轨之上
    condition3 = df['close'].shift() >= df['upper'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 0

    # 找出做空信号
    condition1 = df['close'] < df['lower']  # 当前K线的收盘价 < 下轨
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)  # 之前K线的收盘价 >= 下轨
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # 找出做空平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_lower'] > df['diff_close_lower_max']
    # 当前价格破下轨
    condition2 = df['close'] >= df['lower']
    # 前一周期的价格在下轨之下
    condition3 = df['close'].shift() <= df['lower'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_short'] = 0

    # 去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 修改开仓信号
    df['signal2'] = df['signal']
    df['signal2'].fillna(method='ffill', inplace=True)
    df.loc[df['signal'] != 0, 'signal'] = None
    condition1 = df['signal2'] == 1
    condition2 = df['signal2'] == -1
    df.loc[(condition1 | condition2) & (df['bias'] <= p), 'signal'] = df['signal2']

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # ===删除无关变量
    df.drop(['median', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)
    # df.to_csv('b.csv')
    # df['signal'].fillna(method='ffill', inplace=True)
    return df.iloc[-1]['signal']


def bolling_new_ema_pingjuncha_stopEarly_stopAtReverse(df, now_pos, avg_price, para=[200, 2, 0.01, 3]):  # 改进布林

    """
    不使用std，而使用平均差作为上下轨计算标准
    将ma 换为更平滑的ema

    :param df:
    :param para:
    :return:
    """

    # ===策略参数
    n = int(para[0])
    m = para[1]
    p = para[2]
    s = para[3]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].ewm(span=n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['cha'] = abs(df['close'] - df['median'])
    # 计算平均差
    df['ping_jun_cha'] = df['cha'].rolling(n, min_periods=1).mean()

    # 计算上轨、下轨道
    df['upper'] = df['median'] + m * df['ping_jun_cha']
    df['lower'] = df['median'] - m * df['ping_jun_cha']
    df['bias'] = abs(df['close'] / df['median'] - 1)

    df['upper2'] = df['median'] + s * df['ping_jun_cha']
    df['lower2'] = df['median'] - s * df['ping_jun_cha']

    # n周期close 最高价
    df['close_upper1'] = df['close'].rolling(window=n).max().shift()
    # n周期前n周期 close 最高价
    df['close_upper2'] = df['close'].rolling(window=n).max().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_upper'] = df['close_upper1'] - df['close_upper2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_upper_max'] = df['diff_close_upper'].rolling(window=n).max().shift()
    df['diff_close_upper_min'] = df['diff_close_upper'].rolling(window=n).min().shift()

    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    # condition1 = df['diff_close_upper'] < df['diff_close_upper_min']

    # n周期close 最高价
    df['close_lower1'] = df['close'].rolling(window=n).min().shift()
    # n周期前n周期 close 最高价
    df['close_lower2'] = df['close'].rolling(window=n).min().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_lower'] = df['close_lower1'] - df['close_lower2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_lower_max'] = df['diff_close_lower'].rolling(window=n).max().shift()
    df['diff_close_lower_min'] = df['diff_close_lower'].rolling(window=n).min().shift()

    # ===计算信号
    # 找出做多信号
    condition1 = df['close'] > df['upper']  # 当前K线的收盘价 > 上轨
    condition2 = df['close'].shift(1) <= df['upper'].shift(1)  # 之前K线的收盘价 <= 上轨
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # 找出做多平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_upper'] < df['diff_close_upper_min']
    # 当前价格破上轨
    condition2 = df['close'] <= df['upper']
    # 前一周期的价格在上轨之上
    condition3 = df['close'].shift() >= df['upper'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 0

    condition1 = df['close'] < df['median']  # 当前K线的收盘价 < 中轨
    condition2 = df['close'].shift(1) >= df['median'].shift(1)  # 之前K线的收盘价 >= 中轨
    condition3 = df['close'] > df['upper2']
    df.loc[(condition1 & condition2) | condition3, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 找出做空信号
    condition1 = df['close'] < df['lower']  # 当前K线的收盘价 < 下轨
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)  # 之前K线的收盘价 >= 下轨
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # 找出做空平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_lower'] > df['diff_close_lower_max']
    # 当前价格破下轨
    condition2 = df['close'] >= df['lower']
    # 前一周期的价格在下轨之下
    condition3 = df['close'].shift() <= df['lower'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_short'] = 0

    condition1 = df['close'] > df['median']  # 当前K线的收盘价 > 中轨
    condition2 = df['close'].shift(1) <= df['median'].shift(1)  # 之前K线的收盘价 <= 中轨
    condition3 = df['close'] < df['lower2']
    df.loc[(condition1 & condition2) | condition3, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 修改开仓信号
    df['signal2'] = df['signal']
    df['signal2'].fillna(method='ffill', inplace=True)
    df.loc[df['signal'] != 0, 'signal'] = None
    condition1 = df['signal2'] == 1
    condition2 = df['signal2'] == -1
    df.loc[(condition1 | condition2) & (df['bias'] <= p), 'signal'] = df['signal2']

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']
    df['long_dot'] = df.loc[df['signal'] == 1.0, 'open']
    df['clear_dot'] = df.loc[df['signal'] == 0.0, 'open']
    df['short_dot'] = df.loc[df['signal'] == -1.0, 'open']

    # ===删除无关变量
    df.drop(['median', 'upper', 'lower'], axis=1, inplace=True)
    # df.to_csv('b.csv')
    # df['signal'].fillna(method='ffill', inplace=True)
    return df.iloc[-1]['signal']


def bolling_new_ema_pingjuncha_stopEarly_stopAtProfitEnough(df, now_pos, avg_price, para=[200, 2, 0.01, 0.02]):  # 改进布林

    """
    不使用std，而使用平均差作为上下轨计算标准
    将ma 换为更平滑的ema

    :param df:
    :param para:
    :return:
    """

    # ===策略参数
    n = int(para[0])
    m = para[1]
    p = para[2]
    p_enough = para[3]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].ewm(span=n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['cha'] = abs(df['close'] - df['median'])
    # 计算平均差
    df['ping_jun_cha'] = df['cha'].rolling(n, min_periods=1).mean()

    # 计算上轨、下轨道
    df['upper'] = df['median'] + m * df['ping_jun_cha']
    df['lower'] = df['median'] - m * df['ping_jun_cha']
    df['bias'] = abs(df['close'] / df['median'] - 1)

    # n周期close 最高价
    df['close_upper1'] = df['close'].rolling(window=n).max().shift()
    # n周期前n周期 close 最高价
    df['close_upper2'] = df['close'].rolling(window=n).max().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_upper'] = df['close_upper1'] - df['close_upper2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_upper_max'] = df['diff_close_upper'].rolling(window=n).max().shift()
    df['diff_close_upper_min'] = df['diff_close_upper'].rolling(window=n).min().shift()

    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    # condition1 = df['diff_close_upper'] < df['diff_close_upper_min']

    # n周期close 最高价
    df['close_lower1'] = df['close'].rolling(window=n).min().shift()
    # n周期前n周期 close 最高价
    df['close_lower2'] = df['close'].rolling(window=n).min().shift(n + 1)
    # 两个最高价形成的价差
    df['diff_close_lower'] = df['close_lower1'] - df['close_lower2']
    # 这个最高价形成的价差的n周期最大，最小值
    df['diff_close_lower_max'] = df['diff_close_lower'].rolling(window=n).max().shift()
    df['diff_close_lower_min'] = df['diff_close_lower'].rolling(window=n).min().shift()

    # ===计算信号
    # 找出做多信号
    condition1 = df['close'] > df['upper']  # 当前K线的收盘价 > 上轨
    condition2 = df['close'].shift(1) <= df['upper'].shift(1)  # 之前K线的收盘价 <= 上轨
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 将产生做多信号的那根K线的signal设置为1，1代表做多

    # 找出做多平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_upper'] < df['diff_close_upper_min']
    # 当前价格破上轨
    condition2 = df['close'] <= df['upper']
    # 前一周期的价格在上轨之上
    condition3 = df['close'].shift() >= df['upper'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_long'] = 0

    condition1 = df['close'] < df['median']  # 当前K线的收盘价 < 中轨
    condition2 = df['close'].shift(1) >= df['median'].shift(1)  # 之前K线的收盘价 >= 中轨
    df.loc[condition1 & condition2, 'signal_long'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 找出做空信号
    condition1 = df['close'] < df['lower']  # 当前K线的收盘价 < 下轨
    condition2 = df['close'].shift(1) >= df['lower'].shift(1)  # 之前K线的收盘价 >= 下轨
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 将产生做空信号的那根K线的signal设置为-1，-1代表做空

    # 找出做空平仓信号
    # 两个高价轨道形成的价差 跌破 其n周期最小值，说明最高价形成的价差有反向
    condition1 = df['diff_close_lower'] > df['diff_close_lower_max']
    # 当前价格破下轨
    condition2 = df['close'] >= df['lower']
    # 前一周期的价格在下轨之下
    condition3 = df['close'].shift() <= df['lower'].shift()

    df.loc[condition1 & condition2 & condition3, 'signal_short'] = 0

    condition1 = df['close'] > df['median']  # 当前K线的收盘价 > 中轨
    condition2 = df['close'].shift(1) <= df['median'].shift(1)  # 之前K线的收盘价 <= 中轨
    df.loc[condition1 & condition2, 'signal_short'] = 0  # 将产生平仓信号当天的signal设置为0，0代表平仓

    # 去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1, skipna=True)
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # 修改开仓信号
    df['signal2'] = df['signal']
    df['signal2'].fillna(method='ffill', inplace=True)
    df.loc[df['signal'] != 0, 'signal'] = None
    condition1 = df['signal2'] == 1
    condition2 = df['signal2'] == -1
    df.loc[(condition1 | condition2) & (df['bias'] <= p), 'signal'] = df['signal2']
    df.loc[(df['bias'] >= p_enough), 'signal'] = 0

    # 去除重复信号
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']
    df['long_dot'] = df.loc[df['signal'] == 1.0, 'open']
    df['clear_dot'] = df.loc[df['signal'] == 0.0, 'open']
    df['short_dot'] = df.loc[df['signal'] == -1.0, 'open']

    # ===删除无关变量
    df.drop(['median', 'upper', 'lower'], axis=1, inplace=True)
    # df.to_csv('b.csv')
    # df['signal'].fillna(method='ffill', inplace=True)
    return df.iloc[-1]['signal']
