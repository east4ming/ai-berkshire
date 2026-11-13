# 腾讯与快手估值比较：阅读入口

研究日2026-10-25，行情采用2026-10-23收盘。

先读[主报告](腾讯与快手估值及三年十年回报研究报告-20261025.md)。结论是腾讯长期确定性较高，快手基准收益和乐观上限较高；综合十年排名对概率与买价敏感，不能把模型微小差距当作事实。

| 附件 | 用途 |
|---|---|
| [腾讯底稿](tencent_research.md)、[快手底稿](kuaishou_research.md) | 独立经营研究、会计口径和原件定位 |
| [证据入口](evidence.json) | 市场输入、资料范围与两公司详细事实包 |
| [腾讯证据](tencent_evidence.json)、[快手证据](kuaishou_evidence.json) | 事实、派生项、来源、期间与来源冲突 |
| [模型输入](model_inputs.json)、[完整结果](model_results.json) | 三情景、逐年现金、持有期IRR、九格敏感性 |
| [压力测试结果](stress_results.json) | 不同现金强度、归属、融资与分配政策 |
| [独立审查](independent_review.md)、[独立重算结果](independent_verification.json) | 312项现金、DCF、IRR及权益结构复核 |
| [审计范围](audit/README.md) | 抽样分类、共享工具结果、未覆盖项 |

## 复算

主模型仅需Python标准库，无需安装金融数据包。以下命令在本目录运行：

```sh
python3 model.py
python3 stress.py
python3 independent_check.py
```

`engine_crosscheck.py`与`audit_report.py`额外调用研究时本地仓库的共享工具；这些共享工具不属于本次发布范围。它们的本次输入、结果及审计记录已保存在`audit/`，不影响上述三个独立脚本复算主报告。

金额模型单位为人民币十亿元，股份单位十亿股；报告展示换成亿元、亿股。第一年是估值日之后完整十二个月，固定经济股数；可灵负现金承担比例与正收益归属不同。净回购为零、35%正股权现金分红，其余留存，属于统一比较假设，非公司承诺。

本次仅发布本目录研究，不覆盖既有腾讯、快手报告或其他任务文件。
