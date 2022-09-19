import configparser
import os

"""
os.path.realpath(): 获取当前文件的全路径
os.path.split()：按照路径将文件名和路径分割开
os.path.join(): 将多个路径组合后返回
"""


class ReadConfig:
    """
    初始化ConfigParser实例，使用ConfigParser模块读取配置文件的section节点，section节点就是config.ini中[]的内容
    """

    def __init__(self):
        self.cf = configparser.ConfigParser()
        basePath = os.path.split(os.path.realpath(__file__))[0]
        configPath = os.path.join(basePath + 'config.ini')
        self.cf.read(configPath, encoding='utf-8')

    def get_strategy_config(self, param):
        """
        读取节点STRATEGY_CONFIG中param值；
        :param param:
        :return:
        """
        value = self.cf.get('STRATEGY_CONFIG', param)
        return value

    def get_trade_config(self, param):
        """
        读取节点TRADE_CONFIG中param值；
        :param param:
        :return:
        """
        value = self.cf.get('TRADE_CONFIG', param)
        return value


def read_config():
    """
    读取config参数
    """
    basePath = os.path.split(os.path.realpath(__file__))[0]
    configPath = os.path.join(basePath + 'config.ini')
    cf = configparser.ConfigParser()
    cf.read(configPath, encoding='gbk')
    config = {key1: {key2: f(cf[key1][key2]).strip() for key2 in cf[key1].keys()} for key1 in cf.keys()}


