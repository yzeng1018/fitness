#!/usr/bin/env python3
"""晚间健身日报 - 每天 22:00 自动运行，总结当日饮食与训练

用法：
  python3 evening_report.py        查看今日日报
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from diet import (
    load_log, load_fixed_activities,
    day_calorie_total, day_activity_list,
    MEAL_CN, SCHEDULE, CAL_WORKOUT, CAL_REST,
    DAY_CN, WEIGHT_CURRENT, WEIGHT_GOAL,
)
from fitness import TDEE
from datetime import date

R="\033[0m"; B="\033[1m"; DIM="\033[2m"
GRN="\033[92m"; YEL="\033[93m"; BLU="\033[94m"
MAG="\033[95m"; CYN="\033[96m"; RED="\033[91m"

def sep(char="═", n=58): print(f"{CYN}{char*n}{R}")

def assess(net, target):
    deficit = target - net
    if deficit >= 300:
        return f"{GRN}✓ 赤字合理（{deficit}kcal），减脂有效{R}"
    elif deficit >= 100:
        return f"{YEL}~ 赤字偏小（{deficit}kcal），明天可再控一点{R}"
    elif deficit >= -150:
        return f"{YEL}≈ 基本持平（{abs(deficit)}kcal 差距），略有波动无妨{R}"
    else:
        return f"{RED}↑ 今日超标 {-deficit}kcal，明天适度少吃{R}"

def main():
    today = date.today()
    weekday = today.weekday()
    is_workout = SCHEDULE[weekday] == "workout"
    target = CAL_WORKOUT if is_workout else CAL_REST
    day_type = "训练日" if is_workout else "休息日"

    log = load_log()
    fixed_acts = load_fixed_activities()
    today_log = log.get(today.isoformat(), {})

    sep()
    print(f"{B}{CYN}  📊 今日健身日报{R}   "
          f"{B}{today.strftime('%Y年%m月%d日')} {DAY_CN[weekday]}{R}  "
          f"{DIM}({day_type}){R}")
    print(f"  {DIM}目标：{WEIGHT_CURRENT}kg → {WEIGHT_GOAL}kg | TDEE≈{TDEE}kcal | 今日摄入目标 {target}kcal{R}")
    sep()

    # ── 饮食记录 ──────────────────────────────────────────────────────────
    print(f"\n{B}{BLU}  饮食{R}\n")
    total_intake = 0
    if not any(k in today_log for k in MEAL_CN):
        print(f"  {YEL}⚠ 今日暂无饮食记录{R}")
    else:
        col_w = 26
        print(f"  {'餐次':<6}  {'热量':>6}  {'内容'}")
        print(f"  {'─'*6}  {'─'*6}  {'─'*col_w}")
        for key, cn in MEAL_CN.items():
            entry = today_log.get(key)
            if not entry:
                continue
            cal = entry.get("calories", 0)
            foods = entry.get("foods", "")
            total_intake += cal
            foods_short = foods[:col_w] + ("…" if len(foods) > col_w else "")
            print(f"  {cn:<6}  {B}{cal:>5}{R}  {DIM}{foods_short}{R}")
        print(f"  {'─'*6}  {'─'*6}")
        print(f"  {'合计':<6}  {B}{total_intake:>5}{R}  {DIM}目标 {target}kcal{R}")

    # ── 运动记录 ──────────────────────────────────────────────────────────
    fixed_burn = sum(a.get("kcal_burned", 0) for a in fixed_acts)
    extra_acts = day_activity_list(today_log)
    extra_burn = sum(a.get("kcal_burned", 0) for a in extra_acts)
    total_burn = fixed_burn + extra_burn

    print(f"\n{B}{BLU}  运动{R}\n")
    if extra_acts:
        for a in extra_acts:
            print(f"  {GRN}✓{R} {a['name']}  {a['duration_min']}分钟  ~{a.get('kcal_burned',0)}kcal")
    else:
        print(f"  {DIM}无额外运动记录{R}")
    print(f"  {DIM}固定运动（遛狗/步行）~{fixed_burn}kcal 自动计入{R}")
    print(f"  {DIM}运动总消耗 ~{total_burn}kcal{R}")

    # ── 热量平衡 ──────────────────────────────────────────────────────────
    net = total_intake - total_burn
    deficit = target - net

    print(f"\n{B}{BLU}  热量平衡{R}\n")
    print(f"  {'总摄入':<8}  {B}{total_intake:>5}{R} kcal")
    print(f"  {'运动消耗':<8}  {B}-{total_burn:>4}{R} kcal")
    print(f"  {'净摄入':<8}  {B}{net:>5}{R} kcal  {DIM}（目标 ≤{target}kcal）{R}")
    print(f"  {'赤字':<8}  {B}{deficit:>5}{R} kcal")

    # ── 评估 ──────────────────────────────────────────────────────────────
    sep("─")
    print(f"\n  {assess(net, target)}\n")
    sep()
    print(f"  {DIM}记录遗漏？明天早上 7:30 日报会提醒你补录{R}")
    sep()
    print()

if __name__ == "__main__":
    main()
