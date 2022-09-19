import pandas as pd

from setting.setting import settings
from datetime import timedelta
from multiprocessing.pool import Pool
from datetime import datetime
from .Signals import *
from .Position import *
from .Evaluate import *
import warnings

warnings.filterwarnings("ignore")


def backtest_coin_stg(symbol, pools=4):
    """
    多次循环回测
    """
    # =====读入数据
    df = pd.read_csv('./data/binance/spot/2018-01-01_2022-09-09/%s.csv' % symbol)
    df['candle_begin_time'] = pd.to_datetime(df['candle_begin_time'])
    # df = pd.read_hdf('../data/%s.h5' % symbol, key='df')
    # 任何原始数据读入都进行一下排序、去重，以防万一
    df.sort_values(by=['candle_begin_time'], inplace=True)
    df.drop_duplicates(subset=['candle_begin_time'], inplace=True)
    df.reset_index(inplace=True, drop=True)
    df.set_index('candle_begin_time', drop=True)

    # =====转换为其他分钟数据
    period_df = df.resample(rule=settings.rule_type, on='candle_begin_time', label='left', closed='left').agg(
        {'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'volume': 'sum',
         })
    period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
    period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
    period_df.reset_index(inplace=True)
    df = period_df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume']]
    df = df[df['candle_begin_time'] >= pd.to_datetime('2017-01-01')]
    df.reset_index(inplace=True, drop=True)

    # =====获取策略参数组合
    para_list = signal_simple_bolling_para_list()
    # =====并行提速
    start_time = datetime.now()  # 标记开始时间
    pool = Pool(pools)
    # 使用并行批量获得data frame的一个列表
    df_list = []
    for para in para_list:
        pool.apply_async(func=backtest_coin_stg_by_one_loop,
                         kwds=({'para': para, 'df_signal': df, 'returns': df_list}),
                         error_callback=print_error)
    pool.close()
    pool.join()
    print('读入完成, 开始合并', datetime.now() - start_time)
    df_return = pd.concat(df_list, ignore_index=True)
    # 合并为一个大的DataFrame
    # =====输出
    df_return.sort_values(by='equity_curve', ascending=False, inplace=True)
    return df_return


def backtest_coin_stg_by_one_loop(para, df_signal, returns):
    """
    单次循环回测
    """
    _df = df_signal.copy()
    # 计算交易信号
    _df = signal_simple_bolling(_df, para=para)
    # 计算实际持仓
    _df = position_for_OKEx_future(_df)
    # 计算资金曲线
    # 选取相关时间。币种上线10天之后的日期
    t = _df.iloc[0]['candle_begin_time'] + timedelta(days=settings.drop_days)
    _df = _df[_df['candle_begin_time'] > t]
    # 计算资金曲线
    _df = equity_curve_for_OKEx_USDT_future_next_open(_df, slippage=settings.slippage,
                                                      c_rate=settings.c_rate,
                                                      leverage_rate=settings.leverage_rate,
                                                      face_value=settings.face_value,
                                                      min_margin_ratio=settings.min_margin_ratio)
    # 计算收益
    r = _df.iloc[-1]['equity_curve']
    returns.append([para, r])


def print_error(value):
    """
    打印错误
    """
    print("线程池出错,出错原因为: ", value)
