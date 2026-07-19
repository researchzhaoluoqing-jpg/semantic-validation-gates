# Semantic Validation Gates — 实验设计 v1

对应论文: SSRN_Semantic_Validation_Gates_Axiomatic_Framework_Preprint_v1.pdf
Scope: 论文初版 scope（第 6 节自述的 empirical validation：GSM8K / TruthfulQA；MATH 留到 v2）

## 论文中可实证检验的命题

| 命题 | 论文位置 | 可检验形式 |
|---|---|---|
| C1 五门可具体实例化且偏差可计算 | §3 (f1–f5) | 用嵌入空间 + W2/MMD/Hodge 实现全部五个算子 |
| C2 EVT 阈值良定性 (Conjecture 5.3) | §5.2 | 在 valid 校准集上拟合 Fréchet 分布得 τᵢ(α)，验证留出集误拒率 ≤ α |
| C3 分类实用性 + 字典序分区 (Thm 5.1, Π) | §4–5.1 | Π 对错误输出的首败门分布；每个 ρᵢ 对"答案错误"的 AUROC |
| C4 扰动连续性 (Conjectures 5.2/5.4) | §5.2 | 小扰动下 |Δρᵢ| / W2(µ,µ′) 的经验 Lipschitz 常数；Π 翻转率 vs 扰动幅度 |

## 算子实例化（论文数学对象 → 可计算代理）

输出表示：将模型输出按句切分，用 sentence-transformer 嵌入，得到嵌入空间上的经验测度 µ（均匀权重点云）。W2 用 POT 精确解 EMD。

- **f1 Format**: P_form = 满足任务格式约束的输出集（GSM8K 要求以 `#### <数字>` 结尾；TruthfulQA 要求非空且 ≤6 句）。投影 = 对输出做最小格式修复（补/截断），f1 = W2(µ, µ_repaired)。已合规则 f1=0。
- **f2 Fact**: ν_fact = 该题参考解答（GSM8K 金标准解 / TruthfulQA correct_answers）句子嵌入 + 高斯核抖动（KDE 平滑）。f2 = W2(µ, ν_fact)。
- **f3 Logic**: 输出句两两做 NLI。熵流 Y_ij = p_entail(i→j) − p_entail(j→i)，在完全图上做 Hodge 分解（HodgeRank 式最小二乘），f3 = 非梯度残差分量范数与最大矛盾概率的组合 —— 作为 Čech 障碍类调和范数的可计算代理。
- **f4 Alignment**: 逐句毒性分类（toxic-bert）。P_safe 投影 = 删除毒性句后的测度，f4 = W2(µ, µ_safe)。全安全则 f4=0。
- **f5 Intent**: ψ = RBF 核均值嵌入，f5 = MMD(µ, ν_intent)，ν_intent = 问题+目标答案的嵌入测度。MMD 正是 ∥ψ(µ)−ψ(ν)∥_RKHS，与论文定义一字不差。

## 实验流程 (E1–E4)

1. **E1 生成与测量**: Qwen2.5-1.5B-Instruct 在 GSM8K test (N=150) 与 TruthfulQA generation (N=150) 上生成答案；GSM8K 用数值精确匹配打正误标签，TruthfulQA 用与 correct/incorrect 参考答案的最近邻嵌入相似度打标签。对每个输出算 (f1..f5)。
2. **E2 EVT 校准 (Conj 5.3)**: valid 输出（答案正确+格式合规+无毒）按 60/40 分校准/留出。对每门在校准集拟合 Fréchet（scipy invweibull，兜底用经验分位数），τᵢ = F⁻¹(1−α)，α ∈ {0.01,0.05,0.10}。在留出 valid 集上测每门误拒率与总误拒率，对照 α 与联合界 5α。
3. **E3 分类 (Thm 5.1 / Π)**: 用 α=0.05 的 τ 算 ρᵢ 与 Π。报告：错误输出 vs 正确输出的 Π 分布（首败门直方图）；每门 ρᵢ 判别"答案错误"的 AUROC；分区互斥性按构造成立，报告经验占比。
4. **E4 扰动鲁棒性 (Conj 5.2/5.4)**: 三种扰动 —— 句序打乱、随机删一句、嵌入高斯抖动(σ∈{0.01,0.03,0.1})。测 W2(µ,µ′) 与 |Δρᵢ|，回归斜率 = 经验 Lipschitz 常数；按扰动幅度分箱统计 Π 翻转率。

## 产出

`/kaggle/working/results/`: records.csv（每条输出的全部原始偏差+标签）、thresholds.json、evt_validation.json、auroc.json、lipschitz.csv、summary.json、plots/*.png。

跑完拉回本地 → 分析 → 回改论文（把"待实证"表述替换为实测结果，或据负结果修正猜想表述）。

## 运行环境

Kaggle GPU (T4)，internet ON。所有模型（Qwen2.5-1.5B-Instruct、all-MiniLM-L6-v2、nli-deberta-v3-xsmall、toxic-bert）与数据集（openai/gsm8k、truthful_qa）均为公开权重/数据，**不需要 HF token**。环境变量 `QUICK=1` 触发 N=20 + 0.5B 模型的冒烟测试。
