# 基于价格与均线的相关差交易系统
#

from tradingContext import *
from quotation import *
from mock_quotation import *
class CTickSwaySystem(CStrategy):



    def __init__(self, tradingContext):
        self.tradingContext = tradingContext
        self.tradingContext.addStrategy(self, 'TickSwaySystem')



    # 初始化交易合约信息
    def initialTradingContract(self, _tradingContract):
        self.dict_TradingContract[_tradingContract.instrumentID] = _tradingContract

        _tradingContract.initialContract(_tradingContract.instrumentID)


    def prepareForTrading(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)

        if (_tradingContract.preparedFlag == False) and (quotation.updateTime> "21:30:00" or quotation.updateTime< "14:45:00"):
                _tradingContract.preparedFlag = True
                _tradingContract.dayTradingFlag = True


    def checkQuotation(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)
        _context = self.tradingContext
        _tradingCommand = _context.getTradingCommand()  # CTradingCommand(self.tradingContext)

        #logging.debug(quotation.updateTime +',ratio,'+str(_tradingCon tract.QuotationList.up_tick_count / _tradingContract.QuotationList.MaxLength))

        _pTrade = self.mockTrade(_tradingContract, quotation)
        if _pTrade !=  None :
            #_pTrade = CFutureMatch()

            _tradingContract.ATR = (
                                       _tradingContract.kline.lst_k_line[-2].high_price -
                                       _tradingContract.kline.lst_k_line[
                                           -2].low_price +
                                       _tradingContract.kline.lst_k_line[-3].high_price -
                                       _tradingContract.kline.lst_k_line[
                                           -3].low_price +
                                       _tradingContract.kline.lst_k_line[-4].high_price -
                                       _tradingContract.kline.lst_k_line[
                                           -4].low_price +
                                       _tradingContract.kline.lst_k_line[-5].high_price -
                                       _tradingContract.kline.lst_k_line[
                                           -5].low_price

                                   ) / 4
            logging.debug(_tradingContract.ATR)



            if _pTrade.eo_flag == 'O':

                if _pTrade.bs_flag == 'B':
                    _tradingContract.buyOpenPrice = _pTrade.price

                    _tradingContract.sellStopLoss = _pTrade.price - _tradingContract.ATR * 1
                    _tradingContract.sellClosePrice = _pTrade.price + _tradingContract.ATR * 1

                if _pTrade.bs_flag == 'S':
                    _tradingContract.sellOpenPrice = _pTrade.price
                    _tradingContract.buyStopLoss = _pTrade.price + _tradingContract.ATR * 1
                    _tradingContract.buyClosePrice = _pTrade.price - _tradingContract.ATR * 1

        if (_tradingContract.dayTradingFlag == False) :
            if (_tradingContract.m1_QuotationList.up_bigvolume_tick_count == 0 and _tradingContract.m1_QuotationList.down_bigvolume_tick_count == 0  ) :
                _tradingContract.dayTradingFlag == True

        # v_position == 0,当日尚未开仓，_tradingContract.dayTradingFlag >0 可以交易
        if ((_tradingContract.position == 0) and (_tradingContract.dayTradingFlag == True) and (_tradingContract.tradeNum < self.maxTradeNum)):
            # 如果时间在下午(21:00~21:30,09:00~09:15)，则不再开仓,其他时间可以
            if ((quotation.updateTime > "09:15:00" and quotation.updateTime < "14:50:00")
                or (quotation.updateTime > "21:15:00") and (quotation.updateTime < "22:55:00")):
                # 如果卖一价大于买开仓价,且小于卖平仓价
                #	_tradingContract.priceTick为滑点
                if (quotation.updateTime == "21:45:15"):
                    print('wait...')
                if (
                        #(_tradingContract.LT_QuotationList.up_bigvolume_tick_count -_tradingContract.LT_QuotationList.down_bigvolume_tick_count > 10  )
                        #and (_tradingContract.ST_QuotationList.up_bigvolume_tick_count -_tradingContract.ST_QuotationList.down_bigvolume_tick_count > 5  )
                        #and
                     (    _tradingContract.LT_QuotationList.head.data.lastPrice <= _tradingContract.LT_QuotationList.tail.data.lastPrice
                            and
                                  _tradingContract.ST_QuotationList.head.data.lastPrice <= _tradingContract.ST_QuotationList.tail.data.lastPrice
                                       #      and _tradingContract.LT_QuotationList.head.data.lastPrice <= _tradingContract.ST_QuotationList.head.data.lastPrice
                                       and _tradingContract.LT_QuotationList.up_bigvolume_tick_count > _tradingContract.LT_QuotationList.down_bigvolume_tick_count

                                 and _tradingContract.ST_QuotationList.up_bigvolume_tick_count > _tradingContract.ST_QuotationList.down_bigvolume_tick_count
                             and _tradingContract.m1_QuotationList.up_bigvolume_tick_count > _tradingContract.m1_QuotationList.down_bigvolume_tick_count
                           and (_tradingContract.m1_QuotationList.up_bigvolume_tick_count + _tradingContract.m1_QuotationList.down_bigvolume_tick_count) > 2)
                            and _tradingContract.m1_QuotationList.up_bigvolume_tick_count > _tradingContract.m1_QuotationList.down_bigvolume_tick_count
                    and _tradingContract.positionField.long_order == 0 and _tradingContract.position == 0) :
                    _tradingContract.position = 1
                    _tradingContract.BuyorSell = '0'  # THOST_FTDC_D_Buy  # '0'-Buy

                    # 以对手价委托
                    _pInputOrder = CThostFtdcInputOrderField()

                    # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    _pInputOrder.InstrumentID = quotation.instrumentID
                    _pInputOrder.LimitPrice = quotation.bidPrice1 + 3 * _tradingContract.priceTick
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




                # 如果买一价小于卖开仓价,PriceTick为滑点
                else:
                    if (
                        _tradingContract.LT_QuotationList.head.data.lastPrice >= _tradingContract.LT_QuotationList.tail.data.lastPrice
                                and
                                    _tradingContract.ST_QuotationList.head.data.lastPrice >= _tradingContract.ST_QuotationList.tail.data.lastPrice
                                   # and _tradingContract.LT_QuotationList.head.data.lastPrice >= _tradingContract.ST_QuotationList.head.data.lastPrice
                                and _tradingContract.LT_QuotationList.up_bigvolume_tick_count < _tradingContract.LT_QuotationList.down_bigvolume_tick_count
                            and _tradingContract.ST_QuotationList.up_bigvolume_tick_count < _tradingContract.ST_QuotationList.down_bigvolume_tick_count
                            and _tradingContract.m1_QuotationList.up_bigvolume_tick_count < _tradingContract.m1_QuotationList.down_bigvolume_tick_count
                                and (_tradingContract.m1_QuotationList.up_bigvolume_tick_count + _tradingContract.m1_QuotationList.down_bigvolume_tick_count) > 2
                                and _tradingContract.m1_QuotationList.up_bigvolume_tick_count < _tradingContract.m1_QuotationList.down_bigvolume_tick_count


                        and _tradingContract.positionField.short_order == 0 and _tradingContract.position == 0 ):
                        _tradingContract.position = 1
                        _tradingContract.BuyorSell = THOST_FTDC_D_Sell  # '1'-Sell

                        _pInputOrder = CThostFtdcInputOrderField()

                        # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                        _pInputOrder.InstrumentID = quotation.instrumentID
                        _pInputOrder.LimitPrice = quotation.askPrice1 - 3 * _tradingContract.priceTick
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
                        #调整止损价格
                        if (_tradingContract.sellStopLoss + 1* _tradingContract.ATR )< quotation.bidPrice1:
                            _tradingContract.sellStopLoss = quotation.bidPrice1 - 1* _tradingContract.ATR

                        if ( quotation.bidPrice1 < _tradingContract.sellStopLoss or quotation.bidPrice1 > _tradingContract.sellClosePrice ) :
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



                    # 卖持仓
                    else:

                        if (_tradingContract.positionField.short_posi > 0 and _tradingContract.BuyorSell == THOST_FTDC_D_Sell):
                        #调整止损价格
                            if (_tradingContract.buyStopLoss - 1* _tradingContract.ATR )> quotation.askPrice1:
                                _tradingContract.buyStopLoss = quotation.askPrice1 + 1 * _tradingContract.ATR

                            if ( quotation.askPrice1 > _tradingContract.buyStopLoss  or quotation.askPrice1 < _tradingContract.buyClosePrice) :

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
class CTSSTradingContract(CTradingContract):


    def initialContract(self,instrumentID):
        # 入场阀值
        self.LT_Enter_Ratio = 0.55
        # 出场阀值
        self.LT_Exit_Ratio = 0.5
        #
        self.LT_QuotationList = CQuotationLinkList(360)

        # 入场阀值


        self.ST_Enter_Ratio = 0.6
        # 出场阀值
        self.ST_Exit_Ratio = 0.55
        #
        self.ST_QuotationList = CQuotationLinkList(120)

        self.m1_QuotationList = CQuotationLinkList(30)


class CTSSMdHandler(CMdHandler):

    # 重载
    def handleQuotation(self, quotation):
        # 合约状态为连续交易
        assert  isinstance(quotation, CFutureMarketData), 'handleQuotation parameter is not a instance of CFutureMarketData'
        #logging.debug(quotation.__dict__)

        _strategy = self.tradingContext.getStrategy('TickSwaySystem')
        _tradingContract = self.tradingContext.getStrategy('TickSwaySystem').getTradingContract(quotation.instrumentID)

        #计算DRD,RDV
        # 生成分钟线


        _kbar = _tradingContract.kline.handle(quotation)
        _kbar.average_price = _tradingContract.kline.Average('CLOSE', 15)
        if (quotation.updateTime[:5] >= '20:50' or quotation.updateTime[:5] <='15:00'  ):

            _tradingContract.LT_QuotationList.append(quotation)
            _tradingContract.ST_QuotationList.append(quotation)
            _tradingContract.m1_QuotationList.append(quotation)

            logging.debug(','+quotation.updateTime +','
                          +  str(quotation.lastPrice) + ',' +  str(quotation.tick_volume)
                          + ','+ str(_tradingContract.LT_QuotationList.up_bigvolume_tick_count)+','+str(_tradingContract.LT_QuotationList.down_bigvolume_tick_count)
                          + ',' + str(_tradingContract.ST_QuotationList.up_bigvolume_tick_count) + ',' + str(_tradingContract.ST_QuotationList.down_bigvolume_tick_count)
                          + ',' + str(_tradingContract.m1_QuotationList.up_bigvolume_tick_count) + ',' + str(_tradingContract.m1_QuotationList.down_bigvolume_tick_count)
                          + ','
                          )

        else:
            pass

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
    mock.instrumentID = 'ru1801'
    mock.tradeDate = '20170828'
    mock.root_dir = 'c:\\tmp\\csv\\'
    threading.Thread(target=mock.send,args=(),name='MockThread').start()
    #mock.send()


    context = CTradingContext(mock.tradeDate,mock.instrumentID)
    runType = context.runType

    print('目前运行环境为:'+ runType);
    strategy = CTickSwaySystem(context)

    tradingContract = CTSSTradingContract(context.instrumentID)

    strategy.initialTradingContract(tradingContract)
    tradingContract.exchangeInstrumentStatus = '2'

    handler = CTSSMdHandler(context)
    handler.start_consuming()


    logging.warning('end of main')

if __name__ == "__main__":
    main()
