# 基于价格与均线的相关差交易系统
#

from tradingContext import *
from quotation import CKBar,CKLine
from mock_quotation import *
class CReferenceDeviationSystem(CStrategy):




    def __init__(self, tradingContext):
        self.tradingContext = tradingContext
        self.tradingContext.addStrategy(self, 'ReferenceDeviationSystem')


    # 初始化交易合约信息
    def initialTradingContract(self, _tradingContract):
        self.dict_TradingContract[_tradingContract.instrumentID] = _tradingContract

        _tradingContract.initialContract(_tradingContract.instrumentID)


    def prepareForTrading(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)

        if (_tradingContract.preparedFlag == False) and (quotation.updateTime> "21:30:00" or quotation.updateTime< "14:45:00"):
            if (_tradingContract.RDV < _tradingContract.ET/2) and (_tradingContract.RDV > (_tradingContract.ET/2 * -1)) :
                _tradingContract.preparedFlag = True
                _tradingContract.dayTradingFlag = True


    def checkQuotation(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)
        _context = self.tradingContext
        _tradingCommand = _context.getTradingCommand()  # CTradingCommand(self.tradingContext)

        self.mockTrade(_tradingContract, quotation)

        # v_position == 0,当日尚未开仓，_tradingContract.dayTradingFlag >0 可以交易
        if ((_tradingContract.position == 0) and (_tradingContract.dayTradingFlag == True) and (_tradingContract.tradeNum < self.maxTradeNum)):
            # 如果时间在下午(21:00~21:30,09:00~09:15)，则不再开仓,其他时间可以
            if ((quotation.updateTime > "09:15:00" and quotation.updateTime < "14:25:00")
                or (quotation.updateTime > "21:50:20") or (quotation.updateTime < "02:15:00")):
                # 如果卖一价大于买开仓价,且小于卖平仓价
                #	_tradingContract.priceTick为滑点

                if (_tradingContract.kline.lst_k_line[-1].RDV > _tradingContract.ET and _tradingContract.positionField.long_order == 0 ) :
                    _tradingContract.position = 1
                    _tradingContract.BuyorSell = '0'  # THOST_FTDC_D_Buy  # '0'-Buy

                    # 以对手价委托
                    _pInputOrder = CThostFtdcInputOrderField()

                    # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    _pInputOrder.InstrumentID = quotation.instrumentID
                    _pInputOrder.LimitPrice = quotation.bidPrice1 #+ _tradingContract.priceTick * 1
                    _pInputOrder.Direction = THOST_FTDC_D_Buy
                    _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTotalOriginal
                    _pInputOrder.CombOffsetFlag = "0"
                    # 有效期类型
                    _pInputOrder.TimeCondition = THOST_FTDC_TC_IOC  # THOST_FTDC_TC_GFD - 当日生效，THOST_FTDC_TC_IOC - 立即完成，否则撤销，用于FAK，FOK
                    # 成交量类型
                    _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV  #
                    # pProducerTrade->Publish((void *) pInputOrder, 1, free_data_func_type1)



                    _tradingCommand.openPosition(_pInputOrder)

                    #logging.info(quotation.__dict__)
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
                    if (_tradingContract.kline.lst_k_line[-1].RDV < _tradingContract.ET * -1 and _tradingContract.positionField.short_order == 0 ):
                        _tradingContract.position = 1
                        _tradingContract.BuyorSell = THOST_FTDC_D_Sell  # '1'-Sell

                        _pInputOrder = CThostFtdcInputOrderField()

                        # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                        _pInputOrder.InstrumentID = quotation.instrumentID
                        _pInputOrder.LimitPrice = quotation.askPrice1 #- 1 * _tradingContract.priceTick
                        _pInputOrder.Direction = THOST_FTDC_D_Sell
                        _pInputOrder.VolumeTotalOriginal = _tradingContract.volumeTotalOriginal
                        _pInputOrder.CombOffsetFlag = "0"
                        # 有效期类型
                        _pInputOrder.TimeCondition = THOST_FTDC_TC_IOC
                        # 成交量类型
                        _pInputOrder.VolumeCondition = THOST_FTDC_VC_AV

                        # pProducerTrade->Publish((void *)  pInputOrder, 1, free_data_func_type1)

                        _tradingCommand.openPosition(_pInputOrder)
                        #logging.info(quotation.__dict__)
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

        else:
            if (_tradingContract.positionField.long_posi > 0 or _tradingContract.positionField.short_posi > 0 ):
                # 在收市前2分钟，平掉当日仓位
                if ((quotation.updateTime > "14:58:59") and (quotation.updateTime < "15:00:00")):
                    _pInputOrder = CThostFtdcInputOrderField()

                    # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    _pInputOrder.InstrumentID = quotation.instrumentID
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

                    # pProducerTrade->Publish((void *)         pInputOrder, 1, free_data_func_type1)
                    _tradingCommand.timeToClosePosition(_pInputOrder)

                    # 平仓指令发出后，把仓位置为0
                    _tradingContract.position = 0
                    #_tradingContract.dayTradingFlag = False  # ==0 不允许交易， 但是preprared标志不变




                # 在非收市前2分钟，正常判断价格是否在平仓区间，是否达到止盈和止损平仓位
                else:
                    # 买持仓
                    #if (_tradingContract.BuyorSell == THOST_FTDC_D_Buy):
                    if (_tradingContract.positionField.long_posi > 0 and _tradingContract.BuyorSell == THOST_FTDC_D_Buy):
                        if (_tradingContract.kline.lst_k_line[-1].RDV < 0 ):
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

                            # pProducerTrade->Publish((void *)pInputOrder, 1, free_data_func_type1)
                            _tradingCommand.closePosition(_pInputOrder)

                            # 平仓指令发出后，把仓位置为0
                            _tradingContract.position = 0
                            #_tradingContract.dayTradingFlag = False
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
                        #if (_tradingContract.kline.lst_k_line[-1].RDV > 0 ):
                        if (_tradingContract.positionField.short_posi > 0 and _tradingContract.kline.lst_k_line[-1].RDV > 0 ):
                            if ((quotation.askPrice1 < _tradingContract.buyClosePrice + _tradingContract.priceTick * 0)
                                or (
                                    quotation.bidPrice1 > _tradingContract.buyStopLoss - _tradingContract.priceTick * 0)):
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

                                # pProducerTrade->Publish((void *) pInputOrder, 1, free_data_func_type1)
                                _tradingCommand.closePosition(_pInputOrder)
                                #logging.info(quotation.__dict__)
                                # 平仓指令发出后，把仓位置为0
                                _tradingContract.position = 0
                                #_tradingContract.dayTradingFlag = False


#
class CRDSTradingContract(CTradingContract):
    # 每日的参考偏离值
    DRD = 0.0
    # 参考偏离值
    RDV = 0.0
    #入场阀值
    ET =  0.5

    def initialContract(self,instrumentID):
        pass



class CRDSMdHandler(CMdHandler):

    # 重载
    def handleQuotation(self, quotation):
        # 合约状态为连续交易
        assert  isinstance(quotation, CFutureMarketData), 'handleQuotation parameter is not a instance of CFutureMarketData'

        _strategy = self.tradingContext.getStrategy('ReferenceDeviationSystem')
        _tradingContract = self.tradingContext.getStrategy('ReferenceDeviationSystem').getTradingContract(quotation.instrumentID)

        #计算DRD,RDV
        # 生成分钟线
        _kbar = _tradingContract.kline.handle(quotation)
        _kbar.average_price = _tradingContract.kline.Average('CLOSE', 15)
        if (quotation.updateTime[:5] >= '20:50' or quotation.updateTime[:5] <='15:00'  ):


            _kbar.DRD =   _kbar.average_price  - _kbar.close_price
            sum = 0
            abssum = 0
            if len(_tradingContract.kline.lst_k_line) > 0:
                for item in _tradingContract.kline.lst_k_line[-15:]:
                    sum = sum + item.DRD
                    abssum = abssum + abs(item.DRD)
                _kbar.RDV = sum / abssum
        else:
            _kbar.RDV = 0
            _kbar.DRD = 0
            #logging.debug(_kbar.__dict__)

        if (quotation.updateTime[:5] == '15:00'):
            for item in _tradingContract.kline.lst_k_line[:]:
                #logging.info(item.__dict__)
                if item.trade_time >  '21:50' or item.trade_time < '15:00':
                    print(item.trade_time+','+str(item.close_price)+','+str(item.average_price)+','+str(item.DRD)+','+str(item.RDV))
                else:
                    print(item.trade_time + ',' + str(item.close_price) + ',' + str(item.average_price) + ',' + '0' + ',' + '0')
        if (_tradingContract.exchangeInstrumentStatus == '2') :
            # 21:30:00，确定当日的开仓价格
            if (_tradingContract.preparedFlag == False )  :
                _strategy.prepareForTrading(quotation)
            # 在可交易区间，根据行情和仓位，判断是否开仓或平仓
            else :
                _strategy.checkQuotation(quotation)



def main():

    # 模拟发行情
    mock = CMockTickQuotation()
    mock.instrumentID = 'ru1705'
    mock.tradeDate = '20170112'
    mock.root_dir = 'z:\\'
    threading.Thread(target=mock.send,args=(),name='MockThread').start()
    #mock.send()


    context = CTradingContext(mock.tradeDate,mock.instrumentID)
    runType = context.runType

    print('目前运行环境为:'+ runType);
    strategy = CReferenceDeviationSystem(context)

    tradingContract = CRDSTradingContract(context.instrumentID)

    strategy.initialTradingContract(tradingContract)
    tradingContract.exchangeInstrumentStatus = '2'

    handler = CRDSMdHandler(context)
    handler.start_consuming()


    logging.warning('end of main')

if __name__ == "__main__":
    main()
