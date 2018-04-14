import pika
import json
import time
from quotation import CFutureMarketData
from tradingContext import DBCommand

#类似抽象类，子类CMockTickQuotation 从文件中读行情，子类CMockMinuteQuoatation从数据库中获取行情
class CMockQuotation:
    quotation_type = ''
    connection = None
    channel = None
    tradeDate = ''
    instrumentID = ''

    def handle(self):
        pass

    def send(self):
        pass

class CMockTickQuotation(CMockQuotation):
    quotation_type = 'T'
    root_dir = 'q:\\csv\\'
    file_fullname = ''

    def __init__(self):

        self.quotation_type = 'T'

    def handle(self,_line):
        field = _line.split(',')
        _quotation = CFutureMarketData()
        _quotation.type = 'T'  # T-Tick，M-分钟，5M=5分钟，D-日线
        _quotation.instrumentID = field[1]
        _quotation.actionDay = field[0][0:8]
        _quotation.lastPrice = float(field[2])
        _quotation.volume = float(field[3])
        _quotation.amount = float(field[4])
        _quotation.bidPrice1 = float(field[5])
        _quotation.bidVolume1 = float(field[6])
        _quotation.askPrice1 = float(field[7])
        _quotation.askVolume1 = float(field[8])
        _quotation.turnover = 0.0  # @todo
        _quotation.openInterest = float(field[9])
        _quotation.averagePrice = float(field[10])  # 均价，上期所的在使用时，要注意是否需要处理每手乘数
        _quotation.settlementPrice = float(field[
                                               11])  # 本次结算价,@todo (min(99999999, pDepthMarketData->settlementPrice) == 99999999)? 0:pDepthMarketData->settlementPrice
        _quotation.closePrice = 0.0  # 今收盘 @todo
        _quotation.openPrice = float(field[12])
        _quotation.highPrice = float(field[13])
        _quotation.lowPrice = float(field[14])
        _quotation.upperLimitPrice = float(field[15])  # 涨停板价
        _quotation.lowerLimitPrice = float(field[16])  # 跌停板价
        _quotation.updateTime = field[0][9:17]
        _quotation.updateMillisec = int(field[0][field[0].find('.')+1:])


        # 对象转化为字典
        _dict = _quotation.__dict__
        _quotation_Json = json.dumps(_dict)
        return _quotation_Json


    def send(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='hello')
        self.file_fullname =  self.root_dir+(self.tradeDate)+('\\')+(self.instrumentID)+('.csv')
        print(self.file_fullname)
        fp_md =  open(self.file_fullname,'r')
        t = time.time()
        line = fp_md.readline().strip()
        self.channel.basic_publish(exchange='', routing_key='hello', body='exchangeInstrumentStatus|2')
        while len(line) > 0:
            self.channel.basic_publish(exchange='', routing_key='hello', body='CFutureMarketData|'+ self.handle(line))

            line = fp_md.readline()
        self.channel.basic_publish(exchange='', routing_key='hello', body='exchangeInstrumentStatus|6')
        fp_md.close();
        print('Total Time:')

        print(time.time() - t)
        self.connection.close()


class CMockMinuteQuotation(CMockQuotation):
    quotation_type = 'M'


    def __init__(self):

        self.quotation_type = 'M'

    def handle(self,_line):
        field = _line
        _quotation = CFutureMarketData()
        _quotation.type = 'M'  # T-Tick，M-分钟，5M=5分钟，D-日线
        _quotation.instrumentID = field[2]
        _quotation.actionDay = field[15]
        _quotation.lastPrice = float(field[4])
        _quotation.volume = float(field[7])

        _quotation.closePrice = float(field[4])   # 今收盘 @todo
        _quotation.openPrice = float(field[3])
        _quotation.highPrice = float(field[5])
        _quotation.lowPrice = float(field[6])

        # 按照最低价 作为askprice，最高价作为bidprice,因为模拟撮合的时候，如果买，按照>askprice+1*tick作为判断条件,因而与tick行情不同，是倒挂的
        _quotation.bidPrice1 = _quotation.lowPrice
        _quotation.bidVolume1 = 0
        _quotation.askPrice1 = _quotation.highPrice
        _quotation.askVolume1 = 0
        _quotation.turnover = float(field[9])
        _quotation.openInterest = float(field[10])
        _quotation.averagePrice = float(field[9]) / float(field[8])  # 均价,todo
        _quotation.settlementPrice = float(field[9]) / float(field[8])  # 本次结算价,@todo (min(99999999, pDepthMarketData->settlementPrice) == 99999999)? 0:pDepthMarketData->settlementPrice

        #todo 涨跌停，目前数据表中没有，需要另外取
        _quotation.upperLimitPrice = _quotation.closePrice * 2   # 涨停板价
        _quotation.lowerLimitPrice = 0  # 跌停板价

        _quotation.updateTime = str(field[11]) [:2] + ':' + str(field[11]) [2:4] + ':' +str(field[11]) [4:6]
        #分钟线，暂不需要毫秒信息，只是为了保留此字段，赋值，不至于出错
        _quotation.updateMillisec = 0  #int(field[0][field[0].find('.')+1:-1])


        # 对象转化为字典
        _dict = _quotation.__dict__
        _quotation_Json = json.dumps(_dict)
        return _quotation_Json


    def send(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='hello')

        dbcommand = DBCommand()
        dbcommand.prepare("select TRADE_DATE      ,\
            TRADE_TIME      ,\
            INST_CODE       ,\
            OPEN_PRICE      ,\
            CLOSE_PRICE     ,\
            HIGH_PRICE      ,\
            LOW_PRICE       ,\
            VOLUME          ,\
            TOTAL_VOLUME    ,\
            TURNOVER        ,\
            OPEN_INTEREST   ,\
            UPDATE_TIME     ,\
            TIME_INDEX      ,\
            STATUS          ,\
            KEY_CODE        ,\
            ACTION_DAY    from futureinfo.quctp_future_minute_prices p where  p.inst_code = :1 and p.trade_date = :2 order by p.time_index")
        rows = dbcommand.execute(None,        (self.instrumentID, self.tradeDate))
        t = time.time()



        for line in rows:
            self.channel.basic_publish(exchange='', routing_key='hello', body='CFutureMarketData|'+ self.handle(line))




        print('Total Time:')

        print(time.time() - t)
        self.connection.close()



if __name__ == "__main__":

    mock = CMockTickQuotation()
    mock.instrumentID = 'ru1805'
    mock.tradeDate = '20180323'
    mock.send()



    '''
    mock = CMockMinuteQuotation()
    mock.instrumentID = 'ag1706'
    mock.tradeDate = '20170227'
    mock.send()
    '''
