# ckd-cat-care

猫慢性肾病（CKD）知识库与营养评估技能。**自包含打包——安装即离线可用**，不依赖任何外部抓取。

## 安装

把 `skills/ckd-cat-care/` 整个目录复制到 `~/.workbuddy/skills/` 下，重启 WorkBuddy 后生效。

```
skills/ckd-cat-care/  →  ~/.workbuddy/skills/ckd-cat-care/
```

## 何时触发

用户提到肾猫、猫肾衰、慢性肾病、CKD、IRIS 分期、肌酐、SDMA、血磷、UPC、尿蛋白、
肾处方粮、磷结合剂、皮下补液、肾性高血压、肾性贫血，或需要评估一款猫粮/罐头/冻干
是否适合肾猫、给猫主人写肾猫喂养建议时。

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

若需要轻量版本，删除这两个目录后技能仍可运行——`references/` 已保留全部知识正文，
只是失去查阅原文 PDF 的能力。

## 主要参考资料

- iCatCare 2026 猫 CKD 诊断与管理共识指南（期刊排版版）
- ISFM 猫慢性肾脏病共识指南
- AAFP / AAHA 2021 猫生命阶段与老年照护指南
- IRIS 肾脏疾病分期标准

## License

技能内容版权归作者所有。`assets/literature*/` 下的 PDF 为公开获取的学术文献，
仅供个人学习使用，版权归原作者。