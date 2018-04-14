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
