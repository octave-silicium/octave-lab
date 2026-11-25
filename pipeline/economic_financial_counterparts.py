"""G4 v0.7e: counterpart ledger for the synthetic v0.7d financing path.
One deposit issuer, no interbank settlement or bank solvency model."""
from decimal import Decimal as D
from .economic_core import canonical,digest
from .economic_sector_structural import require

ACTORS=("borrower","bank","owner","supplier","operations")
def num(x):
    v=D(str(x));require(v.is_finite(),"FINITE");return v
def close(a,b):
    require(abs(a-b)<=D("1e-8")*max(D(1),abs(a),abs(b)),"REPLAY_BALANCE")

def counterpart(receipt,initial_deposits,*,initial_equity=0,equity_revaluations=(),evidence):
    require(isinstance(evidence,str) and evidence.strip(),"EVIDENCE")
    r=receipt["result"];require(receipt["sha256"]==digest(canonical(r)) and r["status"]=="CONDITIONAL_FINANCED_CAPITAL_PATH","RECEIPT")
    rows=r["periods"];require(rows,"EMPTY")
    require(set(initial_deposits)==set(ACTORS)-{"bank"},"DEPOSIT_AXIS")
    pos={("DEPOSIT",k,"bank"):num(v) for k,v in initial_deposits.items()}
    pos.update({("LOAN","bank","borrower"):num(rows[0]["opening_debt"]),("EQUITY","owner","borrower"):num(initial_equity),("INTEREST_PAYABLE","bank","borrower"):D(0),("OPERATING_PAYABLE","operations","borrower"):D(0)})
    require(all(v>=0 for v in pos.values()),"INITIAL_POSITIONS")
    changes=dict(equity_revaluations);require(len(changes)==len(equity_revaluations) and all(type(t) is int and 1<=t<=len(rows) for t in changes),"REVALUATION_PERIOD")
    def positions():
        return [{"instrument":k[0],"creditor":k[1],"debtor":k[2],"stock":str(v)} for k,v in sorted(pos.items())]
    def nfa():
        out={a:D(0) for a in ACTORS}
        for (_,c,d),v in pos.items():out[c]+=v;out[d]-=v
        require(sum(out.values())==0,"SYSTEM_NFA")
        return out
    result=[]
    for row in rows:
        t=row["period"];start=dict(pos);opening=nfa();events=[]
        close(pos["DEPOSIT","borrower","bank"],num(row["opening_cash"]))
        close(pos["LOAN","bank","borrower"],num(row["opening_debt"]))
        def event(name,legs,kind="TRANSACTION"):
            # All positions represent a matched asset and liability. Transfers
            # between deposit holders preserve deposits outstanding.
            for key,delta in legs:
                pos[key]+=delta
                require(pos[key]>=-D("1e-8"),"NEGATIVE_POSITION:"+str(key))
            events.append({"name":name,"kind":kind,"legs":[{"instrument":k[0],"creditor":k[1],"debtor":k[2],"delta":str(v)} for k,v in legs]})
        dep=lambda a:("DEPOSIT",a,"bank")
        loan=("LOAN","bank","borrower");eq=("EQUITY","owner","borrower");it=("INTEREST_PAYABLE","bank","borrower");op=("OPERATING_PAYABLE","operations","borrower")
        def transfer(name,payer,payee,value,extra=()):
            x=num(value);require(x>=0,"NEGATIVE_FLOW")
            legs=[]
            if payer!="bank":legs.append((dep(payer),-x))
            if payee!="bank":legs.append((dep(payee),x))
            event(name,legs+list(extra))
        x=num(row["equity_injection"]);transfer("equity_subscription","owner","borrower",x,[(eq,x)])
        x=num(row["old_operating_arrears_paid"]);transfer("settle_operating_arrears","borrower","operations",x,[(op,-x)])
        event("interest_accrual",[(it,num(row["interest_accrued"]))])
        x=num(row["interest_paid"]);transfer("interest_settlement","borrower","bank",x,[(it,-x)])
        x=num(row["principal_paid"]);transfer("loan_principal_repaid","borrower","bank",x,[(loan,-x)])
        x=num(row["new_debt_draw"]);event("loan_origination",[(loan,x),(dep("borrower"),x)])
        transfer("equipment_delivery","borrower","supplier",row["investment_acquired"])
        transfer("operating_receipts","operations","borrower",row["operating_cash_received"])
        x=num(row["operating_loss_paid"]);transfer("operating_loss_settlement","borrower","operations",x)
        unpaid=max(D(0),-num(row["net_operating_cash_proxy"]))-x
        event("new_operating_payable",[(op,unpaid)])
        if t in changes:event("assumed_equity_revaluation",[(eq,num(changes[t]))],"REVALUATION")
        close(pos[dep("borrower")],num(row["closing_cash"]));close(pos[loan],num(row["closing_debt"]))
        close(pos[it],num(row["closing_interest_arrears"]));close(pos[op],num(row["closing_operating_arrears"]))
        ending=nfa();flows={a:D(0) for a in ACTORS};valuation=dict(flows)
        for e in events:
            target=valuation if e["kind"]=="REVALUATION" else flows
            for z in e["legs"]:
                v=num(z["delta"]);target[z["creditor"]]+=v;target[z["debtor"]]-=v
        for a in ACTORS:close(ending[a],opening[a]+flows[a]+valuation[a])
        for k,v in pos.items():
            close(v,start[k]+sum((num(z["delta"]) for e in events for z in e["legs"] if (z["instrument"],z["creditor"],z["debtor"])==k),D(0)))
        result.append({"period":t,"events":events,"positions":positions(),"net_financial_assets":{a:str(v) for a,v in ending.items()},"net_financial_transactions":{a:str(v) for a,v in flows.items()},"net_revaluation":{a:str(v) for a,v in valuation.items()},"borrower_principal_overdue_memo":str(row["closing_principal_overdue"])})
    out={"status":"CONDITIONAL_COUNTERPART_LEDGER","publication":"BLOCK_PUBLICATION","source_receipt":receipt["sha256"],"periods":result,"evidence":evidence,"actual_bank_capital":None,"actual_wealth":None,"actual_default":None,"limitations":["single stylized deposit issuer; all parties share bank; initial counterparty deposits explicit and finite","new loans create matching loan and deposit; bank interest/principal payments extinguish deposits","equity at subscription value plus explicit scenario revaluation, not market price; no physical assets in financial ledger","operations pool not a calibrated institutional sector; counterpart liquidity insufficiency rejects path rather than re-solving it","no bank reserves, capital adequacy, credit supply equilibrium, losses/writeoffs, interbank or cross-border settlement"]}
    return {"result":out,"sha256":digest(canonical(out))}
