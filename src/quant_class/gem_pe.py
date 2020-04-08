# -*- coding: utf-8 -*-
"""
作者：邢不行

本系列帖子“量化小讲堂”，通过实际案例教初学者使用python、pandas进行金融数据处理，希望能对大家有帮助。

必读文章《10年400倍策略分享-附视频逐行讲解代码》：http://bbs.pinggu.org/thread-5558776-1-1.html

所有系列文章汇总请见：http://bbs.pinggu.org/thread-3950124-1-1.html

想要快速、系统的学习量化知识，可以参与我与论坛合作开设的《python量化投资入门》视频课程：http://www.peixun.net/view/1028.html，我会亲自授课，随问随答。
参与课程还可以免费加入我的小密圈，我每天会在圈中分享量化的所见所思，圈子介绍：http://t.xiaomiquan.com/BEiqzVB

微信：xbx_laoshi，量化交流Q群(快满)：438143420，有问题欢迎交流。

文中用到的A股数据可在www.yucezhe.com下载，这里可以下载到所有股票、从上市日起的交易数据、财务数据、分钟数据、分笔数据、逐笔数据等。
"""
import os
import pandas as pd
from common.Functions import get_stock_code_list, import_stock_data
from common import config
from common import config
import numpy as np

import matplotlib.pyplot as plt

plt.rcParams['font.family'] = ['SimHei']

# ========== 遍历数据文件夹中所有股票文件的文件名，得到股票代码列表stock_code_list
stock_code_list = get_stock_code_list()

# ========== 根据上一步得到的代码列表，遍历所有创业板股票，将这些股票合并到一张表格all_stock中
all_stock = pd.DataFrame()

# 遍历每个创业板的股票
progress = 0
for code in stock_code_list:

    progress = progress + 1
    print("Progress: %d/%d" % (progress, len(stock_code_list)))

    # 创业板股票代码都是以3开头，不是3开的股票跳过
    if code[2] != '3':
        continue

    # 从csv文件中读取该股票数据
    colums_list = ['交易日期', '股票代码', '开盘价', '最高价', '最低价', '收盘价', '涨跌幅', '成交额', '成交额', '总市值', '市盈率TTM']
    stock_data = import_stock_data(code, columns=colums_list)

    # 删除PE_TTM值为空的数据行
    stock_data = stock_data[stock_data['市盈率TTM'].notnull()]

    # PE_TTM = 总市值 / 净利润_TTM，这里通过这个公式计算净利润_TTM
    stock_data['净利润'] = stock_data['总市值'] / stock_data['市盈率TTM']

    # 选取需要的字段，去除其他不需要的字段
    stock_data = stock_data[['股票代码', '交易日期', '总市值', '净利润']]

    # 将该股票的合并到output中
    all_stock = all_stock.append(stock_data, ignore_index=True)

# ========== 基于all_stock表格，通过groupby语句，计算创业板股票每天的平均市盈率
# 通过groupby语句计算每天所有股票的市值之和、净利润之和，以及当天交易的股票的数量
output = all_stock.groupby('交易日期')[['总市值', '净利润']].sum()
output['股票数量'] = all_stock.groupby('交易日期').size()

# 平均市盈率 = 所有股票的市值之和 / 所有股票的净利润之和
output['平均市盈率'] = output['总市值'] / output['净利润']
max_pe = output['平均市盈率'].max()

# 算好的数据输出
output.to_csv(config.output_data_path + '创业板平均市盈率.csv', encoding='utf8')  # 注意：这里请填写数据文件在您电脑中的路径

date_list = list(output.index)
date_list = sorted(date_list)
# index是日期
plt.figure(figsize=(16, 8))
plt.plot(date_list, output['平均市盈率'])
plt.title(u"A股创业板平均市盈率")
plt.xlabel(u"交易日期")
plt.ylabel(u"平均市盈率")
plt.yticks(np.arange(0, max_pe, 10))
plt.xticks(pd.date_range(start=date_list[0], end=date_list[len(date_list) - 1], freq="6M"), rotation=60)
plt.grid(True, ls='--')

# savefig函数必须在show函数之前调用, 否则保存的图片是空白的
plt.savefig(config.output_data_path + "创业板平均市盈率.png")
plt.show()

print(output)
