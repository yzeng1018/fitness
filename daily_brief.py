#!/usr/bin/env python3
"""每日健康简报 - 昨日回顾 + 今日训练 + 今日饮食

由 launchd 在每天 7:30 自动打开终端窗口运行
也可手动运行：python3 daily_brief.py
"""

import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))

# 从已有模块复用数据和函数
# fitness.py: SCHEDULE 格式为 {weekday: "A"/"B"/"rest"/"C"/"D"}
# diet.py:    SCHEDULE 格式为 {weekday: "workout"/"rest"}
from fitness import WORKOUTS, USER, TDEE
from fitness import SCHEDULE as FIT_SCHEDULE   # weekday → workout key
from diet import (WEEKLY_PLAN, CAL_WORKOUT, CAL_REST, PROTEIN_G, FAT_G,
                  MEAL_CN, LIVER_AVOID, LIVER_GOOD, DAY_CN, WORKOUT_NAME,
                  SCHEDULE as DIET_SCHEDULE,   # weekday → "workout"/"rest"
                  load_log, load_fixed_activities,
                  day_calorie_total, day_activity_list)

from datetime import date, timedelta

# ─── ANSI 颜色 ────────────────────────────────────────────────────────────────
R="\033[0m"; B="\033[1m"; DIM="\033[2m"
GRN="\033[92m"; YEL="\033[93m"; BLU="\033[94m"
MAG="\033[95m"; CYN="\033[96m"; RED="\033[91m"

def sep(char="═", n=58): print(f"{CYN}{char*n}{R}")
def sec(title): print(f"\n{B}{BLU}{title}{R}\n")

def pbar(cur, total, w=26):
    r = min(cur/total, 1.0) if total else 0
    filled = int(r * w)
    color = GRN if r <= 0.9 else (YEL if r <= 1.05 else RED)
    return f"{color}{'█'*filled}{'░'*(w-filled)}{R} {B}{int(r*100)}%{R}"

def has_protein(foods_str: str) -> bool:
    keywords = ["鸡胸","鸡蛋","蛋","鱼","虾","牛肉","猪肉","豆腐","牛奶","酸奶","三文鱼","鲭鱼","蛋白"]
    return any(k in foods_str for k in keywords)

def day_target(weekday): return CAL_WORKOUT if DIET_SCHEDULE[weekday]=="workout" else CAL_REST
def is_workout(weekday): return DIET_SCHEDULE[weekday] == "workout"


# ════════════════════════════════════════════════════════════════════════
# 昨日回顾
# ════════════════════════════════════════════════════════════════════════
def print_yesterday(log, fixed_acts):
    yesterday = date.today() - timedelta(days=1)
    yd_weekday = yesterday.weekday()
    yd_key = yesterday.isoformat()
    yd_log = log.get(yd_key, {})
    target = day_target(yd_weekday)
    wtype = "训练日" if is_workout(yd_weekday) else "休息日"

    sep("─")
    print(f"\n{B}【昨日回顾】{R}  {DIM}{yesterday.strftime('%m/%d')} "
          f"{DAY_CN[yd_weekday]}（{wtype} · 目标{target}kcal）{R}\n")

    if not yd_log:
        print(f"  {YEL}⚠ 昨天没有饮食记录。{R}")
        print(f"  {DIM}今天吃了什么随时告诉 Claude 来补录。{R}\n")
    else:
        # 饮食
        print(f"  {B}饮食记录{R}")
        all_foods = ""
        for key, cn in MEAL_CN.items():
            entry = yd_log.get(key)
            if entry:
                all_foods += entry.get("foods", "")
                cal_str = f"{DIM}{entry['calories']}kcal{R}"
                print(f"  {GRN}·{R} {cn:<8} {cal_str:<20} {DIM}{entry['foods']}{R}")

        eaten = day_calorie_total(yd_log)
        fixed_burn = sum(a.get("kcal_burned",0) for a in fixed_acts)
        extra_acts = day_activity_list(yd_log)
        extra_burn = sum(a.get("kcal_burned",0) for a in extra_acts)
        total_burn = fixed_burn + extra_burn
        net = eaten - total_burn

        print(f"\n  摄入 {B}{eaten}{R}/{target} kcal  {pbar(eaten, target)}")

        diff = eaten - target
        if abs(diff) <= 150:
            status = f"{GRN}✓ 达标{R}"
        elif diff < -150:
            status = f"{YEL}↓ 偏少 {-diff}kcal{R}"
        else:
            status = f"{RED}↑ 超标 +{diff}kcal{R}"
        print(f"  状态：{status}  {DIM}净摄入（扣除运动）：{net}kcal{R}")

        # 蛋白质检查
        if not has_protein(all_foods):
            print(f"\n  {YEL}⚠ 昨日蛋白质来源不明显，今天注意每餐补充鸡蛋/肉/鱼/豆腐{R}")

        # 昨日额外运动
        if extra_acts:
            print(f"\n  {B}额外运动{R}")
            for a in extra_acts:
                print(f"  {GRN}✓{R} {a['name']}  {a['duration_min']}分钟  ~{a.get('kcal_burned',0)}kcal")

    print(f"\n  {DIM}固定运动 ~{sum(a.get('kcal_burned',0) for a in fixed_acts)}kcal 每日自动计入（遛狗×2 + 步行上下班）{R}")


# ════════════════════════════════════════════════════════════════════════
# 今日训练
# ════════════════════════════════════════════════════════════════════════
def print_today_workout(weekday):
    key = FIT_SCHEDULE[weekday]
    sep("─")
    print()

    if key == "rest":
        print(f"{B}【今日训练】{R}  {GRN}🌿 休息日{R}\n")
        print(f"  轻度拉伸或散步 20-30 分钟即可。")
        print(f"  今天是肌肉恢复和脂肪燃烧的重要时间，保证睡眠 7-8 小时。\n")
        return

    w = WORKOUTS[key]
    print(f"{B}【今日训练】{R}  {B}{w['name']}{R}  {DIM}({w['focus']}){R}  "
          f"{DIM}预计{w['duration']}{R}\n")

    print(f"  {B}{YEL}热身{R}  {DIM}{' · '.join(w['warmup'])}{R}\n")

    print(f"  {B}{YEL}正式训练{R}")
    for i, (name, sets_reps, rest, note) in enumerate(w["exercises"], 1):
        print(f"  {B}{i}.{R} {name:<14} {GRN}{sets_reps:<16}{R} 休息{rest}  {DIM}→ {note}{R}")

    print(f"\n  {B}{YEL}拉伸放松{R}  {DIM}{' · '.join(w['cooldown'])}{R}")
    print(f"\n  {MAG}💡 {w['tips']}{R}\n")


# ════════════════════════════════════════════════════════════════════════
# 今日饮食
# ════════════════════════════════════════════════════════════════════════
def print_today_diet(weekday, log, fixed_acts):
    plan = WEEKLY_PLAN[weekday]
    target = plan["target"]
    today_log = log.get(date.today().isoformat(), {})
    wtype = "训练日" if is_workout(weekday) else "休息日"
    carbs_g = max(0, (target - PROTEIN_G*4 - FAT_G*9)//4)

    sep("─")
    print()
    print(f"{B}【今日饮食】{R}  {DIM}({wtype}) 目标 {target}kcal · "
          f"蛋白质{GRN}{PROTEIN_G}g{R} · 碳水{YEL}{carbs_g}g{R} · 脂肪{RED}{FAT_G}g{R}\n")

    plan_total = 0
    for key, cn in MEAL_CN.items():
        meal = plan["meals"].get(key)
        if not meal:
            continue
        cal, foods = meal
        plan_total += cal
        logged = today_log.get(key)

        if logged:
            status = f"{GRN}✓ 已记录 {logged['calories']}kcal · {logged['foods']}{R}"
        else:
            foods_str = " · ".join(foods[:3]) + ("..." if len(foods)>3 else "")
            status = f"{DIM}○ 未记录  参考：{foods_str}{R}"

        print(f"  {B}{YEL}{cn:<8}{R} ~{cal}kcal  {status}")

    # 固定运动提示
    fixed_burn = sum(a.get("kcal_burned",0) for a in fixed_acts)
    net_target = target - fixed_burn
    print(f"\n  {DIM}固定运动消耗 ~{fixed_burn}kcal → 实际净摄入目标约 {net_target}kcal{R}\n")

    # 今日重点食物（脂肪肝）
    today_plan_text = str(plan["meals"])
    omega3 = "三文鱼" in today_plan_text or "鲭鱼" in today_plan_text or "沙丁鱼" in today_plan_text
    crucif = "西兰花" in today_plan_text or "卷心菜" in today_plan_text
    coffee = "咖啡" in today_plan_text

    highlights = []
    if omega3:  highlights.append(f"{GRN}🐟 今日omega-3日（深海鱼）{R}")
    if crucif:  highlights.append(f"{GRN}🥦 十字花科蔬菜（护肝）{R}")
    if coffee:  highlights.append(f"{GRN}☕ 无糖黑咖啡（护肝）{R}")
    if highlights:
        print(f"  今日重点食物：{'  '.join(highlights)}")
        print()


# ════════════════════════════════════════════════════════════════════════
# 主函数
# ════════════════════════════════════════════════════════════════════════
def main():
    today = date.today()
    weekday = today.weekday()
    log = load_log()
    fixed_acts = load_fixed_activities()

    wname = WORKOUT_NAME[weekday]
    wtype = "训练日" if is_workout(weekday) else "休息日"

    # 标题
    sep()
    print(f"{B}{CYN}  📋 每日健康简报{R}   "
          f"{B}{today.strftime('%Y年%m月%d日')} {DAY_CN[weekday]}{R}  "
          f"{DIM}({wtype} · {wname}){R}")
    print(f"  {DIM}目标：减脂 + 脂肪肝调理 | {USER['height']}cm {USER['weight']}kg | "
          f"TDEE≈{TDEE}kcal | 今日目标 "
          f"{'%d'%CAL_WORKOUT if is_workout(weekday) else '%d'%CAL_REST}kcal{R}")
    sep()

    # 昨日回顾
    print_yesterday(log, fixed_acts)

    # 今日训练
    print_today_workout(weekday)

    # 今日饮食
    print_today_diet(weekday, log, fixed_acts)

    # 脂肪肝提醒
    sep("─")
    print()
    print(f"  {RED}✗ 今日禁忌：{R}{DIM}{'  ·  '.join(LIVER_AVOID)}{R}")
    print(f"  {GRN}✓ 护肝重点：{R}{DIM}{'  ·  '.join(LIVER_GOOD)}{R}")
    print()

    sep()
    print(f"  {DIM}记录饮食/运动：直接告诉 Claude 即可{R}")
    print(f"  {DIM}快速查看：python3 diet.py  |  python3 analyze.py{R}")
    sep()
    print()

if __name__ == "__main__":
    main()
