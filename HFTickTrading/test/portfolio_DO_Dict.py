import time
import cx_Oracle
import threading
import pandas as pd
import numpy as n
import logging
import logging.config



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

    def executeSP(self, sqlstr, *args, **kwargs):
        if self.db == None:
            self.getInstance();

        if self.db_lock.acquire():
            try:
                self.cursor.callproc(sqlstr, *args, **kwargs)
                self.db.commit()

            finally:
                self.db_lock.release()

'''
    组合动态优化
'''
class CPortfolioDO():
    def __init__(self):
        #指标
        self.indicator = 'REV'
        #回测开始日期
        self.from_date = '20100104'
        #回测结束日期
        self.to_date = '20100124'
        # 会看天数
        self.retrieve_days = 10
        # 策略一共分成多少组
        self.groups_number = 10
        # 调仓周期
        self.adjust_days = 5

        self.dict_strategy = {}

        # pd中获取到哪一条数据
        self.current_retrieve_point = 0
        self.current_regress_point  = self.retrieve_days
        # 初始化数据，将需要用到的策略收益数据，存到self.df_capital_data

        self.lst_trade_dt =[]

        #最终的结果
        self.lst_result_group = []

        self.init_data()


    #初始化数据
    def init_data(self):
        # 找到需要的最早的一天的日期
        #self.portfolio_strategy_capital = CPortfolioStrategyCapital()
        dbcommand = DBCommand()
        db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
        cursor = db.cursor()

        # 根据回测起始日期和回看天数，找到时间所需数据的第一天
        dbcommand.prepare(" \
                select * from ( \
                    select c.trade_days \
                            FROM winduser.asharecalendar  c where  c.trade_days < :1      and c.s_info_exchmarket = 'SSE' order by c.trade_days desc \
               ) \
               where rownum < :2        order by trade_days ")


        _rows = dbcommand.execute(None,  (self.from_date ,self.retrieve_days + 1))


        _begin_date = _rows[0][0]
        self.retrieve_date = _begin_date
        logging.info ("beginDate: %s",_begin_date)

        # 所有需要的交易日历，并初始化 lst_trade_dt ，
        dbcommand.prepare("select c.trade_days FROM winduser.asharecalendar  c where  c.trade_days >= :1 and c.trade_days <=:2\
          and c.s_info_exchmarket = 'SSE' order by c.trade_days  ")

        _rows = dbcommand.execute(None, (_begin_date,self.to_date))

        for item in _rows:
            self.lst_trade_dt.append(item[0])

        self.regress_date = self.lst_trade_dt[self.retrieve_days]
        logging.info("regress: %s", self.lst_trade_dt[self.retrieve_days])


        # 获取从最早的一天到to_date的回测的策略数据，放在df中
        # 回看的数据
        dbcommand = DBCommand()
        db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
        cursor = db.cursor()

        dbcommand.prepare(
            "select distinct strategyid from t_f_capital m where m.trade_dt = '20171212' order by strategyid")

        rows = dbcommand.execute(None, ())
        logging.debug('1')
        for item in rows:
            self.dict_strategy[item[0]] = {}

        logging.debug('2')


        #实际回测的数据
        logging.debug('before query')
        dbcommand.prepare(
            "select trade_dt,strategyid,total_capital,initial_total_capital,net_value,hold_pl,offset_pl from t_f_capital where portfolioid='$' and trade_dt >= :1 and trade_dt <= :2 order by trade_dt,strategyid   ")
        _rows = dbcommand.execute(None, (_begin_date, self.to_date))

        for item in _rows:
            print ((item[1],item[0],item[2]))
            print(self.dict_strategy[item[1]])
            #print(self.dict_strategy[item[1]][item[0]])
            self.dict_strategy[item[1]][item[0]] = item[2]
        # 获取这段时间的收益数据


    #准备下一日数据，把当日的收益数据从capital_data中删除，放入retrieve_data，在retrieve_data中删除最早的一天数据
    def prepare_next_data(self):

        self.current_retrieve_point = self.current_retrieve_point + 1
        self.current_regress_point  = self.current_regress_point +  1


    # 回测当天
    def regress_trade_dt(self,trade_dt=None):

        #以上完成当日的回测，准备下一日的数据
        print('regress_dt:' + self.regress_date)
        #根据要求，计算指标
        # 每个策略的当日表现
        _lst_regress_result = []
        for item in self.regress_result.lst_strategy:
            _return_ratio = self.dict_strategy[item][self.regress_date] / self.dict_strategy[item][self.retrieve_date]
            _lst_regress_result.append({'trade_dt':self.regress_date ,'portfolio_id':'','strategy_id':item,'retrieve_days':self.retrieve_days,'indicator_id':self.indicator,'indicator_value':_return_ratio,'return_ratio':_return_ratio})
        # 如果指标在此周期内均未变化，则在本次选择过程中，去掉该策略

        # 对指标进行排序
        _lst_regress_result = sorted(_lst_regress_result, key=lambda value: value['indicator_value'])

        #对排序后的策略进行分组
        _i = 0
        _group = 1
        _groups = len(_lst_regress_result) / self.groups_number
        _score = 0
        for item in _lst_regress_result:
            _i = _i +1

            _score =_score + item["return_ratio"]
            if _i == self.groups_number and _group != _groups:

                self.lst_result_group.append({'trade_dt':self.regress_date ,'portfolio_id':self.indicator+'_'+str(self.retrieve_date)+"_"+str(self.adjust_days)+"_"+str(_group),'retrieve_days':self.retrieve_days,'indicator_id':self.indicator,'group_number':_group,'return_ratio':_score / _i})
                print ({'trade_dt':self.regress_date ,'portfolio_id':self.indicator+'_'+str(self.retrieve_date)+"_"+str(self.adjust_days)+"_"+str(_group),'retrieve_days':self.retrieve_days,'indicator_id':self.indicator,'group_number':_group,'return_ratio':_score / _i})
                _i = 0
                _group = _group +1
                _score = 0

        # 最后一组的处理
        if _i > 0 :
            self.lst_result_group.append({'trade_dt': self.regress_date,
                                          'portfolio_id': self.indicator + '_' + str(self.retrieve_date) + "_" + str(
                                              self.adjust_days) + "_" + str(_group),
                                          'retrieve_days': self.retrieve_days, 'indicator_id': self.indicator,
                                          'group_number': _group, 'return_ratio': _score / _i})


        #按照排序结果分组





    def run(self):
        self.regress_result = CRegressResult()

        i = 0
        while (self.current_regress_point< len(self.lst_trade_dt)):

            self.retrieve_date = self.lst_trade_dt[self.current_retrieve_point]
            self.regress_date = self.lst_trade_dt[self.current_regress_point]
            i = i +1
            if i == self.adjust_days:
                i = 0
                self.regress_trade_dt('')

            self.prepare_next_data()

        return 0

class CRegressResult():
    def __init__(self):
        #key为 日期，values为CstrategyGroups的示例，表示当天的业绩情况
        self.dict_days= {}
        # 考虑一个df放所有的结果，日期，portfolio，strategy，indicator，indicator_value，return_ratio(收益率),
        self.lst_regress_result = []

        # 策略id
        self.lst_strategy = []
        # key是序号，1,2,3...10 代表10组，value是[], 属于该组的strategy
        self.dict_group = {}
        dbcommand = DBCommand()
        db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
        cursor = db.cursor()

        dbcommand.prepare("select distinct strategyid from t_f_capital m where m.trade_dt = '20171212' order by strategyid")

        rows = dbcommand.execute(None, ())
        for item in rows:
            self.lst_strategy.append(item[0])




# 每次调仓使用此记录分组的情况
class CStrategyGroups():
    def __init__(self):
        pass
    # 将所有的group的数据写入数据库
    def dump_to_db(self):
        pass


class CStrategyGroup():
    pass

class CStrategyRevaluation():

    def __init__(self,strategy_id):
        self.strategy_id = strategy_id
        self.net_values = pd.DataFrame()

    def append(self,trade_dt,net_value):
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='myapp.log',
                        filemode='w')
    #logging.config.fileConfig("log/logging.conf")
    logging.debug('test logging')

    start_time = time.time()
    do = CPortfolioDO()
    print('prepare data total time: %d second' % (time.time() - start_time))

    do.run()


    #
    # do.regress_result.df_regress_result.to_clipboard()
    # pd.read_csv()


