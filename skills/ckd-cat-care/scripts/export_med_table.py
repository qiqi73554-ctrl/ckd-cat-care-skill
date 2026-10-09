#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把原始 CKD 用药清单（.ksheet 导出的 rangeData JSON）整理成结构化 Excel。

用法:
  python export_med_table.py --src <rangeData.json> --out <输出.xlsx>

输出 3 个工作表：
  1. 用药清单      —— 分类已向下填充，注意事项合并，图片列剔除
  2. 骨化三醇分药速查
  3. 血磷分级换算  —— 解决资料用 mmol/L、IRIS 用 mg/dL 的单位混乱
"""

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# 列索引（对应原表表头）
C1, C2, C3 = 0, 1, 2
NAME, STAGE = 3, 4
NOTE_COLS = (5, 6, 7, 8)
SPEC = 9
ROUTE, DOSE_CAT, DOSE_DOG = 15, 16, 17

HEADER_BG = "2F5597"      # 蓝底
HEADER_FG = "FFFFFF"      # 白字
NOTE_BG = "FFF2CC"        # 说明行淡黄
WARN_BG = "FCE4E4"        # 单位警告淡红
GAP_BG = "FFE699"         # 信息不全 橙黄

# 原表「肝胆等」工作表的数据，主表未包含，手工补入
EXTRA_ROWS = [
    ("肝胆等", "胆", "", "优思弗熊去氧", "", "", "餐后口服",
     "10-15mg/kg/天；多餐按15mg/kg算总量分三次", "", "肠溶胶囊", ""),
    ("肝胆等", "肝胆", "", "思美泰", "", "", "口服",
     "1-2次/天（每次20mg/kg）", "", "肠溶胶囊", ""),
    ("肝胆等", "肝", "", "谷胱甘肽片", "", "", "口服",
     "以5.35kg猫为例：1片/次，3次/天", "",
     "不得与维生素B12、甲萘醌、泛酸钙、乳清酸、抗组胺制剂、磺胺药及四环素混合使用", ""),
    ("肝胆等", "结石", "", "鸡内金生粉", "", "", "口服",
     "1次/天，2片/次", "",
     "1.有助于膀胱结晶排出\n2.胆结石可用\n3.肾结石有人试过一周没用，长期未知", ""),
    ("肝胆等", "消炎", "", "甲硝唑", "", "", "口服",
     "10-20mg/kg", "", "需自行购买", ""),
]

HEADERS = ["序号", "一级分类", "二级分类", "三级分类", "药物名称", "建议使用分期",
           "规格", "给药方式", "猫用量", "狗用量", "注意事项", "备注"]


def load_rows(src):
    d = json.load(open(src, encoding="utf-8"))
    cells = d["data"]["detail"]["rangeData"]
    grid = {}
    maxr = 0
    for c in cells:
        r0 = c["rowFrom"]
        r1 = c.get("rowTo", r0)
        col = c["colFrom"]
        t = (c.get("cellText") or "").strip()
        if not t or "DISPIMG" in t:
            continue
        if col <= C3:
            # 分类列：合并单元格向下填充，竖排换行压平
            flat = t.replace("\n", "")
            for rr in range(r0, r1 + 1):
                grid[(rr, col)] = flat
        else:
            grid[(r0, col)] = t
        maxr = max(maxr, r1)

    def g(r, col):
        return grid.get((r, col), "")

    rows = []
    for r in range(6, maxr + 1):
        name = g(r, NAME)
        if not name:
            continue
        notes = [g(r, c) for c in NOTE_COLS if g(r, c) and "DISPIMG" not in g(r, c)]
        rows.append({
            "c1": g(r, C1), "c2": g(r, C2), "c3": g(r, C3),
            "name": name, "stage": g(r, STAGE), "spec": g(r, SPEC),
            "route": g(r, ROUTE), "cat": g(r, DOSE_CAT), "dog": g(r, DOSE_DOG),
            "notes": "\n".join(notes),
        })
    return rows


def unit_flag(row):
    """标注单位陷阱：资料混用 mmol/L 与 mg/dL，且碳酸氢根也用 mmol/L"""
    blob = row["notes"] + row["cat"]
    if "血磷" in blob or "PHOS" in blob:
        return "⚠️ 血磷单位 mmol/L（×3.1≈mg/dL）"
    if "碳酸氢" in blob:
        return "碳酸氢根单位 mmol/L（猫目标 16-24）"
    if "血钾" in blob or "血气" in blob:
        return "血气值以雅培血气为准"
    if "mmol" in blob:
        return "注意单位为 mmol/L"
    return ""


def style_sheet(ws, headers, widths, title, freeze="A3"):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    cell = ws.cell(row=1, column=1, value=title)
    cell.fill = PatternFill("solid", fgColor=NOTE_BG)
    cell.font = Font(name="微软雅黑", size=10, color="833C00")
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 34

    for i, h in enumerate(headers, 1):
        c = ws.cell(row=2, column=i, value=h)
        c.fill = PatternFill("solid", fgColor=HEADER_BG)
        c.font = Font(name="微软雅黑", size=10, bold=True, color=HEADER_FG)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 26

    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = freeze


def thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)


def core_missing(row):
    """核心字段缺口：猫用量 / 给药方式 / 注意事项与规格全无"""
    miss = []
    if not row["cat"]:
        miss.append("猫用量")
    if not row["route"]:
        miss.append("给药方式")
    if not row["notes"] and not row["spec"]:
        miss.append("注意事项/规格")
    return miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="rangeData JSON 路径")
    ap.add_argument("--out", required=True, help="输出 xlsx 路径")
    a = ap.parse_args()

    rows = load_rows(a.src)

    from collections import Counter
    dups = {n for n, c in
            Counter(r["name"].replace("\n", "").strip() for r in rows).items() if c > 1}

    wb = Workbook()

    # ---------- Sheet1 用药清单 ----------
    ws = wb.active
    ws.title = "用药清单"
    style_sheet(
        ws, HEADERS,
        [6, 12, 12, 10, 24, 13, 20, 14, 34, 16, 62, 24],
        "来源：CKD、PKD 用药清单 by 肘肉菲妈（金山文档）　|　"
        "本表为整理版：分类已向下填充、注意事项合并、图片列已剔除　|　"
        "⚠️ 剂量为猫友社群经验汇总，非官方指南，具体用药由主治兽医确定",
    )

    r = 3
    bd = thin_border()
    all_rows = [(x, False) for x in rows] + [(x, True) for x in
                [dict(zip(["c1", "c2", "c3", "name", "stage", "spec", "route",
                           "cat", "dog", "notes", "memo"], e)) for e in EXTRA_ROWS]]

    gap_rows = []
    for idx, (row, is_extra) in enumerate(all_rows, 1):
        memo = row.get("memo", "") or unit_flag(row)
        if is_extra:
            miss = []
        else:
            miss = core_missing(row)
            if len(miss) >= 2:
                gap_rows.append((idx, row, miss))
        vals = [idx, row["c1"], row["c2"], row["c3"], row["name"], row["stage"],
                row["spec"], row["route"], row["cat"], row["dog"], row["notes"], memo]
        for i, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=i, value=v)
            c.font = Font(name="微软雅黑", size=10)
            c.border = bd
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
        if len(miss) >= 2:
            for i in range(1, 13):
                ws.cell(row=r, column=i).fill = PatternFill("solid", fgColor=GAP_BG)
        if memo.startswith("⚠️"):
            ws.cell(row=r, column=12).fill = PatternFill("solid", fgColor=WARN_BG)
        if is_extra:
            ws.cell(row=r, column=2).fill = PatternFill("solid", fgColor="E2EFDA")
        r += 1

    ws.auto_filter.ref = f"A2:L{r-1}"

    # ---------- Sheet2 骨化三醇分药速查 ----------
    ws2 = wb.create_sheet("骨化三醇分药速查")
    h2 = ["体重 kg", "单次剂量 ng", "每粒(0.25μg)分成", "实给 ng/次", "折算日均 ng/kg/天", "是否在文献区间 2.5-3.5"]
    style_sheet(ws2, h2, [12, 16, 20, 14, 22, 28],
                "骨化三醇分药速查　|　给药时间：周三晚空腹 + 周日早饭空腹（每周 2 次）　|　"
                "公式：单次剂量 = 体重(kg) × 9 ng；份数 N = 250 ÷ (体重 × 9)")
    r = 3
    for w in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]:
        per = w * 9
        n = 250 / per
        ni = max(1, int(n))
        actual = 250 / ni
        daily = actual * 2 / 7 / w
        ok = "✓ 是" if 2.5 <= daily <= 3.5 else "✗ 否，需兽医确认"
        for i, v in enumerate([w, round(per, 1), ni, round(actual, 1), round(daily, 2), ok], 1):
            c = ws2.cell(row=r, column=i, value=v)
            c.font = Font(name="微软雅黑", size=10)
            c.border = bd
            c.alignment = Alignment(horizontal="center", vertical="center")
        if ok.startswith("✗"):
            ws2.cell(row=r, column=6).fill = PatternFill("solid", fgColor=WARN_BG)
        r += 1

    # ---------- Sheet3 血磷分级换算 ----------
    ws3 = wb.create_sheet("血磷分级换算")
    h3 = ["血磷 mmol/L", "血磷 mg/dL", "IRIS 2023 对应目标", "碳酸镧剂量（资料）", "说明"]
    style_sheet(ws3, h3, [14, 14, 30, 22, 46],
                "⚠️ 资料原表的血磷分级用 mmol/L，IRIS 2023 用 mg/dL —— 这是本表最容易搞错的地方　|　"
                "换算：mg/dL = mmol/L × 3.1")
    data3 = [
        (1.5, 4.65, "Stage 1-2 目标上限 4.6 mg/dL", "-", "IRIS 建议血磷控制在 2.7-4.6 mg/dL"),
        (1.6, 4.96, "Stage 3 目标上限 5.0 mg/dL", "-", "IRIS 2023：Stage 3 <5.0 mg/dL"),
        (1.9, 5.89, "-", "30 mg/kg/天", "资料：血磷 <1.9 mmol/L 用 30 mg/kg/天"),
        (1.94, 6.01, "Stage 4 目标上限 6.0 mg/dL", "-", "IRIS 2023：Stage 4 <6.0 mg/dL"),
        (2.25, 6.98, "-", "60 mg/kg/天", "资料：血磷 1.9-2.25 mmol/L 用 60 mg/kg/天"),
        (">2.25", ">7.0", "任何分期均需立即干预", "90 mg/kg/天", "资料：血磷 >2.25 mmol/L 用 90 mg/kg/天"),
    ]
    r = 3
    for row in data3:
        for i, v in enumerate(row, 1):
            c = ws3.cell(row=r, column=i, value=v)
            c.font = Font(name="微软雅黑", size=10)
            c.border = bd
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        if "IRIS" in row[2] or "干预" in row[2]:
            ws3.cell(row=r, column=3).fill = PatternFill("solid", fgColor="E2EFDA")
        r += 1

    r += 1
    ws3.cell(row=r, column=1,
             value="通用原则：磷结合剂随餐或餐后立即给予，空腹无效；"
                   "在普通粮上加结合剂效果不如直接换肾处方粮").font = Font(
        name="微软雅黑", size=10, color="833C00")

    # ---------- Sheet4 数据缺口 ----------
    ws4 = wb.create_sheet("数据缺口")
    h4 = ["类型", "清单序号", "一级分类 / 出现分类", "二级分类", "药物名称",
          "缺失字段 / 次数", "说明"]
    style_sheet(ws4, h4, [14, 14, 30, 14, 26, 22, 50],
                "整理过程中发现的原始数据缺口与跨分类重复项　|　"
                "「信息不全」对应「用药清单」中橙黄底纹的行，使用前须向原作者或兽医确认")

    r = 3
    for idx, row, miss in gap_rows:
        vals = ["信息不全", idx, row["c1"], row["c2"], row["name"].replace("\n", " "),
                "、".join(miss), "原表未填写任何剂量或用法，不可直接使用"]
        for i, v in enumerate(vals, 1):
            c = ws4.cell(row=r, column=i, value=v)
            c.font = Font(name="微软雅黑", size=10)
            c.border = bd
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws4.cell(row=r, column=1).fill = PatternFill("solid", fgColor=GAP_BG)
        r += 1

    for name in sorted(dups):
        hits = [(i, x) for i, (x, _) in enumerate(all_rows, 1)
                if x["name"].replace("\n", "").strip() == name]
        cats = " / ".join(f'{x["c1"]}·{x["c2"]}' if x["c2"] else x["c1"] for _, x in hits)
        vals = ["跨分类重复", "、".join(str(i) for i, _ in hits), cats, "", name,
                f"出现 {len(hits)} 次",
                "同一药在多个分类下重复列出（原表有意设计，用途不同），非两条不同记录"]
        for i, v in enumerate(vals, 1):
            c = ws4.cell(row=r, column=i, value=v)
            c.font = Font(name="微软雅黑", size=10)
            c.border = bd
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws4.cell(row=r, column=1).fill = PatternFill("solid", fgColor="DDEBF7")
        r += 1

    r += 1
    ws4.cell(row=r, column=1,
             value=f"统计：共 {len(all_rows)} 条，其中信息不全 {len(gap_rows)} 条、"
                   f"跨分类重复 {len(dups)} 组。").font = Font(
        name="微软雅黑", size=10, color="833C00")

    wb.save(a.out)
    print(f"已导出: {a.out}")
    print(f"用药清单 {len(all_rows)} 条（主表 {len(rows)} + 肝胆等 {len(EXTRA_ROWS)}）")
    print(f"信息不全 {len(gap_rows)} 条，跨分类重复 {len(dups)} 组")


if __name__ == "__main__":
    main()
