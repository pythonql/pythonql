#coding: pythonql

def exact_test():
  people = [ {'first':'daniela',
            'last':'f',
            'age':45,
            'zip_code' : {'number':123}},

           {'first':'daniela',
            'last':'k',
            'age':50,
            'zip_code' : {'number':999}},

           {'first':'daniela',
            'last':'j',
            'age':50,
            'extra_field':True,
            'zip_code' : {'number':999}},

           {'first':'john',
            'last':'wayne',
            'age':50,
            'extra_field':True,
            'zip_code' : {'number':999}},

           {'first':'daniela',
            'last':'s',
            'age':55,
            'zip_code' : {'number':999, 'extra_field':True }}]

  res = [
        select z
        match exact
        {       "last" : as x ,
                 "first" : "daniela",
                 "age" : as y  where y>40,
                 "zip_code" : { "number" : as w }
        } as z in people
       order by x
  ]
  assert len(res)==2
  assert res[0]['age'] == 45


  res = [select z
        match 
        {       "last" : as x ,
                 "first" : "daniela",
                 "age" : as y  where y>40,
                 "zip_code" : { "number" : as w }
        } as z in people
       order by x
  ]
  assert len(res)==4
  assert res[3]['age']==55
