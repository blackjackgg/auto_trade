"""策略类"""
import datetime
import random
from pprint import pprint
import matplotlib as mpl
from mt5_util.api import mean

import plot

mpl.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei', 'FangSong']  # 汉字字体,优先使用楷体，如果找不到楷体，则使用黑体
mpl.rcParams['font.size'] = 12  # 字体大小
mpl.rcParams['axes.unicode_minus'] = False  # 正常显示负号

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from apscheduler.schedulers.background import BackgroundScheduler

from mt5_util.api import BasicMt5


def is_in_range(number, range_list):
    """rangelist"""
    return range_list[0] <= number <= range_list[1]


class BullinUtil():
    def sma(self, c, N=20, title="sma"):
        """
            传进来的c应该是一个多行多列的列表
            计算简单移动平均线 c传入一个数据列表
            返回布林带必备的几个参数 同时绘制曲线
        """
        """https://blog.csdn.net/u011702002/article/details/78242400"""
        weights = np.ones(N) / N

        # 卷积实现移动平均
        sma = np.convolve(weights, c)[N - 1:-N + 1]

        deviation = []

        lenc = len(c)
        for i in range(N - 1, lenc):
            dev = c[i - N + 1:i + 1]
            deviation.append(np.std(dev))

        # 两倍标准差

        deviation2 = 2 * np.array(deviation)
        deviation1 = np.array(deviation)
        # 压力线
        upperBB2 = sma + deviation2
        upperBB1 = sma + deviation1
        # 支撑线
        lowerBB2 = sma - deviation2
        lowerBB1 = sma - deviation1

        c_slice = c[N - 1:]

        pprint(c_slice)
        pprint(upperBB2)
        # plt.plot(c_slice, 'y', label="实际价格")
        # plt.plot(upperBB2, 'r', label="2SD")
        # plt.plot(upperBB1, 'r--', label="1SD")
        # plt.plot(sma, 'b--', label="平均值")
        # plt.plot(lowerBB1, 'g--', label="-1SD")
        # plt.plot(lowerBB2, 'g', label="-2SD")
        # plt.title(title)
        # plt.legend()
        # plt.show()

        return {"sma": sma, "2sd": upperBB2, "1sd": upperBB1, "-2sd": lowerBB2, "-1sd": lowerBB1, "dataset": c}

    def get_price_status(self, c):
        """获取当前价格状态 是位于布林带的哪个区间"""

        res = self.sma(c)
        last_point = res['dataset'][-1]

        center_down_range = [res["-1sd"][-1], res["sma"][-1]]  # 中间三无地带
        center_up_range = [res["sma"][-1], res["1sd"][-1]]  # 中间三无地带

        # print("center", center_up_range, center_down_range)
        buy_range = [res["1sd"][-1], res["2sd"][-1]]  # 上带
        sell_range = [res["-2sd"][-1], res["-1sd"][-1]]  # 下带

        # print("buy_sell", center_up_range, center_down_range)

        def get_pos(point):
            center_up = is_in_range(point, center_up_range) and "center_up"
            center_down = is_in_range(point, center_down_range) and "center_down"
            buy = is_in_range(point, buy_range) and "buy"
            sell = is_in_range(point, sell_range) and "sell"
            pos = center_up or center_down or buy or sell
            return pos

        last_2_point = res['dataset'][-2]
        pre_pos = get_pos(last_2_point)
        current_pos = get_pos(last_point)
        print("current_pos", current_pos, pre_pos)
        return {"current_pos": current_pos, "pre_pos": pre_pos, **res}


class BullinTwoSideSimple(BasicMt5):
    """
    布林带1-2sd交易策略 以为以前一个收盘价作为预测点  下一个价格的收盘开盘差价作为盈利亏损计算
    """

    def test_period_profit(self, period=None, num=100):
        """某个周期盈利能力测试  默认测试100条数据  生产盈利曲线！"""
        his = self.get_history(num=num, period=period)
        yingli = []  # 盈利
        leiji = []
        close = []
        for index, i in enumerate(his):
            if index > 22 and i != his[-1]:
                rawlist = his[index - 22:index]
                direct = self.predict_trend(rawlist)
                close.append(i["收盘"])

                if direct == "buy":
                    profit = his[index + 1]["差价"] >= 0 and 1 or -1
                    yingli.append(his[index + 1]["差价"] * profit)
                    leiji.append(yingli[-1] + (leiji and leiji[-1] or 0))
                elif direct == "sell":
                    profit = his[index + 1]["差价"] <= 0 and 1 or -1
                    yingli.append(his[index + 1]["差价"] * profit)
                    leiji.append(yingli[-1] + (leiji and leiji[-1] or 0))
                else:
                    yingli.append(0)
                    leiji.append(yingli[-1] + (leiji and leiji[-1] or 0))

        datadict = {'yingli': yingli,
                    "leiji": leiji,
                    "close": close,
                    }

        # 绘图
        plot.plot_line(datadict)

    def predict_trend(self, rawlist):
        """
        根据预设的方法来猜测趋势
        在这里返回购买的方向
        """
        rawlist = [i["收盘"] for i in rawlist]
        print("rawlist", rawlist)
        if "buy" == BullinUtil().get_price_status(rawlist)["current_pos"]:
            return "buy"
        elif "sell" == BullinUtil().get_price_status(rawlist)["current_pos"]:
            return "sell"
        return None


class BullinTwoSide(BasicMt5):
    """
    布林带1-2s交易策略 带止损止盈
    以第二个sd为标准 超过2个sd

    实现了一套完整的方法
    只需要专注于
    def stop_loss
    def take_profit
    def predict_trend
    三个函数的写作即可！
    """

    def test_period_profit(self, period=None, num=100, title="布林带两端交易收益曲线"):
        """某个周期盈利能力测试  默认测试100条数据  生产盈利曲线！"""
        his = self.get_history(num=num, period=period)
        profit = []  # 盈利
        total_profit = []
        close = []
        for index, i in enumerate(his):
            if index > 22 and i != his[-1]:
                close.append(i["收盘"])
                profit = self.update_profit(his, index, profit)
                total_profit.append(profit[-1] + (total_profit and total_profit[-1] or 0))

        datadict = {'profit': profit,
                    "total_profit": total_profit,
                    "close": close,
                    }
        tail1 = self.use_take_profit and "使用止盈" or ""
        tail2 = self.use_stop_loss and "使用止损" or ""

        tail = (tail1 + tail2) or "不使用止损止盈"

        plot.plot_line(datadict, title="%s:%s天-%s \n 交易次数：%s, 盈利：%s次，亏损%s次，胜率%s \n 总收益：%s,最大亏损：%.2f,最大盈利:%.2f " % (title, num, tail,self.trade_times,self.win_times,self.lose_times,round(self.win_times/self.trade_times,2),round(total_profit[-1],2),min(profit),max(profit)))
        # plot.plot_line({"close": close})


    def update_profit(self, his, index, profit):
        """计算单次投入的盈利 通过某段时间的20天sma值来计算"""
        rawlist = his[index - 22:index]
        res = self.predict_trend(rawlist)
        print("updateprofit", res)
        if res:
            self.trade_times += 1
            direct2 = res["direct"] == "buy"
            print("Seconddirect", direct2)
            win_money = self.get_win_money(his, index, direct2)
            profit.append(win_money * 1000)
        else:
            profit.append(0)
        return profit

    def get_win_money(self, his, index, direct):
        """通过比较止损 止盈 和收盘价来判断 某次进场出场的收益"""
        in_point = his[index]["收盘"]
        out_point = self.get_out_point(his, index, direct)
        win_money = (out_point - in_point) * (direct and 1 or -1)
        if win_money > 0:
            self.win_times += 1
        else:
            self.lose_times += 1
        return win_money

    def get_out_point(self, his, index, direct):
        """计算出场点  存在可能不设置止损的情况 增加可选性 进行对比"""
        stop_loss = self.stop_loss(his, index, direct)
        take_profit = self.take_profit(his, index, direct)

        next_day_close = his[index + 1]["收盘"]
        next_day_min = his[index + 1]["最低价"]
        next_day_max = his[index + 1]["最高价"]

        print("getoutdirect", direct)
        if direct:
            print("buyin")
            if stop_loss and next_day_min <= stop_loss:
                out_point = stop_loss
            elif take_profit and next_day_max >= take_profit:
                out_point = take_profit
            else:
                out_point = next_day_close

        else:  # 卖空的情况
            print("Sellout")
            if stop_loss and next_day_max >= stop_loss:
                out_point = stop_loss
            elif take_profit and next_day_min <= take_profit:
                out_point = take_profit
            else:
                out_point = next_day_close

        return out_point

    def stop_loss(self, his, index, direct):
        """止损点"""
        rawlist = his[index - 22:index]
        rawlist = [i["收盘"] for i in rawlist]
        print("rawlist", rawlist)
        res = BullinUtil().get_price_status(rawlist)
        sl_point = res["sma"][-1]
        return self.use_stop_loss and sl_point or 0

    def take_profit(self, his, index, direct):
        """止盈出场点"""
        rawlist = his[index - 22:index]
        rawlist = [i["收盘"] for i in rawlist]
        print("rawlist", rawlist)
        res = BullinUtil().get_price_status(rawlist)

        tp_point = direct and res["2sd"][-1] or res["-2sd"][-1]
        return self.use_take_profit and tp_point or 0

    def predict_trend(self, rawlist):
        """
        根据预设的方法来猜测趋势
        在这里返回购买的方向
        """
        rawlist = [i["收盘"] for i in rawlist]
        print("rawlist", rawlist)
        res = BullinUtil().get_price_status(rawlist)
        if "buy" == res["current_pos"]:
            # return {"direct": "buy"}
            sd2 = float(res["2sd"][-1])
            sd1 = float(res["1sd"][-1])
            if rawlist[-1] >= (2 / 3 * mean(sd2, sd1)):
                return {"direct": "sell"}
            elif rawlist[-1] <= (1 / 3 * mean(sd2, sd1)):
                return {"direct": "buy"}
            # 还要判断是否是靠近2sd的边缘  如果靠近上缘卖出 靠近下缘买进
            return None
        elif "sell" == res["current_pos"]:
            # return {"direct": "sell"}
            sd2 = float(res["-2sd"][-1])
            sd1 = float(res["-1sd"][-1])
            if rawlist[-1] >= (2 / 3 * mean(sd2, sd1)):
                return {"direct": "sell"}
            elif rawlist[-1] <= (1 / 3 * mean(sd2, sd1)):
                return {"direct": "buy"}
            return None
        return None


if __name__ == '__main__':
    c = [random.randint(0, 10000) for i in range(50)]
    BullinUtil().get_price_status(c)
