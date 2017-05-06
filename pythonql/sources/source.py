class Source:
  def __init__(self):
    None

  def isQueryable(self):
    return False

  def supportsOp(self):
    return True

class RDBMSTable(Source):
  def isQueryable(self):
    return True
