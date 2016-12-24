from collections import namedtuple

open_account = namedtuple('open',['event_name','client_id','date','client_data'])
client_data = namedtuple('client_data',['firstName','lastName','birthdate','address'])
address = namedtuple('address',['street','city','state','zip'])
deposit = namedtuple('deposit',['event_name','client_id','date','amount'])
withdraw = namedtuple('withdraw',['event_name','client_id','date','amount'])
loan_req = namedtuple('loan_req',['event_name','client_id','date','amount','duration'])
loan_issued = namedtuple('loan_issued',['event_name','client_id','loan_id','date','amount','duration','interest'])
loan_paid = namedtuple('loan_paid',['event_name','client_id','loan_id','date','amount'])
reminder = namedtuple('reminder',['event_name','client_id','loan_id','date'])
close_account = namedtuple('close',['event_name','client_id','date'])

cust_journeys = [
  [ open_account('open', 1, '2015-01-16', client_data('John', 'Smith', '1968-12-05',
                                        address('10 Main st.','Austin','TX',81234))),
    deposit('deposit',1,'2015-02-10',250),
    deposit('deposit',1,'2015-02-17',320),
    withdraw('withdraw',1,'2015-02-23',500),
    loan_req('loan_req',1,'2015-02-26',3000,6),
    loan_issued('loan_issued',1,1,'2015-03-01',3000,6,9),
    loan_paid('loan_paid',1,1,'2015-09-01',3270),
     ],

  [ open_account('open', 2, '2016-02-01', client_data('Mary','Jones','1975-05-12',
                                       address('Camino Avenue','Los Angeles','CA',92313))),
    deposit('deposit',2,'2016-02-01',300),
    deposit('deposit',2,'2016-03-05',1500),
    deposit('deposit',2,'2016-04-01',700),
    withdraw('withdraw',2,'2016-05-01',330),
    withdraw('withdraw',2,'2016-06-01',2200),
    close_account('close',2,'2016-06-15') ],

  [ open_account('open', 3, '2015-12-10', client_data('James','Cook','1975-04-12',
                                       address('14 Lincoln Ave', 'Dallas', 'TX',82912))),
    loan_req('loan_req',3,'2015-12-11',1000,5),
    deposit('deposit',3,'2016-01-01',300),
    deposit('deposit',3,'2016-01-13',500),
    withdraw('withdraw',3,'2016-01-18',600),
    withdraw('withdraw',3,'2016-01-20',100),
    deposit('deposit',3,'2016-02-02',700),
    withdraw('withdraw',3,'2016-02-15',300),
    loan_req('loan_req',3,'2016-02-18',1000,3),
    close_account('close',3,'2016-03-01') ],

  [ open_account('open', 4, '2015-12-01', client_data('Bill','Ross','1980-12-15',
                                       address('14 Town Ave','Austin','TX', 89123))),
    deposit('deposit',4, '2016-03-05', 300),
    loan_req('loan_req',4, '2016-03-10', 1000,3),
    loan_issued('loan_issued',4,1,'2016-03-15',1000,3,9) ],

  [ open_account('open', 5, '2015-11-13', client_data('Jeff','Huges','1965-11-23',
                                       address('1232 Santa Fe Ave','Los Angeles','CA',95312))),
    deposit('deposit',5, '2015-11-15', 500),
    withdraw('withdraw',5,'2015-11-18',300),
    deposit('deposit',5,'2015-11-28',500),
    loan_req('loan_req',5,'2015-11-29',1500,3),
    loan_issued('loan_issued',5,1,'2015-12-02',1500,3,8),
    deposit('deposit',5,'2016-01-05',200),
    withdraw('withdraw',5,'2016-02-05',100),
    reminder('reminder',5,1,'2016-03-03'),
    reminder('reminder',5,1,'2016-03-13'),
    reminder('reminder',5,1,'2016-03-23'),
    reminder('reminder',5,1,'2016-04-03'),
    loan_paid('loan_paid',5,1,'2016-04-05',1620),
    close_account('close',5,'2016-04-05') ],

  [ open_account('open', 6, '2016-01-01', client_data('Bob','Dole','1954-09-12',
                                       address('98 Main Street','Fresno','CA',92145))),
    deposit('deposit',6,'2016-01-05',300),
    loan_req('loan_req',6,'2016-01-08',2500,2),
    loan_issued('loan_issued',6,1,'2016-01-12',2500,2,6),
    deposit('deposit',6,'2016-02-10',300),
    reminder('reminder',6,1,'2016-03-13'),
    reminder('reminder',6,1,'2016-03-23'),
    reminder('reminder',6,1,'2016-04-03'),
    loan_paid('loan_paid',6,1,'2016-04-07',2650) ],

  [ open_account('open',7,'2015-10-11', client_data('Jason','Rod','1976-12-04',
                                       address('105 Clairemont street','Los Angeles','CA',92431))),
    deposit('deposit',7,'2015-10-13',500),
    withdraw('withdraw',7,'2015-10-17',200),
    deposit('deposit',7,'2015-11-01',400),
    loan_req('loan_req',7,'2016-01-01',5000,2),
    loan_issued('loan_issued',7,1,'2016-01-03',4000,2,10),
    deposit('deposit',7,'2016-02-02',400),
    withdraw('withdraw',7,'2016-02-20',500),
    reminder('reminder',7,1,'2016-03-04'),
    reminder('reminder',7,1,'2016-03-24'),
    reminder('reminder',7,1,'2016-04-04'),
    reminder('reminder',7,1,'2016-04-24'),
    close_account('close',7,'2016-05-01') ]

]
