# 
# This whole file is about the Window clause of PythonQL
# Its a pretty hairy beast, requires a bunch of helper
# functions

from PQTuple import PQTuple
from PQTable import PQTable

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
  # Create a new schema with window variables added
  new_schema = dict(table.schema)
  for v in c["vars"]:
    new_schema[c["vars"][v]] = len(new_schema)

  # Create window variable name mapping
  var_mapping = {}
  for v in c["vars"]:
    var_mapping[v] = c["vars"][v]
		
  new_table = PQTable( new_schema )
  for t in table.data:
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
      new_t = PQTuple( t.tuple + [None]*(len(new_schema)-len(table.schema)), new_schema)
      new_t[ var_mapping["var"] ] = w["window"]
      for v in [v for v in w["vars"].keys() if v in var_mapping]:
        new_t[ var_mapping[v] ] = w["vars"][v]
      new_table.data.append(new_t)

  return new_table
