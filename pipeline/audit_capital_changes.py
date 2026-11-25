"""G4 v0.7c: pinned stock normalisation and wealth-change diagnostic; no admission."""
import csv,io,json,hashlib,sys,zipfile,statistics
from decimal import Decimal as D
from pathlib import Path
import openpyxl

HASHES={"stocks.zip":"676d19710b1f31828f0a88644e9ec9f46ac705fb855742fe04bffa772a4cd622","fbcf.xlsx":"6f4a513a90a7e37f701cfcb7dcaebcd34f7d37c1ddc17260720d8c8eb30fa164","ccf.xlsx":"16e345a7fccb120c68d2332a4920d612e999dbf5033cd0a893bd99d07cb816df","eu_stocks.json":"b2a299aea8429b26b869cdcb594472f55f2bfb5c8524c8a8b849d88a7e92163c","eu_branch_flows.json":"c4fb044e4de5a6dc5f91b98fa23b9f927275d1cfc8e9c85e87b29df22d40cd44","eu_income.json":"5c822d35fed4fa677d215a958be4730679168700a71d523d8479fb0c24608772","wealth_8211.xlsx":"aee8ad20b78f2fb5f3410ba90ff936995fab60af2f539177e8b03ea37915cc0a","wealth_8212.xlsx":"746b51b1804fc136ae505e42f803e5330ecae6e275e899ce9bf01c613ec306f9","wealth_8213.xlsx":"4e40c8f53735972bfa3e07cda24b078ea43d9810a0c71a0c80757fa4d880c979","wealth_8214.xlsx":"e7fe82d05e67fb57e2d570df4f54ebeb1b8e5f860f8a6b054d1b374c8268e8b7","wealth_8220.xlsx":"d42fd8a2b8591b36337d819d97d0333ef5ad86eef8cd107e3cd3a2f34b663323","wealth_investment.xlsx":"c5d5dc689c844183e4a0f3ace3a783d8d413805e180d0f05a78fcfb2d9898ea9","eu_stock_bridge.json":"3bdeac7504189f57c489e79bde0cfcc67132a464366143af9f817247b4e0ad7f"}
FR="A B C10T12 C13T15 C16T18 C19 C20 C21 C22_23 C24_25 C26 C27 C28 C29_30 C31T33 D35 E F G H I J58T60 J61 J62_63 K L M69T71 M72 M73T75 N O84 P85 Q86 Q87_88 R S T _T".split()
EU="A B C10-C12 C13-C15 C16-C18 C19 C20 C21 C22_C23 C24_C25 C26 C27 C28 C29_C30 C31-C33 D E F G H I J58-J60 J61 J62_J63 K L M69-M71 M72 M73-M75 N O P Q86 Q87_Q88 R S T TOTAL".split()
XLS="A5_AZ A38_BZ A17_C1 A38_CB A38_CC A17_C2 A38_CE A38_CF A38_CG A38_CH A38_CI A38_CJ A38_CK A17_C4 A38_CM A38_DZ A38_EZ A5_FZ A17_GZ A17_HZ A17_IZ A38_JA A38_JB A38_JC A10_KZ A10_LZ A38_MA A38_MB A38_MC A38_NZ A38_OZ A38_PZ A38_QA A38_QB A38_RZ A38_SZ A38_TZ _T".split()
ASSETS="N11N N11G N1132N N1132G N1173N N1173G N1171N N1171G N111N N111G N117N N117G".split()
def req(x,msg):
    if not x:raise ValueError(msg)
def dec(v):
    x=D(str(v));req(x.is_finite(),"NONFINITE");return x
def cell(e,**keys):
    req(set(e['id'])==set(keys),'AXES');i=0
    for k,n in zip(e['id'],e['size']):i=i*n+e['dimension'][k]['category']['index'][keys[k]]
    v=e['value'].get(str(i));return None if v is None else dec(v)
def stock(e,a,k,u,t):return cell(e,freq='A',unit=u,nace_r2=a,asset10=k,geo='FR',time=str(t))
def workbook(raw,s):return openpyxl.load_workbook(io.BytesIO(raw),read_only=True,data_only=True)[s]
def flow(raw,s):
    a=list(workbook(raw,s).values);req(a[1][0]=="Unité : Milliard d'euros",'UNIT');j=a[3].index('2022')
    return {r[0]:None if r[j] is None else dec(r[j])*1000 for r in a if r[0] in XLS}
def run(old,new):
    src={}
    for n,h in HASHES.items():
        p=(Path(new) if n.startswith('wealth_') or n=='eu_stock_bridge.json' else Path(old))/n
        raw=p.read_bytes();req(hashlib.sha256(raw).hexdigest()==h,'HASH:'+n);src[n]=raw
    q={}
    with zipfile.ZipFile(io.BytesIO(src['stocks.zip'])) as z:
        for r in csv.DictReader(io.StringIO(z.read('DD_CNA_CAPITAL_FIXE_data.csv').decode('utf-8-sig')),delimiter=';'):
            if r['TIME_PERIOD'] not in ('2020','2021','2022'):continue
            k=(r['ACTIVITY'],r['INSTR_ASSET'],r['PRICES'],r['TIME_PERIOD']);req(k not in q,'DUPLICATE');q[k]=dec(r['OBS_VALUE'])
    e=json.loads(src['eu_stocks.json'],parse_float=D);b=json.loads(src['eu_stock_bridge.json'],parse_float=D)
    rows=[];missing=[];growth=[];anchor=[];chain=[]
    for a,ea in zip(FR,EU):
        for k in ASSETS:
            def get(p,t):return q.get((a,k,p,str(t)))
            for unit in ('CRC_MEUR','CLV20_MEUR','PYR_MEUR'):
                req(stock(e,ea,k,unit,2022)==stock(b,ea,k,unit,2022),'SNAPSHOT_2022_DRIFT')
            u,v,x,y=get('U',2020),get('LFA',2020),get('LFA',2022),stock(e,ea,k,'CLV20_MEUR',2022)
            if any(z is None for z in (u,v,x,y)) or v==0:
                missing.append([a,k]);continue
            re=x*u/v;rows.append({'branch':a,'asset':k,'insee_2022':x,'eurostat_2022':y,'insee_2020_current':u,'insee_2020_volume':v,'rebased':re,'raw_error':x-y,'rebased_error':re-y})
            c20=stock(b,ea,k,'CRC_MEUR',2020);c21=stock(b,ea,k,'CRC_MEUR',2021);l20=stock(b,ea,k,'CLV20_MEUR',2020);l21=stock(b,ea,k,'CLV20_MEUR',2021)
            p21=stock(b,ea,k,'PYR_MEUR',2021);p22=stock(b,ea,k,'PYR_MEUR',2022)
            if c20 is not None and l20 is not None:anchor.append({'branch':a,'asset':k,'insee_current_minus_eu_current':u-c20,'eu_clv_minus_current':l20-c20})
            if all(z is not None and z>0 for z in (c20,c21,p21,p22,l20,l21)):
                reconstructed=l20*p21/c20*p22/c21
                chain.append({'branch':a,'asset':k,'eu_chain_replay':reconstructed,'eu_reported':y,'error':reconstructed-y})
            for t,lv0,lv1 in [(2021,l20,l21),(2022,l21,y)]:
                iv0,iv1=get('LFA',t-1),get('LFA',t)
                if all(z is not None and z>0 for z in (lv0,iv0)) and iv1 is not None and lv1 is not None:
                    growth.append({'branch':a,'asset':k,'year':t,'insee_growth':iv1/iv0-1,'eurostat_growth':lv1/lv0-1,'difference_pp':100*(iv1/iv0-lv1/lv0)})
    req(len(rows)==370,'COVERAGE');req(sum(abs(r['rebased_error'])<abs(r['raw_error']) for r in rows)==367,'REBASE_REPLAY')
    wealth=[]
    for n,s in [(8211,'S1'),(8212,'S11'),(8213,'S12'),(8214,'S13'),(8220,'S14')]:
        ws=workbook(src[f'wealth_{n}.xlsx'],f'T_{n}');a=list(ws.values)
        req(a[1][0]=="Unité : Milliard d'euros",'WEALTH_UNIT')
        keys=[('2021',"Patrimoine en fin d'année"),('2022','Flux d’actifs'),('2022','Consommation de capital fixe'),('2022','Réévaluation'),('2022','Autres changements de volume et ajustements'),('2022',"Patrimoine en fin d'année")]
        js=[list(zip(a[3],a[4])).index(key) for key in keys]
        for row in a[8:24]:
            k=row[0];req(isinstance(k,str) and k.startswith('N11'),'ASSET_AXIS')
            vals=[None if row[j] is None else dec(row[j])*1000 for j in js]
            if vals[0] is None or vals[-1] is None:continue
            residual=vals[-1]-sum(x for x in vals[:-1] if x is not None)
            wealth.append(dict(zip(('opening','investment','ccf_signed','revaluation','other_changes','closing'),vals),sector=s,asset=k,residual_after_reported_components=residual,missing_components=[name for name,x in zip(('opening','investment','ccf_signed','revaluation','other_changes','closing'),vals) if x is None],status='UNRESOLVED_OR_UNREPORTED' if abs(residual)>3 else 'WITHIN_ROUNDING_OR_UNREPORTED'))
    n=next(r for r in wealth if r['sector']=='S1' and r['asset']=='N11');req(n['residual_after_reported_components']==D('-117'),'NATIONAL_RESIDUAL');req(n['investment']==623312 and n['ccf_signed']==-497833,'TEE_FLOW')
    for r in wealth:
        if r['sector']=='S1':
            for name,t in [('opening',2021),('closing',2022)]:
                v=q.get(('_T',r['asset']+'N','U',str(t)))
                if v is not None:req(abs(r[name]-v)<=D('0.5'),'WEALTH_STOCK:'+r['asset'])
    f=flow(src['fbcf.xlsx'],'T_6301 en niveau');c=flow(src['ccf.xlsx'],'T_6461');ef=json.loads(src['eu_branch_flows.json'],parse_float=D);ec=json.loads(src['eu_income.json'],parse_float=D)
    flows=[]
    for a,x in zip(EU,XLS):
        for name,iv,ev in [('FBCF',f[x],cell(ef,freq='A',unit='CP_MEUR',nace_r2=a,asset10='N11G',na_item='P51G',geo='FR',time='2022')),('CCF',c[x],cell(ec,freq='A',unit='CP_MEUR',nace_r2=a,na_item='P51C',geo='FR',time='2022'))]:
            diff=None if iv is None or ev is None else iv-ev
            if diff is not None:req(abs(diff)<=D('.5'),'FLOW_COMPARE')
            flows.append({'branch':a,'item':name,'insee':iv,'eurostat':ev,'difference':diff})
    inv=list(workbook(src['wealth_investment.xlsx'],'T_8221 à prix courants').values);j=inv[3].index('2022');assetflows=[]
    for r in inv:
        if r[0] not in ('N11G','N111G','N1132G','N117G','N1171G','N1173G'):continue
        v=dec(r[j])*1000;u=cell(ef,freq='A',unit='CP_MEUR',nace_r2='TOTAL',asset10=r[0],na_item='P51G',geo='FR',time='2022');req(abs(v-u)<=D('.5'),'ASSET_FLOW')
        assetflows.append({'asset':r[0],'insee':v,'eurostat':u,'difference':v-u})
    return {'status':'CAPITAL_CHANGE_DIAGNOSTIC_NOT_ADMISSION','publication':'BLOCK_PUBLICATION','source_hashes':HASHES,'units':'MEUR; growth differences in percentage points','rebase':rows,'missing':missing,'anchors':anchor,'growth':growth,'chain':chain,'wealth':wealth,'flow_comparisons':flows,'asset_flows':assetflows,'summary':{'rebase_count':len(rows),'improved':sum(abs(r['rebased_error'])<abs(r['raw_error']) for r in rows),'median_before':statistics.median(abs(r['raw_error']) for r in rows),'median_after':statistics.median(abs(r['rebased_error']) for r in rows),'max_after':max(abs(r['rebased_error']) for r in rows),'growth_count':len(growth),'max_growth_difference_pp':max(abs(r['difference_pp']) for r in growth),'chain_count':len(chain),'max_chain_error':max(abs(r['error']) for r in chain),'wealth_rows':len(wealth),'wealth_residuals_over_3_MEUR':sum(abs(r['residual_after_reported_components'])>3 for r in wealth),'flow_count':sum(r['difference'] is not None for r in flows),'asset_flow_count':len(assetflows)},'limitations':['reanchoring is a diagnostic not official series replacement; growth differences remain','blank other changes not imputed; residual not labelled as observed other changes','S15 not acquired separately; institutional-to-branch mapping unknown','CCF by asset available at national/institutional scope only; no survival or service-capacity estimates']}
if __name__=='__main__':print(json.dumps(run(*sys.argv[1:]),ensure_ascii=False,indent=2,default=str))
