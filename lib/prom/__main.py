from .__metrics import Metrics
from typing import Any
from prometheus_client import start_http_server
import signal
from threading import Event



class Main:
  def __init__(self, db = None, config = None, logger = None ) :
    self.db = db
    self.config = config
    self.logger = logger
    self.db2_metrics = Metrics(self.db)
    self.running_metrics = {}
    self.__metric_output= {
        "online_users" : self.db2_metrics.online_users_total,
        "event_monitors" : self.db2_metrics.event_monitors,
        "mon_get_instance" : self.db2_metrics.mon_get_instance,
        "snapdb" : self.db2_metrics.snapdb
        }
    self.__run_loop = Event()
    # Handle signals
    signal.signal(signal.SIGTERM, self.shutdown )
    signal.signal(signal.SIGINT, self.shutdown )
    return(None)

  def shutdown(self, signum, frame) :
    self.db.disconnect()
    self.logger.post_msg("Shutdown under signal %s"%signal.Signals(signum).name)
    self.__run_loop.set()
    return(None)

  def run_exporters(self) -> None :
    for exp in self.config['PROM']['exporters'].strip().split(',') :
      metric = exp.strip().lower()
      print(metric)

      if self.config['PROM']['log_collections'] is True :
        logger.post_msg('metric %s start'%metric)

      try :
        self.running_metrics[metric] = self.__metric_output[metric]()
      except Exception as e :
        self.logger.post_msg("Error initalizing exporter %s : %s"%(metric,e))

      if self.config['PROM']['log_collections'] is True :
        logger.post_msg('metric %s end'%metric)
    return(None)


  def server(self) -> int:
    ret = 0
    port = int(self.config['HTTP']['port'].strip())
    interval = int(self.config['PROM']['interval'].strip())
    self.logger.post_msg("Starting Exporter at port %d, with a collection interval of %d"%(port,interval), on_screen=True)
    try :
      if self.config['HTTP']['use_https'] is True :
        start_http_server(port, certfile=self.config['HTTP']['certfile'], keyfile=self.config['HTTP']['keyfile'], client_auth_required=self.config['HTTP']['client_auth_required'])
      else :
        start_http_server(port)
      while not self.__run_loop.is_set() :
        try :
          self.run_exporters()
          self.__run_loop.wait(interval)
        except :
          self.shutdown(signal.SIGINT, 0)
    except Exception as e :
      self.logger.post_msg("Error: %s"%e, on_screen=True)
      ret = -1
    return(ret)
