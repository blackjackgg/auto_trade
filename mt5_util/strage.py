"""策略类"""
import datetime
import random
from pprint import pprint
import matplotlib as mpl

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

        print("center", center_up_range, center_down_range)
        buy_range = [res["1sd"][-1], res["2sd"][-1]]  # 上带
        sell_range = [res["-2sd"][-1], res["-1sd"][-1]]  # 下带
        print("buy_sell", center_up_range, center_down_range)

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
        print(current_pos, pre_pos)
        return {"current_pos": current_pos, "pre_pos": pre_pos}


class BullinTwoSide(BasicMt5):
    """
    布林带1-2s交易策略
    """

    def follow_trend(self):
        """跟随趋势玩法"""
        pass

    def reverse_trend(self):
        """逆向趋势玩法"""
        pass

    def get_current_open(self):
        """获取当前的风险敞口 是买入还是卖出  返回当前持有头寸 """
        pass

    def get_lose_info(self):
        """获取失败信息  绘制亏损曲线图 打印最大亏损和总计亏损"""
        pass

    def get_win_info(self):
        """获取盈利信息  绘制盈利曲线图 打印最大盈利和总计盈利"""
        pass

    def test_period_profit(self, period=None, num=100):
        """某个周期盈利能力测试  默认测试100条数据  生产盈利曲线！"""
        his = self.get_history(num=num, period=period)
        yingli = []  # 盈利
        leiji = []
        for index, i in enumerate(his):
            if index > 22 and i != his[-1]:
                rawlist = his[index - 22 :index]
                direct = self.predict_trend(rawlist)

                if direct == "buy":
                    profit = his[index+1]["差价"] >= 0 and 1 or -1
                    yingli.append(his[index+1]["差价"] * profit)
                    leiji.append(sum(yingli))
                if direct == "sell":
                    profit = his[index + 1]["差价"] <= 0 and 1 or -1
                    yingli.append(his[index + 1]["差价"] * profit)
                    leiji.append(sum(yingli))
                else:
                    yingli.append(0)
                    leiji.append(sum(yingli))

        print("yingli",yingli)
        # 柱状图
        # df = pd.DataFrame(
        #     {'yingli': yingli,  "leiji": leiji, "x": range(num)},
        #     columns=['zero', 'yingli'])

        df2 = pd.DataFrame({'yingli': yingli,
                             "leiji": leiji,
                            "x": range(num),
                            },
                           columns=['leiji', 'yingli'])

        # df.plot(kind='bar')  ## 默认是折线图   这是盈利曲线 area  bar
        df2.plot()
        plt.show()

    def predict_trend(self, rawlist):
        """ 根据预设的方法来猜测趋势 """
        rawlist = [ i["收盘"] for i in rawlist]
        print("rawlist",rawlist)
        if "buy"  == BullinUtil().get_price_status(rawlist)["current_pos"]:
            return "buy"
        if "sell"  == BullinUtil().get_price_status(rawlist)["current_pos"]:
            return  "sell"
        return  None


if __name__ == '__main__':
    c = [random.randint(0, 10000) for i in range(50)]
    BullinUtil().get_price_status(c)
