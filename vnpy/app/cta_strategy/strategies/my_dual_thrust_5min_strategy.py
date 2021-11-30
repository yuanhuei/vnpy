from datetime import time
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


class MyDualThrustStrategy(CtaTemplate):
    """"""

    author = "yuanhui"

    fixed_size = 1
    k1 = 0.4
    k2 = 0.6

    bars = [] #日线集合
    NDays=8 #计算range的天数

    day_open = 0
    day_high = 0
    day_low = 0
    day_close=0
    last_min_bar=None

    day_range = None
    long_entry = 0
    short_entry = 0
    exit_time = time(hour=14, minute=55)

    long_entered = False #用来控制每天开多仓只有一次
    short_entered = False

    parameters = ["k1", "k2", "fixed_size"]
    variables = ["day_range", "long_entry", "short_entry"]
    
    intraTradeHigh = 0                  # 持仓期内的最高点  
    intraTradeLow=0                     # 持仓期内的最低点  
    trailingPercent=0.8
    trailing_long=10                   #最高点回落平仓比例,100为全部
    trailing_short=10                  #最低点反弹平仓比例
    TradeHigh_exit=0
    TradeLow_exit=0    

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar,1,self.on_XminBar)
        self.am = ArrayManager()
        self.bars = []

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)
        
        
    def on_XminBar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.write_log("new xminbar")
        self.cancel_all
        self.am.update_bar(bar)


        if self.last_min_bar ==None:#第一个bar
            self.day_open = bar.open_price
            self.day_high = bar.high_price
            self.day_low = bar.low_price
        
        elif self.last_min_bar.datetime.date() != bar.datetime.date():#第二天开盘
            self.write_log("new day")
            daybar=BarData
            daybar.open_price=self.day_open
            daybar.close_price=self.day_close
            daybar.high_price=self.day_high
            daybar.low_price=self.day_low
            daybar.datetime=self.last_min_bar.datetime
            
            self.bars.append(daybar)
            
            self.day_open = bar.open_price
            self.day_high = bar.high_price
            self.day_low = bar.low_price
            
            self.day_range=None#重置为none

        else:#更新日bar的值
            self.day_high = max(self.day_high, bar.high_price)
            self.day_low = min(self.day_low, bar.low_price)
            self.day_close=bar.close_price
        self.last_min_bar=bar
        #self.bars.append(bar)
        if len(self.bars) < self.NDays:#保证bars里面有NDays的数据
            return 
        elif len(self.bars)==self.NDays+1:#到第NDays+1天的时候删除掉第一天的数据
            self.bars.pop(0)
        last_bar = self.bars[-1]#上一日的bar
        if last_bar.datetime.date() == bar.datetime.date():
            return#日线的最后一根分钟bar

        #self.write_log("new day")
        #Max(HH-LC,HC-LL)
        if self.day_range==None: #开盘计算range，后面就不用计算了
            HH=last_bar.high_price
            LC=last_bar.close_price
            HC=last_bar.close_price
            LL=last_bar.low_price
            for daybar in self.bars:
                HH=max(HH,daybar.high_price)
                LC=min(LC,daybar.close_price)
                HC=max(HC,daybar.close_price)
                LL=min(LL,daybar.low_price)

            self.day_range =max(HH-LC,HC-LL) #last_bar.day_high - last_bar.day_low
            self.long_entry = self.day_open + self.k1 * self.day_range
            self.short_entry =self.day_open- self.k2 * self.day_range


        if bar.datetime.time() < self.exit_time:
            if self.pos == 0:
                #if bar.close_price > self.day_open:
                self.write_log("pos=0")
                if not self.long_entered:
                    self.buy(self.long_entry, self.fixed_size, stop=True)
                #else:
                if not self.short_entered:
                    self.short(self.short_entry,
                               self.fixed_size, stop=True)

            elif self.pos > 0:
                self.write_log("pos>0")
                self.long_entered = True
                
                self.intraTradeHigh=max(self.intraTradeHigh,bar.high_price)
                self.intraTradeLow=bar.low_price
                self.TradeHigh_exit=self.intraTradeHigh*(1-self.trailingPercent)

                self.sell(max(self.short_entry,self.TradeHigh_exit), self.fixed_size, stop=True)

                if not self.short_entered:
                    self.short(self.short_entry, self.fixed_size, stop=True)

            elif self.pos < 0:
                self.write_log("pos<0")
                self.short_entered = True
                
                self.intraTradeLow=min(self.intraTradeLow,bar.low_price)
                self.intraTradeHigh=bar.high_price
                self.TradeLow_exit=self.intraTradeLow*(1+self.trailingPercent)
                
                self.cover(min(self.long_entry,self.TradeLow_exit), self.fixed_size, stop=True)

                if not self.long_entered:
                    self.buy(self.long_entry, self.fixed_size, stop=True)

        else:
            self.write_log("收盘前平仓")
            if self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.write_log("发送订单单成功")
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.write_log("成交")
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.write_log("停止单成功")
        pass
