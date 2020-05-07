# coding: utf-8

import pandas as pd
import datetime

# 多头
SIGNAL_LONG = 'long'

# 空头
SIGNAL_SHORT = 'short'

# None
SIGNAL_NONE = 'none'


# 米开朗基罗择时
class MichelangeloTiming(object):

    def __init__(self, index_code, N1, N2):
        """
        :param index_code: 择时用指数代码
        :param N1: 使用股价创N1日新高计算扩散指标
        :param N2: 扩散指标一次平滑窗口大小
        """
        self.index_code = index_code
        self.N1 = N1
        self.N2 = N2

        # 扩散指标二次平滑窗口大小
        self.N3 = 20

        self.his_data = pd.DataFrame()

        self.last_trade_date = {}

    def initialize(self, context):
        """
        :param context: 回测上下文
        :return:
        """
        start_date = self.convert_date(context.run_params['start_date'])

        trade_date_list = sorted(list(get_all_trade_days()))
        for i in range(1, len(trade_date_list)):
            self.last_trade_date[trade_date_list[i]] = trade_date_list[i - 1]

        # 初始化N2+N3天的数据
        n = self.N2 + self.N3 + 10
        init_date_list = []
        for i in range(1, len(trade_date_list)):
            if trade_date_list[i + n - 1] < start_date <= trade_date_list[i + n]:
                for j in range(i, i + n - 1):
                    init_date_list.append(trade_date_list[j])

        for date in init_date_list:
            factor = self.get_factor(date)
            self.his_data.append(factor)

        self.his_data['ma_N2'] = self.his_data['factor'].rolling(window=self.N2).mean()
        self.his_data['ma_N3'] = self.his_data['ma_N2'].rolling(window=self.N3).mean()

        self.his_data['diff'] = self.his_data['ma_N3'].diff()

    # 改函数只能在交易当日调用, 当天可以调用多次
    def get_signal(self, context):
        """
        :param context: 回测上下文
        :return:
        """

        # 获取前一个交易日
        last_date = self.convert_date(context.previous_date)
        if self.his_data.iloc[-1]['date'] > last_date:
            raise Exception("不能间隔交易日调用改函数")

        if self.his_data.iloc[-1]['date'] < last_date:
            factor = self.get_factor(last_date)
            ma_N2 = (self.his_data['factor'].iloc[1 - self.N2:].sum() + factor['factor']) / self.N2
            ma_N3 = (self.his_data['ma_N2'].iloc[1 - self.N3:].sum() + ma_N2) / self.N3
            diff = ma_N3 - self.his_data['ma_N3'].iloc[-1]
            self.his_data.append({
                "date": factor['date'],
                "factor": factor['factor'],
                "ma_N2": ma_N2,
                "ma_N3": ma_N3,
                "diff": diff,
            })

        diff1 = self.his_data.iloc[-1]['diff']
        diff2 = self.his_data.iloc[-2]['diff']
        if (diff2 is None or diff2 < 0) and diff1 > 0:
            return SIGNAL_LONG

        if (diff2 is None or diff2 > 0) and diff1 < 0:
            return SIGNAL_SHORT

        return None

    def get_factor(self, date):
        """
        :param date: datetime类型, 计算当天的扩散指标
        :return:
        """
        stock_list = get_index_stocks(self.index_code, date=date)
        price_df = get_bars(stock_list, count=self.N1, unit='1d', end_dt=date, fields=['date', 'close'],
                            fq_ref_date=date,
                            df=True, include_now=True)
        # print(price_df)

        change_df = price_df.groupby(level=[0]).apply(lambda x: x.iloc[-1]['close'] / x.iloc[0]['close'] - 1)

        # change_df.reset_index(inplace=True)
        # print(change_df)

        cap_df = get_valuation(stock_list, end_date=date, fields=['circulating_market_cap'], count=1)
        cap_df.set_index('code', inplace=True)

        cap_df['n_change'] = change_df

        # print(cap_df[cap_df['n_change'] > 0])

        factor = cap_df[cap_df['n_change'] > 0]['circulating_market_cap'].sum() / cap_df['circulating_market_cap'].sum()
        # print(factor)

        return {
            "date": date,
            "factor": factor,
        }

    def convert_date(self, date):
        if isinstance(date, datetime.date):
            return datetime.datetime(year=date.year, month=date.month, day=date.day)
        return date
