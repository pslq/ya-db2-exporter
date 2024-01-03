from prometheus_client import Gauge, Counter, Summary

from utils import singleton
from typing import Any

@singleton
class Metrics :
  def __init__(self, db) -> None :
    self.__db = db

    # Prometheus vars
    self.__metrics = {}

    self.__metric_desc = {
        'uptime' : (Gauge('database_uptime_seconds', 'Instance uptime in seconds'), self.__db.uptime()),

        'deadlocks' : (Gauge('database_deadlocks_total', 'Concurrent of deadlocks running'), self.__lock_stuff('deadlocks')),
        'lock_waits' : (Gauge('database_lock_waits_total', 'Amount of lock waits'), self.__lock_stuff('lock_waits')),
        'statement_execution_time' : (Gauge('database_statement_execution_time_seconds', 'Amount of time takes to a statement to run'), self.__lock_stuff('statement_execution_time')),
        'time_waited_on_locks' : (Gauge('database_time_waited_on_locks_seconds', 'Time spent waiting on locks'), self.__lock_stuff('time_waited_on_locks')),
                          }
    self.__metric_function = {}

    return(None)

  def online_users_total(self) :
    cur_reading = self.__db.online_users()
    if 'online_users' not in self.__metrics :
      self.__metrics['online_users'] = Gauge("online_users_total", "Online users per database", [ 'database' ] )

    for k,v in cur_reading.items() :
      self.__metrics['online_users'].labels(database=k).set(v)
    return(self.__metrics['online_users'])

  # Just a helper around my lazy deadlock db2 function
  # Something for my future me fix
  def __lock_stuff(self,name) :
    return(self.__db.deadlocks()[( 'deadlocks', 'lock_waits', 'statement_execution_time', 'time_waited_on_locks' ).index(name)])

  def standard_metric(self,name) -> Any :
    ret = None
    try :
      cur_reading = self.__metric_desc[name][1]
      try :
        self.__metrics[name].set(cur_reading)
      except :
        self.__metrics[name] = self.__metric_desc[name][0]
        self.__metrics[name].set(cur_reading)
      ret = self.__metrics[name]
    except Exception as e :
      raise Exception(e)
    return(ret)
