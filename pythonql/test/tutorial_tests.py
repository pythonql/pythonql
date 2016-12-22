#coding: pythonql

def q1_test():
  res = [ (x,y)
            for x in range(1,8)
            for y in range(1,7)
            if x % 2 == 0 and
               y % 2 != 0 and
               x > y ]

  assert res[0].x == 2 and res[0].y == 1

def q2_test():
  res = [ (x, sum(y) as sum)
           for x in range(1,8),
               y in range(1,7)
           if x % 2 == 0 and y % 2 != 0 and x > y
           group by x ]

  assert res[0].x==2 and res[0].sum==1

def q3_test():
  res = [ select (x, sum_y)
           for x in range(1,8),
               y in range(1,7)
           where x % 2 == 0 and y % 2 != 0 and x > y
           group by x
           let sum_y = sum(y)
           where sum_y % 2 != 0
           ]

  assert res[0].x==2 and res[0].sum_y==1
  assert res[1].x==6 and res[1].sum_y==9

def q4_test():
  res = [ (x,y)
           for x in range(1,10)
           let ys = [  y for y in range(1,10)
                      where x%2 == 0 and x > y ],
               ys_and_none = ys if ys != [] else [ None ]

           for y in ys_and_none ]

  assert res[3].x==4 and res[3].y==1
  assert res[6].x==5 and res[6].y is None

def q5_test():
  res = [ select (x,y)
        for x in range(1,5),
            y in range(1,5)
        where x > y
        group by x ]

  assert res[2].x==4 and res[2].y==[1,2,3]

def q6_test():
  res = [ select (x_squared, y)
        for x in range(1,5),
            y in range(1,5)
        where x > y
        group by x**2 as x_squared ]

  assert res[0].x_squared==16 and res[0].y==[1,2,3]
  assert res[1].x_squared==9 and res[1].y==[1,2]

def q7_test():
  res = [ select (x,y)
        for x in range(1,5),
            y in range(1,5)
        where x > y
        order by abs(x-y) asc, y desc ]

  assert res[0].x==4 and res[0].y==3
  assert res[1].x==3 and res[1].y==2

def q8_test():
  db = [ {"region": [{"box": [1,2], "label":"lake" },
                   {"box": {"box": [2,3]} },
                   {"region": {"box":[ 1,2], "label":"lake"} },
                   {"region": {"circle": [0.5,0.5,45], "label":"pond" }}] },
       {"region": {"box": [1,2], "label":"lake" }}]

  assert len(list(db./'region'./'region'))==2
  assert len(list(db .// 'box'))==5

def q9_test():
  data = [ 15, 25, None, 80, 34, "34", "twenty", [12], 54, 12]

  res = sum([ select num 
        for item in data
        let num = try int(item) except 0 ])

  assert res == 254

def q10_test():
  res = [ select {"sequence_start": i,
                "sequence": [ select {"item":k}
                              for k in range(i,i+5) ]}
        for i in [1,3,5]]

  assert res[1]['sequence_start']==3 and len(res[1]['sequence'])==5

def q11_test():
  x = [1,2,3,4,5,6,7]

  res = [ select (y,sum(w) as sum)
        for sliding window w in x
        start y at s when True
        end at e when e-s == 2 ]
  
  assert res[0].y==1 and res[0].sum==6
  assert res[1].y==2 and res[1].sum==9
  assert res[2].y==3 and res[2].sum==12

def q12_test():
  x = [1,2,3,4,5,6,7]

  res = [ select (y,sum(w) as sum)
        for sliding window w in x
        start y when y % 2 == 0
        end z when z-y > 2 ]

  assert res[0].y==2 and res[0].sum==14
  assert res[1].y==4 and res[1].sum==22
  assert res[2].y==6 and res[2].sum==13

def q13_test():
  res = [ select (s, x)
        for sliding window x in
          (select (y,z)
           for (y,z) in [(1,1), (2,2), (3,3),
                         (4,4), (5,5), (6,6)])
        start s when s.y % 2 == 1
        only end e when e.y-s.y >= 2 ]

  assert res[0].s.y==1 and res[0].s.z==1
  assert res[1].s.y==3 and res[1].s.z==3
