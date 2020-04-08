# coding=utf-8
from __future__ import division
import scipy.optimize as sco
from common.indicator import *
from common.Functions import import_index_data
import warnings

plt.rcParams['font.family'] = ['SimHei']

warnings.filterwarnings("ignore")


# 计算投资组合内每只股票的权重
def calculate_weights(pf, type='average_w'):
    """
    :param pf: 投资组合的数据集（索引为日期，每一列是一只股票的日收益率序列）
    :param type: 马科维茨投资组合理论计算最优权重的方法（‘min_var’最小方差，‘max_sharpe’最大化夏普比）,
    不填的话默认为平均赋予权重
    :return: 返回组合内每只股票的权重
    """
    # 计算组合内股票的期望收益率和协方差矩阵
    exp_return = pf.mean()
    cov_matrix = pf.cov() * 250

    # 计算给定权重下的投资组合表现
    def statistics(weights):
        weights = np.array(weights)
        pret = np.sum(exp_return * weights) * 250  # 组合的期望收益
        pvol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))  # 组合的期望波动
        return np.array([pret, pvol, pret / pvol])

    # 投资组合内股票数目
    num = pf.shape[1]

    if type != 'average_w':
        if type == 'min_var':
            # 目标函数为最小化投资组合方差
            def min_func(weights):
                return statistics(weights)[1] ** 2
        else:
            # 目标函数为最大化投资组合夏普比
            def min_func(weights):
                return -statistics(weights)[2]

        # 约束是所有参数(权重)的总和为1
        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        # 参数值(权重)限制在0和1之间
        bnds = tuple((0, 1) for x in range(num))

        # 调用最优化函数，对初始权重使用平均分布
        opt = sco.minimize(min_func, num * [1. / num], method='SLSQP', bounds=bnds, constraints=cons)
        w = opt['x']
    else:
        w = num * [1. / num]

    stock_weights = pd.DataFrame({'指数代码': pf.columns, '权重': w})

    return stock_weights


# 每月月初开始，用之前一段时间（默认为6个月）的历史数据计算出权重，按该权重持有，每月初更新一次权重
def get_portfolio_return(df, window=6, method='average_w'):
    """
    :param df: 原始的股票数据集
    :param window: 用于计算权重的窗口期长度
    :param method: 马科维茨投资组合理论计算最优权重的方法（‘min_var’最小方差，‘max_sharpe’最大化夏普比）,
    不填的话默认为平均赋予权重
    :return: 返回投资组合的收益率序列和资金曲线
    """

    # 重新排列投资组合的数据集（索引为日期，每一列是一个指数的日收益率序列，如果是股票的话停牌当天的收益率设为0）
    pf = df.pivot('交易日期', '指数代码', '涨跌幅').fillna(0)

    # 按月分组，得到每个月月末的日期
    by_month = pf.resample('M').last()

    pf.reset_index(inplace=True)
    by_month.reset_index(inplace=True)

    pf_all_month = pd.DataFrame()

    for i in range(window, len(by_month) - 1):
        end_month = by_month['交易日期'].iloc[i]   # 窗口期最后一个月
        start_month = by_month['交易日期'].iloc[i-window]   # 窗口期第一个月
        pf_temp = pf[(pf['交易日期'] > start_month) & (pf['交易日期'] <= end_month)]  # 用窗口期内的所有数据计算权重
        weights = calculate_weights(pf_temp.iloc[:, 1:], type=method)

        # 取出下个月的数据
        pf_next_month = pf[(pf['交易日期'] > end_month) & (pf['交易日期'] <= by_month['交易日期'].iloc[i + 1])]
        # 计算下个月的组合收益率
        pf_next_month['组合收益率'] = np.dot(np.array(pf_next_month.iloc[:, 1:]), np.array(weights['权重']))
        # 将每个月的组合收益率合并
        pf_all_month = pf_all_month.append(pf_next_month[['交易日期', '组合收益率']], ignore_index=True)

    # 计算投资组合的资金曲线
    pf_all_month['组合资金曲线'] = (pf_all_month['组合收益率'] + 1).cumprod()

    return pf_all_month


# 将沪深300，中小板和创业板指数构成一个投资组合
index_code_list = ['sh000300', 'sz399005', 'sz399006']

all_data = pd.DataFrame()

# 获取指数的数据
for code in index_code_list:
    # 此处为文件存放的本地路径，请自行修改地址
    index_data = import_index_data(code)
    index_data = index_data[['指数代码', '交易日期', '涨跌幅', '收盘价']].sort_values(by='交易日期')
    all_data = all_data.append(index_data, ignore_index=True)
all_data = all_data[all_data['交易日期'] >= '2010-06-01'].reset_index(drop=True)  # 创业板指数10年6月才有

# 调用计算组合收益的函数
portfolio = get_portfolio_return(all_data, method='max_sharpe')

date_line = list(portfolio['交易日期'])  # 日期序列
capital_line = list(portfolio['组合资金曲线'])  # 组合的资产序列
return_line = list(portfolio['组合收益率'])  # 组合收益率序列
print('\n=====================投资组合的各项指标==========================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("平均波动率: %.2f" % volatility(date_line, return_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

index_change = all_data.pivot('交易日期', '指数代码', '涨跌幅').fillna(0)
index_change.reset_index(inplace=True)
index_change = index_change[index_change['交易日期'].isin(date_line)].reset_index(drop=True)

index_close = all_data.pivot('交易日期', '指数代码', '收盘价').fillna(method='ffill')
index_close.reset_index(inplace=True)
index_close = index_close[index_close['交易日期'].isin(date_line)].reset_index(drop=True)

# =======计算沪深300指数的回测指标
capital_line = list(index_close['sh000300'])  # 指数序列
return_line = list(index_change['sh000300'])  # 指数收益率序列
print('\n====================沪深300指数的各项指标=========================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("平均波动率: %.2f" % volatility(date_line, return_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

# =======计算中小板指数的回测指标
capital_line = list(index_close['sz399005'])  # 指数序列
return_line = list(index_change['sz399005'])  # 指数收益率序列
print('\n====================中小板指数的各项指标==========================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("平均波动率: %.2f" % volatility(date_line, return_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

# =======计算创业板指数的回测指标
capital_line = list(index_close['sz399006'])  # 指数序列
return_line = list(index_change['sz399006'])  # 指数收益率序列
print('\n====================创业板指数的各项指标==========================')
print("平均年化收益: %.2f" % annual_return(date_line, capital_line))
print("最大回撤: %.2f, 开始时间: %s, 结束时间: %s" % max_drawdown(date_line, capital_line))
print("平均波动率: %.2f" % volatility(date_line, return_line))
print("夏普比例: %.2f" % sharpe_ratio(date_line, capital_line, return_line))

# 计算组合和各指数的累计收益率
portfolio['马克维茨组合'] = portfolio['组合资金曲线'] / portfolio.iloc[0]['组合资金曲线'] - 1
index_close['沪深300'] = index_close['sh000300'] / index_close.iloc[0]['sh000300'] - 1
index_close['中小板'] = index_close['sz399005'] / index_close.iloc[0]['sz399005'] - 1
index_close['创业板'] = index_close['sz399006'] / index_close.iloc[0]['sz399006'] - 1

df = pd.concat([portfolio[['交易日期', '马克维茨组合']], index_close['沪深300'], index_close['中小板'], index_close['创业板']], axis=1)
df.set_index('交易日期', inplace=True)
# 画出累计收益率的折线图
df.plot(figsize=(14, 7))
plt.legend(list(df.columns), loc='best')
plt.title('累计收益曲线')
plt.savefig(config.output_data_path+'马克维茨投资组合验证.png')
plt.show()

