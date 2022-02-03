from pythonql.algebra.operator import plan_from_list
from pythonql.algebra.operators import *
from pythonql.PQTuple import PQTuple
from pythonql.helpers import flatten
from pythonql.Rewriter import rewrite
from pythonql.debug import Debug
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

def PQTry( try_expr, except_expr, lcs, globs):
  try_expr = str_dec(try_expr)
  except_expr = str_dec(except_expr)
  try:
    return eval(try_expr,lcs,globs)
  except:
    return eval(except_expr,lcs,globs)

# create a table with an empty tuple
def emptyTuple(schema):
  return PQTuple([None] * len(schema), schema)

# Execute the query
def PyQuery( clauses, prior_locs, prior_globs, returnType ):
  data = []
  data.append( emptyTuple([]) )

  clauses = list(clauses)
  clauses.reverse()

  plan = plan_from_list(clauses)
  plan = rewrite(plan, prior_locs)

  if Debug().print_optimized:
      print("Rewritten query:",plan)
  data = plan.execute(data, prior_locs, prior_globs)
  if returnType == "gen":
    return data
  elif returnType == "list":
    return list(data)
  elif returnType == "set":
    return set(data)
  else:
    return dict(data)

# Process Select clause
# We still keep that feature of generating tuples for now
def processSelectClause(c, table, prior_lcs, prior_globs):
  # If this is a list/set comprehension:
  if c.expr:
    # Compile the expression:
    e = compile(c.expr.lstrip(), '<string>','eval')
    for t in table:
      lcs = dict(prior_lcs)
      lcs.update(t.getDict())
      yield eval(e,prior_globs,lcs)

  else:
    k_expr = compile(c.key_expr.lstrip(),'<string>','eval')
    v_expr = compile(c.value_expr.lstrip(),'<string>','eval')
    for t in table:
      lcs = prior_lcs
      lcs.update(t.getDict())
      k = eval(k_expr,prior_globs,lcs)
      v = eval(v_expr,prior_globs,lcs)
      yield (k,v)

# Process the for clause. This clause creates a cartesian
# product of the input table with new sequence
def processForClause(c, table, prior_lcs, prior_globs):
  new_schema = None
  comp_expr = compile(c.expr.lstrip(), "<string>", "eval")

  for t in table:
    if not new_schema:
      new_schema = dict(t.schema)
      for (i,v) in enumerate(c.vars):
        new_schema[v] = len(t.schema) + i

    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    vals = eval(comp_expr, prior_globs, lcs)
    if len(c.vars) == 1:
      for v in vals:
        new_t_data = list(t.tuple)
        new_t_data.append(v)
        new_t = PQTuple(new_t_data, new_schema)
        yield new_t
    
    else:
      for v in vals:
        unpack_expr = "[ %s for %s in [ __v ]]" % (
                      '(' + ",".join(c.vars) + ')', c.unpack)
        unpacked_vals = eval(unpack_expr, prior_globs, {'__v':v})
        new_t_data = list(t.tuple)
        for tv in unpacked_vals[0]:
          new_t_data.append(tv)
        new_t = PQTuple(new_t_data, new_schema)
        yield new_t

# Process the let clause. Here we just add a variable to each
# input tuple
def processLetClause(c, table, prior_lcs, prior_globs):
  comp_expr = compile(c.expr.lstrip(), "<string>", "eval")
  new_schema = None
  for t in table:

    if not new_schema:
      new_schema = dict(t.schema)
      for (i,v) in enumerate(c.vars):
        new_schema[v] = len(t.schema) + i

    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    v = eval(comp_expr, prior_globs, lcs)
    if len(c.vars) == 1:
      t.tuple.append(v)
      new_t = PQTuple( t.tuple, new_schema )
      yield new_t

    else:
      unpack_expr = "[ %s for %s in [ __v ]]" % (
                      '(' + ",".join(c.vars) + ')', c.unpack) 
      unpacked_vals = eval(unpack_expr, prior_globs, {'__v':v})
      new_t_data = list(t.tuple)
      for tv in unpacked_vals[0]:
        new_t_data.append(tv)
      new_t = PQTuple(new_t_data, new_schema)
      yield new_t

# Process a join
def processJoin(c, table, prior_lcs, prior_globs, left_arg, right_arg):
  new_schema = None
  left_conds = c.left_conds
  right_conds = c.right_conds
 
  join_type = 'nl'
  dir = 'right'
  if c.hint:
    join_type = c.hint['join_type']
    dir = c.hint['dir']

  if dir == 'left':
    left_arg,right_arg = right_arg,left_arg

  r_init_data = []
  r_init_data.append( emptyTuple([]) )

  # Build an index on the right relation, if we're doing
  # an index join. 
  index = None
  if join_type == 'index':
    index = {}
    r_data = r_init_data
    r_data = right_arg.execute(r_data, prior_lcs)

    for t in r_data:
        index_tuple = [] 
        for rcond in right_conds:
            lcs = dict(prior_lcs)
            lcs.update(t.getDict())
            rcond_val = eval(rcond, prior_globs, lcs)
            index_tuple.append( rcond_val )
        index_tuple = tuple(index_tuple)
        if not index_tuple in index:
            index[ index_tuple ] = []
        index[ index_tuple ].append( t )

  # Iterate over the tuples of the left relation and
  # compute the tuple of condition vars

  table = left_arg.execute(table, prior_lcs, prior_globs)
  for t in table:
     cond_tuple = []
     for lcond in left_conds:
         lcs = dict(prior_lcs)
         lcs.update(t.getDict())
         lcond_val = eval(lcond, prior_globs, lcs)
         cond_tuple.append( lcond_val )
     cond_tuple = tuple(cond_tuple)

     if index:
         if cond_tuple in index:
             for t2 in index[cond_tuple]:
                 if not new_schema:
                     new_schema = dict(t.schema)
                     for i,_ in enumerate(t2):
                         v = [x for x in t2.schema.items() if x[1]==i][0][0]
                         new_schema[v] = len(new_schema) + i
                 new_t_data = list(t.tuple)
                 new_t_data += list(t2.tuple)
                 new_t = PQTuple(new_t_data, new_schema)
                 yield new_t
         else:
             continue
     else:
          r_data = r_init_data
          r_data = right_arg.execute(r_data, prior_lcs, prior_globs)

          for t2 in r_data:
              rcond_tuple = []
              for rcond in right_conds:
                  lcs = dict(prior_lcs)
                  lcs.update(t2.getDict())
                  rcond_val = eval(rcond, prior_globs, lcs)
                  rcond_tuple.append( rcond_val )

              rcond_tuple = tuple(rcond_tuple)
              if cond_tuple == rcond_tuple:
                 if not new_schema:
                     new_schema = dict(t.schema)
                     for i,_ in enumerate(t2):
                         v = [x for x in t2.schema.items() if x[1]==i][0][0]
                         new_schema[v] = len(new_schema) + i
                 new_t_data = list(t.tuple)
                 new_t_data += list(t2.tuple)
                 new_t = PQTuple(new_t_data, new_schema)
                 yield new_t

# Process the match claise
def processMatchClause(c, table, prior_lcs, prior_globs):
  clause_expr = compile(c.expr, "<string>", "eval")

  # Fetch and compile all expressions in the
  # pattern match clause
  e_patterns = []
  patterns = list(c.pattern)
  while patterns:
    p = patterns.pop() 
    if 'expr_cond' in p:
      e_patterns.append(p)
    if 'pattern' in p:
      patterns.append(p['pattern'])
  
  for ep in e_patterns:
    ep['expr_cond'] = compile(ep["expr_cond"], "<string>", "eval")

  new_schema = None
  for t in table:
    if not new_schema:
      new_schema = dict(t.schema)
      for (i,v) in enumerate(c.vars):
        new_schema[v] = len(t.schema) + i

    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    vals = eval(clause_expr, prior_globs, lcs)

    for v in vals:
      if not hasattr(v, '__contains__'):
        continue
      
      new_t_data = list(t.tuple) + [None]*len(c.vars)
      new_t = PQTuple(new_t_data, new_schema)

      if match_pattern(c.pattern, c.exact, v, new_t, lcs, prior_globs):
        yield new_t

def match_pattern(ps, isExact, v, new_t, lcs, prior_globs):
  all_heads = []
  for p in [x for x in ps if 'match' in x]:
    match = p['match'][1:-1]
    all_heads.append(match)

    if match not in v:
      return False

    if 'const_cond' in p:
      if v[match] != p['const_cond'][1:-1]:
        return False

    if 'bind_to' in p:
      new_t[p['bind_to']] = v[match]
      lcs.update({p['bind_to']:v[match]})

    if 'expr_cond' in p:
      val = eval(p['expr_cond'], prior_globs, lcs)
      if not val:
        return False
      
    if 'pattern' in p:
      if not match_pattern(p['pattern'], isExact, v[match], new_t, lcs, prior_globs):
        return False

  if isExact and any([x for x in v if x not in all_heads]):
    return False

  bind_parent = next((x for x in ps if 'bind_parent_to' in x), None)
  if bind_parent:
    new_t[bind_parent['bind_parent_to']] = v
    lcs.update({bind_parent['bind_parent_to']:v})

  return True
  
# Process the count clause. Similar to let, but simpler
def processCountClause(c, table, prior_lcs, prior_globs):
  new_schema = None
  for (i,t) in enumerate(table):

    if not new_schema:
      new_schema = dict(t.schema)
      new_schema[c.var] = len(t.schema)

    new_t = PQTuple( t.tuple + [i], new_schema )
    yield new_t

# Process the group-by
def processGroupByClause(c, table, prior_lcs, prior_globs):
  gby_aliases = [g if isinstance(g,str) else g[1]
                                for g in c.groupby_list]
  gby_exprs = [g if isinstance(g,str) else g[0]
                                for g in c.groupby_list]
  comp_exprs = [compile(e,'<string>','eval') for e in gby_exprs]
  grp_table = {}

  schema = None
  # Group tuples in a hashtable
  for t in table:
  
    if not schema:
      schema = t.schema

    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    # Compute the key
    k = tuple( [eval(e,prior_globs,lcs) for e in comp_exprs] )
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
def processWhereClause(c, table, prior_lcs, prior_globs):
  comp_expr = compile(c.expr.lstrip(),"<string>","eval")
  for t in table:
    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    val = eval(comp_expr, prior_globs, lcs)
    if val:
      yield t

# Process the orderby clause
def processOrderByClause(c, table, prior_lcs, prior_globs):
  # Here we do n sorts, n is the number of sort specifications
  # For each sort we first need to compute a sort value (could
  # be some expression)

  sort_exprs = [ compile(os[0].lstrip(),"<string>","eval") for os in c.orderby_list]
  sort_rev = [ o[1]=='desc' for o in c.orderby_list]

  def computeSortSpec(tup,sort_spec):
    lcs = dict(prior_lcs)
    lcs.update(tup.getDict())
    return eval(sort_spec, prior_globs, lcs)

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
def fill_in_start_vars(vars, prev, v, nxt, i):
  vars["s_curr"] = v
  vars["s_at"] = i
  vars["s_prev"] = prev
  vars["s_next"] = nxt

# Fill in the end vars of the window, given the values list and current index
def fill_in_end_vars(vars, prev, v, nxt, i):
  vars["e_curr"] = v
  vars["e_at"] = i
  vars["e_prev"] = prev
  vars["e_next"] = nxt

# Check the start condition of the window, i.e. whether we should
# start a new window at this location (without considering tumbling
# windows, that check is done elsewhere).

def check_start_condition(all_vars,clause,locals,prior_globs,var_mapping):
  # we just need to evaluate the when expression 
  # but we need to set up the vars correctly, respecting the visibility
  # conditions
  start_vars = set(all_start_vars).intersection(
		set(var_mapping.keys()) )
  start_bindings = { var_mapping[v] : all_vars[v] for v in start_vars }

  # add the binding to the locals
  locals.update( start_bindings )

  #evaluate the when condition
  return eval( clause.s_when, prior_globs, locals )
  
# Check the end condition of the window.

def check_end_condition(vars,clause,locals,prior_globs,var_mapping):
  # If there is no 'when' clause, return False
  if not clause.e_when:
    return False

  end_vars = set(vars.keys()).intersection( set(var_mapping.keys()))
  end_binding = { var_mapping[v] : vars[v] for v in end_vars }

  locals.update( end_binding )
  res = eval( clause.e_when, prior_globs, locals)

  return res

def generate_triplets(binding_seq):
  if not isinstance(binding_seq, types.GeneratorType):
    binding_seq = (x for x in binding_seq)

  prev = None
  v = next(binding_seq, None)
  nxt = next(binding_seq, None)
  i = 0
  yield (prev,v,nxt,i)

  while nxt:
    prev = v
    v = nxt
    nxt = next(binding_seq, None)
    i += 1
    yield (prev,v,nxt, i)
  
# Process window clause
def processWindowClause(c, table, prior_lcs, prior_globs):
  schema = None
  new_schema = None

  # Create window variable name mapping
  var_mapping = {}
  for v in c.vars:
    var_mapping[v] = c.vars[v]
		
  for t in table:
    if not schema:
      schema = t.schema
      # Create a new schema with window variables added
      new_schema = dict(t.schema)
      for v in c.vars:
        new_schema[c.vars[v]] = len(new_schema)

    lcs = dict(prior_lcs)
    lcs.update(t.getDict())
    # Evaluate the binding sequence
    binding_seq = eval(c.binding_seq, prior_globs, lcs)

    # Create initial window variables

    # Initialize the windows
    open_windows = []

    # Iterate over the binding sequence
    for (prev,v,nxt,i) in generate_triplets(binding_seq):
      # Try to open a new window
      # in case of tumbling windows, only open a
      # window if there are no open windows
      if not c.tumbling or (c.tumbling and not open_windows):
        vars = make_window_vars()
        fill_in_start_vars(vars,prev,v,nxt,i)
        if check_start_condition(vars,c,dict(lcs),prior_globs,var_mapping):
          open_windows.append( {"window":[], "vars":vars} )
      
      new_open_windows = []
      #update all open windows, close those that are finished
      for w in open_windows:
        # Add currnt value to the window
        w["window"].append(v)

        fill_in_end_vars(w["vars"],prev,v,nxt,i)

        if check_end_condition(w["vars"],c,dict(lcs),prior_globs,var_mapping):
          # create a new tuple by extending the tuple from previous clauses
          # with the window variables, for each open window that can now be closed

          new_t = PQTuple( t.tuple + [None]*(len(new_schema)-len(schema)), new_schema)
          new_t[ var_mapping["var"] ] = w["window"]
          for val in [val for val in w["vars"].keys() if val in var_mapping]:
            new_t[ var_mapping[val] ] = w["vars"][val]
          yield new_t
        else:
          new_open_windows.append(w)

      open_windows = new_open_windows
          
    #close or remove all remaining open windows
    #if only is specified, we ignore non-closed windows
    if not c.only:
      # create a new tuple by extending the tuple from previous clauses
      # with the window variables, for each open window
      for w in open_windows:
        new_t = PQTuple( t.tuple + [None]*(len(new_schema)-len(schema)), new_schema)
        new_t[ var_mapping["var"] ] = w["window"]
        for v in [v for v in w["vars"].keys() if v in var_mapping]:
          new_t[ var_mapping[v] ] = w["vars"][v]
        yield new_t
