"""
邢不行量化小讲堂系列文章配套代码
文章标题：用Python验证A股名言：跳空必回补...吗？【附代码】
文章链接：https://mp.weixin.qq.com/s/beg4CkybuOHo6a1YFOS5PA
作者：邢不行
微信号：xingbuxing0807
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from common import config

# 设置字体, 图片中可以显示中文
plt.rcParams['font.family'] = ['SimHei']

pd.set_option('expand_frame_repr', False)
# pd.set_option('max_colwidth', 10)


# ===寻找跳空和回补，并记录
df = pd.read_csv(config.index_data_path + 'sh000001.csv').sort_values(by=['date'], ascending=True)
df = df.reset_index(inplace=True)

# 向上跳空 最低价高于前一日最高价
condition_up = df['low'] > df['high'].shift()

# 向下跳空 最高价低于前一日最低价
condition_down = df['high'] < df['low'].shift()

df['hop'] = np.nan
df.loc[condition_up, 'hop_signal_short'] = -1
df.loc[condition_down, 'hop_signal_long'] = 1

hop_record = []
# 向上跳空，看是否有回落（之后的最低价有没有低于缺口前价格）
# 向下跳空，看是否有回升（之后的最高价有没有高于缺口前价格）
for i in range(len(df)):
    # 如果有向上跳空
    if df['hop_signal_short'].at[i] == -1:

        hop_date = df['date'].at[i]
        ex_hop_price = df['high'].at[i - 1]
        post_hop_price = df['low'].at[i]

        # 计算跳空幅度
        hop_rate = abs(post_hop_price - ex_hop_price) / ex_hop_price

        fill_date = ''
        fill_days = 100000000
        # 看之后有没有回补向上的跳空
        for j in range(i, len(df)):
            if df['low'].at[j] <= ex_hop_price:
                fill_date = df['date'].at[j]
                break
        if fill_date != '':
            fill_days = (datetime.strptime(fill_date, '%Y-%m-%d') - datetime.strptime(hop_date, '%Y-%m-%d')).days
        hop_record.append({'hop': 'up',
                           'hop_date': hop_date,
                           'hop_rate': hop_rate,
                           'ex_hop_price': ex_hop_price,
                           'post_hop_price': post_hop_price,
                           'fill_date': fill_date,
                           'fill_days': fill_days
                           })
    # 如果有向下跳空
    elif df['hop_signal_long'].at[i] == 1:
        hop_date = df['date'].at[i]
        ex_hop_price = df['low'].at[i - 1]
        post_hop_price = df['high'].at[i]

        hop_rate = abs(ex_hop_price - post_hop_price) / ex_hop_price

        fill_date = ''
        fill_days = 100000000
        # 看之后有没有回补向下的跳空
        for j in range(i, len(df)):
            if df['high'].at[j] >= ex_hop_price:
                fill_date = df['date'].at[j]
                break
        if fill_date != '':
            fill_days = (datetime.strptime(fill_date, '%Y-%m-%d') - datetime.strptime(hop_date, '%Y-%m-%d')).days
        hop_record.append({'hop': 'down',
                           'hop_date': hop_date,
                           'hop_rate': hop_rate,
                           'ex_hop_price': ex_hop_price,
                           'post_hop_price': post_hop_price,
                           'fill_date': fill_date,
                           'fill_days': fill_days
                           })

# 每0.5%一个台阶
rate_limit = [0.005 * i for i in range(5)]
filter_fill_days = 200

plot_cnt = len(rate_limit)

plt.subplots(plot_cnt, 2, figsize=(12, 20))
for idx in range(plot_cnt):
    hop_df = pd.DataFrame(hop_record)

    lower_limit = rate_limit[idx]
    hop_df = hop_df[hop_df['hop_rate'] >= lower_limit]

    # 计算全部跳空回补占总跳空的比例
    total_hop = len(hop_df)
    total_fill_cnt = len(hop_df[hop_df["fill_date"] != ''])
    total_fill_rate = 1.0 * total_fill_cnt / total_hop

    all_fill_days_statistic = hop_df[hop_df['fill_days'] <= filter_fill_days]['fill_days'].value_counts(
        sort=True).sort_index().cumsum()
    all_fill_days_statistic = all_fill_days_statistic / hop_df.shape[0]

    # 计算全部跳空回补比例
    # print("总共跳空次数: {}, 回补次数: {}, 回补比例: {}%".format(total_hop, total_fill_cnt, 100 * total_fill_rate))

    # 计算向上跳空回补占总向上跳空的比例
    up_hop_df = hop_df[hop_df['hop'] == "up"]
    total_up_hop = len(up_hop_df)
    total_up_fill_cnt = len(up_hop_df[up_hop_df["fill_date"] != ''])
    total_up_fill_rate = 1.0 * total_up_fill_cnt / total_up_hop
    print("向上跳空次数: {}, 回补次数: {}, 回补比例: {}%".format(total_up_hop, total_up_fill_cnt, 100 * total_up_fill_rate))

    # 计算回补天数小于filter_fill_days, 统计回补天数为n天的次数, 按回补天数排序, 然后求累计和
    up_fill_days_statistic = up_hop_df[up_hop_df['fill_days'] <= filter_fill_days]['fill_days'].value_counts(
        sort=True).sort_index().cumsum()
    up_fill_days_statistic = up_fill_days_statistic / up_hop_df.shape[0]

    # 计算向下跳空回补占总向下跳空的比例
    down_hop_df = hop_df[hop_df['hop'] == "down"]
    total_down_hop = len(down_hop_df)
    total_down_fill_cnt = len(down_hop_df[down_hop_df["fill_date"] != ''])
    total_down_fill_rate = 1.0 * total_down_fill_cnt / total_down_hop
    print("向下跳空次数: {}, 回补次数: {}, 回补比例: {}%".format(total_down_hop, total_down_fill_cnt, 100 * total_down_fill_rate))

    down_fill_days_statistic = down_hop_df[down_hop_df['fill_days'] <= filter_fill_days]['fill_days'].value_counts(
        sort=True).sort_index().cumsum()
    down_fill_days_statistic = down_fill_days_statistic / down_hop_df.shape[0]

    fill_list = [total_fill_cnt, total_up_fill_cnt, total_down_fill_cnt]
    hop_list = [total_hop, total_up_hop, total_down_hop]
    fill_rate_list = [total_fill_rate, total_up_fill_rate, total_down_fill_rate]

    label_list = [u"全部跳空", "向上跳空", "向下跳空"]

    x_pos = [0.4, 1.4, 2.4]
    width = 0.4

    plt.subplot(plot_cnt, 3, 3 * idx + 1)
    hop_bar = plt.bar(x_pos, hop_list, width=width, color="#D2B48C", label="跳空次数")
    fill_bar = plt.bar([x + width for x in x_pos], fill_list, width=width, color="#FFDEAD", label="回补次数")

    plt.title(u"跳空回补次数统计(跳空幅度>%.2f%%)" % (100.0 * lower_limit))
    plt.xlabel(u"次数")
    plt.xticks([x + width / 2 for x in x_pos], label_list)
    plt.legend()

    for b in hop_bar + fill_bar:
        plt.text(b.get_x() + width / 2, b.get_height(), str(b.get_height()), ha='center', va='bottom')

    plt.subplot(plot_cnt, 3, 3 * idx + 2)
    rate_bar = plt.bar(x_pos, fill_rate_list, width=width, color="#D2B48C")

    plt.title(u"跳空回补比例(跳空幅度>%.2f%%)" % (100.0 * lower_limit))
    plt.xlabel(u"回补百分比")
    plt.xticks(x_pos, label_list)
    for b in rate_bar:
        plt.text(b.get_x() + width / 2, b.get_height(), "%.2f%%" % b.get_height(), ha='center', va='bottom')

    plt.subplot(plot_cnt, 3, 3 * idx + 3)
    plt.plot(all_fill_days_statistic.index, all_fill_days_statistic.values, label="全部跳空")
    plt.plot(up_fill_days_statistic.index, up_fill_days_statistic.values, label="向上跳空")
    plt.plot(down_fill_days_statistic.index, down_fill_days_statistic.values, label="向下跳空")

    plt.title(u"回补天数比例累积和(跳空幅度>%.2f%%)" % (100.0 * lower_limit))
    plt.xlabel(u"回补天数小于x填")
    plt.ylabel(u"回补/跳空次数")

    plt.xticks(np.arange(0, filter_fill_days, 20))
    plt.yticks(np.arange(0, 1, 0.1))
    plt.grid(True, ls='--')
    plt.legend()

plt.show()
