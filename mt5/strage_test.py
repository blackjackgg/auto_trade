# -*- coding: utf-8 -*-
import MetaTrader5 as mt5
from mt5 import setting
from mt5.api import loginmt5
from mt5.strage import BullinTwoSide


def test_gbpusd():
    mymt5 = loginmt5(account=setting.account_name, password=setting.password, server=setting.trader_company)
    BullinTwoSide(mt5=mymt5, symbol="GBPUSD").test_period_profit(mt5.TIMEFRAME_H1)
