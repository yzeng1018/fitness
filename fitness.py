#!/usr/bin/env python3
"""健身计划提醒 - 38岁男性 居家无器材 4天/周 塑形维持

用法：
  python3 fitness.py          今天的训练 + 饮食计划
  python3 fitness.py --week   本周计划一览
  python3 fitness.py --notify macOS 系统通知（供 launchd 调用）
"""

import sys
import subprocess
from datetime import date

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

# ─── 用户档案（可按需修改）────────────────────────────────────────────────────
USER = {
    "age":    38,
    "weight": 68,   # kg
    "height": 170,  # cm
    "goal":   "减脂（脂肪肝调理）",
}

# 基础代谢率 Mifflin-St Jeor（男）
BMR  = 10 * USER["weight"] + 6.25 * USER["height"] - 5 * USER["age"] + 5
TDEE = int(BMR * 1.55)   # 中等活动量（每周4次运动）

# 热量目标
CAL_WORKOUT = 2300       # 训练日
CAL_REST    = 2000       # 休息日

# 宏量营养素目标（训练日/休息日通用）
PROTEIN_G = 130          # 蛋白质 g（约2g/kg体重）
FAT_G     = 55           # 脂肪 g

# ─── 4天训练计划 ──────────────────────────────────────────────────────────────
WORKOUTS = {
    "A": {
        "name":  "上肢推力",
        "focus": "胸 · 肩 · 三头肌",
        "duration": "40 分钟",
        "warmup": [
            "手臂大绕环 × 30秒",
            "颈肩动态拉伸 × 30秒",
            "原地高抬腿 × 1分钟",
        ],
        "exercises": [
            # (动作名, 组数×次数, 组间休息, 要点)
            ("标准俯卧撑",    "3组 × 10-15次", "60秒", "手宽与肩同宽，身体一条线，全程控制速度"),
            ("宽距俯卧撑",    "3组 × 10-12次", "60秒", "双手超肩宽，下降时感受胸肌拉伸"),
            ("钻石俯卧撑",    "3组 × 8-10次",  "60秒", "双手并拢成菱形，重点刺激三头肌"),
            ("Pike 俯卧撑",  "3组 × 8-12次",  "60秒", "身体倒V形，屈肘鼻子触地，练肩"),
            ("椅子臂撑",      "3组 × 10-12次", "60秒", "背对椅子支撑，肘弯90°，练三头"),
        ],
        "cooldown": [
            "胸肌拉伸（门框式）× 30秒×2",
            "肩前侧拉伸 × 30秒×2",
            "三头肌过头拉伸 × 30秒×2",
        ],
        "tips": "做不了标准俯卧撑可用跪姿俯卧撑过渡；最后一组感到明显疲劳才有效",
    },
    "B": {
        "name":  "下肢力量",
        "focus": "股四头肌 · 臀大肌 · 腘绳肌",
        "duration": "40 分钟",
        "warmup": [
            "腿部绕环 × 30秒",
            "髋关节画圈 × 1分钟（每侧）",
            "热身深蹲 × 10次（轻松节奏）",
        ],
        "exercises": [
            ("徒手深蹲",       "4组 × 15-20次", "60秒", "膝盖对准脚尖，蹲到大腿平行地面"),
            ("保加利亚分腿蹲", "3组 × 10次/侧", "60秒", "后脚踩椅面，重心在前脚，慢下快上"),
            ("箭步蹲行走",     "3组 × 12步/侧", "60秒", "步幅要大，膝盖不超脚尖"),
            ("臀桥",           "3组 × 15-20次", "45秒", "顶端夹紧臀部停留1秒，勿用腰发力"),
            ("侧卧蚌式开合",   "3组 × 15次/侧", "45秒", "脚跟并拢，向上抬膝，激活臀中肌"),
        ],
        "cooldown": [
            "股四头肌拉伸 × 30秒×2",
            "髂腰肌弓箭步拉伸 × 30秒×2",
            "鸽子式臀部拉伸 × 30秒×2",
        ],
        "tips": "深蹲是核心动作，宁慢不快；膝盖不适时减小蹲深，优先感受大腿发力",
    },
    "C": {
        "name":  "拉力 + 核心",
        "focus": "背部 · 腹肌 · 稳定肌群",
        "duration": "45 分钟",
        "warmup": [
            "猫牛式伸展 × 1分钟",
            "肩膀绕环 × 30秒",
            "开合跳 × 1分钟",
        ],
        "exercises": [
            ("Superman 超人式", "3组 × 12次",    "45秒", "俯卧，同时抬起四肢，顶端停2秒再放"),
            ("俯卧游泳",        "3组 × 20次",    "45秒", "交替摆动对侧手脚，练整个后链"),
            ("毛毛虫爬行",      "3组 × 8次",     "60秒", "站立弯腰走手至俯卧撑位，再走脚回来"),
            ("平板支撑",        "3组 × 40-60秒", "45秒", "核心收紧，腰不下塌，呼吸平稳"),
            ("侧板支撑",        "3组 × 30秒/侧", "45秒", "侧面支撑，髋部不下沉"),
            ("自行车卷腹",      "3组 × 12次/侧", "45秒", "慢速控制，肘碰对侧膝，勿拉脖子"),
        ],
        "cooldown": [
            "猫牛式 × 1分钟",
            "儿童式放松 × 30秒",
            "仰卧脊柱扭转 × 30秒×2",
        ],
        "tips": "核心训练质量比数量重要；平板支撑腰一旦塌了立刻停，宁可时间短",
    },
    "D": {
        "name":  "全身 HIIT",
        "focus": "心肺耐力 · 全身燃脂 · 爆发力",
        "duration": "35 分钟",
        "warmup": [
            "原地慢跑 × 1分钟",
            "开合跳 × 30秒",
            "动态深蹲 × 10次",
        ],
        "exercises": [
            ("波比跳",     "4组 × 8次",   "60秒", "全力完成，落地时膝盖缓冲，保护关节"),
            ("跳跃深蹲",   "4组 × 10次",  "60秒", "跳起充分伸展，落地半蹲吸收冲击"),
            ("山地爬行",   "4组 × 20次",  "45秒", "保持核心稳定，节奏尽量快"),
            ("高抬腿冲刺", "4组 × 20秒",  "40秒", "原地快速高抬腿，摆臂配合"),
            ("俯卧撑跳",   "3组 × 8次",   "60秒", "俯卧撑完成后跳起双脚落地，循环"),
        ],
        "cooldown": [
            "全身静态拉伸 × 3分钟",
            "深呼吸放松（腹式呼吸）× 1分钟",
        ],
        "tips": "HIIT 强度大，心率飙高正常；体力不足可减少组数；充足补水很重要",
    },
}

# ─── 每周安排（固定）─────────────────────────────────────────────────────────
#  周一  周二  周三  周四  周五  周六  周日
SCHEDULE = {0: "A", 1: "B", 2: "rest", 3: "C", 4: "D", 5: "rest", 6: "rest"}
DAY_CN   = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ─── 饮食方案 ─────────────────────────────────────────────────────────────────
def diet(is_workout_day: bool) -> dict:
    cal = CAL_WORKOUT if is_workout_day else CAL_REST
    carbs_g = max(0, (cal - PROTEIN_G * 4 - FAT_G * 9) // 4)

    if is_workout_day:
        meals = [
            ("早餐  07:00", int(cal * 0.25), [
                "鸡蛋 2个（水煮/炒蛋）",
                "全麦面包 2片",
                "牛奶 250ml",
                "香蕉 1根",
            ]),
            ("午餐  12:00", int(cal * 0.30), [
                "糙米/杂粮饭 150g（熟重）",
                "鸡胸肉 150g 或 瘦猪肉 120g",
                "蔬菜 200g（西兰花/菠菜等）",
                "少量橄榄油炒制",
            ]),
            ("训练前加餐（运动前1小时）", int(cal * 0.10), [
                "香蕉 1根 或 燕麦棒 1条",
                "运动期间补水 500ml 以上",
            ]),
            ("晚餐 / 运动后（运动后1小时内）", int(cal * 0.35), [
                "鸡胸肉或蛋白 100g（优先快速蛋白质）",
                "红薯 150g 或 米饭 100g（熟重）",
                "混合蔬菜大份 250g",
                "豆腐 100g（补充蛋白质）",
            ]),
        ]
    else:
        meals = [
            ("早餐  07:00", int(cal * 0.25), [
                "鸡蛋 2个",
                "燕麦粥 50g（干重）",
                "坚果 15g（核桃/杏仁）",
                "水果 1份",
            ]),
            ("午餐  12:00", int(cal * 0.35), [
                "杂粮饭 100g（熟重，少于训练日）",
                "鱼/虾/瘦肉 150g",
                "豆腐 100g",
                "蔬菜 300g（大份）",
            ]),
            ("晚餐  18:30", int(cal * 0.30), [
                "鸡胸肉/鸡蛋 100g",
                "绿叶蔬菜大份 300g",
                "少量主食（约半碗米饭）",
            ]),
            ("加餐（可选）", int(cal * 0.10), [
                "希腊酸奶 150g 或 低脂牛奶 250ml",
                "坚果 10g",
            ]),
        ]
    return {"cal": cal, "protein_g": PROTEIN_G, "carbs_g": carbs_g,
            "fat_g": FAT_G, "meals": meals}


# ─── 输出函数 ─────────────────────────────────────────────────────────────────
def sep(char="═", n=54):
    print(f"{CYN}{char * n}{R}")

def print_header():
    today    = date.today()
    day_name = DAY_CN[today.weekday()]
    sep()
    print(f"{B}{CYN}  💪 健身计划提醒{R}                       {DIM}v1.0{R}")
    sep()
    print(f"  {B}今天：{R}{today.strftime('%Y年%m月%d日')} {B}{day_name}{R}")
    print(f"  {DIM}目标：塑形维持 · 居家无器材 · 4天/周 · TDEE≈{TDEE}kcal{R}")
    sep("─")
    print()

def print_workout(key: str):
    if key == "rest":
        print(f"{B}{GRN}  🌿 今天是休息日{R}\n")
        print("  休息同样是训练的一部分，充分恢复才能进步。\n")
        print("  建议：")
        print("    · 轻度散步或拉伸 20-30 分钟")
        print("    · 保证睡眠 7-8 小时")
        print("    · 饮食照常保证蛋白质摄入\n")
        return

    w = WORKOUTS[key]
    print(f"{B}{BLU}【{key} 训练计划】{R}  {B}{w['name']}{R}  {DIM}({w['focus']}){R}")
    print(f"  预计时长：{w['duration']}\n")

    print(f"  {B}{YEL}▸ 热身（约 5 分钟）{R}")
    for item in w["warmup"]:
        print(f"    · {item}")
    print()

    print(f"  {B}{YEL}▸ 正式训练{R}")
    for i, (name, sets_reps, rest, note) in enumerate(w["exercises"], 1):
        print(f"    {B}{i}. {name}{R}  {GRN}{sets_reps}{R}  休息 {rest}")
        print(f"       {DIM}→ {note}{R}")
    print()

    print(f"  {B}{YEL}▸ 拉伸放松（约 5 分钟）{R}")
    for item in w["cooldown"]:
        print(f"    · {item}")
    print()

    print(f"  {B}{MAG}💡 今日贴士：{R}{DIM}{w['tips']}{R}\n")

def print_diet(is_workout_day: bool):
    d = diet(is_workout_day)
    day_type = "训练日" if is_workout_day else "休息日"
    sep("─")
    print()
    print(f"{B}{BLU}【饮食计划】{R}  {DIM}({day_type}){R}")
    print(f"  每日热量目标：{B}{d['cal']} kcal{R}  "
          f"蛋白质 {GRN}{d['protein_g']}g{R} · "
          f"碳水 {YEL}{d['carbs_g']}g{R} · "
          f"脂肪 {RED}{d['fat_g']}g{R}\n")

    for name, cal, foods in d["meals"]:
        print(f"  {B}{YEL}▸ {name}{R}  {DIM}约 {cal} kcal{R}")
        for food in foods:
            print(f"    · {food}")
        print()

    print(f"  {DIM}* 每天饮水 2L+ · 减少加工食品和含糖饮料 · 优先天然食物{R}\n")

def print_week_overview():
    today   = date.today()
    today_w = today.weekday()
    sep("─")
    print()
    print(f"{B}{BLU}【本周计划一览】{R}\n")
    for i, day_name in enumerate(DAY_CN):
        key    = SCHEDULE[i]
        marker = f" {CYN}← 今天{R}" if i == today_w else ""
        bd     = B if i == today_w else ""
        if key == "rest":
            label = f"{DIM}🌿 休息日{R}"
        else:
            w     = WORKOUTS[key]
            label = f"{GRN}{key}{R}. {bd}{w['name']}{R}  {DIM}({w['focus']}){R}"
        print(f"  {bd}{day_name}{R}  {label}{marker}")
    print()

def send_notify(title: str, msg: str):
    """发送 macOS 系统通知"""
    script = f'display notification "{msg}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], check=False)

# ─── 主程序 ───────────────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    today      = date.today()
    weekday    = today.weekday()
    key        = SCHEDULE[weekday]
    is_workout = key != "rest"
    day_name   = DAY_CN[weekday]

    # 仅发通知模式（供 launchd 调用）
    if "--notify" in args:
        if is_workout:
            w = WORKOUTS[key]
            send_notify(
                "💪 今日健身提醒",
                f"{day_name}：{w['name']}（{w['focus']}）约{w['duration']} · 运行 fitness.py 查看详情"
            )
        else:
            send_notify("🌿 今日健身提醒", f"{day_name}是休息日，注意饮食和充足睡眠！")
        return

    print_header()

    # --week 模式：显示本周一览 + 今日计划
    if "--week" in args or "-w" in args:
        print_week_overview()

    print_workout(key)
    print_diet(is_workout)

    sep("─")
    print(f"  {DIM}python3 fitness.py --week   查看本周计划{R}")
    sep()
    print()


if __name__ == "__main__":
    main()
