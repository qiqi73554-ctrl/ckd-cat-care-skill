#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肾猫粮营养评估器

用法:
  python renal_eval.py "蛋白 32% 脂肪 18% 纤维 2% 灰分 6% 钙 0.9% 磷 0.7% 水分 8%"
  python renal_eval.py --protein 32 --fat 18 --fiber 2 --ash 6 --ca 0.9 --p 0.7 --moisture 8 --taurine 0.2
  python renal_eval.py --csv ../data/cat-food-phosphorus.csv
  python renal_eval.py --protein 32 --p 0.7 --moisture 8 --stage 3

干物质换算: DM% = as-fed% / (1 - 水分%)
热量估算(改进Atwater): ME = 10 * (3.5*蛋白 + 8.5*脂肪 + 3.5*NFE)
判据基准: IRIS 2023 / 文献
"""

import argparse
import csv
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- 判据常量 (IRIS 2023 / 文献) ----------
PHOS_DM_EXCELLENT = 0.5   # DM 磷 <= 0.5% 优秀
PHOS_DM_ACCEPTABLE = 0.6  # DM 磷 <= 0.6% 可接受 (IRIS 上限)
PHOS_PER_1000KCAL = 1.0   # g/1000kcal 参考上限
CA_P_MIN = 1.0            # Ca:P 最低要求

STAGE_PROTEIN_NOTE = {
    1: "Stage 1：不需限蛋白，优先维持瘦体重",
    2: "Stage 2：不需严格限蛋白，重点是限磷",
    3: "Stage 3：可适度限蛋白，仍以保肌肉量为前提",
    4: "Stage 4：进食优先于一切，蛋白限制让位于食欲",
}

KEYS = {
    "蛋白": "protein", "蛋白质": "protein", "粗蛋白": "protein",
    "脂肪": "fat", "粗脂肪": "fat",
    "纤维": "fiber", "粗纤维": "fiber",
    "灰分": "ash", "粗灰分": "ash",
    "钙": "ca",
    "磷": "p",
    "镁": "mg",
    "钾": "k",
    "钠": "na",
    "牛磺酸": "taurine",
    "水分": "moisture", "水份": "moisture",
    "热量": "kcal",
}


def parse_inline(text):
    """解析 '蛋白 32% 脂肪 18%' 或 '蛋白=32,脂肪=18' 形式的输入"""
    data = {}
    # 先按空格切成 token，再匹配 "键 值"
    tokens = re.findall(r"([\u4e00-\u9fa5A-Za-z]+)\s*[=:]?\s*([\d.]+)\s*%?", text)
    for key, val in tokens:
        std = KEYS.get(key)
        if std:
            try:
                data[std] = float(val)
            except ValueError:
                pass
    return data


def to_dm(value, moisture):
    """as-fed % -> 干物质 %"""
    if value is None or moisture is None:
        return None
    if moisture >= 100:
        return None
    return value / (1 - moisture / 100.0)


def estimate_kcal(protein, fat, fiber, ash, moisture):
    """改进 Atwater 估算 ME kcal/kg"""
    if None in (protein, fat, fiber, ash, moisture):
        return None
    nfe = 100 - moisture - protein - fat - fiber - ash
    if nfe < 0:
        return None
    return 10 * (3.5 * protein + 8.5 * fat + 3.5 * nfe)


def phos_per_1000kcal(p_dm, kcal_per_kg):
    """DM 磷% -> g/1000 kcal"""
    if p_dm is None or not kcal_per_kg:
        return None
    return (p_dm / 100.0) * 1_000_000 / kcal_per_kg


def grade_phosphorus(p_dm, p_1000):
    if p_dm is None:
        return "?", "数据不足，无法判定（需磷与水分）"
    if p_dm <= PHOS_DM_EXCELLENT:
        level = "优秀"
        note = f"DM 磷 {p_dm:.2f}% ≤ 0.50%，达到处方肾粮水平"
    elif p_dm <= PHOS_DM_ACCEPTABLE:
        level = "可接受"
        note = f"DM 磷 {p_dm:.2f}% ≤ 0.60%，符合 IRIS 上限，但非最优"
    elif p_dm <= 0.9:
        level = "偏高"
        note = f"DM 磷 {p_dm:.2f}% 超出 IRIS 0.60% 上限，肾猫不推荐"
    else:
        level = "过高"
        note = f"DM 磷 {p_dm:.2f}% 显著超标，肾猫禁用"

    if p_1000 is not None:
        if p_1000 > PHOS_PER_1000KCAL:
            note += f"；按能量计 {p_1000:.2f} g/1000kcal > 1.0，同样超标"
        else:
            note += f"；按能量计 {p_1000:.2f} g/1000kcal"
    return level, note


def grade_ca_p(ca, p):
    if not ca or not p:
        return "?", "数据不足"
    ratio = ca / p
    if ratio >= 1.2:
        return "良好", f"Ca:P = {ratio:.2f}，≥1.0，安全"
    if ratio >= CA_P_MIN:
        return "合格", f"Ca:P = {ratio:.2f}，刚好达标，无余量"
    return "不合格", f"Ca:P = {ratio:.2f} < 1.0，低钙磷比会加重肾损伤"


def grade_protein(protein_dm, stage):
    if protein_dm is None:
        return "?", "数据不足"
    if stage in (1, 2):
        if protein_dm >= 30:
            note = f"DM 蛋白 {protein_dm:.1f}%，早期限蛋白无益反而伤肌肉，此水平合适"
        else:
            note = f"DM 蛋白 {protein_dm:.1f}%，偏低，早期建议保证优质蛋白摄入"
        level = "参考"
    else:
        if protein_dm >= 35:
            note = f"DM 蛋白 {protein_dm:.1f}%，{STAGE_PROTEIN_NOTE.get(stage, '')}，此值偏高"
            level = "偏高"
        elif protein_dm >= 26:
            note = f"DM 蛋白 {protein_dm:.1f}%，处于中期限蛋白的常见区间"
            level = "合适"
        else:
            note = f"DM 蛋白 {protein_dm:.1f}%，偏低，注意肌肉流失风险"
            level = "偏低"
    return level, note


def overall(phos_level, cap_level):
    if phos_level == "过高" or cap_level == "不合格":
        return "❌ 不适合肾猫"
    if phos_level in ("优秀",) and cap_level in ("良好", "合格"):
        return "✅ 适合肾猫（磷与钙磷比均达标）"
    if phos_level == "可接受":
        return "⚠️ 勉强可用，优先选择 DM 磷 ≤0.5% 的产品"
    return "⚠️ 需谨慎，建议核对完整配料表与无机磷盐"


def evaluate(d, stage=2):
    moisture = d.get("moisture")
    p = d.get("p")
    ca = d.get("ca")
    protein = d.get("protein")

    p_dm = to_dm(p, moisture)
    ca_dm = to_dm(ca, moisture)
    protein_dm = to_dm(protein, moisture)
    fat_dm = to_dm(d.get("fat"), moisture)
    fiber_dm = to_dm(d.get("fiber"), moisture)

    kcal = d.get("kcal") or estimate_kcal(
        d.get("protein"), d.get("fat"), d.get("fiber"), d.get("ash"), moisture
    )
    p_1000 = phos_per_1000kcal(p_dm, kcal) if kcal else None

    phos_level, phos_note = grade_phosphorus(p_dm, p_1000)
    cap_level, cap_note = grade_ca_p(ca, p)
    prot_level, prot_note = grade_protein(protein_dm, stage)

    print("=" * 60)
    print("肾猫粮营养评估")
    print("=" * 60)
    print(f"水分        : {moisture if moisture is not None else '-'} % (as-fed)")
    print()
    print("-- 干物质基础 (DM) 换算 --")
    for label, v in [
        ("蛋白", protein_dm), ("脂肪", fat_dm), ("纤维", fiber_dm),
        ("钙", ca_dm), ("磷", p_dm),
    ]:
        print(f"  {label:<6}: {v:.2f} % DM" if v is not None else f"  {label:<6}: -")
    print()
    if kcal:
        src = "标称" if d.get("kcal") else "改进 Atwater 估算"
        print(f"热量        : {kcal:.0f} kcal/kg  ({kcal/10:.1f} kcal/100g) [{src}]")
    print()
    print("-- 判定 --")
    print(f"  磷        : [{phos_level}] {phos_note}")
    print(f"  钙磷比    : [{cap_level}] {cap_note}")
    print(f"  蛋白      : [{prot_level}] {prot_note}")
    print(f"  分期背景  : {STAGE_PROTEIN_NOTE.get(stage, '')}")
    print()
    print("结论：" + overall(phos_level, cap_level))
    print()
    print("※ 还需人工核对：配料表是否含磷酸钠/磷酸钾等无机磷盐（吸收率高，加重肾损伤）")
    print("※ 湿粮优先：干物质值相同的情况下，含水量高者更适合肾猫")
    print("※ 本工具为营养数据分析，不替代兽医诊断")
    print("=" * 60)


def evaluate_csv(path, stage):
    with open(path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("CSV 为空")
        return

    def num(row, *names):
        for n in names:
            for k in row:
                if k and k.strip() == n:
                    v = (row[k] or "").strip().replace("%", "")
                    if v in ("", "-"):
                        return None
                    try:
                        return float(v)
                    except ValueError:
                        return None
        return None

    print(f"{'名称':<26}{'DM磷%':>8}{'Ca:P':>8}{'判定':<22}")
    print("-" * 66)
    for row in rows:
        name = (row.get("名称") or "").strip()
        if not name:
            continue
        d = {
            "protein": num(row, "蛋白%"),
            "fat": num(row, "脂肪%"),
            "fiber": num(row, "纤维%"),
            "ash": num(row, "灰分%"),
            "ca": num(row, "钙%"),
            "p": num(row, "磷%"),
            "moisture": num(row, "水分%"),
            "kcal": num(row, "热量"),
        }
        p_dm = to_dm(d["p"], d["moisture"])
        ratio = f"{d['ca']/d['p']:.2f}" if d["ca"] and d["p"] else "-"
        if p_dm is None:
            print(f"{name:<26}{'-':>8}{ratio:>8}{'数据不足':<22}")
            continue
        lv, _ = grade_phosphorus(p_dm, None)
        cap_lv, _ = grade_ca_p(d["ca"], d["p"])
        print(f"{name:<26}{p_dm:>8.2f}{ratio:>8}{overall(lv, cap_lv):<22}")
    print("-" * 66)
    print("判据：DM 磷 ≤0.5% 优秀 / ≤0.6% 可接受 / >0.6% 不适合；Ca:P 需 ≥1.0")


def main():
    ap = argparse.ArgumentParser(description="肾猫粮营养评估器")
    ap.add_argument("data", nargs="*", help="内联数据，如 '蛋白 32% 脂肪 18% 磷 0.7% 水分 8%'")
    ap.add_argument("--protein", type=float)
    ap.add_argument("--fat", type=float)
    ap.add_argument("--fiber", type=float)
    ap.add_argument("--ash", type=float)
    ap.add_argument("--ca", type=float, help="钙 %")
    ap.add_argument("--p", type=float, help="磷 %")
    ap.add_argument("--k", type=float, help="钾 %")
    ap.add_argument("--na", type=float, help="钠 %")
    ap.add_argument("--moisture", type=float, help="水分 %")
    ap.add_argument("--kcal", type=float, help="热量 kcal/kg")
    ap.add_argument("--stage", type=int, default=2, choices=[1, 2, 3, 4], help="IRIS 分期")
    ap.add_argument("--csv", help="批量评估 CSV 文件")
    a = ap.parse_args()

    if a.csv:
        evaluate_csv(a.csv, a.stage)
        return

    d = {}
    for k in ("protein", "fat", "fiber", "ash", "ca", "p", "k", "na", "moisture", "kcal"):
        v = getattr(a, k)
        if v is not None:
            d[k] = v
    if a.data:
        d.update(parse_inline(" ".join(a.data)))

    if "p" not in d and "moisture" not in d:
        ap.error("至少需要 --p 磷 与 --moisture 水分")

    evaluate(d, a.stage)


if __name__ == "__main__":
    main()
