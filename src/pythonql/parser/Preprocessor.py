import sys
from antlr4 import *
from antlr4.tree.Tree import *
from parser.CustomLexer import CustomLexer
from parser.Errors import CustomErrorStrategy, CustomErrorListener, BufferedErrorListener
from parser.PythonQLParser import PythonQLParser
from functools import reduce

# The preprocessor inserts tokens into
# the token stream, produced by traversing
# the parse tree.
class MyToken(TerminalNodeImpl):
    def __init__(self,text):
        self.text = text
    def getText(self):
        return self.text

# Parse the PythonQL file and return a parse tree
def parsePythonQL( f ):
  # Set up the lexer
  inputStream = FileStream(f)
  lexer = CustomLexer(inputStream)
  stream = CommonTokenStream(lexer)

  # Set up the error handling stuff
  error_handler = CustomErrorStrategy()
  error_listener = CustomErrorListener()
  buffered_errors = BufferedErrorListener()
  error_listener.addDelegatee(buffered_errors)

  # Set up the parser
  parser = PythonQLParser(stream)
  parser.errHandler = error_handler

  # Remove default terminal error listener & add our own
  parser.removeErrorListeners()
  parser.addErrorListener(error_listener)

  # Parse the input
  tree = parser.file_input()

  if error_listener.errors_encountered > 0:
    print(buffered_errors.buffer)
    raise Exception("Syntax error")

  return (tree,parser)

############################################################
# Some methods to test what kind of subtree we're dealing with
def isPathExpression(tree,parser):
    if isinstance(tree,TerminalNodeImpl):
        return False
    return (tree.getRuleIndex()==parser.RULE_test
                and len(tree.children)>1 )

def isQuery(tree,parser):
    if isinstance(tree,TerminalNodeImpl):
        return False
    return tree.getRuleIndex()==parser.RULE_query_expression

def isChildStep(tree,parser):
    return (tree.getRuleIndex()==parser.RULE_path_step 
               and tree.children[0].getRuleIndex()==parser.RULE_child_path_step)

def isDescStep(tree,parser):
    return (tree.getRuleIndex()==parser.RULE_path_step and 
               tree.children[0].getRuleIndex()==parser.RULE_desc_path_step)

def isPredStep(tree,parser):
    return (tree.getRuleIndex()==parser.RULE_path_step and 
               tree.children[0].getRuleIndex()==parser.RULE_pred_path_step)

## Helper function to test the rule type (so we don't have to check
# terminal node all the time)
def ruleType(tree,t):
    if isinstance(tree,TerminalNodeImpl):
        return False
    return tree.getRuleIndex()==t

# Get the text of all terminals in the subtree
def getText(tree):
    if isinstance(tree,TerminalNodeImpl):
        return tree.getText()
    else:
        res = ""
        for c in tree.children:
            res += getText(c)
        return res

# Get all top non-terminals from the tree of specific types
def getAllNodes(tree,rule_list):
  if isinstance(tree,TerminalNodeImpl):
    return []
  if tree.getRuleIndex() in rule_list:
    return [tree]
  else:
    return [x for c in tree.children for x in getAllNodes(c)]

# Create a token list out of a heterogenous list
def mk_tok(items):
    if isinstance(items,list):
        res = []
        for i in items:
            if isinstance(i,str):
                res.append(MyToken(i))
            elif isinstance(i,list):
                res += i
            else:
                res.append(i)
        return res
    else:
        return [MyToken(items)]

# Convert path expressions to Python
def get_path_expression_terminals(tree,parser):
    children = tree.children
    
    baseExpr = children[0]
    result = get_all_terminals(baseExpr,parser)
    
    for c in children[1:]:
        if isChildStep(c,parser):
            result = mk_tok([ "child_path", "(", result, ")" ])
        elif isDescStep(c,parser):
            result = mk_tok([ "desc_path", "(", result, ")"])
        elif isPredStep(c,parser):
            condition = mk_tok([ '"""', get_all_terminals(c,parser)[1:-1], '"""'])
            result = mk_tok([ "pred_path", "(", result, ",", condition, ")"])
    
    return result

# Process the select clause
def process_select_clause(tree,parser):
    sel_vars = [c for c in tree.children if ruleType(c,parser.RULE_selectvar)]
    res = []
    for v in sel_vars:
      value_toks = mk_tok(['"""',get_all_terminals(v,parser),'"""'])
      if len(v.children)==1:
        res.append(mk_tok(["(", value_toks, ",", "None",")"]))
      else:
        value = v.children[0]
        alias = v.children[2]
        alias_toks = mk_tok(['"""',get_all_terminals(alias,parser),'"""'])
        res.append(mk_tok(["(", value_toks, ",", alias_toks,")"]))
    res = reduce(lambda x,y: x + mk_tok([","]) + y, res)
    return mk_tok(["{",'"name":"select"', ",", '"select_list"', ":" , "[", res, "]", "}"])

# Process the for clause
def process_for_clause(tree,parser):
    clauses = [c for c in tree.children if ruleType(c,parser.RULE_for_clause_entry)]
    res = []
    for cl in clauses:
        variable = '"'+getText(cl.children[0])+'"'
        expression = get_all_terminals(cl.children[2],parser)
        clause_tokens =  mk_tok(["{", '"name":"for"', ",", '"var"', ":", variable, ",", '"expr"', ":", '"""', expression, '"""',"}"]) 
        res.append(clause_tokens)
    return res

# Process the let clause
def process_let_clause(tree,parser):
    clauses = [c for c in tree.children if ruleType(c,parser.RULE_let_clause_entry)]
    res = []
    for cl in clauses:
        variable = '"'+getText(cl.children[0])+'"'
        expression = get_all_terminals(cl.children[2],parser)
        clause_tokens =  mk_tok(["{", '"name":"let"', ",", '"var"', ":", variable, ",", '"expr"', ":", '"""', expression, '"""',"}"]) 
        res.append(clause_tokens)
    return res

# Process the order by clause
def process_orderby_clause(tree,parser):
    res = []
    orderlist = tree.children[2]
    elements = [el for el in orderlist.children if ruleType(el,parser.RULE_orderlist_el)]
    for e in elements:
        ascdesc = "asc" if len(e.children)==1 else getText(e.children[1])
        ascdesc = '"'+ascdesc+'"'
        res.append(mk_tok(["(", '"""',get_all_terminals(e.children[0],parser),'"""',",", ascdesc, ")"]))
    res = reduce(lambda x,y: x + mk_tok([","]) + y, res)
    return mk_tok(["{",'"name":"orderby"', "," '"orderby_list"', ":" , "[", res, "]", "}"])

# Process the group by clause
def process_groupby_clause(tree,parser):
    res = []
    groupby_list = tree.children[2]
    for e in [e for e in groupby_list.children if ruleType(e,parser.RULE_group_by_var)]:
        res.append(mk_tok(['"'+getText(e)+'"']))
    res = reduce(lambda x,y: x + mk_tok([","]) + y, res)
    return mk_tok(["{",'"name":"groupby"', "," '"groupby_list"', ":", "[", res, "]", "}"])

def process_count_clause(tree,parser):
    return mk_tok(["{", '"name":"count"', ",", '"var"', ":", '"'+getText(tree.children[1])+'"', "}"])

# Process the where clause (this is easy)
def process_where_clause(tree,parser):
    return mk_tok(["{", '"name":"where"', ",", '"expr"', ":", '"""', get_all_terminals(tree.children[1],parser),'"""',"}"])

# Process the query. The query is turned into a function call
# PyQuery that takes all the clauses and evaluates them.

def get_query_terminals(tree,parser):
    children = tree.children
    clauses = []

    # We process select clause separately, because we add it
    # to the end of the list

    select_clause = process_select_clause(children[0], parser)
    for c in children[1:]:
      if c.getRuleIndex() == parser.RULE_for_clause:
        clauses += process_for_clause(c, parser)
      elif c.getRuleIndex() == parser.RULE_let_clause:
        clauses += process_let_clause(c, parser)
      elif c.getRuleIndex() == parser.RULE_where_clause:
        clauses.append( process_where_clause(c, parser) )
      elif c.getRuleIndex() == parser.RULE_count_clause:
        clauses.append( process_count_clause(c, parser) )
      elif c.getRuleIndex() == parser.RULE_group_by_clause:
        clauses.append( process_groupby_clause(c, parser) )
      elif c.getRuleIndex() == parser.RULE_order_by_clause:
        clauses.append( process_orderby_clause(c, parser) )

    # Add the select clause at the end
    clauses.append( select_clause )

    clauses_repr = reduce( lambda x,y: x + mk_tok([","]) + y, clauses)
    return mk_tok(["PyQuery", "(", "[", clauses_repr, "]", ",", "locals", "(", ")", ")"])

# Process an arbitrary PythonQL program
def get_all_terminals(tree,parser):
    if isinstance(tree,TerminalNodeImpl):
        return [tree]
    if isPathExpression(tree,parser):
        return get_path_expression_terminals(tree,parser)
    elif isQuery(tree,parser):
        return get_query_terminals(tree,parser)
    else:
        children = []
        if tree.children:
            children = reduce( lambda x,y: x+y, [get_all_terminals(c,parser) for c in tree.children])
        return children

####################################
#The rest of the code creates a Python program out of PythonQL, which can be run with Python3 interpreter
####################################

def makeIndent(i):
    return "  "*(2*i)

def all_ws(t):
    return all([x==' ' for x in t])

# Generate a program from a list of text tokens
def makeProgramFromTextTokens(tokens):
    result = ""
    indent = 0
    buffer = ""
    for t in tokens:
        if buffer!="":
            if t==' ' or t=='\n':
                result += buffer + '\n'
                buffer = ""
            else:
                buffer += t + " "
        else:
            if t==' ':
                indent = indent -1
            elif t=='\n':
                indent -= 1
                indent = indent if indent>=0 else 0
            elif all_ws(t):
                indent = len(t)//2
            else:
                buffer = makeIndent(indent)
                buffer += t + " "
    return result

# Generate a program from a parse tree
def makeProgram(fname):
  (tree,parser) = parsePythonQL(fname)
  all_terminals = get_all_terminals(tree,parser)
  text_tokens = [t.getText() for t in all_terminals]
  return makeProgramFromTextTokens(text_tokens)
