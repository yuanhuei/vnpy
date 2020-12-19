from vnpy.trader.rqdata import rqdata_client
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import HistoryRequest
from datetime import datetime

symbols = {
    "SHFE": ["CU", "AL", "ZN", "PB", "NI", "SN", "AU", "AG", "RB", "WR", "HC", "SS", "BU", "RU", "NR", "SP", "SC", "LU", "FU"],
    "DCE": ["C", "CS", "A", "B", "M", "Y", "P", "FB","BB", "JD", "RR", "L", "V", "PP", "J", "JM", "I", "EG", "EB", "PG"],
    "CZCE": ["SR", "CF", "CY", "PM","WH", "RI", "LR", "AP","JR","OI", "RS", "RM", "TA", "MA", "FG", "SF", "ZC", "SM", "UR", "SA", "CL"],
    "CFFEX": ["IH","IC","IF", "TF","T", "TS"]
}
​
symbol_type = "99"

start_date = datetime(2005,1,1)
end_date = datetime(2020,9,10)


def load_data(req):
    data = rqdata_client.query_history(req)
    database_manager.save_bar_data(data)
    print(f"{req.symbol}历史数据下载完成")
​
for exchange, symbols_list in symbols.items():
    for s in symbols_list:
        req = HistoryRequest(
         symbol=s+symbol_type,
     exchange=Exchange(exchange),
     start=start_date,
     interval=Interval.DAILY,
     end=end_date,
     )
        load_data(req=req)