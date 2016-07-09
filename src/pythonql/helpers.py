from pythonql.PQTuple import PQTuple
import types

# The tuples that are used within the processor, as well as
# in the return values

def wrap(list,schema):
  for item in list:
    yield PQTuple(item,schema)

def flatten(nested_list):
  if isinstance(nested_list,list) or isinstance(nested_list,types.GeneratorType):
    for i in nested_list:
      if isinstance(i,list) or isinstance(i,types.GeneratorType):
        for x in flatten(i):
          yield x
      else:
        yield i
  else:
    yield nested_list

def empty(seq):
  if isinstance(seq,types.GeneratorType):
    try:
      next(seq)
      return False
    except:
      return True
  else:
    try:
      seq[0]
      return False
    except:
      return True

