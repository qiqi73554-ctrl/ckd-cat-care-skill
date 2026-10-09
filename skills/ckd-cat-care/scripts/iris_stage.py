#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IRIS CKD 分期判定器 (猫, IRIS 2023)

用法:
  python iris_stage.py --creatinine 2.4 --sdma 22 --upc 0.3 --sbp 165
  python iris_stage.py --creatinine 300 --unit umol --sdma 30
  python iris_stage.py --creatinine 2.4 --thin      # 瘦猫，启用 SDMA 上调规则
"""

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

UMOL_TO_MGDL = 0.0113

STAGES = {
    1: ("Stage 1", "非氮质血症", "监测、排查原发病、关注血磷与血压"),
    2: ("Stage 2", "轻度氮质血症", "肾处方粮、限磷、纠正低钾、控制血压与蛋白尿"),
    3: ("Stage 3", "中度氮质血症", "积极液体支持、磷结合剂、止吐促食欲"),
    4: ("Stage 4", "重度氮质血症", "以生活质量为重心，强化支持治疗，讨论临终安排"),
}

RECHECK = {1: "每 3-6 个月", 2: "每 3-6 个月", 3: "每 2-3 个月", 4: "每 1-2 个月或按临床需要"}


def stage_by_creatinine(cr_mgdl):
    if cr_mgdl is None:
        return None
    if cr_mgdl < 1.6:
        return 1
    if cr_mgdl <= 2.8:
        return 2
    if cr_mgdl <= 5.0:
        return 3
    return 4


def stage_by_sdma(sdma):
    if sdma is None:
        return None
    if sdma < 18:
        return 1
    if sdma <= 25:
        return 2
    if sdma <= 38:
        return 3
    return 4


def apply_sdma_revision(cr_stage, sdma, thin):
    """返回 (修正后分期, 说明列表)"""
    notes = []
    if sdma is None:
        return cr_stage, notes
    if cr_stage and cr_stage <= 1 and sdma > 14:
        notes.append(f"SDMA {sdma} > 14 提示肾功能下降；肌酐 <1.6，仍列 Stage 1")
    if not thin:
        return cr_stage, notes
    if cr_stage == 2 and sdma >= 25:
        notes.append(f"瘦猫 + SDMA {sdma} ≥ 25 → 分期被低估，上调为 Stage 3")
        return 3, notes
    if cr_stage == 3 and sdma >= 45:
        notes.append(f"瘦猫 + SDMA {sdma} ≥ 45 → 分期被低估，上调为 Stage 4")
        return 4, notes
    return cr_stage, notes


def grade_upc(upc):
    if upc is None:
        return None, "未提供"
    if upc < 0.2:
        return "NP 非蛋白尿", "UPC < 0.2"
    if upc <= 0.4:
        return "BP 临界蛋白尿", "UPC 0.2-0.4，需复查（3 次采样间隔≥2周）"
    return "P 蛋白尿", "UPC > 0.4，猫的治疗阈值：肾处方粮 + ACEI/ARB"


def grade_sbp(sbp):
    if sbp is None:
        return None, "未提供"
    if sbp < 140:
        return "正常血压", "收缩压 < 140，靶器官损伤风险最低"
    if sbp <= 159:
        return "高血压前期", "140-159，低风险，定期监测"
    if sbp <= 179:
        return "高血压", "160-179，中风险，通常需启动降压治疗"
    return "重度高血压", "≥180，高风险，视网膜脱离/突发失明风险，紧急处理"


def main():
    ap = argparse.ArgumentParser(description="IRIS CKD 分期判定器（猫）")
    ap.add_argument("--creatinine", type=float, help="肌酐值")
    ap.add_argument("--unit", default="mgdl", choices=["mgdl", "umol"], help="肌酐单位")
    ap.add_argument("--sdma", type=float, help="SDMA μg/dL")
    ap.add_argument("--upc", type=float, help="尿蛋白肌酐比")
    ap.add_argument("--sbp", type=float, help="收缩压 mmHg")
    ap.add_argument("--phosphorus", type=float, help="血磷 mg/dL")
    ap.add_argument("--thin", action="store_true", help="瘦猫（肌肉量低），启用 SDMA 上调规则")
    a = ap.parse_args()

    cr = a.creatinine
    if cr is not None and a.unit == "umol":
        cr = cr * UMOL_TO_MGDL

    cr_stage = stage_by_creatinine(cr)
    sdma_stage = stage_by_sdma(a.sdma)

    print("=" * 60)
    print("IRIS CKD 分期判定（猫 / IRIS 2023）")
    print("=" * 60)

    if cr is not None:
        print(f"肌酐: {cr:.2f} mg/dL" + (f"  (原 {a.creatinine:.0f} μmol/L)" if a.unit == "umol" else ""))
        print(f"  → 肌酐分期: Stage {cr_stage}")
    else:
        print("肌酐: -")
    if a.sdma is not None:
        print(f"SDMA: {a.sdma:.0f} μg/dL → SDMA 分期: Stage {sdma_stage}")
    else:
        print("SDMA: -")

    base = cr_stage
    if cr_stage is not None and sdma_stage is not None and cr_stage != sdma_stage:
        base = max(cr_stage, sdma_stage)
        print(f"\n⚠️ 肌酐与 SDMA 分期不一致 → 取较高者 Stage {base}")
        print("   建议 2-4 周后复查两者；持续不一致则维持较高分期")
    elif cr_stage is None:
        base = sdma_stage

    final, notes = apply_sdma_revision(base, a.sdma, a.thin)
    for n in notes:
        print("   " + n)

    if final is None:
        print("\n数据不足，至少需要肌酐或 SDMA 之一")
        return

    print()
    print("-" * 60)
    name, desc, plan = STAGES[final]
    print(f"【分期】{name} — {desc}")
    print(f"【管理重点】{plan}")
    print(f"【复查频率】{RECHECK[final]}")
    print("-" * 60)

    upc_lv, upc_note = grade_upc(a.upc)
    sbp_lv, sbp_note = grade_sbp(a.sbp)
    print()
    print("-- 亚分期 --")
    print(f"  蛋白尿: {upc_lv or '-'} — {upc_note}")
    print(f"  血压  : {sbp_lv or '-'} — {sbp_note}")

    if a.phosphorus is not None:
        print()
        print("-- 血磷 --")
        targets = {1: (2.7, 4.6), 2: (2.7, 4.6), 3: (0, 5.0), 4: (0, 6.0)}
        lo, hi = targets[final]
        p = a.phosphorus
        if p > 6.0:
            print(f"  血磷 {p:.2f} mg/dL —— 任何分期都必须立即干预")
        elif p > hi:
            print(f"  血磷 {p:.2f} mg/dL —— 超出 Stage {final} 目标 (<{hi})，需限磷/磷结合剂")
        elif lo and p < lo:
            print(f"  血磷 {p:.2f} mg/dL —— 低于目标区间 {lo}-{hi}，注意是否过度限磷/高钙风险")
        else:
            print(f"  血磷 {p:.2f} mg/dL —— 在 Stage {final} 目标内 ({lo}-{hi})")

    print()
    print("※ 分期须在稳定、水合良好、空腹状态下判定；脱水/急性肾损伤/肾后性梗阻需先排除")
    print("※ 分期不反映进展速度，而进展速度往往才是最重要的预后因素")
    print("※ 本工具为资料整理辅助，不替代兽医诊断")
    print("=" * 60)


if __name__ == "__main__":
    main()
