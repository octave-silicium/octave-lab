"""G4 capacity diagnostic with pinned 2022 accounts, hypothetical constraints only."""
import io,json,sys
import numpy as np
import openpyxl
from pipeline.audit_tes_income import audit,pinned,SYM_SHA,CODES
from pipeline.economic_sector_structural import Structure,state
from pipeline.economic_sector_capacity import Limits,allocate

def main(std,sym,eu):
    income=audit(std,sym,eu)
    wb=openpyxl.load_workbook(io.BytesIO(pinned(sym,SYM_SHA)),data_only=True);d,m=wb.worksheets[1:]
    def mat(sh,rs,cs):return np.array([[float(sh.cell(i,j).value) for j in cs] for i in rs])
    V=mat(d,range(11,48),range(4,41));U=mat(d,range(11,48),range(45,82));M=mat(m,range(11,48),range(10,47))
    q=V.sum(1);g=V.sum(0);y=mat(d,range(11,48),[95]).ravel()
    B=U/g;I=M/g;D=V.T/q;A=B@D
    bs=income["branches"]
    def v(k):return np.array([x[k] for x in bs])/g
    def tup(x):return tuple(float(a) for a in x)
    def matrix(x):return tuple(tup(r) for r in x)
    s=Structure(tuple(CODES),matrix(B),matrix(I),matrix(D),tup(v("compensation")),tup(v("other_net_production_taxes")),tup(v("valuation_bridge")),tup(v("gross_surplus_mixed")),tup(y),"PINNED_2022_CONDITIONAL")
    ref=state(s)
    assert np.max(abs(np.array(ref["q"])-q))<1e-5
    n=len(CODES);ix=CODES.index
    unbound=(None,)*n;all_tiers=(tuple(CODES),)
    core=tuple(k for k in CODES if k in ("OZ","PZ","QA","QB"))
    priority=(core,tuple(k for k in CODES if k not in core))
    bc=[None]*n;bc[ix("JC")]=float(.95*g[ix("JC")])
    ic=[None]*n;ic[ix("CI")]=float(.90*M.sum(1)[ix("CI")])
    # Independent dense linear solution and tier-wise bound verification.
    R=np.linalg.solve(np.eye(n)-A,np.eye(n))
    G=D@R;J=I@G
    cases={}
    for name,branch,imports,tiers in [
        ("unconstrained",unbound,unbound,all_tiers),
        ("jc_branch_cap_uniform",tuple(bc),unbound,all_tiers),
        ("jc_branch_cap_priority",tuple(bc),unbound,priority),
        ("ci_import_cap_uniform",unbound,tuple(ic),all_tiers),
        ("joint_caps_priority",tuple(bc),tuple(ic),priority)]:
        l=Limits(branch,imports,tiers,"Hypothetical constraints; JC branch 95% of 2022 output, CI imported intermediate product 90% of 2022 use; priority OZ/PZ/QA/QB when specified.")
        receipt=allocate(s,l);r=receipt["result"]
        served=np.zeros(n);alphas=[]
        for tier in tiers:
            yy=np.array([y[i] if k in tier else 0. for i,k in enumerate(CODES)])
            candidates=[1.]
            for caps,T in ((branch,G),(imports,J)):
                use=T@served;need=T@yy
                candidates.extend(max(0.,cap-use[i])/need[i] for i,cap in enumerate(caps) if cap is not None and need[i]>0)
            alpha=min(candidates);alphas.append(alpha);served+=alpha*yy
        assert np.max(abs(served-r["served_final"]))<1e-5,"REFERENCE_ALLOCATION"
        assert np.max(abs(R@served-r["feasible_output"]))<1e-5,"REFERENCE_OUTPUT"
        assert np.max(abs(np.array(alphas)-[t["fraction"] for t in r["tiers"]]))<1e-9,"REFERENCE_TIER"
        totals=r["totals"];requested=r["unconstrained_totals"]
        cases[name]={"sha256":receipt["sha256"],"served_final":float(sum(r["served_final"])),"unserved_final":float(sum(r["unserved_final"])),"tiers":r["tiers"],"delta_totals":{k:totals[k]-requested[k] for k in totals},"top_unserved":sorted(zip(CODES,r["unserved_final"]),key=lambda p:-p[1])[:6],"limits":{"branch":{k:b for k,b in zip(CODES,branch) if b is not None},"imports":{k:b for k,b in zip(CODES,imports) if b is not None}},"actual_output":None}
    return {"status":"EMPIRICAL_BASE_HYPOTHETICAL_CAPACITY_ALLOCATION","publication":"BLOCK_PUBLICATION","unit":"M EUR reference prices 2022","source_hashes":income["source_hashes"],"priority":"OZ/PZ/QA/QB product codes first; hypothetical, not policy recommendation","cases":cases,"verification":"independent dense NumPy inverse and tier bounds; fixed coefficients, no stocks or market equilibrium"}
if __name__=="__main__":print(json.dumps(main(*sys.argv[1:]),indent=2))
