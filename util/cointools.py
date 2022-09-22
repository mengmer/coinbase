# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2022/8/3 10:21
# @Author : Meng

import pandas as pd
import numpy as np
import math
import os
from datetime import timedelta
from itertools import combinations
import ccxt
from functools import reduce
import time

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行


def make_para_list(lists):
    """输入多个列表组成的列表, 输出其中每个列表所有元素可能的所有排列组合
    code用于分隔每个元素"""

    def myfunc(list1, list2):
        """
        myfunc
        """
        return [[i, j] for i in list1 for j in list2]
    return reduce(myfunc, lists)


def cal_win_rate(return_series):
    """
    计算胜率
    """
    return len(return_series[return_series > 0]) / len(return_series)


def cal_drawdown(return_list):
    """最大回撤率"""
    '''
    return_list：是每日资金的变化曲线
    np.maximum.accumulate(return_list)：找到return_list中的累计最大值，例如：
    d = np.array([2, 0, 3, -4, -2, 7, 9])
    c = np.maximum.accumulate(d)
    #c = array([2, 2, 3, 3, 3, 7, 9])
    i：为最大回撤截止的时间
    j：为最大回撤开始的时间
    drawdown_max：最大回撤
    drawdown_rate：最大回撤对应的回撤率
    drawdown_tian：回撤持续天数
    '''
    i = np.argmax((np.maximum.accumulate(return_list) - return_list))
    if i == 0:
        return 0
    j = np.argmax(return_list[:i])  # 开始位置
    drawdown_max = return_list[j] - return_list[i]
    drawdown_rate = (return_list[j] - return_list[i]) / return_list[j]

    return drawdown_rate, drawdown_max


def sharpe_raio(return_series, stock=False, coin=False):
    """
    计算夏普比率
    """
    n = 252
    if stock is True:
        n = 252
    if coin is True:
        n = 365
    # 计算夏普比率
    return_series -= 0.04 / n
    return (return_series.mean() * math.sqrt(n)) / return_series.std()


def lists_combination(lists, code=' '):
    """输入多个列表组成的列表, 输出其中每个列表所有元素可能的所有排列组合
    code用于分隔每个元素"""

    def myfunc(list1, list2):
        """
        myfunc
        """
        return [str(i) + code + str(j) for i in list1 for j in list2]

    return reduce(myfunc, lists)


# 在币币账户下单
def binance_spot_place_order(exchange, symbol, long_or_short, price, amount):
    """
    :param exchange:  ccxt交易所
    :param symbol: 币币交易对代码，例如'BTC/USDT'
    :param long_or_short:  两种类型：买入、卖出
    :param price:  下单价格
    :param amount:  下单数量
    :return:
    """

    for i in range(5):
        try:
            # 买
            if long_or_short == '买入':
                order_info = exchange.create_limit_buy_order(symbol, amount, price)  # 买单
            # 卖
            elif long_or_short == '卖出':
                order_info = exchange.create_limit_sell_order(symbol, amount, price)  # 卖单
            else:
                raise ValueError('long_or_short只能是：`买入`或者`卖出`')

            print('binance币币交易下单成功：', symbol, long_or_short, price, amount)
            print('下单信息：', order_info, '\n')
            return order_info

        except Exception as e:
            print('binance币币交易下单报错，1s后重试', e)
            time.sleep(1)

    print('binance币币交易下单报错次数过多，程序终止')
    exit()


# 在期货合约账户下限价单
def binance_future_place_order(exchange, symbol, long_or_short, price, amount):
    """
    :param exchange:  ccxt交易所
    :param symbol: 合约代码，例如'BTCUSD_210625'
    :param long_or_short:  四种类型：开多、开空、平多、平空
    :param price: 开仓价格
    :param amount: 开仓数量，这里的amount是合约张数
    :return:

    timeInForce参数的几种类型
    GTC - Good Till Cancel 成交为止
    IOC - Immediate or Cancel 无法立即成交(吃单)的部分就撤销
    FOK - Fill or Kill 无法全部立即成交就撤销
    GTX - Good Till Crossing 无法成为挂单方就撤销

    """

    if long_or_short == '开空':
        side = 'SELL'
    elif long_or_short == '平空':
        side = 'BUY'
    else:
        raise NotImplemented('long_or_short目前只支持 `开空`、`平空`，请参考官方文档添加其他的情况')

    # 确定下单参数
    # 开空
    params = {
        'side': side,
        'positionSide': 'SHORT',
        'symbol': symbol,
        'type': 'LIMIT',
        'price': price,  # 下单价格
        'quantity': amount,  # 下单数量，注意此处是合约张数,
        'timeInForce': 'GTC',  # 含义见本函数注释部分
    }
    # 尝试下单
    for i in range(5):
        try:
            params['timestamp'] = int(time.time() * 1000)
            order_info = exchange.dapiPrivatePostOrder(params)
            print('币安合约交易下单成功：', symbol, long_or_short, price, amount)
            print('下单信息：', order_info, '\n')
            return order_info
        except Exception as e:
            print('币安合约交易下单报错，1s后重试...', e)
            time.sleep(1)

    print('币安合约交易下单报错次数过多，程序终止')
    exit()


# binance各个账户间转钱
def binance_account_transfer(exchange, currency, amount, from_account='币币', to_account='合约'):
    """
    binance各个账户间转钱
    """

    if from_account == '币币' and to_account == '合约':
        transfer_type = 'MAIN_CMFUTURE'
    elif from_account == '合约' and to_account == '币币':
        transfer_type = 'CMFUTURE_MAIN'
    else:
        raise ValueError('未能识别`from_account`和`to_account`的组合，请参考官方文档')

    # 构建参数
    params = {
        'type': transfer_type,
        'asset': currency,
        'amount': amount,
    }

    # 开始转账
    for i in range(5):
        try:
            params['timestamp'] = int(time.time() * 1000)
            transfer_info = exchange.sapiPostAssetTransfer(params=params)
            print('转账成功：', from_account, 'to', to_account, amount)
            print('转账信息：', transfer_info, '\n')
            return transfer_info
        except Exception as e:
            print('转账报错，1s后重试', e)
            time.sleep(1)

    print('转账报错次数过多，程序终止')
    exit()