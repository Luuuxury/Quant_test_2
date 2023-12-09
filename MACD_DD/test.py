import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import backtrader as bt
import os
from datetime import datetime
import calendar
import talib
import backtrader.feeds as btFeeds

numstocks = 5
final_weight = []
total_codes = []



def Fetch_OS_Stockcode(path):
    list_dir = os.listdir(path)
    list_dir_new = []
    for i in list_dir[:]:
        headcode = i.split(".")[0]
        marketcode = i.split(".")[1]
        stockcode = headcode + "." + marketcode
        list_dir_new.append(stockcode)
    return list_dir_new

def Fetch_Local_Data(path):
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

def Add_Indicators(OHLCV):
    # Add Indicate data
    OHLCV['MACD_macd'] = talib.MACD(OHLCV['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[0]
    OHLCV['MACD_sign'] = talib.MACD(OHLCV['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[1]
    OHLCV['MACD_hist'] = talib.MACD(OHLCV['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[2]
    OHLCV['ATR'] = talib.ATR(OHLCV['High'], OHLCV['Low'], OHLCV['Close'], timeperiod=14)
    OHLCV['RSI'] = talib.RSI(OHLCV['Close'], 14)
    return OHLCV


def risk_min(RandomPortfolios, stock_returns):
    # 找到标准差最小数据的索引值
    min_index = RandomPortfolios.Volatility.idxmin()
    # 在收益-风险散点图中突出风险最小的点
    RandomPortfolios.plot('Volatility', 'Returns', kind='scatter', alpha=0.3)
    x = RandomPortfolios.loc[min_index, 'Volatility']
    y = RandomPortfolios.loc[min_index, 'Returns']
    plt.scatter(x, y, color='red')
    # 将该点坐标显示在图中并保留四位小数
    plt.text(np.round(x, 4), np.round(y, 4), (np.round(x, 4), np.round(y, 4)), ha='left', va='bottom', fontsize=10)
    plt.show()
    # 提取最小波动组合对应的权重, 并转换成Numpy数组
    GMV_weights = np.array(RandomPortfolios.iloc[min_index, 0:numstocks])
    # 计算GMV投资组合收益
    stock_returns['Portfolio_GMV'] = stock_returns.mul(GMV_weights, axis=1).sum(axis=1)
    return GMV_weights

def sharp_max(RandomPortfolios, stock_returns):
    # 设置无风险回报率为0
    risk_free = 0
    # 计算每项资产的夏普比率
    RandomPortfolios['Sharpe'] = (RandomPortfolios.Returns - risk_free) / RandomPortfolios.Volatility
    # 绘制收益-标准差的散点图，并用颜色描绘夏普比率
    plt.scatter(RandomPortfolios.Volatility, RandomPortfolios.Returns, c=RandomPortfolios.Sharpe)
    plt.colorbar(label='Sharpe Ratio')
    plt.show()

    # 找到夏普比率最大数据对应的索引值
    max_index = RandomPortfolios.Sharpe.idxmax()
    # 在收益-风险散点图中突出夏普比率最大的点
    RandomPortfolios.plot('Volatility', 'Returns', kind='scatter', alpha=0.3)
    x = RandomPortfolios.loc[max_index, 'Volatility']
    y = RandomPortfolios.loc[max_index, 'Returns']
    plt.scatter(x, y, color='red')
    # 将该点坐标显示在图中并保留四位小数
    plt.text(np.round(x, 4), np.round(y, 4), (np.round(x, 4), np.round(y, 4)), ha='left', va='bottom', fontsize=10)
    plt.show()

    # 提取最大夏普比率组合对应的权重，并转化为numpy数组
    MSR_weights = np.array(RandomPortfolios.iloc[max_index, 0:numstocks])
    # 计算MSR组合的收益
    stock_returns['Portfolio_MSR'] = stock_returns.mul(MSR_weights, axis=1).sum(axis=1)
    #输出夏普比率最大的投资组合的权重
    print(MSR_weights)
    return MSR_weights

def Markowitz(total_codes, stock_returns):
    # method1:探索投资组合的最有方案，使用蒙特卡洛模拟Markowitz模型

    # 设置模拟的次数
    number = 1000
    # 设置空的numpy数组，用于存储每次模拟得到的权重、收益率和标准差
    random_p = np.empty((number, 7))
    # 设置随机数种子，这里是为了结果可重复
    np.random.seed(7)

    # 循环模拟1000次随机的投资组合
    for i in range(number):
        # 生成5个随机数，并归一化，得到一组随机的权重数据
        random5 = np.random.random(5)
        random_weight = random5 / np.sum(random5)

        # 计算年平均收益率
        mean_return = stock_returns.mul(random_weight, axis=1).sum(axis=1).mean()
        annual_return = (1 + mean_return) ** 252 - 1

        # 计算年化标准差，也成为波动率
        # 计算协方差矩阵
        cov_mat = stock_returns.cov()
        # 年化协方差矩阵
        cov_mat_annual = cov_mat * 252
        # 输出协方差矩阵
        print(cov_mat_annual)
        random_volatility = np.sqrt(np.dot(random_weight.T, np.dot(cov_mat_annual, random_weight)))

        # 将上面生成的权重，和计算得到的收益率、标准差存入数组random_p中
        random_p[i][:5] = random_weight
        random_p[i][5] = annual_return
        random_p[i][6] = random_volatility

    # 将Numpy数组转化为DataF数据框
    RandomPortfolios = pd.DataFrame(random_p)
    # 设置数据框RandomPortfolios每一列的名称
    RandomPortfolios.columns = [code + '_weight' for code in total_codes] + ['Returns', 'Volatility']

    # 绘制散点图
    RandomPortfolios.plot('Volatility', 'Returns', kind='scatter', alpha=0.3)
    plt.show()

    # weights = risk_min(RandomPortfolios, stock_returns)
    weights = sharp_max(RandomPortfolios, stock_returns)

    return weights

def weight_cal(total_codes, stock_returns):
    stock_returns['time'] = pd.to_datetime(stock_returns['time']).dt.date
    stock_returns = pd.pivot(stock_returns, index="time", columns="htsc_code", values="close")
    stock_returns.columns = [col + "_daily_return" for col in stock_returns.columns]
    stock_returns = stock_returns.pct_change().dropna()

    GMV_weights = Markowitz(total_codes, stock_returns)

    return GMV_weights

def cumulative_returns_plot(name_list, stock_returns):
    for name in name_list:
        CumulativeReturns = ((1+stock_returns[name]).cumprod()-1)
        CumulativeReturns.plot(label=name)
    plt.legend()
    plt.show()

def last_day_of_month(any_day):
    """
    获取获得一个月中的最后一天
    :param any_day: 任意日期
    :return: string
    """
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

class Select_Strategy(bt.Strategy):
    def __init__(self):
        self.codes = total_codes
    def next(self):
        today = self.data.datetime.date()
        year, month = today.year, today.month
        d, month_length = calendar.monthrange(year, month)
        if today.day == month_length:
            for i in range(len(self.codes)):
                final_weight = [0.1, 0.5, 0.3, 0.1, 0.1]
                self.order_target_percent(target=final_weight[i], data=self.codes[i])



# Only OHLCV + MACD ATR RSI
class BasicIndicatorsFeeded(btFeeds.PandasData):
    lines = ('MACD_macd', 'MACD_sign', 'MACD_hist', 'ATR', 'RSI')
    # 0- Open, 1-High, 2-Low, 3-Close, 4-Volume,
    # 新增的参数必须是从 5开始，--> ("xxx_indicator", 5)
    params = (('MACD_macd', 5), ('MACD_sign', 6), ('MACD_hist', 7), ('ATR', 8), ("RSI", 9))



if __name__ == '__main__':

    dirpath = 'D:\Finance\Data\StockData\OHLCV_Data\OHLCV_Daily\OHLCV_None'
    # dirpath = '/Users/liuyang/Desktop/Finance/Data/StockData/OHLCV_Data/OHLCV_Daily/OHLCV_hfq/'
    ts_code_list = Fetch_OS_Stockcode(path=dirpath)
    cerebro = bt.Cerebro()

    for i, stock_code in enumerate(ts_code_list[:5]):
        print("Index : {} | Back Now: {}  ".format(i, stock_code))
        code_path = stock_code + "." + "csv"

        # datapath = '/Users/liuyang/Desktop/Finance/Data/StockData/OHLCV_Data/OHLCV_Daily/OHLCV/{}'.format(code_path)
        datapath = 'D:\Finance\Data\StockData\OHLCV_Data\OHLCV_Daily\OHLCV_None\{}'.format(code_path)
        OHLCV = Fetch_Local_Data(path=datapath)
        OHLCV = OHLCV.drop(['pct_chg', 'amount', 'turnover_rate', 'volume_ratio'], axis=1)
        OHLCV = Add_Indicators(OHLCV)
        # print(OHLCV)
        data = BasicIndicatorsFeeded(dataname=OHLCV)
        cerebro.adddata(data, name=stock_code)

    cerebro.addstrategy(Select_Strategy)
    cerebro.broker.setcash(10000000.0)

    result = cerebro.run()
    print(result)
    print("value: ", cerebro.broker.get_value())
    print("cash: ", cerebro.broker.getcash())
    cerebro.plot()
