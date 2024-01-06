import ibm_db, os.path
from utils import LoadSQL, singleton
from datetime import datetime

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

  def get_mon_get_instance(self) -> tuple:
    '''
    Return a tuple with ( <uptime in seconds>, TIMEZONEOFFSET, CON_LOCAL_DBASES, TOTAL_CONNECTIONS, AGENTS_REGISTERED, AGENTS_REGISTERED_TOP,
  IDLE_AGENTS, AGENTS_FROM_POOL, AGENTS_CREATED_EMPTY_POOL, NUM_COORD_AGENTS, COORD_AGENTS_TOP, AGENTS_STOLEN,
  GW_TOTAL_CONS, GW_CUR_CONS, GW_CONS_WAIT_HOST, GW_CONS_WAIT_CLIENT, NUM_GW_CONN_SWITCHES )
    '''
    ret = ( 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 )
    try :
      result = self.exec(LoadSQL(os.path.join(self.sql_dir,'mon_get_instance.sql')))
      row = self.fetch(result)
      db_uptime = datetime.now() - row[0]
      ret = (int(db_uptime.seconds),) + row[1:]
    except Exception as e :
      self.logger.post_msg(e)
    return(ret)

  def snapdb(self) -> tuple :
    '''
    Return a tuple with :
      - amount of deadlocks
      - amount of lock_waits
      - Statement execution time
      - time waited on locks
    '''
    ret = (0,0,0,0)
    try :
      result = self.exec(LoadSQL(os.path.join(self.sql_dir,'snapdb.sql')))
      row = self.fetch(result)
      ret = ( int(row[0]), int(row[1]), int(row[2]), int(row[3]) )

    except Exception as e :
      self.logger.post_msg(e)
    return(ret)

  def event_monitors(self) -> dict :
    '''
    Return a dict with tuples
    Ref.: https://www.ibm.com/docs/en/db2oc?topic=views-syscateventmonitors
      { 'EVMONNAME' : ('EVENT_TYPE', 'OWNER', 'AUTOSTART', EVMON_ACTIVATES)}

    '''
    ret = { }
    try :
      result = self.exec(LoadSQL(os.path.join(self.sql_dir,'event_monitors.sql')))
      row = self.fetch(result)
      while row :
        ret[row[0].strip()] = ( row[1],row[2],row[3],row[4] )
        row = self.fetch(result)
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
