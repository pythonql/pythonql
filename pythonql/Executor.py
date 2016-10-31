from pythonql.PQTuple import PQTuple
from pythonql.PQTable import PQTable
from pythonql.helpers import flatten
import json
import types

def make_pql_tuple(vals,lcs):
  t = []
  als = []
  for v in vals:
    t.append(eval(v[0],lcs,globals()))
    alias = v[1] if v[1] else v[0]
    als.append(alias)

  schema = {n:i for (i,n) in enumerate(als)}
  return PQTuple(t,schema)

def str_dec(string):
    res = ""
    prev_slash = False
    for ch in string:
        if ch == chr(92):
            if not prev_slash:
                prev_slash = True
            else:
                res += ch
                prev_slash = False
        else:
            prev_slash = False
            res += ch
    return res

# isList predicate for path expressions
def isList(x):
  return (hasattr(x,'__iter__') and not 
          hasattr(x,'keys') and not
          isinstance(x,str))

# isMap predicate for path expression
def isMap(x):
  return hasattr(x,'keys')

# Implement a child step on some collection or map
def PQChildPath (coll,f,lcs):
  f = eval(str_dec(f), globals(), lcs) if f!='_' else None
  if isList(coll):
    for i in flatten(coll):
      if isMap(i):
        for j in i.keys():
          if f is None:
            yield i[j]
          elif f and j==f:
            yield i[j]

  if isMap(coll):
    for i in coll.keys():
      if f is None:
        yield coll[i]
      elif f and i==f:
        yield coll[i]

class map_tuple:
  def __init__(self,key,value):
    self.key = key
    self.value = value

  def __repr__(self):
    return ("<" + repr(self.key) + ":" + repr(self.value) + ">")

# Implement a descendents path on some collection or map
def PQDescPath(coll,f,lcs):
  f = eval(f,globals(),lcs) if f!='_' else None
  stack = []
  if isList(coll):
    stack = [i for i in flatten(coll)]
  elif isMap(coll):
    stack = [map_tuple(k,v) for (k,v) in coll.items()]

  while stack:
    i = stack.pop()

    if isinstance(i,map_tuple):
      if f is None:
        yield i.value
      elif f and i.key==f:
        yield i.value

      i = i.value

    if isList(i):
      it = iter(i)
      frst = next(it)
      [stack.append(j) for j in it]
      if isList(frst):
        stack.extend([ci for ci in frst])
      elif isMap(frst):
        stack.extend([map_tuple(k,v) for (k,v) in frst.items()])

    elif isMap(i):
      keys = list(i.keys())
      [stack.append(map_tuple(j,i[j])) for j in keys]

def PQTry( try_expr, except_expr, lcs):
  try_expr = str_dec(try_expr)
  except_expr = str_dec(except_expr)
  try:
    return eval(try_expr,lcs,globals())
  except:
    return eval(except_expr,lcs,globals())

# create a table with an empty tuple
def emptyTuple(schema):
  return PQTuple([None] * len(schema), schema)

# Execute the query
def PyQuery( clauses, prior_locs, returnType ):
  data = []
  data.append( emptyTuple([]) )
  for c in clauses:
    data = processClause(c, data, prior_locs)
  if returnType == "gen":
    return data
  elif returnType == "list":
    return list(data)
  elif returnType == "set":
    return set(data)
  else:
    return dict(data)

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
  # If this is a list/set comprehension:
  if "expr" in c:
    # Compile the expression:
    e = compile(c["expr"].lstrip(), '<string>','eval')
    for t in table:
      lcs = prior_lcs
      lcs.update(t.getDict())
      yield eval(e,globals(),lcs)

  else:
    k_expr = compile(c["key"].lstrip(),'<string>','eval')
    v_expr = compile(c["value"].lstrip(),'<string>','eval')
    for t in table:
      lcs = prior_lcs
      lcs.update(t.getDict())
      k = eval(k_expr,globals(),lcs)
      v = eval(v_expr,globals(),lcs)
      yield (k,v)

# Process the for clause. This clause creates a cartesian
# product of the input table with new sequence
def processForClause(c, table, prior_lcs):
  new_schema = None
  comp_expr = compile(c["expr"].lstrip(), "<string>", "eval")

  new_table = PQTable( new_schema )
  for t in table:
    if not new_schema:
      new_schema = dict(t.schema)
      new_schema[c["var"]] = len(t.schema)

    lcs = prior_lcs
    lcs.update(t.getDict())
    vals = eval(comp_expr, globals(), lcs)
    for v in vals:
      new_t_data = list(t.tuple)
      new_t_data.append(v)
      new_t = PQTuple(new_t_data, new_schema)
      yield new_t


# Process the let clause. Here we just add a variable to each
# input tuple
def processLetClause(c, table, prior_lcs):
  comp_expr = compile(c["expr"].lstrip(), "<string>", "eval")
  new_schema = None
  for t in table:

    if not new_schema:
      new_schema = dict(t.schema)
      new_schema[c["var"]] = len(t.schema)

    lcs = prior_lcs
    lcs.update(t.getDict())
    v = eval(comp_expr, globals(), lcs)
    t.tuple.append(v)
    new_t = PQTuple( t.tuple, new_schema )
    yield new_t

# Process the count clause. Similar to let, but simpler
def processCountClause(c, table, prior_lcs):
  new_schema = None
  for (i,t) in enumerate(table):

    if not new_schema:
      new_schema = dict(t.schema)
      new_schema[c["var"]] = len(t.schema)

    new_t = PQTuple( t.tuple + [i], new_schema )
    yield new_t

# Process the group-by
def processGroupByClause(c, table, prior_lcs):
  gby_aliases = [g if isinstance(g,str) else g[1]
                                for g in c["groupby_list"]]
  gby_exprs = [g if isinstance(g,str) else g[0]
                                for g in c["groupby_list"]]
  comp_exprs = [compile(e,'<string>','eval') for e in gby_exprs]
  grp_table = {}

  schema = None
  # Group tuples in a hashtable
  for t in table:
  
    if not schema:
      schema = t.schema

    lcs = prior_lcs
    lcs.update(t.getDict())
    # Compute the key
    k = tuple( [eval(e,globals(),lcs) for e in comp_exprs] )
    if not k in grp_table:
      grp_table[k] = []
    grp_table[k].append(t)

  if not grp_table:
    return
    yield

  # Construct the new table
  # Non-key variables
  non_key_vars = [v for v in schema if not v in gby_aliases ]
  new_schema = {v:i for (i,v) in enumerate( gby_aliases + non_key_vars )}
  new_table = []
  for k in grp_table:
    t = PQTuple([None]*len(new_schema), new_schema)
    #Copy over the key
    for (i,v) in enumerate(gby_aliases):
      t[v] = k[i]

    #Every other variable (not in group by list) is turned into a lists
    #First create empty lists
    for v in non_key_vars:
      t[v] = []

    # Now fill in the lists:
    for part_t in grp_table[k]:
      for v in non_key_vars:
        t[v].append( part_t[v] )

    yield t


# Process where clause
def processWhereClause(c, table, prior_lcs):
  comp_expr = compile(c["expr"].lstrip(),"<string>","eval")
  for t in table:
    lcs = prior_lcs
    lcs.update(t.getDict())
    val = eval(comp_expr, globals(), lcs)
    if val:
      yield t

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

  if isinstance(table,types.GeneratorType):
    table = list(table)

  for (i,e) in enumerate(sort_exprs):
    table.sort( key = lambda x: computeSortSpec(x,e),
         reverse= sort_rev[i])

  for t in table:
    yield t
  
# Create the set of variables for a new window
# This is the full set just for convienience, the
# query might not use all of these vars.
# The names of the variables coincide with the
# names in the specification of window clause

def make_window_vars():
  return {"s_curr":None, "s_at":None, "s_prev":None, "s_next":None,
          "e_curr":None, "e_at":None, "e_prev":None, "e_next":None}

# Start variables from a list of variables
all_start_vars = ["s_curr","s_at","s_prev","s_next"]

# Fill in the start vars of the window, given the value list and current index
def fill_in_start_vars(vars, binding_seq, i ):
  vars["s_curr"] = binding_seq[i]
  vars["s_at"] = i
  vars["s_prev"] = binding_seq[i-1] if i>0 else None
  vars["s_next"] = binding_seq[i+1] if i+1<len(binding_seq) else None

# Fill in the end vars of the window, given the values list and current index
def fill_in_end_vars(vars, binding_seq, i ):
  vars["e_curr"] = binding_seq[i]
  vars["e_at"] = i
  vars["e_prev"] = binding_seq[i-1] if i>0 else None
  vars["e_next"] = binding_seq[i+1] if i+1<len(binding_seq) else None

# Check the start condition of the window, i.e. whether we should
# start a new window at this location (without considering tumbling
# windows, that check is done elsewhere).

def check_start_condition(all_vars,clause,locals,var_mapping):
  # we just need to evaluate the when expression 
  # but we need to set up the vars correctly, respecting the visibility
  # conditions
  start_vars = set(all_start_vars).intersection(
		set(var_mapping.keys()) )
  start_bindings = { var_mapping[v] : all_vars[v] for v in start_vars }

  # add the binding to the locals
  locals.update( start_bindings )

  #evaluate the when condition
  return eval( clause["s_when"], globals(), locals )
  
# Check the end condition of the window.

def check_end_condition(vars,clause,locals,var_mapping):
  # If there is no 'when' clause, return False
  if not clause["e_when"]:
    return False

  end_vars = set(vars.keys()).intersection( set(var_mapping.keys()))
  end_binding = { var_mapping[v] : vars[v] for v in end_vars }

  locals.update( end_binding )
  res = eval( clause["e_when"], globals(), locals)

  return res

# Process window clause
def processWindowClause(c, table, prior_lcs):
  schema = None
  new_schema = None

  # Create window variable name mapping
  var_mapping = {}
  for v in c["vars"]:
    var_mapping[v] = c["vars"][v]
		
  new_table = PQTable( new_schema )
  for t in table:
    if not schema:
      schema = t.schema
      # Create a new schema with window variables added
      new_schema = dict(t.schema)
      for v in c["vars"]:
        new_schema[c["vars"][v]] = len(new_schema)

    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    # Evaluate the binding sequence
    binding_seq = list(eval(c["in"], globals(), lcs))

    # Create initial window variables

    # Initialize the windows
    open_windows = []
    closed_windows = []

    # Iterate over the binding sequence
    for (i,v) in enumerate(binding_seq):
      # Try to open a new window
      # in case of tumbling windows, only open a
      # window if there are no open windows
      if not c["tumbling"] or (c["tumbling"] and not open_windows):
        vars = make_window_vars()
        fill_in_start_vars(vars,binding_seq,i)
        if check_start_condition(vars,c,dict(lcs),var_mapping):
          open_windows.append( {"window":[], "vars":vars} )
      
      new_open_windows = []
      #update all open windows, close those that are finished
      for w in open_windows:
        # Add currnt value to the window
        w["window"].append(v)

        fill_in_end_vars(w["vars"],binding_seq,i)

        if check_end_condition(w["vars"],c,dict(lcs),var_mapping):
          closed_windows.append(w)
        else:
          new_open_windows.append(w)
      open_windows = new_open_windows
          
    #close or remove all remaining open windows
    #if only is specified, we ignore non-closed windows
    if not c["only"]:
      closed_windows.extend(open_windows)
    
    # create a new tuple by extending the tuple from previous clauses
    # with the window variables, for each closed window
    for w in closed_windows:
      new_t = PQTuple( t.tuple + [None]*(len(new_schema)-len(schema)), new_schema)
      new_t[ var_mapping["var"] ] = w["window"]
      for v in [v for v in w["vars"].keys() if v in var_mapping]:
        new_t[ var_mapping[v] ] = w["vars"][v]
      yield new_t
