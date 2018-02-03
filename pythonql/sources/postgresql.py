import re
from pythonql.sources.source import RDBMSTable
from pythonql.Ast import *
from pythonql.algebra.operator import plan_from_list
from pythonql.algebra.operators import *
from pythonql.PQTuple import PQTuple
from sqlalchemy import Table,MetaData,select
from sqlalchemy.types import Integer,Numeric,Date,DateTime,Boolean,Time,String

class Unsupported(Exception):
  None

class TypeError(Exception):
  None

# This function prints an ast of an expression in PostgreSQL SQL format that can
# be included in the queries.

def print_ast_psql(a,paren=False):
    res = ""
    if isinstance(a,boolOp_e):
        res = (" %s " % a.op).join([ print_ast_psql(x,needs_paren(x,a)) for x in a.args ])
    
    elif isinstance(a,binaryOp_e):
        res = (print_ast_psql(a.args[0], needs_paren(a.args[0],a)) + (" %s " % a.op) +
                          print_ast_psql(a.args[1], needs_paren(a.args[1],a.op)))
    
    elif isinstance(a,unaryOp_e):
        res = ("%s " % a.op) + print_ast_psql(a.arg,needs_paren(a.arg,a))
    
    elif isinstance(a,if_e):
        res = "case when " + print_ast_psql(a.test) + " then " + print_ast_psql(a.then) + " else " + print_ast_psql(a.or_else) + " end"
    
    elif isinstance(a,attribute_e):
        res = print_ast_psql(a.value,needs_paren(a.value,a)) + "." + print_ast_psql(a.attribute)
    
    elif isinstance(a,compare_e):
        res = print_ast_psql(a.left,needs_paren(a.left,a))
        for i in range(len(a.ops)):
            res += (" %s " % a.ops[i] ) + print_ast_psql(a.comparators[i], needs_paren(a.comparators[i],a))
    
    elif isinstance(a,call_e):
        # Special case for the parse function:
        if a.func.id == 'parse':
            res = print_ast_psql(a.args[0]) + '::timestamp'
        else:    
            res = print_ast_psql(a.func) + "("
            need_comma = False
            if a.args:
                res += ",".join([print_ast_psql(x) for x in a.args])
                need_comma = True
            if a.kwargs:
                if need_comma:
                    res += ","
                res += print_ast_psql(a.kwargs)
                need_comma = True
            if a.starargs:
                if need_comma:
                    res += ","
                res += print_ast_psql(a.starargs)
            res += ")"
    
    elif isinstance(a,str_literal):
        res = "'" + str_encode(a.value) + "'"
    
    elif isinstance(a,num_literal):
        res = repr(a.value)
    
    elif isinstance(a,name_e):
        res = a.id
    
    elif isinstance(a,bool_literal):
        res = lower(repr(a.value))

    elif isinstance(a,none_literal):
        res = 'NULL'
    
    if paren:
        res = '(' + res + ')'
        
    return res

# This function translates python AST into an AST that is closer to PostgreSQL and
# can be directly converted into an SQL string expression

def psql_translate_ast(expr,symtab,vv,alias_map={}):
    if type(expr)==compare_e:
        op_map = {'==':'=', '!=':"<>"}
        def map_op(o):
            if o in op_map:
                return op_map[o]
            return o
        
        if len(expr.ops)==1:
            return compare_e(psql_translate_ast(expr.left,symtab,vv,alias_map),
                             [map_op(expr.ops[0])],
                             [psql_translate_ast(expr.comparators[0],symtab,vv,alias_map)])
        else:
            comps = []
            for (i,x) in enumerate(expr.ops):
                left_arg = psql_translate_ast(expr.left,symtab,vv,alias_map) if i==0 else psql_translate_ast(expr.comparators[i-1],symtab,vv,alias_map)
                comps.append(compare_e(map_op(expr.ops[i]), left_arg, psql_translate_ast(expr.comparators[i],symtab,vv,alias_map)))
            return boolOp_e('and', comps)
    
    # Currently very limited support for binary ops, just numerics and strings.
    elif type(expr)==binaryOp_e:
        l_type = psql_infer_types_expr(expr.args[0],symtab,vv)['type']
        r_type = psql_infer_types_expr(expr.args[1],symtab,vv)['type']
        l_val = psql_translate_ast(expr.args[0],symtab,vv,alias_map)
        r_val = psql_translate_ast(expr.args[1],symtab,vv,alias_map)
        
        (op,op_type) = psql_func_map[(expr.op,(l_type,r_type))]
        if op_type=='op':
          return binaryOp_e(op, [l_val,r_val])
        else:
          return call_e(func=name_e(op), args=[l_val,r_val], kwargs=[], starargs=[])
    
    # Here we really need a real signature table. Since the function call is going
    # to Postgresql, we ignore keyword and star arguments. The function should also
    # just be a simple function - i.e. no fancy things like labmdas
    elif type(expr)==call_e:
        if expr.kwargs != [] or expr.starargs != []:
            raise Unsupported()
        if type(expr.func) != name_e:
            raise Unsupported()
            
        arg_types = tuple([ psql_infer_types_expr(a,symtab,vv)['type'] for a in expr.args ])
        arg_values = [ psql_translate_ast(a,symtab,vv,alias_map) for a in expr.args ]
        
        (op,op_type) = psql_func_map[ (expr.func.id, arg_types) ]
        if op_type=='func':
          return call_e(name_e(op), arg_values, [], [])
        else:
          return binaryOp_e(op,[arg_values[0], arg_values[1]])
    
    # In case of attribute reference we currently support extracting values from
    # a tuple variable and extracting day,month,year from date (just as a sample)
    elif type(expr)==attribute_e:
        v_type = psql_infer_types_expr(expr.value,symtab,vv)
        if v_type['type'] == 'tuple':
            
            new_val = expr.value
            if type(expr.value)==name_e and expr.value.id in alias_map:
                new_val = name_e(alias_map[expr.value.id])

            return attribute_e(new_val, psql_translate_ast(expr.attribute,symtab,vv,alias_map))
        else:
            return call_e(name_e('date_part'),
                          [str_literal(expr.attribute.id),psql_translate_ast(expr.value,symtab,vv,alias_map)],
                          [],
                          [])
    
    for (i,x) in enumerate(expr):
        if is_ast(x):
            expr = expr._replace(**{expr._fields[i]:psql_translate_ast(x,symtab,vv,alias_map)})
        elif type(x)==list:
            for (j,y) in enumerate(x):
                x[j] = psql_translate_ast(y,symtab,vv,alias_map)
    return expr

# Translate and convert a python AST into an SQL string expression

def psql_translate_expr(e,symtab,vv,alias_map={}):
    return print_ast_psql(psql_translate_ast(e,symtab,vv,alias_map))

# Map datatypes from SQL Alchemy datatypes to internal PythonQL
# datatypes.

def psql_map_type(t):
    if isinstance(t,String):
        return {'type':'string'}
    elif isinstance(t,Numeric) or isinstance(t,Integer):
        return {'type':'number'}
    elif isinstance(t,Boolean):
        return {'type':'boolean'}
    elif isinstance(t,Date):
        return {'type':'date'}
    elif isinstance(t,Time):
        return {'type':'time'}
    elif isinstance(t,DateTime):
        return {'type':'datetime'}

# Python operator and function signature tables

python_signs_table = {
    ('+',('number','number')) : 'number',
    ('-',('number','number')) : 'number',
    ('*',('number','number')) : 'number',
    ('/',('number','number')) : 'number',
    ('**',('number','number')) : 'number',
    
    ('+',('string','string')) : 'string',
    
    ('+',('number',)) : 'number',
    ('-',('number',)) : 'number',
    
    ('upper',('string',)) : 'string',
    ('lower',('string',)) : 'string',
    ('parse',('string',)) : 'datetime',
    ('now',tuple()) : 'datetime'
}

# Mapping from Python operators and functions
# into PostgreSQL ops and functions. The mapping
# is type dependent (for example '+' operator can
# become a '+' in SQL or a '||' string concatenation
# operator

psql_func_map = {
    ('+',('number','number')) : ('+','op'),
    ('-',('number','number')) : ('-','op'),
    ('*',('number','number')) : ('*','op'),
    ('/',('number','number')) : ('/','op'),
    ('**',('number','number')) : ('^','op'),

    ('+',('string','string')) : ('||','op'),

    ('+',('number',)) : ('+','op'),
    ('-',('number',)) : ('-','op'),

    ('upper',('string',)) : ('upper','func'),
    ('lower',('string',)) : ('lower','func'),
    ('parse',('string',)) : ('parse','func'),
    ('now',tuple()) : ('now','func'),
}

# Infer the type of a nested query that we are willing to support
# Todo: we really have a nested query here, so we should have a 
# nested symbol table here

def psql_infer_types_nested(expr,symtab,vv):
    clauses = eval(print_ast(expr.args[0]))
    for c in clauses:
        if not type(c) in [Select,For,Let,Where]:
            raise Unsupported()

        if type(c) == For:
            e = get_ast(c.expr)
            if (isinstance(e,name_e) and isinstance(vv.get(e.id), RDBMSTable) ):
                table = vv[e.id].table
                values = [ (x.name, psql_map_type(x.type)) for x in table.c ]
                symtab[c.vars[0]] = {'type':'tuple', 'table':table, 'values':values}
            else:
                raise Unsupported()

        elif type(c) == Let:
            if len(c.vars) != 1:
               raise Unsupported()
            symtab[c.vars[0]] = psql_infer_types_expr(get_ast(c.expr),symtab,vv)

        elif type(c) == Where:
            psql_infer_types_expr(get_ast(c.expr),symtab,vv)

        # Select clause is very special in the nested query, since we're building
        # up new tuples here. Of course here we only support limited forms of tuple
        # construction, namely just two:
        #   1. A single expression
        #   2. A tuple of expressions
        # In all other cases an exception will be thrown


        # FIXME: Get the tuple business out of the wrapper code into Ast module

        elif type(c) == Select:
            e = get_ast(c.expr)
            if isinstance(e,call_e) and isinstance(e.func,name_e) and e.func.id == 'make_pql_tuple':
                vals = []
                for t in e.args[0].values:
                    te = t.values[0].value
                    te_repr = te.replace(" ","")
                    if re.match("\w+\.",te_repr):
                        te_repr = "".join( te_repr.split(".")[1:] )
                    ae = t.values[1]
                    alias = te_repr if isinstance(ae,none_literal) else ae.value
                    te_type = psql_infer_types_expr(get_ast(te),symtab,vv)
                    if te_type['type'] == 'tuple':
                        raise Unsupported()

                    vals.append((alias, te_type))
                return {'type':'list', 'unit_type':{'type':'tuple', 'values':vals}}
            else:
                return {'type':'list', 'unit_type':psql_infer_types_expr(e, symtab, vv) }
          

# Infer the type an AST expression that we're trying to send
# to the database

def psql_infer_types_expr(expr,symtab, vv):
    
    if type(expr)==compare_e:
        psql_infer_types_expr(expr.left,symtab,vv)
        for a in expr.comparators:
            psql_infer_types_expr(a,symtab,vv)
        return {'type':'boolean'}
    
    elif type(expr) == boolOp_e:
        for a in expr.args:
            psql_infer_types_expr(a,symtab,vv)
        return {'type':'boolean'}
    
    # Currently very limited support for binary ops, just numerics and strings. And
    # the output type is the type of one of the operands. 
    elif type(expr) == binaryOp_e:
        l_type = psql_infer_types_expr(expr.args[0],symtab,vv)['type']
        r_type = psql_infer_types_expr(expr.args[1],symtab,vv)['type']

        if not (expr.op,(l_type,r_type)) in python_signs_table:
          raise Unsupported()

        return {'type':python_signs_table[(expr.op,(l_type,r_type))]}
    
    elif type(expr)==unaryOp_e:
        a_type = psql_infer_types_expr(expr.args[0],symtab,vv)['type']
        return {'type':python_signs_table[(expr.op,(a_type,))]}
    
    # In the case of if_then_else, the Python expression can have different types
    # but not the expression that will be sent to the database. So we reject if types of
    # the then and else are different
    elif type(expr)==if_e:
        psql_infer_types(expr.test,symtab,vv)
        then_type = psql_infer_types_expr(expr.then,symtab,vv)
        else_type = psql_infer_types_expr(expr.or_else,symtab,vv)
        if then_type != else_type:
            raise Unsupported()
        return then_type
    
    # Here we really need a real signature table. Since the function call is going
    # to Postgresql, we ignore keyword and star arguments. The function should also
    # just be a simple function - i.e. no fancy things like labmdas
    elif type(expr)==call_e:
        if expr.kwargs != [] or expr.starargs != []:
            raise Unsupported()
        if type(expr.func) != name_e:
            raise Unsupported()

        # We have two special cases here: one for a nested query and another for an
        # 'outer' function on top of a nested query
        if expr.func.id == 'outer':
          return psql_infer_types_nested(expr.args[0],symtab,vv)

        elif expr.func.id == 'PyQuery':
          return psql_infer_types_nested(expr,symtab,vv)
            
        arg_types = tuple([ psql_infer_types_expr(a,symtab,vv)['type'] for a in expr.args ])
        return {'type':python_signs_table[ (expr.func.id, arg_types) ]}           
        
    elif type(expr)==num_literal:
        return {'type':'number'}
    
    elif type(expr)==str_literal:
        return {'type':'string'}
    
    elif type(expr)==bool_literal:
        return {'type':'boolean'}
    
    elif type(expr)==none_literal:
        return {'type':'none'}
    
    # If we see a name, we substitute the type from the symbol table
    # If its defined externally, then we don't support such expression
    # for now
    elif type(expr)==name_e:
        return symtab[expr.id]
    
    # In case of attribute reference we currently support extracting values from
    # a tuple variable and extracting day,month,year from date (just as a sample)
    elif type(expr)==attribute_e:
        v_type = psql_infer_types_expr(expr.value,symtab,vv)
        if v_type['type'] == 'tuple':
            if 'table' in v_type:
                col_dict = v_type['table'].c
                if not expr.attribute.id in col_dict:
                   raise TypeError("Table '%s' doesn't contain column '%s'" % (v_type['table'].name, expr.attribute.id))
                col = col_dict[expr.attribute.id]
                return psql_map_type(col.type)
            else:
                vmap = {v[0]:v[1] for v in v_type['values']}
                if not expr.attribute.id in vmmap:
                   raise TypeError("Column '%s' not found in nested expression" %  expr.attribute.id)
                return vmap[expr.attribute.id]
        
        elif v_type['type'] in ['date','datetime','time']:
            if v_type['type'] in ['date','datetime'] and expr.attribute.id in ['day','year','month']:
                return {'type':'number'}
            if v_type['type'] in ['datetime','time'] and expr.attriubte.id in ['hour','minute','second','microsecond']:
                return {'type':'number'}
            raise TypeError("Illegal attribute '%s'" % expr.attribute.id )
        else:
            raise TypeError("Illegal attribute '%s'" % expr.attribute.id )

# Infer the datatypes of all variables in the list of clauses

def psql_infer_types(subplan,vv):
    symtab = {}
    for node in subplan.as_list_reversed():
        c = node.op
        if type(c) == For:
            if c.database:
                src = c.database['source']
                values = [ (x.name, psql_map_type(x.type)) for x in src.table.c ]
                symtab[c.vars[0]] = {'type':'tuple', 'table':src.table, 'values':values}
            else:
                t = psql_infer_types_expr(get_ast(c.expr),symtab,vv)
                symtab[c.vars[0]] = t['unit_type']
                
        elif type(c) == Let:
            symtab[c.vars[0]] = psql_infer_types_expr(get_ast(c.expr),symtab,vv)
        elif type(c) == Where:
            psql_infer_types_expr(get_ast(c.expr),symtab,vv)
    return symtab

# PostgreSQL data source. 

class PostgresTable(RDBMSTable):

  def __init__(self,engine,table_name,schema_name=None):
    self.engine = engine
    self.table_name = table_name
    self.schema_name = schema_name
    self.table = Table(table_name, MetaData(), autoload=True, autoload_with=engine, schema=schema_name)

  # Check whether this source supports the given expression, given a set of clauses
  # already pushed to the source

  def supports(self,subplan,expr,visible_vars):
    try:
        symtab = psql_infer_types(subplan,visible_vars)
        psql_infer_types_expr(expr,symtab,visible_vars)
        return True
    except Unsupported:
        return False

  # Return a db_source clause with an SQL query that corresponds to the clauses that
  # have been pushed into this source. Only produce variables that are mentioned in the
  # project_list

  def wrap(self,subplan,project_list,visible_vars):
    tables = []
    output_tuple_vars = []
    output_vars = []
    output_exprs = {}
    where_exprs = []
    
    symtab = psql_infer_types(subplan,visible_vars)
    
    src = None
    
    for node in subplan.as_list_reversed():
        c = node.op

        if type(c) == For:
            
            # If this is a clause that goes against the database source,
            # record the table name in the output SQL and the output variable 
            # as well.
            
            if c.database:
                src_meta = c.database
                src = c.database['source']
                t = psql_infer_types_expr(get_ast(c.vars[0]),symtab,visible_vars)
                tables.append( { 'table_name': src.table_name if not src.schema_name else "%s.%s" % (src.schema_name,src.table_name),
                                 'tuple_var' : c.vars[0],
                                 'output_schema' : t } )
                output_tuple_vars.append(c.vars[0])
                
            # If this is an outerjoin clause, we will process the nested query
            # and create a nested query that we'll outerjoin with the main query.

            else:
                e = get_ast(c.expr)
                if ( isinstance(e,call_e) and isinstance(e.func, name_e) and e.func.id == 'outer' and
                        isinstance(e.args[0],call_e) and isinstance(e.args[0].func, name_e) and e.args[0].func.id == 'PyQuery' ):
                    nested_clauses = eval(print_ast(e.args[0].args[0]))
                    nested_clauses.reverse()
                    nested_plan = plan_from_list(nested_clauses)

                    nested_tables = []
                    n_output_exprs = {}
                    n_where_exprs = []
                    n_output_vars = []
                    is_tuple_expr = False
                    
                    for nnode in nested_plan.as_list():
                        nc = nnode.op

                        if type(nc) == For:
                            # The expression in this clause has to be a variable that binds to an RDBMSTable
                            source = get_ast(nc.expr)
                            n_src = visible_vars[source.id]

                            nested_tables.append( {'table_name': n_src.table_name if not n_src.schema_name else "%s.%s" % (n_src.schema_name,n_src.table_name),
                                                   'tuple_var': nc.vars[0] } )

                        if type(nc) == Let:
                            e2 = get_ast(nc.expr)
                            e2 = replace_vars(e2,n_output_exprs)
                            n_output_exprs[c.vars[0]] = e2

                        if type(nc) == Where:
                            e2 = get_ast(nc.expr)
                            e2 = replace_vars(e2,n_output_exprs)
                            n_where_exprs.append( e2 )

                        if type(nc) == Select:
                            e2 = get_ast(nc.expr)
                            e2 = replace_vars(e2,n_output_exprs)
                            if isinstance(e2,call_e) and isinstance(e2.func,name_e) and e2.func.id == 'make_pql_tuple':
                                for t in e2.args[0].values:
                                    te = t.values[0].value.replace(" ","")
                                    te_a = te.replace(" ","")
                                    if re.match("\w+\.",te_a):
                                        te_a = "".join( te_a.split(".")[1:] )
                                    if not re.match("^\w+$",te_a):
                                        te_a = '"' + te_a + '"'
                                    ae = t.values[1]
                                    alias = te_a if isinstance(ae,none_literal) else ae.value
                                    n_output_vars.append( {'var':get_ast(te), 'alias':alias} )
                                
                            else:
                                if isinstance(e2,name_e) and psql_infer_types_expr(e2,symtab,visible_vars)['type'] == 'tuple':
                                    is_tuple_expr = True
                                n_output_vars = [ {'var':e2, 'alias':None}  ]

                    output_tuple_vars.append(c.vars[0])
                    output_schema = psql_infer_types_expr(e,symtab,visible_vars)['unit_type']
                    if output_schema['type'] != 'tuple':
                        output_schema = {"values":[ ('#value',{'type':output_schema['type']}) ]}
                    output_schema['values'].append( ('#checkbit',{'type':'boolean'}) )

                    tables.append( {'nested_tables':nested_tables, 
                                    'where':n_where_exprs, 
                                    'output':n_output_vars, 
                                    'output_schema': output_schema,
                                    'tuple_var':c.vars[0], 
                                    'is_tuple_expr':is_tuple_expr,
                                    'clause_vars':nested_plan.defined_vars(),
                                    'outer':True } )
        
        if type(c) == Let:
            
            # We support two types of let clauses, the outerjoin let clause and
            # a basic expression let clause
            e = get_ast(c.expr)

            output_vars.append( c.vars[0])
            
            # We need to scan the expression first and
            # replace all non-tuple variables with the expressions that computed them.
            e = replace_vars(e,output_exprs)
            
            output_exprs[c.vars[0]] = e

            
        if type(c) == Where:
            
            # Add a where clause expression to the query. Again, we need to replace all
            # the non-tuple variables with expressions that computed them.
            e = get_ast(c.expr)
            e = replace_vars(e,output_exprs)
            where_exprs.append( e )
            
    # Project out variables that are not needed above in the plan
    output_tuple_vars = [v for v in output_tuple_vars if v in project_list]
    output_vars = [v for v in output_vars if v in project_list]
                
    sql_query = "SELECT "
    sql_query += ", ".join(['%s.*' % v for v in output_tuple_vars])
    if output_vars:
        if output_tuple_vars:
            sql_query += ", "
        sql_query += ", ".join(['%s as %s' % 
                                    (psql_translate_expr(output_exprs[v],symtab,visible_vars),v) for v in output_vars] )
        
    join_expr = ""
    for (i,t) in enumerate(tables):
        if i!=0 and not 'outer' in t:
            join_expr += ", "

        if 'table_name' in t:
            join_expr +=  "%s as %s" % (t['table_name'],t['tuple_var']) 

        if 'outer' in t:
            subquery = "( SELECT "
            if t['is_tuple_expr']:
                subquery += ' %s.*,true as "#checkbit"' % t['output'][0]['var'].id
            else:
                printed_exprs = [(psql_translate_expr(v['var'],symtab,visible_vars), v['alias']) for v in t['output']]
                printed_exprs.append( ('true','"#checkbit"') )
                subquery += ", ".join(['%s as %s' % (v,a) if a else '%s' % v for (v,a) in printed_exprs])
            subquery += "\nFROM " + ", ".join([ "%s as %s" % (x['table_name'],x['tuple_var']) for x in t['nested_tables']])
            subquery += " ) as %s" % t['tuple_var']
            if t['where']:
              aliases = { a for b in [get_aliases(x) for x in t['where']] for a in b}
              filtered_aliases = aliases.intersection( t['clause_vars'] )
              alias_map = { a:t['tuple_var'] for a in filtered_aliases }
              subquery += "\nON " + " and ".join([psql_translate_expr(w,symtab,visible_vars,alias_map) for w in t['where']])
            else:
              subquery += "\nON true"

            join_expr += " LEFT JOIN " + subquery 
            
    sql_query += "\n"
    sql_query += "FROM "
    sql_query += join_expr
        
    sql_query += "\n"
    if where_exprs:
        sql_query += "WHERE " + " and ".join([psql_translate_expr(w,symtab,visible_vars) for w in where_exprs])
        
    return WrappedSubplan(src, sql_query, tables, output_vars)

  # Execute an SQL query and wrap the result in a generator
  # that produces PQTuple objects (possibly nested)

  def execute(self,query,tuple_vars,vars):
    res = self.engine.execute(query)
    schema = {}
    tuple_schemas = []

    for t in tuple_vars:
        v = t['tuple_var']
        schema[v] = len(schema)
        tuple_schema = {}
        final_tuple_schema = {}
        rev_tuple_schema = []
        for (c_name,_) in t['output_schema']['values']:
            tuple_schema[c_name] = len(tuple_schema)
            if c_name != '#checkbit':
                final_tuple_schema[c_name] = len(final_tuple_schema)

            tuple_schema[c_name] = len(tuple_schema)
            rev_tuple_schema.append(c_name)

        tuple_schemas.append( (tuple_schema,final_tuple_schema,rev_tuple_schema) )

    for v in vars:
        schema[v] = len(schema)

    for r in res:
        i = 0
        out_t = []
        for j,_ in enumerate(tuple_vars):
            checkbit = True
            isTuple = True
            t_data = []
            (sc,final_sc,rev_sc) = tuple_schemas[j]
            for k in range(len(sc)):
                if rev_sc[k] == '#checkbit':
                    checkbit = r[i]
                else:
                    t_data.append(r[i])
                if rev_sc[k] == '#value':
                    isTuple = False
                i += 1
            
            if isTuple:
                out_t.append( PQTuple( t_data, final_sc ) if checkbit else None )
            else:
                out_t.append(t_data[0])

        for v in vars: 
            out_t.append(r[i])
            i += 1

        yield PQTuple( out_t, schema )
