import os

import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.offline
from plotly.offline import plot


def draw_chart_mat(df, draw_chart_list, pic_size=[9, 9], dpi=72, font_size=20, title=None, noise_pct=0.05):
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.figure(num=1, figsize=(pic_size[0], pic_size[1]), dpi=dpi)
    plt.xticks(fontsize=font_size)
    plt.yticks(fontsize=font_size)
    row = len(draw_chart_list)
    count = 0
    for data in draw_chart_list:
        temp = df.copy()
        temp['Rank'] = temp[data].rank(pct=True)
        temp = temp[temp['Rank'] < (1 - noise_pct)]
        temp = temp[temp['Rank'] > noise_pct]
        # group = temp.groupby(data)
        # plt.hist(group.groups.keys(), 20)

        ax = plt.subplot2grid((row, 1), (count, 0))
        ax.hist(temp[data], 70)
        ax.set_xlabel(data)
        ax.set_ylabel('数量')
        count += 1

    plt.show()


def draw_equity_curve_mat(df, trade, title, path='./pic.html', show=True):
    g = trade.copy()
    # 买卖点
    mark_point_list = []
    for i in g.index:
        buy_time = i
        sell_time = g.loc[i, 'end_bar']
        # 标记买卖点，在最高价上方标记
        y = df.loc[df['candle_begin_time'] == buy_time, 'high'].iloc[0] * 1.05
        mark_point_list.append({
            'x': buy_time,
            'y': y,
            'showarrow': True,
            'text': '买入',
            'arrowside': 'end',
            'arrowhead': 7
        })
        y = df.loc[df['candle_begin_time'] == sell_time, 'low'].iloc[0] * 1.05
        mark_point_list.append({
            'x': sell_time,
            'y': y,
            'showarrow': True,
            'text': '卖出',
            'arrowside': 'end',
            'arrowhead': 7
        })
    trace1 = go.Candlestick(
        x=df['candle_begin_time'],
        open=df['open'],  # 字段数据必须是元组、列表、numpy数组、或者pandas的Series数据
        high=df['high'],
        low=df['low'],
        close=df['close']
    )

    trace2 = go.Scatter(x=df['candle_begin_time'], y=df['equity_curve'], name='资金曲线', yaxis='y2')
    layout = go.Layout(
        yaxis2=dict(anchor='x', overlaying='y', side='right')  # 设置坐标轴的格式，一般次坐标轴在右侧
    )
    fig = go.Figure(data=[trace1, trace2], layout=layout)

    fig.update_layout(annotations=mark_point_list, title=title)

    plot(figure_or_data=fig, filename=path, auto_open=False)
    # 打开图片的html文件，需要判断系统的类型
    if show:
        res = os.system('start ' + path)
        if res != 0:
            os.system('open ' + path)
