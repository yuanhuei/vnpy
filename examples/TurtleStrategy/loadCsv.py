# encoding: UTF-8
import sys
sys.path.insert(0,r"C:\Users\yuanh\Documents\GitHub\vnpy")
print('sys.path=',sys.path)
from csv import DictReader
from datetime import datetime
from pymongo import MongoClient

from vnpy.trader.object import BarData

from turtleEngine import DAILY_DB_NAME


#----------------------------------------------------------------------
def loadCsv(filename):
    """"""
    symbol = filename.split('.')[0]
    
    mc = MongoClient()
    db = mc[DAILY_DB_NAME]
    collection = db[symbol]
    
    with open(filename) as f:
        r = DictReader(f)
        for d in r:
            bar = BarData(DAILY_DB_NAME)
            bar.datetime = datetime.strptime(d['date'], '%Y/%m/%d')
            bar.symbol = symbol
            bar.open_price = float(d['open'])
            bar.high_price = float(d['high'])
            bar.low_price = float(d['low'])
            bar.close_price = float(d['close'])
            bar.volume= int(d['volume'])
        
            collection.insert(bar.__dict__)
    
if __name__ == '__main__':
    loadCsv('000300.csv')
    loadCsv('000905.csv')