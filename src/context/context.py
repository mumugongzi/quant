# coding: utf-8

import pandas as pd

from common.Functions import get_trade_date_list, import_index_data


class BackContext(object):

    def __init__(self, start_date, end_date, stock_list, columns=None, init_cash=1000000,
                 benchmark='sh000001',
                 slippage=1.0 / 1000, commission_rate=2.0 / 1000, commission_min=5.0, stamp_tax_rate=1.0 / 1000,
                 stamp_tax_min=1.0, print_progress=False, params={}):
        """
        :param start_date: 回测开始时间
        :param end_date: 回测结束时间
        :param stock_list: 回测股票池,
        :param columns: 需要的数据列
        :param init_cash: 初始紫金
        :param benchmark: 基准标的, 可以填多个
        :param slippage: 滑点
        :param commission_rate: 佣金, 默认千分之二
        :param commission_min: 最低佣金, 不足最低值按最低值收取
        :param stamp_tax_rate: 印花税, 默认千分之一
        :param stamp_tax_min: 最低印花税, 不足最低值按最低值收取
        :param print_progress: 回测过程中是否打印回测进度, 默认不打印
        :param params: 定义一些回测参数, 比如小市值因子, 调仓换股周期
        """
        self.start_date = start_date
        self.end_date = end_date
        self.stock_list = stock_list
        self.columns = columns
        self.init_cash = init_cash
        self.benchmark = benchmark
        self.slippage = slippage
        self.commission_rate = commission_rate
        self.commission_min = commission_min
        self.stamp_tax_rate = stamp_tax_rate
        self.stamp_tax_min = stamp_tax_min
        self.print_progress = print_progress
        self.params = params

        self.strategy_name = "无名策略"

        self.available_cash = self.init_cash
        # 当前持仓
        self.cur_position = {}

        # 记录历史持仓, 包含交易日期、股票代码、股票数量、当日收盘价
        self.his_position = pd.DataFrame()

        # 记录账户历史, 包含总资产、资金资产、股票资产、当日盈亏、仓位比例
        self.his_account = pd.DataFrame()

        # 历史交易记录
        self.his_trade_records = pd.DataFrame()

        self.trade_dates = []

    def get_trade_date_list(self):
        if self.trade_dates is None or len(self.trade_dates) <= 0:
            self.trade_dates = get_trade_date_list(self.start_date, self.end_date)
        return self.trade_dates
