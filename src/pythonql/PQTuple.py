# The tuples that are used within the processor, as well as
# in the return values

class PQTuple:
  def __init__(self,tuple,schema):
    self.tuple = tuple
    self.schema = schema

  def __getattr__(self,attr):
    return self.tuple[ self.schema[attr] ]

  def __getitem__(self,item):
    if isinstance(item,int):
      return self.tuple[item]
    else:
      return self.tuple[ self.schema[item] ]

  def getDict(self):
    res = {}
    for v in self.schema:
      res[ v ] = self.tuple[ self.schema[v] ]
    return res

  def __setitem__(self,item,value):
    self.tuple[ self.schema[item] ] = value

  def copy(self):
    return PQTuple(list(self.tuple), self.schema)

  def __repr__(self):
    #print(self.schema)
    #print(self.tuple)
    itms = list(self.schema.items())
    itms.sort(key=lambda x:x[1])
    return "{" + ",".join([ '"%s":%s' % (i[0].lstrip().rstrip(), repr(self.tuple[i[1]]))  for i in itms]) + "}"

def pq_wrap(list,schema):
  for item in list:
    yield PQTuple(item,schema)

