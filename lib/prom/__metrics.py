from prometheus_client import Gauge, Counter, Enum

from utils import singleton
from typing import Any

@singleton
class Metrics :
  def __init__(self, db) -> None :
    self.__db = db

    # Prometheus vars
    self.__metrics = {}

    # Dict where I hold basic, or functions that return a single value
    self.__metric_function = {}

    return(None)

  #############################################################
  def online_users_total(self) :
    cur_reading = self.__db.online_users()
    try :
      for k,v in cur_reading.items() :
        self.__metrics['online_users'].labels(database=k).set(v)
    except KeyError:
      self.__metrics['online_users'] = Gauge("db2_online_users_total", "Online users per database", labelnames=[ 'database' ] )
      for k,v in cur_reading.items() :
        self.__metrics['online_users'].labels(database=k).set(v)
    except Exception as e :
      raise Exception('online_users_total %s Error'%e)
    return(self.__metrics['online_users'])

  #############################################################
  def event_monitors(self) :
    cur_reading = self.__db.event_monitors()
    try :
      for k,v in cur_reading.items() :
        self.__metrics['database_event_monitors']['activates'].labels(evmonname=k).set(v[3])
        self.__metrics['database_event_monitors']['autostart'].labels(evmonname=k).state(v[2])
    except KeyError:
      self.__metrics['database_event_monitors'] = { 'activates' : Gauge("db2_event_monitors_activates", "Activations per event monitor", labelnames=['evmonname']),
                                                    'autostart' : Enum("db2_event_monitors_autostart", "If the event monitor is set to autstart", labelnames=['evmonname'], states=['Y','N'])
                                                   }
      for k,v in cur_reading.items() :
        self.__metrics['database_event_monitors']['activates'].labels(evmonname=k).set(v[3])
        self.__metrics['database_event_monitors']['autostart'].labels(evmonname=k).state(v[2])

    except Exception as e :
      raise Exception('event_monitors %s Error'%e)
    return(self.__metrics['database_event_monitors'])


  # Another helper around handling metrics, and possibly another problem for future me
  # TODO : abstract different metrics as they come
  def __handle_tuple(self,metric,description,fields,values, metric_type=Gauge, extra_metric_parameter = None) :

    # Just avoid further duplication
    def set_values(metric_type,metric,fields) :
      if metric_type.__name__ == "Gauge" :
        for n,k in enumerate(fields) :
          self.__metrics[metric].labels(field=k).set(values[n])
      return(self.__metrics[metric])

    ret = None
    try :
      ret = set_values(metric_type,metric,fields)
    except KeyError :
      if extra_metric_parameter is None :
        self.__metrics[metric] = metric_type(metric,description,labelnames=['field'])
      else :
        self.__metrics[metric] = metric_type(metric,description,labelnames=['field'], **extra_metric_parameter)
      ret = set_values(metric_type,metric,fields)

    except Exception as e :
      raise Exception('__handle_tuple:%s hit: %s Error'%(metric,e))
    return(ret)




  #############################################################
  def mon_get_instance(self) :
    cur_reading = self.__db.get_mon_get_instance()
    metric_fields = [ 'uptime', 'timezoneoffset', 'con_local_dbases', 'total_connections', 'agents_registered',
               'agents_registered_top', 'idle_agents', 'agents_from_pool', 'agents_created_empty_pool',
               'num_coord_agents', 'coord_agents_top', 'agents_stolen', 'gw_total_cons', 'gw_cur_cons',
               'gw_cons_wait_host', 'gw_cons_wait_client', 'num_gw_conn_switches' ]
    metric_description = "Metrics from mon_get_instance, uptime is extrapolated from DB2START_TIME"

    ret = self.__handle_tuple('db2_mon_get_instance', metric_description,metric_fields,cur_reading)
    return(ret)



  #############################################################
  def snapdb(self) :
    cur_reading = self.__db.snapdb()
    metric_fields = ['deadlocks_total','lock_waits_total','statement_execution_seconds','time_waited_on_locks_seconds' ]
    metric_description = "Metrics from sysibmadm.snapdb"

    ret = self.__handle_tuple('db2_snapdb', metric_description,metric_fields,cur_reading)
    return(ret)
