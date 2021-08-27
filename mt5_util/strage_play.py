# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
from mt5_util import setting
from mt5_util.api import loginmt5
from mt5_util.strage import BullinTwoSide


def gbpusd():
    num = 200
    mymt5 = loginmt5(account=setting.account_name, password=setting.password, server=setting.trader_company)
    BullinTwoSide(mt5=mymt5, symbol="GBPUSD").test_period_profit(mt5.TIMEFRAME_D1, num=num)
    BullinTwoSide(mt5=mymt5, symbol="GBPUSD", use_stop_loss=True, use_take_profit=True).test_period_profit(
        mt5.TIMEFRAME_D1, num=num)
    BullinTwoSide(mt5=mymt5, symbol="GBPUSD", use_stop_loss=True, ).test_period_profit(
        mt5.TIMEFRAME_D1, num=num)
    BullinTwoSide(mt5=mymt5, symbol="GBPUSD", use_take_profit=True).test_period_profit(
        mt5.TIMEFRAME_D1, num=num)


if __name__ == '__main__':
    gbpusd()
