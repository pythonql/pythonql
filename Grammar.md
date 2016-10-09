#PythonQL EBNF Grammar
This document describes the grammar that we want to implement in PythonQL

## Path expressions.
We start with path expressions, since they are a separate beast and will be
used not only in query context, but elsewhere in the PythonQL language.
They appear under general expression, so we will give the grammar starting
at `expr`. Btw. in the real grammar this production is called `test`, but
its confusing. Instead of `test` in EBNF we use `expr`, and instead of 
`old_test` (the production before we introduced path expressions) we use
`old_expr`.

```jflex
  expr := old_expr ( path_step )*;
  path_step := './' old_expr | './/' old_expr ;
```
`'./'` is a child path step. `.//` is a descendent path step. The expression 
at the end can be _ or should evaluate to a string.

## Try-except expression
Python has great exception handling and actually a lot of Python code heavily depends on it.
However, Python's exceptions are statements. Hence they cannot be used in path and query 
expressions. But they are incredibly useful there, so we introduced a simple for of try-except
expression.

```jflex
  try_except_expr := 'try'  expr  'except'  expr 
```  

## Tuple constructor
We need named tuples, but Python's namedtuple is not convinient enough to be useful, we really
need a very simple syntax to create them.

```jflex
  tuple_constructor := '(' tuple_element (',' tuple_element)* ','? ')'
  tuple_element := expr ('as' NAME)?
```

## Query Expressions
Our queries come from a superset of Python's comprehensions.

```jflex
query_expression := select 
                ( for | let ) 
                ( for | let | where | window | count | groupby | orderby )* ;

select := 'select' ? expr ;

for := 'for' NAME 'in' expr (',' NAME 'in' expr ) * ;

let := 'let' NAME '=' expr (',' NAME '=' expr ) *;

where := ('where'|'if') expr ;

count := 'count' NAME;

groupby := 'group' 'by' expr ('as' NAME)? (',' expr ('as' NAME)? ) * ;

orderby := 'order' 'by' expr ['asc' | 'desc'] (',' expr ['asc' | 'desc'] ) *;

window := 'for' ( tumbling_window | sliding_window ) ;

tubling_window := 'tumbling' 'window' NAME 'in' expr window_start_cond window_end_cond? ;

sliding_window := 'sliding' 'window' NAME 'in' expr window_start_cond window_end_cond ;

window_start_cond := 'start' window_vars 'when' expr ;

window_end_cond := 'only'? 'end' window_vars 'when' expr ;

window_vars := NAME? ("at" NAME)? ("previous" NAME)? ("following" NAME)?

```
