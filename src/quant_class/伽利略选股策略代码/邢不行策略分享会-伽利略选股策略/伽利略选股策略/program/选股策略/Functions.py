"""
邢不行策略分享会
微信：xbx9025
"""
import pandas as pd  # 导入pandas，我们一般为pandas取一个别名叫做pd
from decimal import Decimal, ROUND_HALF_UP
import os


# 导入某文件夹下所有股票的代码
def get_stock_code_list_in_one_dir(path):
    """
    从指定文件夹下，导入所有csv文件的文件名
    :param path:
    :return:
    """
    stock_list = []

    # 系统自带函数os.walk，用于遍历文件夹中的所有文件
    for root, dirs, files in os.walk(path):
        if files:  # 当files不为空的时候
            for f in files:
                if f.endswith('.csv'):
                    stock_list.append(f[:8])

    return sorted(stock_list)


# 导入指数
def import_index_data(path):
    """
    从指定位置读入指数数据。指数数据来自于：program/构建自己的股票数据库/案例_获取股票最近日K线数据.py
    :param path:
    :return:
    """
    # 导入指数数据
    df_index = pd.read_csv(path, parse_dates=['candle_end_time'])
    df_index['指数涨跌幅'] = df_index['close'].pct_change()
    df_index = df_index[['candle_end_time', '指数涨跌幅']]
    df_index.dropna(subset=['指数涨跌幅'], inplace=True)

    df_index.rename(columns={'candle_end_time': '交易日期'}, inplace=True)
    df_index.sort_values(by=['交易日期'], inplace=True)
    df_index.reset_index(inplace=True, drop=True)

    return df_index


# 将股票数据和指数数据合并
def merge_with_index_data(df, index_data):
    """
    原始股票数据在不交易的时候没有数据。
    将原始股票数据和指数数据合并，可以补全原始股票数据没有交易的日期。
    :param df: 股票数据
    :param index_data: 指数数据
    :return:
    """

    # ===将股票数据和上证指数合并，结果已经排序
    df = pd.merge(left=df, right=index_data, on='交易日期', how='right', sort=True, indicator=True)

    # ===对开、高、收、低、前收盘价价格进行补全处理
    # 用前一天的收盘价，补全收盘价的空值
    df['收盘价'].fillna(method='ffill', inplace=True)
    # 用收盘价补全开盘价、最高价、最低价的空值
    df['开盘价'].fillna(value=df['收盘价'], inplace=True)
    df['最高价'].fillna(value=df['收盘价'], inplace=True)
    df['最低价'].fillna(value=df['收盘价'], inplace=True)
    # 补全前收盘价
    df['前收盘价'].fillna(value=df['收盘价'].shift(), inplace=True)

    # ===将停盘时间的某些列，数据填补为0
    fill_0_list = ['成交量', '成交额', '涨跌幅', '开盘买入涨跌幅']
    df.loc[:, fill_0_list] = df[fill_0_list].fillna(value=0)

    # ===用前一天的数据，补全其余空值
    df.fillna(method='ffill', inplace=True)

    # ===去除上市之前的数据
    df = df[df['股票代码'].notnull()]

    # ===判断计算当天是否交易
    df['是否交易'] = 1
    df.loc[df['_merge'] == 'right_only', '是否交易'] = 0
    del df['_merge']

    df.reset_index(drop=True, inplace=True)

    return df


# 将日线数据转换为其他周期的数据
def transfer_to_period_data(df, period_type='m'):
    """
    将日线数据转换为相应的周期数据
    :param df:
    :param period_type:
    :return:
    """

    # 将交易日期设置为index
    df['周期最后交易日'] = df['交易日期']
    df.set_index('交易日期', inplace=True)

    period_df = df.resample(rule=period_type).agg(
        {
            # 必须列
            '周期最后交易日': 'last',
            '股票代码': 'last',
            '股票名称': 'last',
            '是否交易': 'last',
            '下日_是否交易': 'last',
            '下日_开盘涨停': 'last',
            '下日_是否ST': 'last',
            '下日_是否退市': 'last',
            '下日_开盘买入涨跌幅': 'last',

            # 因子列
            '开盘价': 'first',
            '最高价': 'max',
            '最低价': 'min',
            '收盘价': 'last',
            '成交量': 'sum',
            '成交额': 'sum',
            '流通市值': 'last',
            '总市值': 'last',

            '量价相关系数_1_10': 'last',
            '均线_20': 'last',
            'bias_20': 'last',

            '上市至今交易天数': 'last',

            'K': 'last',
            'D': 'last',
            'J': 'last',
        }
    )

    # 计算必须额外数据
    period_df['周期_涨跌幅'] = df['涨跌幅'].resample(period_type).apply(lambda x: (x + 1.0).prod() - 1.0)
    period_df['交易天数'] = df['是否交易'].resample(period_type).sum()
    period_df['市场交易天数'] = df['股票代码'].resample(period_type).size()
    period_df = period_df[period_df['市场交易天数'] > 0]  # 有的时候整个周期不交易（例如春节、国庆假期），需要将这一周期删除

    # 计算其他因子

    # 计算周期资金曲线
    period_df['每天涨跌幅'] = df['涨跌幅'].resample(period_type).apply(lambda x: list(x))

    # 重新设定index
    period_df.reset_index(inplace=True)
    period_df['交易日期'] = period_df['周期最后交易日']
    del period_df['周期最后交易日']

    return period_df


# 计算是涨停
def cal_if_zhangting_with_st(df):
    """
    计算股票当天的涨跌停价格。在计算涨跌停价格的时候，按照严格的四舍五入。
    包含st股，但是不包含新股

    :param df: 必须得是日线数据。必须包含的字段：前收盘价，开盘价，最高价，最低价
    :return:
    """

    # 计算涨停价格
    df['涨停价'] = df['前收盘价'] * 1.1

    # 针对st进行修改
    df.loc[df['股票名称'].str.contains('ST'), '涨停价'] = df['前收盘价'] * 1.05

    # 四舍五入
    df['涨停价'] = df['涨停价'].apply(lambda x: float(Decimal(x * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 100))

    # 判断是否一字涨停
    df['一字涨停'] = False
    df.loc[df['最低价'] >= df['涨停价'], '一字涨停'] = True

    # 判断是否开盘涨停
    df['开盘涨停'] = False
    df.loc[df['开盘价'] >= df['涨停价'], '开盘涨停'] = True

    return df
