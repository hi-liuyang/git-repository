#每次程序运行的运行环境
import logging
import logging.config
import os
import re
import cx_Oracle
import threading
import math
import json
import pika
#暂时没用到
from sqlalchemy import *
from sqlalchemy.sql import select
from sqlalchemy.schema import *
from sqlalchemy.orm import sessionmaker

from CTPAPIStructWrapper import *
from CTPAPIDataTypeWrapper import *
from TradeStruct import *
from quotation import CKLine,CKBar,CFutureMarketData,CInstrument

class DBCommand:

    db= None
    cursor = None
    db_clock = None
    #sqlalchemy
    db_engine = None
    DB_Session = None
    db_session = None

    def __init__(self):
        if self.db == None :
            self.getInstance();
        #这个锁好像要仔细想想是否需要
        self.db_lock = threading.Lock()

        self.db_engine=create_engine('oracle://quant:quant@192.168.1.100:1521/windinfo', echo=True)


        self.DB_Session = sessionmaker(bind=self.db_engine)
        self.db_session = self.DB_Session()

    def getInstance(self):
        self.db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
        self.cursor = self.db.cursor()

    #cx_oracle
    def prepare(self, *args, **kwargs ):#
        #print(sqlstr)
        if self.db == None :
            self.getInstance();

        self.cursor.prepare( *args, **kwargs)

    #cx_oracle ， select语句调用此方法
    #
    def execute(self, sqlstr,*args, **kwargs):
        if self.db == None :
            self.getInstance();

        if self.db_lock.acquire():
            self.cursor.execute(sqlstr,*args,**kwargs)
            rows = self.cursor.fetchall()
            self.db_lock.release()
        return rows

    # update delete
    def executeUpdate(self, sqlstr, *args, **kwargs):
        if self.db == None:
            self.getInstance();

        if self.db_lock.acquire():
            try:
                self.cursor.execute(sqlstr, *args, **kwargs)
                self.db.commit()

            finally:
                self.db_lock.release()


class CContext:
    # 生产环境 PRODUCT，还是模拟环境 MOCK
    runType = 'MOCK'

    #初始化日志配置
    '''
    logging.basicConfig(filename=os.path.join(os.getcwd()+'\log', 'log.txt'), level = logging.DEBUG, filemode = 'a', format = '%(asctime)s - %(levelname)s: %(message)s - [%(filename)s:%(lineno)s]')
    logging.debug('this is a message')
    # 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
    console = logging.StreamHandler()
    #console.parent is root_logger
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logging.info('print to Console')
    '''
    CONF_LOG = "./log/logging.conf"
    logging.config.fileConfig(CONF_LOG);    # 采用配置文件

    #logger = logging.getLogger("app")
    #logger.debug("app logger initialized")




#每个交易日运行的上下文环境
class CTradingContext(CContext) :

    tradingDate = ''
    instrumentID = ''
    OrderRef = 0
    match_no = 0
    dict_Strategy = {}
    tradingCommand = None

    def __init__(self, tradingDate, instrumentID):
        self.tradingDate = tradingDate
        self.instrumentID = instrumentID
        self.dict_Strategy = {}
        self.tradingCommand = None
        self.match_no = 0
        self.OrderRef = 0
        # 初始化合约，对应于具体的策略，tradingContract将会重新赋值
        if instrumentID != None :
            self.instrument = CInstrument(instrumentID)
            self.tradingContract = CTradingContract(instrumentID)


    # value : 策略的实例，startegy：策略的名称，以后用
    def addStrategy(self, value=None, strategy='strategy'):

        if len(self.dict_Strategy) == 0 :
            self.dict_Strategy[strategy] = value
        else:
            logging.error('only one strategy is ok now')

    #暂时只考虑一个策略 todo,以后需要考虑扩展
    def getStrategy(self, strategy='strategy'):
        for item in self.dict_Strategy.values():
            return item

    def getOrderRef(self):
        self.OrderRef = self.OrderRef + 1
        return str(self.OrderRef)

    def getMatchNo(self):
        self.match_no = self.match_no + 1
        return str(self.match_no)

    #tradingCommand 是否应该放在context中
    def getTradingCommand(self):
        if self.tradingCommand == None :
            self.tradingCommand = CTradingCommand(self)

        self.tradingCommand.tradingContext = self
        return self.tradingCommand

class CStrategy:
    # key为instrumentid，value为CTradingContract对象
    dict_TradingContract = {}

    tradingContext = None

    #一天的最大交易次数
    maxTradeNum = 5
    # 一天的最大敞口手数
    maxExposure = 5
    # 一天的最大亏损，0.1代表10%的亏损
    maxLossAmount = 0.1



    def getTradingContract(self, instrumentID):
        return  self.dict_TradingContract[instrumentID]

    #向dict中增加，如果已有就修改
    def addTradingContract(self, instrumentID, tradingContract):
        self.dict_TradingContract[instrumentID] = tradingContract

    #初始化交易合约信息,每日交易前调用
    def initialTradingContract(self, _tradingContract):
        pass

    def __init__(self):
        self.tradingContext = None
        self.dict_TradingContract = {}

    #交易前准备，比如构建第一根5分钟线，在5分钟时，将当日的可交易状态置为True
    def prepareForTrading(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)
        _tradingContract.dayTradingFlag = True  # 初始值为0
        _tradingContract.preparedFlag = True  # 初始值为0

    #根据每一笔行情判断是否触发交易
    def checkQuotation(self,quotation):
        pass

    # 模拟成交,
    def mockTrade(self, tradingContract, quotation):
        # 如果是mock环境，如果有未全部成交的委托，则需要检查是否生成模拟的成交单

        if self.tradingContext.runType == 'MOCK':
            if tradingContract.positionField.long_order == 0 and tradingContract.positionField.short_order == 0:
                return

            for _pOrder in tradingContract.dict_Order.values():
                if _pOrder.matched_volume < _pOrder.volume and _pOrder.inst_code == quotation.instrumentID:
                    # 如果方向为买，且买价大于行情的卖一价，则生成一条成交
                    if (_pOrder.bs_flag == 'B' and _pOrder.price >= quotation.askPrice1) or (
                            _pOrder.bs_flag == 'S' and quotation.bidPrice1 >= _pOrder.price):
                        _pTrade = CFutureMatch()
                        _pTrade.inst_code = _pOrder.inst_code
                        _pTrade.trade_date = _pOrder.trade_date
                        _pTrade.trade_time = quotation.updateTime
                        if _pOrder.bs_flag == 'B':
                            _pTrade.price = quotation.askPrice1 #_pOrder.price
                        if _pOrder.bs_flag == 'S':
                            _pTrade.price = quotation.bidPrice1  # _pOrder.price
                        _pTrade.volume = _pOrder.volume - _pOrder.matched_volume

                        _pTrade.local_order_no = _pOrder.local_order_no
                        _pTrade.match_exch_no = self.tradingContext.getMatchNo()
                        _pTrade.bs_flag = _pOrder.bs_flag
                        _pTrade.eo_flag = _pOrder.eo_flag

                        self.tradingContext.getTradingCommand().rtnTrade(_pTrade)
                        # 每个tick只处理一笔委托的模拟成交
                        return _pTrade



#交易策略相关合约信息
class CTradingContract(CInstrument):
    #初始化合约信息

    today_PriceRange = 0.0  # 价格区间
    avgPrice_2130 = 0.0  # 开盘半小时的均价

    buyOpenPrice = 0.0  # 买开仓，价位1
    sellOpenPrice = 0.0  # 卖开仓，价位1
    buyClosePrice = 0.0  # 买平仓，价位1
    sellClosePrice = 0.0  # 卖平仓，价位1

    sellStopLoss = 0.0  # 对应买开仓的，卖出止损价1
    buyStopLoss = 0.0  # 对应卖开仓的，买入止损价1

    dayTradingFlag = False  # 单日是否可以继续开仓；每日开始前半小时，如21:30之前，不开仓，如果发生平仓后，当日则不再交易；0- 不可交易； 1- 可以继续开仓； 2- 只可平仓，不可开仓
    preparedFlag = False  # 当日交易的准备是否已经完成，即9点半的各个价位计算是否已经完成

    exchangeInstrumentStatus = ''  # 合约交易状态，CTP推送
    forceFlag = 0  # 强平标志 0- 非强平 1 - 强平 2 - 收市前平仓

    position = 0  # 当前持仓，在委托时标记，
    buyorSell = ''  # '0'- Buy, '1'- Sell

    memo = ''  # 备注

    OrderRef = 0; # 类似本地报单号的起始
    ##交易相关信息
    # 委托
    # 委托单号，供撤单用
    direction = ''  # 开仓方向 0 - 买 1 - 卖
    volumeTotalOriginal = 0  # 委托手数
    volumeTraded = 0  # 成交手数，在收到成交回报时更改
    parkedVolume = 0  # 撤单手数
    volumeTotal = 0  # /剩余数量

    # 平仓
    # 平仓单号，供撤单用
    close_VolumeTotalOriginal = 0  # 平仓手数
    close_VolumeTraded = 0  # 平仓成交手数
    close_ParkedVolume = 0  # 平仓撤单手数
    close_VolumeTotal = 0  # /剩余数量

    #每个合约一天可以交易的次数,与策略中的maxTradeNum对应
    tradeNum = 0

    kline = None
    #委托,key 为本地报单号，值为class CFutureOrder
    dict_Order = {}
    #成交，key 为成交编号_委托单号，值为class CFutureOrder
    dict_Trade = {}
    #持仓
    positionField = None



    def initialContract(self,instrumentID):
        pass

    def __init__(self,instrumentID):
        CInstrument.__init__(self, instrumentID)
        self.instrumentID = instrumentID
        self.positionField = CFuturePosition(instrumentID)
        self.dict_Order = {}
        self.dict_Trade = {}
        self.kline = CKLine(self.instrumentID,'T')
        self.OrderRef = 0



        # 初始化合约基本信息

        self.dayTradingFlag = False
        self.preparedFlag = False
        self.position = 0
        self.volumeTraded = 0
        self.avgPrice_2130 = 0
        self.buyorSell = '9'  # 可能的值为 '0'  或 '1', '9' 代表初始的情况，如果系统尚未触发开仓，而在其他工具开仓，则系统内部的各值都不变
        self.exchangeInstrumentStatus = '0'


        self.initialContract(instrumentID)




#交易执行
class CTradingCommand:
    #单实例，@todo
    instance = None
    tradingContext = None

    '''
    def __init__(self):
        pass
    '''

    def __init__(self,tradingContext):
        self.tradingContext = tradingContext

    def getInstance(self):

        return self.instance

    def setTradingContext(self, tradingContext):
        self.tradingContext = tradingContext


    def openPosition(self,pInputOrder):

        #_tradingContract.tradeNum++
        #开仓委托，调整long_order 和short_order , '0'- 买
        if pInputOrder.Direction == '0':
            self.tradingContext.getStrategy().getTradingContract(pInputOrder.InstrumentID).positionField.long_order =+ pInputOrder.VolumeTotalOriginal
        else:
            self.tradingContext.getStrategy().getTradingContract(
                pInputOrder.InstrumentID).positionField.short_order = + pInputOrder.VolumeTotalOriginal

        self._inputOrder(pInputOrder)


    def closePosition(self,pInputOrder):

        self._inputOrder(pInputOrder)
        #平仓后，需要等恢复状态后，才可以重新进行交易；否则有可能出现平仓后又立即开仓的情况
        #self.tradingContext.getStrategy().getTradingContract(pInputOrder.InstrumentID).dayTradingFlag = False


    def forcePosition(self,pInputOrder):
        #logging.info('forcePosition: ' )
        self._inputOrder(pInputOrder)

        #self.tradingContext.getStrategy().getTradingContract(pInputOrder.InstrumentID).dayTradingFlag = False
    def timeToClosePosition(self,pInputOrder):
        #logging.info('timeToClosePosition: ' )
        self._inputOrder(pInputOrder)

        #self.tradingContext.getStrategy().getTradingContract(pInputOrder.InstrumentID).dayTradingFlag = False
    #委托
    def _inputOrder(self, pInputOrder):
        assert isinstance(pInputOrder, CThostFtdcInputOrderField), "_pInputOrder is not a CThostFtdcInputOrderField instance"
        #logging.info(pInputOrder.__dict__)
        _tradingContract = self.tradingContext.getStrategy().getTradingContract(pInputOrder.InstrumentID)
        # 判断此笔委托是否已经处理，如果未处理则继续：
        if _tradingContract.dict_Order.get(pInputOrder.OrderRef) == None:
            _local_order_no = self.tradingContext.getOrderRef()
            pInputOrder.OrderRef = _local_order_no

            _tradingContract.dict_Order[_local_order_no] =  CFutureOrder(pInputOrder)
            #CTP的inputOrderField中没有tradingdate的字段
            _tradingContract.dict_Order[_local_order_no].trade_date = self.tradingContext.tradingDate

    #撤单
    def rspOrderAction(self):
        pass

    #委托回报
    def rtnOrder(self,pOrder):
        pass

    #成交回报
    def rtnTrade(self, pTrade):

        _tradingContract = self.tradingContext.getStrategy().getTradingContract(pTrade.inst_code)


        #判断此笔成交回报是否已经处理，如果未处理则继续：
        if _tradingContract.dict_Trade.get(pTrade.match_exch_no+ '_'+pTrade.local_order_no) == None :
            # 根据原委托号找到委托，更新委托中的成交数量
            if _tradingContract.dict_Order.get(pTrade.local_order_no) != None:
                _tradingContract.dict_Order[pTrade.local_order_no].matched_volume = _tradingContract.dict_Order[pTrade.local_order_no].matched_volume + pTrade.volume

            #增加成交, 以成交单号_委托单号，合起来作为key
            _tradingContract.dict_Trade[pTrade.match_exch_no + '_' + pTrade.local_order_no] = pTrade

            #调整持仓
            if pTrade.bs_flag == 'B':
                if pTrade.eo_flag == 'O':
                    _tradingContract.positionField.long_posi = _tradingContract.positionField.long_posi + pTrade.volume
                    _tradingContract.positionField.open_price = pTrade.price
                    _tradingContract.volumeTraded = _tradingContract.volumeTraded + pTrade.volume


                else :
                    if     pTrade.eo_flag == 'C':
                        _tradingContract.positionField.short_posi = _tradingContract.positionField.short_posi - pTrade.volume

                        _tradingContract.positionField.close_price = pTrade.price
                        _tradingContract.volumeTraded = _tradingContract.volumeTraded - pTrade.volume

                        _tradingContract.positionField.short_order = _tradingContract.positionField.short_order - pTrade.volume

            else:
                if pTrade.bs_flag == 'S':
                    if pTrade.eo_flag == 'O':
                        _tradingContract.positionField.short_posi = _tradingContract.positionField.short_posi + pTrade.volume
                        _tradingContract.positionField.open_price = pTrade.price
                        _tradingContract.volumeTraded = _tradingContract.volumeTraded + pTrade.volume
                    else:
                        #如果是卖平仓，则原来为空头持仓，所以减short_posi
                        if pTrade.eo_flag == 'C':
                            _tradingContract.positionField.long_posi = _tradingContract.positionField.long_posi - pTrade.volume
                            _tradingContract.positionField.close_price = pTrade.price
                            _tradingContract.volumeTraded = _tradingContract.volumeTraded - pTrade.volume
                            _tradingContract.positionField.long_order = _tradingContract.positionField.long_order - pTrade.volume
            #写入数据库
            dbcommand = DBCommand()
            dbcommand.prepare("insert into  t_future_match     \
                                 (                              \
                                       trade_date            ,  \
                                       trade_time            ,  \
                                       inst_code             ,  \
                                       bs_flag 			     ,  \
                                       eo_flag 			     ,  \
                                       price				 ,  \
                                       volume 				 ,  \
                                       match_exch_no         ,  \
                                       order_local_no        ,  \
                                       order_exch_no         ,  \
                                       exch_code             ,  \
                                       app_id                ,  \
                                       create_time           ,  \
                                       seq_no                   \
                                                                \
                                )                               \
                                values (                        \
                                       :trade_date            , \
                                       :trade_time            , \
                                       :inst_code             , \
                                       :bs_flag 			  , \
                                       :eo_flag 			  , \
                                       :price				 ,  \
                                       :volume 				 ,  \
                                       :match_exch_no         , \
                                       :order_local_no        , \
                                       :order_exch_no         , \
                                       :exch_code             , \
                                       :app_id                , \
                                       :create_time           , \
                                       :seq_no                  \
                                )")
            rows = dbcommand.executeUpdate(None,        {

                        'trade_date': pTrade.trade_date,
                        'trade_time': pTrade.trade_time,
                         'inst_code':pTrade.inst_code,
                         'bs_flag' 		:pTrade.bs_flag 		 ,
                         'eo_flag' 		  :pTrade.eo_flag 		 ,
                         'price'			  :pTrade.price			 ,
                         'volume' 		  :pTrade.volume 		 ,
                         'match_exch_no'   :pTrade.match_exch_no   , 'order_local_no'  :pTrade.order_local_no  ,
                         'order_exch_no'   :pTrade.order_exch_no   ,
                         'exch_code'       :pTrade.exch_code       ,
                         'app_id'          :pTrade.app_id          ,
                         'create_time'     :pTrade.create_time     ,
                         'seq_no'          :pTrade.seq_no
            })




class CMdHandler:
    tradingContext = None
    _connection = None
    _channel = None
    _quotation = None



    def __init__(self,_context):
        self.tradingContext = _context;
        print(_context)

        self._connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='hello')
        self._channel.basic_consume(self.callback, queue='hello', no_ack=True)

    def callback(self,ch, method, properties, body):
        _quotation = CFutureMarketData()
        # _dict = body
        # print(body)
        _str = str(body, 'utf-8').split('|')
        if _str[0] == 'CFutureMarketData' :
            _quotation.__dict__ = json.loads(_str[1])
            self.handleQuotation(_quotation)
        elif  _str[0] == 'exchangeInstrumentStatus': # TFtdcInstrumentStatus  6- 收盘，0- 开盘前，2- 连续交易
                if _str[1] == '6':
                    self._connection.close()

        else :
            print('body is not a CFutureMarketData/InstrumentStatus string:%s'%(body,))
        #print(_quotation.instrumentID + ',' + _quotation.updateTime + ',' + str(_quotation.lastPrice))

    def start_consuming(self):
        assert self._channel != None,"should not be None"
        self._channel.start_consuming()

    def handleQuotation(self, quotation):
        # 合约状态为连续交易
        assert  isinstance(quotation, CFutureMarketData), 'handleQuotation parameter is not a instance of CFutureMarketData'

        _strategy = self.tradingContext.getStrategy()
        _tradingContract = self.tradingContext.getStrategy().getTradingContract(quotation.instrumentID)

        # 生成分钟线
        _tradingContract.kline.handle(quotation)

        if (_tradingContract.exchangeInstrumentStatus == '2') :
            # 21:30:00，确定当日的开仓价格
            if (_tradingContract.preparedFlag == False )  :
                _strategy.prepareForTrading(quotation)
            # 在可交易区间，根据行情和仓位，判断是否开仓或平仓
            else :
                _strategy.checkQuotation(quotation)


if __name__ == "__main__":
    pass
