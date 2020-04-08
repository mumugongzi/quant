# coding: utf-8

"""
小市值因子回测
"""
from context.context import BackContext
from data.datasource import ds
from report.report import BackReport
from strategy.strategy import AbstractBackStrategy, BUY_SIGNAL
from tool.progress import print_progress
from common.Functions import get_stock_code_list


class SmallCapStrategy(AbstractBackStrategy):
    name = '小市值策略'

    def prepare(self):
        start_date = self.context.start_date
        end_date = self.context.end_date
        stock_list = self.context.stock_list
        stock_data = ds.get_multi_stock(stock_list, start_date, end_date, columns=['交易日期', '股票代码', '总市值'])

        change_day_num = self.context.params['调仓周期']
        stock_num = self.context.params['选股数量']

        sample_date_list = self.sample_date(change_day_num)
        self.sample_date_list = sample_date_list
        for trade_date in sample_date_list:
            if self.context.print_progress:
                print_progress(len(sample_date_list), step=0.01, name='prepare')
            cur_data = stock_data[stock_data['交易日期'] == trade_date]
            cur_data = cur_data.sort_values('总市值')
            cur_data = cur_data[:stock_num]
            stock_data.loc[(stock_data['交易日期'] == trade_date) &
                           stock_data['股票代码'].isin(cur_data['股票代码']), "交易信号"] = BUY_SIGNAL
        self.stock_data = stock_data

    def handle_bar(self, trade_date, **kwargs):
        if trade_date not in self.sample_date_list:
            return
        # 先平掉所有仓位
        self.close_out_all(trade_date)

        stock_data = self.stock_data
        choose_stock = stock_data[(stock_data['交易日期'] == trade_date) & (stock_data['交易信号'] == BUY_SIGNAL)]
        choose_stock = choose_stock['股票代码'].values

        stock_num = self.context.params['选股数量']
        for stock_code in choose_stock:
            self.order_pos_rate(stock_code, trade_date, rate=1.0 / stock_num, side=BUY_SIGNAL)


if __name__ == '__main__':

    start_date = '2017-01-01'
    end_date = '2020-01-01'
    stock_list = get_stock_code_list()
    columns = ['交易日期', '股票代码', '开盘价', '收盘价', '涨跌幅', '总市值']

    ds.import_data(start_date, end_date, stock_list, columns=columns)
    rpt = BackReport()

    params_list = [(20, 30)]

    for p in params_list:
        context = BackContext(start_date, end_date, stock_list, columns, init_cash=1000000,
                              params={"调仓周期": p[0], "选股数量": p[1]}, print_progress=True)

        stra = SmallCapStrategy(context)
        stra.run()

        rpt.append_ctx(context)
    rpt.save(mode='w')
