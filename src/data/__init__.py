# coding: utf-8

class StockDataSource(object):

    def __init__(self):
        pass

    def import_data(self):
        pass

    def get_one_stock(self, stock_code, start_date, end_date, columns=None):
        pass

    def get_multi_stock(self, stock_code_list, start_date, end_date, columns=None):
        pass

    def get_one_trade_record(self, stock_code, trade_date, columns=None):
        pass

    def get_multi_trade_record(self, stock_code_list, trade_date, columns=None):
        pass

    def get_all(self):
        pass


def filter_columns(df, columns):
    if columns is not None and len(columns) > 0:
        df = df[columns]
        df = df.copy(deep=True)
    df = df.copy(deep=True)
    df.reset_index(drop=True, inplace=True)
    # 按交易日期升序排列
    df.sort_values(by=['交易日期'], inplace=True)
    return df


def merge_import_columns(*columns):
    """
    :param columns: 列名列表元组, 比如(['交易日期'],['股票代码'])
    :return: 需要导入的数据列
    """

    sets = []
    # 如果为空, 就默认导入全部的数据列
    for elem in columns:
        if elem is None or len(elem) <= 0:
            return []
        else:
            sets = sets + elem

    return list(set(sets))
