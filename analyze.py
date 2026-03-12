#!/usr/bin/env python3
"""健康数据分析 - 综合饮食 + 运动趋势分析

用法：
  python3 analyze.py            分析最近 7 天
  python3 analyze.py --days 14  分析最近 14 天
"""

import sys
import json
import os
from datetime import date, timedelta

# ─── ANSI 颜色 ────────────────────────────────────────────────────────────────
R   = "\033[0m"
B   = "\033[1m"
DIM = "\033[2m"
GRN = "\033[92m"
YEL = "\033[93m"
BLU = "\033[94m"
MAG = "\033[95m"
CYN = "\033[96m"
RED = "\033[91m"

# ─── 配置（与 diet.py 一致）──────────────────────────────────────────────────
DATA_DIR       = os.path.join(os.path.dirname(__file__), "data")
LOG_FILE       = os.path.join(DATA_DIR, "food_log.json")
FIXED_ACT_FILE = os.path.join(DATA_DIR, "fixed_activities.json")
CAL_WORKOUT = 2300
CAL_REST    = 2000
SCHEDULE    = {0: "workout", 1: "workout", 2: "rest",
               3: "workout", 4: "workout", 5: "rest", 6: "rest"}
WORKOUT_NAME = {0: "A 上肢推力", 1: "B 下肢力量", 2: "休息",
                3: "C 拉力+核心", 4: "D 全身HIIT", 5: "休息", 6: "休息"}
DAY_CN      = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ─── 数据加载 ─────────────────────────────────────────────────────────────────
def load_log() -> dict:
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_fixed_activities() -> list:
    if not os.path.exists(FIXED_ACT_FILE):
        return []
    with open(FIXED_ACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("activities", [])

def day_target(weekday: int) -> int:
    return CAL_WORKOUT if SCHEDULE[weekday] == "workout" else CAL_REST

def food_calories(day_log: dict) -> int:
    return sum(
        v.get("calories", 0)
        for k, v in day_log.items()
        if k != "activity" and isinstance(v, dict)
    )

def activity_burned(day_log: dict) -> int:
    return sum(a.get("kcal_burned", 0) for a in day_log.get("activity", []))

def activity_list(day_log: dict) -> list:
    return day_log.get("activity", [])

# ─── 工具函数 ─────────────────────────────────────────────────────────────────
def sep(char="═", n=54):
    print(f"{CYN}{char * n}{R}")

def bar(val, total, width=24, color=None):
    ratio  = min(val / total, 1.0) if total > 0 else 0
    filled = int(ratio * width)
    b      = "█" * filled + "░" * (width - filled)
    if color is None:
        color = GRN if ratio <= 0.85 else (YEL if ratio <= 1.0 else RED)
    return f"{color}{b}{R}"

def trend_arrow(vals):
    """简单趋势：比较前半段和后半段均值"""
    if len(vals) < 2:
        return ""
    mid  = len(vals) // 2
    avg1 = sum(vals[:mid]) / mid if mid else 0
    avg2 = sum(vals[mid:]) / (len(vals) - mid) if (len(vals) - mid) else 0
    diff = avg2 - avg1
    if diff > 50:
        return f" {YEL}↑{R}"
    elif diff < -50:
        return f" {GRN}↓{R}"
    return f" {DIM}→{R}"

# ─── 核心分析 ─────────────────────────────────────────────────────────────────
def analyze(days: int = 7):
    log   = load_log()
    today = date.today()

    # 收集区间数据
    fixed_acts        = load_fixed_activities()
    fixed_daily_burn  = sum(a.get("kcal_burned", 0) for a in fixed_acts)

    records = []
    for i in range(days - 1, -1, -1):
        d       = today - timedelta(days=i)
        weekday = d.weekday()
        key     = d.isoformat()
        dlog    = log.get(key, {})
        intake  = food_calories(dlog)
        extra_b = activity_burned(dlog)
        total_b = fixed_daily_burn + extra_b
        target  = day_target(weekday)
        records.append({
            "date":        d,
            "weekday":     weekday,
            "target":      target,
            "intake":      intake,
            "burned":      total_b,
            "fixed_burn":  fixed_daily_burn,
            "extra_burn":  extra_b,
            "net":         intake - total_b,
            "activities":  activity_list(dlog),
            "logged":      bool(dlog),
        })

    recorded = [r for r in records if r["logged"]]
    n_rec    = len(recorded)

    # ── 标题 ────────────────────────────────────────────────────────────────
    start_str = records[0]["date"].strftime("%m/%d")
    end_str   = records[-1]["date"].strftime("%m/%d")
    sep()
    print(f"{B}{CYN}  📊 健康数据分析{R}  {DIM}{start_str} ~ {end_str}（{days}天）{R}")
    sep()
    print()

    # ── 1. 每日热量摄入一览 ──────────────────────────────────────────────────
    print(f"{B}{BLU}【每日热量摄入】{R}\n")
    intake_vals = []
    for r in records:
        d       = r["date"]
        is_today = d == today
        bd      = B if is_today else ""
        marker  = f" {CYN}今{R}" if is_today else ""
        wname   = WORKOUT_NAME[r["weekday"]]
        target  = r["target"]

        if not r["logged"]:
            print(f"  {bd}{d.strftime('%m/%d')} {DAY_CN[r['weekday']]}{R}  "
                  f"{DIM}无记录  目标{target}kcal{R}{marker}")
            continue

        intake = r["intake"]
        intake_vals.append(intake)
        burned = r["burned"]
        net    = r["net"]
        b      = bar(intake, target)
        pct    = int(intake / target * 100) if target else 0

        diff = intake - target
        if diff > 100:
            diff_str = f"{RED}+{diff}{R}"
        elif diff < -200:
            diff_str = f"{YEL}{diff}{R}"
        else:
            diff_str = f"{GRN}≈达标{R}"

        burned = r["burned"]
        net    = r["net"]
        burned_str = f"  {DIM}消耗-{burned}kcal（固定{r['fixed_burn']}+额外{r['extra_burn']}）→ 净{net}kcal{R}" if burned else ""
        print(f"  {bd}{d.strftime('%m/%d')} {DAY_CN[r['weekday']]}{R}  "
              f"{b} {B}{pct}%{R}  {intake}/{target}  {diff_str}{burned_str}{marker}")

    print()

    # ── 2. 统计摘要 ──────────────────────────────────────────────────────────
    sep("─")
    print()
    print(f"{B}{BLU}【摘要统计】{R}\n")

    if n_rec == 0:
        print(f"  {DIM}暂无记录，快去记录第一天吧！{R}\n")
    else:
        avg_intake  = sum(r["intake"] for r in recorded) / n_rec
        avg_target  = sum(r["target"] for r in recorded) / n_rec
        total_burned = sum(r["burned"] for r in records)
        avg_net      = sum(r["net"] for r in recorded) / n_rec
        adherence   = sum(1 for r in recorded if abs(r["intake"] - r["target"]) <= 200) / n_rec * 100
        t_arrow     = trend_arrow(intake_vals)

        print(f"  记录天数        {B}{n_rec}{R} / {days} 天  "
              f"{DIM}({'%.0f' % (n_rec/days*100)}% 完成率){R}")
        print(f"  日均摄入        {B}{'%.0f' % avg_intake}{R} kcal  "
              f"{DIM}（目标均值 {'%.0f' % avg_target}kcal）{R}{t_arrow}")
        print(f"  热量达标天数    {B}{sum(1 for r in recorded if abs(r['intake']-r['target'])<=200)}{R} 天  "
              f"{DIM}（误差±200kcal内）{R}")
        print(f"  总运动消耗      {B}{total_burned}{R} kcal  "
              f"{DIM}（固定{fixed_daily_burn*n_rec} + 额外{total_burned - fixed_daily_burn*n_rec}）{R}")
        print(f"  日均净摄入      {B}{'%.0f' % avg_net}{R} kcal  "
              f"{DIM}（摄入 - 运动消耗）{R}")
        print()

    # ── 3. 运动记录 ──────────────────────────────────────────────────────────
    sep("─")
    print()
    print(f"{B}{BLU}【运动记录】{R}\n")

    # 固定运动
    print(f"  {DIM}── 每日固定运动（自动计入）───────────────{R}")
    for a in fixed_acts:
        print(f"  {BLU}●{R} {a['name']}  {a['duration_min']}分钟  {DIM}{a['intensity']}{R}  "
              f"~{a['kcal_burned']}kcal/天")
    print(f"  {DIM}固定运动合计：~{fixed_daily_burn}kcal/天  ×{days}天 = ~{fixed_daily_burn*days}kcal{R}\n")

    # 额外运动
    all_extra = [(r["date"], a) for r in records for a in r["activities"]]
    if all_extra:
        print(f"  {DIM}── 额外运动记录 ─────────────────────{R}")
        for d, a in all_extra:
            print(f"  {GRN}✓{R} {d.strftime('%m/%d')} {DAY_CN[d.weekday()]}  "
                  f"{B}{a['name']}{R}  {a['duration_min']}分钟  "
                  f"{DIM}{a['intensity']}{R}  ~{a.get('kcal_burned',0)}kcal")
        extra_min = sum(a.get("duration_min", 0) for _, a in all_extra)
        print(f"  {DIM}额外运动累计：{extra_min} 分钟{R}")
    else:
        print(f"  {DIM}── 暂无额外运动记录 ─────────────────{R}")
    print()

    # ── 4. 分析洞察 ──────────────────────────────────────────────────────────
    sep("─")
    print()
    print(f"{B}{BLU}【分析与建议】{R}\n")

    insights = []

    if n_rec == 0:
        insights.append(("⚠", YEL, "还没有饮食记录，坚持每天告诉 Claude 你吃了什么"))
    else:
        # 记录率
        rec_rate = n_rec / days
        if rec_rate < 0.5:
            insights.append(("⚠", YEL, f"记录率偏低（{n_rec}/{days}天），建议每天坚持记录，数据越多分析越准"))
        elif rec_rate >= 0.85:
            insights.append(("✓", GRN, f"记录很规律（{n_rec}/{days}天），继续保持！"))

        # 热量趋势
        if intake_vals:
            avg_in = sum(intake_vals) / len(intake_vals)
            if avg_in < avg_target * 0.80:
                insights.append(("⚠", YEL,
                    f"平均摄入偏低（{avg_in:.0f}kcal，目标{avg_target:.0f}kcal），长期吃太少会导致肌肉流失"))
            elif avg_in > avg_target * 1.15:
                insights.append(("⚠", RED,
                    f"平均摄入偏高（{avg_in:.0f}kcal，目标{avg_target:.0f}kcal），注意控制热量"))
            else:
                insights.append(("✓", GRN, f"热量摄入整体控制不错（均值{avg_in:.0f}kcal）"))

        # 运动频率
        workout_days_in_period = sum(
            1 for r in records
            if SCHEDULE[r["weekday"]] == "workout"
        )
        extra_activity_days = sum(1 for r in records if r["activities"])
        if extra_activity_days > 0:
            insights.append(("✓", GRN,
                f"有{extra_activity_days}天记录了额外运动，保持日常活动量很有益"))

        # 低蛋白质食物提醒（基于食物描述关键词检测）
        low_protein_days = 0
        for r in recorded:
            dlog = log.get(r["date"].isoformat(), {})
            all_foods = " ".join(
                v.get("foods", "") for k, v in dlog.items()
                if k != "activity" and isinstance(v, dict)
            )
            has_protein = any(kw in all_foods for kw in [
                "鸡胸", "鸡蛋", "蛋", "鱼", "虾", "牛肉", "猪肉",
                "豆腐", "牛奶", "酸奶", "蛋白"
            ])
            if not has_protein:
                low_protein_days += 1
        if low_protein_days > 0:
            insights.append(("⚠", YEL,
                f"有{low_protein_days}天饮食中蛋白质来源不明显，注意每餐搭配鸡蛋/肉/豆腐等"))

    for icon, color, msg in insights:
        print(f"  {color}{icon}{R} {msg}")

    print()
    sep()
    print(f"  {DIM}python3 analyze.py --days 14  查看更长周期{R}")
    sep()
    print()


# ─── 主程序 ───────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    days = 7
    if "--days" in args:
        idx = args.index("--days")
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            days = int(args[idx + 1])
    analyze(days)

if __name__ == "__main__":
    main()
