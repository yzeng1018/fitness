#!/usr/bin/env python3
"""饮食管理工具 - 每周饮食计划 + 每日记录追踪

用法：
  python3 diet.py              查看今日饮食计划 + 已记录情况
  python3 diet.py --log        记录一餐（交互输入）
  python3 diet.py --week       本周饮食计划一览
  python3 diet.py --history    查看最近7天记录
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

# ─── 数据文件 ─────────────────────────────────────────────────────────────────
DATA_DIR       = os.path.join(os.path.dirname(__file__), "data")
LOG_FILE       = os.path.join(DATA_DIR, "food_log.json")
FIXED_ACT_FILE = os.path.join(DATA_DIR, "fixed_activities.json")

# ─── 用户目标（与 fitness.py 保持一致）────────────────────────────────────────
CAL_WORKOUT = 2300
CAL_REST    = 2000
PROTEIN_G   = 130
FAT_G       = 55

# 每周训练安排
SCHEDULE = {0: "workout", 1: "workout", 2: "rest",
            3: "workout", 4: "workout", 5: "rest", 6: "rest"}
DAY_CN   = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WORKOUT_NAME = {0: "A 上肢推力", 1: "B 下肢力量", 2: "休息",
                3: "C 拉力+核心", 4: "D 全身HIIT", 5: "休息", 6: "休息"}

MEAL_KEYS   = ["breakfast", "lunch", "pre_workout", "dinner", "snack"]
MEAL_CN     = {
    "breakfast":   "早餐",
    "lunch":       "午餐",
    "pre_workout": "训练前加餐",
    "dinner":      "晚餐",
    "snack":       "加餐/零食",
}

# ─── 每周饮食计划（7天轮换，按周一=0对齐）────────────────────────────────────
# 格式：(餐次key, 参考热量, [食物列表])
WEEKLY_PLAN = {
    0: {  # 周一 - 训练日 A（上肢推力）2300kcal
        "target": CAL_WORKOUT,
        "meals": {
            "breakfast": (550, [
                "燕麦粥 50g（干重）",
                "水煮蛋 2个",
                "牛奶 250ml",
                "香蕉 1根",
            ]),
            "lunch": (700, [
                "糙米饭 150g（熟重）",
                "鸡胸肉 150g（清炒或水煮）",
                "西兰花 200g",
                "少量橄榄油",
            ]),
            "pre_workout": (200, [
                "香蕉 1根（运动前1小时）",
                "补水 500ml",
            ]),
            "dinner": (750, [
                "鸡胸肉 120g 或 鸡蛋白 3个",
                "红薯 150g",
                "混合蔬菜 250g",
                "豆腐 100g",
            ]),
            "snack": (100, [
                "坚果 15g（核桃/杏仁）",
            ]),
        },
    },
    1: {  # 周二 - 训练日 B（下肢力量）2300kcal
        "target": CAL_WORKOUT,
        "meals": {
            "breakfast": (550, [
                "全麦面包 2片",
                "炒蛋 2个",
                "豆浆 250ml（无糖）",
                "苹果 1个",
            ]),
            "lunch": (700, [
                "糙米饭 150g（熟重）",
                "瘦猪肉 120g（清蒸/炒）",
                "菠菜 150g + 番茄 100g",
                "少量植物油",
            ]),
            "pre_workout": (200, [
                "燕麦棒 1条 或 香蕉 1根",
                "补水 500ml",
            ]),
            "dinner": (750, [
                "清蒸鱼 150g",
                "土豆 130g（水煮）",
                "绿叶蔬菜大份 250g",
                "鸡蛋 1个",
            ]),
            "snack": (100, [
                "低脂牛奶 200ml",
            ]),
        },
    },
    2: {  # 周三 - 休息日 2000kcal
        "target": CAL_REST,
        "meals": {
            "breakfast": (500, [
                "燕麦粥 50g（干重）",
                "水煮蛋 2个",
                "坚果 15g",
                "橙子 1个",
            ]),
            "lunch": (700, [
                "杂粮饭 100g（熟重）",
                "虾 150g（白灼）",
                "豆腐 100g（红烧/清蒸）",
                "蔬菜 300g（大份）",
            ]),
            "dinner": (600, [
                "鸡胸肉 120g（柠檬蒸制）",
                "蔬菜沙拉 300g（少油醋汁）",
                "半碗米饭（约100g熟重）",
            ]),
            "snack": (200, [
                "希腊酸奶 150g（无糖）",
                "坚果 10g",
            ]),
        },
    },
    3: {  # 周四 - 训练日 C（拉力+核心）2300kcal
        "target": CAL_WORKOUT,
        "meals": {
            "breakfast": (550, [
                "全麦面包 2片",
                "水煮蛋 2个",
                "牛奶 250ml",
                "香蕉 1根",
            ]),
            "lunch": (700, [
                "糙米饭 150g（熟重）",
                "牛肉/猪里脊 120g",
                "西兰花+胡萝卜 200g",
                "少量橄榄油",
            ]),
            "pre_workout": (200, [
                "香蕉 1根（运动前1小时）",
                "补水 500ml",
            ]),
            "dinner": (750, [
                "鸡蛋 3个（炒蛋）",
                "红薯 150g",
                "混合蔬菜 250g",
                "豆腐 100g",
            ]),
            "snack": (100, [
                "坚果 15g 或 低脂牛奶 150ml",
            ]),
        },
    },
    4: {  # 周五 - 训练日 D（HIIT）2300kcal
        "target": CAL_WORKOUT,
        "meals": {
            "breakfast": (550, [
                "燕麦粥 50g（干重）",
                "鸡蛋 2个",
                "豆浆 250ml（无糖）",
                "蓝莓/草莓 100g",
            ]),
            "lunch": (700, [
                "糙米饭 150g（熟重）",
                "鸡胸肉 150g",
                "西兰花+彩椒 200g",
            ]),
            "pre_workout": (200, [
                "香蕉 1根（HIIT前1小时）",
                "补水 600ml（HIIT消耗大）",
            ]),
            "dinner": (750, [
                "虾 150g 或 鱼 180g",
                "糙米饭 100g（熟重）",
                "绿叶蔬菜大份 300g",
            ]),
            "snack": (100, [
                "希腊酸奶 100g",
            ]),
        },
    },
    5: {  # 周六 - 休息日 2000kcal
        "target": CAL_REST,
        "meals": {
            "breakfast": (500, [
                "全麦面包 2片",
                "炒蛋 2个",
                "牛奶 250ml",
                "苹果 1个",
            ]),
            "lunch": (700, [
                "杂粮饭 100g（熟重）",
                "豆腐 150g（麻婆/清蒸）",
                "瘦肉 100g",
                "蔬菜 250g",
            ]),
            "dinner": (600, [
                "鸡胸肉 120g",
                "蔬菜沙拉大份 300g",
                "少量主食（约半碗）",
            ]),
            "snack": (200, [
                "低脂酸奶 150g",
                "坚果 10g",
            ]),
        },
    },
    6: {  # 周日 - 休息日 2000kcal
        "target": CAL_REST,
        "meals": {
            "breakfast": (500, [
                "燕麦粥 50g（干重）",
                "坚果 20g",
                "水煮蛋 2个",
                "牛奶 200ml",
            ]),
            "lunch": (700, [
                "杂粮饭 100g（熟重）",
                "清蒸鱼 180g",
                "蔬菜 300g（任意绿叶菜）",
            ]),
            "dinner": (600, [
                "鸡胸肉沙拉（生菜+番茄+黄瓜+鸡肉120g）",
                "少量主食（半碗米饭）",
                "无糖酸汁调味",
            ]),
            "snack": (200, [
                "希腊酸奶 150g",
                "蓝莓/草莓 50g",
            ]),
        },
    },
}


# ─── 数据读写 ─────────────────────────────────────────────────────────────────
def load_log() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_log(log: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def load_fixed_activities() -> list:
    if not os.path.exists(FIXED_ACT_FILE):
        return []
    with open(FIXED_ACT_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("activities", [])

def today_str() -> str:
    return date.today().isoformat()

def get_day_log(log: dict, day: str) -> dict:
    return log.get(day, {})


# ─── 工具函数 ─────────────────────────────────────────────────────────────────
def sep(char="═", n=54):
    print(f"{CYN}{char * n}{R}")

def progress_bar(current: int, target: int, width: int = 28) -> str:
    ratio  = min(current / target, 1.0) if target > 0 else 0
    filled = int(ratio * width)
    bar    = "█" * filled + "░" * (width - filled)
    pct    = int(ratio * 100)
    color  = GRN if ratio <= 0.85 else (YEL if ratio <= 1.0 else RED)
    return f"{color}{bar}{R} {B}{pct}%{R}"

def day_calorie_total(day_log: dict) -> int:
    return sum(
        v.get("calories", 0)
        for k, v in day_log.items()
        if k != "activity" and isinstance(v, dict)
    )

def day_activity_list(day_log: dict) -> list:
    return day_log.get("activity", [])

def is_workout_day(weekday: int) -> bool:
    return SCHEDULE[weekday] == "workout"


# ─── 今日视图 ─────────────────────────────────────────────────────────────────
def show_today(log: dict):
    today   = date.today()
    weekday = today.weekday()
    plan    = WEEKLY_PLAN[weekday]
    target  = plan["target"]
    logged  = get_day_log(log, today_str())
    eaten   = day_calorie_total(logged)
    day_type = "训练日" if is_workout_day(weekday) else "休息日"
    workout_label = WORKOUT_NAME[weekday]

    sep()
    print(f"{B}{CYN}  🥗 饮食管理{R}                         {DIM}v1.0{R}")
    sep()
    print(f"  {B}今天：{R}{today.strftime('%Y年%m月%d日')} {B}{DAY_CN[weekday]}{R}  "
          f"{DIM}({day_type} · {workout_label}){R}")
    print(f"  热量目标：{B}{target} kcal{R}   "
          f"蛋白质 {GRN}{PROTEIN_G}g{R} · 碳水 {YEL}{(target - PROTEIN_G*4 - FAT_G*9)//4}g{R} · "
          f"脂肪 {RED}{FAT_G}g{R}")
    sep("─")
    print()

    # 计划 vs 已记录
    print(f"{B}{BLU}【今日饮食计划】{R}\n")
    for key, cn in MEAL_CN.items():
        meal_plan = plan["meals"].get(key)
        if not meal_plan:
            continue
        plan_cal, foods = meal_plan
        actual = logged.get(key)

        if actual:
            status = f"{GRN}✓ 已记录{R}  {DIM}{actual['calories']}kcal · {actual['foods']}{R}"
        else:
            status = f"{DIM}○ 未记录{R}"

        print(f"  {B}{YEL}▸ {cn}{R}  {DIM}约{plan_cal}kcal{R}  {status}")
        if not actual:
            for food in foods:
                print(f"    {DIM}· {food}{R}")
        print()

    # 今日运动记录
    fixed_acts   = load_fixed_activities()
    extra_acts   = day_activity_list(logged)
    fixed_burned = sum(a.get("kcal_burned", 0) for a in fixed_acts)
    extra_burned = sum(a.get("kcal_burned", 0) for a in extra_acts)
    total_burned = fixed_burned + extra_burned

    sep("─")
    print()
    print(f"{B}{BLU}【今日运动】{R}\n")
    print(f"  {DIM}── 固定运动（每日）─────────────────────{R}")
    for a in fixed_acts:
        print(f"  {BLU}●{R} {a['name']}  {a['duration_min']}分钟  "
              f"{DIM}{a['intensity']}{R}  ~{a['kcal_burned']}kcal")
    if extra_acts:
        print(f"  {DIM}── 额外运动 ─────────────────────────{R}")
        for a in extra_acts:
            print(f"  {GRN}✓{R} {B}{a['name']}{R}  {a['duration_min']}分钟  "
                  f"{DIM}{a['intensity']}{R}  ~{a.get('kcal_burned',0)}kcal")
    print(f"\n  {DIM}今日运动消耗合计：~{total_burned}kcal（固定{fixed_burned} + 额外{extra_burned}）{R}\n")

    # 当日热量进度
    sep("─")
    print()
    print(f"  {B}今日热量进度{R}")
    bar = progress_bar(eaten, target)
    print(f"  {bar}  {B}{eaten}{R} / {target} kcal")
    remaining = target - eaten
    if remaining > 0:
        print(f"  {DIM}还差 {remaining} kcal，继续加油！{R}")
    elif remaining == 0:
        print(f"  {GRN}完美达标！{R}")
    else:
        print(f"  {YEL}已超出目标 {-remaining} kcal{R}")
    net = eaten - total_burned
    print(f"  {DIM}净摄入（扣除运动消耗）：{net} kcal{R}")
    print()

    sep("─")
    print(f"  {DIM}python3 diet.py --log      记录一餐{R}")
    print(f"  {DIM}python3 diet.py --week     本周计划{R}")
    print(f"  {DIM}python3 diet.py --history  最近记录{R}")
    sep()
    print()


# ─── 交互记录一餐 ─────────────────────────────────────────────────────────────
def log_meal(log: dict) -> dict:
    today   = date.today()
    weekday = today.weekday()
    print()
    sep()
    print(f"{B}{CYN}  📝 记录一餐{R}  {DIM}{today.strftime('%Y年%m月%d日')} {DAY_CN[weekday]}{R}")
    sep()
    print()

    # 选择餐次
    meal_options = list(MEAL_CN.items())
    print(f"  {B}选择餐次：{R}")
    for i, (key, cn) in enumerate(meal_options, 1):
        plan = WEEKLY_PLAN[weekday]["meals"].get(key)
        ref  = f"{DIM}（参考 {plan[0]}kcal）{R}" if plan else ""
        print(f"    {B}{i}.{R} {cn} {ref}")
    print()

    while True:
        choice = input(f"  输入序号 (1-{len(meal_options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(meal_options):
            meal_key, meal_cn = meal_options[int(choice) - 1]
            break
        print(f"  {RED}请输入有效序号{R}")

    # 参考计划
    plan = WEEKLY_PLAN[weekday]["meals"].get(meal_key)
    if plan:
        print(f"\n  {DIM}今日参考 {meal_cn}：{R}")
        for food in plan[1]:
            print(f"    {DIM}· {food}{R}")
        print()

    # 输入吃了什么
    print(f"  {B}你吃了什么？{R}{DIM}（简单描述，如：糙米饭+鸡胸肉+西兰花）{R}")
    foods = input("  > ").strip()
    if not foods:
        foods = "（未填写）"

    # 输入热量
    print(f"\n  {B}估计热量（kcal）：{R}{DIM}（不确定可直接回车使用参考值）{R}")
    ref_cal = plan[0] if plan else 400
    cal_input = input(f"  > [参考 {ref_cal}kcal]: ").strip()
    if cal_input.isdigit():
        calories = int(cal_input)
    else:
        calories = ref_cal
        print(f"  {DIM}已使用参考热量 {ref_cal}kcal{R}")

    # 保存
    today_key = today_str()
    if today_key not in log:
        log[today_key] = {}
    log[today_key][meal_key] = {"foods": foods, "calories": calories}
    save_log(log)

    print()
    print(f"  {GRN}✓ 已记录：{meal_cn} · {foods} · {calories}kcal{R}")

    # 更新今日热量
    total = day_calorie_total(log[today_key])
    target = WEEKLY_PLAN[weekday]["target"]
    bar = progress_bar(total, target)
    print(f"\n  今日热量：{bar}  {B}{total}{R}/{target} kcal")
    print()
    sep()
    print()
    return log


# ─── 本周计划一览 ─────────────────────────────────────────────────────────────
def show_week(log: dict):
    today   = date.today()
    weekday = today.weekday()
    # 本周周一
    monday  = today - timedelta(days=weekday)

    sep()
    print(f"{B}{CYN}  📅 本周饮食计划{R}")
    sep()
    print()

    for i in range(7):
        day        = monday + timedelta(days=i)
        plan       = WEEKLY_PLAN[i]
        target     = plan["target"]
        day_log    = get_day_log(log, day.isoformat())
        eaten      = day_calorie_total(day_log)
        is_today   = i == weekday
        is_past    = day < today

        # 日期行
        marker  = f" {CYN}← 今天{R}" if is_today else ""
        bd      = B if is_today else ""
        day_str = day.strftime("%m/%d")
        wtype   = f"{DIM}(训练 · {WORKOUT_NAME[i]}){R}" if is_workout_day(i) else f"{DIM}(休息日){R}"
        print(f"  {bd}{DAY_CN[i]} {day_str}{R}  目标 {B}{target}kcal{R}  {wtype}{marker}")

        # 热量进度（如果是过去或今天）
        if is_past or is_today:
            bar = progress_bar(eaten, target, width=20)
            print(f"    {bar}  {eaten}/{target} kcal  "
                  f"{'✓' if eaten > 0 else DIM+'未记录'+R}")
        else:
            # 显示计划摘要
            for key, cn in MEAL_CN.items():
                m = plan["meals"].get(key)
                if m:
                    foods_str = "、".join(m[1][:2])
                    if len(m[1]) > 2:
                        foods_str += f"等"
                    print(f"    {DIM}{cn}：{foods_str}（约{m[0]}kcal）{R}")
        print()

    sep()
    print(f"  {DIM}本周已记录天数：{sum(1 for i in range(7) if get_day_log(log, (monday+timedelta(days=i)).isoformat()))}/7{R}")
    sep()
    print()


# ─── 最近记录 ─────────────────────────────────────────────────────────────────
def show_history(log: dict):
    today = date.today()
    sep()
    print(f"{B}{CYN}  📊 最近 7 天饮食记录{R}")
    sep()
    print()

    has_any = False
    for i in range(6, -1, -1):
        day      = today - timedelta(days=i)
        weekday  = day.weekday()
        plan     = WEEKLY_PLAN[weekday]
        target   = plan["target"]
        day_log  = get_day_log(log, day.isoformat())
        eaten    = day_calorie_total(day_log)
        is_today = i == 0
        bd       = B if is_today else ""
        marker   = " ← 今天" if is_today else ""

        print(f"  {bd}{day.strftime('%m/%d')} {DAY_CN[weekday]}{R}{DIM}{marker}{R}")

        if not day_log:
            print(f"    {DIM}无记录{R}\n")
            continue

        has_any = True
        for key, cn in MEAL_CN.items():
            entry = day_log.get(key)
            if entry:
                print(f"    {GRN}·{R} {cn}：{entry['foods']}  {DIM}{entry['calories']}kcal{R}")

        fixed_acts   = load_fixed_activities()
        fixed_burned = sum(a.get("kcal_burned", 0) for a in fixed_acts)
        extra_acts   = day_activity_list(day_log)
        for a in extra_acts:
            print(f"    {BLU}♦{R} 运动：{a['name']} {a['duration_min']}分钟（{a['intensity']}）  "
                  f"{DIM}消耗~{a.get('kcal_burned',0)}kcal{R}")
        total_burned = fixed_burned + sum(a.get("kcal_burned",0) for a in extra_acts)
        print(f"    {DIM}运动消耗：~{total_burned}kcal（固定{fixed_burned}）{R}")

        bar = progress_bar(eaten, target, width=22)
        diff = eaten - target
        diff_str = f"{GRN}(-{-diff}){R}" if diff < 0 else (f"{RED}(+{diff}){R}" if diff > 0 else f"{GRN}(达标){R}")
        print(f"    合计 {B}{eaten}{R}/{target} kcal  {diff_str}")
        print(f"    {bar}")
        print()

    if not has_any:
        print(f"  {DIM}还没有任何记录，先用 --log 记录第一餐吧！{R}\n")

    sep()
    print()


# ─── 主程序 ───────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]
    log  = load_log()

    if "--log" in args or "-l" in args:
        log = log_meal(log)
    elif "--week" in args or "-w" in args:
        show_week(log)
    elif "--history" in args or "-h" in args:
        show_history(log)
    else:
        show_today(log)


if __name__ == "__main__":
    main()
