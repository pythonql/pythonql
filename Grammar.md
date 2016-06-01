#PythonQL EBNF Grammar
This document describes the grammar that we want to implement in PythonQL

##Path expressions.
We start with path expressions, since they are a separate beast and will be
used not only in query context, but elsewhere in the PythonQL language.
They appear under general expression, so we will give the grammar starting
at `expr`. Btw. in the real grammar this production is called `test`, but
its confusing. Instead of `test` in EBNF we use `expr`, and instead of 
`old_test` (the production before we introduced path expressions) we use
`old_expr`.

```jflex
  expr := old_expr ( path_step )*;
  path_step := './' | './/' | '{' expr '}';
```
`'./'` is a child path step. `.//` is a descendent path step. `'{' expr '}'` is a filter.

Predicate expression is an arbitrary Python expression, but has the following predefined variables
avaiable for use: `item` if the predicate is applied to list and `key` and `value` if the predicate
is applied to a map.

## Try-except expression
Python has great exception handling and actually a lot of Python code heavily depends on it.
However, Python's exceptions are statements. Hence they cannot be used in path and query 
expressions. But they are incredibly useful there, so we introduced a simple for of try-except
expression.

```jflex
  try_except_expr := 'try' '{' expr '}' 'except' expr ? '{' expr '}'
```  

##Query Expression
This is our main grammar piece. Again, all Python expressions are written as
`expr` production, instead of `test`. **Caution:** Python community won't like
a whole lot of new keywords added to the language (this means old code that
uses these keywords might need to be fixed up). So maybe we should converge
to the fewest possible keywords later on.

```jflex
query_expression := select 
                ( for | let ) 
                ( for | let | where | window | count | groupby | orderby )* ;

select := ( 'select' | 'return' ) select_var (',' select_var) * ;

select_var := expr ("as" NAME)? ;

for := ( 'for' | 'from' ) NAME 'in' expr (',' NAME 'in' expr ) * ;

let := ( 'let' | 'with' ) NAME '=' expr (',' NAME '=' expr ) *;

where := 'where' | 'having' expr ;

count := 'count' NAME;

groupby := 'group' 'by' expr ('as' NAME)? (',' expr ('as' NAME)? ) * ;

orderby := 'order' 'by' expr ['asc' | 'desc'] (',' expr ['asc' | 'desc'] ) *;

window := 'for' ( tumbling_window | sliding_window ) ;

tubling_window := 'tumbling' 'window' NAME 'in' expr window_start_cond window_end_cond? ;

sliding_window := 'sliding' 'window' NAME 'in' expr window_start_cond window_end_cond ;

window_start_cond := 'start' window_vars 'when' expr ;

window_end_cond := 'only'? 'end' window_vars 'when' expr ;

window_vars := NAME? ("at" NAME)? ("previous" NAME)? ("next" NAME)?

```
**TODO:** We need to decide if we want to keep the select in the current shape. Or just replace the whole thing with a single expression like in JSONiq or XQuery. The semantics of the select list with mutlitple expressions and aliases right now is to create a PQTuple object, which combines dict(JSON), tuple (native Python tuple) and namedtuple (also avaiable in Python) interfaces. So its pretty cool for relational data, but also can be used for JSONiq and maybe XML (we can make a default mapping from PQTuple to XML.
