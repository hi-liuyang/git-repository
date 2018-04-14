#输入报单
class CThostFtdcInputOrderField:
    # 经纪公司代码 TThostFtdcBrokerIDType
    BrokerID = ''
    # 投资者代码TThostFtdcInvestorIDType
    InvestorID = ''
    # 合约代码 TThostFtdcInstrumentIDType
    InstrumentID = ''
    # 报单引用    TThostFtdcOrderRefType
    OrderRef = ''
    # 用户代码  TThostFtdcUserIDType
    UserID = ''
    # 报单价格条件    TThostFtdcOrderPriceTypeType
    OrderPriceType = ''
    # 买卖方向     TThostFtdcDirectionType
    Direction = ''
    # 组合开平标志     TThostFtdcCombOffsetFlagType
    CombOffsetFlag = ''
    # 组合投机套保标志     TThostFtdcCombHedgeFlagType
    CombHedgeFlag = ''
    # 价格     TThostFtdcPriceType
    LimitPrice = 0.0
    # 数量     TThostFtdcVolumeType
    VolumeTotalOriginal = 0
    # 有效期类型     TThostFtdcTimeConditionType
    TimeCondition = ''
    # GTD日期     TThostFtdcDateType
    GTDDate = ''
    # 成交量类型     TThostFtdcVolumeConditionType     
    VolumeCondition =''
    # 最小成交量    TThostFtdcVolumeType
    MinVolumev = 0
    # 触发条件     TThostFtdcContingentConditionType
    ContingentCondition =''
    # 止损价   TThostFtdcPriceType
    StopPrice = 0.0
    # 强平原因      TThostFtdcForceCloseReasonType
    ForceCloseReason = ''
    # 自动挂起标志        TThostFtdcBoolType
    IsAutoSuspend = 0
    # 业务单元      TThostFtdcBusinessUnitType
    BusinessUnit =''
    # 请求编号      TThostFtdcRequestIDType
    RequestID = 0
    # 用户强评标志     TThostFtdcBoolType
    UserForceClose = 0
    # 互换单标志      TThostFtdcBoolType
    IsSwapOrder = 0


#报单
class CThostFtdcOrderField:
	#经纪公司代码
	BrokerID = ''
	#投资者代码
	InvestorID = ''
	#合约代码
	InstrumentID = ''
	#报单引用
	OrderRef = ''
	#用户代码
	UserID = ''
	#报单价格条件
	OrderPriceType = ''
	#买卖方向
	Direction = ''
	#组合开平标志
	CombOffsetFlag = ''
	#组合投机套保标志
	CombHedgeFlag = ''
	#价格
	LimitPrice = 0.0
	#数量
	VolumeTotalOriginal = 0
	#有效期类型
	TimeCondition = ''
	#GTD日期
	GTDDate = ''
	#成交量类型
	VolumeCondition = ''
	#最小成交量
	MinVolume = 0
	#触发条件
	ContingentCondition = ''
	#止损价
	StopPrice = 0.0
	#强平原因
	ForceCloseReason = ''
	#自动挂起标志
	IsAutoSuspend = 0
	#业务单元
	BusinessUnit = ''
	#请求编号
	RequestID = 0
	#本地报单编号
	OrderLocalID = ''
	#交易所代码
	ExchangeID = ''
	# 会员代码
	ParticipantID = ''
	# 客户代码
	ClientID = ''
	# 合约在交易所的代码
	ExchangeInstID = ''
	# 交易所交易员代码
	TraderID = ''
	# 安装编号
	InstallID = ''
	# 报单提交状态
	OrderSubmitStatus = ''
	# 报单提示序号
	NotifySequence = 0
	# 交易日
	TradingDay = ''
	# 结算编号
	SettlementID = 0
	# 报单编号
	OrderSysID = ''
	# 报单来源
	OrderSource = ''
	# 报单状态
	OrderStatus = ''
	# 报单类型
	OrderType = ''
	# 今成交数量
	VolumeTraded = 0
	# 剩余数量
	VolumeTotal = 0
	# 报单日期
	InsertDate = ''
	# 委托时间
	InsertTime = ''
	# 激活时间
	ActiveTime = ''
	# 挂起时间
	SuspendTime = ''
	# 最后修改时间
	UpdateTime = ''
	# 撤销时间
	CancelTime = ''
	# 最后修改交易所交易员代码
	ActiveTraderID = ''
	# 结算会员编号
	ClearingPartID = ''
	# 序号
	SequenceNo = 0
	# 前置编号
	FrontID = 0
	# 会话编号
	SessionID = 0
	# 用户端产品信息
	UserProductInfo = ''
	# 状态信息
	StatusMsg = ''
	# 用户强评标志
	UserForceClose = 0
	# 操作用户代码
	ActiveUserID = ''
	# 经纪公司报单编号
	BrokerOrderSeq = 0
	# 相关报单
	RelativeOrderSysID = ''
	# 郑商所成交数量
	ZCETotalTradedVolume = 0
	# 互换单标志
	IsSwapOrder = 0



#成交
class CThostFtdcTradeField:
	#经纪公司代码
	BrokerID = ''
	#投资者代码
	InvestorID = ''
	#合约代码
	InstrumentID = ''
	#报单引用
	OrderRef = ''
	#用户代码
	UserID = ''
	#交易所代码
	ExchangeID = ''
	#成交编号
	TradeID = ''
	#买卖方向
	Direction = ''
	#报单编号
	OrderSysID = ''
	#会员代码
	ParticipantID = ''
	#客户代码
	ClientID = ''
	#交易角色
	TradingRole = ''
	#合约在交易所的代码
	ExchangeInstID = ''
	#开平标志
	OffsetFlag = ''
	#投机套保标志
	HedgeFlag = ''
	#价格
	Price = 0.0
	#数量
	Volume = 0
	#成交时期
	TradeDate = ''
	#成交时间
	TradeTime = ''
	#成交类型
	TradeType = ''
	#成交价来源
	PriceSource = ''
	#交易所交易员代码
	TraderID = ''
	#本地报单编号
	OrderLocalID = ''
	#结算会员编号
	ClearingPartID = ''
	#业务单元
	BusinessUnit = ''
	#序号
	SequenceNo = 0
	#交易日
	TradingDay = ''
	#结算编号
	SettlementID = 0
	#经纪公司报单编号
	BrokerOrderSeq = 0
	#成交来源
	TradeSource = ''


#报单操作,如撤单
class CThostFtdcOrderActionField:
	#经纪公司代码
	BrokerID= ''
	#投资者代码
	InvestorID= ''
	#报单操作引用
	OrderActionRef= 0
	#报单引用
	OrderRef= 0.0
	#请求编号
	RequestID= 0
	#前置编号
	FrontID= 0
	#会话编号
	SessionID= 0
	#交易所代码
	ExchangeID= ''
	#报单编号
	OrderSysID= ''
	#操作标志
	ActionFlag= ''
	#价格
	LimitPrice= 0.0
	#数量变化
	VolumeChange= 0
	#操作日期
	ActionDate= ''
	#操作时间
	ActionTime= ''
	#交易所交易员代码
	TraderID= ''
	#安装编号
	InstallID= 0.0
	#本地报单编号
	OrderLocalID= ''
	#操作本地编号
	ActionLocalID= ''
	#会员代码
	ParticipantID= ''
	#客户代码
	ClientID= ''
	#业务单元
	BusinessUnit= ''
	#报单操作状态
	OrderActionStatus= ''
	#用户代码
	UserID= ''
	#状态信息
	StatusMsg= ''
	#合约代码
	InstrumentID= ''

