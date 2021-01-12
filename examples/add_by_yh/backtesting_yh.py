#%%
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.my_bolling_strategy import (
    MyBollingStrategy,
)
from vnpy.app.cta_strategy.strategies.my_bolling_multipos_strategy import (
    MyBollingMultiPosStrategy,
)
from vnpy.app.cta_strategy.strategies.my_bolling_day_strategy import (
    MyBollingDayStrategy,
)
from vnpy.app.cta_strategy.strategies.my_bolling_15min_strategy import (
    MyBolling15MinStrategy,
)
from datetime import datetime

#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2010, 4, 16),
    end=datetime(2012, 4, 16),
    rate=0.3/10000,
    slippage=1,
    size=10,
    pricetick=0.2,
    capital=1_000_000,
)
engine.add_strategy(MyBollingDayStrategy, {})

#%%
engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()

'''
setting = OptimizationSetting()
setting.set_target("sharpe_ratio")
setting.add_parameter("bollWindow15min", 20, 30, 1)
#setting.add_parameter("atr_ma_length", 10, 30, 1)

engine.run_optimization(setting)
'''