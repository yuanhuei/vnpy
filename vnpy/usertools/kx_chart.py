from datetime import datetime
from typing import List, Tuple, Dict

import numpy as np
import pyqtgraph as pg
import talib
import copy

from vnpy.trader.ui import create_qapp, QtCore, QtGui, QtWidgets
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager
from vnpy.chart.base import NORMAL_FONT

from vnpy.trader.engine import MainEngine
from vnpy.event import Event, EventEngine

from vnpy.trader.event import (
    EVENT_TICK,
    EVENT_TRADE,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_LOG
)

from vnpy.app.cta_strategy.base import (   
    EVENT_CTA_TICK,     
    EVENT_CTA_BAR,      
    EVENT_CTA_ORDER,    
    EVENT_CTA_TRADE,     
    EVENT_CTA_HISTORY_BAR
)

from vnpy.trader.object import (
    Direction, 
    Exchange, 
    Interval, 
    Offset, 
    Status, 
    Product, 
    OptionType, 
    OrderType,
    OrderData,
    TradeData,
)

from vnpy.usertools.chart_items import (
    LineItem,
    RsiItem,
    SmaItem,
    MacdItem,
    TradeItem,
    OrderItem,
)


class NewChartWidget(ChartWidget):
    """ 
    基于ChartWidget的K线图表 
    """
    MIN_BAR_COUNT = 100

    signal_cta_history_bar:QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cta_tick: QtCore.pyqtSignal = QtCore.pyqtSignal(Event)
    signal_cta_bar:QtCore.pyqtSignal = QtCore.pyqtSignal(Event)

    def __init__(self, parent: QtWidgets.QWidget = None,event_engine: EventEngine = None,strategy_name:str=""):
        """ 初始化 """
        super().__init__(parent)
        self.strategy_name = strategy_name
        self.event_engine = event_engine

        # 创建K线主图及多个绘图部件
        self.add_plot("candle", hide_x_axis=True)
        self.add_item(CandleItem, "candle", "candle")
        self.add_item(LineItem, "line", "candle")
        self.add_item(SmaItem, "sma", "candle")
        self.add_item(OrderItem, "order", "candle")
        self.add_item(TradeItem, "trade", "candle")

        # 创建成交量附图及绘图部件
        self.add_plot("volume", maximum_height=150)
        self.add_item(VolumeItem, "volume", "volume")

        # 创建RSI附图及绘图部件
        self.add_plot("rsi", maximum_height=150)
        self.add_item(RsiItem, "rsi", "rsi")

        # 创建MACD附图及绘图部件
        self.add_plot("macd", maximum_height=150)
        self.add_item(MacdItem, "macd", "macd")

        # 创建最新价格线、光标
        self.add_last_price_line()
        self.add_cursor()
        self.setWindowTitle(f"K线图表——{symbol}.{exchange.value},{interval},{start}-{end}")

        # 委托单列表
        self.orders:List[str,OrderData] = {}
        # 成交单列表
        self.trades:List[str,TradeData] = {}

        # self.register_event()
        # self.event_engine.start()

    def register_event(self) -> None:
        """"""
        self.signal_cta_history_bar.connect(self.process_cta_history_bar)
        self.event_engine.register(EVENT_CTA_HISTORY_BAR, self.signal_cta_history_bar.emit)

        self.signal_cta_tick.connect(self.process_tick_event)
        self.event_engine.register(EVENT_CTA_TICK, self.signal_cta_tick.emit)

        self.signal_cta_bar.connect(self.process_cta_bar)
        self.event_engine.register(EVENT_CTA_BAR, self.signal_cta_bar.emit)

    def process_cta_history_bar(self, event:Event) -> None:
        """ 处理历史K线推送 """
        strategy_name,history_bars = event.data
        if strategy_name == self.strategy_name:
            self.update_history(history_bars)

            # print(f" {strategy_name} got an EVENT_CTA_HISTORY_BAR")

    def process_tick_event(self, event: Event) -> None:
        """ 处理tick数据推送 """
        strategy_name,tick = event.data
        if strategy_name == self.strategy_name:
            if self.last_price_line:
                self.last_price_line.setValue(tick.last_price)
            #print(f" {strategy_name} got an EVENT_CTA_TICK")

    def process_cta_bar(self, event:Event)-> None:
        """ 处理K线数据推送 """

        strategy_name,bar = event.data
        if strategy_name == self.strategy_name:
            self.update_bar(bar)
            # print(f"{strategy_name} got an EVENT_CTA_BAR")

    def add_last_price_line(self):
        """"""
        plot = list(self._plots.values())[0]
        color = (255, 255, 255)

        self.last_price_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            label="{value:.1f}",
            pen=pg.mkPen(color, width=1),
            labelOpts={
                "color": color,
                "position": 1,
                "anchors": [(1, 1), (1, 1)]
            }
        )
        self.last_price_line.label.setFont(NORMAL_FONT)
        plot.addItem(self.last_price_line)

    def update_history(self, history: List[BarData]) -> None:
        """
        Update a list of bar data.
        """
        self._manager.update_history(history)

        for item in self._items.values():
            item.update_history(history)

        self._update_plot_limits()

        self.move_to_right()

        self.update_last_price_line(history[-1])

    def update_bar(self, bar: BarData) -> None:
        """
        Update single bar data.
        """
        self._manager.update_bar(bar)

        for item in self._items.values():
            item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()

        self.update_last_price_line(bar)

    def update_last_price_line(self, bar: BarData) -> None:
        """"""
        if self.last_price_line:
            self.last_price_line.setValue(bar.close_price)

    def add_orders(self,orders:List[OrderData]) -> None:
        """ 
        增加委托单列表到委托单绘图部件 
        """
        for order in orders:
            self.orders[order.orderid] = order

        order_item : OrderItem = self.get_item('order')
        if order_item:
            order_item.add_orders(self.orders.values())

    def add_trades(self,trades:List[TradeData]) -> None:
        """ 
        增加成交单列表到委托单绘图部件 
        """
        for trade in trades:
            self.trades[trade.tradeid] = trade

        trade_item : TradeItem = self.get_item('trade')
        if trade_item:
            trade_item.add_trades(self.trades.values())



def ConvertBar(bars,show_minute):
    newbars=[]
    i=len(bars)//show_minute
    if len(bars)>show_minute*i:
        i=i+1
    newbars=[x for x in range(i)]

    
    i=0
    while i<((len(bars)//show_minute)+1):
        if len(bars)==show_minute*i:
            break
        datetime=bars[show_minute*i].datetime
        symbol=bars[show_minute*i].symbol
        exchange=bars[show_minute*i].exchange
        interval=bars[show_minute*i].interval
        volume=bars[show_minute*i].volume
        open_interest=bars[show_minute*i].open_interest
        open_price=bars[show_minute*i].open_price
        close_price=bars[show_minute*i].close_price
        high_price=bars[show_minute*i].high_price
        low_price=bars[show_minute*i].low_price
        j=1
        while j <show_minute:
            if (show_minute*i+j)==len(bars):
                break
            high_price=max(high_price,bars[show_minute*i+j].high_price)
            low_price=min(low_price,bars[show_minute*i+j].low_price)
            close_price=bars[show_minute*i+j].close_price
            j=j+1
        newbars[i] = BarData(
            symbol=symbol,
            exchange=Exchange(exchange),
            datetime=datetime,
            interval=Interval(interval),
            volume=volume,
            open_price=open_price,
            high_price=high_price,
            open_interest=open_interest,
            low_price=low_price,
            close_price=close_price,
            gateway_name="DB"
        )        
        i=i+1
    return newbars
################################################################
# 以下为测试代码
if __name__ == "__main__":
    def make_trades():
        import pytz
        CHINA_TZ = pytz.timezone("Asia/Shanghai")
        from vnpy.trader.object import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType,TradeData
        trades = [
            TradeData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_1', tradeid='         455', direction=Direction.LONG, offset=Offset.OPEN, price=6131.0, volume=3, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 0, 1))),
            TradeData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_2', tradeid='       12738', direction=Direction.LONG, offset=Offset.OPEN, price=6142.0, volume=3, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 14, 46))),
            TradeData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_3', tradeid='       16233', direction=Direction.LONG, offset=Offset.OPEN, price=6158.0, volume=3, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 21, 59))),
            TradeData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_4', tradeid='       22815', direction=Direction.LONG, offset=Offset.OPEN, price=6180.0, volume=3, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 39, 53))),
            TradeData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_1962356227_1', tradeid='       67570', direction=Direction.SHORT, offset=Offset.CLOSEYESTERDAY, price=6400.0, volume=12, datetime=CHINA_TZ.localize(datetime(2020, 8, 14, 1, 44,35))),
        ]
        return trades

    def make_orders():
        import pytz
        CHINA_TZ = pytz.timezone("Asia/Shanghai")
        orders=[]
        return orders

        ''''orders = [
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_1', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3.0, traded=0, status=Status.SUBMITTING, datetime=None, reference='TTS-ag2012'),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_1', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 0, 1)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_1', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 0, 1)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_1', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=3, status=Status.ALLTRADED, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 0, 1)), reference=''),

            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_2', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3.0, traded=0, status=Status.SUBMITTING, datetime=None, reference='TTS-ag2012'),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_2', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 14, 46)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_2', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 14, 46)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_2', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=3, status=Status.ALLTRADED, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 14, 46)), reference=''),

            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_3', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3.0, traded=0, status=Status.SUBMITTING, datetime=None, reference='TTS-ag2012'),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_3', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 21, 59)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_3', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 21, 59)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_3', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=3, status=Status.ALLTRADED, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 21, 59)), reference=''),

            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_4', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3.0, traded=0, status=Status.SUBMITTING, datetime=None, reference='TTS-ag2012'),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_4', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 39, 53)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_4', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 39, 53)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_753490688_4', type=OrderType.LIMIT, direction=Direction.LONG, offset=Offset.OPEN, price=6494.0, volume=3, traded=3, status=Status.ALLTRADED, datetime=CHINA_TZ.localize(datetime(2020, 8, 13, 21, 39, 53)), reference=''),

            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_1962356227_1', type=OrderType.LIMIT, direction=Direction.SHORT, offset=Offset.CLOSEYESTERDAY, price=5870.0, volume=12.0, traded=0, status=Status.SUBMITTING, datetime=None, reference='TTS-ag2012'),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_1962356227_1', type=OrderType.LIMIT, direction=Direction.SHORT, offset=Offset.CLOSEYESTERDAY, price=5870.0, volume=12, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 14, 1, 44,20)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_1962356227_1', type=OrderType.LIMIT, direction=Direction.SHORT, offset=Offset.CLOSEYESTERDAY, price=5870.0, volume=12, traded=0, status=Status.SUBMITTING, datetime=CHINA_TZ.localize(datetime(2020, 8, 14, 1, 44,25)), reference=''),
            OrderData(gateway_name='CTP', symbol='ag2012', exchange=Exchange.SHFE, orderid='3_1962356227_1', type=OrderType.LIMIT, direction=Direction.SHORT, offset=Offset.CLOSEYESTERDAY, price=5870.0, volume=12, traded=12, status=Status.ALLTRADED, datetime=CHINA_TZ.localize(datetime(2020, 8, 14, 1, 44,35)), reference=''),
        ]'''

        
        


    # 开始测试代码
    app = create_qapp()
    import sys
    print(sys.path)
    symbol = "rb888"
    exchange = Exchange.SHFE
    interval=Interval.MINUTE
    start=datetime(2015, 11, 2)
    end=datetime(2016, 6, 1)    

    dynamic = False  # 是否动态演示
    n = 1000          # 缓冲K线根数

    bars = database_manager.load_bar_data(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        start=start,
        end=end
    )
    
    show_minute=15
    print(f"一共读取{len(bars)}根1minute K线")
    print(f"一共读取{len(bars)//show_minute}根{show_minute}minute K线")
    

        
    newbars=ConvertBar(bars,420)
    
    print(f"一共读取{len(bars)}根K线")

    event_engine = EventEngine()

    widget = NewChartWidget(event_engine = event_engine)

    if dynamic:
        history = newbars[:n]      # 先取得最早的n根bar作为历史
        new_data = newbars[n:]     # 其它留着演示
    else:
        history = newbars          # 先取得最新的n根bar作为历史
        new_data = []           # 演示的为空

    # 绘制历史K线主图及各个副图
    widget.update_history(history)
    '''
    # 绘制委托单到主图
    orders = make_orders()
    widget.add_orders(orders)

    # 绘制成交单到主图
    trades = make_trades()
    widget.add_trades(trades)
    '''
    def update_bar():
        if new_data:
            bar = new_data.pop(0)
            widget.update_bar(bar)

    timer = QtCore.QTimer()
    timer.timeout.connect(update_bar)
    if dynamic:
        timer.start(100)

    widget.show()

    event_engine.start()
    app.exec_()
