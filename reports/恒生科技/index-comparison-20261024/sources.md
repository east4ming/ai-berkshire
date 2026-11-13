# 来源、观察日与独立性登记

研究基准日 2026-10-24，中国时区；采集和复核跨越 10-25 凌晨。市场基准仍为 2026-10-23。仅保留必要事实摘录及公开链接，不重新分发完整商业数据库、财报或机构报告。

## 核心估值序列

- 原页面：[投资工作台](https://etf.whatsid.me/indices/valuation)；原公开图表接口：[valuation/history](https://etf.whatsid.me/api/valuation/history)。网页明确恒科为市值加权 PE-TTM，NDX 来自蛋卷历史估值。
- 选用 `display_history`，不用另一组 `index_history`。接口编码 `columnar-v1`，`d` 为 calendar 下标，`v` 对应 PE/PB。关键数据及 dataVersion 保存在 `valuation-extract.json`；NDX 与两条 forward 序列摘录另见 `nasdaq-source-extract.json`。
- 恒科：2022-10-31 PE31.94/PB1.743；2026-10-23 PE20.63/PB2.092。NDX：2022-10-30 标签 PE25.34/PB6.490；2026-10-21 标签 PE28.74/PB9.037；2022-10-16 标签 PE22.72。
- 网站未完整披露逐股亏损、股数、调整项和财报重述规则。恒科 underlying provider 未公开；字段名不能证明是理杏仁。NDX 虽明示蛋卷，本次未从蛋卷取得同日原始快照。
- **验证等级：B；同站同展示序列复取，不是完整独立双源或逐股复算。** NDX 历史周日标签及当期混合频率，未有美国交易日/时区映射。已经删除将该标签与 FRED 同名日期强行配对产生的指数目标点位。

## 行情事实

| 事实 | 原始或高优先来源 | 交叉检查与限度 |
|---|---|---|
| 恒科2026-10-23：3871.66 | [恒生指数公司](https://www.hsi.com.hk/zh-hk/indexes/all-indexes/index-details/?seriesCode=hstech)，搜索索引带完整日期表 | [信报行情](https://stock360.hkej.com/stock)、[恒生银行/财经智珠](https://cbbc.hangseng.com/zh-cn/market/stock/code/hstech)数值相同；指数公司新站open为JS壳 |
| 恒科2022-10-31：2852.57 | [证券时报当日原稿](https://www.stcn.com/article/detail/712355.html) | [智通财经当日稿](https://hk.stockstar.com/IG2022103100006085.shtml)相同 |
| 恒科当月收盘低点2801.99；盘中2720.38 | [指数纪录表](https://zh.wikipedia.org/wiki/%E6%81%92%E7%94%9F%E7%A7%91%E6%8A%80%E6%8C%87%E6%95%B8) | [当时盘中低点报道](https://finance.sina.com.cn/stock/roll/2022-11-04/doc-imqmmthc3233363.shtml)；来源级别低于主表月末值，仅辅助 |
| NDX2022-10-31：11405.57；2026-10-23：28957.53 | [FRED原始历史](https://fred.stlouisfed.org/data/NASDAQ100)，来源Nasdaq | 历史与下述KFH/Refinitiv月报、[Motilal基金月报](https://www.motilaloswalmf.com/CMS/assets/uploads/Documents/d51f1-monthly-dashboard-10-11-2022.pdf)一致；当前未取得第二独立底层行情链，FRED转发Nasdaq不算两源 |
| IXIC2022-10-31：10988.15；2026-10-23：25955.34 | [FRED原始历史](https://fred.stlouisfed.org/data/NASDAQCOM)，来源Nasdaq | 当前与[AP当日报道](https://apnews.com/article/e07c72bc5cbe5dffe352ddf30054e35f)一致；历史与StatMuse逐日表一致，但主报告优先FRED |

## 估值旁证与不能消除的差异

| 来源 | 必要观察 | 采用方式 |
|---|---|---|
| [国海证券2022-11-15报告摘要](https://stock.stockstar.com/JC2022111500003578.shtml) | 截至2022-10-31恒科TTM PE35.3 | 与主序列31.94差异超1%，不平均；只支持历史约三十多倍量级 |
| [百分位](https://baifenwei.com/index/hstech/) | 2026-10-23恒科PE20.63/PB2.09 | 与主源精度舍入一致，可能共用底层，不能证明独立 |
| [同花顺10-22报道](https://stock.10jqka.com.cn/20261022/c680963993.shtml) | PE-TTM21.20 | 缺精确估值时点，不能与10-23视为同日 |
| [KFH Capital/Refinitiv 2022年10月月报](https://www.kfhcapital.com.kw/media/1800bd40-9745-42e3-8af4-8a70ff1aff31/emNbwQ/Research/Monthly/KFHC%20Market%20Monitor%20%E2%80%93%20October%202022.pdf) | 10-31 NDX PE-TTM24.37 | 第3页；与主序列周标签25.34有日期/算法差异 |
| [GuruFocus](https://www.gurufocus.com/economic_indicators/6778/nasdaq-100-pe-ratio) | 2026-10-23 NDX PE28.7 | 交叉量级，未确认与蛋卷底层独立 |
| [Worldperatio](https://worldperatio.com/index/nasdaq-100/) | 2026-10-23 PE26.68 | 自述基于QQQ；不冒充NDX官方PE |
| [Invesco QQQ官方产品页](https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html) | 2026-09-30基金特征：PE29.48、forward25.75、PB9.91 | 搜索抓取可读，open偶为导航壳；正文不作为当前指数主值 |
| [Siblis](https://siblisresearch.com/data/nasdaq-100-pe-ratio/) | 2026-09-30 PE35.09、forward23.26 | 说明提供商差异大；不平均、不跨月伪造双源通过 |

官方年度口径：[恒生2022年10月月报](https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/monthly_roundup/20221101T000000.pdf)第8页PE348.85；[Operation Guide](https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_operation_guide_e.pdf)现行June2026 v3.28，第35—36页§10.15—10.16与脚注，latest final results、自由流通及上限调整。没有据此宣称负利润一律剔除或完整重建2022年利润桥。

前瞻来源：[iFAST展望](https://fsm.global/sg/article/rcms397960)的16.9倍是2026-09-23 FY2026E；[Business Times/彭博历史回顾](https://www.businesstimes.com.sg/companies-markets/china-tech-stocks-roar-back-new-normal-will-test-upside)约17倍缺具体日与盈利年份。NDX [History of Market](https://historyofmarket.com/nasdaq/ndx-forward-pe/)及[公开JSON](https://historyofmarket.com/api/ndx/forward-pe.json)的`forward`与`forwardOwn`是两种算法；18.56与20.12分属两条序列，不计算精确前后价差。

## 现金流事实与交叉核验

| 事实 | 原始披露 | 独立编辑来源 | 说明 |
|---|---|---|---|
| 腾讯2026Q2 FCF -138亿元 | [公司发布稿](https://www.prnewswire.com/apac/news-releases/tencent-announces-2026-second-quarter-results-302849608.html) | [Telecompaper](https://www.telecompaper.com/news/tencent-records-negative-free-cash-in-q2-after-surge-in-ai-capex--1579852)同为-13.8 billion CNY | 原始稿归母净利56022百万元；剔预付款FCF376亿元是公司调整值，未独立确认其可持续性 |
| 阿里2026年6月季度FCF -446.70亿元 | [公司Business Wire原稿](https://www.nasdaq.com/press-release/alibaba-group-announces-june-quarter-2026-results-2026-08-20) | [MoneyDJ](https://www.moneydj.com/kmdj/news/newsviewer.aspx?a=c70b733e-4ea8-4dfa-bd37-d11655f13382)同值，归母净利105.37亿元也相同 | FCF为公司非GAAP定义；不将每股数、集团净利与归母混用 |
| 微软FY26Q4 FCF196亿美元 | [公司原始电话会](https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4) | [Reuters转载](https://ca.marketscreener.com/news/microsoft-tops-quarterly-cloud-growth-estimates-easing-spending-concerns-ce7f51d3dd88f520)同为19.6 billion USD | OCF55.4、现金PP&E35.8见原件及[StockAnalysis实录](https://stockanalysis.com/stocks/msft/transcripts/647770-q4-2026/)；实录转发不算独立编辑源 |

这些编辑来源仍主要根据公司披露，交叉核对的是抄录、单位与定义，不是第二家审计机构的独立核算。没有把季节性单季FCF年化。

## 宏观、方法与未取得数据

- 美国十年国债：[FRED DGS10全表](https://fred.stlouisfed.org/data/DGS10)及[Fed H.15](https://www.federalreserve.gov/releases/h15/current/)，同一底层链：2022-10-31 4.10%，2026-10-22 4.96%；AP的10-23市场4.99%是异日旁证。
- 中国国债：[中债官方曲线](https://yield.chinabond.com.cn/cbweb-cbrc-web/cbrc/more)10-23十年1.6400%，动态页搜索索引可读；[国元期货2022年10月月报/中期协存档](https://www.cfachina.org/servicesupport/analygarden/jrl/gz/202211/P020221104548361065880.pdf)历史约2.64%。未取得2022当日官方原表。
- 历史风险时点：[2022-11-11防疫二十条](https://app.www.gov.cn/govdata/gov/202211/11/494135/article.html)、[2022-12-15 PCAOB公告](https://pcaobus.org/news-events/news-releases/news-release-detail/fact-sheet-pcaob-secures-complete-access-to-inspect-investigate-chinese-firms-for-first-time-in-history)，均晚于历史锚点。
- [Nasdaq 2026-10-23简报](https://www.nasdaq.com/economic-institute/chartstopper-102326)的45%是正在披露中的Q3盈利跟踪，不是最终财报或五年预测。
- [Nasdaq编制规则](https://indexes.nasdaq.com/docs/Methodology_NDX.pdf)及[方法更新说明](https://www.nasdaq.com/newsroom/nasdaq100-index-methodology-update-why-now)说明成分权重规则发生变化；这不等于PE计算公式在同日变化。[恒生媒体中心](https://www.hsi.com.hk/media-room/)显示编制咨询结论标题，未取完整公告，因此正文没有写确定新名单或生效细节。
- 未获得：完整两时点成分/权重/当时已知财报、逐股含亏损TTM重建、完全同法同日NTM、可比IXIC估值、同口径两日股息率。情景派息率均为假设，不能当历史事实。
- 不使用：旧报告的十家公司合成分位、未复核的9月官方28.23倍；HistoricalPERatio网站的“Nasdaq”实际为NDAQ公司；不把网页中星号标记的短历史当完整十年分位。

研究可支持“在所列序列下倍数怎样变化”，不支持“全部指标已独立双源通过”或“某指数确定能获得某个回报”。
