from CTPAPIStructWrapper import *
#输入报单
class CFutureOrder:
    trade_date = ''
    trade_time = ''
    inst_code = ''
    bs_flag = ''
    eo_flag = ''
    price = 0.0
    volume = 0
    matched_volume = 0
    order_type = ''
    local_order_no = ''
    exch_order_no = ''
    order_status = ''
    exch_code = ''
    app_id = ''
    strategy_id = ''
    strategy_type = ''
    strategy_subno = ''
    create_time = ''

    def __init__(self,inputOrderField,trade_date='',trade_time=''):
        #_inputOrderField = CThostFtdcInputOrderField()
        self.trade_date = trade_date
        self.trade_time = trade_time
        self.inst_code = inputOrderField.InstrumentID
        if inputOrderField.Direction == '0':
            self.bs_flag = 'B'
        else:
            self.bs_flag = 'S'
        if inputOrderField.CombOffsetFlag == '0':
            self.eo_flag = 'O'
        else:
            self.eo_flag = 'C'
        self.price = inputOrderField.LimitPrice
        self.volume = inputOrderField.VolumeTotalOriginal
        self.local_order_no = inputOrderField.OrderRef

#quant.t_future_match
class CFutureMatch:
    trade_date  = ''
    trade_time  = ''
    inst_code  = ''
    bs_flag  = ''       # 'B' 'S'
    eo_flag  = ''       # 'O' 'C'
    price  = 0.0
    volume  = 0
    match_exch_no  = ''
    order_local_no  = ''
    order_exch_no  = ''
    exch_code  = ''
    app_id  = ''
    create_time  = ''
    seq_no  = ''

# todo 没有区分今仓，昨仓
class CFuturePosition:
    trade_date  = ''
    app_id  = ''
    inst_code  = ''
    strategy_type  = ''
    # 发出开仓委托，就增加long_order,short_order 数量，有平仓时减，根据这两个值判断是否可以开仓
    long_order = 0
    open_price = 0
    close_price = 0
    short_order = 0
    # 成交回报调整long_posi,
    long_posi  = 0
    short_posi  = 0
    long_posi_frozen  = 0
    short_posi_frozen  = 0
    long_posi_unmatch  = 0
    short_posi_unmatch  = 0

    def __init__(self,instrumentID):
        self.inst_code = instrumentID


