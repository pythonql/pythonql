# The tuples that are used within the processor, as well as
# in the return values

def str_encode(string):
    res = ""
    for ch in string:
        if ch == '"':
            res += chr(92)
            res += '"'
        elif ch == chr(92):
            res += chr(92)
            res += chr(92)
        else:
            res += ch
    return res

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

  def __iter__(self):
    return self.tuple.__iter__()

  def getDict(self):
    res = {}
    for v in self.schema:
      res[ v ] = self.tuple[ self.schema[v] ]
    return res

  def __setitem__(self,item,value):
    self.tuple[ self.schema[item] ] = value

  def copy(self):
    return PQTuple(list(self.tuple), self.schema)

  def __lt__(self,other):
    if isinstance(other, self.__class__):
      if self.schema == other.schema:
        return self.tuple < other.tuple
      else:
        return False
    elif isinstance(other, tuple):
      return self.tuple < other
    else:
      return False

  def __eq__(self,other):
    if isinstance(other, self.__class__):
      if self.schema == other.schema:
        return self.tuple == other.tuple
      else:
        return False
    elif isinstance(other, tuple):
      return self.tuple == other
    else:
      return False

  def __gt__(self,other):
    if isinstance(other, self.__class__):
      if self.schema == other.schema:
        return self.tuple > other.tuple
      else:
        return False
    elif isinstance(other, tuple):
      return self.tuple > other
    else:
      return False

  def __le__(self,other):
    return self.__gt__(other) or self.__eq__(other)

  def __ge__(self,other):
    return self.__gt__(other) or self.__eq__(other)

  def __ne__(self,other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash(self.tuple)

  def __repr__(self):
    #print(self.schema)
    #print(self.tuple)
    itms = list(self.schema.items())
    itms.sort(key=lambda x:x[1])
    return "{" + ",".join([ '"%s":%s' % (str_encode(i[0].lstrip().rstrip()), repr(self.tuple[i[1]]))  for i in itms]) + "}"
