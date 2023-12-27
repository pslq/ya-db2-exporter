def singleton(cls) :
  """
  Decorator to generate a singleton, prevents
  from creating multiple instances of a class

  Borrowed the idea from: https://github.com/Thunderbottom/prometheus-exporter-py/blob/master/prometheus_exporter/__init__.py
  """
  instance = None

  def get_instance(*args, **kwargs):
    nonlocal instance
    if instance is None:
      instance = cls(*args, **kwargs)
    return instance

  return get_instance

