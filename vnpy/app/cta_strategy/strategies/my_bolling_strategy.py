# encoding: UTF-8

"""
仅在知乎Live中分享，请勿外传。

基于布林通道通道的交易策略，适合用在股指上5分钟线上。


from __future__ import division

import talib
import numpy as np

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate, BarGenerator, ArrayManager

import csv
from vnpy.trader.vtConstant import (EMPTY_STRING, EMPTY_UNICODE, 
                                    EMPTY_FLOAT, EMPTY_INT)

from vnpy.event import Event
from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtEvent import *
from vnpy.trader.vtGateway import *
from vnpy.trader.language import text
from vnpy.trader.vtFunction import getTempPath
"""
########################################################################
import csv
from datetime import datetime
from vnpy.usertools.function import write_csv_file
from vnpy.trader.constant import Exchange, Interval,Offset,Direction
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
'''
日线小时策略，日线空头或多头的时候，小时上下轨开仓，下上轨平仓，不加仓
'''

class MyBollingStrategy(CtaTemplate):
    """基于布林通道的交易策略"""
    className = 'MyBollingerBotStrategy'
    author = 'yuanhui'

    # 策略参数
    #bollWindow = 26         # 通道窗口数
    entryDev = 2          # 开仓偏差    
    bollWindow5min = 26         # 通道窗口数
    entryDev5min = 2          # 开仓偏差
    bollWindow15min = 26         # 通道窗口数
    entryDev15min = 2          # 开仓偏差    
    bollWindow30min = 52         # 通道窗口数
    entryDev30min = 2          # 开仓偏差
    bollWindowDay = 26         # 通道窗口数
    entryDevDay = 2          # 开仓偏差
    
    #exitDev = 1.2           # 平仓偏差
    #trailingPrcnt = 0.4     # 移动止损百分比
    #maWindow = 10           # 过滤用均线窗口
    initDays = 15           # 初始化数据所用的天数
    fixedSize = 1           # 每次交易的数量
    priceTick = 0.2         # 价格最小变动 
    
    DayTrendStatus='panzhen'  #DuoTou, KongTou,Panzheng
    FifteenMinTrendStatus='panzhen'
    FiveMinTrendStatus='panzhen'
    ThirtyMinTrendStatus='panzhen'
    

    # 5Min策略变量    
    bollMid = 0                         # 布林带中轨
    BeforebollMid=0                     #上一根K线的布林线中轨
    #bollStd = 0                         # 布林带宽度
    bollUp = 0                          # 开仓上轨
    Beforebollup=0                      #上一根K线的布林线上轨
    bollDown = 0                        # 平仓下轨    
    beforebolldown=0                    #上一根K线的布林线下轨
    
    # 15Min策略变量    
    bollMid15 = 0                         # 布林带中轨
    BeforebollMid15=0                     #上一根K线的布林线中轨
    #bollStd15 = 0                         # 布林带宽度
    bollUp15 = 0                          # 开仓上轨
    Beforebollup15=0                      #上一根K线的布林线上轨
    bollDown15 = 0                        # 平仓下轨    
    beforebolldown15=0                    #上一根K线的布林线下轨    
 
    # 30Min策略变量    
    bollMid30 = 0                         # 布林带中轨
    BeforebollMid30=0                     #上一根K线的布林线中轨
    #bollStd30 = 0                         # 布林带宽度
    bollUp30 = 0                          # 开仓上轨
    Beforebollup30=0                      #上一根K线的布林线上轨
    bollDown30 = 0                        # 平仓下轨    
    beforebolldown30=0                    #上一根K线的布林线下轨       
    
    # 日线策略变量    
    bollMidDay = 0                         # 布林带中轨
    BeforebollMidDay=0                     #上一根K线的布林线中轨
    #bollStd30 = 0                         # 布林带宽度
    bollUpDay = 0                          # 开仓上轨
    BeforebollupDay=0                      #上一根K线的布林线上轨
    bollDownDay= 0                        # 平仓下轨    
    beforebolldownDay=0                    #上一根K线的布林线下轨         
  
    #maFilter = 0                        # 均线过滤
    #maFilter1 = 0                       # 上一期均线                   
    
    intraTradeHigh = 0                  # 持仓期内的最高点  
    longEntry = 0                       #多头开仓位置
    longExit = 0                        #多头平仓位置 
    shortEntry=0                        #空头开仓位置
    shortExit=0                         #空头平仓位置
    #上一个交易单子保本否
    lastTrade_baoben=False
    
    deal=0                              # 多头平仓为正，空头平仓为  
    dealopen=0                          # 多头开仓正，空头开仓负 
    
    
    orderList = []                      # 保存委托代码的列表
    tradedata=[]
    tradedata_boll=[] #所有的需要在布林线止损的交易单
    tradedata_baoben=[] #所有的已经过了保本线的交易单
    tradedata_day=[] #所有的需要在日线布林中轨止损的交易单

    # 参数列表，保存了参数的名称
    parameters = [
                 'bollWindow5min',
                 'bollWindow15min',
                 'bollWindow30min',
                 'entryDev',
                 'initDays',
                 'fixedSize',
                 'DayTrendStatus'
    ]    

    # 变量列表，保存了变量的名称
    variables = ['inited',
               'trading',
               'pos',
               'bollUp',
               'bollDown',
               'bollUp15',
               'bollDown15',
               'bollUp30',
               'bollDown30',               
               'FifteenMinTrendStatus',
               'FiveMinTrendStatus',
               'ThirtyMinTrendStatus'
               ]
    
    # 同步列表
    syncList = ['pos',
                'intraTradeHigh']

    #----------------------------------------------------------------------

        
    def __init__(self, ctaEngine, strategy_name, vt_symbol, setting):
        """Constructor"""
        #super(MyBollingerBotStrategy, self).__init__(ctaEngine, setting)
        super().__init__(ctaEngine, strategy_name, vt_symbol, setting)
        
        self.bm5 = BarGenerator(self.on_bar, 5, self.on_5Min_bar)
        self.am5 = ArrayManager(80)
        
        self.bm15 = BarGenerator(self.on_bar, 15, self.on_15Min_bar)
        self.am15 = ArrayManager(80)        
        
        self.bm30 = BarGenerator(self.on_bar, 30, self.on_30Min_bar)
        self.am30 = ArrayManager(80)                
 
        self.bmDay = BarGenerator(self.on_bar, 9, self.onDayBar,Interval.HOUR)
        self.amDay = ArrayManager(30)       
        
        head=["datetime","BollStatus","open","close","high","low","openInterest","volume","deal","pDown","pUp","dealOpen"]
        write_csv_file("datasig5.csv",head,None,"w")
        write_csv_file("datasig15.csv",head,None,"w")
        write_csv_file("datasig30.csv",head,None,"w")
        write_csv_file("datasigDay.csv",head,None,"w")
        head=["datetime","orderid","tradeid","direction","offset","price","volume"]
        write_csv_file("datasigTrade.csv",head,None,"w")
        
  
    #----------------------------------------------------------------------
    def on_init(self):
        """初始化策略（必须由用户继承实现）"""
        self.write_log(u'%s策略初始化' %self.className)
        
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.load_bar(self.initDays)
        #for bar in initData:
        #   self.onBar(bar)

        #self.put_event()

    #----------------------------------------------------------------------
    def on_start(self):
        """启动策略（必须由用户继承实现）"""
        self.write_log(u'%s策略启动' %self.className)
        self.put_event()

    #----------------------------------------------------------------------
    def on_stop(self):
        """停止策略（必须由用户继承实现）"""
        self.write_log(u'%s策略停止' %self.className)
        self.put_event()

    #----------------------------------------------------------------------
    def on_tick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bm5.updateTick(tick)

    #----------------------------------------------------------------------
    def on_bar(self, bar: BarData):
        """收到Bar推送（必须由用户继承实现）"""
        #早盘开盘前一分钟收到的多余的tick的清除
        if "09:29:00" in bar.datetime.strftime("%Y-%m-%d %H:%M:%S") and "IF" in bar.symbol:
            return
        if "08:59:00" in bar.datetime.strftime("%Y-%m-%d %H:%M:%S"):
            return

        #s基于日线判断趋势过滤，因此先更新
        self.bmDay.update_bar(bar)        
        #s基于30分钟更新
        self.bm30.update_bar(bar)
        # 基于15分钟更新
        self.bm15.update_bar(bar)
        # 基于5分钟更新
        self.bm5.update_bar(bar)        
        
        #判断当前5Min布林线趋势状态
        if not self.am5.inited or not self.am15.inited or not self.am30.inited or not self.amDay.inited:
            return
        if self.bm5.window_bar !=None:   
            if self.bm5.window_bar.high_price > self.bollUp and self.bm5.window_bar.low_price > self.bollMid:
                self.FiveMinTrendStatus='duotou'
            elif self.bm5.window_bar.low_price < self.bollDown and self.bm5.window_bar.high_price < self.bollMid:
                self.FiveMinTrendStatus='kongtou'
            elif self.bm5.window_bar.low_price < self.bollMid and self.FiveMinTrendStatus=='duotou':
                self.FiveMinTrendStatus='panzhen'
            elif self.bm5.window_bar.high_price > self.bollMid and self.FiveMinTrendStatus=='kongtou':
                self.FiveMinTrendStatus='panzhen'        
            #判断当前15Min布林线趋势状态
        if self.bm15.window_bar!=None:
            if self.bm15.window_bar.high_price > self.bollUp15 and self.bm15.window_bar.low_price > self.bollMid15:
                self.FifteenMinTrendStatus='duotou'
            elif self.bm15.window_bar.low_price < self.bollDown15 and self.bm15.window_bar.high_price < self.bollMid15:
                self.FifteenMinTrendStatus='kongtou'
            elif self.bm15.window_bar.low_price < self.bollMid15 and self.FifteenMinTrendStatus=='duotou':
                self.FifteenMinTrendStatus='panzhen'
            elif self.bm15.window_bar.high_price > self.bollMid15 and self.FifteenMinTrendStatus=='kongtou':
                self.FifteenMinTrendStatus='panzhen'
            #判断当前30Min布林线趋势状态
        if self.bm30.window_bar!=None:
            if self.bm30.window_bar.high_price > self.bollUp30 and self.bm30.window_bar.low_price > self.bollMid30:
                self.ThirtyMinTrendStatus='duotou'
            elif self.bm30.window_bar.low_price < self.bollDown30 and self.bm30.window_bar.high_price < self.bollMid30:
                self.ThirtyMinTrendStatus='kongtou'
            elif self.bm30.window_bar.low_price < self.bollMid30 and self.ThirtyMinTrendStatus=='duotou':
                self.ThirtyMinTrendStatus='panzhen'
            elif self.bm30.window_bar.high_price > self.bollMid30 and self.ThirtyMinTrendStatus=='kongtou':
                self.ThirtyMinTrendStatus='panzhen'
            #判断当前日线布林线趋势状态
        if self.bmDay.window_bar!=None:
            if self.bmDay.window_bar.high_price > self.bollUpDay and self.bmDay.window_bar.low_price > self.bollMidDay:
                self.DayTrendStatus='duotou'
            elif self.bmDay.window_bar.low_price < self.bollDownDay and self.bmDay.window_bar.high_price < self.bollMidDay:
                self.DayTrendStatus='kongtou'
            elif self.bmDay.window_bar.low_price < self.bollMidDay and self.DayTrendStatus=='duotou':
                self.DayTrendStatus='panzhen'
            elif self.bmDay.window_bar.high_price > self.bollMidDay and self.DayTrendStatus=='kongtou':
                self.DayTrendStatus='panzhen'
        '''
                
        if self.pos == 0:
            #self.intraTradeHigh = bar.high
            orderList=[]
            if self.DayTrendStatus=='duotou' and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus=='duotou' and self.FiveMinTrendStatus=='duotou':
                #self.longEntry = bar.close
                self.cancelAll()
                orderList=self.buy(bar.close+self.priceTick, self.fixedSize, True)        
                print (u"策略：%s,委托多单，1分钟收盘价开仓"%self.__dict__["name"]) 
            elif self.DayTrendStatus=='kongtou'  and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus=='kongtou' and self.FiveMinTrendStatus=='kongtou':
                #self.shortEntry = bar.close
                self.cancelAll()
                orderList=self.short( bar.close-self.priceTick, self.fixedSize, True)   
                print (u"策略：%s,委托空单，1分钟收盘价开仓"%self.__dict__["name"])
        '''      
        #print (u'策略:',self.__dict__["name"])
        #print (u"策略：%s,时间：%s,1分钟刷新，5分钟趋势%s,15分钟趋势%s,30分钟趋势%s,日线趋势%s"%(self.__dict__["name"],bar.datetime,self.FiveMinTrendStatus,self.FifteenMinTrendStatus,self.ThirtyMinTrendStatus,self.DayTrendStatus))  
        self.put_event()

#----------------------------------------------------------------------
    def on_5Min_bar(self, bar: BarData):
        """收到5分钟K线"""        

        if not self.am5.inited or not self.am15.inited or not self.am30.inited or not self.amDay.inited:
            self.am5.update_bar(bar)
            return        
        #计算上一个k线的布林中轨，上轨，下轨
        self.BeforebollMid=self.am5.sma(self.bollWindow5min)
        self.Beforebollup,self.beforebolldown=self.am5.boll(self.bollWindow5min,self.entryDev5min)
        
        # 保存K线数据
        self.am5.update_bar(bar)
        
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        #self.cancel_all()
        orderList=[]
    
        # 计算指标数值
        self.bollMid = self.am5.sma(self.bollWindow5min)
        self.bollUp,self.bollDown = self.am5.boll(self.bollWindow5min,self.entryDev5min)

        #判断当前5Min布林线趋势状态
        if bar.high_price > self.Beforebollup and bar.low_price > self.BeforebollMid:
            self.FiveMinTrendStatus='duotou'
        elif bar.low_price < self.beforebolldown and bar.high_price < self.BeforebollMid:
            self.FiveMinTrendStatus='kongtou'
        elif bar.low_price < self.BeforebollMid and self.FiveMinTrendStatus=='duotou':
            self.FiveMinTrendStatus='panzhen'
        elif bar.high_price > self.BeforebollMid and self.FiveMinTrendStatus=='kongtou':
            self.FiveMinTrendStatus='panzhen'
        '''
        if bar.high > self.bollMid15 and self.FifteenMinTrendStatus == 'kongtou':
            self.FifteenMinTrendStatus=='panzhen'
        if bar.low < self.bollMid15 and self.FifteenMinTrendStatus == 'duotou':      
            self.FifteenMinTrendStatus=='panzhen'       
        '''   
        # 判断是否要进行交易
        print (u"策略：%s,5分钟刷新，趋势状态,5分钟趋势%s,15分钟趋势%s,30分钟趋势%s,日线趋势%s"%(self.className,self.FiveMinTrendStatus,self.FifteenMinTrendStatus,self.ThirtyMinTrendStatus,self.DayTrendStatus))
        # 当前无仓位，发送OCO开仓委托
        '''        
        if self.pos == 0:
            #self.intraTradeHigh = bar.high
            #多头处理
            if self.DayTrendStatus=='duotou' and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus!='duotou' :
                orderList=self.buy(self.bollUp15+self.priceTick, self.fixedSize, True)
                print (u"策略：%s,委托多单，15分钟上轨开仓"%self.__dict__["name"])
            elif self.DayTrendStatus=='duotou' and self.ThirtyMinTrendStatus=="panzhen" :
                orderList=self.buy(self.bollUp30+self.priceTick, self.fixedSize, True)
                print (u"策略：%s,委托多单，30分钟上轨开仓"%self.__dict__["name"])     
            elif self.DayTrendStatus=='duotou' and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus=='duotou' and self.FiveMinTrendStatus=='duotou':
                self.longEntry = bar.close
                orderList=self.buy(self.longEntry+self.priceTick, self.fixedSize, True)        
                print (u"策略：%s,委托多单，5分钟收盘价开仓"%self.__dict__["name"])
            elif self.DayTrendStatus=='duotou' and self.ThirtyMinTrendStatus!="panzhen"  and self.FifteenMinTrendStatus=='duotou' and self.FiveMinTrendStatus!='duotou':
                self.longEntry=self.bollUp
                orderList=self.buy(self.longEntry+self.priceTick, self.fixedSize, True)    
                print (u"策略：%s,委托多单，5分钟上轨开仓"%self.__dict__["name"])
            #空头处理    
            elif  self.DayTrendStatus=='kongtou' and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus!='kongtou' :
                orderList=self.short(self.bollDown15-self.priceTick, self.fixedSize, True)
                print (u"策略：%s,委托空单，15分钟下轨开仓"%self.__dict__["name"])
            elif  self.DayTrendStatus=='kongtou' and self.ThirtyMinTrendStatus=="panzhen" :
                orderList=self.short(self.bollDown30-self.priceTick, self.fixedSize, True)
                print (u"策略：%s,委托空单，30分钟下轨开仓"%self.__dict__["name"])   
            elif self.DayTrendStatus=='kongtou'  and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus=='kongtou' and self.FiveMinTrendStatus=='kongtou':
                self.shortEntry = bar.close
                orderList=self.short(self.shortEntry-self.priceTick, self.fixedSize, True)   
                print (u"策略：%s,委托空单，5分钟收盘价开仓"%self.__dict__["name"])
            elif self.DayTrendStatus=='kongtou'  and self.ThirtyMinTrendStatus!="panzhen" and self.FifteenMinTrendStatus=='kongtou' and self.FiveMinTrendStatus!='kongtou':
                self.shortEntry=self.bollDown
                orderList=self.short(self.shortEntry-self.priceTick, self.fixedSize, True)  
                print (u"策略：%s,委托空单，5分钟下轨开仓"%self.__dict__["name"])
                     

        # 持有多头仓位
        elif self.pos > 0:
            orderList=self.sell(self.bollDown-self.priceTick, abs(self.pos), True)
            print (u"策略：%s,委托止损单，5分钟下轨平仓"%self.__dict__["name"])
        # 持有空头仓位
        elif self.pos < 0:
            orderList=self.cover(self.bollUp+self.priceTick, abs(self.pos), True)
            print (u"策略：%s,委托止损单，5分钟上轨平仓"%self.__dict__["name"])
    
        with open("datasig5.csv","ab+",) as csvfile: 
            writer = csv.writer(csvfile)
            writer.writerow([bar.datetime,bar.open, bar.close, bar.high, bar.low,bar.openInterest,bar.volume,self.deal,self.bollDown,self.bollUp,self.dealopen])
        self.deal=0
        self.dealopen=0
        

        if orderList:
            print (u"策略：%s,委托单成功,单号%s"%(self.__dict__["name"],orderList[-1]))
        #else:
         #   print u"策略：%s,委托单失败"%self.__dict__["name"]            
        # 发出状态更新事件
        '''
        self.put_event()        


    def on_15Min_bar(self, bar: BarData):
        """15分钟K线推送"""
    
        if not self.am15.inited or not self.am30.inited or not self.amDay.inited:
            self.am15.update_bar(bar)
            return
        
        #计算上一个k线的布林中轨，上轨，下轨
        self.BeforebollMid15=self.am15.sma(self.bollWindow15min)
        self.Beforebollup15,self.beforebolldown15=self.am15.boll(self.bollWindow15min,self.entryDev15min)   
    
        self.am15.update_bar(bar)        
        # 计算指标数值
        self.bollMid15 = self.am15.sma(self.bollWindow15min)
        self.bollUp15,self.bollDown15 = self.am15.boll(self.bollWindow15min,self.entryDev15min)

    
        #判断当前15Min布林线趋势状态
        if bar.high_price > self.Beforebollup15 and bar.low_price > self.BeforebollMid15:
            self.FifteenMinTrendStatus='duotou'
        elif bar.low_price < self.beforebolldown15 and bar.high_price < self.BeforebollMid15:
            self.FifteenMinTrendStatus='kongtou'
        elif bar.low_price < self.BeforebollMid15 and self.FifteenMinTrendStatus=='duotou':
            self.FifteenMinTrendStatus='panzhen'
        elif bar.high_price > self.BeforebollMid15 and self.FifteenMinTrendStatus=='kongtou':
            self.FifteenMinTrendStatus='panzhen'
   
        with open("datasig15.csv","ab+",) as csvfile: 
            writer = csv.writer(csvfile)
            #writer.writerow([bar.datetime,bar.open_price, bar.close_price, bar.high_price, bar.low_price,bar.open_interest,bar.volume,self.deal,self.bollDown15,self.bollUp15,self.dealopen])
        
        print (u"策略:%s,15分钟刷新，趋势状态,5分钟趋势%s,15分钟趋势%s,30分钟趋势%s,日线趋势%s"%(self.className,self.FiveMinTrendStatus,self.FifteenMinTrendStatus,self.ThirtyMinTrendStatus,self.DayTrendStatus))
        #print u"15分钟收盘价",self.am15.closeArray[75:]
        # 当前无仓位，发送OCO开仓委托
        '''
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            
            if self.FifteenMinTrendStatus=='panzhen':
                self.longEntry = self.bollUp15
                self.shortEntry=self.booldown15
                self.buy(self.longEntry, self.fixedSize, True)
                self.short(self.shortEntry,self.fixedSize,True)
        '''
        # 发出状态更新事件
        self.put_event() 
        
    def on_30Min_bar(self, bar: BarData):
        """30分钟K线推送"""
        t1=str(bar.datetime)
        t2=str(datetime(2016,2,3,21,0,0))
        if t2 in t1:
            i=0
            
        if not self.am30.inited:# or not self.amDay.inited:
            self.am30.update_bar(bar)
            return
        
        #计算上一个k线的布林中轨，上轨，下轨
        self.BeforebollMid30=self.am30.sma(self.bollWindow30min)
        self.Beforebollup30,self.beforebolldown30=self.am30.boll(self.bollWindow30min,self.entryDev30min)   
    
        self.am30.update_bar(bar)        
        # 计算指标数值
        self.bollMid30 = self.am30.sma(self.bollWindow30min)
        self.bollUp30,self.bollDown30 = self.am30.boll(self.bollWindow30min,self.entryDev30min)

    
        #判断当前30Min布林线趋势状态
        if bar.high_price > self.Beforebollup30 and bar.low_price > self.BeforebollMid30:
            self.ThirtyMinTrendStatus='duotou'
        elif bar.low_price < self.beforebolldown30 and bar.high_price < self.BeforebollMid30:
            self.ThirtyMinTrendStatus='kongtou'
        elif bar.low_price < self.BeforebollMid30 and self.ThirtyMinTrendStatus=='duotou':
            self.ThirtyMinTrendStatus='panzhen'
        elif bar.high_price > self.BeforebollMid30 and self.ThirtyMinTrendStatus=='kongtou':
            self.ThirtyMinTrendStatus='panzhen'
        
        self.cancel_all()
        #开平仓位置
        self.intraTradeHigh = bar.high_price
        self.longEntry = self.bollUp30+self.priceTick
        self.longExit=self.bollDown30-self.priceTick             
        self.shortEntry=self.bollDown30-self.priceTick      
        self.shortExit=self.bollUp30+self.priceTick
        if not self.tradedata:  #策略启动到现在无交易
            if self.ThirtyMinTrendStatus=='panzhen' and self.DayTrendStatus=='duotou':
                self.buy(self.longEntry, self.fixedSize, True)            
            elif self.ThirtyMinTrendStatus=='panzhen' and self.DayTrendStatus=='kongtou':                     
                self.short(self.shortEntry,self.fixedSize,True)    
        else:                   #策略启动到现在有交易 
            #需要在布林线上下轨止损的但系，重新发出止损单子
            trade=self.tradedata[-1]           
            if trade.offset==Offset.CLOSE:    #最后一个交易为平仓单，发送开仓单在布林线上下轨
                if self.ThirtyMinTrendStatus=='panzhen' and self.DayTrendStatus=='duotou':
                    self.buy(self.longEntry, self.fixedSize, True)            
                elif self.ThirtyMinTrendStatus=='panzhen' and self.DayTrendStatus=='kongtou':                     
                    self.short(self.shortEntry,self.fixedSize,True)           
            elif trade.offset==Offset.OPEN and trade.direction==Direction.LONG: # 最后一笔交易为多头仓位，发送平仓单在下轨
                orderList=self.sell(self.longExit, trade.volume, True)
                print (u"策略：%s,委托止损单，30分钟下轨平仓"%self.className)
            elif trade.offset==Offset.OPEN and trade.direction==Direction.SHORT: # 最后一笔交易为空头仓位，发送平仓单在上轨
                orderList=self.cover(self.shortExit, trade.volume, True)
                print (u"策略：%s,委托止损单，30分钟上轨平仓"%self.className)   
            #需要在保本位置设置止损的交易单，重新发出止损单子
            if len(self.tradedata_baoben)>0:
                i=0
                while i <len(self.tradedata_day):
                    volume=self.tradedata_baoben[i].volume
                    i=i+1
                    if self.tradedata_baoben[i-1].direction==Direction.LONG:
                        orderList=self.sell(self.tradedata_baoben[i].price, volume, True)
                        print (u"策略：%s,委托止损单，保本价格平仓"%self.className)          
                    elif self.tradedata_baoben[i-1].direction==Direction.SHORT:
                        orderList=self.cover(self.tradedata_baoben[i].price, volume, True)
                        print (u"策略：%s,委托止损单，保本价格平仓"%self.className)          
            #需要在日线中轨止损的单子，需要在新的日线中轨处发出止损单
            if len(self.tradedata_day)>0:
                i=0
                volume=0
                while i <len(self.tradedata_day):
                    volume=self.tradedata_day[i].volume+volume
                    i=i+1
                if self.tradedata_day[i-1].direction==Direction.LONG:
                    orderList=self.sell(self.shortExit, volume, True)
                    print (u"策略：%s,委托止损单，日线中轨平仓"%self.className)          
                elif self.tradedata_day[i-1].direction==Direction.SHORT:
                    orderList=self.cover(self.shortExit, volume, True)
                    print (u"策略：%s,委托止损单，日线中轨平仓"%self.className)                 
            
        bardata=[bar.datetime,self.ThirtyMinTrendStatus,bar.open_price, bar.close_price, bar.high_price, bar.low_price,bar.open_interest,bar.volume,self.pos,self.bollDown30,self.bollUp30,self.dealopen]
        write_csv_file("datasig30.csv",None,bardata,"a+")
        print(u"时间：",bar.datetime)
        print (u"策略:%s,30分钟刷新，趋势状态,5分钟趋势%s,15分钟趋势%s,30分钟趋势%s,日线趋势%s"%(self.className,self.FiveMinTrendStatus,self.FifteenMinTrendStatus,self.ThirtyMinTrendStatus,self.DayTrendStatus))
        print (u"30分钟收盘价",self.am30.close_array[60:]) 

        # 发出状态更新事件
        self.put_event()      
        
    def onDayBar(self, bar: BarData):
        """日K线推送"""
    
        if not self.amDay.inited:
            self.amDay.update_bar(bar)
            return
        

        #计算上一个k线的布林中轨，上轨，下轨
        self.BeforebollMidDay=self.amDay.sma(self.bollWindowDay)
        self.BeforebollupDay,self.beforebolldownDay=self.amDay.boll(self.bollWindowDay,self.entryDevDay)   
    
        self.amDay.update_bar(bar)        
        # 计算指标数值
        self.bollMidDay = self.amDay.sma(self.bollWindowDay)
        self.bollUpDay,self.bollDownDay = self.amDay.boll(self.bollWindowDay,self.entryDevDay)

    
        #判断当前日线布林线趋势状态
        if bar.high_price > self.BeforebollupDay and bar.low_price > self.BeforebollMidDay:
            self.DayTrendStatus='duotou'
        elif bar.low_price < self.beforebolldownDay and bar.high_price < self.BeforebollMidDay:
            self.DayTrendStatus='kongtou'
        elif bar.low_price < self.BeforebollMidDay and self.DayTrendStatus=='duotou':
            self.DayTrendStatus='panzhen'
        elif bar.high_price > self.BeforebollMidDay and self.DayTrendStatus=='kongtou':
            self.DayTrendStatus='panzhen'
       
        #需要在日线中轨止损的单子，需要在新的日线中轨处发出止损单
        if len(self.tradedata_day)>0:
            i=0
            volume=0
            while i <len(self.tradedata_day):
                volume=self.tradedata_day[i].volume+volume
                i=i+1
            if self.tradedata_day[i-1].direction==Direction.LONG:
                orderList=self.sell(self.shortExit, volume, True)
                print (u"策略：%s,委托止损单，日线中轨平仓"%self.className)          
            elif self.tradedata_day[i-1].direction==Direction.SHORT:
                orderList=self.cover(self.shortExit, volume, True)
                print (u"策略：%s,委托止损单，日线中轨平仓"%self.className)              
        '''         
        #日线盘整，上下轨开仓  
        if self.DayTrendStatus=="panzhen" and self.pos==0:
            self.cancelAll()
            orderList=[]
            orderList=self.buy(self.bollUpDay+self.priceTick, self.fixedSize, True)
            print (u"策略：%s,委托多单，日线上轨开仓"%self.__dict__["name"])
            if orderList:
                print (u"策略：%s,委托单成功,单号%s"%(self.__dict__["name"],orderList[-1]))
            else:
                print (u"策略：%s,委托单失败"%self.__dict__["name"])              
            orderList=[]    
            orderList=self.short(self.bollDownDay-self.priceTick, self.fixedSize, True)
            print (u"策略：%s,委托空单，日线下轨开仓"%self.__dict__["name"])                       
            if orderList:
                print (u"策略：%s,委托单成功,单号%s"%(self.__dict__["name"],orderList[-1]))
            else:
                print (u"策略：%s,委托单失败"%self.__dict__["name"] )             
                
        '''
        bardata=[bar.datetime,self.DayTrendStatus,bar.open_price, bar.close_price, bar.high_price, bar.low_price,bar.open_interest,bar.volume,self.pos,self.bollDownDay,self.bollUpDay,self.dealopen]
        write_csv_file("datasigDay.csv",None,bardata,"a+")        
        print(u"时间：",bar.datetime)
        print (u"策略:%s,日线刷新，趋势状态,5分钟趋势%s,15分钟趋势%s,30分钟趋势%s,日线趋势%s"%(self.className,self.FiveMinTrendStatus,self.FifteenMinTrendStatus,self.ThirtyMinTrendStatus,self.DayTrendStatus))
        print (u"日线开盘价",self.amDay.open_array[1:])
        print (u"日线收盘价",self.amDay.close_array[1:])  

    
        # 发出状态更新事件
        self.put_event()               
 
    #----------------------------------------------------------------------
    def on_order(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def on_trade(self, trade):
        #打印信息
        print ("策略:%s,趋势状态,5分钟趋势%s,15分钟趋势%s,30分钟趋势%s,日线趋势%s"%(self.className,self.FiveMinTrendStatus,self.FifteenMinTrendStatus,self.ThirtyMinTrendStatus,self.DayTrendStatus))
        
        print (u"策略：%s, 委托单成交"%self.className)
        print (trade.direction)
        print (trade.offset)
        #print "15min:",self.FifteenMinTrendStatus
        #print "5min:",self.FiveMinTrendStatus
        
        #head=["datetime","orderid","tradeid","direction","offset","price","volume"]
        #所有交易单保存下来
        self.tradedata.append(trade)
        #开仓的交易单单独保存下来到需要布林止损的list中
        if trade.offset==Offset.OPEN:
            self.tradedata_boll.append(trade)
        #保存到文件
        tradedata=[trade.datetime,trade.orderid,trade.tradeid,trade.direction,trade.offset,trade.price,trade.volume]
        write_csv_file("datasigTrade.csv",None,tradedata,"a+")        
        #开仓成功后先取消掉还有的挂单，主要针对的是日线的双向挂单
        #if self.pos!=0:        
        #    self.cancel_all()
        # 发出状态更新事件
        orderList=[]
        if trade.offset==Offset.OPEN and trade.direction==Direction.LONG: #多头成交，设置止损单
            orderList=self.sell(self.bollDown30-self.priceTick, trade.volume, True)
            print (u"委托止损单，30分钟下轨平仓")
            if orderList:
                print( u"委托单成功单号",orderList)    
            else :
                print (u"委托单失败")                  
        elif trade.offset==Offset.OPEN and trade.direction==Direction.SHORT: #空头成交，设置止损单
            orderList=self.cover(self.bollUp30+self.priceTick, trade.volume, True)
            print (u"委托止损单，30分钟上轨平仓")
            if orderList:
                print( u"委托单成功单号",orderList)    
            else :
                print (u"委托单失败")             
        #更新周期状态          
        if trade.offset==Offset.OPEN:
            if trade.direction==Direction.LONG:
                self.dealopen=1
                self.DayTrendStatus="duotou"
                self.FifteenMinTrendStatus='duotou'
                self.FiveMinTrendStatus='duotou'
                self.ThirtyMinTrendStatus='duotou'
            else:
                self.dealopen=-1
                self.DayTrendStatus="kongtou"
                self.FifteenMinTrendStatus='kongtou'
                self.FiveMinTrendStatus='kongtou'
                self.ThirtyMinTrendStatus='kongtou'
                
        if trade.offset==Offset.CLOSE:
            if trade.direction==Direction.LONG:
                self.ThirtyMinTrendStatus='kongtou'
                self.deal=1
            else:
                self.deal=-1
                

        self.put_event()

    #----------------------------------------------------------------------
    def on_stop_order(self, so):
        """停止单推送"""
        pass