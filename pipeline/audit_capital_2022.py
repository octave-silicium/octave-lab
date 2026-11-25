"""G4 v0.7b: audited 2022 capital stock/flow diagnostic; not capacity calibration.
Replays pinned partial archive; separate replacement-cost and volume comparisons."""
import csv,io,json,hashlib,sys,zipfile,math
from decimal import Decimal as D
from pathlib import Path
import openpyxl

HASHES={"stocks.zip":"676d19710b1f31828f0a88644e9ec9f46ac705fb855742fe04bffa772a4cd622","fbcf.xlsx":"6f4a513a90a7e37f701cfcb7dcaebcd34f7d37c1ddc17260720d8c8eb30fa164","ccf.xlsx":"16e345a7fccb120c68d2332a4920d612e999dbf5033cd0a893bd99d07cb816df","eu_stocks.json":"b2a299aea8429b26b869cdcb594472f55f2bfb5c8524c8a8b849d88a7e92163c"}
CODES="AZ BZ CA CB CC CD CE CF CG CH CI CJ CK CL CM DZ EZ FZ GZ HZ IZ JA JB JC KZ LZ MA MB MC NZ OZ PZ QA QB RZ SZ TZ".split()
FR="A B C10T12 C13T15 C16T18 C19 C20 C21 C22_23 C24_25 C26 C27 C28 C29_30 C31T33 D35 E F G H I J58T60 J61 J62_63 K L M69T71 M72 M73T75 N O84 P85 Q86 Q87_88 R S T".split()
EU="A B C10-C12 C13-C15 C16-C18 C19 C20 C21 C22_C23 C24_C25 C26 C27 C28 C29_C30 C31-C33 D E F G H I J58-J60 J61 J62_J63 K L M69-M71 M72 M73-M75 N O P Q86 Q87_Q88 R S T".split()
XLS="A5_AZ A38_BZ A17_C1 A38_CB A38_CC A17_C2 A38_CE A38_CF A38_CG A38_CH A38_CI A38_CJ A38_CK A17_C4 A38_CM A38_DZ A38_EZ A5_FZ A17_GZ A17_HZ A17_IZ A38_JA A38_JB A38_JC A10_KZ A10_LZ A38_MA A38_MB A38_MC A38_NZ A38_OZ A38_PZ A38_QA A38_QB A38_RZ A38_SZ A38_TZ".split()
ASSETS="N11N N11G N1132N N1132G N1173N N1173G N1171N N1171G N111N N111G N117N N117G".split()
def req(x,msg):
    if not x:raise ValueError(msg)
def dec(x):
    v=D(str(x));req(v.is_finite(),"FINITE");return v
def read_source(folder,name):
    raw=(Path(folder)/name).read_bytes();req(hashlib.sha256(raw).hexdigest()==HASHES[name],"HASH:"+name);return raw
def flow(raw,sheet,year):
    sh=openpyxl.load_workbook(io.BytesIO(raw),read_only=True,data_only=True)[sheet];a=list(sh.values)
    req(str(a[1][0]).startswith("Unité : Milliard d'euros"),"UNIT")
    col=a[3].index(str(year));lookup={row[0]:(i+1,row[col]) for i,row in enumerate(a) if row[0] in XLS+["_T"]}
    req(len(lookup)==38,"BRANCH_AXIS")
    return {k:{"cell":sh.cell(i,col+1).coordinate if v is not None else None,"value_MEUR":None if v is None else dec(v)*1000} for k,(i,v) in lookup.items()}
def eu_cell(e,keys):
    dims=e["id"];req(set(dims)==set(keys),"JSONSTAT_SCOPE")
    i=0
    for k,n in zip(dims,e["size"]):
        idx=e["dimension"][k]["category"]["index"];req(len(idx)==n and keys[k] in idx,"JSONSTAT_AXIS")
        i=i*n+idx[keys[k]]
    loc=str(i);v=e["value"].get(loc)
    return (None if v is None else dec(v),e.get("status",{}).get(loc))
def run(folder):
    src={name:read_source(folder,name) for name in HASHES}
    with zipfile.ZipFile(io.BytesIO(src["stocks.zip"])) as z:
        req(z.testzip() is None and sum(x.file_size for x in z.infolist())<100_000_000,"ZIP")
        metadata=list(csv.DictReader(io.StringIO(z.read("DD_CNA_CAPITAL_FIXE_metadata.csv").decode("utf-8-sig")),delimiter=";"))
        rows=list(csv.DictReader(io.StringIO(z.read("DD_CNA_CAPITAL_FIXE_data.csv").decode("utf-8-sig")),delimiter=";"))
    req(len(rows)==160100,"ROW_COUNT")
    for k,v in {"REF_SECTOR":"S1","COUNTERPART_AREA":"W0","ACCOUNTING_ENTRY":"D","STO":"LE","UNIT_MEASURE":"XDC","UNIT_MULT":"6","FREQ":"A","TRANSFORMATION":"N","PRODUCT":"_T","EXPENDITURE":"_Z"}.items():
        req(all(r[k]==v for r in rows),"SCOPE:"+k)
    labels={(x["COD_VAR"],x["COD_MOD"]):x["LIB_MOD"] for x in metadata}
    req(labels["PRICES","U"]=="Au coût de remplacement" and "chaînés" in labels["PRICES","LFA"],"PRICE_SCOPE")
    q={};years=set()
    for r in rows:
        years.add(int(r["TIME_PERIOD"]))
        if r["TIME_PERIOD"]!="2022":continue
        k=(r["ACTIVITY"],r["INSTR_ASSET"],r["PRICES"])
        req(k not in q and r["OBS_STATUS_FR"]=="D","DUPLICATE_OR_VINTAGE")
        q[k]=dec(r["OBS_VALUE"])
        req(q[k]>=0,"STOCK_SIGN")
    req(len(q)==2448 and min(years)==1959 and max(years)==2025,"YEAR_SCOPE")
    pairs=0
    for (a,k,p),v in q.items():
        g=(a,k[:-1]+"G",p)
        if p=="U" and k.endswith("N") and g in q:
            req(v<=q[g],"NET_GT_GROSS");pairs+=1
    aggs=[]
    for asset in ("N11N","N11G","N1132N","N1173N","N1171N"):
        vals=[q[(a,asset,"U")] for a in FR]
        error=sum(vals)-q["_T",asset,"U"];req(error==0,"STOCK_AGG:"+asset)
        aggs.append({"asset":asset,"residual_MEUR":str(error)})
    e=json.loads(src["eu_stocks.json"],parse_float=D)
    comparisons={};missing=[]
    for unit,p in [("CRC_MEUR","U"),("CLV20_MEUR","LFA")]:
        obs=[]
        for a,b in zip(FR+["_T"],EU+["TOTAL"]):
            for k in ASSETS:
                v=q.get((a,k,p));x,flag=eu_cell(e,{"freq":"A","unit":unit,"nace_r2":b,"asset10":k,"geo":"FR","time":"2022"})
                if v is None or x is None:
                    missing.append({"unit":unit,"branch":a,"asset":k,"insee":v,"eurostat":x});continue
                obs.append({"branch":a,"asset":k,"insee":v,"eurostat":x,"difference":v-x,"flag":flag})
        comparisons[unit]={"count":len(obs),"exact":sum(x["difference"]==0 for x in obs),"max_absolute_difference":max(abs(x["difference"]) for x in obs),"rows":obs}
    req(comparisons["CRC_MEUR"]["count"]==450 and comparisons["CRC_MEUR"]["exact"]==450,"REPLACEMENT_COST_MATCH")
    # Volume differences are a blocked scope, never made equal by rescaling.
    req(comparisons["CLV20_MEUR"]["count"]==370 and comparisons["CLV20_MEUR"]["exact"]==1,"VOLUME_DIAGNOSTIC")
    f=flow(src["fbcf.xlsx"],"T_6301 en niveau",2022);c=flow(src["ccf.xlsx"],"T_6461",2022)
    fv=flow(src["fbcf.xlsx"],"T_6302 en niveau",2022);cv=flow(src["ccf.xlsx"],"T_6462",2022)
    # TEE verified national totals from audit_tee_2022: billion EUR, converted.
    req(f["_T"]["value_MEUR"]==D("623312") and c["_T"]["value_MEUR"]==D("497833"),"TEE_TOTALS")
    req(c["A38_TZ"]["value_MEUR"] is None,"TZ_MISSING")
    branch=[]
    for k,a,x in zip(CODES,FR,XLS):
        n=q[a,"N11N","U"];g=q[a,"N11G","U"];i=f[x]["value_MEUR"];d=c[x]["value_MEUR"]
        branch.append({"code":k,"stock_activity":a,"flow_activity":x,"stock_net":n,"stock_gross":g,"ict_net":q[a,"N1132N","U"],"software_net":q[a,"N1173N","U"],"rd_net":q[a,"N1171N","U"],"fbcf":i,"ccf":d,"fbcf_chain":fv[x]["value_MEUR"],"ccf_chain":cv[x]["value_MEUR"],"net_formation":None if i is None or d is None else i-d,"fbcf_over_closing_gross_stock":None if not g or i is None else i/g,"ccf_over_closing_gross_stock":None if not g or d is None else d/g})
    result={"status":"EMPIRICAL_CAPITAL_DIAGNOSTIC_PARTIAL","publication":"BLOCK_PUBLICATION","source_hashes":HASHES,"years":[min(years),max(years)],"source_observations":len(rows),"observations_2022":len(q),"gross_net_pairs_checked":pairs,"stock_aggregations":aggs,"stock_comparisons":comparisons,"missing_comparisons":missing,"eurostat_updated":e.get("updated"),"branch_rows":branch,"national":{"net_stock":q["_T","N11N","U"],"gross_stock":q["_T","N11G","U"],"dwellings_net":q["_T","N111N","U"],"ict_net":q["_T","N1132N","U"],"software_net":q["_T","N1173N","U"],"rd_net":q["_T","N1171N","U"],"ip_net":q["_T","N117N","U"],"fbcf":f["_T"]["value_MEUR"],"ccf":c["_T"]["value_MEUR"],"net_formation":f["_T"]["value_MEUR"]-c["_T"]["value_MEUR"]},"limitations":["replacement costs not physical productive capacity or historical cost","stocks and flows valuation differ; ratios descriptive not depreciation rates","chain-linked volumes not additive, cross-source differences unresolved","asset-specific FBCF/CCF missing from this qualified scope; no automated AI-capital classification","TZ CCF missing, no imputation; no implied bilateral asset purchases, survival curves or causal estimates","no empirical admission"]}
    return result
if __name__=="__main__":
    print(json.dumps(run(sys.argv[1]),ensure_ascii=False,indent=2,default=str))
