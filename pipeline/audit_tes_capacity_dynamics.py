"""Quarterly conditional paths from pinned French annual accounts, not quarterly observations."""
import io,json,sys
from dataclasses import replace
import numpy as np
import openpyxl
from pipeline.audit_tes_income import audit,pinned,SYM_SHA,CODES
from pipeline.economic_sector_structural import Structure,state
from pipeline.economic_sector_capacity_dynamics import Period,CapacityOrder,trajectory

def main(std,sym,eu):
    income=audit(std,sym,eu)
    wb=openpyxl.load_workbook(io.BytesIO(pinned(sym,SYM_SHA)),data_only=True);d,m=wb.worksheets[1:]
    def mat(sh,rs,cs):return np.array([[float(sh.cell(i,j).value) for j in cs] for i in rs])
    V=mat(d,range(11,48),range(4,41));U=mat(d,range(11,48),range(45,82));M=mat(m,range(11,48),range(10,47))
    q=V.sum(1);g=V.sum(0);y=mat(d,range(11,48),[95]).ravel()
    B=U/g;I=M/g;D=V.T/q
    bs=income["branches"]
    def v(k):return np.array([x[k] for x in bs])/g
    def tup(x):return tuple(float(a) for a in x)
    def matrix(x):return tuple(tup(r) for r in x)
    s=Structure(tuple(CODES),matrix(B),matrix(I),matrix(D),tup(v("compensation")),tup(v("other_net_production_taxes")),tup(v("valuation_bridge")),tup(v("gross_surplus_mixed")),tup(y/4),"PINNED_2022_CONDITIONAL")
    ref=state(s);assert np.max(abs(np.array(ref["g"])-g/4))<1e-5
    n=len(CODES);ci=CODES.index("CI");jc=CODES.index("JC")
    cap=g/4;im=M.sum(1)/4
    # Hypothetical 20% delivery shortfall for three periods, then 120% for two, then normal.
    # Initial inventories 40% of one normal quarterly CI input flow when specified.
    # All other delivery and capacity flows held at annual/4.
    normal=Period(s,tup(im),(tuple(CODES),),"Annual accounts divided by four; no quarterly measurement")
    ds=[]
    for f in (.8,.8,.8,1.2,1.2,1.):
        a=im.copy();a[ci]*=f
        ds.append(replace(normal,deliveries=tup(a)))
    z=np.zeros(n);buf=z.copy();buf[ci]=.4*im[ci]
    lower=cap.copy();lower[jc]*=.95
    expand=CapacityOrder(1,2,"JC",float(cap[jc]-lower[jc]),"Hypothetical recovery after two periods")
    withdraw=CapacityOrder(1,2,"JC",float(-.05*cap[jc]),"Hypothetical capacity retirement")
    cases={}
    for name,ps,cc,ss,orders in [
        ("baseline",(normal,)*6,cap,z,()),
        ("delivery_shock_no_buffer",tuple(ds),cap,z,()),
        ("delivery_shock_buffer",tuple(ds),cap,buf,()),
        ("delayed_capacity_recovery",(normal,)*6,lower,z,(expand,)),
        ("delayed_capacity_withdrawal",(normal,)*6,cap,z,(withdraw,)),
        ("joint_shock",tuple(ds),lower,buf,(expand,))]:
        r=trajectory(ps,tup(cc),tup(ss),orders,period_unit="QUARTER",evidence="Synthetic quarterly paths on annual 2022 reference-price structure")["result"]
        # Independent dense inverse, with identical exogenous priority rule (one tier).
        R=np.linalg.solve(np.eye(n)-B@D,np.eye(n));G=D@R;J=I@G
        stock=ss.copy();cur=cc.copy();refrows=[]
        for t,(p,row) in enumerate(zip(ps,r["periods"]),1):
            for o in orders:
                if o.placed+o.lag==t:cur[CODES.index(o.branch)]+=o.delta
            avail=stock+np.array(p.deliveries);yy=np.array(p.structure.final)
            gneed=G@yy;mneed=J@yy
            ratios=[1.]+[cur[i]/v for i,v in enumerate(gneed) if v>0]+[avail[i]/v for i,v in enumerate(mneed) if v>0]
            alpha=min(ratios);served=alpha*yy;used=J@served;stock=np.maximum(0,avail-used)
            assert np.max(abs(served-row["served_final"]))<1e-5,"INDEPENDENT_FINAL"
            assert np.max(abs(stock-row["closing_stock"]))<1e-5,"INDEPENDENT_STOCK"
            assert np.max(abs(cur-row["capacity"]))<1e-5,"INDEPENDENT_CAPACITY"
            refrows.append({"period":t,"fraction":row["tiers"][0]["fraction"],"unserved":sum(row["unserved_final"]),"ci_delivery":row["deliveries"][ci],"ci_use":row["imported_input_use"][ci],"ci_stock":row["closing_stock"][ci],"jc_capacity":row["capacity"][jc],"jc_idle":row["idle_capacity"][jc],"va":row["totals"]["va"],"binding":row["tiers"][0]["binding"],"flow_stock_residual":row["flow_stock_residual"]})
        cases[name]={"periods":refrows,"cumulative_unserved":r["cumulative_unserved_final"],"pending":r["pending_orders"]}
    return {"status":"EMPIRICAL_BASE_HYPOTHETICAL_DYNAMIC_PATHS","publication":"BLOCK_PUBLICATION","unit":"M EUR reference prices 2022 per hypothetical quarter","source_hashes":income["source_hashes"],"assumptions":{"quarter":"annual 2022 flows divided by four, not observed quarters","delivery_shock":"CI factors 0.8,0.8,0.8,1.2,1.2,1.0","buffer":"0.4 of normal quarterly CI use","capacity":"JC 95% initially with recovery after two quarters, or retirement of 5% after two quarters","allocation":"single tier proportional; all other capacity and delivery at reference levels"},"cases":cases,"verification":"independent dense linear solve, stock and capacity path checks"}
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),indent=2))
