from pythonql.Ast import *
from pythonql.sources.source import RDBMSTable

def ensure_list(x):
    if isinstance(x,list):
        return x
    else:
        return [x]

def clause_vars(clauses):
    vs = set()
    for c in clauses:
        if c['name'] == 'join':
                vs = vs.union(clause_vars(ensure_list(c['left'])))
                vs = vs.union(clause_vars(ensure_list(c['right'])))
        elif c['name'] in ['for','let','window','match']:
            vs = vs.union(set(c['vars']))
        elif c['name'] =='groupby':
            vs = vs.union({v[1] for v in c['groupby_list']})            
    return vs

# Need to add a case for the match clause here
def clause_live_vars(clauses):
    vs = set()
    for c in clauses:
        if c['name'] == 'select':
            vs = vs.union(get_all_vars(get_ast(c['expr'])))
        elif c['name'] == 'join' and 'cond' in c:
            vs = vs.union(get_all_vars(get_ast(c['cond'])))
        elif c['name'] in ['for','let','where']:
            e = get_ast(c['expr'])
            vs = vs.union(get_all_vars(e))
        elif c['name'] == 'orderby':
            for ex in c['orderby_list']:
                e = get_ast(ex)
                vs = vs.union(get_all_vars(e))
        elif c['name'] == 'groupby':
            for (ex,_) in c['groupby_list']:
                e = get_ast(ex)
                vs = vs.union(get_all_vars(e))
    return vs

def is_join_cond(e):
    if isinstance(e,compare_e):
        if len(e.ops)==1 and e.ops[0] == '==':
            if all([type(x) in [name_e,attribute_e] for x in  visit(e.left) ]):
                if all([type(x) in [name_e,attribute_e] for x in  visit(e.comparators[0]) ]):
                    return True
    return False

def visit_joins(j):
    yield j
    
    if not isinstance(j['left'],list):
        for jj in visit_joins(j['left']):
            yield jj
            
    if not isinstance(j['right'],list):
        for jj in visit_joins(j['right']):
            yield jj

def rewrite(clauses,visible_vars):
    source_id = 0
    databases = {}
    source_meta = {}
    source_clauses = {}
    rest_clauses = []
    
    # Have we seen any group-bys in the plan?
    # In this case we can't push fors or lets any longer
    groupbys_seen = False
    
    # All visible variables at this point in the plan
    current_vars = set()
    
    # Live variables - all variables that are needed above in the plan
    live_vars = set()
    
    # Variables that were turned into a list by group-by
    list_vars = set()
    
    hints = []
    join_conds = []
    
    for c in clauses:
        
        # Compute all defined vars
        current_vars = current_vars.union(clause_vars([c]))
        
        # If we see a for clause, we try to find its source, if there's none,
        # we'll create a new source. We'll then push the for clause into the
        # source clause. This can be done for the clauses that don't depend upon
        # any variables.
        if c['name'] == 'for' and not groupbys_seen:
            source = get_ast(c['expr'])
            if (len(c['vars']) == 1 
                    and isinstance(source,name_e) 
                    and isinstance(visible_vars[source.id], RDBMSTable) ):
                database = visible_vars[source.id]
                meta = {"type":"database", 
                            "database":database.engine,
                            "source":database
                }
                c['database'] = meta

                if not database.engine.url in databases:
                    source_meta[source_id] = meta
                    databases[database.engine.url] = source_id
                    source_clauses[source_id] = []
                    source_id += 1
                source_clauses[databases[database.engine.url]].append(c)
                
            # elif (isinstance(source,call_e) and 
            #        isinstance(source.func,name_e) and
            #        source.func.id == 'Postgres'):
                
            #    database = source.args[0]
            #    if not database in databases:
            #        databases[database] = source_id
            #        source_meta[source_id] = {"type":"database", "database":database}
            #        source_clauses[source_id] = []
            #        source_id += 1
            #    source_clauses[databases[database]].append(c)
            
            elif len(c['vars'])==1 and set(get_all_vars(source)).intersection(current_vars) == set():
                source_meta[source_id] = {"type":"expr", "expr":c['expr']}
                source_clauses[source_id] = [c]
                source_id += 1
            else:
                rest_clauses.append(c)
        
        # We can push let clause into one of the sources, if that can't happen, we'll create
        # a new source for it. It can be pushed into an existing source only if it only depends
        # upon the variables in only the source or has no dependencies. 
        elif c['name'] == 'let' and not groupbys_seen:
            expr = get_ast(c['expr'])
            let_vars = get_all_vars(expr)
            srcs = [s for s in range(source_id) if let_vars - clause_vars(source_clauses[s]) == set()]
            if len(c['vars'])==1 and srcs:
                src = srcs[0]
                if source_meta[src]['type'] == 'database':
                    if source_meta[src]['source'].supports(source_clauses[src],get_ast(c['expr'])):
                        source_clauses[src].append(c)
                    else:
                        rest_clauses.append(c)
                else:
                    source_clauses[src].append(c)
            else:
                rest_clauses.append(c)
            
        # When we see a group-by, we mark all the variables not in the group-by key as list
        # variables. This knowledge will help to figure out whether we can send further clauses
        # that depend on these variables to the source.
        elif c['name'] == 'groupby':
            list_vars = current_vars - {x[1] for x in c['groupby_list']}
            rest_clauses.append(c)
            groupbys_seen = True
            
        # The where clause is especially important for us, since it includes conditions that
        # we can push to the sources, including join conditions, and also various hints.
        elif c['name'] == 'where':
            expr = get_ast(c['expr'])
            exprs = [expr]
            if isinstance(expr,boolOp_e) and expr.op == 'and':
                exprs = expr.args
            remaining_exprs = []
            for e in exprs:
                # If this is a hint, record the hint
                if isinstance(e,call_e) and isinstance(e.func,name_e) and e.func.id=='hint':
                    hints.append(e)
                else: 
                    # If the entire expression can be pushed to a specific source, do so
                    srcs = [s for s in range(source_id) if get_all_vars(e) - clause_vars(source_clauses[s]) == set()]
                    if srcs:
                        src = srcs[0]
                        if source_meta[src]['type'] == 'database':
                            if source_meta[src]['source'].supports(source_clauses[src],e):
                                source_clauses[src].append({'name':'where', 'expr':print_ast(e)})
                            else:
                                remaining_exprs.append(e)
                        else:
                            source_clauses[src].append({'name':'where', 'expr':print_ast(e)})
                    
                    # If this looks like a join condition, we'll record it separately. However, we need to
		    # to check that its a real join condition, i.e. doesn't include a refence from the
                    # local variables
                    elif is_join_cond(e) and not get_all_vars(e).intersection(visible_vars):
                        join_conds.append(e)
                    else:
                        remaining_exprs.append(e)
            if remaining_exprs:
                e = remaining_exprs[0] if len(remaining_exprs)==1 else boolOp_e('and',remaining_exprs)
                rest_clauses.append( {'name':'where', 'expr':print_ast(e)})
        else:
            rest_clauses.append(c)
            
    join = None
    
    # Create a tree of joins if there is more than one source
    if len(source_meta)>1:
        last_join = {'name':'join',
                     'left':source_clauses[source_id-2],
                     'right':source_clauses[source_id-1],
                     'left_conds':[],
                     'right_conds':[]}
        for s in range(source_id-3,-1,-1):
            last_join = {'name':'join',
                         'left':source_clauses[s], 
                         'right':last_join,
                         'left_conds':[],
                         'right_conds':[]}
        join = last_join
        
        # Push join condition to the deepest level
        for cond in join_conds:
            all_cond_vars = get_all_vars(cond)
            deepest_join = join
            while True:
                left_vars = clause_vars(ensure_list(deepest_join['left']))
                right_vars = clause_vars(ensure_list(deepest_join['right']))
                if all_cond_vars.intersection(left_vars) == all_cond_vars:
                    deepest_join == deepest_join['left']
                elif all_cond_vars.intersection(right_vars) == all_cond_vars:
                    deepest_join == deepest_join['right']
                else:
                    break

            left_cond_vars = clause_vars(ensure_list(deepest_join['left']))
            c1 = cond.left
            c2 = cond.comparators[0]

            if get_all_vars(c1).intersection(left_cond_vars):
                deepest_join['left_conds'].append(print_ast(c1))
                deepest_join['right_conds'].append(print_ast(c2))
            else:
                deepest_join['left_conds'].append(print_ast(c2))
                deepest_join['right_conds'].append(print_ast(c1))
        
        # Push in join hints to the level with join conditions
        for hint in hints:
            join_type = hint.args[0].value
            left_var = hint.args[1].value
            right_var = hint.args[2].value
            
            for j in visit_joins(join):
                l_vars = clause_vars(ensure_list(j['left']))
                r_vars = clause_vars(ensure_list(j['right']))
                if left_var in l_vars and right_var in r_vars:
                    j['hint'] = {'join_type':join_type, 'dir':'right'}
                elif left_var in r_vars and right_var in l_vars:
                    j['hint'] = {'join_type':join_type, 'dir':'left'}
        
    # Iterate over the database sources and translate the queries into
    # database-specific dialects
    for db in databases:
        src_id = databases[db]
        src_clauses = source_clauses[src_id]
        src_meta = source_meta[src_id]
        
        
        # Compute the project list
        live_var_list = clause_live_vars(rest_clauses)
        if join:
            live_var_list = live_var_list.union(clause_live_vars([join]))
            
        vars = clause_vars(src_clauses)
        project_list = live_var_list.intersection(vars)

        
        wrapped = src_meta['source'].wrap(src_clauses,project_list)
        src_clauses.clear()
        src_clauses.append( wrapped )
        
    if join:
        return [join] + rest_clauses
    else:
        return source_clauses[0] + rest_clauses


