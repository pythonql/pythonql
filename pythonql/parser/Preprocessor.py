import sys

from pythonql.parser.PythonQLParser import Parser, Node, print_program
from pythonql.parser.PythonQLLexer import PQLexerToken
from functools import reduce
import time
import json

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

# Parse the PythonQL file and return a parse tree
def parsePythonQL( s ):

  p = Parser()
  tree = p.parse(s)

  return tree

############################################################
# Some methods to test what kind of subtree we're dealing with
def isPathExpression(tree):
    if not isinstance(tree,Node):
        return False
    return (tree.label == 'test' and tree.children[1].children)

def isTryExceptExpression(tree):
    if not isinstance(tree,Node):
        return False
    return (tree.label == 'try_catch_expr' and len(tree.children)>1 )

def isTupleConstructor(tree):
    if not isinstance(tree,Node):
        return False

    if tree.label == 'testseq_query':
      if tree.children[0].label == 'test_as_list':
        if len(tree.children[0].children) > 1 or len(tree.children[0].children[0].children)>1:
          return True

    return False

def moreThanPythonComprehension(tree):
  select_cl = tree.children[0]
  if len(select_cl.children)==2 or len(select_cl.children)==4:
    return True
  for cl in tree.children[1:]:
    if not cl.label in ['for_clause','where_clause']:
      return True
    if cl.label == 'where_clause':
      if cl.children[0].getText() == 'where':
        return True

  return False

def isQuery(tree):
    if not isinstance(tree,Node):
        return False

    if tree.label in ['gen_query_expression','list_query_expression']: 
        if len(tree.children)==2:
          return False
        if tree.children[1].label in ['testlist_query','testseq_query']:
          query = tree.children[1].children[0]
          if query.label == 'query_expression':
            return moreThanPythonComprehension(query)
        return False

    if tree.label =='set_query_expression':
        if len(tree.children)==2:
          return False

        dictorset = tree.children[1]
        if (dictorset.children[0].label in ['query_map_expression','query_expression']):
          return moreThanPythonComprehension(dictorset.children[0])

        return False

    return False

def isChildStep(tree):
    return (tree.label == 'path_step' and tree.children[1].type == 'CHILD_AXIS')

def isDescStep(tree):
    return (tree.label == 'path_step' and tree.children[1].type == 'DESCENDANT_AXIS')

## Helper function to test the rule type (so we don't have to check
# terminal node all the time)
def ruleType(tree,t):
    if not isinstance(tree,Node):
        return False
    return tree.label ==t

def tokType(tree,t):
    if not isinstance(tree,Node):
        return tree.value==t
    elif len(tree.children)==1:
        return tokType(tree.children[0],t)
    return False

# Get the text of all terminals in the subtree
def getText(tree):
    if not isinstance(tree,Node):
        return tree.value
    else:
        res = ""
        for c in tree.children:
            res += getText(c)
        return res

def getTextList(trees):
    return " ".join([getText(t) for t in trees])

def getTermsEsc(tree):
    str = getTextList( get_all_terminals(tree) )
    str = str_encode(str)
    return '\"' + str + '\"'

# Get all top non-terminals from the tree of specific types
def getAllNodes(tree,rule_list):
  if not isinstance(tree,Node):
    return []
  if tree.label in rule_list:
    return [tree]
  else:
    return [x for c in tree.children for x in getAllNodes(c)]

# Create a token list out of a heterogenous list
def mk_tok(items):
    if isinstance(items,list):
        res = []
        for i in items:
            if isinstance(i,str):
                res.append(PQLexerToken('PQL',i,-1,-1))
            elif isinstance(i,list):
                res += i
            else:
                res.append(i)
        return res
    else:
        return [PQLexerToken('PQL',items,-1,-1)]

# Convert path expressions to Python
def get_path_expression_terminals(tree):
    baseExpr = tree.children[0]
    result = get_all_terminals(baseExpr)
    
    path_steps = [p for p in tree.get_children('path_step') if p.children]
    path_steps.reverse()

    for p in path_steps:
      cond = mk_tok([ getTermsEsc(p.children[2]) ])
      if isChildStep(p):
        result = mk_tok([ "PQChildPath", "(", result, ",", cond, ",", "locals", "(", ")", ")" ])
      else:
        result = mk_tok([ "PQDescPath", "(", result, ",", cond, ",", "locals", "(", ")", ")" ])
    
    return result

# Convert try-catch expression to Python
def get_try_except_expression_terminals(tree):
    children = tree.children
    try_expr = children[1]
    except_expr = children[3]
 
    result = mk_tok(["PQTry", "(", getTermsEsc(try_expr), ",",
               getTermsEsc(except_expr), ",","locals()",")"])
    return result

# Convert the tuple constructor
def get_tuple_constructor_terminals(tree):
    elements = [x for x in tree.children[0].children if isinstance(x,Node)]
    res = []
    for e in elements:
      value = mk_tok([getTermsEsc(e.children[0])])
      if len(e.children)==1:
        res.append(mk_tok(["(",value,",","None",")"]))
      else:
        alias = mk_tok([getTermsEsc(e.children[2])])
        res.append(mk_tok(["(",value,",",alias,")"]))
    res = reduce(lambda x,y: x + mk_tok([","]) + y, res)
    return mk_tok(["make_pql_tuple","(", "[",res,"]",",","locals","(",")",")"])

# Process the select clause
def process_select_clause(tree):
    res = []

    # Standard select clause
    if tree.label == 'select_clause':
      e = tree.children[0]
      if not isinstance(tree.children[0], Node):
        e = tree.children[1]

      value_toks = mk_tok([getTermsEsc(e)])
      return mk_tok(["{",'"name":"select"', ",", '"expr"', ":", value_toks, "}"])

    # Map select clause
    else:
      k = tree.children[0]
      e = tree.children[2]
      if not isinstance(tree.children[0], Node):
        k = tree.children[1]
        e = tree.children[3]

      key_toks = mk_tok([getTermsEsc(k)])
      value_toks = mk_tok([getTermsEsc(e)])
      return mk_tok(["{",'"name":"select"', ",", '"key"', ":", key_toks, ",", '"value"', ":", value_toks, "}" ])

# Process the for clause
def process_for_clause(tree):
    clauses = [c for c in tree.children[1].children if isinstance(c,Node) and c.label == 'for_clause_entry']
    res = []
    for cl in clauses:
        vars = [mk_tok(['"%s"' % t.value]) for t in cl.children[0].terms() if t.type == 'NAME']
        vars = mk_tok([ "[", reduce(lambda x,y: x + mk_tok([","]) + y, vars), "]" ])
        unpack_expr = '"' + " ".join([t.value for t in cl.children[0].terms()]) + '"'
        expression = getTermsEsc(cl.children[2])
        clause_tokens =  mk_tok(["{", '"name":"for"', ",", '"vars"', ":", vars, ",", '"unpack"', ":", unpack_expr, ",", '"expr"', ":", expression,"}"]) 
        res.append(clause_tokens)
    return res

# Process the let clause
def process_let_clause(tree):
    clauses = [c for c in tree.children[1].children if isinstance(c,Node) and c.label == 'let_clause_entry']
    res = []
    for cl in clauses:
        vars = [mk_tok(['"%s"' % t.value]) for t in cl.children[0].terms() if t.type == 'NAME']
        vars = mk_tok([ "[", reduce(lambda x,y: x + mk_tok([","]) + y, vars), "]" ])
        unpack_expr = '"' + " ".join([t.value for t in cl.children[0].terms()]) + '"'
        expression = getTermsEsc(cl.children[2])
        clause_tokens =  mk_tok(["{", '"name":"let"', ",", '"vars"', ":", vars, ",", '"unpack"', ":", unpack_expr, ",", '"expr"', ":", expression,"}"]) 
        res.append(clause_tokens)
    return res

# Process the match clause
def process_match_clause(tree):
    exact = False
    try:
      exact = tree.children[1].children[0].type != 'FILTER'
    except:
      pass
    vars = []
    pattern = process_pattern(tree.children[2], vars)
    expression = getTermsEsc(tree.children[4])
    vars = [mk_tok(['"' + v + '"']) for v in vars]
    vars = mk_tok([ "[", reduce(lambda x,y: x + mk_tok([","]) + y, vars), "]" ])
    res = mk_tok(["{", '"name":"match"' , "," , '"exact"' , ":", repr(exact) , "," , '"vars"', ":", vars, ",", '"pattern"', ":", json.dumps(pattern), ",",
                       '"expr"', ":", expression, "}"])
    
    return res

def process_pattern(tree, vars):
    if (len(tree.children)>1 and isinstance(tree.children[1],Node) 
                   and tree.children[1].label=='pattern_object_list'):
      list = tree.children[1]
      res = []
      for l in list.children:
        if not isinstance(l,Node):
          continue
        res.append(process_pattern(l,vars))
      if len(tree.children[3].children):
        var = getText(tree.children[3].children[1])
        res.append({'bind_parent_to':var})
        vars.append(var)
      return res

    elif (len(tree.children)==1 and isinstance(tree.children[0],Node)
                   and tree.children[0].label == 'pattern_object_element'):
      return process_pattern(tree.children[0],vars)

    else:
      res = {'match':getText(tree.children[0])}
      if isinstance(tree.children[2],Node) and tree.children[2].label == 'pattern_object':
        res['pattern'] = process_pattern(tree.children[2],vars)
        return res
      if tree.children[2].type == 'STRING_LITERAL':
        res['const_cond'] = getText(tree.children[2])
        return res
      if tree.children[2].type == 'NAME':
        res['var_cond'] = getText(tree.children[2])
        return res
      if tree.children[2].type == 'WHERE':
        res['expr_cond'] = getText(tree.children[3])
        return res

      if tree.children[2].type == 'AS':
        res['bind_to'] = getText(tree.children[3])
        vars.append(res['bind_to'])
        if len(tree.children) == 6:
          res['expr_cond'] = getText(tree.children[5])
        return res

# Process the order by clause
def process_orderby_clause(tree):
    res = []
    orderlist = tree.children[2]
    elements = [el for el in orderlist.children if isinstance(el,Node) and el.label == 'order_element']
    for e in elements:
        ascdesc = "asc" if len(e.children)==1 else getText(e.children[1])
        ascdesc = '"'+ascdesc+'"'
        res.append(mk_tok(["(", getTermsEsc(e.children[0]),",", ascdesc, ")"]))
    res = reduce(lambda x,y: x + mk_tok([","]) + y, res)
    return mk_tok(["{",'"name":"orderby"', "," '"orderby_list"', ":" , "[", res, "]", "}"])

# Process the group by clause
def process_groupby_clause(tree):
    res = []
    groupby_list = tree.children[2]
    for e in [e for e in groupby_list.children if isinstance(e,Node) and e.label == 'group_by_var']:
        if len(e.children)==1 and tokType(e.children[0],'NAME'):
          res.append(mk_tok(['"'+getText(e)+'"']))
        else:
          gby_expr = getTermsEsc(e.children[0])
          alias = gby_expr
          if len(e.children)==3:
             alias = '"'+getText(e.children[2])+'"'
          res.append(mk_tok(["(", gby_expr, ",", alias, ")"]))
        
    res = reduce(lambda x,y: x + mk_tok([","]) + y, res)
    return mk_tok(["{",'"name":"groupby"', "," '"groupby_list"', ":", "[", res, "]", "}"])

def process_count_clause(tree):
    return mk_tok(["{", '"name":"count"', ",", '"var"', ":", '"'+getText(tree.children[1])+'"', "}"])

# Process the where clause (this is easy)
def process_where_clause(tree):
    return mk_tok(["{", '"name":"where"', ",", '"expr"', ":", getTermsEsc(tree.children[1]),"}"])

# Process the window clause (hairy stuff)
def get_window_vars(tree,type):
  res = {}
  for c in tree.children:
    if c.label == 'current_item_opt' and c.children:
      res[type+"_curr"] = getText(c)
    if c.label == 'positional_var_opt' and c.children:
      res[type+"_at"] = getText(c.children[1])
    if c.label == 'previous_var_opt' and c.children:
      res[type+"_prev"] = getText(c.children[1])
    if c.label == 'next_var_opt' and c.children:
      res[type+"_next"] = getText(c.children[1])
  return res

def process_window_clause(tree):
  window = tree.children[0]
  tumbling = window.label == 'tumbling_window'
  window_var = getText(window.children[3])
  binding_seq = getTermsEsc(window.children[5])

  start = window.get_child('window_start_cond')
  end = window.get_child_opt('window_end_cond')

  start_vars = get_window_vars(start.children[1],"s")
  start_cond = getTermsEsc(start.children[3])
  end_vars = {}
  end_cond = None
  only = False

  if end:
    if len(end.children) == 5:
      end_vars = get_window_vars(end.children[2],"e")
      end_cond = getTermsEsc(end.children[4])
      only = True
    else:
      end_vars = get_window_vars(end.children[1],"e")
      end_cond = getTermsEsc(end.children[3])

  start_vars.update( end_vars )
  var_tokens = [mk_tok([ '"'+k+'"', ":", '"'+start_vars[k]+'"' ]) for k in start_vars ]
  var_tokens = reduce(lambda x,y: x + mk_tok([","]) + y, var_tokens)

  return mk_tok([ "{", '"name":"window"', "," , '"tumbling"', ":", repr(tumbling), "," '"only"', ":", repr(only), ",",
			'"in"', ":", binding_seq, ",",
                        '"s_when"', ":", start_cond, ",",
                        mk_tok([ '"e_when"', ":", end_cond, ","]) if end_cond else [],
                        '"vars"', ":", "{", '"var"', ":", '"'+window_var+'"', ",", var_tokens, "}", "}" ])
                        
# Process the query. The query is turned into a function call
# PyQuery that takes all the clauses and evaluates them.

def get_query_terminals(tree):
    query_type = None
    if tree.label == 'gen_query_expression':
      query_type = "gen"

    elif tree.label == 'list_query_expression':
      query_type = "list"

    elif tree.label == 'set_query_expression':
      if tree.children[1].children[0].label == 'query_expression':
        query_type = "set"
      else:
        query_type = "map"

    query_expr = tree.children[1].children[0]
    children = query_expr.children
    clauses = []

    # We process select clause separately, because we add it
    # to the end of the list

    select_clause = process_select_clause(children[0])
    cls = [ children[1].children[0] ] + [x.children[0] for x in children[2].children]
    
    for c in cls:
      if c.label == 'for_clause':
        clauses += process_for_clause(c)
      elif c.label == 'let_clause':
        clauses += process_let_clause(c)
      elif c.label == 'match_clause':
        clauses.append( process_match_clause(c) )
      elif c.label == 'where_clause':
        clauses.append( process_where_clause(c) )
      elif c.label == 'count_clause':
        clauses.append( process_count_clause(c) )
      elif c.label == 'group_by_clause':
        clauses.append( process_groupby_clause(c) )
      elif c.label == 'order_by_clause':
        clauses.append( process_orderby_clause(c) )
      elif c.label == 'window_clause':
        clauses.append( process_window_clause(c) )
      else: 
        raise Exception("Unknown clause encountered")

    # Add the select clause at the end
    clauses.append( select_clause )

    clauses_repr = reduce( lambda x,y: x + mk_tok([","]) + y, clauses)
    return mk_tok(["PyQuery", "(", "[", clauses_repr, "]", ",", "locals", "(", ")", ",", '"'+query_type+'"', ")"])

# Process an arbitrary PythonQL program
def get_all_terminals(tree):
    if not isinstance(tree,Node):
        return [tree]
    if isPathExpression(tree):
        return get_path_expression_terminals(tree)
    elif isTryExceptExpression(tree):
        return get_try_except_expression_terminals(tree)
    elif isTupleConstructor(tree):
        return get_tuple_constructor_terminals(tree)
    elif isQuery(tree):
        return get_query_terminals(tree)
    else:
        children = []
        if tree.children:
            children = reduce( lambda x,y: x+y, [get_all_terminals(c) for c in tree.children])
        return children

# Generate a program from a parse tree
def makeProgramFromFile(fname):
  str = "".join( open(fname).readlines() )
  return makeProgramFromString(str)

def makeProgramFromString(str):
  tree = parsePythonQL(str)
  all_terminals = get_all_terminals(tree)
  return print_program(all_terminals)
