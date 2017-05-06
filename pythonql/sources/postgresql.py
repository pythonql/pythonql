from pythonql.sources.source import RDBMSTable
from pythonql.Ast import *
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
            res += print_ast_psql(a.args[0]) + '::timestamp'
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
        res += repr(a.value)
    
    elif isinstance(a,name_e):
        res += a.id
    
    elif isinstance(a,bool_literal):
        res += lower(repr(a.value))

    elif isinstance(a,none_literal):
        res += 'NULL'
    
    if paren:
        res = '(' + res + ')'
        
    return res

# This function translates python AST into an AST that is closer to PostgreSQL and
# can be directly converted into an SQL string expression

def psql_translate_ast(expr,symtab):
    if type(expr)==compare_e:
        op_map = {'==':'=', '!=':"<>"}
        def map_op(o):
            if o in op_map:
                return op_map[o]
            return o
        
        if len(expr.ops)==1:
            return compare_e(psql_translate_ast(expr.left,symtab),
                             [map_op(expr.ops[0])],
                             [psql_translate_ast(expr.comparators[0],symtab)])
        else:
            comps = []
            for (i,x) in enumerate(expr.ops):
                left_arg = psql_translate_ast(expr.left,symtab) if i==0 else psql_translate_ast(expr.comparators[i-1],symtab)
                comps.append(compare_e(map_op(expr.ops[i]), left_arg, psql_translate_ast(expr.comparators[i],symtab)))
            return boolOp_e('and', comps)
    
    # Currently very limited support for binary ops, just numerics and strings.
    elif type(expr)==binaryOp_e:
        l_type = psql_infer_types_expr(expr.args[0],symtab)['type']
        r_type = psql_infer_types_expr(expr.args[1],symtab)['type']
        l_val = psql_translate_ast(expr.args[0],symtab)
        r_val = psql_translate_ast(expr.args[1],symtab)
        
        op = psql_func_map[(expr.op,(l_type,r_type))]
        return binaryOp_e(op, [l_val,r_val])
    
    # Here we really need a real signature table. Since the function call is going
    # to Postgresql, we ignore keyword and star arguments. The function should also
    # just be a simple function - i.e. no fancy things like labmdas
    elif type(expr)==call_e:
        if expr.kwargs != [] or expr.starargs != []:
            raise Unsupported()
        if type(expr.func) != name_e:
            raise Unsupported()
            
        arg_types = tuple([ psql_infer_types_expr(a,symtab)['type'] for a in expr.args ])
        arg_values = [ psql_translate_ast(a,symtab) for a in expr.args ]
        
        return call_e(name_e(psql_func_map[ (expr.func.id, arg_types) ]), arg_values, [], [])
    
    # In case of attribute reference we currently support extracting values from
    # a tuple variable and extracting day,month,year from date (just as a sample)
    elif type(expr)==attribute_e:
        v_type = psql_infer_types_expr(expr.value,symtab)
        if v_type['type'] == 'tuple':
            return expr
        else:
            return call_e(name_e('date_part'),
                          [str_literal(expr.attribute.id),psql_translate_ast(expr.value,symtab)],
                          [],
                          [])
    
    for (i,x) in enumerate(expr):
        if is_ast(x):
            expr = expr._replace(**{expr._fields[i]:psql_translate_ast(x,symtab)})
        elif type(x)==list:
            for (j,y) in enumerate(x):
                x[j] = psql_translate_ast(y,symtab)
    return expr

# Translate and convert a python AST into an SQL string expression

def psql_translate_expr(e,symtab):
    return print_ast_psql(psql_translate_ast(e,symtab))

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
    ('parse',('string',)) : 'datetime'
}

# Mapping from Python operators and functions
# into PostgreSQL ops and functions. The mapping
# is type dependent (for example '+' operator can
# become a '+' in SQL or a '||' string concatenation
# operator

psql_func_map = {
    ('+',('number','number')) : '+',
    ('-',('number','number')) : '-',
    ('*',('number','number')) : '*',
    ('/',('number','number')) : '/',
    ('**',('number','number')) : '^',
    
    ('+',('string','string')) : '||',
    
    ('+',('number',)) : '+',
    ('-',('number',)) : '-',
    
    ('upper',('string',)) : 'upper',
    ('lower',('string',)) : 'lower',
    ('parse',('string',)) : 'parse'
}

# Infer the type an AST expression that we're trying to send
# to the database

def psql_infer_types_expr(expr,symtab):
    
    if type(expr)==compare_e:
        psql_infer_types_expr(expr.left,symtab)
        for a in expr.comparators:
            psql_infer_types_expr(a,symtab)
        return {'type':'boolean'}
    
    elif type(expr) == boolOp_e:
        for a in expr.args:
            psql_infer_types_expr(a,symtab)
        return {'type':'boolean'}
    
    # Currently very limited support for binary ops, just numerics and strings. And
    # the output type is the type of one of the operands. 
    elif type(expr) == binaryOp_e:
        l_type = psql_infer_types_expr(expr.args[0],symtab)['type']
        r_type = psql_infer_types_expr(expr.args[1],symtab)['type']

        if not (expr.op,(l_type,r_type)) in python_signs_table:
          raise Unsupported()

        return {'type':python_signs_table[(expr.op,(l_type,r_type))]}
    
    elif type(expr)==unaryOp_e:
        a_type = psql_infer_types_expr(expr.args[0],symtab)['type']
        return {'type':python_signs_table[(expr.op,(a_type,))]}
    
    # In the case of if_then_else, the Python expression can have different types
    # but not the expression that will be sent to the database. So we reject if types of
    # the then and else are different
    elif type(expr)==if_e:
        psql_infer_types(expr.test,symtab)
        then_type = psql_infer_types_expr(expr.then,symtab)
        else_type = psql_infer_types_expr(expr.or_else,symtab)
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
            
        arg_types = tuple([ psql_infer_types_expr(a,symtab)['type'] for a in expr.args ])
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
        v_type = psql_infer_types_expr(expr.value,symtab)
        if v_type['type'] == 'tuple':
            col_dict = v_type['table'].c
            if not expr.attribute.id in col_dict:
                raise TypeError("Table '%s' doesn't contain column '%s'" % (v_type['table'].name, expr.attribute.id))
            col = col_dict[expr.attribute.id]
            return psql_map_type(col.type)
        
        elif v_type['type'] in ['date','datetime','time']:
            if v_type['type'] in ['date','datetime'] and expr.attribute.id in ['day','year','month']:
                return {'type':'number'}
            if v_type['type'] in ['datetime','time'] and expr.attriubte.id in ['hour','minute','second','microsecond']:
                return {'type':'number'}
            raise TypeError("Illegal attribute '%s'" % expr.attribute.id )
        else:
            raise TypeError("Illegal attribute '%s'" % expr.attribute.id )

# Infer the datatypes of all variables in the list of clauses

def psql_infer_types(clauses):
    symtab = {}
    for c in clauses:
        if c['name'] == 'for':
            src = c['database']['source']
            symtab[c['vars'][0]] = {'type':'tuple', 'table':src.table}
        elif c['name'] == 'let':
            symtab[c['vars'][0]] = psql_infer_types_expr(get_ast(c['expr']),symtab)
        elif c['name'] == 'where':
            psql_infer_types_expr(get_ast(c['expr']),symtab)
    return symtab

# PostgreSQL data source. 

class PostgresTable(RDBMSTable):

  def __init__(self,engine,table_name,schema_name=None):
    self.engine = engine
    self.table_name = table_name
    self.schema_name = schema_name
    self.table = Table(table_name, MetaData(), autoload=True, autoload_with=engine)

  # Check whether this source supports the given expression, given a set of clauses
  # already pushed to the source

  def supports(self,clauses,expr):
    try:
        symtab = psql_infer_types(clauses)
        psql_infer_types_expr(expr,symtab)
        return True
    except Unsupported:
        return False

  # Return a db_source clause with an SQL query that corresponds to the clauses that
  # have been pushed into this source. Only produce variables that are mentioned in the
  # project_list

  def wrap(self,clauses,project_list):
    tables = []
    output_tuple_vars = []
    output_vars = []
    output_exprs = {}
    where_exprs = []
    
    symtab = psql_infer_types(clauses)
    
    src = None
    
    for c in clauses:
        if c['name'] == 'for':
            
            # If this is a clause that goes against the database source,
            # record the table name in the output SQL and the output variable 
            # as well.
            
            if 'database' in c:
                src_meta = c['database']
                src = c['database']['source']
                tables.append( (src.table_name, c['vars'][0]))
                output_tuple_vars.append(c['vars'][0])
                
            # We don't do anything otherwise yet (for example if the for clause
            # drills into a JSONb object or into a datetime object or just into the
            # tuple variable)
        
        if c['name'] == 'let':
            
            # For the let clause, we'll just add an output variable and an expression
            # to the select clause. 
            
            output_vars.append( c['vars'][0])
            
            # We need to scan the expression first and
            # replace all non-tuple variables with the expressions that computed them.
            e = get_ast(c['expr'])
            e = replace_vars(e,output_exprs)
            
            output_exprs[c['vars'][0]] = e

            
        if c['name'] == 'where':
            
            # Add a where clause expression to the query. Again, we need to replace all
            # the non-tuple variables with expressions that computed them.
            e = get_ast(c['expr'])
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
                                    (psql_translate_expr(output_exprs[v],symtab),v) for v in output_vars] )
        
    sql_query += "\n"
    sql_query += "FROM "
    sql_query += ", ".join( ["%s as %s" % (t[0],t[1]) for t in tables])
        
    sql_query += "\n"
    if where_exprs:
        sql_query += "WHERE " + " and ".join([psql_translate_expr(w,symtab) for w in where_exprs])
        
    return {'name':'db_source', 
            'database':src, 
            'query':sql_query, 
            'tuple_vars':tables,
            'vars':output_vars
    }

  # Execute an SQL query and wrap the result in a generator
  # that produces PQTuple objects (possibly nested)

  def execute(self,query,tuple_vars,vars):
    res = self.engine.execute(query)
    schema = {}
    tuple_schemas = []
    for table_name,v in tuple_vars:
        schema[v] = len(schema)
        tuple_schema = {}
        table = Table(table_name, MetaData(), autoload=True, autoload_with=self.engine)
        for c in table.columns:
            tuple_schema[c.name] = len(tuple_schema)
        tuple_schemas.append( tuple_schema )

    for v in vars:
        schema[v] = len(schema)

    for r in res:
        i = 0
        out_t = []
        for j,(_,v) in enumerate(tuple_vars):
            t_data = []
            sc = tuple_schemas[j]
            for k in range(len(sc)):
                t_data.append(r[i])
                i += 1
            out_t.append( PQTuple( t_data, sc ) )

        for v in vars: 
            out_t.append(r[i])
            i += 1

        yield PQTuple( out_t, schema )
