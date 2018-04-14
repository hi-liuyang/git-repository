import time
import threadpool
import cx_Oracle
import threading

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

def sayhello(str):
    cur = dbcommand.cursor.var(cx_Oracle.CURSOR)
    o_code = dbcommand.cursor.var(cx_Oracle.NUMBER)
    o_msg = dbcommand.cursor.var(cx_Oracle.STRING)
    params = []

    params.append(str)
    params.append("20080602")
    params.append("20080631")
    params.append(o_code)
    params.append(o_msg)
    params.append(cur)


    dbcommand.executeSP("pk_portfolio_regress.sp_strategy_regress", params)

def runsp_with_threadpool(name_list):

    start_time = time.time()
    pool = threadpool.ThreadPool(5)
    requests = threadpool.makeRequests(sayhello, name_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    print ('run_with_threadpool： %d second'% (time.time()-start_time))


def run_with_threadpool():
    name_list =['xiaozi','aa','bb','cc']
    start_time = time.time()
    pool = threadpool.ThreadPool(2)
    requests = threadpool.makeRequests(sayhello, name_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    print ('run_with_threadpool： %d second'% (time.time()-start_time))

def run_without_threadpool(name_list):
    name_list = ['xiaozi', 'aa', 'bb', 'cc']
    start_time = time.time()
    for item in name_list:
        sayhello(item)
    print('run_without_threadpool: %d second' % (time.time() - start_time))


if __name__ == "__main__":
    dbcommand = DBCommand()
    dbcommand.prepare("select * from (select distinct strategyid from FutureStrategyTable@dzh m where m.modeldate = '20171212') where rownum<21")

    #dbcommand.prepare("select distinct strategyid from FutureStrategyTable@dzh m where m.modeldate = '20171212'")
    strategy_list = []
    rows = dbcommand.execute(None, ())
    for item in rows:
        strategy_list.append(item[0])

    runsp_with_threadpool(strategy_list)