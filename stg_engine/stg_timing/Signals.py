from Function import *


# =====简单布林策略
# 策略
def signal_simple_bolling(df, para=[200, 2], proportion=1):
    """
    :param df:
    :param para: n, m
    :return:

    # 布林线策略
    # 布林线中轨：n天收盘价的移动平均线
    # 布林线上轨：n天收盘价的移动平均线 + m * n天收盘价的标准差
    # 布林线上轨：n天收盘价的移动平均线 - m * n天收盘价的标准差
    # 当收盘价由下向上穿过上轨的时候，做多；然后由上向下穿过中轨的时候，平仓。
    # 当收盘价由上向下穿过下轨的时候，做空；然后由下向上穿过中轨的时候，平仓。
    """

    # ===策略参数
    n = int(para[0])
    m = para[1]

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)  # ddof代表标准差自由度
    df['upper'] = df['median'] + m * df['std']
    df['lower'] = df['median'] - m * df['std']

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

    # 合并做多做空信号，去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1,
                                                           skipna=True)  # 若你的pandas版本是最新的，请使用本行代码代替上面一行
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # ===删除无关变量
    # df.drop(['median', 'std', 'upper', 'lower', 'signal_long', 'signal_short'], axis=1, inplace=True)
    df.drop(['std', 'signal_long', 'signal_short'], axis=1, inplace=True)

    # 进行止盈止损
    df = process_stop_loss_close(df, proportion)

    return df


# 策略参数组合
def signal_simple_bolling_para_list(m_list=range(20, 1000 + 20, 20),
                                    n_list=[i / 10 for i in list(np.arange(3, 50 + 2, 2))]):
    """
    产生布林 策略的参数范围
    :param m_list:
    :param n_list:
    :return:
    """
    print('参数遍历范围：')
    print('m_list', list(m_list))
    print('n_list', list(n_list))

    para_list = []

    for m in m_list:
        for n in n_list:
            para = [m, n]
            para_list.append(para)

    return para_list


# =====作者邢不行
# 策略
def signal_xingbuxing(df, para=[200, 2, 0.05], proportion=1):
    """
    针对原始布林策略进行修改。
    bias = close / 均线 - 1
    当开仓的时候，如果bias过大，即价格离均线过远，那么就先不开仓。等价格和均线距离小于bias_pct之后，才按照原计划开仓
    :param df:
    :param para: n,m,bias_pct
    :return:
    """

    # ===策略参数
    n = int(para[0])
    m = float(para[1])
    bias_pct = float(para[2])

    # ===计算指标
    # 计算均线
    df['median'] = df['close'].rolling(n, min_periods=1).mean()
    # 计算上轨、下轨道
    df['std'] = df['close'].rolling(n, min_periods=1).std(ddof=0)
    df['upper'] = df['median'] + m * df['std']
    df['lower'] = df['median'] - m * df['std']
    # 计算bias
    df['bias'] = df['close'] / df['median'] - 1

    # ===计算原始布林策略信号
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

    # ===将long和short合并为signal
    df['signal_short'].fillna(method='ffill', inplace=True)
    df['signal_long'].fillna(method='ffill', inplace=True)
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1)
    df['signal'].fillna(value=0, inplace=True)
    df['raw_signal'] = df['signal']

    # ===根据bias，修改开仓时间
    df['temp'] = df['signal']

    # 将原始信号做多时，当bias大于阀值，设置为空
    condition1 = (df['signal'] == 1)
    condition2 = (df['bias'] > bias_pct)
    df.loc[condition1 & condition2, 'temp'] = None

    # 将原始信号做空时，当bias大于阀值，设置为空
    condition1 = (df['signal'] == -1)
    condition2 = (df['bias'] < -1 * bias_pct)
    df.loc[condition1 & condition2, 'temp'] = None

    # 原始信号刚开仓，并且大于阀值，将信号设置为0
    condition1 = (df['signal'] != df['signal'].shift(1))
    condition2 = (df['temp'].isnull())
    df.loc[condition1 & condition2, 'temp'] = 0

    # 使用之前的信号补全原始信号
    df['temp'].fillna(method='ffill', inplace=True)
    df['signal'] = df['temp']

    # ===将signal中的重复值删除
    temp = df[['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp

    df.drop(['raw_signal', 'median', 'std', 'upper', 'lower', 'bias', 'temp', 'signal_long', 'signal_short'], axis=1,
            inplace=True)

    # 进行止盈止损
    df = process_stop_loss_close(df, proportion)

    return df


# 策略参数组合
def signal_xingbuxing_para_list(m_list=range(20, 1000 + 20, 20), n_list=[i / 10 for i in list(np.arange(3, 50 + 2, 2))],
                                bias_pct_list=[i / 100 for i in list(np.arange(5, 20 + 2, 2))]):
    """
    :param m_list:
    :param n_list:
    :param bias_pct_list:
    :return:
    """
    print('参数遍历范围：')
    print('m_list', list(m_list))
    print('n_list', list(n_list))
    print('bias_pct_list', list(bias_pct_list))

    para_list = []
    for bias_pct in bias_pct_list:
        for m in m_list:
            for n in n_list:
                para = [m, n, bias_pct]
                para_list.append(para)

    return para_list


def signal_add_bias(df, para=[20, 0.05], proportion=1):
    para_ = para[0]
    df['median'] = df['close'].rolling(para_, min_periods=1).mean()
    df['bias'] = df['close'] / df['median'] - 1
    bias_pct = float(para[1])

    df['TYP'] = (df['high'] + df['low'] + df['close']) / 3
    df['H'] = np.where(df['high'] - df['TYP'].shift(1) > 0, df['high'] - df['TYP'].shift(1), 0)
    df['L'] = np.where(df['TYP'].shift(1) - df['low'] > 0, df['TYP'].shift(1) - df['low'], 0)

    # 计算均线
    df['Cr_%s' % (para_)] = df['H'].rolling(para_).sum() / df['L'].rolling(
        para_).sum() * 100

    # =======  找出做多信号 CR 上穿 200
    condition1 = df['Cr_%s' % str(para_)] > 200  # 均线大于0
    # condition2 = df['Cr_%s' % str(params)].shift(1) <= 200  # 上一周期的均线小于等于0
    condition2 = df['Cr_%s' % str(para_)].shift() <= 200
    df.loc[condition1 & condition2, 'signal_long'] = 1  # 1代表做多

    condition1 = df['Cr_%s' % str(para_)] < 50  # 均线大于0
    # condition2 = df['Cr_%s' % str(params)].shift(1) <= 200  # 上一周期的均线小于等于0
    condition2 = df['Cr_%s' % str(para_)].shift() >= 50
    df.loc[condition1 & condition2, 'signal_short'] = -1  # 1代表做多

    # 合并做多做空信号，去除重复信号
    df['signal'] = df[['signal_long', 'signal_short']].sum(axis=1, min_count=1,
                                                           skipna=True)  # 若你的pandas版本是最新的，请使用本行代码代替上面一行
    temp = df[df['signal'].notnull()][['signal']]
    temp = temp[temp['signal'] != temp['signal'].shift(1)]
    df['signal'] = temp['signal']

    # ===根据bias，修改开仓时间
    df['temp'] = df['signal']

    # 将原始信号做多时，当bias大于阀值，设置为空
    condition1 = (df['signal'] == 1)
    condition2 = (df['bias'] > bias_pct)
    df.loc[condition1 & condition2, 'temp'] = None

    # 将原始信号做空时，当bias大于阀值，设置为空
    condition1 = (df['signal'] == -1)
    condition2 = (df['bias'] < -1 * bias_pct)
    df.loc[condition1 & condition2, 'temp'] = None

    # 使用之前的信号补全原始信号
    df['temp'].fillna(method='ffill', inplace=True)
    df['signal'] = df['temp']

    # ===考察是否需要止盈止损
    process_stop_loss_close(df, proportion)

    return df


def signal_add_bias_para_list(para_list=generate_fibonacci_sequence(2, 100), pa=generate_fibonacci_sequence(1, 100)):
    para = []
    for p in para_list:
        for b in pa:
            b = b / 100
            para.append([int(p), b])

    return para
