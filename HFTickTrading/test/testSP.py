import time
import threadpool
import cx_Oracle
import threading
from util.DBUtil import *

def sayhello(str):
    print ("Hello ",str)
    time.sleep(2)

def run_with_threadpool():
    name_list =['xiaozi','aa','bb','cc']
    start_time = time.time()
    pool = threadpool.ThreadPool(2)
    requests = threadpool.makeRequests(sayhello, name_list)
    [pool.putRequest(req) for req in requests]
    pool.wait()
    print ('run_with_threadpool： %d second'% (time.time()-start_time))

def run_without_threadpool():
    name_list = ['xiaozi', 'aa', 'bb', 'cc']
    start_time = time.time()
    for item in name_list:
        sayhello(item)
    print('run_without_threadpool: %d second' % (time.time() - start_time))


if __name__ == "__main__":
    dbcommand = DBCommand()
    db = cx_Oracle.connect('quant', 'quant', '192.168.1.100:1521/windinfo')
    cursor = db.cursor()


    dbcommand.prepare("select distinct strategyid from FutureStrategyTable@dzh m where m.modeldate = '20171212'")
    strategy_list = []
    rows = dbcommand.execute(None, ())
    for item in rows:
        strategy_list.append(item[0])


    print(strategy_list[0])

    cur = cursor.var(cx_Oracle.CURSOR)
    o_code = cursor.var(cx_Oracle.STRING)
    o_msg = cursor.var(cx_Oracle.STRING)

    params = []
    params.append(strategy_list[0][0])
    params.append("20080602")
    params.append("20080631")
    params.append(o_code)
    params.append(o_msg)
    params.append(cur)

    cursor.callproc("pk_portfolio_regress.sp_strategy_Regress",params)

    print(o_msg)
    db.commit()

