from pandas import DataFrame
from pythonql.PQTuple import PQTuple

def to_df(query_res,columns=[]):
  it = iter(query_res)

  try:
    first = next(it)

    if isinstance(first,PQTuple) and not columns:
      schema = first.schema.items()
      cols = [k for (k,v) in sorted(schema, key=lambda x:x[0])]
      return DataFrame.from_records([first] + [x for x in it], columns=cols)

    elif columns:
      return DataFrame.from_records([first] + [x for x in it], columns=columns)

    else:
      return DataFrame([first] + [x for x in it])

  except:
    return DataFrame.from_records([],columns=columns)

def wrap_df(df):
  schema = { n:i for (i,n) in enumerate(df.columns) }
  for t in df.itertuples(False):
    yield PQTuple(t,schema)
