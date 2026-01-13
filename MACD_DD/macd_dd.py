import csv
import os
import sys

import talib
import datetime
import warnings
import calendar
import tushare as ts
import numpy as np
warnings.filterwarnings('ignore')
import pandas as pd
from queue import Queue
pd.set_option('display.expand_frame_repr', False)
import backtrader as bt
import backtrader.feeds as btFeeds
import backtrader.indicators as btind
ts.set_token('')


def Fetch_Stock_Code_List(list_date="20180101"):
    """

    :return: Stock_List
    """
    ts_api = ts.pro_api('')

    Df_Stocks_info = ts_api.stock_basic(exchange='', list_status='L',
                                        fields='ts_code,symbol,name,area,industry,list_date')
    Df_Stocks_info = Df_Stocks_info[Df_Stocks_info["list_date"] < list_date]
    Df_Stocks_info = Df_Stocks_info[~Df_Stocks_info["name"].str.contains("ST")]
    ts_code_list = list(Df_Stocks_info['ts_code'])

    return ts_code_list


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


def Save_Csv(csv_data, file_name):
    # path = "/Users/liuyang/Desktop/Finance/Data/Quant_OP_Data/MACD/significance_test/{}.csv".format(file_name)
    path = r"D:\Finance\Data\Quant_OP_Data\MACD\significance_test\{}".format(file_name)
    with open(path, "a+", encoding='utf-8-sig') as f:
        writer = csv.writer(f, dialect="excel")
        csv_write = csv.writer(f)
        # csv_data = ["StockCode", "2019","2020", "2021", "2022", "WinNum", "LossNum", "WinRatio", "KellyRatio", "MaxDown", "SharpeRatio"]
        csv_write.writerow(csv_data)
        f.close()


def Save_Txt(txt_data, file_name):
    # path = "/Users/liuyang/Desktop/Finance/Data/Quant_OP_Data/MACD/significance_test/{}.txt".format(file_name)
    path = r"D:\Finance\Data\Quant_OP_Data\MACD\significance_test\{}".format(file_name)
    with open(path, "a+", encoding='utf-8-sig') as f:
        f.write(txt_data)
        f.close()

def Red_Split(OHLCV):
    """
    :param OHLCV: OHLCV data
    :return: list - index of hist red green
    """
    # Red-1
    split_index = [0]
    i = -1
    while OHLCV.MACD_hist[i] <= 0:
        i -= 1
    i += 1
    split_index.append(i)

    # Green-1
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] >= 0:
        i -= 1
    split_index.append(i)

    # Red-2
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] <= 0:
        i -= 1
    split_index.append(i)

    # Green-2
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] >= 0:
        i -= 1
    split_index.append(i)

    # Red-3
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] <= 0:
        i -= 1
    split_index.append(i)

    return split_index

def Green_Split(OHLCV):
    """

    :param OHLCV: self.data
    :return: list - index of hist green red
    """
    # Green-1
    split_index = [0]
    i = -1
    while OHLCV.MACD_hist[i] >= 0:
        i -= 1
    i += 1
    split_index.append(i)

    # Red-1
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] <= 0:
        i -= 1
    split_index.append(i)

    # Green-2
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] >= 0:
        i -= 1
    split_index.append(i)

    # Red-2
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] <= 0:
        i -= 1
    split_index.append(i)

    # Green-3
    split_index.append(i - 1)
    while OHLCV.MACD_hist[i - 1] >= 0:
        i -= 1
    split_index.append(i)

    return split_index


def Long_Core(OHLCV, Hist_CP, price_cp):
    # print(OHLCV[0])
    Go_long = False
    if OHLCV.MACD_hist[0] > 0:
        pass
    else:
        # print("Today is ", bt.num2date(OHLCV.lines[6][0]))
        split_index = Red_Split(OHLCV)
        Red_1_Price_Zone = OHLCV.low.get(ago=split_index[0], size=split_index[0] - split_index[1] + 1)
        Red_2_Price_Zone = OHLCV.low.get(ago=split_index[4], size=split_index[4] - split_index[5] + 1)

        # 前几个周期的数据 指标为Nan，跳过
        if (len(Red_1_Price_Zone) == 0) | (len(Red_2_Price_Zone) == 0):
            pass
        else:
            Red_1_Min_Price = min(Red_1_Price_Zone)
            Red_2_Min_Price = min(Red_2_Price_Zone)
            # Price Double Divergence
            if Red_1_Min_Price <= Red_2_Min_Price * price_cp:
                # Hist Check
                Red_1_Hist_Zone = OHLCV.MACD_hist.get(ago=split_index[0], size=split_index[0] - split_index[1] + 1)
                Red_2_Hist_Zone = OHLCV.MACD_hist.get(ago=split_index[4], size=split_index[4] - split_index[5] + 1)
                Red_1_Min_Hist = min(Red_1_Hist_Zone)
                Red_2_Min_Hist = min(Red_2_Hist_Zone)
                # Hist Triple Divergence
                if Red_2_Min_Hist < Red_1_Min_Hist * Hist_CP:
                    Go_long = True
                    # print("Go_long Day is ", bt.num2date(OHLCV.lines[6][0]))
                    # print("Red_1_Min_Price :", Red_1_Price_Zone)
                    # print("Red_2_Min_Price :", Red_2_Price_Zone)
    return Go_long


def Add_Indicators(OHLCV):
    # Add Indicate data
    OHLCV['MACD_macd'] = talib.MACD(OHLCV['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[0]
    OHLCV['MACD_sign'] = talib.MACD(OHLCV['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[1]
    OHLCV['MACD_hist'] = talib.MACD(OHLCV['Close'], fastperiod=12, slowperiod=26, signalperiod=9)[2]
    OHLCV['ATR'] = talib.ATR(OHLCV['High'], OHLCV['Low'], OHLCV['Close'], timeperiod=14)
    OHLCV['RSI'] = talib.RSI(OHLCV['Close'], 14)
    return OHLCV


# Only OHLCV + MACD ATR RSI
class BasicIndicatorsFeeded(btFeeds.PandasData):
    lines = ('MACD_macd', 'MACD_sign', 'MACD_hist', 'ATR', 'RSI')
    # 0- Open, 1-High, 2-Low, 3-Close, 4-Volume,
    # 新增的参数必须是从 5开始，--> ("xxx_indicator", 5)
    params = (('MACD_macd', 5), ('MACD_sign', 6), ('MACD_hist', 7), ('ATR', 8), ("RSI", 9))


class MyStragegt(bt.Strategy):
    # https://community.backtrader.com/topic/2759/take-profit-stop-loss/5
    params = dict(
        sleep_tag=28,
        trailpercent=0.05,
        hist_cp=2,
        price_cp=1.0,
    )

    def __init__(self):
        self.order = None
        self.position_days = 0
        self.position_queque = Queue(maxsize=0)


    def log(self, txt, dt=None):
        ''' Logging function fot this strategy '''
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('ORDER ACCEPTED/SUBMITTED', dt=order.created.dt)
            self.order = order
            return

        if order.status in [order.Expired]:
            self.log('BUY EXPIRED')
            return

        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                return

            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

                self.position_days = 0

        # Sentinel to None: new orders allowed
        self.order = None

    def next(self):
        # print("self.o_lit len is : ", len(self.o_li))
        # date_now = bt.num2date(self.data.lines[6][0])
        # print(self.data._name)
        # TODO: 不管有没有仓位 每天都要检查有没有背离发生，发生了就开今天的仓位

        if self.position.size == 0:
            for self.data in self.datas:
                print("---------->self.data is {} | self.data Today is : {} ".format(self.data._name,  bt.num2date(self.data.lines[6][0])))
                if self.data in self.position_queque.queue:
                    print("self.data is already exitsed ", self.data._name)
                    continue
                # print(("len(data) : ", len(self.datas)))
                open_symbol_list = []
                # symbol_price_dict = {}
                # print("self.data now: ", self.data._name, self.data._id)
                Go_long = Long_Core(self.data, Hist_CP=self.p.hist_cp, price_cp=self.p.price_cp)
                if Go_long is True:
                    # TODO: 去重，保留近一个月第一次出现的Symbol
                    # TODO: 再从这些中选出特定的 N 支 to buy it
                    print("Today Long Symbol : ", self.data._name)
                    # self.order_target_percent(target=0.01, data=self.data)
                    self.buy(data=self.data)
                    self.position_queque.put(self.data)
                    # self.buy(data=self.data._name, size=1, exectype=bt.Order.StopTrail, trailpercent=0.02)
        else:
            self.position_days += 1
            if self.position_days == 5:
                for self.data in self.position_queque.queue:
                    self.sell(self.data)
                self.position_queque.queue.clear()


    def stop(self):
        # price_range = ",".join(str(i) for i in self.price_range)
        # Save_Txt(price_range, "st1_positionRecords_tmp")
        # Save_Txt("\n", "st1_positionRecords_tmp")
        #
        # open_date = ",".join(str(i) for i in self.open_date)
        # Save_Txt(open_date, "st1_openDate_tmp")
        # Save_Txt("\n", "st1_openDate_tmp")
        # print("self.price_range is :", self.price_range)
        # print("self.open_date is :", self.open_date)
        pass



if __name__ == "__main__":

    """ Single Symbol """

    # ts_code_list = ["000001.SZ"]

    """ All Symbol """
    dirpath = 'D:\Finance\Data\StockData\OHLCV_Data\OHLCV_Daily\OHLCV_None'
    # dirpath = '/Users/liuyang/Desktop/Finance/Data/StockData/OHLCV_Data/OHLCV_Daily/OHLCV_hfq/'
    ts_code_list = Fetch_OS_Stockcode(path=dirpath)

    """ Index Content """
    # ts.set_token('4fc4dd522aa66c2c91f7c2ad32a92fcc19dc6926deafc6b62fbca017')
    # ts_api = ts.pro_api()
    # index_weight_sh = ts_api.index_weight(index_code='000002.SH')
    # ts_code_list = index_weight_sh["con_code"]

    """ If add BenchMark """
    # datapath = "/Users/liuyang/Desktop/Finance/Data/StockData/OHLCV_Data/Index_OHLCV/HS300.csv"
    # # datapath = "D:\Finance\Data\StockData\OHLCV_Data\OHLCV_Daily\Index_OHLCV\HS300.csv"
    # OHLCV_single = Fetch_Local_Data(path=datapath)

    cerebro = bt.Cerebro()
    for i, stock_code in enumerate(ts_code_list[:10]):
        # print("Index : {} | Back Now: {}  ".format(i, stock_code))

        code_path = stock_code + "." + "csv"

        # datapath = '/Users/liuyang/Desktop/Finance/Data/StockData/OHLCV_Data/OHLCV_Daily/OHLCV/{}'.format(code_path)
        datapath = 'D:\Finance\Data\StockData\OHLCV_Data\OHLCV_Daily\OHLCV_None\{}'.format(code_path)
        OHLCV = Fetch_Local_Data(path=datapath)
        OHLCV = OHLCV.drop(['pct_chg', 'amount', 'turnover_rate', 'volume_ratio'], axis=1)
        OHLCV = Add_Indicators(OHLCV)
        # print(OHLCV)
        # cerebro = bt.Cerebro()
        data = BasicIndicatorsFeeded(dataname=OHLCV)
        cerebro.adddata(data, name=stock_code)
        print("\r", end="")
        print("Data feed num : {} : ".format(i), end="")
        sys.stdout.flush()

        # Save_Txt(stock_code, "st1_positionRecords_tmp")
        # Save_Txt("\n", "st1_positionRecords_tmp")
        # Save_Txt(stock_code, "st1_openDate_tmp")
        # Save_Txt("\n", "st1_openDate_tmp")

        # ================ Cerebor head to tail =================

    cerebro.addstrategy(MyStragegt)
    # init setting
    cerebro.broker.setcash(100000000.0)
    # cerebro.broker.setcommission(commission=0.0002)
    # cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
    cerebro.addsizer(bt.sizers.SizerFix, stake=10)

    # Analyze
    results = cerebro.run()
    print("value: ", cerebro.broker.get_value())
    print("cash: ", cerebro.broker.getcash())

    cerebro.plot()






