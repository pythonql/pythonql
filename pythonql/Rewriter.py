from pythonql.Ast import *
from pythonql.algebra.operators import *
from pythonql.algebra.operator import OpTreeNode, plan_from_list
from pythonql.sources.source import RDBMSTable
import re

# Create a synthetic variable for outerjoin
cvar_count = 0
def make_cvar():
    global cvar_count
    retval = "synthetic_count_"
    retval += repr(cvar_count)
    cvar_count += 1
    return retval
   
# Check if an expression looks like a join condition
# This just checks the syntax of an expression

def is_join_cond(e):
    if isinstance(e,compare_e):
        if len(e.ops)==1 and e.ops[0] == '==':
            if all([type(x) in [name_e,attribute_e] for x in  visit(e.left) ]):
                if all([type(x) in [name_e,attribute_e] for x in  visit(e.comparators[0]) ]):
                    return True
    return False

# Extract sources from a potential outerjoin expression (nested query)
def outerjoin_sources(expr,visible_vars):
    clauses = eval(print_ast(expr.args[0]))
    sources = []
    for c in [x for x in clauses if type(x)==For]:
        e = get_ast(c.expr)
        if (isinstance(e,name_e) and isinstance(visible_vars.get(e.id), RDBMSTable)):
            sources.append( visible_vars.get(e.id) )
        else:
            sources.append( e )
    return sources

# Is this nested query and outerjoin that we want to expand?
# We only support outerjoins via 'outer' syntax
# Had an idea to also support list construction via let clause as
# outerjoins, but will leave that for a new clean version of PythonQL

def good_outerjoin(e,defined_vars,clause_type):
    nested_expr = None

    if clause_type == 'for':
        if not ( isinstance(e,call_e) and isinstance(e.func, name_e) and e.func.id == 'outer' and
                 isinstance(e.args[0],call_e) and isinstance(e.args[0].func, name_e) and e.args[0].func.id == 'PyQuery' ):
           return False
        nested_expr = e.args[0].args[0]

    else:
        return False
    nested_clauses = eval(print_ast(nested_expr))
    schema = {}
    select_schema = []

    for (i,op) in enumerate(nested_clauses):

        # If this is a Where clause that has references to variables
        # defined outside of the outerjoin subquery, it should be the
        # last clause in the query before select. This is a rather restrictive
        # condition, but otherwise pretty in-depth analysis needs to be done.

        if type(op) == Where and op.used_vars().intersection( defined_vars ) != set():
            if not( i+1 == len(nested_clauses)-1 and type(nested_clauses[i+1]) == Select ):
                return False

        # We don't want any clauses except for Where to use variables
        # defined outside of the outerjoin

        else:
            if op.used_vars().intersection( defined_vars ) != set():
                return False

        # A common problem in the outerjoin case is when the where clause references
        # tuple constituents that are not defined in the select clause. Of course, we
        # perform a very simple analysis and err on the side of not processing such
        # cases as outerjoins. So let's record all variables in for and let clauses
        # and then check that the where clause only explicitly references variables
        # that have been defined

        if type(op) == For and len(op.vars)==1:
            schema[ op.vars[0] ] = 'tuple'

        if type(op) == Let and len(op.vars)==1:
            schema[ op.vars[0] ] = 'value'

        # To build the schema of the result of select operator, we consider only two
        # cases:
        # 1. Select is a tuple, in such case we decompose it an map each alias to an appropriate
        #    entry in the schema, assembled so far
        # 2. Select is a single name reference, in which case we map to the appropriate entry
        #    in the schema assembled so far

        if type(op) == Select:
            e = get_ast(op.expr)

            # Dig into the tuple
            # FIXME: need to make most of this a method of AST and also get this out of wrapper code

            if isinstance(e,call_e) and isinstance(e.func,name_e) and e.func.id == 'make_pql_tuple':
                for t in e.args[0].values:
                    te = t.values[0].value
                    te_repr = te.replace(" ","")
                    if re.match("\w+\.",te_repr):
                        te_repr = "".join( te_repr.split(".")[1:] )
                    ae = t.values[1]
                    alias = te_repr if isinstance(ae,none_literal) else ae.value

                    te_expr = get_ast(te)
                    if isinstance(te_expr,name_e):
                        var_value = te_expr.id if te_expr.id in schema else None
                        select_schema.append( {'alias':alias, 'type':'value', 'value':var_value} )

                    elif isinstance(te_expr,attribute_e) and isinstance(te_expr.value,name_e) and isinstance(te_expr.attribute,name_e):
                        select_schema.append( {'alias':alias, 'type':'path', 'attr':te_expr.value.id, 'value':te_expr.attribute.id} )

            elif isinstance(e,name_e):
                select_schema.append( {'alias':None, 'type':'value', 'value':e.id if e.id in schema else None} )

            elif isinstance(e,attribute_e) and isinstance(e.value,name_e) and isinstance(e.attribute,name_e):
                select_schema.append( {'alias':None, 'type':'path', 'attr':e.value.id, 'value':e.attribute.id} )


    # We have built up the schemas, now check that all where clauses behave well with respect
    # to the select schema
                
    for w_clause in [op for op in nested_clauses if type(op)==Where]:
        e = get_ast(w_clause.expr)
        v_map = get_all_var_mappings(e)

        for v in v_map:
            if v not in defined_vars:
                # If we are dealing with a path expression:
                #   If we have a tuple in the select schema, then we're fine
                #   Else, if we have a path expression whose alias match, we're also fine
                #   Otherwise, we can't support such query

                if v_map[v]:
                    if v not in [x['value'] for x in select_schema if x['type'] == 'value']:
                        if v_map[v] not in [x['alias'] for x in select_schema if x['type'] == 'path']:
                            return False

                # Otherwise, we are matching on a single value we return
                else:
                    if v not in [x['value'] for x in select_schema if x['type'] == 'value']:
                        return False

    return True

# Extract the where and the rest part from outerjoin clauses
def extract_where(clauses,visible_vars):
    hints = []
    rest_exprs = []
    join_expr = None
    remaining_exprs = []
    remaining_clauses = []
    for c in clauses:
        if type(c) == Where:
            expr = get_ast(c.expr)
            exprs = [expr]
            if isinstance(expr,boolOp_e) and expr.op == 'and':
                exprs = expr.args
            for e in exprs:
                # If this is a hint, record the hint
                if isinstance(e,call_e) and isinstance(e.func,name_e) and e.func.id=='hint':
                    hints.append(e)
                else:
                    remaining_exprs.append(e)
        else:
            remaining_clauses.append(c)

    if remaining_exprs:
       join_expr = remaining_exprs[0] if len(remaining_exprs)==1 else boolOp_e('and',remaining_exprs)

    return (remaining_clauses,hints,join_expr)

# Main rewriter routine, pushed as much work as possible into the database sources,
# creates joins and join condition and handles query hints.
#
# The rewriter operates on a chain of operators, but the result is an operator tree

def rewrite(plan,visible_vars):
    source_id = 0
    databases = {}
    source_meta = {}
    source_plans = {}
    rest_clauses = []
    
    # Have we seen any group-bys in the plan?
    # In this case we can't push fors or lets any longer
    groupbys_seen = False
    
    # All variables defined by this plan
    defined_vars = set()
    
    # Live variables - all variables that are needed above in the plan
    live_vars = set()
    
    # Variables that were turned into a list by group-by
    list_vars = set()
    
    hints = []
    join_conds = []
    
    for subplan in plan.as_list_reversed():

        # Current operator
        op = subplan.op
 
        # Compute all defined vars
        defined_vars = subplan.defined_vars()

        # Current variables are the union of variables visible outside of the
        # scope of this plan and variables defined by this subplan
        current_vars = defined_vars.union( set(visible_vars) )
        
        # If we see a for clause, we try to find its source, if there's none,
        # we'll create a new source. We'll then push the for clause into the
        # source plans. This can be done for the clauses that don't depend upon
        # any variables.
        if type(op) == For and len(op.vars)==1 and not groupbys_seen:
            source = get_ast(op.expr)
            if (isinstance(source,name_e) 
                    and isinstance(visible_vars.get(source.id), RDBMSTable) ):
                database = visible_vars[source.id]
                meta = {    "type":"database", 
                            "database":database.engine,
                            "source":database
                }
                op.database = meta

                url = database.engine.url
                if not url in databases:
                    source_meta[source_id] = meta
                    databases[url] = source_id
                    source_plans[source_id] = OpTreeNode(op,None)
                    source_id += 1
                else:
                    source_plans[databases[url]] = OpTreeNode(op,source_plans[databases[url]])
               
            # Check if this is an iterator over an outerjoin
            elif good_outerjoin(source,defined_vars,'for'):
                srcs = outerjoin_sources(source.args[0],visible_vars)

                # If we can push this thing into an existing wrapper, do so
                pushed = False
                if all([isinstance(s, RDBMSTable) for s in srcs]):
                    urls = {s.engine.url for s in srcs}
                    if len(urls) == 1 and list(urls)[0] in databases:
                        url = list(urls)[0]
                        sid = databases[url]
                        if source_meta[sid]['source'].supports(source_plans[sid],get_ast(op.expr),visible_vars):
                            source_plans[sid] = OpTreeNode(op,source_plans[sid])
                            pushed = True

                # If we didn't manage to push the outerjoin into the wrapper,
                # add it as another outerjoin source to the plan

                if not pushed:
                    #clauses = eval(print_ast(source.args[0].args[0]))
                    #(clauses,hints,on) = extract_where(clauses,visible_vars)
                    #clauses.reverse()

                    # Create a "broken" outerjoin without a left child, we'll
                    # fix this up when we introduce joins into the plan

                    #op = LeftOuterJoin(on=on, hints=hints)
                    #source_meta[source_id] = {"type":"for_outerjoin",
                    #                          "clauses":clauses, 
                    #                          "hints":hints,
                    #                          "on":on }
                    #source_plans[source_id] = OpTreeNode(op,None,plan_from_list(clauses))
                    #source_id += 1
                    rest_clauses.append(op)
            
            # Check whether the variables used in the operator don't occur in the subplan
            elif op.used_vars().intersection(defined_vars) == set():
                source_meta[source_id] = {"type":"expr", "expr":op.expr}
                source_plans[source_id] = OpTreeNode(op)
                source_id += 1
            else:
                rest_clauses.append(op)
        
        # We can push let clause into one of the sources, if that can't happen, we'll create
        # a new source for it. It can be pushed into an existing source only if it only depends
        # upon the variables in only the source or has no dependencies. 

        elif type(op) == Let and not groupbys_seen:
            expr = get_ast(op.expr)

            # At some point it will be nice to translate a let clause into an outerjoin
            # if it looks like an outerjoin

            if (isinstance(expr,call_e) and isinstance(expr.func,name_e) and expr.func.id == 'PyQuery'):
                if good_outerjoin(expr,defined_vars,'let'):
                    clauses = eval(print_ast(expr.args[0]))
                    (clauses,hints,on) = extract_where(clauses,visible_vars)
                    clauses.reverse()

                    # Create a "broken" outerjoin without a left child, we'll
                    # fix this up when we introduce joins into the plan
                    op = LeftOuterJoin(on=on, hints=hints)
                    source_meta[source_id] = {"type":"let_outerjoin",
                                              "clauses":clauses,
                                              "hints":hints,
                                              "on":on}
                    source_plans[source_id] = OpTreeNode(op, None, plan_from_list(clauses))
                    source_id += 1
                else:
                    rest_clauses.append(op)
            else:

                let_vars = get_all_vars(expr)
                srcs = [s for s in range(source_id) if let_vars - source_plans[s].defined_vars() == set()]
                if len(op.vars)==1 and srcs:
                   src = srcs[0]
                   if source_meta[src]['type'] == 'database':
                       if source_meta[src]['source'].supports(source_plans[src],get_ast(op.expr),visible_vars):
                           source_plans[src] = OpTreeNode(op, source_plans[src])
                       else:
                           rest_clauses.append(op)
                   else:
                       source_plans[src] = OpTreeNode(op,source_plans[src])
                else:
                    rest_clauses.append(op)
            
        # When we see a group-by, we mark all the variables not in the group-by key as list
        # variables. This knowledge will help to figure out whether we can send further clauses
        # that depend on these variables to the source.
        elif type(op) == GroupBy:
            list_vars = current_vars - {x[1] for x in op.groupby_list}
            rest_clauses.append(op)
            groupbys_seen = True
            
        # The where clause is especially important for us, since it includes conditions that
        # we can push to the sources, including join conditions, and also various hints.
        elif type(op) == Where:
            expr = get_ast(op.expr)
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
                    srcs = [s for s in range(source_id) if get_all_vars(e) - source_plans[s].defined_vars() == set()]
                    if srcs:
                        src = srcs[0]
                        if source_meta[src]['type'] == 'database':
                            if source_meta[src]['source'].supports(source_plans[src],e,visible_vars):
                                source_plans[src] = OpTreeNode(Where(print_ast(e)),source_plans[src])
                            else:
                                remaining_exprs.append(e)
                        else:
                            source_plans[src] = OpTreeNode(Where(print_ast(e)), source_plans[src])
                    
                    # If this looks like a join condition, we'll record it separately. However, we need to
		    # to check that its a real join condition, i.e. doesn't include a refence from the
                    # local variables
                    elif is_join_cond(e) and not get_all_vars(e).intersection(visible_vars):
                        join_conds.append(e)
                    else:
                        remaining_exprs.append(e)
            if remaining_exprs:
                e = remaining_exprs[0] if len(remaining_exprs)==1 else boolOp_e('and',remaining_exprs)
                rest_clauses.append( Where(print_ast(e)) )
        else:
            rest_clauses.append(op)
            
    join = None
    
    # Create a tree of joins if there is more than one source
    if source_id>1:
        last_join = OpTreeNode( Join(), source_plans[0],source_plans[1] )

        if type(source_plans[1].op) == LeftOuterJoin:
            oj_tree = source_plans[1]
            last_join = oj_tree
            oj_tree.left_child = source_plans[0]

            if source_meta[1]['type'] == 'let_outerjoin':
                all_left_vars = oj_tree.left_child.defined_vars()
                new_counter_var = make_cvar()
                new_child = OpTreeNode( Count(new_counter_var), oj_tree.left_child )
                oj_tree.left_child = new_child

                new_last_join = OpTreeNode( MakeList(new_counter_var, all_left_vars), last_join )
                last_join = new_last_join

        for s in range(2,source_id-3):
            if type(source_plans[s].op) == LeftOuterJoin:
                oj_tree = source_plans[s]
                last_join = oj_tree
                oj_tree.left_child = last_join

                if source_meta[s]['type'] == 'let_outerjoin':
                    all_left_vars = oj_tree.left_child.defined_vars()
                    new_counter_var = make_cvar()
                    new_child = OpTreeNode( Count(new_counter_var), oj_tree.left_child )
                    oj_tree.left_child = new_child

                    new_last_join = OpTreeNode( MakeList(new_counter_var, all_left_vars ), last_join)
                    last_join = new_last_join
            else:
                last_join = OpTreeNode( Join(), source_plans[s], last_join )

        
        def find_next_join(tree):
            if isinstance(tree.op, Join) or isinstance(tree.op, LeftOuterJoin):
                return tree
            else:
                return find_next_join(tree.left_child)

        join = find_next_join(last_join)

        # Push join condition to the deepest level
        for cond in join_conds:
            all_cond_vars = get_all_vars(cond)
            deepest_join = join
            while True:
                left_vars = deepest_join.left_child.defined_vars()
                right_vars = deepest_join.right_child.defined_vars()
                if all_cond_vars.intersection(left_vars) == all_cond_vars:
                    deepest_join == find_next_join(deepest_join.left_child)
                elif all_cond_vars.intersection(right_vars) == all_cond_vars:
                    deepest_join == find_next_join(deepest_join.right_child)
                else:
                    break

            left_child_vars = deepest_join.left_child.defined_vars()
            c1 = cond.left
            c2 = cond.comparators[0]

            if get_all_vars(c1).intersection(left_child_vars):
                deepest_join.op.left_conds.append(print_ast(c1))
                deepest_join.op.right_conds.append(print_ast(c2))
            else:
                deepest_join.op.left_conds.append(print_ast(c2))
                deepest_join.op.right_conds.append(print_ast(c1))
        
        # Push in join hints to the level with join conditions
        for hint in hints:
            join_type = hint.args[0].value
            left_var = hint.args[1].value
            right_var = hint.args[2].value
            
            for j in [x for x in join.visit() if type(x)==Join]:
                l_vars = j.left_child.defined_vars()
                r_vars = j.right_child.defined_vars()
                if left_var in l_vars and right_var in r_vars:
                    j.hint = {'join_type':join_type, 'dir':'right'}
                elif left_var in r_vars and right_var in l_vars:
                    j.hint = {'join_type':join_type, 'dir':'left'}
        
    # Build the final plan
    res = None

    if join:
        res = join

    else:
        res = source_plans[0] if source_plans else None

    for c in rest_clauses:
        res = OpTreeNode(c, res)

    res.compute_parents()

    # Iterate over the database sources and translate the queries into
    # database-specific dialects
    for db in databases:
        src_id = databases[db]
        subplan = source_plans[src_id]
        src_meta = source_meta[src_id]
        
        # Compute the project list
        used_var_list = subplan.used_vars_above()
        vars = subplan.defined_vars()
        project_list = used_var_list.intersection(vars)
        
        wrapped = src_meta['source'].wrap(subplan,project_list,visible_vars)
        subplan.replace( OpTreeNode(wrapped) )

    return res

