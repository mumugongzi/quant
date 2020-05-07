"""
邢不行策略分享会
微信：xbx9025
"""
from program.选股策略.Functions import *
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数

# ===数据周期
period_type = 'W'  # W代表周，M代表月

# ===读取所有股票代码的列表
path = '/Users/xingbuxingx/Desktop/策略分享会直播/191011- 若干选股策略说明及如何简单组合策略/如何简单组合策略/data/选股策略/xbx_stock_day_data/stock'
stock_code_list = get_stock_code_list_in_one_dir(path)

# ===循环读取并且合并
# 导入上证指数，保证指数数据和股票数据在同一天结束，不然会出现问题。
index_data = import_index_data('/Users/xingbuxingx/Desktop/策略分享会直播/191011- 若干选股策略说明及如何简单组合策略/如何简单组合策略/data/选股策略/sh000001.csv')

# 循环读取股票数据
all_stock_data = pd.DataFrame()  # 用于存储数据
for code in stock_code_list:
    print(code)

    """
    注意点：在计算个股数据的时候，有两个重要步骤，一个是和上证指数合并，补全停牌日期。一个是转化为其他周期的数据
    一定要注意
    """

    # =读入股票数据
    df = pd.read_csv(path + '/%s.csv' % code, encoding='gbk', skiprows=1, parse_dates=['交易日期'])

    # =计算涨跌幅
    df['涨跌幅'] = df['收盘价'] / df['前收盘价'] - 1
    df['开盘买入涨跌幅'] = df['收盘价'] / df['开盘价'] - 1  # 为之后开盘买入做好准备

    # 计算换手率
    df['换手率'] = df['成交额'] / df['流通市值']

    # 计算后复权价
    df['复权因子'] = (1 + df['涨跌幅']).cumprod()
    df['收盘价_复权'] = df['复权因子'] * (df.iloc[0]['收盘价'] / df.iloc[0]['复权因子'])
    df['开盘价_复权'] = df['开盘价'] / df['收盘价'] * df['收盘价_复权']
    df['最高价_复权'] = df['最高价'] / df['收盘价'] * df['收盘价_复权']
    df['最低价_复权'] = df['最低价'] / df['收盘价'] * df['收盘价_复权']

    # 计算均线、bias
    df['均线_20'] = df['收盘价_复权'].rolling(20, min_periods=1).mean()
    df['bias_20'] = df['收盘价_复权'] / df['均线_20'] - 1

    # 计算kdj指标
    low_list = df['最低价_复权'].rolling(9, min_periods=1).min()
    high_list = df['最高价_复权'].rolling(9, min_periods=1).max()
    rsv = (df['收盘价_复权'] - low_list) / (high_list - low_list) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']

    # 计算交易天数
    df['上市至今交易天数'] = df.index+1

    # =将股票和上证指数合并，补全停牌的日期，新增数据"是否交易"、"指数涨跌幅"
    df = merge_with_index_data(df, index_data)

    # =计算量价相关因子
    df['复权因子'] = (1 + df['涨跌幅']).cumprod()
    df['量价相关系数_1_10'] = df['复权因子'].rolling(10).corr(df['换手率'].rolling(10))

    # =计算涨跌停价格
    df = cal_if_zhangting_with_st(df)

    # =计算下个交易的相关情况
    df['下日_是否交易'] = df['是否交易'].shift(-1)
    df['下日_一字涨停'] = df['一字涨停'].shift(-1)
    df['下日_开盘涨停'] = df['开盘涨停'].shift(-1)
    df['下日_是否ST'] = df['股票名称'].str.contains('ST').shift(-1)
    df['下日_是否退市'] = df['股票名称'].str.contains('退').shift(-1)
    df['下日_开盘买入涨跌幅'] = df['开盘买入涨跌幅'].shift(-1)

    # =将日线数据转化为月线或者周线，如果新增一些字段，一定要查看是否在这个函数中是否需要修改
    df = transfer_to_period_data(df, period_type=period_type)

    # =对数据进行整理
    # 删除上市的第一个周期
    df.drop([0], axis=0, inplace=True)  # 删除第一行数据
    # 删除2017年之前的数据
    df = df[df['交易日期'] > pd.to_datetime('20061215')]
    # 计算下周期每天涨幅
    df['下周期每天涨跌幅'] = df['每天涨跌幅'].shift(-1)
    del df['每天涨跌幅']

    # =删除不能交易的周期数
    # 删除月末为st状态的周期数
    df = df[df['股票名称'].str.contains('ST') == False]
    # 删除月末有退市风险的周期数
    df = df[df['股票名称'].str.contains('退') == False]
    # 删除月末不交易的周期数
    df = df[df['是否交易'] == 1]
    # 删除交易天数过少的周期数
    df = df[df['交易天数'] / df['市场交易天数'] >= 0.8]
    df.drop(['交易天数', '市场交易天数'], axis=1, inplace=True)

    # 合并数据
    all_stock_data = all_stock_data.append(df, ignore_index=True)

# ===将数据存入数据库之前，先排序、reset_index
all_stock_data.sort_values(['交易日期', '股票代码'], inplace=True)
all_stock_data.reset_index(inplace=True, drop=True)

# 将数据存储到hdf文件
all_stock_data.to_hdf('/Users/jxing/Downloads/190927-量价相关选股策略/量价相关/data/选股策略/all_stock_data_'+period_type+'.h5', 'df', mode='w')

# ===注意事项
# 目前我们只根据市值选股，所以数据中只有一些基本数据加上市值。
# 实际操作中，会根据很多指标进行选股。在增加这些指标的时候，一定要注意在这两个函数中如何增加这些指标：merge_with_index_data(), transfer_to_period_data()
# 比如增加：成交量、财务数据
