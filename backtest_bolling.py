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
    stg_name = 'simple_turtle'
    stg_coin = 'LTC-USDT_15m'
    default_para_bolling = [710, 3.5]
    default_para_turtle = [20, 10]
    backtest_coin_stg_by_one_loop(stg=stg_name, para=default_para_turtle, symbol=stg_coin)
    # m_list = [j for j in range(10, 1000, 10)]
    # n_list = [i / 10 for i in list(np.arange(5, 50, 1))]
    # para_list = make_para_list([m_list, n_list])
    # print(f'start crypto coin backtest, stg_name: {stg_name}, stg_coin: {stg_coin}, paras: {str(len(para_list))}')
    # df_return = backtest_coin_stg(stg=stg_name, symbol=stg_coin, para_list=para_list, pools=2)
    # df_return.to_csv(f'./data/backtest/{stg_name}/return_{stg_coin}_{str(len(para_list))}.csv', index=False)
