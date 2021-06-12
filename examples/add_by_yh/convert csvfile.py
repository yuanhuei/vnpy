import csv
from datetime import datetime
from typing import List, Dict, Tuple

from vnpy.trader.engine import BaseEngine, MainEngine, EventEngine
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.database import database_manager
from vnpy.trader.rqdata import rqdata_client

    
def covertfile_5MinTo1Min():

    file_path='d:\\vnpy\\TExHisData_pta99.csv'
    symbol="rb888"
    exchange=Exchange.SHFE
    interval=Interval.MINUTE
    date_head="Date"
    time_head="Time"
    open_head="Open"
    high_head="High"
    low_head="Low"
    close_head="Close"
    volume_head="Volume"
    open_interest_head="Amount"
    datetime_format='%Y-%m-%d %H:%M:%S'
    """"""
    with open(file_path, "rt") as f:
        buf = [line.replace("\0", "") for line in f]

    reader = csv.DictReader(buf, delimiter=",")

    bars = []
    start = None
    count = 0

    for item in reader:
        ''' 
        if datetime_format:
            dt = datetime.strptime(item[datetime_head], datetime_format)
        else:
            dt = datetime.fromisoformat(item[datetime_head])
        '''
       
        open_interest = item.get(open_interest_head, 0)
        
        time_hour=item[time_head][:-6]
        time_minute=item[time_head][-5:-3]
        time_second=item[time_head][-2:]       
        if time_minute=='00':
            i=0
            while i<5:
                #i=i+1
                
                if time_hour=='00':
                    time='23'+':'+str(55+i)+':'+time_second
                else:
                    time=str(int(time_hour)-1)+':'+str(55+i)+':'+time_second
                dt=datetime.strptime(item[date_head]+" "+time, datetime_format)

                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    interval=interval,
                    volume=item[volume_head],
                    open_price=item[open_head],
                    high_price=item[high_head],
                    low_price=item[low_head],
                    close_price=item[close_head],
                    open_interest=open_interest,
                    gateway_name="DB",
                    )
                bars.append(bar)
                i=i+1
                
        else:
            i=5
            while i>0:

                time=time_hour+':'+str(int(time_minute)-i)+':'+time_second
                dt=datetime.strptime(item[date_head]+" "+time, datetime_format)
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    interval=interval,
                    volume=item[volume_head],
                    open_price=item[open_head],
                    high_price=item[high_head],
                    low_price=item[low_head],
                    close_price=item[close_head],
                    open_interest=open_interest,
                    gateway_name="DB",
                    )
                bars.append(bar) 
                i=i-1

            
             
        # do some statistics
    '''     count += 1
        if not start:
            start = bar.datetime
    end = bar.datetime
    '''
    fieldnames = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_interest"
    ]
    file_path='d:\\vnpy\\TExHisData_pta991.csv'
    try:
        with open(file_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()

            for bar in bars:
                d = {
                    "datetime": bar.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": bar.open_price,
                    "high": bar.high_price,
                    "low": bar.low_price,
                    "close": bar.close_price,
                    "volume": bar.volume,
                    "open_interest": bar.open_interest,
                }
                writer.writerow(d)

        return True
    except PermissionError:
        return False
    
def covertfile_Day():

    file_path='d:\\vnpy\\TExHisData_rbDay.csv'
    symbol="rb888"
    exchange=Exchange.SHFE
    interval=Interval.MINUTE
    date_head="Date"
    time_head="Time"
    open_head="Open"
    high_head="High"
    low_head="Low"
    close_head="Close"
    volume_head="Volume"
    open_interest_head="Amount"
    datetime_format='%Y-%m-%d %H:%M:%S'
    """"""
    with open(file_path, "rt") as f:
        buf = [line.replace("\0", "") for line in f]

    reader = csv.DictReader(buf, delimiter=",")

    bars = []
    start = None
    count = 0

    for item in reader:
                
        #time=time_hour+':'+str(int(time_minute)-i)+':'+time_second
        open_interest = item.get(open_interest_head, 0)
        time="09:00:00"
        dt=datetime.strptime(item[date_head]+" "+time, datetime_format)
        bar = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=dt,
            interval=interval,
            volume=item[volume_head],
            open_price=item[open_head],
            high_price=item[high_head],
            low_price=item[low_head],
            close_price=item[close_head],
            open_interest=open_interest,
            gateway_name="DB",
            )
        bars.append(bar)         
  
             
        # do some statistics
    '''     count += 1
        if not start:
            start = bar.datetime
    end = bar.datetime
    '''
    fieldnames = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_interest"
    ]
    file_path='d:\\vnpy\\TExHisData_rbDay1.csv'
    try:
        with open(file_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()

            for bar in bars:
                d = {
                    "datetime": bar.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": bar.open_price,
                    "high": bar.high_price,
                    "low": bar.low_price,
                    "close": bar.close_price,
                    "volume": bar.volume,
                    "open_interest": bar.open_interest,
                }
                writer.writerow(d)

        return True
    except PermissionError:
        return False
    
if __name__ == "__main__":
    '''main()'''
    covertfile_5MinTo1Min()
    #covertfile_Day()
    print("finished")
   