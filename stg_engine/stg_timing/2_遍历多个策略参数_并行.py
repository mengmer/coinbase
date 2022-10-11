import warnings
from datetime import datetime
from datetime import timedelta
from functools import partial
from multiprocessing import Pool, cpu_count

import Signals
from Config import *
from Evaluate import *
from Function import *
from Position import *
from Statistics import *


# =====批量遍历策略参数
# ===单次循环
def calculate_by_one_loop(para, df, signal_name, symbol, rule_type, min_amount):
    warnings.filterwarnings('ignore')
    _df = df.copy()
    # 计算交易信号
    _df = getattr(Signals, signal_name)(_df, para=para, proportion=proportion)
    # 计算实际持仓
    _df = position_for_future(_df)

    # 选取相关时间。币种上线10天之后的日期
    t = _df.iloc[0]['candle_begin_time'] + timedelta(days=drop_days)
    _df = _df[_df['candle_begin_time'] > t]

    _df = cal_equity_curve(_df, slippage=slippage, c_rate=c_rate,
                           leverage_rate=leverage_rate,
                           min_amount=min_amount,
                           min_margin_ratio=min_margin_ratio)
    # =====策略评价
    # 计算每笔交易
    trade = transfer_equity_curve_to_trade(_df)
    if trade.empty:
        return pd.DataFrame()
    # print('逐笔交易：\n', trade)

    # 计算各类统计指标
    r, monthly_return = strategy_evaluate(_df, trade)
    # 保存策略收益
    rtn = pd.DataFrame()
    rtn.loc[0, 'para'] = str(para)
    for i in r.index:
        rtn.loc[0, i] = r.loc[i, 0]  # 最终收益
    print(signal_name, symbol, rule_type, para, '策略收益：', r.loc['累积净值', 0])
    return rtn


if __name__ == '__main__':
    # 计算资金曲线
    for signal_name in ['signal_add_bias']:
        for symbol in symbol_list:
            min_amount = min_amount_dict[symbol.replace('-', '')]
            for rule_type in ['4H']:
                print(signal_name, symbol, rule_type)
                print('开始遍历该策略参数：', signal_name, symbol, rule_type)
                # ===读入数据
                df = pd.read_csv(os.path.join(symbol_data_path, symbol + '.csv'), encoding='gbk',
                                 parse_dates=['candle_begin_time'], skiprows=1)

                # 任何原始数据读入都进行一下排序、去重，以防万一
                df.sort_values(by=['candle_begin_time'], inplace=True)
                df.drop_duplicates(subset=['candle_begin_time'], inplace=True)
                df.reset_index(inplace=True, drop=True)

                # =====转换为其他分钟数据
                period_df = df.resample(rule=rule_type, on='candle_begin_time', label='left', closed='left').agg(
                    {'open': 'first',
                     'high': 'max',
                     'low': 'min',
                     'close': 'last',
                     'volume': 'sum',
                     'quote_volume': 'sum',
                     'trade_num': 'sum',
                     'taker_buy_base_asset_volume': 'sum',
                     'taker_buy_quote_asset_volume': 'sum',
                     })
                period_df.dropna(subset=['open'], inplace=True)  # 去除一天都没有交易的周期
                period_df = period_df[period_df['volume'] > 0]  # 去除成交量为0的交易周期
                period_df.reset_index(inplace=True)
                df = period_df[
                    ['candle_begin_time', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trade_num',
                     'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']]
                df = df[df['candle_begin_time'] >= pd.to_datetime(date_start)]
                df.reset_index(inplace=True, drop=True)

                # ===获取策略参数组合
                para_list = getattr(Signals, signal_name + '_para_list')()

                # ===并行回测
                start_time = datetime.now()  # 标记开始时间

                # 利用partial指定参数值
                part = partial(calculate_by_one_loop, df=df, signal_name=signal_name, symbol=symbol,
                               rule_type=rule_type, min_amount=min_amount)
                multiple_process = True
                # 标记开始时间
                if multiple_process:
                    with Pool(max(cpu_count() - 1, 1)) as pool:
                        # 使用并行批量获得data frame的一个列表
                        df_list = pool.map(part, para_list)
                else:
                    df_list = []
                    for para in para_list:
                        res_df = calculate_by_one_loop(para=para, df=df, signal_name=signal_name, symbol=symbol,
                                                       rule_type=rule_type, min_amount=min_amount)
                        df_list.append(res_df)
                print('读入完成, 开始合并', datetime.now() - start_time)
                # 合并为一个大的DataFrame
                para_curve_df = pd.concat(df_list, ignore_index=True)

                # 读取基准数据
                p = root_path + '/data/output/para/基准&%s&%s.csv' % (leverage_rate, rule_type)
                original = pd.read_csv(p, encoding='gbk')
                # 合并原始数据
                para_curve_df['币种原始累积净值'] = original.loc[original['币种'] == symbol].iloc[0]['累积净值']
                para_curve_df['币种原始年化收益'] = original.loc[original['币种'] == symbol].iloc[0]['年化收益']
                para_curve_df['币种原始最大回撤'] = original.loc[original['币种'] == symbol].iloc[0]['最大回撤']
                para_curve_df['币种原始年化收益/回撤比'] = original.loc[original['币种'] == symbol].iloc[0][
                    '年化收益/回撤比']

                # ===输出
                para_curve_df.sort_values(by='年化收益/回撤比', ascending=False, inplace=True)
                print(para_curve_df.head(10))

                # ===存储参数数据
                p = root_path + '/data/output/para/%s&%s&%s&%s.csv' % (
                    signal_name, symbol, leverage_rate, rule_type)
                para_curve_df.to_csv(p, index=False, mode='a', encoding='gbk')
                print(datetime.now() - start_time)
