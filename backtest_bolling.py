#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2022/9/18 14:47
# @Author : Meng
# @Site : 
# @File : backtest_bolling.py
# @Software: PyCharm

from db_engine import *
from setting.setting import settings
from backtest_engine import backtest_coin_stg,  backtest_coin_stg_by_one_loop


if __name__ == "__main__":
    stg_name = 'simple_bolling'
    backtest_coin_stg_by_one_loop([710, 3.5])

    # m_list = [j for j in range(10, 1000, 10)]
    # n_list = [i / 10 for i in list(np.arange(5, 50, 1))]
    # para_list = make_para_list([m_list, n_list])
    # df_return = backtest_coin_stg(symbol=settings.symbol, para_list=para_list)
    # df_return.to_csv(f'./data/backtest/simple_bolling/backtest_result_{str(len(para_list))}.csv', index=False)
