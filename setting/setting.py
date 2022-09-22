# SETTINGS = {
#     'strategy_name': "bolling",
#     'account_id': 1,
#     'symbol': 'BTC-USDT_15m',
#     'face_value': 0.01,
#     'c_rate': 0.0005,
#     'slippage': 0.001,
#     'leverage_rate': 3,
#     'min_margin_ratio': 0.01,
#     'rule_type': '15T',
#     'drop_days': 10,
# }

# class Settings:
#     """
#     settings
#     """
#
#     def __init__(self):
#         # 策略名
#         self.strategy_name = "bolling"
#         # 账户名
#         self.account_id = 1
#         # 交易币种
#         self.symbol = 'BTC-USDT_15m'
#         # btc是0.01，不同的币种要进行不同的替换
#         self.face_value = 0.01
#         # 手续费，commission fees，默认为万分之5。不同市场手续费的收取方法不同，对结果有影响。比如和股票就不一样。
#         self.c_rate = 0.0005
#         # 滑点 ，可以用百分比，也可以用固定值。建议币圈用百分比，股票用固定值
#         self.slippage = 0.001
#         # 杠杆比率
#         self.leverage_rate = 3
#         # 最低保证金率，低于就会爆仓
#         self.min_margin_ratio = 0.01
#         # k线种类
#         self.rule_type = '15T'
#         # 币种刚刚上线10天内不交易
#         self.drop_days = 10
#
#
# settings = Settings()

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['setting/settings.toml', 'setting/.secrets.toml'],
)

# HERE ENDS DYNACONF EXTENSION LOAD (No more code below this line)
# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
