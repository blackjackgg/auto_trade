import pandas as pd
from matplotlib import pyplot as plt


def plot_line(datadict,title=""):
    """传入一个字典 字典名作为坐标轴"""
    print(datadict)
    df2 = pd.DataFrame(datadict,
                       columns=datadict.keys())

    # df.plot(kind='bar')  ## 默认是折线图   这是盈利曲线 area  bar
    df2.plot()
    plt.title(label=title)
    plt.show()