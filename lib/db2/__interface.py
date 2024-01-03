import ibm_db, os.path
from utils import LoadSQL, singleton
from datetime import datetime
from functools import lru_cache

'''
some queries from: https://github.com/glinuz/db2_exporter/tree/master
                   https://github.com/lausser/check_db2_health
                   https://github.com/IBM/db2histmon/blob/master/1_setup/task_details.json
                   https://github.com/angoca/monitor-db2-with-nagios/blob/master/check_instance_memory
                   https://github.com/caperock/db2monitor
'''

@singleton
class Interface:
  def __init__(self, config = None, logger = None, query_retries = 2 ) :
    '''
    config = object from utils.GetConfig
    logger = object from utils.SetLogger
    query_retries = amount of times it will try to re-execute ( and reconnect ) a query before fails
    '''
    self.config            = config
    self.logger            = logger
    if not self.config or not self.logger :
      raise Exception('Missing Mandatory Parameters Error')
    self.conn              = None
    self.db_info           = None
    self.sql_dir           = os.path.join(os.path.dirname(os.path.abspath(__file__)),"sql")
    self.query_retries     = query_retries


    return(None)

  def __enter__(self) :
    self.connect()
    return(self)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.disconnect()
    return(None)

  def disconnect(self) -> bool :
    ret = False
    try :
      if not ibm_db.close(self.conn) :
        self.logger.post_msg("Error closing conn %s"%ibm_db.conn_errormsg())
      else :
        ret = True
    except Exception as e :
      self.logger.post_msg(e)
    return(ret)

  def info(self) :
    '''
    wrap around ibm_db.server_info
    '''
    if not self.db_info :
      self.db_info = ibm_db.server_info(self.conn)
    return(self.db_info)

  def connect(self) -> bool :
    ret = False
    try :
      self.conn = ibm_db.pconnect(self.config['DB']['conn'], "", "")
      ret = True
    except Exception as e :
      self.logger.post_msg(e)
    return(ret)

  def uptime(self) -> int:
    '''
    Return seconds since the server is up
    '''
    ret = 0
    try :
      result = self.exec(LoadSQL(os.path.join(self.sql_dir,'uptime.sql')))
      db_uptime = datetime.now() - self.fetch(result)[0]
      ret = int(db_uptime.seconds)
    except Exception as e :
      self.logger.post_msg(e)
    return(ret)

  @lru_cache(maxsize=4)
  def deadlocks(self) -> tuple :
    '''
    Return a tuple with :
      - amount of deadlocks
      - amount of lock_waits
      - Statement execution time
      - time waited on locks
    '''
    ret = (0,0,0,0)
    try :
      result = self.exec(LoadSQL(os.path.join(self.sql_dir,'deadlocks.sql')))
      row = self.fetch(result)
      ret = ( int(row[0]), int(row[1]), int(row[2]), int(row[3]) )

    except Exception as e :
      self.logger.post_msg(e)
    return(ret)

  def online_users(self) -> dict :
    '''
    Return
      { 'db' : 10 }
    '''
    ret = {}
    try :
      result = self.exec(LoadSQL(os.path.join(self.sql_dir,'online_users.sql')))
      row = self.fetch(result)
      while row :
        ret[row[0].strip()] = int(row[1])
        row = self.fetch(result)
    except Exception as e :
      self.logger.post_msg(e)
    return(ret)


  def exec(self,query, attempt=0) :
    ret = None
    try :
      ret = ibm_db.exec_immediate(self.conn, query)
      if not ret and attempt < self.query_retries :
        if self.connect() :
          ret = self.exec(query, attempt = attempt+1)
    except Exception as e :
      self.logger.post_msg("%s : %s"%(e,ibm_db.stmt_errormsg()))
    return(ret)

  def fetch_all(self,result) -> list:
    ret = []
    row = self.fetch(result)
    while row :
      ret.append(row)
      row = self.fetch(result)
    return(ret)

  def fetch(self,result) :
    ret = None
    try :
      ret = ibm_db.fetch_tuple(result)
    except Exception as e :
      self.logger.post_msg(e)
    return(ret)


'''
  bufferpool_hit.sql
bufferpool_size.sql
get_memory_pool.sql
get_mem_usage.sql
get_version.sql
health_db_hi.sql
lock_time.sql
lock_waits.sql
log_utilization.sql
system_resources.sql
tblspace_size.sql
'''
