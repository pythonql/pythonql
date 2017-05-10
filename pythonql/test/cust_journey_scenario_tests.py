#coding: pythonql


def cust_journey_test():
  import numpy as np
  from cust_journey_data import cust_journeys
  from datetime import date
  from calendar import monthrange
  from collections import namedtuple
  from dateutil.parser import parse

  res = [ # We will return state, total number of customers with loans and customer's default rate
       select (state,
              len(last_issued) as custs_with_loans,
              sum(default)/len(last_issued) as default_rate )

       # Iterate over all journeys
       for cj in cust_journeys

       # Fetch the 'open' and 'loan_issued' events from the journey
       let new = [select e
                  for e in cj
                  where e.event_name=='open'][0],
           issued = [select e
                           for e in cj
                           where e.event_name=='loan_issued']

       # We're only interested in customers who were issued at least one loan
       where issued != []

       # Find the last issued loan
       let last_issued = issued[-1],

           # Check whether this loan has been paid
            paid = [select e
                    for e in cj
                    where e.event_name=='loan_paid'
                         and e.loan_id==last_issued.loan_id] != [],
            default = 1 if not paid else 0

       # Group the results by state
       group by new.client_data.address.state as state
       order by state ]

  assert res[0].state=='CA' and res[1].state=='TX'
  assert res[0].custs_with_loans==3 and res[1].custs_with_loans==2

  res = [
   select (state, len(balance) as n_customers)
   for cj in cust_journeys

   let new = [select e for e in cj where e.event_name=='open'][0],
       withdrawals = [select e.amount for e in cj where e.event_name=='withdraw'],
       deposits = [select e.amount for e in cj where e.event_name=='deposit']

   let balance = sum(deposits) - sum(withdrawals)
   where balance > 300
   group by new.client_data.address.state as state
   order by state ]

  assert res[0].n_customers==3
  assert res[1].n_customers==1

  n_closed = len([
   select cj
   for cj in cust_journeys
   where [select e for e in cj where e.event_name=='close']])

  # These customers closed their accounts and were refused a loan
  n_closed_and_refused = len([
   # Iterate over customer journeys
   select cj
   for cj in cust_journeys

   # Pick out the close event, if it doesn't exist, filter our the journey
   let close = next((select e for e in cj where e.event_name=='close'),None)
   where close

   # Get the last loan request event
   let requests = [select e for e in cj where e.event_name=='loan_req']
   where requests
   let last_request = requests[-1],
       last_request_date = parse(last_request.date),
       close_date = parse(close.date)

   # Make sure the last loan request was at most 30 days before
   # the account was closed, and check the there was no loan
   # issued
   where (close_date - last_request_date).days < 30
     and not [select e
              for e in cj
              where e.event_name=='loan_issued' and
              (parse(e.date) - last_request_date) > 0 ]  ])

  assert n_closed_and_refused/float(n_closed) == 0.25

  # Compute the list of closed accounts
  closed = [
    select cj
    for cj in cust_journeys
    let close = next((select e for e in cj where e.event_name=='close'),None)
    where close
  ]

  # Compute the list of closed accounts with lots of reminders
  too_many_reminders = [

    # Iterate over closed accounts
    select cj
    for cj in closed

    # Get a list of dates of all reminders
    let reminder_dates = [select parse(e.date)
                        for e in cj
                        where e.event_name=='reminder']

    # Check whether two different dates are less than 30 days appart
    where [ select d1
          for d1 in reminder_dates, d2 in reminder_dates
          where d1 != d2 and (d1 - d2).days < 30 ]]

  assert len(too_many_reminders)/float(len(closed)) == 0.5

  res = np.mean([

    # Return the mean of customer's burn rates
    select np.mean(burn_rates) if burn_rates else 0

    # Iterate over customer journeys
    for cj in cust_journeys

    # Get the dates of the first and last customer journey events
    let first_date = parse(cj[0].date),
        last_date = parse(cj[-1].date),
        withdrawals = [select (e.amount as amount, parse(e.date) as date)
                       for e in cj where e.event_name=='withdraw']

    # Compute the burn rates by iterating over all months in the
    # period from the first to last events in the customer journey

    let burn_rates = [
          select sum(ws)
          for yr in range(first_date.year, last_date.year+1),
              month in range(1,12+1)
          let last_day_month = date(yr, month, monthrange(yr,month)[1]),
               first_day_month = date(yr,month,1)
          where last_day_month > first_date.date() and first_day_month < last_date.date()
          let ws = [select e.amount
                    for e in withdrawals
                    where e.date.year == yr and e.date.month == month] ]
  ])

  assert res > 152 and res < 153
