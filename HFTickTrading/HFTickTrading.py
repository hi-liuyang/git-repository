# 基于价格与均线的相关差交易系统
#

from tradingContext import *
from quotation import *
from mock_quotation import *

import pandas as pd

import numpy as np
import matplotlib.pyplot as plt


class CHFTickTrading(CStrategy):



    def __init__(self, tradingContext):
        self.tradingContext = tradingContext
        self.tradingContext.addStrategy(self, 'HFTickTrading')
        self.dict_quotation_list = []



    # 初始化交易合约信息
    def initialTradingContract(self, _tradingContract):
        self.dict_TradingContract[_tradingContract.instrumentID] = _tradingContract

        _tradingContract.initialContract(_tradingContract.instrumentID)


    def prepareForTrading(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)

        if (_tradingContract.preparedFlag == False) and (quotation.updateTime> "21:05:00" or quotation.updateTime< "14:45:00"):
                _tradingContract.preparedFlag = True
                #_tradingContract.dayTradingFlag = True

    '''
    def checkQuotation(self,quotation):
        _tradingContract = self.getTradingContract(quotation.instrumentID)

        _sum_minus_volume = _tradingContract.QuotationList_1m.sum_buy_minus_sell_volume * 2 + _tradingContract.QuotationList_2m.sum_buy_minus_sell_volume * 1.2 + _tradingContract.QuotationList_5m.sum_buy_minus_sell_volume
        #if _sum_minus_volume > 2000:
        #logging.debug(quotation.updateTime + ',' +  str(_tradingContract.QuotationList_1m.tail.data.buy_minus_sell_volume) + ','+ str(_tradingContract.QuotationList_1m.sum_buy_minus_sell_volume) +','+ str(_sum_minus_volume))

    '''
    def checkQuotation(self,quotation):


        _tradingContract = self.getTradingContract(quotation.instrumentID)
        _context = self.tradingContext
        _tradingCommand = _context.getTradingCommand()  # CTradingCommand(self.tradingContext)


        _sum_minus_volume = _tradingContract.QuotationList_1m.sum_buy_minus_sell_volume * 2 + _tradingContract.QuotationList_2m.sum_buy_minus_sell_volume * 1.2 + _tradingContract.QuotationList_5m.sum_buy_minus_sell_volume

        # 如果prepare结束，但是_sum_minus_volume 过高，不交易
        if (_tradingContract.dayTradingFlag == False):

            if (_sum_minus_volume <_tradingContract.Exit_sum_minus_volume) and (_sum_minus_volume > (_tradingContract.Exit_sum_minus_volume * -1)):
                _tradingContract.dayTradingFlag = True
                return
            else:
                return

        self.mockTrade(_tradingContract, quotation)

        # v_position == 0,当日尚未开仓，_tradingContract.dayTradingFlag >0 可以交易
        if ((_tradingContract.position == 0) and (_tradingContract.dayTradingFlag == True) and (_tradingContract.tradeNum < self.maxTradeNum)):
            # 如果时间在下午(21:00~21:30,09:00~09:15)，则不再开仓,其他时间可以
            if ((quotation.updateTime > "09:01:00" and quotation.updateTime < "14:45:00")
                or (quotation.updateTime > "21:05:00") or (quotation.updateTime < "02:15:00")):
                # 如果卖一价大于买开仓价,且小于卖平仓价
                #	_tradingContract.priceTick为滑点
                #  以后再考虑  _tradingContract.QuotationList.up_tick_count  /_tradingContract.QuotationList.MaxLength > _tradingContract.Enter_Ratio
                if (_tradingContract.QuotationList_1m.sum_buy_minus_sell_volume / _tradingContract.QuotationList_1m.sum_tick_volume > 0.85
                    and _tradingContract.QuotationList_1m.sum_tick_volume > 600
                    and _tradingContract.positionField.long_order == 0 ) :
                    _tradingContract.position = 1
                    _tradingContract.BuyorSell = '0'  # THOST_FTDC_D_Buy  # '0'-Buy

                    # 以对手价委托
                    _pInputOrder = CThostFtdcInputOrderField()

                    # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                    _pInputOrder.InstrumentID = quotation.instrumentID
                    _pInputOrder.LimitPrice = quotation.askPrice1 + _tradingContract.priceTick * 1
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
                    if ( _tradingContract.QuotationList_1m.sum_buy_minus_sell_volume / _tradingContract.QuotationList_1m.sum_tick_volume < -0.85
                         and _tradingContract.QuotationList_1m.sum_tick_volume > 600
                         and _tradingContract.positionField.short_order == 0 ):
                        _tradingContract.position = 1
                        _tradingContract.BuyorSell = THOST_FTDC_D_Sell  # '1'-Sell

                        _pInputOrder = CThostFtdcInputOrderField()

                        # 初始化InputOrder的内容，公共的内容，在Command中初始化，这里只关系合约、价格、数量、买卖、开平
                        _pInputOrder.InstrumentID = quotation.instrumentID
                        _pInputOrder.LimitPrice = quotation.bidPrice1 - 1 * _tradingContract.priceTick
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
                        if ( _tradingContract.QuotationList_1m.sum_buy_minus_sell_volume / _tradingContract.QuotationList_1m.sum_tick_volume < 0 ):
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
                        #if (_tradingContract.kline.lst_k_line[-1].RDV > 0 ):
                        if (_tradingContract.positionField.short_posi > 0 and _tradingContract.QuotationList_1m.sum_buy_minus_sell_volume / _tradingContract.QuotationList_1m.sum_tick_volume > 0 ):
                            # if ((quotation.askPrice1 < _tradingContract.buyClosePrice + _tradingContract.priceTick * 0)
                            #     or (
                            #         quotation.bidPrice1 > _tradingContract.buyStopLoss - _tradingContract.priceTick * 0)):
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
class CHFTickTradingContract(CTradingContract):


    def initialContract(self,instrumentID):
        # 入场阀值
        self.Enter_sum_minus_volume = 2000
        # 出场阀值
        self.Exit_sum_minus_volume = 500
        #
        self.QuotationList_10s = CQuotationLinkList(20)
        self.QuotationList_1m = CQuotationLinkList(120)
        self.QuotationList_2m = CQuotationLinkList(240)

        self.QuotationList_5m = CQuotationLinkList(600)


class CHFMdHandler(CMdHandler):

    # 重载
    def handleQuotation(self, quotation):
        # 合约状态为连续交易
        assert  isinstance(quotation, CFutureMarketData), 'handleQuotation parameter is not a instance of CFutureMarketData'
        #logging.debug(quotation.__dict__)

        _strategy = self.tradingContext.getStrategy('HFTickTrading')
        _tradingContract = self.tradingContext.getStrategy('HFTickTrading').getTradingContract(quotation.instrumentID)

        #计算DRD,RDV
        # 生成分钟线


        _kbar = _tradingContract.kline.handle(quotation)
        #_kbar.average_price = _tradingContract.kline.Average('CLOSE', 15)
        if (quotation.updateTime[:5] >= '20:50' or quotation.updateTime[:5] <='15:00'  ):

            _tradingContract.QuotationList_10s.append(quotation)
            _tradingContract.QuotationList_1m.append(quotation)
            _tradingContract.QuotationList_2m.append(quotation)
            _tradingContract.QuotationList_5m.append(quotation)


        else:
            pass

        if (_tradingContract.exchangeInstrumentStatus == '2') :
            # 21:30:00，确定当日的开仓价格
            if (_tradingContract.preparedFlag == False )  :
                _strategy.prepareForTrading(quotation)
            # 在可交易区间，根据行情和仓位，判断是否开仓或平仓
            else :
                _strategy.checkQuotation(quotation)
        _strategy.dict_quotation_list.append(_tradingContract.QuotationList_1m.tail.data.__dict__)


def main():

    # 模拟发行情
    mock = CMockTickQuotation()
    mock.instrumentID = 'ru1805'
    mock.tradeDate = '20180323'
    #mock.root_dir = 'c:\\tmp\\csv\\'
    #threading.Thread(target=mock.send,args=(),name='MockThread').start()
    #mock.send()


    context = CTradingContext(mock.tradeDate,mock.instrumentID)
    #context = CTradingContext('20180404','cu1805')
    runType = context.runType

    print('目前运行环境为:'+ runType);
    strategy = CHFTickTrading(context)

    tradingContract = CHFTickTradingContract(context.instrumentID)
    context.tradingContract = tradingContract

    strategy.initialTradingContract(tradingContract)
    tradingContract.exchangeInstrumentStatus = '2'

    handler = CHFMdHandler(context)
    handler.start_consuming()



    quotation_df = pd.DataFrame(strategy.dict_quotation_list)
    quotation_df.to_csv(context.instrumentID + '_' + context.tradingDate + '_all.csv')
    # df1 = quotation_df[
    #     ['lastPrice', 'tick_volume','bidPrice1','askPrice1','bidPrice1_change',  'askPrice1_change', 'bidVolume1','askVolume1',  'bid_vol_change', 'ask_vol_change','buy_tick_volume','sell_tick_volume', 'buy_minus_sell_volume', 'updateTime']]
    #
    #
    # df1.to_csv(context.instrumentID+'_'+context.tradingDate+'.csv')
    # fig, axes = plt.subplots(5, 1)
    # l = quotation_df['lastPrice']
    # v = quotation_df['tick_volume']
    # s_v = quotation_df['sell_tick_volume']
    # b_v = quotation_df['buy_tick_volume']
    # op = s_v-b_v
    # l.plot(ax=axes[0])
    # v.plot(ax=axes[1])
    # s_v.plot(ax=axes[2])
    # b_v.plot(ax=axes[3])
    # op.plot(ax=axes[4],kind='bar')
    #
    # plt.show()
    #

    logging.warning('end of main')

if __name__ == "__main__":
    main()
