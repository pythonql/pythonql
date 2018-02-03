# Interface for the data source used in queries.
# Currently only includes query capabilities.

class Source:
  def __init__(self):
    None

  def isQueryable(self):
    return False

  # Check if the source will support the execution of an expression,
  # given that clauses have already been pushed into it.

  def supports(self,clauses,expr,visible_vars):
    return False

# Database source for all relational database sources. Currently there is
# no common functionality across different RDBMS sources

class RDBMSTable(Source):
  def isQueryable(self):
    return True
