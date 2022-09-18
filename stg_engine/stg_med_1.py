# !/usr/bin/env python
from db_engine.coin_tools import *


def mid_stg_backtest(df, factor_class_dict, c_rate=2.5 / 10000, leverage=1,
                     start_date='2021-01-01', end_date='2022-07-25'):
    """
    默认回测函数，只改动了传入df，可大大加快回测速度
    """
    for (key, value) in factor_class_dict.items():
        if value == 'True':
            factor_class_dict[key] = True
        else:
            factor_class_dict[key] = False
    df = df[['time', 'symbol', '下周期币种涨跌幅'] + list(factor_class_dict.keys())]
    # 筛选日期范围
    df = df[df['time'] >= pd.to_datetime(start_date)]
    df = df[df['time'] <= pd.to_datetime(end_date)]

    # 计算每个因子的排名
    for f in list(factor_class_dict.keys()):
        df['{f}_rank'] = df.groupby('time')[f].rank(method='first', ascending=factor_class_dict[f])
    # 计算因子综合排名
    df['因子'] = df[[i + '_rank' for i in list(factor_class_dict.keys())]].sum(axis=1, skipna=False)

    # 根据因子对比进行排名
    # 从小到大排序 - 做多
    df['排名1'] = df.groupby('time')['因子'].rank(method='first')
    df1 = df[(df['排名1'] <= 1)]
    df1 = df1.copy()
    df1['方向'] = 1

    # 从大到小排序 - 做空
    df['排名2'] = df.groupby('time')['因子'].rank(method='first', ascending=False)
    df2 = df[(df['排名2'] <= 1)]
    df2 = df2.copy()
    df2['方向'] = -1

    # 合并排序结果
    df = pd.concat([df1, df2], ignore_index=True)
    df['选币'] = df['symbol'] + '(' + df['方向'].astype(str) + ')' + ' '
    df = df[['time', 'symbol', '方向', '选币', '下周期币种涨跌幅']]
    df.sort_values(by=['time', '方向'], ascending=[True, False], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 计算下周期收益
    df['下周期交易涨跌幅'] = df['下周期币种涨跌幅'] * df['方向'] * leverage / 2 - leverage / 2 * c_rate - leverage / 2 * c_rate * (
            1 + df['下周期币种涨跌幅'])  # 杠杆，多空，并且扣除手续费
    select_coin = pd.DataFrame()
    select_coin['当周期选币'] = df.groupby('time')['选币'].sum()
    select_coin['下周期策略涨跌幅'] = df.groupby('time')['下周期交易涨跌幅'].sum()
    select_coin['净值'] = (select_coin['下周期策略涨跌幅'] + 1).cumprod()
    # print(select_coin)

    # 画图
    select_coin.reset_index(inplace=True)
    # plt.plot(select_coin['time'], select_coin['净值'])
    # plt.show()
    # plt.savefig(str(factor_class_dict) + '.png')

    # 计算最终收益率，夏普，最终收益率，最大回撤及所选参数
    max_return = select_coin['净值'].max()
    final_return = select_coin['净值'].values[-1]
    max_drawdown_rate, max_drawdown = cal_drawdown(select_coin['净值'].values)
    sharpe = sharpe_raio(select_coin['下周期策略涨跌幅'])
    win = cal_win_rate(select_coin['下周期策略涨跌幅'])
    return [str(factor_class_dict), round(final_return, 4),
            round(max_return, 4), round(sharpe, 4), round(max_drawdown_rate, 4), round(win, 2)]


def auto_config(period, factors_num, factor_day_list, direction_change=None, factor_list=None):
    """
    自动调参回测
    period: 周期
    factors_num: 选用n个因子
    factor_day_list：单因子天数列表，[2, 3, 4, 5, 6, ...]
    direction_change: 是否变换因子排列顺序，变换传入[True, False]，不变可不填
    """
    if direction_change is None:
        direction_change = [False]
    if factor_list is None:
        df_factor = pd.read_excel('因子详细说明.xlsx')
        factor_list = df_factor['因子名称'].tolist()
    backtest_result_list = []
    factor_portfolio_list = list(combinations([i for i in factor_list], factors_num))
    # 提前读取一遍数据，传入回测函数，加快速度
    df = pd.read_csv('./all_coin_factor_data_{period}.csv', encoding='gbk', parse_dates=['time'])
    for factor_portfolio in factor_portfolio_list:
        factor_list_temp = []
        for factor in iter(factor_portfolio):
            list_1 = lists_combination([[factor], factor_day_list])
            list_2 = lists_combination([list_1, direction_change], code=':')
            factor_list_temp.append(list_2)
        factor_list_all = lists_combination(factor_list_temp, code=',')
        for factors in factor_list_all:
            factor_dict = {}
            for factor in factors.split(","):
                factor_dict[factor.split(":")[0]] = factor.split(":")[1]
            result_list = mid_stg_backtest(df, factor_dict)
            print('Coin Mid Backtest: ', result_list)
            backtest_result_list.append(result_list)
    df_back_test = pd.DataFrame(backtest_result_list, columns=['parameter', 'return', 'max_return',
                                                               'sharpe', 'max_drawdown_rate', 'win_rate'])
    return df_back_test

