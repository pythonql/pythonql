from pythonql.algebra.operator import operator

class Count(operator):
  def __init__(self,var):
    self.var = var

  def defined_vars(self):
    return { self.var }

  def used_vars(self):
    return set()

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processCountClause
    return processCountClause(self, table, prior_locs, prior_globs)

class For(operator):
  def __init__(self,vars,unpack,expr):
    self.vars = vars
    self.unpack = unpack
    self.expr = expr
    self.database = None

  def defined_vars(self):
    return set(self.vars)

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    return get_all_vars(get_ast(self.expr))

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processForClause
    return processForClause(self, table, prior_locs, prior_globs)

  def __repr__(self):
    return "For (" + repr(self.vars) + "," + repr(self.unpack) + "," + self.expr + ")"

class GroupBy(operator):
  def __init__(self,groupby_list):
    self.groupby_list = groupby_list

  def defined_vars(self):
    return {v[1] for v in self.groupby_list}

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    vs = set()
    for (ex,_) in self.groupby_list:
        vs = vs.union(get_all_vars(get_ast(ex)))

    return vs

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processGroupByClause
    return processGroupByClause(self, table, prior_locs, prior_globs)

  def __repr__(self):
    return "GroupBy ( " + repr(self.groupby_list) + ")"

class Join(operator):
  def __init__(self,left_conds=[],right_conds=[]):
    self.left_conds=left_conds
    self.right_conds=right_conds
    self.hint = None

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    vs = set()
    for c in self.left_conds:
        vs = vs.union( get_all_vars(get_ast(c)))
    for c in self.right_conds:
        vs = vs.union( get_all_vars(get_ast(c)))

    return vs

  def execute(self, table, prior_locs, prior_globs, left_child, right_child):
    from pythonql.Executor import processJoin
    return processJoin(self, table, prior_locs, prior_globs, left_child, right_child)

  def __repr__(self):
    return "Join(" + repr(self.left_conds) + "," + repr(self.right_conds) + ")"

class LeftOuterJoin(operator):
  def __init__(self,on,hints):
    self.on = on
    self.hints = hints

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    return get_all_vars(self.on)

  def execute(self, table, prior_locs, prior_globs, left_child, right_child):
    from pythonql.Executor import processLeftOuterJoin
    return processLeftOuterJoin(self, table, prior_locs, prior_globs, left_child, right_child)

  def __repr__(self):
    return "LeftOuterJoin(" + repr(self.on) + "," + repr(self.hints) + ")"

class Let(operator):
  def __init__(self, vars, unpack, expr):
    self.vars = vars
    self.unpack = unpack
    self.expr = expr

  def defined_vars(self):
    return set(self.vars)

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    return get_all_vars(get_ast(self.expr))

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processLetClause
    return processLetClause(self, table, prior_locs, prior_globs)

  def __repr__(self):
    return "Let (" + repr(self.vars) + "," + repr(self.unpack) + "," + self.expr + ")"
  
class Match(operator):
  def __init__(self,exact,vars,pattern,expr):
    self.exact = exact
    self.vars = vars
    self.pattern = pattern
    self.expr = expr

  def defined_vars(self):
    return set( self.vars )

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processMatchClause
    return processMatchClause(self, table, prior_locs, prior_globs)

class OrderBy(operator):
  def __init__(self,orderby_list):
    self.orderby_list = orderby_list

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    vs = set()
    for ex in self.orderby_list:
        vs = vs.union( get_all_vars( get_ast( ex )))

    return vs

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processOrderByClause
    return processOrderByClause(self, table, prior_locs, prior_globs)

class Select(operator):
  def __init__(self, expr, second_expr=None):
    if not second_expr:
       self.expr = expr
    else:
       self.expr = None
       self.key_expr = expr
       self.value_expr = second_expr

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    if self.expr:
        return get_all_vars(get_ast(self.expr))

    else:
        return get_all_vars(get_ast(self.key_expr)).union(
            get_all_vars(get_ast(self.value_expr)))

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processSelectClause
    return processSelectClause(self, table, prior_locs, prior_globs)

  def __repr__(self):
    if self.expr:
        return "Select( " + self.expr + ")"
    else:
        return "Select( " + self.key_expr + ":" + self.value_expr + ")"

class Where(operator):
  def __init__(self, expr):
    self.expr = expr

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    return get_all_vars(get_ast(self.expr))

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processWhereClause
    return processWhereClause(self, table, prior_locs, prior_globs)

  def __repr__(self):
    return "Where (" + self.expr + ")"

class Window(operator):
  def __init__(self,var,tumbling,only,binding_seq,s_when,e_when,vars):
    self.var = var
    self.tumbling = tumbling
    self.only = only
    self.binding_seq = binding_seq
    self.s_when = s_when
    self.e_when = e_when
    self.vars = vars

  def defined_vars(self):
    return { self.var }

  def used_vars(self):
    from pythonql.Ast import get_all_vars,get_ast
    return get_all_vars( get_ast( expr.binding_seq ))

  def execute(self, table, prior_locs, prior_globs):
    from pythonql.Executor import processWindowClause
    return processWindowClause(self, table, prior_locs, prior_globs)

class WrappedSubplan(operator):
  def __init__(self,database,query,tuple_vars,vars):
    self.database = database
    self.query = query
    self.tuple_vars = tuple_vars
    self.vars = vars   

  def __repr__(self):
    return "Wrapped(" + self.query + "," + repr([x['tuple_var'] for x in self.tuple_vars]) + "," + repr(self.vars) + ")"

  def execute(self, table, prior_locs, prior_globs):
    res = self.database.execute(self.query, self.tuple_vars, self.vars)
    return self.database.execute(self.query, self.tuple_vars, self.vars)
