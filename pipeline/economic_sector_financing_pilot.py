"""Independent hand-derived expected cash, debt, delivery and capacity trajectories."""
from dataclasses import replace
from .economic_sector_structural import Structure
from .economic_sector_capital import Asset,Vintage,Investment,Period
from .economic_sector_financing import Funding,funded_path

def audit():
    s=Structure(("A","B"),((0,0),(0,0)),((0,0),(0,0)),((1,0),(0,1)),(.5,.5),(0,0),(0,0),(.5,.5),(100,80),"SYNTHETIC")
    a=Asset("machine","A","B",2,10,0,0,10,"synthetic");v=Vintage("machine",10,0,20)
    p=Period(s,(None,None),(("A","B"),),(1,),"synthetic");i=Investment("order","machine",1,5,2,"synthetic")
    f=Funding(0,10,10,0,0,0,0,0,"synthetic")
    # Each row: acquired investment, closing cash, debt, interest arrears, principal overdue, capacity A.
    cases={}
    specs=[
      ("full_credit",(f,)*4,(i,),0,0,(0,100),[(10,0,10,0,0,100),(0,0,10,0,0,100),(0,0,10,0,0,150),(0,0,10,0,0,150)]),
      ("credit_limit",(replace(f,new_credit_limit=4),)*4,(i,),0,0,(0,100),[(4,0,4,0,0,100),(0,0,4,0,0,100),(0,0,4,0,0,120),(0,0,4,0,0,120)]),
      ("supply_limit",(f,)*4,(i,),5,0,(0,45),[(5,0,0,0,0,100),(0,0,0,0,0,100),(0,0,0,0,0,125),(0,0,0,0,0,125)]),
      ("cash_reinvestment",(replace(f,new_credit_limit=0,surplus_to_cash=.1),)*4,(replace(i,period=2,lag=1),),0,0,(0,100),[(0,5,0,0,0,100),(5,5,0,0,0,100),(0,10,0,0,0,125),(0,15,0,0,0,125)]),
      ("service_and_cure",(replace(f,interest_rate=.1,principal_fraction=.2),replace(f,interest_rate=.1,principal_fraction=.2,equity_injection=10)),(),0,10,(0,100),[(0,0,10,1,2,100),(0,4.4,6.4,0,0,100)]),
      ("blocked_by_service",(replace(f,interest_rate=.1,debt_ceiling=30),)*4,(i,),0,10,(0,100),[(0,0,10,1,0,100),(0,0,10,2,0,100),(0,0,10,3,0,100),(0,0,10,4,0,100)]),
      ("equity_and_credit",(replace(f,equity_injection=4,cash_reserve=2),f,f,f),(i,),0,0,(0,100),[(10,2,8,0,0,100),(0,2,8,0,0,100),(0,2,8,0,0,150),(0,2,8,0,0,150)])]
    for name,pol,orders,cash,debt,cap,expected in specs:
        receipt=funded_path((p,)*len(pol),(a,),(v,),orders,pol,borrower="A",initial_cash=cash,initial_debt=debt,noncapital_capacity=cap,period_unit="YEAR",evidence="synthetic")
        actual=[]
        for row,exp in zip(receipt["result"]["periods"],expected):
            values=[row["investment_acquired"],row["closing_cash"],row["closing_debt"],row["closing_interest_arrears"],row["closing_principal_overdue"],row["capital"]["capacity"][0]]
            assert all(abs(x-y)<1e-8 for x,y in zip(values,exp)),(name,values,exp)
            actual.append(values)
        cases[name]={"sha256":receipt["sha256"],"actual":actual,"analytical":expected}
    return {"status":"SYNTHETIC_FINANCED_CAPITAL_AUDIT","publication":"BLOCK_PUBLICATION","columns":["acquired","cash","debt","interest_arrears","principal_overdue","capacity_A"],"cases":cases,"verification":"hand-derived conditional ledger and capital capacity paths"}
if __name__=="__main__":
    import json
    print(json.dumps(audit(),indent=2))
