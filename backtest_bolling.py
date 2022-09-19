#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2022/9/18 14:47
# @Author : Meng
# @Site : 
# @File : backtest_bolling.py
# @Software: PyCharm
import traceback
from backtest_engine import backtest_coin_stg
from setting.setting import settings

if __name__ == "__main__":
    df_return = backtest_coin_stg(symbol=settings.symbol)
