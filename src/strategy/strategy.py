# coding: utf-8
import math

import pandas as pd

from strategy.position import Position
from common.Functions import get_trade_date_list
from context.context import BackContext
from data.datasource import ds
from data.datasource import DiskDataSource
from tool.progress import print_progress

BUY_SIGNAL = 1
SELL_SIGNAL = -1
NO_SIGNAL = 0

# 等交易日间隔采样
SAMPLE_INTERVAL_TRADE_DAY = 'trade'

# 等自然日间隔采样
SAMPLE_INTERVAL_NATURAL_DAY = 'natural'


class AbstractBackStrategy(object):
    name = '策略框架'

    def __init__(self, context):
        """
        :param context: 回测上下文
        """
        if not isinstance(context, BackContext):
            raise Exception("invalid context type")

        self.context = context
        # 当前可用紫金

        # list结构, 2010-01-01
        self.trade_dates = self.context.get_trade_date_list()

    # 可以做一些数据准备操作, 比如计算指标的金叉、死叉等等
    def prepare(self):
        pass

    def finish(self):
        self.context.his_position.set_index('交易日期', inplace=True)
        self.context.his_position.sort_index(inplace=True)

        self.context.his_account.set_index('交易日期', inplace=True)
        self.context.his_account.sort_index(inplace=True)

        self.context.his_trade_records.set_index('交易日期', inplace=True)
        self.context.his_trade_records.sort_index(inplace=True)

    def order_lots(self, stock_code, trade_date, lots, side=BUY_SIGNAL):
        """
        :param stock_code: 按股票手数下单, A股一手100股
        :param trade_date: 交易日期
        :param lots: 按手数下单
        :param side: 股票交易方向, BUY_SIGNAL买入, SELL_SIGNAL: 卖出
        :return:
        """
        self.order_quantity(stock_code, trade_date, 100 * lots, side)

    def order_quantity(self, stock_code, trade_date, quantity, side=BUY_SIGNAL):
        """
        :param stock_code: 按股票手数下单, A股一手100股
        :param trade_date: 交易日期
        :param quantity: 按股数下单
        :param side: 股票交易方向, BUY_SIGNAL买入, SELL_SIGNAL: 卖出
        :return:
        """

        real_quantity = math.floor(abs(quantity) / 100) * 100
        if side == BUY_SIGNAL:
            self.buy(stock_code, trade_date, real_quantity)
        elif side == SELL_SIGNAL:
            self.sell(stock_code, trade_date, real_quantity)

    def order_money(self, stock_code, trade_date, money, side=BUY_SIGNAL):
        """
        :param stock_code: 按股票手数下单, A股一手100股
        :param trade_date: 交易日期
        :param money: 按交易金额下单
        :param side: 股票交易方向, BUY_SIGNAL买入, SELL_SIGNAL: 卖出
        :return:
        """

        price = self.get_trade_price(stock_code, trade_date)
        quantity = int(money / price)
        self.order_quantity(stock_code, trade_date, quantity, side)

    def order_pos_rate(self, stock_code, trade_date, rate, side=BUY_SIGNAL):
        """
        :param stock_code: 按股票手数下单, A股一手100股
        :param trade_date: 交易日期
        :param rate: 按仓位比例下单, 仓位比例为正数买入股票, 负数卖出股票
        :return:
        """

        if rate > 1:
            rate = 1.0
        money = self.context.init_cash * rate
        self.order_money(stock_code, trade_date, money, side)

    # 全部平仓
    def close_out_all(self, trade_date):
        for stock_code in self.context.cur_position.keys():
            self.close_out_one_stock(stock_code, trade_date)

    # 平仓单只股票
    def close_out_one_stock(self, stock_code, trade_date):
        if stock_code not in self.context.cur_position.keys():
            raise Exception("can't find stock {} in position".format(stock_code))
        position = self.context.cur_position[stock_code]
        self.sell(stock_code, trade_date, position.get_quantity())

    # TODO 需要考虑涨跌停限制和停牌
    # 买卖统一按开盘价处理
    def sell(self, stock_code, trade_date, quantity):

        # 停牌直接返回
        if ds.is_suspended(stock_code, trade_date):
            return

        if stock_code not in self.context.cur_position.keys():
            raise Exception("can't find stock {} in position".format(stock_code))

        position = self.context.cur_position[stock_code]
        sell_quantity = position.sell(trade_date, quantity)
        if sell_quantity <= 0:
            return

        sell_price = self.get_trade_price(stock_code, trade_date)
        sell_money = sell_quantity * sell_price
        commission = max(self.context.commission_min, sell_money * self.context.commission_rate)
        stamp_tax = max(self.context.stamp_tax_min, sell_money * self.context.stamp_tax_rate)
        # 卖出收取印花税和佣金
        self.context.available_cash = self.context.available_cash + sell_money - commission - stamp_tax
        self.context.his_trade_records = self.context.his_trade_records.append({
            "交易日期": trade_date,
            "股票代码": stock_code,
            "成交价": sell_price,
            "成交量": sell_quantity,
            "成交方向": SELL_SIGNAL,
            "佣金": commission,
            "印花税": stamp_tax,
        }, ignore_index=True)

    # 计算当前余额最多可以买入的股票数量
    def get_available_quantity(self, buy_price):
        commission = max(self.context.commission_min, self.context.available_cash * self.context.commission_rate)
        available_cash = self.context.available_cash - commission
        quantity = int(available_cash / buy_price)
        return quantity - quantity % 100

    # TODO 需要考虑涨跌停限制和停牌
    # 买卖统一按开盘价处理
    def buy(self, stock_code, trade_date, quantity):
        """
        :param stock_code: 股票代码
        :param trade_date: 交易日期
        :param quantity: 买入数量
        :return:
        """

        # 交易量小于1直接返回
        if quantity < 1:
            return

        # 停牌直接返回
        if ds.is_suspended(stock_code, trade_date):
            return

        buy_price = self.get_trade_price(stock_code, trade_date)

        available_quantity = self.get_available_quantity(buy_price)
        quantity = min(available_quantity, quantity)

        buy_money = buy_price * quantity
        commission = max(self.context.commission_min, buy_money * self.context.commission_rate)

        # 金额不足, 无法买入
        if self.context.available_cash < buy_money + commission:
            return

        if stock_code not in self.context.cur_position.keys():
            self.context.cur_position[stock_code] = Position(stock_code)

        position = self.context.cur_position[stock_code]
        position.buy(trade_date, quantity)
        self.context.available_cash = self.context.available_cash - buy_money - commission

        self.context.his_trade_records = self.context.his_trade_records.append({
            "交易日期": trade_date,
            "股票代码": stock_code,
            "成交价": buy_price,
            "成交量": quantity,
            "成交方向": BUY_SIGNAL,
            "佣金": commission,
            "印花税": 0,
        }, ignore_index=True)

    def get_trade_price(self, stock_code, trade_date):
        trade_record = ds.get_one_trade_record(stock_code, trade_date)
        return trade_record.iloc[0]["开盘价"]


    # 运行回验
    def run(self, **kwargs):

        ds.import_data(self.context.start_date, self.context.end_date, self.context.stock_list, self.context.columns,
                       self.context.print_progress)
        self.set_strategy_name()
        self.prepare()

        trade_date_list = self.trade_dates
        for trade_date in trade_date_list:
            if self.context.print_progress:
                print_progress(len(trade_date_list), step=0.02, name='trading')
            self.before_trade(trade_date)
            self.handle_bar(trade_date, **kwargs)
            self.after_trade(trade_date)
        self.finish()

    # 生成买入、卖出信号, 将买卖信号写入到'买卖信号'列中
    def handle_bar(self, trade_date, **kwargs):
        raise Exception("AbstractBackStrategy not implement this method")

    def before_trade(self, trade_date):
        pass

    # 记录当天账户曲线
    def after_trade(self, trade_date):
        cash_asset = self.context.available_cash
        stock_asset = 0

        # hold_stocks = ds.get_multi_trade_record(list(self.context.cur_position.keys()), trade_date)
        for stock_code, position in self.context.cur_position.items():
            # 如果股票停牌, 需要回去最近一个交易日的收盘价, 另外买卖股票的时候也要考虑股票是否停牌
            # price = hold_stocks[hold_stocks['股票代码'] == stock_code].iloc[0]['收盘价']
            price = ds.get_latest_close_price(stock_code, trade_date)
            hold_quantity = position.get_quantity()

            if hold_quantity <= 0:
                continue

            stock_asset = stock_asset + price * hold_quantity

            self.context.his_position = self.context.his_position.append({
                "交易日期": trade_date,
                "股票代码": stock_code,
                "持仓数量": hold_quantity,
                "当日收盘价": price,
            }, ignore_index=True)

        total_asset = cash_asset + stock_asset

        # 昨日总资产
        last_total_asset = self.context.init_cash
        if len(self.context.his_account) > 0:
            last_total_asset = self.context.his_account.iloc[-1]['总资产']

        self.context.his_account = self.context.his_account.append(
            {
                "交易日期": trade_date,
                "资金资产": cash_asset,
                "股票资产": stock_asset,
                "总资产": total_asset,
                "仓位比例": 1.0 * stock_asset / total_asset,
                "当日盈亏": total_asset - last_total_asset,
                "涨跌幅": 1.0 * (total_asset - last_total_asset) / last_total_asset,
            }, ignore_index=True
        )

    # 对日期进行采样
    def sample_date(self, interval=1):
        trade_date_list = self.context.get_trade_date_list()
        if interval == 1:
            return trade_date_list

        res = []

        for i in range(len(trade_date_list)):
            if i % interval == 0:
                res.append(trade_date_list[i])
        return res

    # 对日期进行采样
    def set_strategy_name(self):

        strategy_name = self.context.strategy_name = self.__class__.__name__
        if hasattr(self.__class__, "name"):
            name = getattr(self.__class__, "name")
            if isinstance(name, str):
                strategy_name = name

        self.context.strategy_name = strategy_name


if __name__ == "__main__":
    context = BackContext("2020-01-04", "2020-03-01", [], print_progress=True)
    ds = DiskDataSource(context)
    strategy = AbstractBackStrategy(context, ds)
    strategy.set_strategy_name()
    print(strategy.context.strategy_name)
