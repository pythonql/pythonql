from pythonql.PQTuple import PQTuple
import types

# The tuples that are used within the processor, as well as
# in the return values

def wrap_tuples(list,schema):
  _schema = {n:i for (i,n) in schema }
  for item in list:
    yield PQTuple(item,_schema)

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

def print_table(tuples,max_len=0):

  def fit(str,max_len):
    if len(str)<=max_len:
      return str + " " * int((max_len - len(str))*1.8)
    else:
      return str[0:max_len]

  if not tuples:
    return

  schema = [ x[0] for x in sorted(tuples[0].schema.items(), key=lambda z:z[1] ) ]

  lengths = [0]* len(tuples[0].tuple)
  for x in range(len(tuples[0].tuple)):
    lengths[x] = max([ len(repr(y[x])) for y in tuples ] + [len(schema[x])])
    if max_len:
      lengths[x] = lengths[x] if lengths[x]<max_len else max_len

  print( " | ".join( [ fit(x, lengths[i]) for (i,x) in enumerate(schema) ] ))
  print( "-".join( [ fit('-'*len(x), lengths[i]) for (i,x) in enumerate(schema) ] ))
  for t in tuples:
    print( " | ".join( [fit(repr(x), lengths[i]) for (i,x) in enumerate(t.tuple) ] ))
  print()
