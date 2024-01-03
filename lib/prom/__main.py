from .__metrics import Metrics
from typing import Any
from prometheus_client import start_http_server
import time



class Main:
  def __init__(self, db = None, config = None, logger = None ) :
    self.db = db
    self.config = config
    self.logger = logger
    self.db2_metrics = Metrics(self.db)
    self.running_metrics = {}
    return(None)

  def landing_page(self) :
    return(None)

  def run_exporters(self) -> None :
    try :
      for exp in self.config['PROM']['exporters'].strip().split(',') :
        metric = exp.strip().lower()
        if metric == "online_users" :
          self.running_metrics["online_users"] = self.db2_metrics.online_users_total()
        else :
          self.running_metrics[metric] =  self.db2_metrics.standard_metric(metric)

    except Exception as e :
      self.logger.post_msg("Error initalizing exporters %s"%e)
    return(None)

  def server(self) -> int:
    port = int(self.config['HTTP']['port'].strip())
    interval = int(self.config['PROM']['interval'].strip())
    self.logger.post_msg("Starting Exporter at port %d, with a collection interval of %d"%(port,interval), on_screen=True)
    start_http_server(port)
    while 1 :
      self.run_exporters()
      time.sleep(interval)
    return(0)
