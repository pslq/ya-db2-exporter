#######################################################################################################################
def GetConfig(log_start=False, default_config_file='ya-db2-exporter.conf', config_path:str='') -> dict :
  '''
  Function to get current logging and configuration parameters
  Parameters :
    log_start           -> [True,False] : write a message at log file, informing which config file is being used
    default_config_file -> str : Default filename used
    config_path         -> str : Specific config file to be loaded ( usefull for debug )

  Returns:
    Two variables:
    config, logger
      config -> configparser object
      logger -> pq_logger object
  '''
  import configparser, os.path, shutil, logging, importlib.util, os
  from .__logger import SetLogger

  if len(config_path) == 0 :
    if importlib.util.find_spec('xdg.BaseDirectory') :
      import xdg.BaseDirectory
      search_path = [ xdg.BaseDirectory.xdg_config_home ]
    elif importlib.util.find_spec('xdg') :
      import xdg
      try :
        search_path = [ str(xdg.XDG_CONFIG_HOME) ]
      except :
        search_path = [ os.getenv('HOME') ]
    else :
      search_path = [ os.getenv('HOME') ]

    search_path = search_path + [ '/etc' , '/opt/freeware/etc' ]
    config_path = None

    for ph in search_path :
      full_path = os.path.join(ph,default_config_file)
      if os.path.exists(full_path) :
        config_path = full_path
        break

  if not config_path :
    new_config_path = os.path.join(search_path[0],default_config_file)
    try :
      template_file = os.path.join(os.path.dirname(importlib.util.find_spec('ya-db2-exporter').origin),'ya-db2-exporter.conf.template')
    except :
      template_file = os.path.join(os.getcwd(),'ya-db2-exporter.conf.template')
    try :
      shutil.copy(template_file,new_config_path)
      config_path = new_config_path
      print('Configuration not found at %s, writting new one at %s'%(' '.join(search_path), new_config_path),flush=True)
    except Exception as e :
      raise SystemError(e)

  config = configparser.ConfigParser()
  if not config_path :
      raise SystemError('No config file could be either located or created, need at least be able to write a new one at %s'%search_path[0])
  else :
    config.read(config_path)

    # Logging configuration
    log_level = logging.INFO
    if config['LOG']['log_level'] == "DEBUG" :
      log_level = logging.DEBUG
    log_file = None
    to_dev_log = True
    if len(config['LOG']['log_file']) > 0 :
      log_file = config['LOG']['log_file']
      to_dev_log = False

    logger = SetLogger(log_level = log_level, stdout = False, name = 'ya-db2-exporter', to_dev_log = to_dev_log, dst_file = log_file)

    try:
      import setproctitle
      setproctitle.setproctitle("ya-db2-exporter")
    except ImportError:
        pass

    if log_start :
      logger.post_msg('Using config file: %s'%config_path, on_screen=True, flush=True)

  return({ "config" : config, "logger" : logger})
