# pythonql
PythonQL is an extension to Python that allows language-integrated queries against relational, XML and JSON data, as well an Python's collections


Python has pretty advanced comprehensions, that cover a big chunk of SQL, to the point where PonyORM was able to build a whole ORM system based on comprehensions. However, group by mechanisms, outerjoins and support for semi-structured data are not handled well at all.


We propose the following extensions to Python( that are implemeneted in this demo preprocessor and query executor):

 - Path expressions. When working with nested data that has varied structure, path expressions are extremely useful. We have modeled our path expression on XPath, however we use a much simplified verison:

  - Child step:  ```for x in data ./ _``` or ```for x in data ./ expr ``` where expr must evaluate to string 
  - Descendants step: ```for x in data .// _``` or ```for x in data ../ expr``` where expr must evaluate to string

So we can write path expression in the query language (and elsewhere in Python expressions) like this:
```
  for x in data ./ "hotels" .// "room"
```

 - Try-except expressions. Python has try-except statement, but in many cases when working with dirty or semi-structured data, we need to be able to use an expression inside an iterator or the query. So we introduced a try-except expressions:
 
```
   try int(x) except 0 for x in values 
```

 - Tuple constructor. Tuples that have named columns are very useful in querying, however Python's native namedtuple is not very convenient. We have extended Python's tuple constructor syntax:
 ```
   (id as employee_id, sum(x) as total_salary)
 ```

 - Query expressions:
Our query syntax is a strict superset of Python's comprehensions, we extend the comprehensions to do much more powerful queries
than they are capable of now.
```
 [ select prod,len(p) 
   for p in sales 
   let prod = p.prod 
   group by prod ]
```

 At the same time our queries look similar to SQL, but are more flexible and of course most of the expressions in the queres are
in pure Python. A lot of functionality is cleaner than in SQL, like the window queries, subqueries in general, etc.


As in Python, our query expressions can return generators, list, sets and maps.


Here is a small example PythonQL program (we're building a demo website with a number of scenarios that are especially good for solving with PythonQL):

```Python
# This example illustrates the try-catch business in PythonQL.
# Basically, some data might be dirty, but you still want to be able to write a simple query

from collections import namedtuple
ord = namedtuple('Order', ['cust_id','prod_id','price'])
cust = namedtuple('Cust', ['cust_id','cust_name'])

ords = [ ord(1,1,"16.54"),
         ord(1,2,"18.95"),
         ord(1,5,"8.96"),
         ord(2,1,"????"),
         ord(2,2,"20.00") ]

custs = [ cust(1,"John"), cust(2,"Dave"), cust(3,"Boris") ]

# Basic SQL query, but with some data cleaning
res = [select (name, sum(price) as sum)
        for o in ords
        let price = try float(o.price)  except 0
        for c in custs
        where c.cust_id == o.cust_id
        group by c.cust_id as id, c.cust_name as name]

print (res)

# Funny query, lets count how many integers there are everywhere in the data
res = [ select x
        for x in ords .// _
        let y = try isinstance(int(x),int) else False except False
        where y
        ]

print (len(res))
```

## Installing pythonql:

Currently you need to clone this repository. In the future we'll make a pip installer.

## Running pythonql:

Currently PythonQL is available as a pre-processor, so you need to write a pythonql script and
execute it, or execute a pythonql string. We have a runner that you can use to execute a file:

`python3 pythonql/RunPYQL.py <pythonql program>`

## How it will work soon (and properly):

In the near future we will reimplement PythonQL to use file encoding, hence it will compile automatically
if you mark your Python file as a PythonQL file.
