# coding=utf-8
"""
本系列帖子“量化小讲堂”，通过实际案例教初学者使用python、pandas进行金融数据处理，希望能对大家有帮助。


必读文章《10年400倍策略分享-附视频逐行讲解代码》：http://bbs.pinggu.org/thread-5558776-1-1.html


所有系列文章汇总请见：http://bbs.pinggu.org/thread-3950124-1-1.html


想要快速、系统的学习量化知识，可以参与我与论坛合作开设的《python量化投资入门》视频课程：http://www.peixun.net/view/1028.html，我会亲自授课，随问随答。
参与课程还可以免费加入我的小密圈，我每天会在圈中分享量化的所见所思，圈子介绍：http://t.xiaomiquan.com/BEiqzVB


微信：xbx_laoshi，量化交流Q群(快满)：438143420，有问题欢迎交流。


文中用到的A股数据可在www.yucezhe.com下载，这里可以下载到所有股票、从上市日起的交易数据、财务数据、分钟数据、分笔数据、逐笔数据等。
"""
import pandas as pd
import matplotlib.pyplot as plt

from common import config
from common.Functions import import_index_data

plt.rcParams['font.family'] = ['SimHei']


def automatic_investment_plan(index_code, start_date, end_date):
    """
    :param index_code: 需要定投的指数代码
    :param start_date: 开始定投的日期
    :param end_date: 结束定投的日期
    :return: 返回从定投到现在每天的资金和累计投入的资金
    """
    # 读取指数数据，此处为csv文件的本地地址，请自行修改
    index_data = import_index_data(index_code, columns=['交易日期', '指数代码', '收盘价'])
    index_data.set_index('交易日期', inplace=True)

    index_data = index_data.sort_index()
    index_data = index_data[start_date:end_date]
    index_data['无风险利率'] = (4.0 / 100 + 1) ** (1.0 / 250) - 1  # 假设年化无风险利率是4%(余额宝等理财产品),计算无风险日利率
    index_data['无风险收益_净值'] = (index_data['无风险利率'] + 1).cumprod()

    # 每月第一个交易日定投
    by_month = index_data.resample('M', kind='period').first()

    # 定投购买指数基金
    trade_log = pd.DataFrame(index=by_month.index)
    trade_log['基金净值'] = by_month['收盘价'] / 1000  # 以指数当天收盘点位除以1000作为单位基金净值
    trade_log['money'] = 1000  # 每月月初投入1000元申购该指数基金
    trade_log['基金份额'] = trade_log['money'] / trade_log['基金净值']  # 当月的申购份额
    trade_log['总基金份额'] = trade_log['基金份额'].cumsum()  # 累积申购份额
    trade_log['累计定投资金'] = trade_log['money'].cumsum()  # 累积投入的资金
    # 定投购买余额宝等无风险产品
    trade_log['理财份额'] = trade_log['money'] / by_month['无风险收益_净值']  # 当月的申购份额
    trade_log['总理财份额'] = trade_log['理财份额'].cumsum()  # 累积申购份额

    temp = trade_log.resample('D').ffill()
    index_data = index_data.to_period('D')

    # 计算每个交易日的资产（等于当天的基金份额乘以单位基金净值）
    daily_data = pd.concat([index_data, temp[['总基金份额', '总理财份额', '累计定投资金']]], axis=1, join='inner')
    daily_data['基金定投资金曲线'] = daily_data['收盘价'] / 1000 * daily_data['总基金份额']
    daily_data['理财定投资金曲线'] = daily_data['无风险收益_净值'] * daily_data['总理财份额']

    return daily_data


# 运行程序
index_code = 'sz399006'
df = automatic_investment_plan(index_code, '2008-10-01', '2019-07-31')
print(df[['累计定投资金', '基金定投资金曲线', '理财定投资金曲线']].iloc[[0, -1],])

temp = (df['基金定投资金曲线'] / df['理财定投资金曲线'] - 1).sort_values()
print("最差时基金定投相比于理财定投亏损: %.2f%%，日期为%s" % (temp.iloc[0] * 100, str(temp.index[0])))
print("最好时基金定投相比于理财定投盈利: %.2f%%，日期为%s" % (temp.iloc[-1] * 100, str(temp.index[-1])))

df[['基金定投资金曲线', '理财定投资金曲线']].plot(figsize=(12, 6))
# plt.legend(loc='upper left')
df['收盘价'].plot(secondary_y=True)
plt.legend(['大盘指数'], loc='best')
plt.title(index_code + "大盘指数定投")
plt.savefig(config.output_data_path + index_code + '指数定投验证.png')
plt.show()
