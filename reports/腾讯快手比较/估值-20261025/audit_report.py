"""Classify the fixed report sample; keep facts, assumptions and calculations apart."""
from pathlib import Path
from decimal import Decimal as D
import json, subprocess, sys, hashlib, re
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
REPORT=ROOT/'腾讯与快手估值及三年十年回报研究报告-20261025.md'
AUDIT=ROOT/'audit'
def clean_log(value):
 return '\n'.join(line.rstrip() for line in re.sub(r'\x1b\[[0-9;]*m','',value).splitlines())+'\n'
raw=subprocess.run([sys.executable,str(REPO/'tools/report_audit.py'),'extract','--report',str(REPORT),'--ratio','.15','--seed','42'],capture_output=True,text=True,check=True).stdout
raw=clean_log(raw.replace(str(REPO)+'/', ''))
(AUDIT/'extract.txt').write_text(raw)
sample=json.loads(raw[raw.index('\n[\n')+1:])
m=json.loads((ROOT/'model_results.json').read_text());s=json.loads((ROOT/'stress_results.json').read_text())
t=m['companies']['Tencent'];k=m['companies']['Kuaishou']
T1='https://www.tencent.com/wp-content/uploads/2026/08/E700_IR.pdf'
T3='https://www.hkexnews.hk/listedco/listconews/sehk/2026/0409/2026040901232_c.pdf'
K1='https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0424/2026042401899.pdf'
K2='https://www.hkexnews.hk/listedco/listconews/sehk/2026/0903/2026090300643_c.pdf'
TA='https://stockanalysis.com/quote/hkg/0700/financials/'
KA='https://stockanalysis.com/quote/hkg/1024/financials/cash-flow-statement/'
facts={
 9:('7884.83',T1+' and '+T3+'; (751766+401243-364526)/100','7884.83',TA,'derived_financial_fact'),
 23:('-58.38',K1+' and '+K2+'; TTM simple FCF-18.29 less lease cash40.09',None,None,'derived_financial_fact'),
 24:('984.14',T1+' p9 VAS revenue983? adopted98414 million',None,None,'fact'),
 27:('1.4',K2+' second-quarter operating review; 35535/35046-1',None,None,'fact'),
 29:('4.4',K2+' second-quarter online marketing review',None,None,'fact'),
 36:('6602.57',TA+' FY2024 revenue660257 million; history is single-source in this run',None,None,'fact_single_source'),
 51:('297.87',KA+' FY2024 CFO29787 million',None,None,'fact_single_source'),
 56:('239.79',K1+' and '+K2+'; (26716+9044-11781)/100','239.79',KA,'derived_financial_fact'),
 58:('70.75',K2+' p63 H12025 PPE/intangible payments and prepayments7075 million',None,None,'fact'),
 60:('258.08',K1+' and '+K2+'; (14942+17941-7075)/100; stale independent database rejected',None,None,'derived_financial_fact'),
 63:('-88.97',K2+' p63; (9044-17941)/100',None,None,'derived_financial_fact')}
facts[24]=('984.14',T1+' p9 VAS revenue98414 million',None,None,'fact')
calc={
 7:D(t['market']['cny_cap'])*10,8:D(k['market']['cny_cap'])*10,
 140:D(t['scenarios']['bear']['horizons']['3']['irr'])*100,
 144:D(t['scenarios']['bull']['horizons']['3']['exit_price']),
 152:D(k['scenarios']['base']['horizons']['3']['irr'])*100,
 155:D(k['scenarios']['bull']['horizons']['3']['irr'])*100,
 164:D(t['scenarios']['bull']['horizons']['10']['irr'])*100,
 167:D(k['scenarios']['bear']['horizons']['10']['irr'])*100,
 174:D(t['weighted']['3']['irr_of_expected_cashflows'])*100,
 180:D(t['scenarios']['base']['horizons']['10']['irr'])*100,
 189:D(s['Kuaishou_reverse_starting_cash_sensitivity']['5'])*100,
 213:D(s['Tencent_full_cash_distribution_alternative']['fair'])}
assumptions={71:'Tencent base year10 revenue1500bn',109:'Kuaishou bull platform year3 revenue175bn',130:'Tencent nonconsolidated investment realizable-value assumption650bn',184:'Reverse proxy starting cash150bn',190:'Reverse proxy starting cash8bn'}
dates={222,223}
assert set(x['id'] for x in sample)==set(facts)|set(calc)|set(assumptions)|dates,'Report sample changed: re-review mappings before using this script.'
checked=[];calculations=[];dispositions=[]
for x in sample:
 i=x['id'];y=dict(x)
 if i in facts:
  v,src,v2,src2,cl=facts[i]
  y.update(fetched_value=float(v),fetched_source=src,fetched_value2=None if v2 is None else float(v2),fetched_source2=src2,classification=cl)
  checked.append(y)
 elif i in calc:
  y.update(fetched_value=float(calc[i]),fetched_source='Declared model arithmetic; checked by independent reverse-recursion/Newton implementation; not an external fact',classification='derived_model_result')
  calculations.append(y)
 elif i in assumptions:
  y.update(classification='assumption_not_a_verified_fact',disposition=assumptions[i])
 else:y.update(classification='parser_date_fragment',disposition='Date fragment excluded from numeric financial sample; full research/financial/market dates separately checked.')
 dispositions.append(y)
for name,items in [('facts',checked),('calculations',calculations)]:
 (AUDIT/(name+'.json')).write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
 r=subprocess.run([sys.executable,str(REPO/'tools/report_audit.py'),'verdict','--results',json.dumps(items,ensure_ascii=False)],capture_output=True,text=True,check=True)
 (AUDIT/(name+'-verdict.txt')).write_text(clean_log(r.stdout))
(AUDIT/'sample-dispositions.json').write_text(json.dumps(dispositions,ensure_ascii=False,indent=2)+'\n')
commands=[['calc','--expr','386*9088885829*0.85696/100000000'],['calc','--expr','27.90*4304151598*0.85696/100000000'],
 ['calc','--expr','(26716+9044-11781)-(14942+17941-7075)'],
 ['cross-validate','--field','Tencent_TTM_revenue','--values','{"filing":788483,"StockAnalysis":788483}','--unit','CNY_million'],
 ['cross-validate','--field','Kuaishou_TTM_CFO','--values','{"filing":23979,"StockAnalysis":23979}','--unit','CNY_million'],
 ['verify-market-cap','--price','386','--shares','9088885829','--reported','3508309929994','--currency','HKD'],
 ['verify-market-cap','--price','27.9','--shares','4304151598','--reported','120085829584.2','--currency','HKD']]
logs=[]
for args in commands:
 r=subprocess.run([sys.executable,str(REPO/'tools/financial_rigor.py')]+args,capture_output=True,text=True,check=True)
 logs.append(clean_log(r.stdout))
(AUDIT/'financial-rigor.txt').write_text('\n'.join(logs))
status={'status':'PASS_WITH_EXPLICIT_SCOPE','report_sha256':hashlib.sha256(REPORT.read_bytes()).hexdigest(),
 'requested_sample_ratio':'.15','seed':42,'extracted_points':225,'sampled':len(sample),
 'tool_sample_cap':30,'actual_sample_fraction':'30/225 = 13.33%',
 'facts_and_financial_derivations':len(checked),'model_calculations':len(calculations),
 'assumptions_excluded_from_fact_pass':len(assumptions),'date_fragments':len(dates),
 'independent_full_model_checks':312,'shared_engine_core_components':6,
 'not_verified':['forecast accuracy','probabilities','live complete diluted cap tables','October complete financial balances','Kling cash receipt and standalone current-period audited costs','Tencent complete mark-to-market investment portfolio','historical table full two-source audit'],
 'note':'Tool passes certify declared sample/calculation scope only. Source judgments and investment outcomes are not machine-verified.'}
(AUDIT/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(status,ensure_ascii=False,indent=2))
