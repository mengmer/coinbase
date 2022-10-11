from datetime import timedelta, datetime

import Signals
from Config import *
from Evaluate import *
from Function import *
from Position import *
from Statistics import *

start_time = datetime.now()
# =====读入数据
df = pd.read_csv(os.path.join(symbol_data_path, symbol + '.csv'), encoding='gbk', parse_dates=['candle_begin_time'],
                 skiprows=1)

# 任何原始数据读入都进行一下排序、去重，以防万一
df.sort_values(by=['candle_begin_time'], inplace=True)
df.drop_duplicates(subset=['candle_begin_time'], inplace=True)
df.reset_index(inplace=True, drop=True)

# =====转换为指定周期数据
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
df = period_df[['candle_begin_time', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trade_num',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']]
df = df[df['candle_begin_time'] >= pd.to_datetime(date_start)]
df.reset_index(inplace=True, drop=True)

# =====计算交易信号
df = getattr(Signals, signal_name)(df, para=para, proportion=proportion)

# =====计算实际持仓
df = position_for_future(df)

# =====计算资金曲线
# 选取相关时间。币种上线10天之后的日期
t = df.iloc[0]['candle_begin_time'] + timedelta(days=drop_days)
df = df[df['candle_begin_time'] > t]
# 计算资金曲线
min_amount = min_amount_dict[symbol.replace('-', '')]
df = cal_equity_curve(df, slippage=slippage, c_rate=c_rate, leverage_rate=leverage_rate,
                      min_amount=min_amount, min_margin_ratio=min_margin_ratio)
print(df)
print('策略最终收益：', df.iloc[-1]['equity_curve'])
# 输出资金曲线文件
df_output = df[
    ['candle_begin_time', 'open', 'high', 'low', 'close', 'signal', 'pos', 'quote_volume',
     'equity_curve']]
df_output.rename(columns={'median': 'line_median', 'upper': 'line_upper', 'lower': 'line_lower',
                          'quote_volume': 'b_bar_quote_volume',
                          'equity_curve': 'r_line_equity_curve'}, inplace=True)
df_output.to_csv(root_path + '/data/output/equity_curve/%s&%s&%s&%s.csv' % (signal_name, symbol.split('-')[0],
                                                                            rule_type, str(para)), index=False)

# =====策略评价
# 计算每笔交易
trade = transfer_equity_curve_to_trade(df)
print('逐笔交易：\n', trade)

title = symbol + '_' + str(para)
draw_equity_curve_mat(df, trade, title)

# 计算各类统计指标
r, monthly_return = strategy_evaluate(df, trade)
print(r)
print(monthly_return)
print(datetime.now() - start_time)
