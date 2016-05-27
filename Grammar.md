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
I don't have descendent or self here, do we need one?

##Query Expression
This is our main grammar piece. Again, all Python expressions are written as
`expr` production, instead of `test`. **Caution:** Python community won't like
a whole lot of new keywords added to the language (this means old code that
uses these keywords might need to be fixed up). So maybe we should converge
to the fewest possible keywords later on.

```jflex
query_expression := select 
                  (for|let) 
                  (for|let|where|window|count|groupby|orderby)* ;

select := ('select'|'return') expr ;

for := ('for'|'from') NAME 'in' expr (',' NAME 'in' expr ) * ;

let := ('let'|'with') NAME '=' expr (',' NAME '=' expr ) *;

where := 'where' | 'having' expr ;

window := TBD

count := 'count' NAME;

groupby := 'group' 'by' expr (',' expr) * ;

orderby := 'order' 'by' expr ['asc'|'desc'] (',' expr ['asc'|'desc'] ) *;

```
**TODO:** We need to decide if we want to keep the select in the current shape. Or just replace the whole thing with a single expression like in JSONiq or XQuery. The semantics of the select list with mutlitple expressions and aliases right now is to create a PQTuple object, which combines dict(JSON), tuple (native Python tuple) and namedtuple (also avaiable in Python) interfaces. So its pretty cool for relational data, but also can be used for JSONiq and maybe XML (we can make a default mapping from PQTuple to XML.
