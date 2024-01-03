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
        'deadlocks' : (Gauge('database_deadlocks_total', 'Concurrent of deadlocks running'), self.__db.deadlocks())
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
