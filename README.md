# pythonql
A LINQ type extension to Python that allows language-integrated queries against relational, XML and JSON data, as well an Python's collections


Python has pretty advanced comprehensions, that cover a big chunk of SQL, to the point where PonyORM was able to build a whole ORM system based on comprehensions. However, group by mechanisms, outerjoins and support for semi-structured data are not handled well at all.


We propose the following extensions to Python( that are implemeneted in this demo preprocessor and query executor):

1. Path expressions. When working with nested data that has varied structure, path expressions are extremely useful. We have modeled our path expression on XPath, however we use a much simplified verison:

  - Child step:  for x in data ./ 
  - Descended step: for x in data .//
  - Filter step: for x in data { key == 'green' }

So we can write path expression in the query language (and elsewhere in Python expressions) like this:

  - for x in data ./ {key == 'green'} .// { key == 'yellow' }

2. Query expression:

   select x, y, sum(w)
   for x in data ./,
       y = x ./,
       w in data 2
   group by x,y
   where x % 2 == 0



We'll be adding a window and maybe try/catch to the expression, to make it as powerful as a JSONiq query.


The query expressions can be executed on top of any Python collections, but if databases are at the source, the
idea is to push as much work as possible into the database layer.
