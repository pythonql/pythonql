from PQTuple import PQTuple

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
  stack = [coll]
  while stack:
    i = stack.pop()
    if isList(i):
      [stack.push(j) for j in i[1:]]
      yield i[0]
    if isMap(i):
      keys = list(i.keys())
      [stack.push(i[j]) for j in keys[1:]]
      yield i[keys[0]]

# create a table with an empty tuple
def emptyTupleTable(for_schema):
  return [ PQTuple([None] * len(for_schema), for_schema) ]

# Execute the query
def PyQuery( select_list, for_clauses, groupby_list, where, order_list, prior_lcs):
  for_schema = {f[0]:i for (i,f) in enumerate(for_clauses)}

  # Process the for clause
  table = []
  for fc in for_clauses:
    if fc[1] == '=':
      if not table:
        table = emptyTupleTable(for_schema)
      for t in table:
        lcs = prior_lcs
        lcs.update(t.getDict())
        t[fc[0]] = eval(fc[2], globals(), lcs)
    else:
      new_table = []
      for t in (table if table else emptyTupleTable(for_schema)):
        lcs = prior_lcs
        lcs.update(t.getDict())
        vals = eval(fc[2], globals(), lcs)
        for v in vals:
          t2 = t.copy()
          t2[fc[0]] = v
          new_table.append(t2)
      table = new_table

  if groupby_list:
    # Process the groupby clause
    grp_table = {}

    # Group tuples in a hashtable
    for t in table:
      k = tuple( [t[k] for k in groupby_list] )
      if not k in grp_table:
        grp_table[k] = []
      grp_table[k].append(t)

    new_table = []
    for k in grp_table:
      t = PQTuple([None]*len(for_schema), for_schema)
      #Copy over the key
      for (i,v) in enumerate(groupby_list):
        t[v] = k[i]

      #Every other variable (not in group by list) is turned into a lists
      #First create empty lists
      non_key_vars = [v for v in for_schema if not v in groupby_list]
      for v in non_key_vars:
        t[v] = []

      # Now fill in the lists:
      for part_t in grp_table[k]:
        for v in non_key_vars:
          t[v].append( part_t[v] )

      new_table.append(t)

    table = new_table

  # Process the where clause
  if where:
    new_table = []
    for t in table:
      lcs = prior_lcs
      lcs.update(t.getDict())
      val = eval(where, globals(), lcs)
      if val:
        new_table.append(t)
    table = new_table

  # Process the orderby clause

  # Here we do n sorts, n is the number of sort specifications
  # For each sort we first need to compute a sort value (could
  # be some expression)

  def computeSortSpec(tup,sort_spec):
    lcs = prior_lcs
    lcs.update(tup.getDict())
    return eval(sort_spec, globals(), lcs)

  order_list.reverse()
  for sort_spec in order_list:
    table.sort( key = lambda x: computeSortSpec(x,sort_spec[0]),
         reverse=sort_spec[1]=='desc' )


  # Process the select clause
  # If its a star expression, just return the whole table
  if select_list[0][0]=='*':
    return table

  # Otherwise build up new tuples
  # If the output is a tuple of length 1 (even with alias), don't
  # build tuples, just return a list of values
  new_table = []
  select_schema = { (sel[1] if sel[1] else sel[0]) : i for (i,sel) in enumerate(select_list)}
  for t in table:
    new_tuple = []
    for sel in select_list:
      lcs = prior_lcs
      lcs.update(t.getDict())
      new_tuple.append( eval(sel[0], globals(), lcs))
    if len(select_list) == 1:
      new_table.append(new_tuple[0])
    else:
      new_table.append(PQTuple( new_tuple, select_schema))
  table = new_table
  return table

if __name__=='__main__':
  x = [ 1 , 2 , 3 , 4 , 5 ] 
  y = [ 6 , 7 , 8 , 9 , 10 ] 
  res = PyQuery ( 
	[ ("z", None), ("sum(w)", "WWW") ], # Select clause, expressions and their aliases
	[ ( "z" , "in" , """ x """ ) , ( "w" , "in" , """ y """ ) ], # From clause
	["z"],	# Group by clause
	""" z % 2 == 0 """, # Where clause
	[],	# Order by clause
	locals())
  print(res)
