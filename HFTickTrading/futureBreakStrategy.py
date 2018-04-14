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
from CTPAPIStructWrapper import *
from CTPAPIDataTypeWrapper import *
from TradeStruct import *
from tradingContext import *
from datetime import datetime,timedelta
import time

class CFutureBreakStrategy(CStrategy) :
    #构造
    def __init__(self, tradingContext):
        self.tradingContext = tradingContext

        self.tradingContext.addStrategy(self, 'futureBreakStrategy')

    #初始化交易合约信息
    def initialTradingContract(self, _tradingContract):
        self.dict_TradingContract[_tradingContract.instrumentID] = _tradingContract
        _tradingContract.initialContract(_tradingContract.instrumentID)

        #初始化合约基本信息

        _tradingContract.dayTradingFlag = False
        _tradingContract.preparedFlag = False
        _tradingContract.position = 0
        _tradingContract.volumeTraded = 0
        _tradingContract.avgPrice_2130 = 0
        _tradingContract.buyorSell = '9' # 可能的值为 '0'  或 '1', '9' 代表初始的情况，如果系统尚未触发开仓，而在其他工具开仓，则系统内部的各值都不变
        _tradingContract.exchangeInstrumentStatus = '0'

        #暂时供测试用，实际应该从数据库中获取数据

        #如果以ag开头
        if (re.match(r'[\D]*',_tradingContract.instrumentID).group(0) == "ag"  ) :
            #pTradingContract->v_Today_PriceRange = 72.17; // 60.06; // 66.8; // 73.56; //
            _tradingContract.priceTick = 1
            _tradingContract.volumeMultiple = 15
            _tradingContract.volumeTotalOriginal = 5
            _tradingContract.productID = 'ag'

        dbcommand = DBCommand()
        dbcommand.prepare("select avg(high_price - low_price)  from ( \
            								 SELECT t.* FROM  \
            								 ( \
            										   select p.trade_dt, p.s_dq_high high_price ,p.s_dq_low low_price from winduser.ccommodityfutureseodprices  p \
            											  where substr(lower(p.s_info_windcode),1,    INSTR（p.s_info_windcode,'.',1,1）- 1)  = :1 and p.trade_dt < :2\
            											  order by p.trade_dt desc \
            								  )  t where rownum < :3 \
            						  )")
        rows = dbcommand.execute(None,        ('ag1706', self.tradingContext.tradingDate,22))
        _avgPrice_22d = rows[0][0];
        #print(_avgPrice_22d)
        rows = dbcommand.execute(None, ('ag1706', self.tradingContext.tradingDate, 6))
        _avgPrice_5d = rows[0][0];
        #print(_avgPrice_5d)
        rows = dbcommand.execute(None, ('ag1706', self.tradingContext.tradingDate, 2))
        _avgPrice_1d = rows[0][0];
        #print(_avgPrice_1d)
        _tradingContract.today_PriceRange = _avgPrice_22d * 0.1 + _avgPrice_5d * 0.7 + _avgPrice_1d * 0.2
        '''
        _tradingContract.today_PriceRange = max(_avgPrice_22d,_avgPrice_5d,_avgPrice_1d) * 0.7 \
                                            + min(_avgPrice_22d,_avgPrice_5d,_avgPrice_1d) *0.1 \
                                            + (_avgPrice_22d+_avgPrice_5d+_avgPrice_1d - max(_avgPrice_22d,_avgPrice_5d,_avgPrice_1d) - min(_avgPrice_22d,_avgPrice_5d,_avgPrice_1d)) * 0.2
        '''

    #接收行情
    def receiveQuotation(self,quotation):
        pass

    #根据21:30 行情，生成当日的各个触发价位
    def prepareForTrading(self, quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)
        if ( '21:29:59' <= quotation.updateTime) and (quotation.updateTime < '21:32:00') :
            _tradingContract.avgPrice_2130 = quotation.averagePrice / _tradingContract.volumeMultiple

            _tradingContract.buyOpenPrice = _tradingContract.avgPrice_2130 + _tradingContract.today_PriceRange / 2
            _tradingContract.sellClosePrice = _tradingContract.buyOpenPrice + _tradingContract.today_PriceRange
            _tradingContract.sellStopLoss = _tradingContract.buyOpenPrice - _tradingContract.today_PriceRange / 3

            _tradingContract.sellOpenPrice = _tradingContract.avgPrice_2130 - _tradingContract.today_PriceRange / 2
            _tradingContract.buyClosePrice = _tradingContract.sellOpenPrice - _tradingContract.today_PriceRange
            _tradingContract.buyStopLoss = _tradingContract.sellOpenPrice + _tradingContract.today_PriceRange / 3

            logging.debug(
                "CFutureBreakStrategy::prepareForTrading，_tradingContract->instrumentID=[%s]，_tradingContract.avgPrice_2130=[%f],priceRange=[%f]\n v_buyOpenPrice=[%f],v_sellClosePrice=[%f],v_SellStopLoss=[%f],\n v_sellOpenPrice=[%f],v_buyClosePrice=[%f],v_BuyStopLoss=[%f] \n"%
                (quotation.instrumentID, _tradingContract.avgPrice_2130, _tradingContract.today_PriceRange, _tradingContract.buyOpenPrice, _tradingContract.sellClosePrice,
                 _tradingContract.sellStopLoss, _tradingContract.sellOpenPrice, _tradingContract.buyClosePrice,
                 _tradingContract.buyStopLoss))

            if (_tradingContract.buyClosePrice <= quotation.lowerLimitPrice) :
                _tradingContract.buyClosePrice = quotation.lowerLimitPrice + 2 * _tradingContract.priceTick



            if (_tradingContract.sellClosePrice >= quotation.upperLimitPrice) :
                _tradingContract.sellClosePrice = quotation.upperLimitPrice - 2 * _tradingContract.priceTick




            # 设置好各点位后，当日可以交易
            if ((quotation.lastPrice < (_tradingContract.buyClosePrice + 5 * _tradingContract.priceTick))
                or (quotation.lastPrice > (_tradingContract.sellClosePrice - 5 * _tradingContract.priceTick))
                or (_tradingContract.sellClosePrice < (_tradingContract.buyOpenPrice + 10 * _tradingContract.priceTick))
                or (_tradingContract.buyClosePrice > (_tradingContract.sellOpenPrice - 10 * _tradingContract.priceTick))
                ) :
                logging.debug("CFutureBreakStrategy::prepareForTrading，_tradingContract->instrumentID=[%s]， _quotation.lastPrice=[%f]，did not trade today，\n " % (quotation.instrumentID, quotation.lastPrice))
                _tradingContract.dayTradingFlag = False  # 初始值为0
                _tradingContract.preparedFlag = False

            else :
                _tradingContract.dayTradingFlag = True  # 初始值为0
                _tradingContract.preparedFlag = True  # 初始值为0

                logging.info("CFutureBreakStrategy::prepareForTrading，_tradingContract->instrumentID=[%s]，avgPrice_2130=[%f], _quotation.lastPrice=[%f]，can trade now，\n " % (quotation.instrumentID, _tradingContract.avgPrice_2130, quotation.lastPrice))



    #根据行情、仓位，判断是否需要触发交易
    def checkQuotation(self, quotation):

        assert isinstance(quotation,
                          CFutureMarketData), 'handleQuotation parameter is not a instance of CFutureMarketData'
        _tradingContract = self.getTradingContract(quotation.instrumentID)
        _context = self.tradingContext
        _avgPrice = quotation.averagePrice / _tradingContract.volumeMultiple #@todo ， 改成通过_quotation.getAveragePrice函数获取
        _tradingCommand =  _context.getTradingCommand() #CTradingCommand(self.tradingContext)

        _tradingContract.sellClosePrice = min((_avgPrice +    _tradingContract.today_PriceRange /2  + _tradingContract.today_PriceRange ), quotation.upperLimitPrice - 2 * _tradingContract.priceTick)

        _tradingContract.buyClosePrice = max((
                                               _avgPrice - _tradingContract.today_PriceRange / 2 - _tradingContract.today_PriceRange  ), quotation.lowerLimitPrice + 2 * _tradingContract.priceTick)

        self.mockTrade(_tradingContract, quotation)


        # v_position == 0,当日尚未开仓，_tradingContract.dayTradingFlag >0 可以交易
        if ((_tradingContract.position == 0) and (_tradingContract.dayTradingFlag == True) and (_tradingContract.tradeNum < self.maxTradeNum)):
        # 如果时间在下午(21:00~21:30,09:00~09:15)，则不再开仓,其他时间可以
            if ((quotation.updateTime> "09:15:00" and quotation.updateTime< "14:25:00")
                or (quotation.updateTime> "21:30:20") or (quotation.updateTime< "02:15:00")):
            # 如果卖一价大于买开仓价,且小于卖平仓价
            #	_tradingContract.priceTick为滑点

                if ((quotation.askPrice1 > (
                    _tradingContract.buyOpenPrice - _tradingContract.priceTick * 0)) and (quotation.askPrice1 < (_tradingContract.sellClosePrice -  _tradingContract.priceTick * 5))):
                    _tradingContract.position = 1
                    _tradingContract.BuyorSell = '0'  #  THOST_FTDC_D_Buy  # '0'-Buy

                    # 以对手价委托
                    _pInputOrder =  CThostFtdcInputOrderField()

                    # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    _pInputOrder.InstrumentID =  quotation.instrumentID
                    _pInputOrder.LimitPrice = quotation.askPrice1 - _tradingContract.priceTick * 3
                    _pInputOrder.Direction = THOST_FTDC_D_Buy
                    _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTotalOriginal
                    _pInputOrder.CombOffsetFlag= "0"
                    # 有效期类型
                    _pInputOrder.TimeCondition =  THOST_FTDC_TC_IOC  # THOST_FTDC_TC_GFD - 当日生效，THOST_FTDC_TC_IOC - 立即完成，否则撤销，用于FAK，FOK
                    # 成交量类型
                    _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV  #
                    #pProducerTrade->Publish((void *) pInputOrder, 1, free_data_func_type1)



                    _tradingCommand.openPosition(_pInputOrder)

                    logging.info(quotation.__dict__)
                    '''
                    #挂单
                    _pInputOrder_1 = new CThostFtdcInputOrderField()

                    #初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    strcpy(_pInputOrder_1.InstrumentID, _quotation.instrumentID)
                    _pInputOrder_1.LimitPrice = _quotation.askPrice1 -  5 * _tradingContract.priceTick
                    _pInputOrder_1.Direction = THOST_FTDC_D_Buy
                    _pInputOrder_1.VolumeTotalOriginal = 1 #p_tradingContract->m_VolumeTotalOriginal
                    strcpy(_pInputOrder_1.CombOffsetFlag,"0")
                    # 有效期类型
                    _pInputOrder_1.TimeCondition = THOST_FTDC_TC_GFD #THOST_FTDC_TC_GFD - 当日生效，THOST_FTDC_TC_IOC - 立即完成，否则撤销，用于FAK，FOK
                    # 成交量类型
                    _pInputOrder_1.VolumeCondition = THOST_FTDC_VC_AV  #


                    pProducerTrade->Publish((void *) _pInputOrder_1, 1, free_data_func_type1)
                    '''



                # 如果买一价小于卖开仓价,PriceTick为滑点
                else:
                    if ((quotation.bidPrice1 < _tradingContract.sellOpenPrice + _tradingContract.priceTick * 0) and (quotation.bidPrice1 > _tradingContract.buyClosePrice + _tradingContract.priceTick * 5)):
                        _tradingContract.position = 1
                        _tradingContract.BuyorSell = THOST_FTDC_D_Sell  # '1'-Sell

                        _pInputOrder =        CThostFtdcInputOrderField()

                        # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                        _pInputOrder.InstrumentID = quotation.instrumentID
                        _pInputOrder.LimitPrice = quotation.bidPrice1 + 3 * _tradingContract.priceTick
                        _pInputOrder.Direction = THOST_FTDC_D_Sell
                        _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTotalOriginal
                        _pInputOrder.CombOffsetFlag = "0"
                        # 有效期类型
                        _pInputOrder.TimeCondition = THOST_FTDC_TC_IOC
                        # 成交量类型
                        _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV

                        #pProducerTrade->Publish((void *)  pInputOrder, 1, free_data_func_type1)

                        _tradingCommand.openPosition(_pInputOrder)
                        logging.info(quotation.__dict__)
                        '''
                        # 挂单
                        _pInputOrder_1 = CThostFtdcInputOrderField()

                        # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                        _pInputOrder_1.InstrumentID =  _quotation.instrumentID
                        _pInputOrder_1.LimitPrice = _quotation.bidPrice1 + _tradingContract.priceTick * 5
                        _pInputOrder_1.Direction = THOST_FTDC_D_Sell
                        _pInputOrder_1.VolumeTotalOriginal = 1
                        _pInputOrder_1.CombOffsetFlag =  "0"
                        # 有效期类型
                        _pInputOrder_1.TimeCondition = THOST_FTDC_TC_GFD
                        # 成交量类型
                        _pInputOrder_1.VolumeCondition = THOST_FTDC_VC_AV

                        #pProducerTrade->Publish((void *)                         _pInputOrder_1, 1, free_data_func_type1)

                        _tradingCommand.openPosition(_pInputOrder_1)
                        #logging.info(_quotation)
                        '''

        # 有持仓，检查平仓条件是否满足
        else:
             if (_tradingContract.position > 0):
                # 在收市前2分钟，平掉当日仓位
                if ((quotation.updateTime > "14:58:59") and (quotation.updateTime< "15:00:00")):
                    _pInputOrder = CThostFtdcInputOrderField()

                    # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    _pInputOrder.InstrumentID =  quotation.instrumentID
                    _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTraded
                    _pInputOrder.CombOffsetFlag = "3"  # 平今
                    # 有效期类型,当日有效
                    _pInputOrder.TimeCondition = THOST_FTDC_TC_GFD
                    # 成交量类型
                    _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV
                    # 买持仓
                    if (_tradingContract.BuyorSell == THOST_FTDC_D_Buy):
                        _pInputOrder.Direction = THOST_FTDC_D_Sell
                        _pInputOrder.LimitPrice = quotation.bidPrice1 - _tradingContract.priceTick * 0  # 5

                    # 卖持仓
                    else:
                        _pInputOrder.Direction = THOST_FTDC_D_Buy
                        _pInputOrder.LimitPrice = quotation.askPrice1 + _tradingContract.priceTick * 0  # 5

                    #pProducerTrade->Publish((void *)         pInputOrder, 1, free_data_func_type1)
                    _tradingCommand.timeToClosePosition(_pInputOrder)

                    # 平仓指令发出后，把仓位置为0
                    _tradingContract.position = 0
                    _tradingContract.dayTradingFlag = False  # ==0 不允许交易， 但是preprared标志不变




                # 在非收市前2分钟，正常判断价格是否在平仓区间，是否达到止盈和止损平仓位
                else:
                    # 买持仓
                    if (_tradingContract.BuyorSell == THOST_FTDC_D_Buy):

                        if (
                        (quotation.bidPrice1 > _tradingContract.sellClosePrice - _tradingContract.priceTick * 0)
                        or (quotation.askPrice1 < _tradingContract.sellStopLoss  + _tradingContract.priceTick * 0)  ):


                            _pInputOrder = CThostFtdcInputOrderField()

                            # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                            _pInputOrder.InstrumentID = quotation.instrumentID

                            _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTraded
                            _pInputOrder.CombOffsetFlag = "3"  # 平今
                            # 有效期类型,当日有效
                            _pInputOrder.TimeCondition = THOST_FTDC_TC_GFD
                            # 成交量类型
                            _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV

                            _pInputOrder.Direction = THOST_FTDC_D_Sell
                            _pInputOrder.LimitPrice = quotation.bidPrice1 - _tradingContract.priceTick * 1

                            #pProducerTrade->Publish((void *)pInputOrder, 1, free_data_func_type1)
                            _tradingCommand.closePosition(_pInputOrder)

                            # 平仓指令发出后，把仓位置为0
                            _tradingContract.position = 0
                            _tradingContract.dayTradingFlag = False
                            '''
                        logging(
                                    "InstumentID=[%s],ActoinDate=[%s %s.%d], lastPrice=[%f],volume=[%f],position=[%d],averagePrice=[%f]\n" % (
                                        _quotation.instrumentID,
                                        _quotation.actionDay,
                                        _quotation.updateTime,
                                        _quotation.updateMillisec,
                                        _quotation.lastPrice,
                                        _quotation.volume,
                                        _quotation.openInterest,
                                        _quotation.averagePrice)
                                   )
                        '''


                    # 卖持仓
                    else:
                        if (_tradingContract.BuyorSell == THOST_FTDC_D_Sell):

                            if ((quotation.askPrice1 < _tradingContract.buyClosePrice + _tradingContract.priceTick * 0)
                            or (quotation.bidPrice1 > _tradingContract.buyStopLoss  - _tradingContract.priceTick * 0)):


                                _pInputOrder = CThostFtdcInputOrderField()

                                # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                                _pInputOrder.InstrumentID = quotation.instrumentID

                                _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTraded
                                _pInputOrder.CombOffsetFlag = "3"  # 平今
                                # 有效期类型,当日有效
                                _pInputOrder.TimeCondition = THOST_FTDC_TC_GFD
                                # 成交量类型
                                _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV

                                _pInputOrder.Direction = THOST_FTDC_D_Buy
                                _pInputOrder.LimitPrice = quotation.askPrice1 + _tradingContract.priceTick * 1  # 5

                                #pProducerTrade->Publish((void *) pInputOrder, 1, free_data_func_type1)
                                _tradingCommand.closePosition(_pInputOrder)
                                logging.info(quotation.__dict__)
                                # 平仓指令发出后，把仓位置为0
                                _tradingContract.position = 0
                                _tradingContract.dayTradingFlag = False


class CFutureBreakMdHandler(CMdHandler):

    # 重载
    def handleQuotation(self, quotation):
        # 合约状态为连续交易
        assert  isinstance(quotation, CFutureMarketData), 'handleQuotation parameter is not a instance of CFutureMarketData'

        _strategy = self.tradingContext.getStrategy('futureBreakStrategy')
        _tradingContract = self.tradingContext.getStrategy('futureBreakStrategy').getTradingContract(quotation.instrumentID)

        if (_tradingContract.exchangeInstrumentStatus == '2') :
            # 21:30:00，确定当日的开仓价格
            if (_tradingContract.preparedFlag == False )  :
                _strategy.prepareForTrading(quotation)
            # 在可交易区间，根据行情和仓位，判断是否开仓或平仓
            else :
                _strategy.checkQuotation(quotation)



def main():
    t = time.time()
    context = CTradingContext('20170227','ag1706')
    runType = context.runType

    print('目前运行环境为:'+ runType);
    futureBreakStrategy = CFutureBreakStrategy(context)

    tradingContract = CTradingContract(context.instrumentID)

    futureBreakStrategy.initialTradingContract(tradingContract)
    tradingContract.exchangeInstrumentStatus = '2'

    handler = CMdHandler(context)
    handler.start_consuming()

    print(time.time() - t)
    logging.warning('end of main')

if __name__ == "__main__":
    main()
