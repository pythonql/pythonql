import ast,_ast
from collections import namedtuple

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
subscript_e = namedtuple('subscript_e',['value','slice'])

slice_e = namedtuple('slice_e',['lower','upper','step'])
index_e = namedtuple('index_e',['value'])

comprehension_e = namedtuple('comprehension',['target','iter','ifs'])

opMap = {_ast.Add:'+', _ast.Sub:'-', _ast.Mult:'*', _ast.Div:'/', 
        _ast.Mod:'%', _ast.Pow:'**', _ast.LShift:'<<', ast.RShift:'>>',
        _ast.BitOr:'???', _ast.BitXor:'???', _ast.BitAnd:'???', _ast.FloorDiv:'//',
        _ast.Invert:'???', _ast.Not:'not', _ast.Eq:'==', _ast.NotEq:'!=',
        _ast.Lt:'<', _ast.Gt:'>', _ast.LtE:'<=', _ast.GtE:'>=', _ast.Is:'is',
        _ast.IsNot:'isnot', _ast.In:'in', _ast.NotIn:"notin", _ast.And:'and',
        _ast.Or:'or'}

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
            else:        
                vs = [v for x in a[1:] for v in get_all_vars(x) ]
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

def get_ast(expr):
    return convert_ast(compile(expr, '<string>', 'eval',ast.PyCF_ONLY_AST).body)

class_prec_table = {
    ('boolOp_e','compareOp_e'):True,
    ('boolOp_e','binaryOp_e'):True,
    ('boolOp_e','unaryOp_e'):True,
    ('compareOp_e','binaryOp_e'):True,
    ('compareOp_e','unaryOp_e'):True,
    ('binaryOp_e','unaryOp_e'):True
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

def needs_paren(child,parent):
    if (type(child),type(parent)) in class_prec_table:
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
        
    # elif isinstance(a,_ast.ListComp):    
    # elif isinstance(a,_ast.SetComp):    
    # elif isinstance(a,_ast.DictComp):    
    # elif isinstance(a,_ast.comprehension):
    
    # elif isinstance(a,_ast.List):    
    # elif isinstance(a,_ast.Tuple):
    # elif isinstance(a,_ast.Set):
    
    # elif isinstance(a,_ast.Dict):
    
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
