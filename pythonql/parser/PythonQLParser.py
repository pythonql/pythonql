import ply.yacc as yacc
from pythonql.parser.PythonQLLexer import Lexer

# This function prints out propertly indented program
# based only on the leaf tokens

def print_program(terms):
  indent_stack = [""]
  buffer = ""

  for t in terms:
    if t.type == 'NEWLINE':
      buffer += "\n"
      buffer += indent_stack[-1]
    elif t.type == 'INDENT':
      if len(indent_stack[-1]):
        buffer = buffer[0:-len(indent_stack[-1])]
      indent_stack.append( t.value )
      buffer += t.value
    elif t.type == 'DEDENT':
      buffer = buffer[0:-len(indent_stack[-1])]
      indent_stack.pop()
      buffer += indent_stack[-1]
    else:
      buffer += t.value + " "

  return buffer
    
# This is a class for a non-terminal node in the
# AST of the PythonQL grammar

class Node:
  def __init__(self,label,children):
    self.label = label
    self.children = children

  def __repr__(self):
    terms = self.terms()
    return " ".join([x[1] for x in terms])

  def terms(self):
    res = []
    for ch in self.children:
      if isinstance(ch,Node):
        res += ch.terms()
      else:
        res += [ ch ]
    return res

  def all_nodes(self):
    res = []
    for ch in self.children:
      if isinstance(ch,Node):
        res += [ ch ]
        res += ch.all_nodes()
    return res

  def get_child(self,label):
    matches = [n for n in self.all_nodes() if n.label==label]
    if len(matches) != 1:
      raise Exception("No matches or more than one match in get_child('%s')" % label)
    return matches[0]
    
  def get_child_opt(self,label):
    matches = [n for n in self.all_nodes() if n.label==label]
    if len(matches) > 1:
      raise Exception("More than one match in get_child_opt('%s')" % label)
    return matches[0] if matches else None

  def get_children(self,label):
    matches = [n for n in self.all_nodes() if n.label==label]
    return matches

# Creates a node with a given name and children from
# the production

def make_node(node_name, p):
  return Node(node_name, p[1:])

# Create a list node by collapsing all lists inside the
# production into a single list

def make_list(list_name, p):
  list_elements = []
  for x in p[1:]:
    if isinstance(x,Node) and (x.label.endswith("_list") 
       or x.label.endswith("_list_opt")):
      list_elements += x.children
    else:
      list_elements.append( x )
  return Node(list_name, list_elements)

# Parser class

class Parser:
  def __init__(self,lexer=Lexer):
    self.lex = Lexer()
    self.lex.build()
    self.tokens = self.lex.tokens
    self.parser = yacc.yacc(module=self,start='file_input',tabmodule='pythonql.parser.parsertab',debug=True)

  def parse(self,text):
    return self.parser.parse(text)

  # Precedence rules
  precedence = (
     ('left', 'OR'),
     ('left', 'AND'),
     ('right', 'NOT'),
     ('left', '<','>','EQUALS','GT_EQ','LT_EQ','NOT_EQ_1','NOT_EQ_2','IN','IS'),
     ('left', '|'),
     ('left', '^'),
     ('left', '&'),
     ('left', 'LEFT_SHIFT'),
     ('left', 'RIGHT_SHIFT'),
     ('left', '+','-'),
     ('left', '*','/','%','IDIV'),
     ('left', '@'),
     ('right', 'UPLUS', 'UMINUS', 'UNOT'))

  def p_file_input(self,p):
    """file_input : stmt_or_newline_list"""
    p[0] = make_node('file_input', p)

  def p_stmt_or_newline_list(self,p):
    """stmt_or_newline_list : NEWLINE
                            | stmt
                            | stmt_or_newline_list NEWLINE
                            | stmt_or_newline_list stmt """
    p[0] = make_list('stmt_or_newline_list', p)

  def p_decorator(self,p):
    """decorator : '@' dotted_name args_opt NEWLINE"""
    p[0] = make_node('decorator', p)

  def p_dotted_name(self,p):
    """dotted_name : NAME
                   | dotted_name '.' NAME"""
    p[0] = make_node('dotted_name', p)

  def p_args_opt(self,p):
    """args_opt : '(' arg_list ')'
                | """
    p[0] = make_node('args_opt', p)

  def p_decorator_list(self,p):
    """decorator_list : decorator_list decorator
                      | decorator"""
    p[0] = make_list('decorator_list',p)

  def p_decorated(self,p):
    """decorated : decorator_list funcdef
                 | decorator_list classdef"""
    p[0] = make_node('decorated', p)

  def p_funcdef(self,p):
    """funcdef : DEF NAME parameters signature_opt ':' suite"""
    p[0] = make_node('funcdef', p)

  def p_signature_opt(self,p):
    """signature_opt : ARROW test 
                     | """
    p[0] = make_node('signature_opt', p)

  def p_parameters(self,p):
    """parameters : '(' typedargs_list_opt ')'"""
    p[0] = make_node('parameters',p)

  def p_typedargs_list_opt(self,p):
    """typedargs_list_opt : typedargs_list
                         | """
    p[0] = make_list('typedargs_list_opt', p)

  def p_typedargs_list(self,p):
    """typedargs_list : normal_args_list 
                      | normal_args_list ',' star_args_list
                      | normal_args_list ',' star_args_list ',' double_star_arg
                      | normal_args_list ',' double_star_arg
                      | star_args_list ',' double_star_arg
                      | double_star_arg"""
    p[0] = make_list('typeargs_list', p)

  def p_normal_args_list(self,p):
    """normal_args_list : normal_args_list ',' normal_arg
                        | normal_arg"""
    p[0] = make_list('normal_args_list', p)

  def p_normal_arg(self,p):
    """normal_arg : tpdef
                  | tpdef '=' test"""
    p[0] = make_node('normal_arg', p)

  def p_star_args_list(self,p):
    """star_args_list : star_tpdef
                      | star_tpdef ',' normal_args_list
                      | star_tpdef ',' double_star_arg
                      | star_tpdef ',' normal_args_list ',' double_star_arg"""
    p[0] = make_list('star_args_list', p)

  def p_double_star_arg(self,p):
    """double_star_arg : POWER tpdef"""
    p[0] = make_node('double_star_arg', p)

  def p_tpdef(self,p):
    """tpdef : NAME
             | NAME ':' test"""
    p[0] = make_node('tpdef', p)

  def p_star_tpdef(self,p):
    """star_tpdef : '*'
                  | '*' tpdef"""
    p[0] = make_node('star_tpdef', p)

  def p_stmt(self,p):
    """stmt : simple_stmt
            | compound_stmt"""
    p[0] = make_node('stmt', p)

  def p_simple_stmt(self,p):
    """simple_stmt : small_stmt_list ';' NEWLINE
                   | small_stmt_list NEWLINE"""
    p[0] = make_node('simple_stmt', p)

  def p_small_stmt_list(self, p):
    """small_stmt_list : small_stmt
                       | small_stmt_list ';' small_stmt"""
    p[0] = make_list('small_stmt_list', p)

  def p_small_stmt(self, p):
    """small_stmt : expr_stmt
                  | del_stmt
                  | pass_stmt
                  | flow_stmt
                  | import_stmt
                  | global_stmt
                  | non_local_stmt
                  | assert_stmt"""
    p[0] = make_node('small_stmt', p)

  def p_expr_stmt(self, p):
    """expr_stmt : testlist_star_expr augassign yield_expr
                | testlist_star_expr augassign test_list_comma_opt
                | testlist_star_expr assign_list"""
    p[0] = make_node('expr_stmt', p)

  def p_testlist_star_expr(self,p):
    """testlist_star_expr : test comma_opt
                          | star_expr comma_opt
                          | testlist_star_expr ',' test comma_opt
                          | testlist_star_expr ',' star_expr comma_opt"""
    p[0] = make_node('testlist_star_expr', p)

  def p_comma_opt(self, p):
    """comma_opt : ','
                 | """
    p[0] = make_node('comma_opt',p)

  def p_augassign(self, p):
    """augassign : ADD_ASSIGN
                 | SUB_ASSIGN
                 | MULT_ASSIGN
                 | AT_ASSIGN
                 | AND_ASSIGN
                 | OR_ASSIGN
                 | XOR_ASSIGN
                 | LEFT_SHIFT_ASSIGN
                 | RIGHT_SHIFT_ASSIGN
                 | POWER_ASSIGN
                 | DIV_ASSIGN
                 | MOD_ASSIGN
                 | IDIV_ASSIGN"""
    p[0] = make_node('augassign', p)

  def p_assign_list(self, p):
    """assign_list : '=' yield_expr
                   | '=' testlist_star_expr
                   | assign_list '=' yield_expr
                   | assign_list '=' testlist_star_expr
                   | """
    p[0] = make_node('assign_list', p)

  def p_del_stmt(self, p):
    """del_stmt : DEL expr_list"""
    p[0] = make_node('del_stmt', p)

  def p_pass_stmt(self, p):
    """pass_stmt : PASS"""
    p[0] = make_node('pass_stmt', p)

  def p_flow_stmt(self, p):
    """flow_stmt : break_stmt
                 | continue_stmt
                 | return_stmt
                 | raise_stmt
                 | yield_stmt"""
    p[0] = make_node('flow_stmt', p)

  def p_break_stmt(self, p):
    """break_stmt : BREAK"""
    p[0] = make_node('break_stmt', p)

  def p_continue_stmt(self, p):
    """continue_stmt : CONTINUE"""
    p[0] = make_node('continue_stmt', p)

  def p_return_stmt(self, p):
    """return_stmt : RETURN test_list_comma_opt
                   | RETURN"""
    p[0] = make_node('return_stmt', p)

  def p_yield_stmt(self, p):
    """yield_stmt : yield_expr"""
    p[0] = make_node('yield_stmt', p)

  def p_raise_stmt(self, p):
    """raise_stmt : RAISE
                  | RAISE test
                  | RAISE test FROM test"""
    p[0] = make_node('raise_stmt', p)

  def p_import_stmt(self, p):
    """import_stmt : import_name
                   | import_from"""
    p[0] = make_node('import_stmt', p)

  def p_import_name(self, p):
    """import_name : IMPORT dotted_as_names"""
    p[0] = make_node('import_name', p)

  def p_import_from(self, p):
    """import_from : FROM dots_list_opt dotted_name dots_list_opt IMPORT '*'
                   | FROM dots_list_opt dotted_name dots_list_opt IMPORT '(' import_as_names comma_opt ')'
                   | FROM dots_list_opt dotted_name dots_list_opt IMPORT import_as_names comma_opt"""
    p[0] = make_node('import_from', p)

  def p_dots_list_opt(self,p):
    """dots_list_opt : dots_list
                     | """
    p[0] = make_list('dots_list_opt', p)

  def p_dots_list(self,p):
    """dots_list : '.'
                 | ELLIPSIS
                 | dots_list '.'
                 | dots_list ELLIPSIS"""
    p[0] = make_list('dots_list', p)

  def p_import_as_name(self, p):
    """import_as_name : NAME
                      | NAME AS NAME"""
    p[0] = make_node('import_as_name', p)

  def p_dotted_as_names(self, p):
    """dotted_as_names : dotted_as_name
                       | dotted_as_names ',' dotted_as_name"""
    p[0] = make_node('dotted_as_name', p)

  def p_dotted_as_name(self, p):
    """dotted_as_name : dotted_name
                      | dotted_name AS NAME"""
    p[0] = make_node('dotted_as_name', p)

  def p_import_as_names(self, p):
    """import_as_names : import_as_name
                       | import_as_names ',' import_as_name"""
    p[0] = make_node('import_as_names', p)

  def p_global_stmt(self, p):
    """global_stmt : GLOBAL name_list"""
    p[0] = make_node('global_stmt', p)

  def p_name_list(self, p):
    """name_list : NAME
                 | name_list ',' NAME"""
    p[0] = make_list('name_list', p)

  def p_non_local_stmt(self, p):
    """non_local_stmt : NONLOCAL name_list"""
    p[0] = make_node('non_local_stmt', p)

  def p_assert_stmt(self, p):
    """assert_stmt : ASSERT test
                   | ASSERT test ',' test"""
    p[0] = make_node('assert_stmt', p)

  def p_compound_stmt(self, p):
    """compound_stmt : if_stmt
                     | while_stmt
                     | for_stmt
                     | try_stmt
                     | with_stmt
                     | funcdef
                     | classdef
                     | decorated"""
    p[0] = make_node('compound_stmt', p)

  def p_if_stmt(self, p):
    """if_stmt : IF test ':' suite elif_list else_opt"""
    p[0] = make_node('if_stmt', p)

  def p_elif_list(self, p):
    """elif_list : elif_list ELIF test ':' suite
                 | """
    p[0] = make_node('elif_list', p)

  def p_else_opt(self, p):
    """else_opt : ELSE ':' suite
                | """
    p[0] = make_node('else_opt', p)

  def p_while_stmt(self, p):
    """while_stmt : WHILE test ':' suite else_opt"""
    p[0] = make_node('while_stmt', p)

  def p_for_stmt(self, p):
    """for_stmt : FOR expr_list IN test_list_comma_opt ':' suite else_opt"""
    p[0] = make_node('for_stmt', p)

  def p_try_stmt(self, p):
    """try_stmt : TRY ':' suite except_clauses_list else_opt finally_opt
                | TRY ':' suite finally"""
    p[0] = make_node('try_stmt', p)

  def p_except_clauses_list(self, p):
    """except_clauses_list : except_clauses_list except_clause ':' suite
                           | except_clause ':' suite"""
    p[0] = make_list('except_clauses_list', p)

  def p_finally_opt(self, p):
    """finally_opt : finally
                   | """
    p[0] = make_node('finally_opt', p)

  def p_finally(self, p):
    """finally : FINALLY ':' suite"""
    p[0] = make_node('finally', p)

  def p_with_stmt(self, p):
    """with_stmt : WITH with_item_list ':' suite"""
    p[0] = make_node('with_stmt', p)
 
  def p_with_item_list(self, p):
    """with_item_list : with_item_list with_item
                      | """
    p[0] = make_list('with_item_list', p)

  def p_with_item(self, p):
    """with_item : test
                 | test AS expr"""
    p[0] = make_node('with_item', p)

  def p_except_clause(self, p):
    """except_clause : EXCEPT test AS NAME
                     | EXCEPT test
                     | EXCEPT"""
    p[0] = make_node('except_clause', p)

  def p_suite(self, p):
    """suite : simple_stmt
             | NEWLINE INDENT stmt_list DEDENT"""
    p[0] = make_node('suite', p)

  def p_stmt_list(self, p):
    """stmt_list : stmt
                 | stmt_list stmt"""
    p[0] = make_list('stmt_list', p)

  def p_test(self, p):
    """test : try_catch_expr path_step"""
    p[0] = make_node('test', p)

  def p_path_step(self, p):
    """path_step : path_step CHILD_AXIS try_catch_expr
                      | path_step DESCENDENT_AXIS try_catch_expr
                      | """
    p[0] = make_node('path_step', p)

  def p_try_catch_expr(self, p):
    """try_catch_expr : old_test
                      | TRY old_test EXCEPT old_test"""
    p[0] = make_node('try_catch_expr', p)

  def p_old_test(self, p):
    """old_test : logical
                | logical IF logical ELSE old_test
                | lambdef"""
    p[0] = make_node('old_test', p)

  def p_test_nocond(self, p):
    """test_nocond : logical
                   | lambdef_nocond"""
    p[0] = make_node('test_nocond', p)

  def p_lambdef(self, p):
    """lambdef : LAMBDA varargs_list ':' test
               | LAMBDA ':' test"""
    p[0] = make_node('lambdef', p)

  def p_lambdef_nocond(self, p):
    """lambdef_nocond : LAMBDA varargs_list ':' test_nocond
                      | LAMBDA ':' test_nocond"""
    p[0] = make_node('lambdef_nocond', p)

  def p_varargs_list(self, p):
    """varargs_list : vfpdef_list comma_opt
                    | vfpdef_list ',' star_vfpdef vfpdef_rest
                    | vfpdef_list ',' power_vfpdef
                    | star_vfpdef vfpdef_rest
                    | power_vfpdef"""
    p[0] = make_node('varargs_list', p)

  def p_vfpdef_list(self, p):
    """vfpdef_list : NAME
                   | NAME '=' test
                   | vfpdef_list ',' NAME
                   | vfpdef_list ',' NAME '=' test"""
    p[0] = make_node('vfpdef_list', p)

  def p_star_vfpdef(self, p):
    """star_vfpdef : '*'
                   | '*' NAME"""
    p[0] = make_node('star_vfpdef', p)

  def p_vfpdef_rest(self, p):
    """vfpdef_rest : comma_vfpdef_list comma_power_vfpdef"""
    p[0] = make_node('vfpdef_rest', p)

  def p_comma_vfpdef_list(self, p):
    """comma_vfpdef_list : ',' NAME
                         | ',' NAME '=' test
                         | comma_vfpdef_list ',' NAME
                         | comma_vfpdef_list ',' NAME '=' test
                         | """
    p[0] = make_node('comma_vfpdef_list', p)

  def p_comma_power_vfpdef(self, p):
    """comma_power_vfpdef : ',' POWER NAME
                          | """
    p[0] = make_node('comma_power_vfpdef', p)

  def p_power_vfpdef(self, p):
    """power_vfpdef : POWER NAME"""
    p[0] = make_node('power_vfpdef', p)

  def p_logical(self, p):
    """logical : logical AND logical
               | logical OR logical
               | NOT logical
               | comparison"""
    p[0] = make_node('comparison', p)

  def p_comparison(self, p):
    """comparison : comparison comp_op comparison
                  | not_in_expr"""
    p[0] = make_node('comparison', p)

  def p_comp_op(self, p):
    """comp_op : '<'
               | '>'
               | EQUALS
               | GT_EQ
               | LT_EQ
               | NOT_EQ_1
               | NOT_EQ_2
               | IN
               | NOT IN
               | IS
               | IS NOT"""
    p[0] = make_node('comp_op', p)

  def p_not_in_expr(self, p):
    """not_in_expr : is_not_expr NOT IN not_in_expr
                   | is_not_expr"""
    p[0] = make_node('not_in_expr', p)

  def p_is_not_expr(self, p):
    """is_not_expr : star_expr IS NOT is_not_expr 
                   | star_expr"""
    p[0] = make_node('is_not_expr', p)

  def p_star_expr(self, p):
    """star_expr : '*' expr
                 | expr"""
    p[0] = make_node('star_expr', p)

  def p_expr(self, p):
    """expr : expr '|' expr
            | expr '^' expr
            | expr '&' expr
            | expr LEFT_SHIFT expr
            | expr RIGHT_SHIFT expr
            | expr '+' expr
            | expr '-' expr
            | expr '*' expr
            | expr '/' expr
            | expr '%' expr
            | expr IDIV expr
            | expr '@' expr
            | factor"""
    p[0] = make_node('expr', p)

  def p_factor(self, p):
    """factor : '+' expr %prec UPLUS
                | '-' expr %prec UMINUS
                | '~' expr %prec UNOT
                | power"""
    p[0] = make_node('factor', p)

  def p_power(self, p):
    """power : atom trailer_list_opt
             | atom trailer_list_opt POWER factor"""
    p[0] = make_node('power', p)

  def p_trailer_list_opt(self, p):
    """trailer_list_opt : trailer_list_opt trailer
                        | """
    p[0] = make_list('trailer_list_opt', p)

  def p_atom(self, p):
    """atom : NAME
            | number
            | string_list
            | ELLIPSIS
            | NONE
            | TRUE
            | FALSE
            | gen_query_expression
            | list_query_expression
            | set_query_expression"""
    p[0] = make_node('atom', p)

  def p_string_list(self, p):
    """string_list : string_list string
                   | string"""
    p[0] = make_list('string_list', p)

  def p_gen_query_expression(self, p):
    """gen_query_expression : '(' ')'
                           | '(' yield_expr ')'
                           | '(' testseq_query ')'""" 
    p[0] = make_node('gen_query_expression', p)

  def p_list_query_expression(self, p):
    """list_query_expression : '[' ']'
                             | '[' testlist_query ']'"""
    p[0] = make_node('list_query_expression', p)

  def p_set_query_expression(self, p):
    """set_query_expression : '{' '}'
                            | '{' dictorsetmaker '}'"""
    p[0] = make_node('set_query_expression', p)

  def p_query_expression(self, p):
    """query_expression : select_clause first_clause rest_clauses_list_opt"""
    p[0] = make_node('query_expression', p)

  def p_first_clause(self, p):
    """first_clause : for_clause
                    | let_clause 
                    | window_clause
                    | match_clause"""
    p[0] = make_node('first_clause', p)

  def p_rest_clauses_list_opt(self, p):
    """rest_clauses_list_opt : rest_clauses_list_opt query_clause
                             | """
    p[0] = make_list('rest_clauses_list_opt', p)

  def p_query_clause(self, p):
    """query_clause : for_clause
                    | let_clause
                    | window_clause
                    | match_clause
                    | group_by_clause
                    | where_clause
                    | order_by_clause
                    | count_clause"""
    p[0] = make_node('query_clause', p)

  def p_query_map_expression(self, p):
    """query_map_expression : map_select_clause first_clause rest_clauses_list_opt"""
    p[0] = make_node('query_map_expression', p)

  def p_select_clause(self, p):
    """select_clause : SELECT test
                     | test"""
    p[0] = make_node('select_clause', p)

  def p_map_select_clause(self, p):
    """map_select_clause : SELECT test ':' test
                         | test ':' test"""
    p[0] = make_node('map_select_clause', p)

  def p_for_clause(self, p):
    """for_clause : FOR for_clause_entry_list"""
    p[0] = make_node('for_clause', p)

  def p_for_clause_entry_list(self, p):
    """for_clause_entry_list : for_clause_entry
                             | for_clause_entry_list ',' for_clause_entry"""
    p[0] = make_list('for_clause_entry_list', p)

  def p_for_clause_entry(self, p):
    """for_clause_entry : expr_list IN logical"""
    p[0] = make_node('for_clause_entry', p)

  def p_let_clause(self, p):
    """let_clause : LET let_clause_entry_list"""
    p[0] = make_node('let_clause', p)

  def p_let_clause_entry_list(self, p):
    """let_clause_entry_list : let_clause_entry
                             | let_clause_entry_list ',' let_clause_entry"""
    p[0] = make_list('let_clause_entry_list', p)

  def p_let_clause_entry(self, p):
    """let_clause_entry : expr_list '=' test"""
    p[0] = make_node('let_clause_entry', p)

  def p_window_clause(self, p):
    """window_clause : tumbling_window
                     | sliding_window"""
    p[0] = make_node('window_clause', p)

  def p_tumbling_window(self, p):
    """tumbling_window : FOR TUMBLING WINDOW NAME IN test window_start_cond window_end_cond_opt"""
    p[0] = make_node('tumbling_window', p)

  def p_sliding_window(self, p):
    """sliding_window : FOR SLIDING WINDOW NAME IN test window_start_cond window_end_cond"""
    p[0] = make_node('sliding_window', p)

  def p_window_start_cond(self, p):
    """window_start_cond : START window_vars WHEN test"""
    p[0] = make_node('window_start_cond', p)

  def p_window_end_cond_opt(self, p):
    """window_end_cond_opt : window_end_cond
                           | """
    p[0] = make_node('window_end_cond_opt', p)

  def p_window_end_cond(self, p):
    """window_end_cond : ONLY END window_vars WHEN test
                       | END window_vars WHEN test"""
    p[0] = make_node('window_end_cond', p)

  def p_window_vars(self, p):
    """window_vars : current_item_opt positional_var_opt previous_var_opt following_var_opt"""
    p[0] = make_node('window_vars', p)

  def p_current_item_opt(self, p):
    """current_item_opt : NAME 
                        | """
    p[0] = make_node('current_item_opt', p)

  def p_positional_var_opt(self, p):
    """positional_var_opt : AT NAME
                          | """
    p[0] = make_node('positional_var_opt', p)

  def p_previous_var_opt(self, p):
    """previous_var_opt : PREVIOUS NAME
                        | """
    p[0] = make_node('previous_var_opt', p)

  def p_following_var_opt(self, p):
    """following_var_opt : FOLLOWING NAME
                         | """
    p[0] = make_node('following_var_opt', p)

  def p_match_clause(self,p):
    """match_clause : MATCH exact_or_filter_opt pattern_object IN test"""
    p[0] = make_node('match_clause', p)

  def p_exact_or_filter_opt(self,p):
    """exact_or_filter_opt : EXACT
                       | FILTER
                       | """
    p[0] = make_node('exact_or_filter_opt',p)

  def p_pattern_object(self,p):
    """pattern_object : '{' pattern_object_list '}' as_opt"""
    p[0] = make_node('pattern_object',p)

  def p_as_opt(self,p):
    """as_opt : AS NAME
              | """
    p[0] = make_node('as_opt',p)

  def p_pattern_object_list(self,p):
    """pattern_object_list : pattern_object_element
                           | pattern_object_list ',' pattern_object_element"""
    p[0] = make_list('pattern_object_list', p)

  def p_pattern_object_element(self,p):
    """pattern_object_element : STRING_LITERAL ':' STRING_LITERAL
                              | STRING_LITERAL ':' AS NAME WHERE test
                              | STRING_LITERAL ':' AS NAME
                              | STRING_LITERAL ':' WHERE test
                              | STRING_LITERAL ':' NAME
                              | STRING_LITERAL ':' pattern_object"""
    p[0] = make_node('pattern_object_element', p)

  def p_order_by_clause(self, p):
    """order_by_clause : ORDER BY order_list"""
    p[0] = make_node('order_by_clause', p)

  def p_order_list(self, p):
    """order_list : order_element
                  | order_list ',' order_element"""
    p[0] = make_list('order_list', p)

  def p_order_element(self, p):
    """order_element : test
                     | test ASC
                     | test DESC"""
    p[0] = make_node('order_element', p)

  def p_group_by_clause(self, p):
    """group_by_clause : GROUP BY group_by_var_list"""
    p[0] = make_node('group_by_clause', p)

  def p_group_by_var_list(self, p):
    """group_by_var_list : group_by_var
                         | group_by_var_list ',' group_by_var"""
    p[0] = make_list('group_by_var_list', p)

  def p_group_by_var(self, p):
    """group_by_var : old_test
                    | old_test AS NAME"""
    p[0] = make_node('group_by_var', p)

  def p_where_clause(self,p):
    """where_clause : WHERE test
                    | IF test"""
    p[0] = make_node('where_clause', p)

  def p_count_clause(self, p):
    """count_clause : COUNT NAME"""
    p[0] = make_node('count', p)

  def p_testseq_query(self, p):
    """testseq_query : test_as_list comma_opt
                     | query_expression"""
    p[0] = make_node('testseq_query', p)

  def p_test_as_list(self, p):
    """test_as_list : test_as
                    | test_as_list ',' test_as """
    p[0] = make_list('test_as_list', p)

  def p_test_as(self, p):
    """test_as : test
               | test AS NAME"""
    p[0] = make_node('test_as', p)

  def p_testlist_query(self, p):
    """testlist_query : test_list_comma_opt
                      | query_expression"""
    p[0] = make_node('testlist_query', p)

  def p_trailer(self, p):
    """trailer : '(' ')'
               | '(' arg_list ')'
               | '[' subscript_list ']'
               | '.' NAME"""
    p[0] = make_node('trailer', p)

  def p_subscript_list(self, p):
    """subscript_list : subscript
                      | subscript_list ',' subscript"""
    p[0] = make_list('subscript_list', p)

  def p_subscript(self, p):
    """subscript : test
                 | test_opt ':' test_opt sliceop"""
    p[0] = make_node('subscript', p)
 
  def p_test_opt(self, p):
    """test_opt : test
                | """
    p[0] = make_node('test_opt', p)

  def p_sliceop(self, p):
    """sliceop : ':' test
               | ':'
               | """
    p[0] = make_node('sliceop', p)

  def p_expr_list(self, p):
    """expr_list : star_expr 
                 | expr_list ',' star_expr"""
    p[0] = make_list('expr_list', p)

  def p_test_list(self, p):
    """test_list : test
                 | test_list ',' test"""
    p[0] = make_list('test_list', p)

  def p_test_list_comma_opt(self, p):
    """test_list_comma_opt : test_list comma_opt"""
    p[0] = make_list('test_list_comma_opt', p)

  def p_dictorsetmaker(self, p):
    """dictorsetmaker : test_map_list_comma_opt
                      | query_map_expression
                      | test_list_comma_opt
                      | query_expression"""
    p[0] = make_node('dictorsetmaker', p)

  def p_test_map_list_comma_opt(self, p):
    """test_map_list_comma_opt : test_map_list"""
    p[0] = make_list('test_map_list_comma_opt', p)

  def p_test_map_list(self, p):
    """test_map_list : test ':' test
                     | test_map_list ',' test ':' test"""
    p[0] = make_list('test_map_list', p)

  def p_classdef(self, p):
    """classdef : CLASS NAME '(' arg_list ')' ':' suite
                | CLASS NAME '(' ')' ':' suite
                | CLASS NAME ':' suite"""
    p[0] = make_node('classdef', p)

  def p_arg_list(self, p):
    """arg_list : argument_list_opt_comma argument comma_opt
                | argument_list_opt_comma '*' test ',' argument_list_opt
                | argument_list_opt_comma '*' test ',' argument_list_opt ',' POWER test
                | argument_list_opt_comma POWER test"""
    p[0] = make_list('arg_list', p)

  # An optional arg list with a comma at the end
  def p_argument_list_opt_comma(self, p):
    """argument_list_opt_comma : argument_list_opt_comma argument ','
                        | """
    p[0] = make_list('argument_list_opt_comma', p)

  def p_argument_list_opt(self, p):
    """argument_list_opt : argument_list
                    | """
    p[0] = make_list('argument_list_opt', p)

  def p_argument_list(self, p):
    """argument_list : argument
                     | argument_list ',' argument"""
    p[0] = make_list('argument_list', p)

  def p_argument(self, p):
    """argument : test
                | test comp_for
                | test '=' test"""
    p[0] = make_node('argument', p)

  def p_comp_iter(self, p):
    """comp_iter : comp_for
                 | comp_if"""
    p[0] = make_node('comp_iter', p)

  def p_comp_for(self, p):
    """comp_for : FOR expr_list IN logical comp_iter_opt"""
    p[0] = make_node('comp_for', p)
    
  def p_comp_if(self, p):
    """comp_if : IF test_nocond comp_iter_opt"""
    p[0] = make_node('comp_if', p)

  def p_comp_iter_opt(self, p):
    """comp_iter_opt : comp_iter
                     | """
    p[0] = make_node('comp_iter_opt', p)

  def p_yield_expr(self, p):
    """yield_expr : YIELD yield_arg
                  | YIELD"""
    p[0] = make_node('yield_expr', p)

  def p_yield_arg(self, p):
    """yield_arg : FROM test
                 | test_list_comma_opt"""
    p[0] = make_node('yield_arg', p)

  def p_string(self, p):
    """string : STRING_LITERAL
              | LONG_STRING_LITERAL"""
    p[0] = make_node('string', p)

  def p_number(self,p):
    """number : integer
              | FLOAT_NUMBER
              | IMAG_NUMBER"""
    p[0] = make_node('number', p)

  def p_integer(self, p):
    """integer : DECIMAL_INTEGER
               | OCT_INTEGER
               | HEX_INTEGER
               | BIN_INTEGER"""
    p[0] = make_node('integer', p)

  def p_error(self,p):
    raise Exception("Syntax error at line %d, column %d, token '%s'" % (p.lineno,p.value.column,p.value.value))

if __name__=='__main__':
  import sys
  source_file = open(sys.argv[1])
  p = Parser()
  str = "".join(source_file.readlines())
  print("Parsing:", repr(str))
  t = p.parse(str)
  print(print_program(t.terms()))
