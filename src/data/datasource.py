# coding: utf-8
import time

import pandas as pd

from common.Functions import import_stock_data
from data import StockDataSource, filter_columns, merge_import_columns
from tool import progress
from common.Functions import get_stock_code_list


class DiskDataSource(StockDataSource):
    need_columns = ['股票代码', '交易日期']

    def __init__(self):
        self.cache = pd.DataFrame()
        self.has_import = False
        self.data_map = {}

    def import_data(self, start_date, end_date, stock_list, columns=None, print_progress=True):

        # 避免重复调用导致重复导入数据
        if self.has_import:
            return

        columns = merge_import_columns(columns, self.__class__.need_columns)
        total = len(stock_list)

        stock_data_list = []
        for code in stock_list:
            if print_progress:
                progress.print_progress(total, step=0.01, name="import_data")
            stock_data = import_stock_data(code, columns=columns)

            stock_data = stock_data[(stock_data['交易日期'] >= start_date) & (stock_data['交易日期'] <= end_date)]
            stock_data_list.append(stock_data)

            # self.cache = self.cache.append(stock_data, ignore_index=True)
            # self.data_map[code] = stock_data
        self.cache = pd.concat(stock_data_list)
        print(self.cache)
        self.cache.sort_values(by=['交易日期'], inplace=True)
        self.cache.reset_index(inplace=True, drop=True)
        self.has_import = True

    def get_one_stock(self, stock_code, start_date, end_date, columns=None):
        stock_data = self.cache
        df = stock_data[
            (stock_data["股票代码"] == stock_code) & (stock_data["交易日期"] >= start_date) & (stock_data["交易日期"] <= end_date)]
        return filter_columns(df, columns)

    def get_one_stock_from_map(self, stock_code, start_date, end_date, columns=None):
        stock_data = self.data_map[stock_code]
        df = stock_data[
            (stock_data["股票代码"] == stock_code) & (stock_data["交易日期"] >= start_date) & (stock_data["交易日期"] <= end_date)]
        df = df.copy()
        return filter_columns(df, columns)

    def get_multi_stock_from_map(self, stock_code_list, start_date, end_date, columns=None):
        res = pd.DataFrame()
        for stock_code in stock_code_list:
            stock_data = self.data_map[stock_code]
            df = stock_data[
                (stock_data["股票代码"] == stock_code) & (stock_data["交易日期"] >= start_date) & (
                        stock_data["交易日期"] <= end_date)]
            res = res.append(df, ignore_index=True)
        # print(res)
        return filter_columns(res, columns)

    def get_multi_stock(self, stock_code_list, start_date, end_date, columns=None):
        stock_data = self.cache
        df = stock_data[(stock_data["股票代码"].isin(stock_code_list)) & (stock_data["交易日期"] >= start_date) & (
                stock_data["交易日期"] <= end_date)]
        df = df.copy()
        return filter_columns(df, columns)

    def get_one_trade_record(self, stock_code, trade_date, columns=None):
        stock_data = self.cache
        df = stock_data[(stock_data["股票代码"] == stock_code) & (stock_data["交易日期"] == trade_date)]
        df = df.copy()
        return filter_columns(df, columns)

    def get_latest_close_price(self, stock_code, trade_date):
        trade_record = self.get_one_trade_record(stock_code, trade_date)
        if len(trade_record) > 0:
            return trade_record.iloc[0]["收盘价"]
        else:
            # 如果停牌, 则获取上一个交易日收盘价
            stock_data = self.cache
            df = stock_data[(stock_data["股票代码"] == stock_code) & (stock_data["交易日期"] < trade_date)]
            return df.iloc[-1]["收盘价"]

    def get_multi_trade_record(self, stock_code_list, trade_date, columns=None):
        stock_data = self.cache
        df = stock_data[(stock_data["股票代码"].isin(stock_code_list)) & (stock_data["交易日期"] == trade_date)]
        df = df.copy()
        return filter_columns(df, columns)

    def get_all(self):
        return self.cache

    def is_suspended(self, stock_code, trade_date):
        record = self.get_one_trade_record(stock_code, trade_date)
        return len(record) <= 0


ds = DiskDataSource()


def init_ds(start_date, end_date, stock_list, columns=None, print_progress=True):
    ds.import_data(start_date, end_date, stock_list, columns, print_progress)


if __name__ == "__main__":
    stock_code_list = get_stock_code_list()
    # stock_code_list = ['sh600001']
    ds = DiskDataSource()

    ds.import_data('2008-01-01', '2019-02-01', stock_code_list, columns=['股票代码', '开盘价', '收盘价'], print_progress=True)

    print(ds.is_suspended('sh600001', '2009-01-06'))
    # exit(0)

    print(ds.cache)

    print("==========get_one_stock=======")
    print(ds.get_one_stock('sh600001', '2006-01-10', '2006-01-20'))

    print("==========get_multi_stock=======")
    print(ds.get_multi_stock(['sh600001', 'sh600010'], '2006-01-10', '2006-01-20', columns=['交易日期', '股票代码', '收盘价']))

    print("==========get_one_trade_record=======")
    print(ds.get_one_trade_record('sh600001', '2006-01-17'))

    print("==========get_multi_stock=======")
    print(ds.get_multi_trade_record(['sh600001', 'sh600010'], '2006-01-16'))

    print("isintance of StockDataSource: {}".format(isinstance(ds, StockDataSource)))

    start_time = time.time()
    ds.get_one_stock('sh600001', '2006-01-10', '2006-01-20')
    end_time = time.time()
    print("get_one_stock cost: %.4fs" % (end_time - start_time))

    start_time = time.time()
    ds.get_one_stock_from_map('sh600001', '2006-01-10', '2006-01-20')
    end_time = time.time()
    print("get_one_stock_from_map cost: %.4fs" % (end_time - start_time))

    for n in range(50, 500, 50):
        start_time = time.time()
        ds.get_multi_stock(stock_code_list[:n], '2006-01-10', '2006-01-20')
        end_time = time.time()
        print("get_multi_stock, stock list size %d, cost: %.4fs" % (n, end_time - start_time))

    for n in range(50, 500, 50):
        start_time = time.time()
        ds.get_multi_stock_from_map(stock_code_list[:n], '2006-01-10', '2006-01-20')
        end_time = time.time()
        print("get_multi_stock_from_map, stock list size %d, cost: %.4fs" % (n, end_time - start_time))

"""
平铺的DataFrame VS map[code]DataFrame查找性能对比如下:
get_one_stock cost: 0.0029s
get_one_stock_from_map cost: 0.0017s
get_multi_stock, stock list size 50, cost: 0.0029s
get_multi_stock, stock list size 100, cost: 0.0027s
get_multi_stock, stock list size 150, cost: 0.0031s
get_multi_stock, stock list size 200, cost: 0.0032s
get_multi_stock, stock list size 250, cost: 0.0031s
get_multi_stock, stock list size 300, cost: 0.0034s
get_multi_stock, stock list size 350, cost: 0.0036s
get_multi_stock, stock list size 400, cost: 0.0033s
get_multi_stock, stock list size 450, cost: 0.0030s
get_multi_stock_from_map, stock list size 50, cost: 0.1076s
get_multi_stock_from_map, stock list size 100, cost: 0.2190s
get_multi_stock_from_map, stock list size 150, cost: 0.2765s
get_multi_stock_from_map, stock list size 200, cost: 0.3832s
get_multi_stock_from_map, stock list size 250, cost: 0.4874s
get_multi_stock_from_map, stock list size 300, cost: 0.6561s
get_multi_stock_from_map, stock list size 350, cost: 0.6541s
get_multi_stock_from_map, stock list size 400, cost: 0.7489s
get_multi_stock_from_map, stock list size 450, cost: 0.8652s

结论: 查找单个股票数据, map结构效率更高, 批量查找时, 平铺的DataFrame结构的时间复杂度是常数,
而且效率远远高于map结构
"""
