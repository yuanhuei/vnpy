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
from vnpy.app.cta_strategy.strategies.my_kama_3min_strategy import (
    MyKama3MinStrategy,
)
from datetime import datetime
'''
# 交易所类型
EXCHANGE_SSE = 'SSE'       # 上交所
EXCHANGE_SZSE = 'SZSE'     # 深交所
EXCHANGE_CFFEX = 'CFFEX'   # 中金所
EXCHANGE_SHFE = 'SHFE'     # 上期所
EXCHANGE_CZCE = 'CZCE'     # 郑商所
EXCHANGE_DCE = 'DCE'       # 大商所
EXCHANGE_SGE = 'SGE'       # 上金所
'''
#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="pvc99.DCE", 
    #橡胶ru99.CFFEX,焦炭j99.DCE,螺纹钢rb888.SHFE,铜cu888.SHFE,鸡蛋jd99.DCE,铁矿石i99.DCE,豆粕m99.CFFEX,玉米c99.DCE
    #郑醇ma99.CZCE,pp99.DCE,pvc99.DCE,pta99.CZCE，al99.SHFE,zn99.SHFE
    interval="1m",
    start=datetime(2010, 1, 16),
    end=datetime(2020, 5, 16),
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
setting.add_parameter("bollWindow15min", 25, 27, 1)
setting.add_parameter("entryDev15min", 2, 3, 1)

engine.run_ga_optimization(setting)
'''