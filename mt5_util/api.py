# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
from apscheduler.schedulers.blocking import BlockingScheduler


def loginmt5(account, password, server):
    """登录mt5返回实例"""
    # display data on the MetaTrader 5 package
    print("MetaTrader5 package author: ", mt5.__author__)
    print("MetaTrader5 package version: ", mt5.__version__)

    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return None

    # now connect to another trading account specifying the password
    print(account, password, server)
    authorized = mt5.login(account, password=password, server=server)
    if authorized:
        # display trading account data 'as is'
        print(mt5.account_info())
        # display trading account data in the form of a list
        print("Show account_info()._asdict():")
        account_info_dict = mt5.account_info()._asdict()
        print(account_info_dict)
        # for prop in account_info_dict:
        #     print("  {}={}".format(prop, account_info_dict[prop]))
        return mt5
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))
        return None


class BasicMt5:
    """
    mt5基础类
    get_history 获取历史记录
    buy sell fill  三个交易方法
    start 和 trade 方法进行循环自动交易
    """

    def __init__(self, mt5=None, symbol=None, deviation=1000, maxdiancha=1000, lot=1.00, use_stop_loss=False,
                 use_take_profit=False):
        self.mt5 = mt5
        self.symbol = symbol  # 标的外汇
        self.maxdiancha = maxdiancha  # 开仓时点差大小  市价买入需要考虑 点差太大不开仓
        self.lot = lot  # 手数
        self.deviation = deviation  # 开仓时允许的价格波动
        self.use_stop_loss = use_stop_loss  # 是否使用止损
        self.use_take_profit = use_take_profit  # 是否使用止盈


    def get_history(self, period=None, num=3, pos=0):
        # 获取过去的bar从当前开始
        """
        获取历史价格！
        pos为起始位置
        num 从起始位置往前推多少条
        period是计算的周期
        """
        mt5 = self.mt5
        period = period or mt5.TIMEFRAME_M1  # 默认为一分钟
        rates = mt5.copy_rates_from_pos(self.symbol, period, pos, num)  # 从当前到过去num条记录

        newlist = [
            {"开盘": round(i[1], 5), "收盘": round(i[4], 5),
             "差价": round((round(i[4], 5) - (round(i[1], 5))) * 10000, 2),
             "最高价": round(i[2], 5),
             "最低价": round(i[3], 5)}
            for i in rates
        ]
        print("从pos:%s往前%s条过去的记录:%s" % (pos, num, newlist))
        return newlist

    def buy(self):
        """
        市价买入函数，注意计算点差，点差太大不进行交易
        symbol:交易的品种 价格
        lots: 手数 0.01为迷你手
        deviation 买入允许最大价差
        """
        # 根据每个周期进行开仓平仓 统计价格
        mt5 = self.mt5
        symbol = self.symbol
        lot = self.lot
        deviation = self.deviation
        diancha = abs(mt5.symbol_info_tick(symbol).ask - mt5.symbol_info_tick(symbol).bid)
        if diancha < self.maxdiancha:
            """在固定点差范围内才进行买入 每秒钟检查一遍"""
            # point = mt5.symbol_info(symbol).point
            price = mt5.symbol_info_tick(symbol).ask
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": deviation,  # 开单价格波动
                "magic": 234000,  # 标识码
                "comment": "开仓买入！！",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            print(result)
            print("1. 买入订单(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("2. 买入失败, retcode={}".format(result.retcode))
                # request the result as a dictionary and display it element by element
                result_dict = result._asdict()
                print(result_dict)
                if result.comment == 'Requote':
                    self.buy()
                return None

            print("2. 买入成功, ", result)
            return result
        return None

    def sell(self):
        """
        市价卖出函数，注意计算点差，点差太大不进行交易
        symbol:交易的品种 价格
        lots: 手数 0.01为迷你手
        deviation 买入允许最大价差
        """
        # 根据每个周期进行开仓平仓 统计价格
        mt5 = self.mt5
        symbol = self.symbol
        lot = self.lot
        deviation = self.deviation
        diancha = abs(mt5.symbol_info_tick(symbol).ask - mt5.symbol_info_tick(symbol).bid)

        if diancha < self.maxdiancha:

            price = mt5.symbol_info_tick(symbol).bid  # ask卖方的出价 bid买方出价
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                # "sl": price - 100 * point,  # 止损
                # "tp": price + 100 * point,  # 止盈
                "deviation": deviation,  # 开单价格波动
                "magic": 234000,  # 标识码
                "comment": "开仓卖出！！",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # send a trading request
            result = mt5.order_send(request)
            # check the execution result
            print("1. 卖出订单(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print("2. 卖出失败, retcode={}".format(result.retcode))
                # request the result as a dictionary and display it element by element
                result_dict = result._asdict()
                print(result_dict)
                if result.comment == 'Requote':
                    self.sell()
                return None

            print("2. 卖出成功, ", result)
            return result
        return None

    def fill(self, result=None, lot=0.01):  # 这里应该是平掉所有的仓
        """
        平仓函数，注意计算点差，点差太大不进行交易
        symbol:交易的品种 价格
        lots: 手数 0.01为迷你手
        deviation 买入允许最大价差
        """
        # 根据每个周期进行开仓平仓 统计价格
        mt5 = self.mt5
        symbol = self.symbol
        deviation = self.deviation
        diancha = abs(mt5.symbol_info_tick(symbol).ask - mt5.symbol_info_tick(symbol).bid)
        # if diancha < self.maxdiancha:
        if result.request.type == mt5.ORDER_TYPE_BUY:
            deal_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            deal_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask

        position_id = result.order

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": deal_type,
            "position": position_id,
            "price": price,
            "deviation": deviation,
            "magic": 234000,
            "comment": "关闭订单！",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # send a trading request
        result2 = mt5.order_send(request)
        # check the execution result
        print("1. 平仓订单(): by {} {} lots at {} with deviation={} points".format(symbol, lot, price, deviation))
        if result2.retcode != mt5.TRADE_RETCODE_DONE:
            print("2. 平仓订单失败, retcode={}".format(result2.retcode))
            # request the result as a dictionary and display it element by element
            result_dict = result2._asdict()
            print(result_dict)
            self.fill(result, lot)
            return None

        print("2. 平仓订单成功, ", result2)
        return result2

    def trade(self):
        """执行交易操作 每个自动交易的方法改写这个函数"""
        pass

    def start(self):  # 定时器函数
        """开始执行交易循环"""
        scheduler = BlockingScheduler()
        scheduler.add_job(self.trade, 'cron', day_of_week='*', hour='*', minute="*", second=1, )
        scheduler.start()
