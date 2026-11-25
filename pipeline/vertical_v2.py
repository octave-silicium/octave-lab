"""V2a single internal investigation object. No empirical-scenario numeric fusion."""
import json,argparse,os
from pathlib import Path
from .vertical_v1 import OLD,SOURCES,retrieve,digest,require,employment,adoption,REGISTRIES,ROOT
from .vertical_v11 import PERIODS,diagnostic
from .vertical_v12 import parse,metadata,META,PIN
from .vertical_scenarios import compare
from .economic_core import canonical,digest as cdigest

def readreg(name):return json.loads((ROOT/"governance"/name).read_text())
def make_observations(fetcher=retrieve):
    old=json.loads(OLD.read_text());src={}
    for k,u in SOURCES.items():
        b=fetcher(u);require(digest(b)==old["sources"][k]["sha256"],"UNREVIEWED_VINTAGE")
        if k=="urssaf_headcount":a=diagnostic(employment(b,PERIODS),"employment")
        elif k=="urssaf_dpae":
            m=metadata(fetcher(META));require(m["notice_sha256"]=="f9d328ff7adc327dcf08e56932b68ac5ddef0817c23a4bf2cade8217ef987d56","UNREVIEWED_NOTICE")
            a=parse(b)
        else:a=adoption(b)
        src[k]={"url":u,"sha256":digest(b),"analysis":a,"publication":"BLOCK_PUBLICATION"}
    return src

# Per-item dispositions, explicitly scoped to this investigation, not implementation statuses.
M_HYP={"M007","M008","M009","M018","M027","M028","M030","M032","M033","M035","M036","M042","M052","M062"}
M_OBS={"M049","M059","M061","M063","M064"}
M_PENDING={"M060"}
M_GROUPS=[
 ({"M001","M002","M003","M004","M005","M006","M010","M011","M012","M013","M014","M015","M016","M017","M019","M020","M021","M023","M024","M025","M026"},"No sector-specific measured task/process graph, capacity/quality and organizational transition data."),
 ({"M022","M029","M031","M034","M037","M038","M039","M040","M041","M043","M044","M045","M046","M047","M048"},"No admitted firm-level adoption, market structure, finance, sourcing, resource or network data for this service perimeter."),
 ({"M050","M051","M053","M054","M055","M056","M057","M058"},"No matched hours, worker/cohort income, investment, prices or institutional data to close macro feedback.")]
def coverage():
    arch=readreg("economic_mechanisms_v2.json");contract=readreg("investigation_result_v1.json")
    entries=[]
    def add(x,status,reason,refs=()):
        entries.append({"id":x,"disposition":status,"reason":reason,"claim_refs":list(refs),
                        "decision_relevance":"Determine whether the mechanism can inform this investigation; do not infer omitted effects.",
                        "next_test":"Qualify data or method specific to this entry before promoting scope."})
    for m in arch["mechanisms"]:
        i=m["id"]
        if i in M_HYP:add(i,"HYPOTHESIS_ONLY","Normalized service scenario tests conditional mechanisms; no measured parameters.",("C04",))
        elif i in M_OBS:add(i,"HYPOTHESIS_ONLY","Observed stock and declaration series, rival explanations and vintage controls; no full mechanism identification.",("C01","C02","C05"))
        elif i in M_PENDING:add(i,"BLOCKED_MISSING_DATA","No credible causal design or matched exposure panel.",("C05",))
        else:
            reason=next((r for ks,r in M_GROUPS if i in ks),None);require(reason is not None,"UNASSESSED_MECHANISM");add(i,"BLOCKED_MISSING_DATA",reason)
    for file in ("transversal_enrichment_v1.json","shapiro_enrichment_v1.json"):
        for e in readreg(file)["entries"]:
            related=set(e.get("mechanisms",[]));covered=related&M_HYP
            # Link to exact requirement; related hypothetical mechanism is not proof of full AC/SH.
            add(e["id"],"PENDING_QUALIFICATION",e["concept"]+": full requirement not tested in V2a; "+("related mechanisms explored conditionally: "+", ".join(sorted(covered)) if covered else "no direct scenario implementation for this requirement."),("C04",) if covered else ())
    for l in arch["layers"]:add(l["id"],"PENDING_QUALIFICATION",l["name"]+": only the source-native observation and normalized service scenario scope is evaluated.")
    for e in arch["engines"]:add(e["id"],"PENDING_QUALIFICATION",e["name"]+": full engine qualification not performed; scenario allocation reused, no claim of integration of all engines.")
    for i in contract["coverage"]["interfaces"]:add(i["id"],"PENDING_QUALIFICATION",i["flow"]+": no empirically calibrated cross-layer link in this investigation.")
    expected=set(contract["coverage"]["mechanism_ids"]+contract["coverage"]["layers"]+contract["coverage"]["engines"]+[i["id"] for i in contract["coverage"]["interfaces"]]+[e["id"] for f in ("transversal_enrichment_v1.json","shapiro_enrichment_v1.json") for e in readreg(f)["entries"]])
    require({r["id"] for r in entries}==expected and len(entries)==len(expected),"COVERAGE")
    return entries

def claim(i,t,statement,units,pop,period,source,mechanisms,method,limits,competing,trigger):
    return {"id":i,"revision":1,"claim_type":t,"statement":statement,"decision_relevance":"Prioritize investigation and avoid unsupported attribution.",
            "population":pop,"period":period,"geography":"France (observations); fictional service market (scenario)",
            "units_or_non_quantifiable":units,"source_and_vintage_refs":source,"mechanism_refs":mechanisms,"method_and_assumptions":method,
            "uncertainty_and_limits":limits,"competing_explanations":competing,"falsification_or_revision_trigger":trigger,
            "dependency_refs":source,"publication_status":"BLOCK_PUBLICATION"}
def build(src):
    sim=compare();a=src["urssaf_headcount"]["analysis"];d=src["urssaf_dpae"]["analysis"];e=src["eurostat_ai"]["analysis"]
    latest_h=next(x for x in a["same_quarter_year_on_year"] if x["to"]=="2026Q2")
    latest_d=next(x for x in d["comparisons"] if x["to"]=="2026Q3")
    claims=[
      claim("C01","DESCRIPTIVE_COMPARISON","Latest same-quarter headcount comparison; subgroup contributions available in evidence.", "CVS employees and percent","private NACE J employers","2025Q2–2026Q2",["urssaf_headcount"],["M049","M063"],"V1.1 exact sums, guarded same-quarter comparison","Apprentice/DSN breaks and revisions; not occupations.","Demand, AI, mobility, classification","Revision or compatible independent series"),
      claim("C02","DESCRIPTIVE_COMPARISON","Latest corrected DPAE annual comparison and subgroup changes.","CVS-CJO declarations and percent","private general scheme excluding temporary agency work, NACE J","2025Q3–2026Q3",["urssaf_dpae"],["M049","M063"],"V1.2 pinned correction only","Declarations are not hires; correction residual unknown.","Demand, composition, recruitment policy","New vintage and independent realized flow data"),
      claim("C03","OBSERVATION","Reported AI adoption levels only; changes not admitted.","percent enterprises","NACE J enterprises >=10 persons employed","2023–2025",["eurostat_ai"],["M029","M063"],"Native selectors and annual levels","2023 break, 2025 basket change","Survey composition and definition","Compatible official bridge"),
      claim("C04","CONDITIONAL_SCENARIO","Direct work-time saving alone does not determine paid hours, profit or demand; signs depend on declared scenarios.","normalized units, EUR, hours","two fictional service sellers","one quarter and 12-quarter NPV",["scenario_receipt"],sorted(M_HYP),"G3 allocation, exact cash bridge and explicit parameter grid","Equal quality assumed; no sector calibration or jobs forecast","Low demand, wage retention, capacity and competition","Measured process time, quality, costs, demand and financing"),
      claim("C05","NON_IDENTIFIABLE","No AI-attributable employment effect identified.","not quantifiable","NACE J employers","2019–2026",["urssaf_headcount","urssaf_dpae","eurostat_ai"],["M060","M061","M064"],"Separate observations and scenario, no joint exposure panel","No causal design, no independent microdata","Cycle, offshoring, finance, labor supply, AI complementarity/substitution","Admitted matched panel, competing model and pretrend tests")]
    required=set(readreg("investigation_result_v1.json")["claim_required"])
    require(all(required<=set(c) for c in claims),"CLAIM_FIELDS")
    section_data={
      "D01":("PARTIAL","France NACE J, 2019–2026; identify discriminating evidence and decision thresholds, not a sector employment forecast.",["C01","C02","C04"]),
      "D02":("PARTIAL","Latest observations in evidence; opposite conditional results on hours and value capture.",["C01","C02","C04"]),
      "D03":("PARTIAL","Three sources, two families, fixed source hashes; scope and breaks retained.",["C01","C02","C03"]),
      "D04":("BLOCKED","No independently measured technical capacity/quality for sector tasks.",[]),
      "D05":("PARTIAL","Conditional active vs paid hours; no occupation weights, juniors or observed skill flows.",["C04"]),
      "D06":("PARTIAL","Refonte represented by lower assumed direct time and coordination; no new sector process simulation.",["C04"]),
      "D07":("PARTIAL","Scoped cash ledger, unit cost, conditional NPV; no full firm finance or balance sheet.",["C04"]),
      "D08":("PARTIAL","Fixed basket prices, demand response, bounded capacity; no calibrated market or competition dynamics.",["C04"]),
      "D09":("BLOCKED","No calibrated sector/territory production network or sourcing links for the normalized service.",[]),
      "D10":("PARTIAL","Observed headcounts and DPAE separately; conditional hours, not macro employment or income closure.",["C01","C02","C04"]),
      "D11":("PARTIAL","Exact revenue/cash incidence bridge; no economic rents, consumer surplus or GDP.",["C04"]),
      "D12":("PARTIAL","O1 direct time/cost; O2 price/quantity; O3 conditional payroll/receipts; feedback O4+ blocked. Orders describe path, not time or causal proof.",["C04"]),
      "D13":("PARTIAL","Eight named alternatives and 21 elasticity/pass-through cases, baseline and threshold.",["C04"]),
      "D14":("PARTIAL","Source observations and causal non-identification; OEM replication blocked.",["C01","C02","C03","C05"]),
      "D15":("PARTIAL","Proposed signals: realized hires, exits, hours, sector turnover, price and exposure panel. No validated warning score.",["C05"]),
      "D16":("PARTIAL","Measure demand, quality and paid-time adjustment before automating or assuming job reductions; conditional thresholds only.",["C04","C05"]),
      "D17":("PARTIAL","All registry entries checked for scoped disposition; competing explanations and next evidence. No global validation.",["C05"]),
      "D18":("PARTIAL","Source hashes, registry hashes, scenario receipt, code hash and exact computations; durable private raw archive and rights pending.",["C01","C02","C03","C04"])}
    sections=[{"id":s["id"],"title":s["title"],"status":section_data[s["id"]][0],"content":section_data[s["id"]][1],"claim_refs":section_data[s["id"]][2]} for s in readreg("investigation_result_v1.json")["sections"]]
    require(len(sections)==18,"SECTIONS")
    cov=coverage()
    payload={"study":"VERTICAL-001","phase":"V2a","publication":"BLOCK_PUBLICATION","causal_identification":"NOT_IDENTIFIED",
       "overview":{"claim_refs":["C01","C02","C04","C05"],"observation_refs":["latest_headcount","latest_dpae"],"scenario_ref":"scenario_receipt"},
       "sections":sections,"claims":claims,"coverage":cov,"observations":{"latest_headcount":latest_h,"latest_dpae":latest_d,"source_native":src},
       "scenario_receipt":sim,"registry_sha256":{p:digest((ROOT/"governance"/p).read_bytes()) for p in REGISTRIES},
       "code_sha256":{p:digest((ROOT/"pipeline"/p).read_bytes()) for p in ("vertical_v2.py","vertical_scenarios.py","vertical_v1.py","vertical_v11.py","vertical_v12.py","economic_market.py")},
       "cross_source_numeric_join":False,"sector_calibrated_scenario":False,"oem_comparator":"BLOCKED_MISSING_DATA"}
    return {"result":payload,"sha256":cdigest(canonical(payload))}
def summary(r):
    p=r["result"];s=p["scenario_receipt"]["result"]
    return {"study":p["study"],"phase":p["phase"],"publication":p["publication"],"causal_identification":p["causal_identification"],
       "section_count":len(p["sections"]),"claim_count":len(p["claims"]),"coverage_count":len(p["coverage"]),
       "coverage_dispositions":{k:sum(x["disposition"]==k for x in p["coverage"]) for k in sorted({x["disposition"] for x in p["coverage"]})},
       "sources":{k:v["sha256"] for k,v in p["observations"]["source_native"].items()},
       "synthetic_only_scenarios":[{k:x[k] for k in ("id","quantity","price_eur","paid_hours_delta","cash_surplus_delta_eur","incremental_npv_eur","simple_direct_time_comparator_delta_hours")} for x in s["scenarios"]],
       "sensitivity_count":len(s["sensitivity"]),"result_sha256":r["sha256"],"scenario_sha256":p["scenario_receipt"]["sha256"],
       "registry_sha256":p["registry_sha256"],"code_sha256":p["code_sha256"]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--internal-output",type=Path);args=p.parse_args()
    if args.internal_output:
        target=args.internal_output.resolve();require(not target.is_relative_to(ROOT),"OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    r=build(make_observations())
    if args.internal_output:
        with os.fdopen(os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print("VERTICAL_V2 "+json.dumps(summary(r),ensure_ascii=False))
if __name__=="__main__":main()
