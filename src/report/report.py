# coding: utf-8
import os

from common.Functions import import_index_data
from common.config import back_report_path
from tool.indicator import *
from tool.plot import *
from context.context import BackContext
import pandas as pd

"""
一个回验策略最好单独使用一个Report对象, Report对象里的context的回验参数需要对齐, 即回测参数列表必须是一致的,
比如有一个context有布林通道Dev和调仓周期两个参数, 那么其他context也都必须有且仅有这两个参数, 否则会报错
"""


class BackReport(object):

    def __init__(self, root_path=None):
        """
        :param start_date: 字符串类型, 2019-01-01
        :param end_date: 字符串类型, 2019-01-02
        :param strategy_name:
        :param param_names:
        :param root_path:
        """

        if root_path is None or root_path == "":
            self.root_path = back_report_path
        else:
            self.root_path

        self.ctx_list = []
        self.strategy_name = None

        # 将传递进来的参数去重
        self.param_names = []
        self.start_date = None
        self.end_date = None

    def check(self, context):

        if not isinstance(context, BackContext):
            raise Exception("invalid back context")

        if context.strategy_name is None or context.strategy_name == "":
            raise Exception("strategy name is empty")

        param_names = []
        if context.params is not None or len(context.params) > 0:
            param_names = list(set(context.params.keys()))

        if len(self.ctx_list) <= 0:
            self.strategy_name = context.strategy_name
            self.start_date = context.start_date
            self.end_date = context.end_date
            self.param_names = param_names
        else:
            if context.strategy_name != self.strategy_name:
                raise Exception(
                    "only allow append %s context, but provider %s" % (self.strategy_name, context.strategy_name))

            if context.start_date != self.start_date or context.end_date != context.end_date:
                raise Exception("invalid start_date or end_date")

            if len(set(self.param_names) - set(param_names)) > 0 or len(set(param_names) - set(self.param_names)) > 0:
                raise Exception("invalid params name: %s" % (",".join(list(param_names))))

    def append_ctx(self, context):
        self.check(context)
        self.ctx_list.append(context)

    def save(self, mode='a', show=True):
        """
        :param overwrite: 如果存在同名的报告, 是否要覆盖原来的报告, True: 覆盖, False: 抛异常
        :param plot: 是否要画回撤紫金曲线
        :return:
        """

        start_str = str(self.start_date).replace("-", "")
        end_str = str(self.end_date).replace("-", "")

        date_range = start_str + "_" + end_str

        report_dir = os.path.join(self.root_path, self.strategy_name, date_range)
        os.makedirs(report_dir, exist_ok=True)

        # 持仓记录
        hold_pos_df_list = []

        # 交易记录
        trade_record_df_list = []

        # 紫金曲线
        capital_line_list = []

        # 风险指标
        risk_indicator_df = pd.DataFrame()

        for ctx in self.ctx_list:
            if not isinstance(ctx, BackContext):
                continue

            # TODO 需要确认一下, 这里是否是取的闭区间的数据
            benchmark_df = import_index_data(ctx.benchmark, ['交易日期', '涨跌幅', '收盘价'])
            benchmark_df = benchmark_df[(benchmark_df['交易日期'] >= ctx.start_date) &
                                        (benchmark_df['交易日期'] <= ctx.end_date)]
            benchmark_df.set_index('交易日期', inplace=True)

            back_capital_df = pd.DataFrame(data={
                '策略总资产': ctx.his_account['总资产'],
                '策略涨跌幅': ctx.his_account['涨跌幅'],
                '策略累计收益率': (ctx.his_account['涨跌幅'] + 1).cumprod(),
                '策略仓位比例': ctx.his_account['仓位比例'],
                '基准总资产': benchmark_df['收盘价'],
                '基准涨跌幅': benchmark_df['涨跌幅'],
                '基准累计收益率': (benchmark_df['涨跌幅'] + 1).cumprod()
            })

            max_drawdown_rate, max_drawdown_start, max_drawdown_end = max_drawdown(back_capital_df)
            max_up, max_down = max_successive_up(back_capital_df)

            indicator_map = {
                "回测开始时间": ctx.start_date,
                "回测结束时间": ctx.end_date,
                "策略总收益": (back_capital_df['策略涨跌幅'] + 1).prod(),
                "基准总收益": (back_capital_df['基准涨跌幅'] + 1).prod(),
                "策略平均年化收益": annual_return(back_capital_df),
                "阿尔法": alpha(back_capital_df),
                "贝塔": beta(back_capital_df),
                "夏普比率": sharpe_ratio(back_capital_df),
                "信息比率": info_ratio(back_capital_df),
                "最大回撤": max_drawdown_rate,
                "最大回撤开始时间": max_drawdown_start,
                "最大回测结束时间": max_drawdown_end,
                "连续最大盈利天数": max_up,
                "连续最大亏损天数": max_down,
                "月度胜率": period_win_rate(back_capital_df),
            }

            for k, v in ctx.params.items():
                ctx.his_position[k] = v
                ctx.his_trade_records[k] = v
                back_capital_df[k] = v
                indicator_map[k] = v

            year_rtn_name = '年度收益'
            for k, v in ctx.params.items():
                year_rtn_name = "{}_{}={}".format(year_rtn_name, k, v)
            plot_year_return(back_capital_df, save_path=report_dir, title=year_rtn_name, show=show)

            back_line_name = '回测曲线'
            for k, v in ctx.params.items():
                back_line_name = "{}_{}={}".format(back_line_name, k, v)
            plot_back_line(back_capital_df, save_path=report_dir, title=back_line_name, show=show)

            hold_pos_df_list.append(ctx.his_position)
            trade_record_df_list.append(ctx.his_trade_records)
            capital_line_list.append(back_capital_df)
            risk_indicator_df = risk_indicator_df.append(indicator_map, ignore_index=True)

        # TODO: 参数调优曲线,



        pd.concat(hold_pos_df_list).to_csv(os.path.join(report_dir, '持仓记录.csv'), mode=mode, float_format='%.4f')
        pd.concat(trade_record_df_list).to_csv(os.path.join(report_dir, '交易记录.csv'), mode=mode, float_format='%.4f')
        pd.concat(capital_line_list).to_csv(os.path.join(report_dir, '回测资金曲线.csv'), mode=mode, float_format='%.4f')
        risk_indicator_df.to_csv(os.path.join(report_dir, '回测风险指标.csv'), mode=mode, float_format='%.4f', index=None)
