import time
import cx_Oracle
import threading

import pandas as pd
import numpy as n
from util import DBUtil
import time
import threading
import cx_Oracle

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
        self.to_date = '20100129'
        # 会看天数
        self.retrieve_days = 10
        # 策略一共分成多少组
        self.group_numbers = 10
        # 调仓周期
        self.adjust_days = 5

        # pd中获取到哪一条数据
        self.current_point  = 0
        # 初始化数据，将需要用到的策略收益数据，存到self.df_capital_data
        self.init_data()


    #初始化数据
    def init_data(self):
        # 找到需要的最早的一天的日期

        dbcommand = DBCommand()
        db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
        cursor = db.cursor()

        dbcommand.prepare(" \
                select * from ( \
                    select c.trade_days \
                            FROM winduser.asharecalendar  c where  c.trade_days < :1      and c.s_info_exchmarket = 'SSE' order by c.trade_days desc \
               ) \
               where rownum < :2        order by trade_days ")


        _rows = dbcommand.execute(None,  (self.from_date ,self.retrieve_days))


        _begin_date = _rows[0][0]
        print ("beginDate: %s",_begin_date)
        # 获取从最早的一天到to_date的回测的策略数据，放在df中
        # 回看的数据

#         dbcommand.prepare("select trade_dt,strategyid,total_capital,initial_total_capital,net_value,hold_pl,offset_pl from t_f_capital where portfolioid='$' and trade_dt >= :1 and trade_dt < :2 order by trade_dt,strategyid   ")
#         _rows = dbcommand.execute(None, (_begin_date, self.from_date))
#
#         self.df_retrieve_capital_data = pd.DataFrame(_rows)
#         self.df_retrieve_capital_data.rename(columns={0:'trade_dt',1:'strategyid',2:'total_capital',3:'initial_total_capital',4:'net_value',5:'hold_pl',6:'offset_pl'},inplace=True
# )
#         self.retrieve_date = _rows[0][0]
        # for item in _rows:
        #     print(item)

        #实际回测的数据
        dbcommand.prepare(
            "select trade_dt,strategyid,total_capital,initial_total_capital,net_value,hold_pl,offset_pl from t_f_capital where portfolioid='$' and trade_dt >= :1 and trade_dt <= :2 order by trade_dt,strategyid   ")
        _rows = dbcommand.execute(None, (_begin_date, self.to_date))

        self.df_capital_data = pd.DataFrame(_rows)

        self.df_capital_data.rename(
            columns={0: "trade_dt", 1: "strategyid", 2: 'total_capital', 3: 'initial_total_capital', 4: 'net_value',
                     5: 'hold_pl', 6: 'offset_pl'},inplace=True)


        self.df_retrieve_capital_data = self.df_capital_data[self.df_capital_data['trade_dt']<self.from_date]
        self.retrieve_date = self.df_retrieve_capital_data.iloc[0][0]

        self.regress_date = self.from_date
        # 回测当天的数据
        self.df_regress_capital_data = self.df_capital_data[self.df_capital_data['trade_dt']==self.from_date]

        #print(self.df_retrieve_capital_data.head())
        #print(self.df_capital_data.columns)
        #print(self.df_capital_data["strategyid"])

    ''' 
        for item in _rows:
            print(item)
        '''
        # 获取这段时间的收益数据


    #准备下一日数据，把当日的收益数据从capital_data中删除，放入retrieve_data，在retrieve_data中删除最早的一天数据
    def prepare_next_data(self):

        #self.df_retrieve_capital_data
        #print('prepare_next_data')
        #df.drop(df[df['a'] == 3].index)
        #df.drop(df['strategyid']=='MARB_BOR2')
        #inplace
        self.df_retrieve_capital_data.drop(self.df_retrieve_capital_data[self.df_retrieve_capital_data['trade_dt']==self.retrieve_date].index, inplace=True)



        #self.df_retrieve_capital_data.append(self.df_capital_data[self.df_capital_data['trade_dt']==self.regress_date])
        self.df_retrieve_capital_data = pd.concat([self.df_retrieve_capital_data,self.df_regress_capital_data[self.df_capital_data['trade_dt']==self.regress_date]])


        #print(self.df_retrieve_capital_data.tail())
        self.regress_date = self.df_capital_data[self.df_capital_data['trade_dt'] > self.regress_date].iloc[0][0]
        self.retrieve_date = self.df_retrieve_capital_data.iloc[0][0]

        self.df_regress_capital_data = self.df_capital_data[self.df_capital_data['trade_dt']==self.regress_date]


        #print(self.df_capital_data.head())


    def regress_trade_dt(self,trade_dt=None):

        print('retrieve_date' + self.retrieve_date)
        print('regress_date' + self.regress_date)
        #以上完成当日的回测，准备下一日的数据

        # 构建当日的{}， key为strategyid，value为指标值，所有计算完成后，按照values排列，进行分组，
        for item in self.regress_result.lst_strategy:
            print(item)
            _return_ratio = self.df_regress_capital_data[  (self.df_regress_capital_data['strategyid']==item  )& ( self.df_regress_capital_data['trade_dt']==self.regress_date  ) ]['total_capital'].iloc[0] /   self.df_retrieve_capital_data[(self.df_retrieve_capital_data['strategyid'] == item) & (self.df_retrieve_capital_data['trade_dt'] == self.retrieve_date)]['total_capital'].iloc[0]
            self.regress_result.df_regress_result = self.regress_result.df_regress_result.append({'trade_dt':self.regress_date ,'portfolio_id':'','strategy_id':item,'retrieve_days':self.retrieve_days,'indicator_id':self.indicator,'indicator_value':_return_ratio,'return_ratio':0},ignore_index=True)




    def run(self):
        self.regress_result = CRegressResult()

        while (self.regress_date< self.to_date):



            self.regress_trade_dt('')

            self.prepare_next_data()



        return 0


class CRegressResult():
    def __init__(self):
        #key为 日期，values为CstrategyGroups的示例，表示当天的业绩情况
        self.dict_days= {}
        # 考虑一个df放所有的结果，日期，portfolio，strategy，indicator，indicator_value，return_ratio(收益率),
        self.df_strategy_result = pd.DataFrame(
            columns={'trade_dt','portfolio_id', 'strategy_id','retrieve_days', 'indicator_id', 'indicator_value', 'return_ratio'})

        self.df_regress_result = pd.DataFrame(columns={'trade_dt','portfolio_id','retrieve_days','indicator_id','indicator_value','return_ratio'})

        # 策略id
        self.lst_strategy = []
        # key是序号，1,2,3...10 代表10组，value是[], 属于该组的strategy
        self.dict_group = {}
        dbcommand = DBCommand()
        db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
        cursor = db.cursor()

        #dbcommand.prepare("select distinct strategyid from FutureStrategyTable@dzh m where m.modeldate = '20171212' order by strategyid")
        dbcommand.prepare(
            "select distinct strategyid from t_f_capital m where m.trade_dt = '20171212' order by strategyid")
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
    start_time = time.time()
    do = CPortfolioDO()
    do.run()

    do.regress_result.df_regress_result.to_clipboard()
    pd.read_csv()
    print('prepare data total time: %d second' % (time.time() - start_time))

    # print (len(do.df_capital_data))
    # print(len(do.df_retrieve_capital_data))
    # print(len(do.df_regress_capital_data))
    #
    # print("do.df_capital_data.head()")
    # print(do.df_capital_data.head())
    # print("do.df_retrieve_capital_data.head()")
    # print(do.df_retrieve_capital_data.head())
    # print("do.df_regress_capital_data.head()")
    # print(do.df_regress_capital_data.head())
    # print('run total time: %d second' % (time.time() - start_time))

'''
dbcommand = DBCommand()
db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
cursor = db.cursor()


#dbcommand.prepare("select * from FutureStrategyTable@dzh m where m.modeldate = '20171212'")

dbcommand.prepare("select * from t_f_capital where portfolioid='$' order by trade_dt,strategyid ")

rows = dbcommand.execute(None, ())

zz = pd.DataFrame(rows)

print (zz)


'''