# ckd-cat-care

猫慢性肾病（CKD）知识库与营养评估技能。**自包含打包——安装即离线可用**，不依赖任何外部抓取。

## 安装

### 方式一：GitHub 上直接下载

仓库根目录下的 `skills/ckd-cat-care/` 就是技能本体，下载整个目录即可。

```bash
git clone https://github.com/qiqi73554-ctrl/ckd-cat-care-skill.git
```

### 方式二：只取技能目录

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/qiqi73554-ctrl/ckd-cat-care-skill.git
cd ckd-cat-care-skill
git sparse-checkout set skills/ckd-cat-care
```

### 放到对应工具的技能目录

| 工具 | 目标路径 |
|---|---|
| Codex CLI | `~/.codex/skills/ckd-cat-care/` |
| WorkBuddy | `~/.workbuddy/skills/ckd-cat-care/` |
| Claude Code | `~/.claude/skills/ckd-cat-care/` |

Windows 的 `~` 是 `%USERPROFILE%`。

装好后重启工具即可生效。Codex 里用 `$ckd-cat-care` 显式调用。

> **只想用知识正文、 不要 301MB 文献？** 见文末「体积说明」。

## 依赖

- **必需**：Python 3（跑 `scripts/` 下的工具）
- **可选**：如果要读 `assets/literature/pdfs/` 里的 PDF，需自备PDF 读取能力

## 何时触发

用户提到肾猫、猫肾衰、慢性肾病、CKD、IRIS 分期、肌酐、SDMA、血磷、UPC、尿蛋白、
肾处方粮、磷结合剂、皮下补液、肾性高血压、肾性贫血，或需要评估一款猫粮/罐头/冻干
是否适合肾猫、给猫主人写肾猫喂养建议时。

## 工具脚本

```bash
python scripts/renal_eval.py "蛋白 32% 脂肪 18% 纤维 2% 灰分 6% 钙 0.9% 磷 0.7% 水分 8%"
python scripts/iris_stage.py --creatinine 2.4 --sdma 22 --upc 0.3 --sbp 165
python scripts/calcitriol.py --weight 5.48
```

| 脚本 | 用途 |
|---|---|
| `renal_eval.py` | 猫粮营养评估：DM 换算、磷/蛋白/钠评级、IRIS 各期适用性、热量估算 |
| `iris_stage.py` | IRIS 分期与亚分期判定 |
| `calcitriol.py` | 骨化三醇分药计量 |
| `export_med_table.py` | 用药表格导出 |

⚠️ 剂量类输出均须标注「由兽医确定」，本工具是资料整理与科普，**不是诊断工具**。

## 目录结构

```
ckd-cat-care/
├── SKILL.md                        技能入口与触发条件
├── AUDIT-跨资料核验与待复核汇总.md  资料交叉核验记录
├── references/                     知识正文（12 篇，md）
│   ├── 01-病理与IRIS分期.md
│   ├── 02-营养管理标准.md
│   ├── 03-食物与磷数据库.md
│   ├── 04-用药与护理.md
│   ├── 05-复查与指标解读.md
│   ├── 06-常见误区.md
│   ├── 07-主人沟通话术.md
│   ├── 08-肠肾轴与尿毒症毒素.md
│   ├── 09-老年猫预防肾衰完全指南.md
│   ├── 10-2026新证据速览.md
│   ├── 11-家长速查用药清单.md
│   └── 12-照护手册要点.md
├── data/                           结构化数据
│   ├── lab-reference-ranges.csv     化验参考区间
│   ├── rx-renal-diets.csv          肾处方粮数据
│   └── cat-food-phosphorus.csv      猫粮磷含量
├── scripts/                        计算工具
│   ├── renal_eval.py                肾功能综合评估
│   ├── iris_stage.py                IRIS 分期判定
│   ├── calcitriol.py                骨化三醇剂量计算
│   └── export_med_table.py          用药表格导出
└── assets/
    ├── literature/
    │   ├── pdfs/                    原始文献 PDF
    │   └── translations/           中文译文
    ├── literature-collection/       文献总集卷一～卷六 + 总目录
    └── deliverables/                已生成的成品（HTML/xlsx/pdf/pptx/docx）
```

## 体积说明

总计约 **357MB**，其中 `assets/literature/` 与 `assets/literature-collection/`
为离线文献 PDF 原文合集，约 **301MB（占 84%）**，按"安装即离线可用"设计打包。

**只想要轻量版（约 56MB）**：clone 后删掉这两个目录再拷进技能目录即可，

```bash
rm -rf skills/ckd-cat-care/assets/literature skills/ckd-cat-care/assets/literature-collection
```

技能仍可完整运行——`references/` 已保留全部知识正文，只是失去查阅原文 PDF 的能力。
这是推荐给普通用户的安装方式。

## 主要参考资料

- iCatCare 2026 猫 CKD 诊断与管理共识指南（期刊排版版）
- ISFM 猫慢性肾脏病共识指南
- AAFP / AAHA 2021 猫生命阶段与老年照护指南
- IRIS 肾脏疾病分期标准

## 医疗边界

本技能是**资料整理与科普工具，不是诊断工具**。任何具体病例都应以主治兽医的判断为准；
剂量类信息仅列常规范围供参考，须由兽医确定。遇到急症征象（超过 24 小时不进食、
突发失明、抽搐、无尿超过 24 小时等）应立即就医。

## License

技能内容版权归作者所有。`assets/literature*/` 下的 PDF 为公开获取的学术文献，
仅供个人学习使用，版权归原作者。`assets/deliverables/` 下含兽医访谈整理稿，
文件名含受访者姓名，转载或再分发前请自行确认授权。