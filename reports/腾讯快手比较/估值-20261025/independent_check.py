"""Independent review: reverse-recursive DCF and derivative-based IRR.

Reads inputs and outputs but does not import or execute the primary model.
Values are CNY bn; share counts bn. No network access or third-party packages.
"""
from decimal import Decimal as D, getcontext
from pathlib import Path
from datetime import datetime
import hashlib
import json

getcontext().prec = 60
ROOT = Path(__file__).resolve().parent
ZERO, ONE = D(0), D(1)


def root_irr(flows):
    """Safeguarded Newton iteration, using an independently computed derivative."""
    lo, hi, rate = D('-.999'), D('10'), D('.10')
    for _ in range(300):
        z = ONE + rate
        f = sum((v / z**t for t, v in enumerate(flows)), ZERO)
        if abs(f) < D('1e-48'):
            return rate
        if f > 0:
            lo = rate
        else:
            hi = rate
        derivative = -sum((D(t)*v/z**(t+1) for t,v in enumerate(flows) if t), ZERO)
        trial = rate - f/derivative if derivative else (lo+hi)/2
        rate = trial if lo < trial < hi else (lo+hi)/2
    raise ArithmeticError('Independent IRR failed to converge')


def independently_compute(company, fx):
    shares, price = D(company['model_shares']), D(company['price'])
    result = {}
    for scenario, data in company['scenarios'].items():
        components = []
        for comp in data['components']:
            cf = []
            for year in range(1, 11):
                lower, upper = (1, 3) if year <= 3 else (3, 10)
                weight = D(year-lower)/D(upper-lower)
                a, b = comp['anchors'][str(lower)], comp['anchors'][str(upper)]
                drv = {k: D(a[k])*(ONE-weight) + D(b[k])*weight for k in a}
                operating = drv['revenue']*drv['margin']
                after_tax = operating*(ONE-D(comp['tax'])) if operating > 0 else operating
                standalone = after_tax-drv['net_reinvestment']
                stake = D(comp.get('loss_funding_share',comp['ownership'])) if standalone < 0 else D(comp['ownership'])
                cf.append(standalone*stake)
            rate, growth = D(comp['rate']), D(comp['g'])
            terminal = ZERO if comp.get('shutdown') else cf[-1]*(ONE+growth)/(rate-growth)
            # Future values at each anniversary, calculated from the end backwards.
            values = {10: terminal}
            for year in range(10, 0, -1):
                values[year-1] = (cf[year-1]+values[year])/(ONE+rate)
            components.append({'name':comp['name'], 'cf':cf, 'values':values,
                               'terminal':terminal, 'rate':rate})
        op_value = sum((p['values'][0] for p in components), ZERO)
        bridge = D(data['bridge'])
        fair = (op_value+bridge)/(shares*fx)
        retained, dividends, ledger, horizons = ZERO, [], [], {}
        for year in range(1,11):
            fcff = sum((c['cf'][year-1] for c in components), ZERO)
            equity_cash = fcff-D(company['after_tax_interest'])
            distribution = max(ZERO,equity_cash)*D(company['dividend_payout'])
            retained += equity_cash-distribution
            dividends.append(distribution/(shares*fx))
            ledger.append({'fcff':fcff,'equity_cash':equity_cash,
                           'dividend':distribution,'retained':retained})
            if year in (3,10):
                remaining = sum((c['values'][year] for c in components), ZERO)
                exit_price = max(ZERO,(remaining+bridge+retained)/(shares*fx))
                flows = [-price] + dividends[:]
                flows[-1] += exit_price
                starting_multiple = (price*shares*fx-bridge)/D(company['normalized_starting_fcff'])
                nr_price = max(ZERO,(max(ZERO,starting_multiple*fcff)+bridge+retained)/(shares*fx))
                nr_flows = [-price]+dividends[:]
                nr_flows[-1] += nr_price
                horizons[str(year)] = {'exit':exit_price,'irr':root_irr(flows),
                    'cashflows':flows,'no_rerating_irr':root_irr(nr_flows),
                    'retained':retained,'future_op':remaining}
        result[scenario] = {'probability':D(data['probability']), 'fair':fair,
            'operating_value':op_value,'parts':components,'ledger':ledger,'horizons':horizons}
    weighted = {}
    for h in ('3','10'):
        flows = [sum((s['probability']*s['horizons'][h]['cashflows'][t]
                       for s in result.values()),ZERO) for t in range(int(h)+1)]
        weighted[h] = root_irr(flows)
    return {'scenarios':result,'weighted':weighted}


def main():
    input_bytes = (ROOT/'model_inputs.json').read_bytes()
    result_bytes = (ROOT/'model_results.json').read_bytes()
    inputs, published = json.loads(input_bytes), json.loads(result_bytes)
    fx = D(inputs['cny_per_hkd'])
    assertions, largest_difference, details = 0, ZERO, {}
    def check(a,b):
        nonlocal assertions, largest_difference
        diff = abs(a-D(b))
        largest_difference = max(diff, largest_difference)
        assert diff < D('1e-35'), (a,b,diff)
        assertions += 1
    for name, company in inputs['companies'].items():
        own = independently_compute(company, fx)
        ref = published['companies'][name]
        for scenario, row in own['scenarios'].items():
            other = ref['scenarios'][scenario]
            check(row['fair'], other['fair_price'])
            check(row['operating_value'],other['operating_value'])
            for h in ('3','10'):
                check(row['horizons'][h]['exit'],other['horizons'][h]['exit_price'])
                check(row['horizons'][h]['irr'],other['horizons'][h]['irr'])
                check(row['horizons'][h]['no_rerating_irr'],other['horizons'][h]['no_rerating_irr'])
            for computed, saved in zip(row['ledger'],other['cash_ledger']):
                for a,b in [('fcff','attributable_fcff'),('equity_cash','equity_cash_after_interest'),
                            ('dividend','dividend'),('retained','retained_cash')]:
                    check(computed[a],saved[b])
            for p in row['parts']:
                ref_p = next(p2 for p2 in other['parts'] if p2['name']==p['name'])
                check(p['values'][0],ref_p['valuation']['value'])
                check(p['terminal'],ref_p['valuation']['terminal_value'])
        for h in ('3','10'):
            check(own['weighted'][h],ref['weighted'][h]['irr_of_expected_cashflows'])
        details[name] = own
    # Factual bookkeeping and arithmetic independent of the forecast mechanics.
    bridges = {
        'Tencent_base':D('511.154')-D(80)-D('452.963')-D('2.312')+D(650),
        'Kuaishou':D('121.095')-D('27.362')-D('25.253')-D('8.657')-D('4.842')-D('2.584')-D('12.5')}
    check(bridges['Tencent_base'],inputs['companies']['Tencent']['scenarios']['base']['bridge'])
    check(bridges['Kuaishou'],inputs['companies']['Kuaishou']['scenarios']['base']['bridge'])
    funding_value = D('20.4471')*D('.6833')
    # Stress: 50% of positive Kling cash flows; funding obligations unchanged.
    stress_inputs = json.loads(input_bytes)['companies']['Kuaishou']
    for scenario in stress_inputs['scenarios'].values():
        next(c for c in scenario['components'] if c['name']=='Kling')['ownership']='0.50'
    diluted = independently_compute(stress_inputs,fx)
    full_funding_inputs = json.loads(input_bytes)['companies']['Kuaishou']
    for scenario in full_funding_inputs['scenarios'].values():
        next(c for c in scenario['components'] if c['name']=='Kling')['loss_funding_share']='1'
    full_funding = independently_compute(full_funding_inputs,fx)
    ranking_thresholds = {}
    for horizon in ('3','10'):
        benchmark = details['Tencent']['weighted'][horizon]
        def present_value(flows):
            return sum((v/(ONE+benchmark)**t for t,v in enumerate(flows)),ZERO)
        k_scenarios = details['Kuaishou']['scenarios']
        expected_npv = sum((s['probability']*present_value(s['horizons'][horizon]['cashflows'])
                            for s in k_scenarios.values()),ZERO)
        delta = present_value(k_scenarios['base']['horizons'][horizon]['cashflows'])-present_value(k_scenarios['bear']['horizons'][horizon]['cashflows'])
        ranking_thresholds[horizon] = {
            'tencent_benchmark_irr':benchmark,
            'probability_shift_bear_to_base_to_match':-expected_npv/delta,
            'kuaishou_entry_price_to_match':D(inputs['companies']['Kuaishou']['price'])+expected_npv,
            'note':'Bull probability and all operating assumptions unchanged; probabilities are subjective assumptions'}
    output = {'reviewed_at':datetime.now().astimezone().isoformat(),
        'input_sha256':hashlib.sha256(input_bytes).hexdigest(),
        'result_sha256':hashlib.sha256(result_bytes).hexdigest(),
        'method':'Independent reverse-recursive DCF plus safeguarded Newton IRR; no import of main model',
        'arithmetic_assertions':assertions,'max_absolute_difference':largest_difference,
        'status':'ARITHMETIC_PASS_ONLY','bridges':bridges,'companies':details,
        'ranking_thresholds':ranking_thresholds,
        'funding_sensitivity':{'gross_funding_cny_bn':'20.4471','ownership':'.6833',
            'attributable_cash_before_burn':funding_value,
            'per_share_hkd_before_burn':funding_value/D('4.5')/fx,
            'note':'Conditional arithmetic only; not proof of cash receipt or freely distributable cash'},
        'kling_50pct_ownership_sensitivity':{
            'base_fair':diluted['scenarios']['base']['fair'],
            'base_irr_3':diluted['scenarios']['base']['horizons']['3']['irr'],
            'base_irr_10':diluted['scenarios']['base']['horizons']['10']['irr'],
            'weighted_irr':diluted['weighted'],
            'note':'Positive cash flow ownership falls to 50%; loss funding share unchanged; no compensating financing cash'},
        'kling_parent_funds_all_losses_sensitivity':{
            'base_fair':full_funding['scenarios']['base']['fair'],
            'base_irr_3':full_funding['scenarios']['base']['horizons']['3']['irr'],
            'base_irr_10':full_funding['scenarios']['base']['horizons']['10']['irr'],
            'weighted_irr':full_funding['weighted'],
            'note':'Parent funds 100% of future Kling deficits; keeps 68.33% of positive cash flow; no equity issue'}}
    (ROOT/'independent_verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2,default=str)+'\n')
    print(json.dumps({k:output[k] for k in ['status','arithmetic_assertions','max_absolute_difference','bridges','funding_sensitivity','kling_50pct_ownership_sensitivity','kling_parent_funds_all_losses_sensitivity']},ensure_ascii=False,indent=2,default=str))


if __name__=='__main__':
    main()
