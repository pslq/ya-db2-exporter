from .__singleton import singleton
@singleton
class SetLogger:
  def __init__(self,log_level:int=10, stdout:bool=False, name:str=__name__, to_dev_log:bool=True, dst_file = None) :
    import importlib.util, logging, logging.handlers, os.path
    self.logger = logging.getLogger(name)
    self.log_level = log_level
    self.stdout = stdout
    self.name = name
    self.to_dev_log = to_dev_log
    self.dst_file = dst_file

    try :
      if os.path.exists(os.path.dirname(dst_file)) :
        self.logger.addHandler(logging.handlers.RotatingFileHandler(dst_file, maxBytes=10485760, backupCount=90))
      else :
        self.post_mgs('Error when trying to use %s as logfile'%dst_file, on_screen=True, flush=True)
    except:
      pass

    if stdout == True :
      self.logger.addHandler(logging.StreamHandler())

    if to_dev_log :
      if os.path.exists('/dev/log') :
        self.logger.addHandler(logging.handlers.SysLogHandler(address = '/dev/log'))

    if importlib.util.find_spec('systemd') is not None :
      from systemd import journal
      self.logger.addHandler(journal.JournalHandler())

    ch = logging.StreamHandler()
    ch.setLevel(self.log_level)
    formatter = logging.Formatter('%(name)s - %(message)s')
    ch.setFormatter(formatter)
    self.logger.addHandler(ch)

    return(None)

  def post_msg(self,msg:str, on_screen:bool = False, end:str='\n', \
                           flush:bool=False, raise_type=None,
                           pre_str:str = "") -> None:
    from sys import stderr as sys_stderr
    from sys import stdout as sys_stdout

    try :
      try:
        cur_level = self.logger.getEffectiveLevel()
        if   cur_level >= 40 :
          self.logger.error(msg)
        elif cur_level >= 30 :
          self.logger.warning(msg)
        elif cur_level >= 20 :
          self.logger.info(msg)
        elif cur_level >= 10 :
          self.logger.debug(msg)
        if on_screen :
          print(msg, file=sys_stderr, end=end, flush=flush)
        if raise_type :
          raise raise_type(msg)
      except Exception as e :
        raise raise_type(msg)
    except Exception as e:
      raise Exception(e)
    return(None)

