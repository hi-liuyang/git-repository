import datetime
import json
import pika
import logging
import logging.config
import copy
import re


#合约基本信息
class CInstrument:
    instrumentID='' #合约
    productID = '' #产品
    volumeMultiple = 0  # 合约乘数
    marginRatio = 0 # 保证金率
    feeRatio = 0 # 手续费率
    maxMarginSideAlgorithm = 0 # 是否使用大额单边保证金算法 , 0 - 不启用
    upperLimitPrice= 0.0 # 涨停板价格
    lowerLimitPrice= 0.0 # 跌停板价格
    priceTick = 0 # 最小变动价位

    def __init__(self,instrumentid):
        self.instrumentID = instrumentid
        # 暂时供测试用，实际应该从数据库中获取数据

        # 如果以ag开头
        if (re.match(r'[\D]*', self.instrumentID).group(0) == "ag"):
            # pTradingContract->v_Today_PriceRange = 72.17; // 60.06; // 66.8; // 73.56; //
            self.priceTick = 1
            self.volumeMultiple = 15
            self.volumeTotalOriginal = 5
            self.productID = 'ag'

        # 如果以ru开头
        if (re.match(r'[\D]*', self.instrumentID).group(0) == "ru"):
            # pTradingContract->v_Today_PriceRange = 72.17; // 60.06; // 66.8; // 73.56; //
            self.priceTick = 5
            self.volumeMultiple = 10
            self.volumeTotalOriginal = 1
            self.productID = 'ru'

        # 如果以ni开头
        if (re.match(r'[\D]*', self.instrumentID).group(0) == "ni"):
            # pTradingContract->v_Today_PriceRange = 72.17; // 60.06; // 66.8; // 73.56; //
            self.priceTick = 10
            self.volumeMultiple = 1
            self.volumeTotalOriginal = 1
            self.productID = 'ni'

        # 如果以rb开头
        if (re.match(r'[\D]*', self.instrumentID).group(0) == "rb"):
            # pTradingContract->v_Today_PriceRange = 72.17; // 60.06; // 66.8; // 73.56; //
            self.priceTick = 1
            self.volumeMultiple = 10
            self.volumeTotalOriginal = 1
            self.productID = 'rb'

        # 如果以rb开头
        if (re.match(r'[\D]*', self.instrumentID).group(0) == "cu"):
            # pTradingContract->v_Today_PriceRange = 72.17; // 60.06; // 66.8; // 73.56; //
            self.priceTick = 10
            self.volumeMultiple = 5
            self.volumeTotalOriginal = 1
            self.productID = 'cu'


#行情
class CFutureMarketData:
    type = 'T' # T-Tick，M-分钟，5M=5分钟，D-日线
    instrumentID = ''
    actionDay = 0.0
    askPrice1 = 0.0
    bidPrice1 = 0.0
    askVolume1 = 0.0
    bidVolume1 = 0.0
    lastPrice = 0.0
    volume = 0.0
    turnover = 0.0
    openInterest = 0.0
    averagePrice = 0.0  # 均价
    closePrice = 0.0  # 今收盘
    openPrice = 0.0
    highPrice = 0.0
    lowPrice = 0.0
    settlementPrice = 0.0  # 本次结算价
    upperLimitPrice = 0.0  # 涨停板价
    lowerLimitPrice = 0.0  # 跌停板价
    updateTime = 0.0
    updateMillisec = 0.0

    def __init__(self,_type='M'):
        self.type = _type

    def getAveragePrcie(self):
        #上期所的合约
        pass

# #技术指标
# class CIndicator:
#     def __init__(self):
#         pass
#     def calculate(self):
#         pass
#
# #
# class RSI(CIndicator):
#     def __init__(self,N=1 ,kline=None):
#         self.kline = kline
#         self.N = N
#
#     def setKLine(self,kline):
#         self.kline = kline
#
#     def calculate(self):
#         assert(self.kline == None,"k线为空，无法计算技术指标")
#         _len = len(self.kline.lst_k_line)
#         if (_len < self.N):
#             return -1
#         else:
#             i = 0
#             A = 0
#             B = 0
#             while i < self.N:
#
#                 if self.kline.lst_k_line[-1-i].close_price < self.kline.lst_k_line[-1-i].open_price:
#                     B = B + self.kline.lst_k_line[-1-i].open_price - self.kline.lst_k_line[-1-i].close_price
#                 else:
#                     A = A + self.kline.lst_k_line[-1-i].close_price - self.kline.lst_k_line[-1-i].open_price
#                 i = i+1
#             return 100 * A/(A+B)
#
# #


#单根K线
class CKBar:
    trade_time = ''
    inst_code = ''
    time_index = 0
    high_price = 0.0
    open_price = 0.0
    low_price = 0.0
    close_price = 0
    volume = 0.0
    open_insterest = 0
    amount = 0.0
    #如果是5分钟线，则为5分钟均价，不是当日的均价
    avg_price = 0.0
    #上一笔行情，
    __last_quotation = None

#一天的完整k线
class CKLine:
    #如果为一天的，则指定trade_date,如果是周k线，月K线，则代表开始的第一天的日期
    trade_date= ''
    # M- 分钟 ，
    type = 'M'
    #key 为trade_time ,value 为 K线值
    k_line = {}
    lst_k_line = []
    __kbar = None

    __last_kbar = None
    __last_quotation = None

    # interval为5，表示5分钟线
    def __init__(self,trade_date,type='M',interval=1):
        self.trade_date = trade_date
        self.type = type
        self.interval = interval
        self.__kbar = None
        self.k_line = {}
        self.lst_k_line = []

        #注册的技术指标,key为indicator名称，value为eval中的表达式，如RSI(24)
        self.dict_indicator = {}
        #计算下一根k线的开始时间
        self.next_k_start_time = None

    def handle(self,_quotation):

        # _quotation.updateMillisec = int(field[0][field[0].find('.')+1:-1])


        t_str = _quotation.actionDay + ' ' + _quotation.updateTime[:5] + ":00"
        d = datetime.datetime.strptime(t_str, '%Y%m%d %H:%M:%S')

        t_str_1 = _quotation.actionDay + ' ' + _quotation.updateTime+ '.'+str(_quotation.updateMillisec)

        #如果是第一根k线，赋值下一根k线的开始时间
        if self.__last_quotation == None:
            time_plus_delta = datetime.timedelta(minutes=self.interval)
            self.next_k_start_time = d + time_plus_delta

        # 如果时间小于下一根k线的开始时间，说明是同一根分钟线，调整各个价格，

        #if self.__last_quotation != None and  _quotation.updateTime[:5] == self.__last_quotation.updateTime[:5]:
        #if self.__last_quotation != None and t_str_1 <=  self.next_k_start_time.strftime('%Y%m%d %H:%M:%S')+ '.0':
        if self.__last_quotation != None and d < self.next_k_start_time:
            self.__kbar.close_price = _quotation.lastPrice
            if _quotation.lastPrice > self.__kbar.high_price:
                self.__kbar.high_price = _quotation.lastPrice
            if _quotation.lastPrice < self.__kbar.low_price:
                self.__kbar.low_price = _quotation.lastPrice

            #如果该tick创了新高或新低，则需要更新
            if _quotation.lowPrice <self.__last_quotation.lowPrice:
                self.__kbar.low_price = _quotation.lowPrice
            if _quotation.highPrice > self.__last_quotation.highPrice:
                self.__kbar.high_price = _quotation.highPrice

            self.__kbar.volume = self.__kbar.volume + (_quotation.volume - self.__last_quotation.volume)
            self.__kbar.open_insterest = _quotation.openInterest


            self.lst_k_line[-1] = self.__kbar
            self.k_line[self.__kbar.trade_time] = self.__kbar


        # 生成一根新的K线，
        else:
            if self.__kbar != None:
                #     self.k_line[_quotation.updateTime[9:]] = self.__kbar
                #     self.lst_k_line.append(self.__kbar)
                print(self.__kbar.__dict__)
                #print (self.dict_indicator['RSI6'])
            self.__kbar = CKBar()
            self.__kbar.trade_time = _quotation.updateTime[:5]
            self.__kbar.inst_code = _quotation.instrumentID
            self.__kbar.open_price = _quotation.lastPrice
            self.__kbar.close_price = _quotation.lastPrice
            self.__kbar.high_price = _quotation.lastPrice
            self.__kbar.low_price = _quotation.lastPrice

            self.__kbar.open_insterest = _quotation.openInterest
            self.__kbar.volume = 0

            #如果该tick创了新高或新低，则需要更新
            if self.__last_quotation != None:
                self.__kbar.volume = self.__kbar.volume + (_quotation.volume - self.__last_quotation.volume)

                if _quotation.lowPrice <self.__last_quotation.lowPrice:
                    self.__kbar.low_price = _quotation.lowPrice
                if _quotation.highPrice > self.__last_quotation.highPrice:
                    self.__kbar.high_price = _quotation.highPrice
            else:
                self.__kbar.volume = _quotation.volume

            #增加新的k线
            self.lst_k_line.append( self.__kbar)
            self.k_line[self.__kbar.trade_time] = self.__kbar

            #更新下一根k线的开始时间
            time_plus_delta = datetime.timedelta(minutes=self.interval)
            self.next_k_start_time = d + time_plus_delta


        self.cal_indicator()
        #处理完成后，将当前这笔行情赋值给上一笔行情，供后续使用’
        self.__last_quotation = _quotation

        #计算技术指标


        return self.__kbar
    #
    # def register_indicator(self,indicator,parameter_expr):
    #     self.dict_indicator[indicator] = parameter_expr
    #
    #
    #
    # def calculate_indicator(self):
    #
    #     for item in self.dict_indicator.keys():
    #
    #         expr = "self." + item + " = " +  'self.'+self.dict_indicator[item]
    #
    #         exec(expr)
    #         print(self.RSI6)


    def reg_indicator(self,indicator,indicator_exp):
        self.dict_indicator[indicator] = indicator_exp



    def cal_indicator(self):

        for item in self.dict_indicator.keys():

            expr = "self." + item + " = " +  'self.'+self.dict_indicator[item]

            exec(expr)
            #print(self.RSI6)

    #求k线的均价，默认为收盘价，周期为5
    def cal_Average(self,price_type='CLOSE',length=5):
        sum = 0
        _len = len(self.lst_k_line)
        for item in  self.lst_k_line[(length*-1):]:
            sum = sum + item.close_price

        return sum /max(min(length,_len),1)

    # 正常在0-100，如果某分钟无成交，返回-1
    def cal_ATR(self):
        _len = len(self.lst_k_line)
        if _len == 0 :
            return 0
        elif _len == 1:
            return self.lst_k_line[-1].high_price -self.lst_k_line[-1].low_price
        else:
            _last_kbar = self.lst_k_line[-2]
            _kbar = self.lst_k_line[-1]
            return max(_kbar.high_price - min(_kbar.low_price,_last_kbar.high_price),max(_kbar.high_price,_last_kbar.low_price) - _kbar.low_price)

    def cal_RSI(self,N):
        _len = len(self.lst_k_line)
        if (_len < N):
            return -1
        else:
            i = 0
            A = 0
            B = 0
            while i < N:

                if self.lst_k_line[-1-i].close_price < self.lst_k_line[-1-i].open_price:
                    B = B + self.lst_k_line[-1-i].open_price - self.lst_k_line[-1-i].close_price
                else:
                    A = A + self.lst_k_line[-1-i].close_price - self.lst_k_line[-1-i].open_price
                i = i+1
            if (A+B) == 0 :
                ret = -1
            else:
                ret = 100 * A / (A + B)

            return ret

class CMDHandler:
    __dict_kline = {}
    _connection = None
    _channel = None
    _quotation = None



    def __init__(self):



        self._connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='hello')
        self._channel.basic_consume(self.callback, queue='hello', no_ack=True)

    def addKLine(self,kline):
        assert isinstance(kline, CKLine), "kline is not a CKLine instance"
        self.__dict_kline[kline.type] = kline;

    def callback(self,ch, method, properties, body):
        _quotation = CFutureMarketData()
        # _dict = body
        # print(body)
        _str = str(body, 'utf-8').split('|')
        if _str[0] == 'CFutureMarketData' :
            _quotation.__dict__ = json.loads(_str[1])
            self.handleQuotation(_quotation)
            #print('Data:%s' % (body,))
        else :
            print('body is not a CFutureMarketData json string:%s'%(body,))
        #print(_quotation.instrumentID + ',' + _quotation.updateTime + ',' + str(_quotation.lastPrice))

    def start_consuming(self):
        assert self._channel != None,"should not be None"
        self._channel.start_consuming()

    def handleQuotation(self,_quotation):
        # 合约状态为连续交易
        assert  isinstance(_quotation,CFutureMarketData),'handleQuotation parameter is not a instance of CFutureMarketData'
        for _kline in self.__dict_kline.values():
            _kline.handle(_quotation)




class CQuotationNode(object):
    def __init__(self,_val,_pre=None,_next=None):
        #data的内容是CFutureMarketData
        self.data = _val
        self.pre = _pre
        self.next = _next



class CQuotationLinkList(object):
    def __init__(self,_maxLength):
        self.MaxLength = _maxLength
        self.length = 0
        # 第一个node
        self.head = None
        #最后一个Node
        self.tail = None

        # 向上tick根数
        self.up_tick_count = 0
        self.down_tick_count = 0
        #向上的成交量
        self.up_volume_count = 0
        self.down_volume_count = 0
        #向上(卖价 - 买价 > 1 tick)price的数量
        self.up_price_count = 0
        self.down_price_count = 0
        #向上持仓量的变化
        self.up_position_count = 0
        self.down_position_count = 0

        #大于一定成交量的tick的数量

        self.up_bigvolume_sum = 0
        self.down_bigvolume_sum = 0

        self.up_bigvolume_tick_count = 0
        self.down_bigvolume_tick_count = 0
        # ATR和BIG_VOLUME_THRESHOLD 都是合约的属性，为了测试方便，先放在这里，实际应该每日重新计算并初始化
        self.ATR = 3
        #
        self.BIG_VOLUME_THRESHOLD = 30
        #
        self.sum_buy_minus_sell_volume = 0
        #
        self.sum_tick_volume = 0


    def getlength(self):
            return self.length

    def is_empty(self):
        if self.getlength() ==0:
            return True
        else:
            return False

    def clear(self):

        self.head = None
        self.length = 0

    #@param item 为CFutureMarketData
    def append(self,item):

        # 处理buy_tick_volume,sell_tick_volume,由于只需要本node的信息就可以处理，单独完成，后续需要linklist的head，tail的信息，所以在另一个部分处理，看起来是重复的。
        if self.head is None:

            self.instrumentID = item.instrumentID
            self.instrument  = CInstrument(item.instrumentID)

            self.sum_buy_minus_sell_volume = 0

            item.tick_volume = item.volume
            item.tick_openInterest = item.openInterest

            if item.lastPrice == item.askPrice1:
                item.buy_tick_volume = 0
                item.sell_tick_volume = item.volume
            else:
                item.buy_tick_volume = item.volume
                item.sell_tick_volume = 0

            item.buy_minus_sell_volume = item.buy_tick_volume - item.sell_tick_volume
            item.sum_buy_minus_sell_volume = item.buy_minus_sell_volume
            self.sum_buy_minus_sell_volume = item.buy_minus_sell_volume

            item.sum_tick_volume = item.tick_volume
            self.sum_tick_volume = item.tick_volume

        else :
            # tick的成交量
            item.tick_volume = item.volume - self.tail.data.volume
            # 持仓量变化
            item.tick_openInterest = item.openInterest - self.tail.data.openInterest
            # bid_vol_change bid价位上量的变化，如果bid价格变动，则该值为0，@todo bid价格变小时，是否要算
            item.bid_vol_change = 0
            item.ask_vol_change = 0

            # sell_tick_volume，主动卖量， buy_tick_volume，主动买量
            # 如果item.askPrice1 <= self.tail.data.bidPrice1，说明价格下跌，那么所有成交量都算在主动卖上面
            if item.askPrice1 <= self.tail.data.bidPrice1:
                item.sell_tick_volume = item.tick_volume
                item.buy_tick_volume = 0

            elif  item.bidPrice1 >= self.tail.data.askPrice1:
                     item.buy_tick_volume = item.tick_volume
                     item.sell_tick_volume = 0
            else:

                item.sell_tick_volume = ((item.amount - self.tail.data.amount) / self.instrument.volumeMultiple - self.tail.data.askPrice1 * item.tick_volume) / (self.tail.data.bidPrice1 - self.tail.data.askPrice1)
                if (item.sell_tick_volume > item.tick_volume):
                    item.sell_tick_volume = item.tick_volume
                if (item.sell_tick_volume < 0 ):
                    item.sell_tick_volume = 0
                item.buy_tick_volume = item.tick_volume - item.sell_tick_volume




            #_vol是考虑了另一种情况，如果
            #item.sell_tick_vol = item.sell_tick_volume
            #item.buy_tick_vol = item.buy_tick_volume
            if item.bidPrice1 == self.tail.data.bidPrice1:
                item.bid_vol_change = item.bidVolume1 - self.tail.data.bidVolume1
                #item.sell_tick_vol = item.bid_vol_change
            if item.askPrice1 == self.tail.data.askPrice1:
                item.ask_vol_change = item.askVolume1 - self.tail.data.askVolume1
                #item.buy_tick_vol = item.ask_vol_change
            #买量 - 卖量
            item.buy_minus_sell_volume = item.buy_tick_volume - item.sell_tick_volume
            #item.buy_minus_sell_vol = item.buy_tick_vol - item.sell_tick_vol

            if item.bidPrice1 < self.tail.data.bidPrice1:
                item.bidPrice1_change = -1
            elif  item.bidPrice1 > self.tail.data.bidPrice1:
                item.bidPrice1_change = 1
            else :
                item.bidPrice1_change = 0

            if item.askPrice1 < self.tail.data.askPrice1:
                item.askPrice1_change = -1
            elif item.askPrice1 > self.tail.data.askPrice1:
                item.askPrice1_change = 1
            else:
                item.askPrice1_change = 0


        #由于需要head，tail的信息，所以另外一段程序处理

        _item = copy.deepcopy(item)

        _item.up_bigvolume_tick_count = 0
        _item.down_bigvolume_tick_count = 0

        #由于需要head，tail的信息，所以另外一段程序处理
        if self.head != None :
            _head_quotation = self.head.data
            _tail_quotation = self.tail.data
            #已经形成完整的链表，数量不会增多，则选择链首节点的数据，从self中减去
            if (self.length == self.MaxLength):
                # self.up_bigvolume_tick_count = self.up_bigvolume_tick_count - _head_quotation.up_bigvolume_tick_count
                # self.down_bigvolume_tick_count = self.down_bigvolume_tick_count - _head_quotation.down_bigvolume_tick_count
                #
                self.sum_buy_minus_sell_volume = self.sum_buy_minus_sell_volume + (item.buy_tick_volume - item.sell_tick_volume )  - (_head_quotation.buy_tick_volume - _head_quotation.sell_tick_volume )
                self.sum_tick_volume = self.sum_tick_volume + item.tick_volume - _head_quotation.tick_volume

                if (_head_quotation.lastPrice >= _head_quotation.askPrice1):
                    self.up_tick_count = self.up_tick_count - 1
                    self.up_volume_count = self.up_volume_count - _head_quotation.tick_volume

                    if _head_quotation.tick_volume > self.BIG_VOLUME_THRESHOLD:
                        self.up_bigvolume_sum = self.up_bigvolume_sum - _head_quotation.tick_volume

                if (_head_quotation.lastPrice <= _head_quotation.bidPrice1):
                    self.down_tick_count = self.down_tick_count - 1
                    self.down_volume_count = self.down_volume_count - _head_quotation.tick_volume
                    if _head_quotation.tick_volume > self.BIG_VOLUME_THRESHOLD:
                        self.down_bigvolume_sum = self.down_bigvolume_sum - _head_quotation.tick_volume


                # 处理行情数据
                _quotation = _item
                if (_quotation.lastPrice >=  _quotation.askPrice1) :
                    self.up_tick_count = self.up_tick_count + 1

                    if _quotation.tick_volume > self.BIG_VOLUME_THRESHOLD :
                        self.up_bigvolume_sum = self.up_bigvolume_sum + _quotation.tick_volume
                        if _quotation.lastPrice > _tail_quotation.askPrice1:
                            self.up_bigvolume_tick_count = self.up_bigvolume_tick_count + 1;
                            _item.up_bigvolume_tick_count = 1;

                if (_quotation.lastPrice <= _quotation.bidPrice1):
                    self.down_tick_count = self.down_tick_count + 1
                    self.down_volume_count = self.down_volume_count + _quotation.tick_volume
                    if _quotation.tick_volume > self.BIG_VOLUME_THRESHOLD:
                        self.down_bigvolume_sum = self.down_bigvolume_sum + _quotation.tick_volume
                        if _quotation.lastPrice < _tail_quotation.bidPrice1:
                            self.down_bigvolume_tick_count = self.down_bigvolume_tick_count + 1;
                            _item.down_bigvolume_tick_count = 1;
            else:
                #
                self.sum_buy_minus_sell_volume = self.sum_buy_minus_sell_volume + (item.buy_tick_volume - item.sell_tick_volume)
                self.sum_tick_volume = self.sum_tick_volume + item.tick_volume
            #
            _item.sum_buy_minus_sell_volume  = self.sum_buy_minus_sell_volume
            _item.sum_tick_volume = self.sum_tick_volume

        #节点数据处理完成后，对linklist进行处理，增加新节点
        q = CQuotationNode(_item)
        if self.head ==None:
            q.pre = q
            q.next = q
            self.head = q
            self.tail = q
            self.length = 1

        else:
            if self.length < self.MaxLength :
                q.pre = self.tail
                self.tail.next = q
                self.tail = q
                q.next = self.head
                self.head.pre = q
                self.length = self.length + 1
            else:
                self.head.data = q.data
                self.head = self.head.next
                self.tail = self.head.pre
        #logging.debug('up_tick_count:'+str(self.up_tick_count))
        #logging.debug('down_tick_count:' + str(self.down_tick_count))
        #logging.debug('all_count:' + str(self.up_tick_count + self.down_tick_count))


def main():
    kline = CKLine(trade_date='20180411',type='M',interval=1)
    kline.type='T'
    #kline1 = CKLine('20170512','5M')
    kline.reg_indicator('RSI6','cal_RSI(6)')
    print(kline.type)
    mdhandler = CMDHandler()
    mdhandler.addKLine(kline)
    #mdhandler.addKLine(kline1)

    mdhandler.start_consuming()

    logging.warning('end of main')



if __name__ == "__main__":
    main()

