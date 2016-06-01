from pythonql.PQTuple import PQTuple
from pythonql.PQTable import PQTable
from pythonql.Window import processWindowClause

# isList predicate for path expressions
def isList(x):
  return hasattr(x,'__iter__') and not hasattr(x,'keys')

# isMap predicate for path expression
def isMap(x):
  return hasattr(x,'keys')

# Implement a child step on some collection or map
def PQChildPath (coll):
  if isList(coll):
    for i in coll:
      if isList(i):
        for j in i:
          yield j
      elif isMap(i):
        for j in i.keys():
          yield i[j]
  if isMap(coll):
    for i in coll.keys():
      yield coll[i]

# Implement a descendents path on some collection or map
def PQDescPath(coll):
  stack = []
  if isList(coll):
    stack = [i for i in coll]
  elif isMap(coll):
    stack = list(coll.values())
  while stack:
    i = stack.pop()
    yield i
    if isList(i):
      [stack.append(j) for j in i[1:]]
      if isList(i[0]):
        stack.extend([ci for ci in i[0]])
      elif isMap(i[0]):
        stack.extend(i[0].values())
      yield i[0]
    elif isMap(i):
      keys = list(i.keys())
      [stack.append(i[j]) for j in keys[1:]]
      yield i[keys[0]]

#Implements a predicate step on a collection
def PQPred(coll, pred):
  if isList(coll):
    return PQPred_list(coll,pred)
  elif isMap(coll):
    return PQPred_map(coll,pred)

def PQPred_list(coll,pred):
  lcs = locals()
  for i in coll:
    lcs.update({'item':i})
    if eval(pred,globals(),lcs):
      yield i

def PQPred_map(coll,pred):
  lcs = locals()
  result = {}
  for (k,v) in coll.items():
    lcs.update({'key':k, 'value':v})
    if eval(pred,globals(),lcs):
      result[k] = v
  return result

def PQTry( try_expr, except_expr, exc, lcs):
  if exc:
    try:
      return eval(try_expr,lcs,globals())
    except eval(exc):
      return eval(except_expr,lcs,globals())
  else:
    try:
      return eval(try_expr,lcs,globals())
    except:
      return eval(except_expr,lcs,globals())

# create a table with an empty tuple
def emptyTuple(schema):
  return PQTuple([None] * len(schema), schema)

# Execute the query
def PyQuery( clauses, prior_locs ):
  table = PQTable([])
  table.data.append( emptyTuple([]) )
  for c in clauses:
    table = processClause(c, table, prior_locs)
  return table.data

# Process clauses
def processClause(c, table, prior_locs):
  if c["name"] == "select":
    return processSelectClause(c, table, prior_locs)
  elif c["name"] == "for":
    return processForClause(c, table, prior_locs)
  elif c["name"] == "let":
    return processLetClause(c, table, prior_locs)
  elif c["name"] == "count":
    return processCountClause(c, table, prior_locs)
  elif c["name"] == "where":
    return processWhereClause(c, table, prior_locs)
  elif c["name"] == "groupby":
    return processGroupByClause(c, table, prior_locs)
  elif c["name"] == "orderby":
    return processOrderByClause(c, table, prior_locs)
  elif c["name"] == "window":
    return processWindowClause(c, table, prior_locs)
  else:
    raise Exception("Unknown clause %s encountered" % c[0] )
  
# Process Select clause
# We still keep that feature of generating tuples for now
def processSelectClause(c, table, prior_lcs):
  # Compute the output schema
  select_schema = { (sel[1] if sel[1] else sel[0]) : i 
			for (i,sel) in enumerate(c["select_list"]) }
  # Create a new table that will be filled out by this
  # method
  new_table = PQTable(select_schema)

  # Compile all the expressions
  comp_exprs = [ s[0].lstrip() for s in c["select_list"] ]
  comp_exprs = [ compile(e,'<string>','eval') for e in comp_exprs ]
  for t in table.data:
    # Compute the value of tuple elements
    new_tuple = []
    for (i,sel) in enumerate(c["select_list"]):
      lcs = prior_lcs
      lcs.update(t.getDict())
      new_tuple.append( eval(comp_exprs[i], globals(), lcs))

    # If we have only one element in the select list
    # then the output table will be a sequence of values
    if len(c["select_list"]) == 1:
      new_table.data.append(new_tuple[0])

    # Otherwise we'll create tuples in the output
    else:
      new_table.data.append(PQTuple( new_tuple, select_schema))

  return new_table

# Process the for clause. This clause creates a cartesian
# product of the input table with new sequence
def processForClause(c, table, prior_lcs):
  new_schema = dict(table.schema)
  new_schema[c["var"]] = len(table.schema)
  comp_expr = compile(c["expr"].lstrip(), "<string>", "eval")

  new_table = PQTable( new_schema )
  for t in table.data:
    lcs = prior_lcs
    lcs.update(t.getDict())
    vals = eval(comp_expr, globals(), lcs)
    for v in vals:
      new_t_data = list(t.tuple)
      new_t_data.append(v)
      new_t = PQTuple(new_t_data, new_schema)
      new_table.data.append(new_t)

  return new_table

# Process the let clause. Here we just add a variable to each
# input tuple
def processLetClause(c, table, prior_lcs):
  new_schema = dict(table.schema)
  new_schema[ c["var"]] = len(table.schema)
  comp_expr = compile(c["expr"].lstrip(), "<string>", "eval")
  new_table = PQTable( new_schema )
  for t in table.data:
    lcs = prior_lcs
    lcs.update(t.getDict())
    v = eval(comp_expr, globals(), lcs)
    new_t = PQTuple( t.tuple + [v], new_schema )
    new_table.data.append(new_t)
  return new_table

# Process the count clause. Similar to let, but simpler
def processCountClause(c, table, prior_lcs):
  new_schema = dict(table.schema)
  new_schema[ c["var"]] = len(table.schema)
  new_table = PQTable( new_schema )
  for (i,t) in enumerate(table.data):
    new_t = PQTuple( t.tuple + [i], new_schema )
    new_table.data.append(new_t)
  return new_table

# Process the group-by
def processGroupByClause(c, table, prior_lcs):
  groupby_list = c["groupby_list"]
  grp_table = {}

  # Group tuples in a hashtable
  for t in table.data:
    k = tuple( [t[k] for k in groupby_list] )
    if not k in grp_table:
      grp_table[k] = []
    grp_table[k].append(t)

  # Construct the new table
  # Non-key variables
  non_key_vars = [v for v in table.schema if not v in groupby_list ]
  new_schema = {v:i for (i,v) in enumerate( groupby_list + non_key_vars )}
  new_table = PQTable(new_schema)
  for k in grp_table:
    t = PQTuple([None]*len(new_schema), new_schema)
    #Copy over the key
    for (i,v) in enumerate(groupby_list):
      t[v] = k[i]

    #Every other variable (not in group by list) is turned into a lists
    #First create empty lists
    for v in non_key_vars:
      t[v] = []

    # Now fill in the lists:
    for part_t in grp_table[k]:
      for v in non_key_vars:
        t[v].append( part_t[v] )

    new_table.data.append(t)

  return new_table

# Process where clause
def processWhereClause(c, table, prior_lcs):
  new_table = PQTable(table.schema)
  comp_expr = compile(c["expr"].lstrip(),"<string>","eval")
  for t in table.data:
    lcs = prior_lcs
    lcs.update(t.getDict())
    val = eval(comp_expr, globals(), lcs)
    if val:
      new_table.data.append(t)

  return new_table

# Process the orderby clause
def processOrderByClause(c, table, prior_lcs):
  # Here we do n sorts, n is the number of sort specifications
  # For each sort we first need to compute a sort value (could
  # be some expression)

  sort_exprs = [ compile(os[0].lstrip(),"<string>","eval") for os in c["orderby_list"]]
  sort_rev = [ o[1]=='desc' for o in c["orderby_list"]]

  def computeSortSpec(tup,sort_spec):
    lcs = prior_lcs
    lcs.update(tup.getDict())
    return eval(sort_spec, globals(), lcs)

  sort_exprs.reverse()
  sort_rev.reverse()
  for (i,e) in enumerate(sort_exprs):
    table.data.sort( key = lambda x: computeSortSpec(x,e),
         reverse= sort_rev[i])

  return table
  
if __name__=='__main__':
  x = [ 2, 4, 6, 8, 10, 12, 14 ]
  res = PyQuery ( 
        [{"name":"window", "tumbling":False, "in":"x", "only":False,
         "vars":{"var":"y", "s_curr":"s_c", "s_at":"s", "s_prev":"s_prev", "s_next":"s_next",
           "e_curr":"e_c", "e_at":"e", "e_prev":"e_prev", "e_next":"e_next"},
           "s_when":"True", "e_when":"e-s == 2"},
	{"name":"select", "select_list": [("y",None)] }
	],
	locals())
  print(res)
