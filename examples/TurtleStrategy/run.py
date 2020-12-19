#%matplotlib inline
import sys
sys.path.insert(0,r"C:\Users\yuanh\Documents\GitHub\vnpy")
print('sys.path=',sys.path)
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

from turtleEngine import BacktestingEngine


engine = BacktestingEngine()
engine.setPeriod(datetime(2014, 1, 1), datetime(2018, 12, 30))
engine.initPortfolio('setting.csv', 10000000)

engine.loadData()
engine.runBacktesting()
engine.showResult()

tradeList = engine.getTradeData('000300')
for trade in tradeList:
    print ('%s %s %s %s @%s' %(trade.vtSymbol, trade.direction, trade.offset,trade.volume, trade.price))