import utils,sys,db2,prom

ret = -1
config = utils.GetConfig()
with db2.Interface(**config) as DB :
  ret = prom.Main(db = DB, **config).server()

sys.exit(ret)
