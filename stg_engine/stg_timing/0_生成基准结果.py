import warnings
from datetime import datetime
from datetime import timedelta
from multiprocessing import Pool, cpu_count

from Config import *
from Evaluate import *
from Function import *
from Statistics import *


# =====批量遍历策略参数
# ===单次循环
def calculate_by_one_loop(symbol):
    print(symbol)
    # ===读入数据
    df = pd.read_csv(os.path.join(symbol_data_path, symbol + '.csv'), encoding='gbk',
                     parse_dates=['candle_begin_time'], skiprows=1)
    # 币种上线10天之后的日期
    t = df.iloc[0]['candle_begin_time'] + timedelta(days=drop_days)
    df = df[df['candle_begin_time'] > t]
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
    df = df[df['candle_begin_time'] >= pd.to_datetime('2017-01-01')]
    df.reset_index(inplace=True, drop=True)
    min_amount = min_amount_dict[symbol.replace('-', '')]
    warnings.filterwarnings('ignore')
    df['pos'] = 1
    df = cal_equity_curve(df, slippage=slippage, c_rate=c_rate,
                          leverage_rate=leverage_rate,
                          min_amount=min_amount,
                          min_margin_ratio=min_margin_ratio)
    original_trade = transfer_equity_curve_to_trade(df)
    original, _ = strategy_evaluate(df, original_trade)
    rtn = pd.DataFrame()
    rtn.loc[0, '币种'] = symbol
    rtn.loc[0, '累积净值'] = original.loc['累积净值', 0]
    rtn.loc[0, '年化收益'] = original.loc['年化收益', 0]
    rtn.loc[0, '最大回撤'] = original.loc['最大回撤', 0]
    rtn.loc[0, '年化收益/回撤比'] = original.loc['年化收益/回撤比', 0]
    return rtn


if __name__ == '__main__':
    for rule_type in ['4H']:

        # ===并行回测
        start_time = datetime.now()  # 标记开始时间

        # 利用partial指定参数值
        multiple_process = True
        # 标记开始时间
        if multiple_process:
            with Pool(max(cpu_count() - 1, 1)) as pool:
                # 使用并行批量获得data frame的一个列表
                df_list = pool.map(calculate_by_one_loop, symbol_list)
        else:
            df_list = []
            for symbol in symbol_list:
                res_df = calculate_by_one_loop(symbol=symbol)
                df_list.append(res_df)
        print('读入完成, 开始合并', datetime.now() - start_time)
        # 合并为一个大的DataFrame
        para_curve_df = pd.concat(df_list, ignore_index=True)

        # ===输出
        para_curve_df.sort_values(by='年化收益/回撤比', ascending=False, inplace=True)
        print(para_curve_df.head(10))

        # ===存储参数数据
        p = root_path + '/data/output/para/基准&%s&%s.csv' % (leverage_rate, rule_type)
        para_curve_df.to_csv(p, index=False, encoding='gbk')
