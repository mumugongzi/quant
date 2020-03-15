# coding=utf-8
"""
@author: 邢不行
微信：xingbx007
小密圈：每天分享、讨论量化的内容，http://t.xiaomiquan.com/BEiqzVB
量化课程（在微信中打开）：https://st.h5.xiaoe-tech.com/st/5mXf4p6se
"""
import os

# 获取当前程序的地址
current_file = __file__

# 程序根目录地址
root_path = os.path.abspath(os.path.join(current_file, os.pardir, os.pardir, os.pardir))

# 输入数据根目录地址
train_data_path = os.path.abspath(os.path.join(root_path, 'data'))

index_data_path = os.path.abspath(os.path.join(root_path, 'data', 'index_data')) + "/"

stock_data_path = os.path.abspath(os.path.join(root_path, 'data', 'stock_data')) + "/"

# 输出数据根目录地址
output_data_path = os.path.abspath(os.path.join(root_path, 'output')) + "/"

# # 当前路径
# print os.path.abspath('.')
# # 父辈路径
# print os.path.abspath('..')

name_map = {
    "指数代码": "index_code",
    "股票代码": "code",
    "交易日期": "date",
    "开盘价": "open",
    "收盘价": "close",
    "最高价": "high",
    "最低价": "low",
    "涨跌幅": "change",
    "成交量": "volume",
    "成交额": "money",
    "流通市值": "traded_market_value",
    "总市值": "market_value",
    "换手率": "turnover",
    "后复权价": "adjust_price",
    "前复权价": "adjust_price_f",
    "市盈率TTM": "PE_TTM",
    "市销率TTM": "PS_TTM",
    "市现率TTM": "PC_TTM",
    "市净率": "PB"
}
