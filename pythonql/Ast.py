import ast,_ast
from pythonql.algebra.operators import *
from collections import namedtuple
import sys

# List of classes for our internal AST

boolOp_e = namedtuple('boolOp_e',['op','args'])
binaryOp_e = namedtuple('binaryOp_e',['op','args'])
unaryOp_e = namedtuple('unaryOp_e',['op','arg'])
lambda_e = namedtuple('lambda_e',['args','body'])
if_e = namedtuple('if_e',['test','then','or_else'])
listComp_e = namedtuple('listComp_e',['expr','generators'])
setComp_e = namedtuple('setComp_e',['expr','generators'])
dictComp_e = namedtuple('dictComp_e',['key','value','generators'])
generatorExpr_e = namedtuple('generatorExpr_e',['expr','generators'])
compare_e = namedtuple('compare_e',['left','ops','comparators'])
call_e = namedtuple('call_e',['func','args','kwargs','starargs'])

num_literal = namedtuple('num_literal',['value'])
str_literal = namedtuple('str_literal',['value'])
bool_literal = namedtuple('bool_literal',['value'])
none_literal = namedtuple('none_literal',[])
name_e = namedtuple('name_e',['id'])

set_e = namedtuple('set_e',['values'])
list_e = namedtuple('list_e',['values'])
tuple_e = namedtuple('tuple_e',['values'])
dict_e = namedtuple('dict_e',['keys','values'])

attribute_e = namedtuple('attribute_e',['value','attribute'])
subscript_e = namedtuple('subscript_e',['value','lower','upper','step'])
subscript_ind_e = namedtuple('subscript_e',['value','index'])

slice_e = namedtuple('slice_e',['lower','upper','step'])
index_e = namedtuple('index_e',['value'])

comprehension_e = namedtuple('comprehension',['target','iter','ifs'])

# Mapping from Python's AST into the operators of our internal AST

opMap = {_ast.Add:'+', _ast.Sub:'-', _ast.UAdd:'+', _ast.USub:'-', _ast.Mult:'*', _ast.Div:'/', 
        _ast.Mod:'%', _ast.Pow:'**', _ast.LShift:'<<', ast.RShift:'>>',
        _ast.BitOr:'???', _ast.BitXor:'???', _ast.BitAnd:'???', _ast.FloorDiv:'//',
        _ast.Invert:'???', _ast.Not:'not', _ast.Eq:'==', _ast.NotEq:'!=',
        _ast.Lt:'<', _ast.Gt:'>', _ast.LtE:'<=', _ast.GtE:'>=', _ast.Is:'is',
        _ast.IsNot:'isnot', _ast.In:'in', _ast.NotIn:"notin", _ast.And:'and',
        _ast.Or:'or'}

# Convert Python AST into our internal AST

def convert_ast(a):
    
    if isinstance(a,_ast.BoolOp):
        return boolOp_e(opMap[type(a.op)],
                          [convert_ast(x) for x in a.values])
    
    elif isinstance(a,_ast.BinOp):
        return binaryOp_e(opMap[type(a.op)], 
                          [convert_ast(a.left), convert_ast(a.right)])
    
    elif isinstance(a,_ast.UnaryOp):
        return unaryOp_e(opMap[type(a.op)], convert_ast(a.operand))
    
    elif isinstance(a,_ast.Lambda):
        return lambda_e(convert_ast(a.args), convert_ast(a.body))
    
    elif isinstance(a,_ast.IfExp):
        return if_e(convert_ast(a.test),convert_ast(a.body), convert_ast(a.orelse))
    
    elif isinstance(a,_ast.Attribute):
        return attribute_e(convert_ast(a.value), name_e(a.attr))

    elif isinstance(a,_ast.Subscript):
        if isinstance(a.slice,ast.Index):
            return subscript_ind_e(convert_ast(a.value), convert_ast(a.slice.value))
        else:
            return subscript_e(convert_ast(a.value),
                               convert_ast(a.slice.lower),
                               convert_ast(a.slice.upper),
                               convert_ast(a.slice.step))
    
    elif isinstance(a,_ast.Compare):
        return compare_e(convert_ast(a.left),
                        [opMap[type(x)] for x in a.ops],
                        [convert_ast(x) for x in a.comparators])
    
    elif isinstance(a,_ast.Call):
        return call_e(convert_ast(a.func),
                     [convert_ast(x) for x in a.args if not isinstance(x,_ast.Starred)],
                     [{k.arg : convert_ast(k.value)} for k in a.keywords],
                     [convert_ast(x.value) for x in a.args if isinstance(x,_ast.Starred)]
                     )
    
    elif isinstance(a,_ast.ListComp):
        return listComp_e(convert_ast(a.elt), [convert_ast(x) for x in a.generators])
    
    elif isinstance(a,_ast.SetComp):
        return setComp_e(convert_ast(a.elt), [convert_ast(x) for x in a.generators])
    
    elif isinstance(a,_ast.DictComp):
        return dictComp_e(convert_ast(a.key), convert_ast(a.value), [convert_ast(x) for x in a.generators])
    
    elif isinstance(a,_ast.comprehension):
        return comprehension_e(convert_ast(a.target), convert_ast(a.iter), convert_ast(a.ifs))
    
    elif isinstance(a,_ast.List):
        return list_e([convert_ast(x) for x in a.elts])
    
    elif isinstance(a,_ast.Tuple):
        return tuple_e([convert_ast(x) for x in a.elts])
    
    elif isinstance(a,_ast.Set):
        return set_e([convert_ast(x) for x in a.elts])
    
    elif isinstance(a,_ast.Dict):
        return dict_e([convert_ast(x) for x in a.keys],[convert_ast(x) for x in a.values])
    
    elif isinstance(a,_ast.Str):
        return str_literal(a.s)
    
    elif isinstance(a,_ast.Num):
        return num_literal(a.n)
    
    elif isinstance(a,_ast.Name):
        return name_e(a.id)
    
    elif isinstance(a,_ast.NameConstant):
        if type(a.value) == bool:
            return bool_literal(a.value)
        else:
            return none_literal()


def convert_ast8(a):
    
    if isinstance(a,_ast.BoolOp):
        return boolOp_e(opMap[type(a.op)],
                          [convert_ast8(x) for x in a.values])
    
    elif isinstance(a,_ast.BinOp):
        return binaryOp_e(opMap[type(a.op)], 
                          [convert_ast8(a.left), convert_ast8(a.right)])
    
    elif isinstance(a,_ast.UnaryOp):
        return unaryOp_e(opMap[type(a.op)], convert_ast8(a.operand))
    
    elif isinstance(a,_ast.Lambda):
        return lambda_e(convert_ast8(a.args), convert_ast8(a.body))
    
    elif isinstance(a,_ast.IfExp):
        return if_e(convert_ast8(a.test),convert_ast8(a.body), convert_ast8(a.orelse))
    
    elif isinstance(a,_ast.Attribute):
        return attribute_e(convert_ast8(a.value), name_e(a.attr))

    elif isinstance(a,_ast.Subscript):
        if isinstance(a.slice,ast.Index):
            return subscript_ind_e(convert_ast8(a.value), convert_ast8(a.slice.value))
        else:
            return subscript_e(convert_ast8(a.value),
                               convert_ast8(a.slice.lower),
                               convert_ast8(a.slice.upper),
                               convert_ast8(a.slice.step))
    
    elif isinstance(a,_ast.Compare):
        return compare_e(convert_ast8(a.left),
                        [opMap[type(x)] for x in a.ops],
                        [convert_ast8(x) for x in a.comparators])
    
    elif isinstance(a,_ast.Call):
        return call_e(convert_ast8(a.func),
                     [convert_ast8(x) for x in a.args if not isinstance(x,_ast.Starred)],
                     [{k.arg : convert_ast(k.value)} for k in a.keywords],
                     [convert_ast8(x.value) for x in a.args if isinstance(x,_ast.Starred)]
                     )
    
    elif isinstance(a,_ast.ListComp):
        return listComp_e(convert_ast8(a.elt), [convert_ast8(x) for x in a.generators])
    
    elif isinstance(a,_ast.SetComp):
        return setComp_e(convert_ast8(a.elt), [convert_ast8(x) for x in a.generators])
    
    elif isinstance(a,_ast.DictComp):
        return dictComp_e(convert_ast8(a.key), convert_ast8(a.value), [convert_ast8(x) for x in a.generators])
    
    elif isinstance(a,_ast.comprehension):
        return comprehension_e(convert_ast8(a.target), convert_ast8(a.iter), convert_ast8(a.ifs))
    
    elif isinstance(a,_ast.List):
        return list_e([convert_ast8(x) for x in a.elts])
    
    elif isinstance(a,_ast.Tuple):
        return tuple_e([convert_ast8(x) for x in a.elts])
    
    elif isinstance(a,_ast.Set):
        return set_e([convert_ast8(x) for x in a.elts])
    
    elif isinstance(a,_ast.Dict):
        return dict_e([convert_ast8(x) for x in a.keys],[convert_ast8(x) for x in a.values])
    
    elif isinstance(a,_ast.Constant):
        if isinstance(a.value, str):
            return str_literal(a.s)
        elif isinstance(a.value, int) or isinstance(a.value,float):
            return num_literal(a.value)
        elif isinstance(a.value, bool):
            return bool_literal(a.value)
        elif a.value is None:
            return none_literal()
    
    elif isinstance(a,_ast.Name):
        return name_e(a.id)
    
all_ast_types = [boolOp_e,
                 binaryOp_e,
                 unaryOp_e,
                 lambda_e,
                 if_e,
                 listComp_e,
                 setComp_e,
                 dictComp_e,
                 generatorExpr_e,
                 compare_e,
                 call_e,
                 num_literal,
                 str_literal,
                 bool_literal,
                 none_literal,
                 name_e,
                 set_e,
                 list_e,
                 tuple_e,
                 dict_e,
                 attribute_e,
                 subscript_ind_e,
                 subscript_e,
                 slice_e,
                 index_e,
                 comprehension_e]

literal_ast_types = [num_literal,
                 str_literal,
                 bool_literal,
                 none_literal]

comprehension_types = [listComp_e,
                 setComp_e,
                 dictComp_e,
                 generatorExpr_e]

def is_ast(t):
    return type(t) in all_ast_types

def is_literal(t):
    return type(t) in literal_ast_types

def is_comprehension(t):
    return type(t) in comprehension_types
    

# Get all alias variables (where a is an alias, if a comes from
# some expression of the form 'a.x')

def get_aliases(a):
    if is_ast(a) and not is_literal(a):
        
        if type(a)==call_e:
            vs = [v for x in a[1:] for y in x for v in get_aliases(y) ]
            return set(vs)

        if type(a)==attribute_e:
            if type(a.value)==name_e:
                return { a.value.id }
            else:
                return set()

        retvars = set()
        for x in a:
            if is_ast(x):
                retvars = retvars.union(get_aliases(x))
            elif type(x)==list:
                for y in x:
                    if is_ast(y):
                        retvars = retvars.union(get_aliases(y))
        return retvars
    return set()
        
# Get all variables used in the AST expression

def get_all_vars(a):
    if is_ast(a) and not is_literal(a):
        if type(a) == name_e:
            return {a.id}
        
        if is_comprehension(a):
            vs = list(get_all_vars(a.expr)) + [v for g in a.generators for v in get_all_vars(g)]
            vs = set(vs) - {v for g in a.generators for v in get_all_vars(g.target)}
            return vs
            
        if type(a)==call_e:
            # We need a special case for the make_pql_tuple
            if isinstance(a.func, name_e) and a.func.id == 'make_pql_tuple':
                t = a.args[0].values
                vs = [v for x in t for v in get_all_vars(get_ast(x.values[0].value))]
                return set(vs)

            # And we need a special case for nested queries also. 
            if isinstance(a.func, name_e) and a.func.id == 'PyQuery':
                # Dig into the clauses of the nested query:
                clauses = eval(print_ast(a.args[0]))
                defined_vars = set()
                used_vars = set()
                for c in clauses:
                    used_vars = used_vars.union( c.used_vars() )
                            
                return used_vars - defined_vars

            else:        
                vs = [v for x in a[1:] for y in x for v in get_all_vars(y) ]
                return set(vs)
        
        if type(a)==attribute_e:
            return get_all_vars(a.value)
        
        retvars = set()
        for x in a:
            if is_ast(x):
                retvars = retvars.union(get_all_vars(x))
            elif type(x)==list:
                for y in x:
                    if is_ast(y):
                        retvars = retvars.union(get_all_vars(y))
        return retvars
    return set()

# Get all attribute mappings
# Similar to get all variables, but for each variable we also provide a mapping,
# if the variable binds to a simple attribute expression

def get_all_var_mappings(a):
    if is_ast(a) and not is_literal(a):
        if type(a) == name_e:
            return {a.id:None}
        
        if is_comprehension(a):
            vs = get_all_var_mappings(a.expr)
            for g in a.generators:
                gvs = vs.update( get_all_var_mappings(g) )
                for tv in get_all_vars(g.target):
                    if tv in gvs:
                        del gvs[tv]
                vs.update( gvs )
            return vs

        if type(a)==call_e:
            # We need a special case for the make_pql_tuple
            if isinstance(a.func, name_e) and a.func.id == 'make_pql_tuple':
                t = a.args[0].values
                vs = {}
                for tvs in [get_all_var_mappings(get_ast(x.values[0].value)) for x in t]:
                   vs.update( tvs)
                return vs

            if isinstance(a.func, name_e) and a.func.id == 'PyQuery':
                vs = {}
                # Dig into the clauses of the nested query:
                clauses = eval(print_ast(a.args[0]))
                defined_vars = set()
                used_vars = set()
                for c in clauses:
                    used_vars = used_vars.union( c.used_vars() )
                            
                for v in (used_vars - defined_vars):
                    vs[v] = None

                return vs

            else:        
                vs = {}
                for nested_vs in [get_all_var_mappings(y) for y in a.args]:
                    vs.update( nested_vs )

                return vs
        
        if type(a)==attribute_e:
            if type(a.value)==name_e:
                return {a.value.id : a.attribute.id}

            return get_all_var_mappings(a.value)
        
        retvars = {}
        for x in a:
            if is_ast(x):
                retvars.update(get_all_var_mappings(x))
            elif type(x)==list:
                for y in x:
                    if is_ast(y):
                        retvars.update(get_all_var_mappings(y))
        return retvars
    return {}



# Replace variables inside an expression accorind to the table
# of mappings

def replace_vars(a,table):
    if is_ast(a) and not is_literal(a):
        if type(a) == name_e:
            if a.id in table:
                return table[a.id]
            else:
                return a
            
        if type(a)==call_e:
            return call_e(a.func, *([replace_vars(x,table) for x in a[1:]]))
        
        if type(a)==attribute_e:
            return attribute_e(replace_vars(a.value,table),a.attribute)
 
        for (i,x) in enumerate(a):
            if is_ast(x):
                a = a._replace(**{a._fields[i]:replace_vars(x,table)})
            elif type(x)==list:
                for (j,y) in enumerate(x):
                    x[j] = replace_vars(y,table)
 
    return a

# Visit all nodes in the AST

def visit(a):
    if is_ast(a):
        yield a
    
    for x in a:
        if is_ast(x):
            for y in visit(x):
                yield y
        elif type(x)==list:
            for y in x:
                for z in visit(y):
                    yield z

# Compile into Python's AST and convert into our internal AST format

def get_ast(expr):
    a = compile(expr, '<string>', 'eval',ast.PyCF_ONLY_AST)

    if sys.version_info.major==3 and sys.version_info.minor >= 8:
        return convert_ast8(a.body)
    return convert_ast(a.body)

# Precedence table for figuring out whether we need to parenthesize an expression
# when printing it out

class_prec_table = {
    ('boolOp_e','compareOp_e'):True,
    ('boolOp_e','binaryOp_e'):True,
    ('boolOp_e','unaryOp_e'):True,
    ('boolOp_e','attribute_e'):True,
    ('boolOp_e','subscript_e'):True,
    ('boolOp_e','subscript_ind_e'):True,
    ('compareOp_e','binaryOp_e'):True,
    ('compareOp_e','unaryOp_e'):True,
    ('compareOp_e','attribute_e'):True,
    ('compareOp_e','subscript_e'):True,
    ('compareOp_e','subscript_ind_e'):True,
    ('binaryOp_e','unaryOp_e'):True,
    ('binaryOp_e','attribute_e'):True,
    ('binaryOp_e','subscript_e'):True,
    ('binaryOp_e','subscript_ind_e'):True,
    ('unaryOp_e','attribute_e'):True,
    ('unaryOp_e','subscript_e'):True,
    ('unaryOp_e','subscript_ind_e'):True,
    ('attribute_e','subscript_e'):True,
    ('attribute_e','subscript_ind_e'):True
  }

op_prec_table = {
    ('**','*'):1,
    ('**','/'):1,
    ('**','//'):1,
    ('**','%'):1,
    ('**','+'):1,
    ('**','||'):1,
    ('**','-'):1,
    ('^','*'):1,
    ('^','/'):1,
    ('^','//'):1,
    ('^','%'):1,
    ('^','+'):1,
    ('^','||'):1,
    ('^','-'):1,
    ('*','+'):1,
    ('*','||'):1,
    ('*','-'):1,
    ('/','+'):1,
    ('/','||'):1,
    ('/','-'):1,
    ('//','+'):1,
    ('//','||'):1,
    ('//','-'):1,
    ('%','+'):1,
    ('%','||'):1,
    ('%','-'):1
}

# A method that decides whether a node should be parenthesised when printed
# given its parent AST node

def needs_paren(child,parent):
    if (type(child).__doc__.split('(')[0], type(parent).__doc__.split('(')[0]) in class_prec_table:
        return True
    try:
        if (child.op,parent.op) in op_prec_table:
            return True
    except:
        return False
    return False

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

# Print AST into a Python expression format

def print_ast(a,paren=False):
    res = ""
    if isinstance(a,boolOp_e):
        res = (" %s " % a.op).join([ print_ast(x,needs_paren(x,a)) for x in a.args ])
    
    elif isinstance(a,binaryOp_e):
        res = (print_ast(a.args[0], needs_paren(a.args[0],a)) + (" %s " % a.op) +
                          print_ast(a.args[1], needs_paren(a.args[1],a.op)))
    
    elif isinstance(a,unaryOp_e):
        res = ("%s " % a.op) + print_ast(a.arg,needs_paren(a.arg,a))
    
    elif isinstance(a,lambda_e):
        res = "lambda " + ",".join([print_ast(x) for x in a.args]) + ": " + print_ast(a.body)
    
    elif isinstance(a,if_e):
        res = print_ast(a.test) + " if " + print_ast(a.then) + " else " + print_ast(a.or_else)
    
    elif isinstance(a,attribute_e):
        res = print_ast(a.value,needs_paren(a.value,a)) + "." + print_ast(a.attribute)
    
    elif isinstance(a,subscript_ind_e):
        res = print_ast(a.value,needs_paren(a.value,a)) + "[" + print_ast(a.index) + "]"

    elif isinstance(a,subscript_e):
        res = print_ast(a.value,needs_paren(a.value,a)) + "[" + ":".join([print_ast(x) if x else "" for x in [a.lower,a.upper,a.step]]) + "]"

    elif isinstance(a,compare_e):
        res = print_ast(a.left,needs_paren(a.left,a))
        for i in range(len(a.ops)):
            res += (" %s " % a.ops[i] ) + print_ast(a.comparators[i], needs_paren(a.comparators[i],a))
    
    elif isinstance(a,call_e):
        res = print_ast(a.func) + "("
        need_comma = False
        if a.args:
            res += ",".join([print_ast(x) for x in a.args])
            need_comma = True
        if a.kwargs:
            if need_comma:
                res += ","
            res += print_ast(a.kwargs)
            need_comma = True
        if a.starargs:
            if need_comma:
                res += ","
            res += print_ast(a.starargs)
        res += ")"
        
    elif isinstance(a,listComp_e):    
        res += '[' + print_ast(a.expr) + " " + " ".join([print_ast(x) for x in a.generators]) + ']'

    elif isinstance(a,setComp_e):    
        res += '{' + print_ast(a.expr) + " " + " ".join([print_ast(x) for x in a.generators]) + '}'

    elif isinstance(a,dictComp_e):    
        res += '{' + print_ast(a.key) + ':' + print_ast(a.value) + ' ' + " ".join([print_ast(x) for x in a.generators]) + '}'

    elif isinstance(a,comprehension_e):
        res += 'for ' + print_ast(a.target) + ' in ' + print_ast(a.iter)
        if a.ifs:
            res += ' if ' + print_ast(a.ifs)
    
    elif isinstance(a,list_e):    
        res += '[' + ','.join([print_ast(x) for x in a.values]) + ']'

    elif isinstance(a,tuple_e):
        res += '(' + ','.join([print_ast(x) for x in a.values])
        if len(a.values) == 1:
          res += ','
        res += ')'

    elif isinstance(a,set_e):
        res += '{' + ','.join([print_ast(x) for x in a.values]) + '}'
        
    elif isinstance(a,dict_e):
        res += '{' + ','.join([print_ast(k) + ':' + print_ast(v) for (k,v) in zip(a.keys,a.values)]) + '}'
    
    elif isinstance(a,str_literal):
        res = '"' + str_encode(a.value) + '"'
    
    elif isinstance(a,num_literal):
        res += repr(a.value)
    
    elif isinstance(a,name_e):
        res += a.id
    
    elif isinstance(a,bool_literal):
        res += repr(a.value)

    elif isinstance(a,none_literal):
        res += 'None'
    
    if paren:
        res = '(' + res + ')'
        
    return res
