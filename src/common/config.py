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

# 如果目录不存在, 创建目录
os.makedirs(output_data_path, exist_ok=True)

# 回测报告输出目录
# back_report_path = os.path.abspath(os.path.join(root_path, os.pardir, 'back_report')) + "/"
back_report_path = os.path.abspath(os.path.join(root_path, 'back_report')) + "/"
os.makedirs(back_report_path, exist_ok=True)

# # 当前路径
# print os.path.abspath('.')
# # 父辈路径
# print os.path.abspath('..')

rename_map = {
    'index_code': '指数代码',
    'code': '股票代码',
    'date': '交易日期',
    'open': '开盘价',
    'close': '收盘价',
    'high': '最高价',
    'low': '最低价',
    'change': '涨跌幅',
    'volume': '成交量',
    'money': '成交额',
    'traded_market_value': '流通市值',
    'market_value': '总市值',
    'turnover': '换手率',
    'adjust_price': '后复权价',
    'adjust_price_f': '前复权价',
    'PE_TTM': '市盈率TTM',
    'PS_TTM': '市销率TTM',
    'PC_TTM': '市现率TTM',
    'PB': '市净率',
}

index_name_map = {
    'sh0000001': '上证指数',
}
