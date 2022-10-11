import os

# =====手工设定策略参数
import pandas as pd

symbol = 'FIL-USDT'  # 指定币种
para = [13, 0.08]  # 策略参数
proportion = 0.25  # 止盈止损比例
signal_name = 'signal_add_bias'  # 策略名称
rule_type = '4H'  # 周期
date_start = '2021-04-01'  # 回测开始时间
date_end = '2022-08-20'  # 回测结束时间
c_rate = 5 / 10000  # 手续费，commission fees，默认为万分之5。不同市场手续费的收取方法不同，对结果有影响。比如和股票就不一样。
slippage = 1 / 1000  # 滑点 ，可以用百分比，也可以用固定值。建议币圈用百分比，股票用固定值
leverage_rate = 2  # 杠杆倍数
min_margin_ratio = 1 / 100  # 最低保证金率，低于就会爆仓
drop_days = 10  # 币种刚刚上线10天内不交易

# ===获取项目根目录
_ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径
root_path = os.path.abspath(os.path.join(_, '..'))  # 返回根目录文件夹

symbol_data_path = '/Users/xbx/Downloads/swap_binance_1h'

min_amount_df = pd.read_csv(os.path.join(root_path, 'data/合约面值.csv'), encoding='gbk')
min_amount_dict = {}
for i in min_amount_df.index:
    min_amount_dict[min_amount_df.at[i, '合约']] = min_amount_df.at[i, '最小下单量']

# 本次小组所交易的币种
symbol_list = ['ETH-USDT', 'BTC-USDT', 'BTCBUSD', 'ETC-USDT', 'SOL-USDT', 'EOS-USDT', 'ADA-USDT', 'CHZ-USDT',
               'BNB-USDT', 'MATIC-USDT', 'AVAX-USDT', 'ATOM-USDT', 'XRP-USDT', 'NEAR-USDT', 'TRB-USDT',
               'LTC-USDT', 'FIL-USDT', 'RVN-USDT', 'HNT-USDT', 'DOT-USDT', 'DOGE-USDT', 'BLZ-USDT', 'LINK-USDT',
               'UNFI-USDT', 'CRV-USDT', 'BCH-USDT', 'SAND-USDT', 'AXS-USDT', 'SNX-USDT', 'FTM-USDT',
               'WAVES-USDT', 'AAVE-USDT', 'KNC-USDT', 'RLC-USDT', 'THETA-USDT', 'ANKR-USDT', 'UNI-USDT',
               'TRX-USDT', 'RUNE-USDT', 'CTK-USDT', 'YFI-USDT', 'BAL-USDT', 'SUSHI-USDT', 'ZEC-USDT',
               'XMR-USDT', 'FLM-USDT', 'ALGO-USDT', 'CHR-USDT', 'COMP-USDT', 'XTZ-USDT']
