"""策略类"""
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from apscheduler.schedulers.background import BackgroundScheduler

from mt5.api import BasicMt5


class BullinTwoSide(BasicMt5):
    """
    布林带1-2s交易策略
    """

    def get_current_open(self):
        """获取当前的风险敞口 是买入还是卖出 """
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
        tmplist = {}
        yingli = []  # 盈利
        kuisun = []  # 亏损
        chajia = []  # 使用累计算法  反向后重新计数
        tmpup = 0

        leiji = []
        predict_tmp = 0
        predict_res = []  ## 预测收益值得集合
        for index, i in enumerate(his):
            if index > 5:
                if i["差价"] >= 0:
                    maxchajia = i['收盘'] - i['开盘']
                    maxchajia = round(maxchajia * 1000, 5)
                    yingli.append(maxchajia)
                    chajia.append(maxchajia)
                    tmpup += maxchajia

                    rawlist = his[index - 5:index]
                    direct = self.predict_trend(rawlist)
                    if direct and direct.get("direct"):
                        predict_tmp += maxchajia
                    elif direct and not direct.get("direct"):
                        predict_tmp -= maxchajia
                    leiji.append(tmpup)
                    predict_res.append(predict_tmp)
                    # 添加累计数

                if i["差价"] < 0:
                    maxchajia = i['收盘'] - i['开盘']
                    maxchajia = round(maxchajia * 1000, 5)
                    print(maxchajia)
                    yingli.append(maxchajia)

                    chajia.append(maxchajia)

                    tmpup += maxchajia

                    rawlist = his[index - 5:index]
                    direct = self.predict_trend(rawlist)
                    if direct and direct.get("direct"):
                        predict_tmp += maxchajia
                    elif direct and not direct.get("direct"):
                        predict_tmp -= maxchajia
                    leiji.append(tmpup)  # 旧的累计曲线
                    predict_res.append(predict_tmp)

        tmplist["可盈利"] = yingli
        tmplist["亏损"] = kuisun

        print(tmplist, len(yingli), len(kuisun), "盈利次数:%s" % (len(yingli) - len(kuisun)))

        print({"最大盈利": np.max(yingli), "最大亏损": np.max(kuisun), "mean": np.mean(yingli)})

        print(chajia)
        print({"正买曲线": yingli, "结果": sum(yingli)})
        ## 一小时的盈利均值 在1.4左右  最大值达到5.97  超过3为小概率事件了    最小盈利都有0.23

        # 柱状图
        df = pd.DataFrame({'yingli': yingli, "maxchajia": chajia, "zero": [0] * num, "leiji": leiji, "x": range(num)},
                          columns=['zero', 'yingli'])

        df2 = pd.DataFrame({'yingli': yingli, "maxchajia": chajia,
                            "zero": [0] * num, "leiji": leiji,
                            "x": range(num), "predict": predict_res
                            },
                           columns=['zero', 'leiji', 'predict'])

        df.plot(kind='bar')  ## 默认是折线图   这是盈利曲线 area  bar
        df2.plot()
        plt.show()


    def predict_trend(self, rawlist):
        """ 根据预设的方法来猜测趋势 """
        nega = 0
        posi = 0
        for i in rawlist:
            if i > 0:
                posi += 1
            if i < 0:
                nega += 1
        total = sum(rawlist)

        ## 出现峰值得情况  波动很剧烈 价格上下波动 最终偏向大幅上升 # 这种情况价格会出现反转
        if posi - nega < 2 and total > 3:
            return {"direct": False}

        elif nega - posi < 2 and total < -3:
            return {"direct": True}

        ### 其他情况 单方面突进  价格跟随即可

        elif nega - posi >= 2:
            return {"direct": False}

        elif posi - nega >= 2:
            return {"direct": True}

        else:
            return None

    def get_direct(self):
        history = self.get_history()
        close = history[1]['收盘']
        is_win = (history[1]['差价'] > 0 and history[0]['差价'] > 0) or (history[1]['差价'] < 0 and history[0]['差价'] < 0)

        if history[1]["差价"] > 0 and (history[1]["差价"] >= 0.3 or abs(history[1]["差价"] - history[0]["差价"]) >= 0.3):
            return ["sell", close, is_win]
        elif history[1]['差价'] < 0 and (history[1]["差价"] <= -0.3 or abs(history[1]["差价"] - history[0]["差价"]) >= 0.3):
            return ["buy", close, is_win]
        elif history[1]["差价"] > 0:
            return ["buy", close, is_win]
        elif history[1]["差价"] < 0:
            return ["sell", close, is_win]
        else:
            return {"balance", close, is_win}

    def trade(self):
        """开新仓 平旧仓函数"""
        predict = self.get_direct()
        # 根据winnum判断是否加仓
        if predict[0] == "buy":
            result = self.buy()
            run_date = datetime.datetime.now() + datetime.timedelta(seconds=59)
            if result:
                print("开始平仓。。。。。")
                scheduler = BackgroundScheduler()
                scheduler.add_job(self.fill, 'date', run_date=run_date, args=[result, self.lot])
                scheduler.start()
        elif predict[0] == "sell":
            result = self.sell()
            run_date = datetime.datetime.now() + datetime.timedelta(seconds=59)
            if result:
                print("开始平仓。。。。。")
                scheduler = BackgroundScheduler()
                scheduler.add_job(self.fill, 'date', run_date=run_date, args=[result, self.lot])
                scheduler.start()
