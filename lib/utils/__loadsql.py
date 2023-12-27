def LoadSQL(file:str, specific_replacements:list=[]) -> str:
  '''
  Load and parse files
  '''
  # Replace strings if any replacement defined
  ret_str = ''

  if file:
    try :
      with open(file, 'r') as fptr :
        ret_str = fptr.read()
    except Exception as e :
      raise Exception('Error loading sqlfile : %s'%str(e))

  for r in specific_replacements :
    try :
      ret_str = ret_str.replace(r[0],r[1])
    except :
      pass

  return(ret_str)
