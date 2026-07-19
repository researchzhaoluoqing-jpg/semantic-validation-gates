# svg_experiments — E0–E4 实验代码包 (ERS v1.0 配套实现)

## 实验 → 模块 → 理论支撑映射
| 实验 | 入口 (runners.py) | 核心算法 | 支撑的定理/命题 |
|---|---|---|---|
| E0 | run_e0_s1/s2 | S1 衰减曲线、S2 假阳率 + CP 区间 | 论文 §6 假设 S1/S2 |
| E1 | run_e1 + e1_verdict | 5 检测臂、配对 bootstrap ΔAUROC、Holm、和乐定位 | §3.3、Prop 4.6、预注册 P-A/B/C |
| E2 | run_e2 | 千次切分覆盖分布 vs Beta(m,n+1−m) KS + 精确二项 | Thm 4.2 (Vovk/A&B 覆盖分布律) |
| E3 | match_claims, stats.cmin_from_audit | 双向蕴含匹配、CP 下界 c_min 规则 | Prop 4.6、§4.5 弃权底线 |
| E4 | run_e4 | 同底配对 m 扫描、Cochran–Armitage、log-log 斜率 | Prop 3.6/3.7 (稀释与单元敏感度) |

## 冒烟研究发现 (AMENDMENTS,须回写 ERS 与论文)
- **F1 环稀释 → 和乐统计量**:最小二乘残差把闭合缺口摊到环上 L 条边 (能量∝gap²/L),
  被噪声淹没且无法定位;正确对象是 H¹ 障碍在基本环上的和乐 h=|Σ±δ|,长度不变且
  定位于闭合边。detectors.affine_energy 已实现;写入论文 §3.3 数值实例化。
- **F2 配对纪律**:稀释指数必须在同底配对(同一单元集、只翻转一个)上测量;
  独立采样注入 O(m^{-1/2}) 噪声,把斜率从 −1 污染到 −0.53。E4 预注册证伪对象
  修正为"嵌入均值移动量"而非"得分差"。
- **F3 生成器闭环**:V3 的闭合声明必须在既有节点间闭环 (0, n−1),悬挂新节点
  不产生任何环/障碍。
- **观察 O1(相补性)**:mock 下 SAT 在 V3 达 1.0(提取置信全高于阈值时精确闭包
  完美),SHEAF 软分 0.906;真实数据中阈值化提取会退化 SAT(见 V2/k5:0.50),
  软和乐保持。这正是 relax-and-certify 组合的存在理由——部署门 = max(软, 证书)。

## 真模型接入清单
1. nli_wrapper.HFNLI:核对 checkpoint 标签映射 (CONTRA_IDX),MNLI-val 拟合温度并冻结,报 ECE。
2. insertion:V1/V2 的否定模板作用于真实 GSM8K 声明文本;V3 换数值方程模板;
   MockNLI 参数以 E0 实测值回填,先跑功效模拟再上真机。
3. E4:sample_units 换 sentence-transformer 嵌入,IFEval 长输出。
4. 全量样本按 ERS:E1 每格配对 n=1000,E2 R=1000,E3 n=400 双标注。
