#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
骨化三醇分药计量 (猫 CKD)

来源：[你的资料] CKD用药清单 by 肘肉菲妈
  单次目标剂量 = 体重(kg) × 9 ng
  给药时间：周三晚空腹 + 周日早饭空腹（每周两次）
  每粒 0.25 μg = 250 ng

用法:
  python calcitriol.py --weight 5.48
  python calcitriol.py --weight 5 --per-pill 0.5      # 每粒 0.5μg 规格
  python calcitriol.py --weight 4 --freq 3            # 每周三次
"""

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NG_PER_KG_PER_DOSE = 9      # ng/kg，每次
DEFAULT_PER_PILL_UG = 0.25  # μg
DEFAULT_FREQ = 2            # 次/周
REF_DAILY_RANGE = (2.5, 3.5)  # ng/kg/天，文献参考区间


def main():
    ap = argparse.ArgumentParser(description="骨化三醇分药计量（猫）")
    ap.add_argument("--weight", type=float, required=True, help="体重 kg")
    ap.add_argument("--per-pill", type=float, default=DEFAULT_PER_PILL_UG,
                    help="每粒规格 μg，默认 0.25")
    ap.add_argument("--freq", type=int, default=DEFAULT_FREQ,
                    help="每周给药次数，默认 2（周三晚空腹 + 周日早饭空腹）")
    a = ap.parse_args()

    w = a.weight
    per_dose_ng = w * NG_PER_KG_PER_DOSE
    pill_ng = a.per_pill * 1000
    parts = pill_ng / per_dose_ng
    parts_int = int(parts)
    daily_avg = per_dose_ng * a.freq / 7 / w

    print("=" * 58)
    print("骨化三醇分药计量（猫 CKD）")
    print("=" * 58)
    print(f"体重            : {w:.2f} kg")
    print(f"每粒规格        : {a.per_pill} μg ({pill_ng:.0f} ng)")
    print(f"给药频次        : 每周 {a.freq} 次")
    print()
    print(f"单次目标剂量    : {per_dose_ng:.1f} ng  (体重 × {NG_PER_KG_PER_DOSE} ng/kg)")
    print(f"每粒分成        : {parts:.2f} 份  →  实际操作取 {parts_int} 份")
    print(f"  (取整后单次实给 {pill_ng / parts_int:.1f} ng)")
    print()
    print(f"折算日均剂量    : {daily_avg:.2f} ng/kg/天")
    lo, hi = REF_DAILY_RANGE
    if lo <= daily_avg <= hi:
        print(f"                  ✓ 落在文献参考区间 {lo}-{hi} ng/kg/天 内")
    else:
        print(f"                  ⚠️ 超出文献参考区间 {lo}-{hi} ng/kg/天，请与兽医确认")
    print()
    print("-- 使用前提 --")
    print("  1. 离子钙必须正常")
    print("  2. 折耳猫、高血钙、肾结石 → 不用骨化三醇，改用普通鱼油")
    print("  3. 分装必须用肠溶胶囊")
    print("  4. 用骨化三醇/丰兹欧期间，其他含钙补剂和药需停用")
    print("  5. 谨慎同服：含钙磷结合剂、巴比妥类、皮质类固醇、含镁抗酸剂、噻嗪利尿剂")
    print("  6. 定期监测离子钙与血磷")
    print()
    print("※ 来源为猫友社群整理资料，非官方指南；剂量须经主治兽医确认")
    print("=" * 58)


if __name__ == "__main__":
    main()
