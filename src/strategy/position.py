# coding: utf-8
from context.context import BackContext


class Position(object):

    def __init__(self, stock_code):
        self.stock_code = stock_code

        # key为买入时间, value为剩余股数
        self.buy_map = {}

    # 平仓
    def close_out(self, trade_date):
        """
        :param trade_date: 非trade_date当天买入的股票全部平仓, 当天买入受T+1交易限制无法卖出
        :return:
        """

        sort_date = sorted(list(self.buy_map.keys()))
        sell_quantity = 0
        for buy_date in sort_date:
            # T+1交易必须至少过一天才能卖出
            if (trade_date - buy_date).days <= 0:
                continue
            sell_quantity = sell_quantity + self.buy_map[buy_date]
            del self.buy_map[buy_date]
        return sell_quantity

    def sell(self, trade_date, quantity):
        """
        :param trade_date: 交易日期
        :param quantity: 需要卖出的股票数量
        :return: 由于T+1交易日的限制, 无法当天买、当天卖, 所以有些股票无法卖出, 这里返回的是成功卖出的股票数量
        """
        sort_date = sorted(list(self.buy_map.keys()))
        need_sell_quantity = quantity
        for buy_date in sort_date:
            # T+1交易必须至少过一天才能卖出
            if (trade_date - buy_date).days <= 0:
                continue

            if self.buy_map[buy_date] <= need_sell_quantity:
                need_sell_quantity = need_sell_quantity - self.buy_map[buy_date]
                # buy_date这一天买入的股票已全部卖出
                del self.buy_map[buy_date]
            else:
                self.buy_map[buy_date] = self.buy_map[buy_date] - need_sell_quantity
                need_sell_quantity = 0

            if need_sell_quantity == 0:
                break

        return quantity - need_sell_quantity

    # 买入
    def buy(self, trade_date, quantity):
        if trade_date in self.buy_map.keys():
            old = self.buy_map[trade_date]
            self.buy_map[trade_date] = old + quantity
        else:
            self.buy_map[trade_date] = quantity

    def get_quantity(self):
        res = 0
        for quantity in self.buy_map.values():
            res = res + quantity
        return res


if __name__ == '__main__':

    context = BackContext("2020-01-04", "2020-03-01", print_progress=True)
    pos = Position("test")

    idx = 0
    for date in context.trade_dates:
        pos.buy(date, 1)
        pos.buy(date, 2)

        for k, v in pos.buy_map.items():
            print("date: {}, quantity: {}".format(k, v))
        idx = idx + 1
        if idx % 2 == 0:
            pos.close_out(date)
            for k, v in pos.buy_map.items():
                print("date: {}, quantity: {}".format(k, v))
