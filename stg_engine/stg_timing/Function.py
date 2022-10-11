import numpy as np
import pandas as pd


# =====计算资金曲线
def cal_equity_curve(df, slippage=1 / 1000, c_rate=5 / 10000, leverage_rate=3,
                     min_amount=0.01,
                     min_margin_ratio=1 / 100):
    """
    :param df:
    :param slippage:  滑点 ，可以用百分比，也可以用固定值。建议币圈用百分比，股票用固定值
    :param c_rate:  手续费，commission fees，默认为万分之5。不同市场手续费的收取方法不同，对结果有影响。比如和股票就不一样。
    :param leverage_rate:  杠杆倍数
    :param min_amount:  最小下单量
    :param min_margin_ratio: 最低保证金率，低于就会爆仓
    :return:
    """
    # =====下根k线开盘价
    df['next_open'] = df['open'].shift(-1)  # 下根K线的开盘价
    df['next_open'].fillna(value=df['close'], inplace=True)

    # =====找出开仓、平仓的k线
    condition1 = df['pos'] != 0  # 当前周期不为空仓
    condition2 = df['pos'] != df['pos'].shift(1)  # 当前周期和上个周期持仓方向不一样。
    open_pos_condition = condition1 & condition2

    condition1 = df['pos'] != 0  # 当前周期不为空仓
    condition2 = df['pos'] != df['pos'].shift(-1)  # 当前周期和下个周期持仓方向不一样。
    close_pos_condition = condition1 & condition2

    # =====对每次交易进行分组
    df.loc[open_pos_condition, 'start_time'] = df['candle_begin_time']
    df['start_time'].fillna(method='ffill', inplace=True)
    df.loc[df['pos'] == 0, 'start_time'] = pd.NaT

    # =====开始计算资金曲线
    initial_cash = 10000  # 初始资金，默认为10000元
    # ===在开仓时
    # 在open_pos_condition的K线，以开盘价计算买入合约的数量。（当资金量大的时候，可以用5分钟均价）
    df.loc[open_pos_condition, 'contract_num'] = initial_cash * leverage_rate / (min_amount * df['open'])
    df['contract_num'] = np.floor(df['contract_num'])  # 对合约张数向下取整
    # 开仓价格：理论开盘价加上相应滑点
    df.loc[open_pos_condition, 'open_pos_price'] = df['open'] * (1 + slippage * df['pos'])
    # 开仓之后剩余的钱，扣除手续费
    df['cash'] = initial_cash - df['open_pos_price'] * min_amount * df['contract_num'] * c_rate  # 即保证金

    # ===开仓之后每根K线结束时
    # 买入之后cash，contract_num，open_pos_price不再发生变动
    for _ in ['contract_num', 'open_pos_price', 'cash']:
        df[_].fillna(method='ffill', inplace=True)
    df.loc[df['pos'] == 0, ['contract_num', 'open_pos_price', 'cash']] = None

    # ===在平仓时
    # 平仓价格
    df.loc[close_pos_condition, 'close_pos_price'] = df['next_open'] * (1 - slippage * df['pos'])
    # 平仓之后剩余的钱，扣除手续费
    df.loc[close_pos_condition, 'close_pos_fee'] = df['close_pos_price'] * min_amount * df['contract_num'] * c_rate

    # ===计算利润
    # 开仓至今持仓盈亏
    df['profit'] = min_amount * df['contract_num'] * (df['close'] - df['open_pos_price']) * df['pos']
    # 平仓时理论额外处理
    df.loc[close_pos_condition, 'profit'] = min_amount * df['contract_num'] * (
            df['close_pos_price'] - df['open_pos_price']) * df['pos']
    # 账户净值
    df['net_value'] = df['cash'] + df['profit']

    # ===计算爆仓
    # 至今持仓盈亏最小值
    df.loc[df['pos'] == 1, 'price_min'] = df['low']
    df.loc[df['pos'] == -1, 'price_min'] = df['high']
    df['profit_min'] = min_amount * df['contract_num'] * (df['price_min'] - df['open_pos_price']) * df['pos']
    # 账户净值最小值
    df['net_value_min'] = df['cash'] + df['profit_min']
    # 计算保证金率
    df['margin_ratio'] = df['net_value_min'] / (min_amount * df['contract_num'] * df['price_min'])
    # 计算是否爆仓
    df.loc[df['margin_ratio'] <= (min_margin_ratio + c_rate), '是否爆仓'] = 1

    # ===平仓时扣除手续费
    df.loc[close_pos_condition, 'net_value'] -= df['close_pos_fee']
    # 应对偶然情况：下一根K线开盘价格价格突变，在平仓的时候爆仓。此处处理有省略，不够精确。
    df.loc[close_pos_condition & (df['net_value'] < 0), '是否爆仓'] = 1

    # ===对爆仓进行处理
    df['是否爆仓'] = df.groupby('start_time')['是否爆仓'].fillna(method='ffill')
    df.loc[df['是否爆仓'] == 1, 'net_value'] = 0

    # =====计算资金曲线
    df['equity_change'] = df['net_value'].pct_change()
    df.loc[open_pos_condition, 'equity_change'] = df.loc[open_pos_condition, 'net_value'] / initial_cash - 1  # 开仓日的收益率
    df['equity_change'].fillna(value=0, inplace=True)
    df['equity_curve'] = (1 + df['equity_change']).cumprod()

    # =====删除不必要的数据，并存储
    df.drop(['next_open', 'contract_num', 'open_pos_price', 'cash', 'close_pos_price', 'close_pos_fee',
             'profit', 'net_value', 'price_min', 'profit_min', 'net_value_min', 'margin_ratio', '是否爆仓'],
            axis=1, inplace=True)

    return df


def process_stop_loss_close(df, stop_loss_pct):
    """
    止损函数
    :param df:
    :param stop_loss_pct: 止损比例
    :return:
    """
    position = 0  # 持仓方向
    df['原始信号'] = df['signal']
    last_price = np.nan
    # df['last_price'] = np.nan
    # df['stop_loss_price'] = np.nan

    for i in df.index:
        # 开平仓
        if not np.isnan(df.loc[i, 'signal']):
            position = int(df.loc[i, 'signal'])
            if df.loc[i, 'signal']:  # 开仓
                last_price = df.loc[i, 'close']
            else:
                position = int(df.loc[i, 'signal'])
                last_price = np.nan
        # 持仓
        if position:
            stop_loss_price = last_price * (1 - position * stop_loss_pct)
            stop_loss_condition = position * (df.loc[i, 'close'] - stop_loss_price) <= 0  # 止损条件
            df.at[i, 'stop_loss_condition'] = stop_loss_price
            if stop_loss_condition and np.isnan(df.loc[i, 'signal']):
                df.at[i, 'signal'] = 0
                position = 0
                last_price = np.nan
    return df


def write_file(content, path):
    """
    写入文件
    :param content: 写入内容
    :param path: 文件路径
    :return:
    """
    with open(path, 'w', encoding='utf8') as f:
        f.write(content)

# 将数字转为百分数
def num_to_pct(value):
    return '%.2f%%' % (value * 100)


def generate_fibonacci_sequence(min_number, max_number):
    """
    生成费拨那契数列，支持小数的生成
    :param min_number: 最小值
    :param max_number: 最大值
    :return:
    """
    sequence = []
    base = 1
    if min_number < 0:
        base = 10 ** len(str(min_number).split('.')[1])
    last_number = 0
    new_number = 1
    while True:
        last_number, new_number = new_number, last_number + new_number
        if new_number / base > min_number:
            sequence.append(new_number / base)
        if new_number / base > max_number:
            break
    return sequence[:-1]
