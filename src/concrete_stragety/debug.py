# coding: utf-8
from report.report import BackReport
from strategy.strategy import *
from data.datasource import ds
import pandas as pd

# 显示所有列
# pd.set_option('display.max_columns', None)
# 显示所有行
# pd.set_option('display.max_rows', None)
# 设置value的显示长度为100，默认为50
# pd.set_option('max_colwidth',100)

"""
调试回测框架, 无实际用途
"""


class DebugStrategy(AbstractBackStrategy):
    name = '调试测试'

    # def __init__(self, context):
    #     super.__init__(context)

    def prepare(self):
        fisrt_code = self.context.stock_list[0]
        start_date = self.context.start_date
        end_date = self.context.end_date
        first_stock = ds.get_one_stock(stock_code=fisrt_code, start_date=start_date, end_date=end_date,
                                       columns=['交易日期', '股票代码', '开盘价'])
        first_stock['交易信号'] = None
        for i in range(0, len(first_stock)):
            if i % 2 == 0:
                first_stock.loc[i, '交易信号'] = BUY_SIGNAL
            else:
                first_stock.loc[i, '交易信号'] = SELL_SIGNAL
        self.first_stock = first_stock

    def handle_bar(self, trade_date, **kwargs):

        # if hasattr(trade_date, 'strftime'):
        # trade_date = getattr(trade_date, 'strftime')('%Y-%m-%d')
        # getattr(trade_date, 'strftime')
        # strftime('%Y-%m-%d')
        records = self.first_stock[self.first_stock['交易日期'] == trade_date]
        stock_code = records.iloc[0]['股票代码']
        if records.iloc[0]['交易信号'] == BUY_SIGNAL:
            self.order_pos_rate(stock_code, trade_date, 1.0)
        else:
            self.close_out_all(trade_date)


if __name__ == '__main__':
    start_date = '2015-01-01'
    end_date = '2020-03-01'
    stock_list = ['sz000001']
    columns = ['交易日期', '股票代码', '开盘价', '收盘价', '涨跌幅']

    ds.import_data(start_date, end_date, stock_list)
    rpt = BackReport()

    period = [1, 2, 3]

    for p in period:
        context = BackContext(start_date, end_date, stock_list, columns, init_cash=10000, params={"调仓日期": p}, print_progress=True)

        stra = DebugStrategy(context)
        stra.run()

        rpt.append_ctx(context)
    rpt.save(mode='w')
