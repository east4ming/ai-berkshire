"""Standalone Decimal SOTP and holding-period model. CNY bn, shares bn.

Forecast years are full 12-month periods after 2026-10-23, not fiscal years.
No external packages or unpublished repository tools are required to reproduce.
"""
from decimal import Decimal as D, getcontext
from pathlib import Path
import json
getcontext().prec = 45
ROOT = Path(__file__).resolve().parent

def dec(x):
    return D(str(x))

def interpolate(anchors):
    """Linear economic drivers between explicitly specified years 1, 3, 10."""
    out = []
    for y in range(1, 11):
        lo, hi = (1, 3) if y <= 3 else (3, 10)
        a, b = anchors[str(lo)], anchors[str(hi)]
        out.append({k: dec(a[k]) + (dec(b[k])-dec(a[k]))*D(y-lo)/D(hi-lo) for k in a})
    return out

def schedule(component):
    out = []
    tax, own = dec(component['tax']), dec(component['ownership'])
    for y, row in enumerate(interpolate(component['anchors']), 1):
        ebit = row['revenue'] * row['margin']
        # No artificial cash tax refund on a loss; no unverified loss shield carried.
        cash_tax = max(ebit, D(0)) * tax
        nopat = ebit - cash_tax
        standalone_cf = nopat-row['net_reinvestment']
        # Employee incentive shares are not assumed to fund capital calls.
        funding_share = dec(component.get('loss_funding_share', component['ownership']))
        cf = standalone_cf * (funding_share if standalone_cf < 0 else own)
        out.append(dict(year=y, **row, ebit=ebit, cash_tax=cash_tax,
                        nopat=nopat, standalone_cash_flow=standalone_cf, attributable_fcff=cf))
    return out

def component_value(component, rows, horizon=0, rate_shift=D(0), g_shift=D(0)):
    r, g = dec(component['rate'])+rate_shift, dec(component['g'])+g_shift
    assert r > g
    terminal = rows[-1]['attributable_fcff']*(1+g)/(r-g) if not component.get('shutdown') else D(0)
    pv_exp = sum((x['attributable_fcff']/(1+r)**(x['year']-horizon)
                  for x in rows if x['year'] > horizon), D(0))
    pv_tv = terminal/(1+r)**(10-horizon)
    return dict(explicit_pv=pv_exp, terminal_pv=pv_tv, value=pv_exp+pv_tv,
                terminal_value=terminal, rate=r, terminal_growth=g)

def irr(cashflows):
    def npv(r):
        return sum((c/(1+r)**i for i,c in enumerate(cashflows)),D(0))
    lo, hi = D('-.999'), D('10')
    assert npv(lo) > 0 and npv(hi) < 0
    for _ in range(240):
        mid=(lo+hi)/2
        if npv(mid)>0: lo=mid
        else: hi=mid
    return (lo+hi)/2

def calculate_company(company, fx, rate_shift=D(0), g_shift=D(0)):
    shares, price = dec(company['model_shares']),dec(company['price'])
    results={}
    for name, s in company['scenarios'].items():
        parts=[]
        for c in s['components']:
            rows=schedule(c)
            parts.append(dict(name=c['name'], rows=rows,
                         valuation=component_value(c, rows, rate_shift=rate_shift,g_shift=g_shift)))
        op_value=sum((p['valuation']['value'] for p in parts),D(0))
        bridge=dec(s['bridge'])
        fair=(op_value+bridge)/shares/fx
        # No-buyback neutral capital-allocation case: dividends plus retained cash.
        # Interest is excluded from FCFF, so it is deducted before equity distribution.
        # Debt principal is already in bridge and is rolled at constant nominal principal.
        # Net financing charge excludes income on separately valued financial assets.
        retained=D(0); dividends=[]; cash_ledger=[]; horizons={}
        for y in range(1,11):
            cf=sum((p['rows'][y-1]['attributable_fcff'] for p in parts),D(0))
            equity_cash=cf-dec(company['after_tax_interest'])
            dividend=max(equity_cash,D(0))*dec(company['dividend_payout'])
            retained+=equity_cash-dividend
            div_per_share=dividend/shares/fx
            dividends.append(div_per_share)
            cash_ledger.append(dict(year=y, attributable_fcff=cf,
                equity_cash_after_interest=equity_cash, dividend=dividend,
                retained_cash=retained, shares=shares, net_buybacks=D(0)))
            if y in (3,10):
                future_op=sum((component_value(c,p['rows'],y,rate_shift,g_shift)['value']
                               for c,p in zip(s['components'],parts)),D(0))
                exit_price=max((future_op+bridge+retained)/shares/fx,D(0))
                flows=[-price]+dividends[:]
                flows[-1]+=exit_price
                # No re-rating = initial P/normalized parent FCFF for core value remains.
                # A common starting cash flow is used for all scenarios, not each scenario's trough.
                starting_op=price*shares*fx-bridge
                starting_multiple=starting_op/dec(company['normalized_starting_fcff'])
                no_rerating_op=max(starting_multiple*cf,D(0))
                nr_price=max((no_rerating_op+bridge+retained)/shares/fx,D(0))
                nr_flows=[-price]+dividends[:]
                nr_flows[-1]+=nr_price
                # Price compatible with a 12% personal hurdle, separate from WACC.
                buy_12=sum((v/(D('1.12')**t) for t,v in enumerate(flows[1:],1)),D(0))
                horizons[str(y)]=dict(exit_price=exit_price, cumulative_dividends=sum(dividends),
                    irr=irr(flows), total_wealth_multiple=(exit_price+sum(dividends))/price,
                    price_for_12pct_irr=buy_12, cashflows=flows,
                    no_rerating_exit=nr_price,no_rerating_irr=irr(nr_flows),
                    no_rerating_multiple=starting_multiple, future_operating_value=future_op)
        results[name]=dict(probability=dec(s['probability']),parts=parts,
            operating_value=op_value,bridge=bridge,fair_price=fair,
            terminal_share=sum((p['valuation']['terminal_pv'] for p in parts),D(0))/op_value,
            cash_ledger=cash_ledger,horizons=horizons)
    assert sum((r['probability'] for r in results.values()),D(0))==1
    weighted={}
    for h in ('3','10'):
        flows=[sum((r['probability']*r['horizons'][h]['cashflows'][i] for r in results.values()),D(0))
               for i in range(int(h)+1)]
        weighted[h]=dict(cashflows=flows,irr_of_expected_cashflows=irr(flows),
            expected_terminal_wealth=sum((r['probability']*(r['horizons'][h]['exit_price']+
            r['horizons'][h]['cumulative_dividends']) for r in results.values()),D(0)))
    return dict(scenarios=results,weighted=weighted,
        weighted_fair_price=sum((r['probability']*r['fair_price'] for r in results.values()),D(0)))

def reverse_growth(company, fx):
    """Constant growth in total normalized attributable FCFF; not a profit forecast."""
    s=company['scenarios']['base']; r=dec(company['reverse_rate']);g=dec(company['reverse_g'])
    start=dec(company['normalized_starting_fcff']); bridge=dec(s['bridge'])
    target=dec(company['price'])*dec(company['model_shares'])*fx
    def value(x):
        cf=[start*(1+x)**t for t in range(1,11)]
        return sum((v/(1+r)**t for t,v in enumerate(cf,1)),D(0))+cf[-1]*(1+g)/(r-g)/(1+r)**10+bridge
    lo,hi=D('-.5'),D('.5')
    assert value(lo)<target<value(hi)
    for _ in range(200):
        mid=(lo+hi)/2
        if value(mid)<target:lo=mid
        else:hi=mid
    return dict(growth=(lo+hi)/2,rate=r,g=g,start_fcff=start,
        note='Kuaishou is a simplified consolidated cash-flow proxy, not a split Kling forecast.')

def main():
    data=json.loads((ROOT/'model_inputs.json').read_text())
    fx=dec(data['cny_per_hkd'])
    out={'metadata':data['metadata'],'companies':{},'sensitivity':{}}
    for name,c in data['companies'].items():
        result=calculate_company(c,fx)
        result['reverse_dcf']=reverse_growth(c,fx)
        basic=dec(c['basic_shares']);price=dec(c['price'])
        result['market']=dict(hkd_cap=basic*price,cny_cap=basic*price*fx,
            ifrs_pe=basic*price*fx/dec(c['ttm_ifrs_profit']),
            adjusted_pe=basic*price*fx/dec(c['ttm_adjusted_profit']))
        out['companies'][name]=result
        out['sensitivity'][name]=[]
        for dr in ('-.01','0','.01'):
            for dg in ('-.005','0','.005'):
                changed=calculate_company(c,fx,dec(dr),dec(dg))
                out['sensitivity'][name].append(dict(rate_change=dr,g_change=dg,
                    base_fair=changed['scenarios']['base']['fair_price']))
        print(name, 'fair', {k:round(v['fair_price'],2) for k,v in result['scenarios'].items()},
              'weighted',round(result['weighted_fair_price'],2))
        for k,v in result['scenarios'].items():
            print(k,[(h,round(q['exit_price'],2),round(q['irr']*100,2),
                    round(q['no_rerating_irr']*100,2)) for h,q in v['horizons'].items()])
        print('expected', {h:round(q['irr_of_expected_cashflows']*100,2) for h,q in result['weighted'].items()})
    (ROOT/'model_results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+'\n')

if __name__=='__main__':main()
