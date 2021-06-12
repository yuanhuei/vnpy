from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy
from vnpy.app.cta_strategy.strategies.boll_channel_strategy import BollChannelStrategy
from datetime import datetime
from vnpy.app.cta_strategy.strategies.my_bolling_multipos_strategy import (
    MyBollingMultiPosStrategy,
)
from vnpy.app.cta_strategy.strategies.my_bolling_day_strategy import (
    MyBollingDayStrategy,
)
from vnpy.app.cta_strategy.strategies.my_bolling_15min_strategy import (
    MyBolling15MinStrategy,
)


def run_backtesting(strategy_class, setting, vt_symbol, interval, start, end, rate, slippage, size, pricetick, capital):
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval=interval,
        start=start,
        end=end,
        rate=rate,
        slippage=slippage,
        size=size,
        pricetick=pricetick,
        capital=capital    
    )
    engine.add_strategy(strategy_class, setting)
    engine.load_data()
    engine.run_backtesting()
    df = engine.calculate_result()
    return df

def show_portafolio(df):
    engine = BacktestingEngine()
    engine.calculate_statistics(df)
    engine.show_chart(df)
    
df1 = run_backtesting(
    strategy_class=MyBollingDayStrategy, 
    setting={}, 
    vt_symbol="ru99.CFFEX",
    #橡胶ru99.CFFEX,焦炭j99.DCE,螺纹钢rb888.SHFE,铜cu888.SHFE,鸡蛋jd99.DCE,铁矿石i99.DCE,豆粕m99.CFFEX,玉米c99.DCE
    interval="1m", 
    start=datetime(2010, 1, 1), 
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=1,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
    )

df2 = run_backtesting(
    strategy_class=MyBollingDayStrategy, 
    setting={}, 
    vt_symbol="j99.DCE",
    interval="1m", 
    start=datetime(2010, 1, 1), 
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=1,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
    )
df3 = run_backtesting(
    strategy_class=MyBollingDayStrategy, 
    setting={}, 
    vt_symbol="rb888.SHFE",
    interval="1m", 
    start=datetime(2010, 1, 1), 
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=1,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
    )

df4 = run_backtesting(
    strategy_class=MyBollingDayStrategy, 
    setting={}, 
    vt_symbol="i99.DCE",
    interval="1m", 
    start=datetime(2010, 1, 1), 
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=1,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
    )

df5 = run_backtesting(
    strategy_class=MyBollingDayStrategy, 
    setting={}, 
    vt_symbol="m99.CFFEX",
    interval="1m", 
    start=datetime(2010, 1, 1), 
    end=datetime(2020, 4, 30),
    rate=0.3/10000,
    slippage=1,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
    )

dfp = df1+df2+df3+df4+df5
dfp =dfp.dropna() 
show_portafolio(dfp)    