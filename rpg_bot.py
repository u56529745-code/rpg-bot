import telebot
from telebot import types
import sqlite3
import random
import os
from flask import Flask
import threading

TOKEN = "8620344298:AAHr_PhXczzO8rhQHgd_DpQtl3rwIA2XPgA"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DB = "rpg.db"

MOBS = {
    1: {"name": "🐀 Крыса", "hp": 20, "dmg": 3, "exp": 10, "silver": 50},
    2: {"name": "🦇 Летучая мышь", "hp": 35, "dmg": 6, "exp": 20, "silver": 100},
    3: {"name": "🐺 Волк", "hp": 60, "dmg": 10, "exp": 40, "silver": 200},
    4: {"name": "🐗 Кабан", "hp": 90, "dmg": 15, "exp": 70, "silver": 350},
    5: {"name": "🐻 Медведь", "hp": 150, "dmg": 25, "exp": 120, "silver": 600},
    6: {"name": "🦂 Скорпион", "hp": 220, "dmg": 35, "exp": 200, "silver": 1000},
    7: {"name": "🐉 Дракон", "hp": 350, "dmg": 50, "exp": 350, "silver": 1800},
    8: {"name": "👹 Демон", "hp": 500, "dmg": 70, "exp": 550, "silver": 3000},
    9: {"name": "💀 Лич", "hp": 750, "dmg": 95, "exp": 850, "silver": 5000},
    10: {"name": "👑 Владыка", "hp": 1200, "dmg": 130, "exp": 1500, "silver": 10000},
}

WEAPONS = {
    "fists": {"name": "👊 Кулаки", "dmg": 5},
    "sword": {"name": "🗡 Меч", "dmg": 15},
    "axe": {"name": "🪓 Топор", "dmg": 25},
    "spear": {"name": "🔱 Копьё", "dmg": 40},
    "magic": {"name": "🔮 Посох", "dmg": 60},
    "legend": {"name": "⚔️ Легендарный клинок", "dmg": 100},
}

ARMORS = {
    "none": {"name": "🚫 Без брони", "def": 0},
    "leather": {"name": "🧥 Кожаная", "def": 3},
    "chain": {"name": "⛓ Кольчуга", "def": 8},
    "plate": {"name": "🛡 Латная", "def": 15},
    "dragon": {"name": "🐲 Драконья", "def": 25},
    "titan": {"name": "⚡ Титановая", "def": 40},
}

ORES = {
    "copper": {"name": "🟠 Медь"},
    "iron": {"name": "⚙️ Железо"},
    "gold": {"name": "🟡 Золото"},
    "mithril": {"name": "💠 Мифрил"},
}

RECIPES = {
    "sword": {"name": "🗡 Меч", "copper": 5, "iron": 2},
    "axe": {"name": "🪓 Топор", "copper": 3, "iron": 4},
    "spear": {"name": "🔱 Копьё", "iron": 5, "gold": 2},
    "magic": {"name": "🔮 Посох", "iron": 3, "gold": 4, "mithril": 1},
    "legend": {"name": "⚔️ Легендарный клинок", "gold": 5, "mithril": 3},
    "leather": {"name": "🧥 Кожаная", "copper": 4},
    "chain": {"name": "⛓ Кольчуга", "copper": 3, "iron": 3},
    "plate": {"name": "🛡 Латная", "iron": 6},
    "dragon": {"name": "🐲 Драконья", "gold": 5, "mithril": 2},
    "titan": {"name": "⚡ Титановая", "mithril": 5},
}

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS players (
        uid INTEGER PRIMARY KEY, name TEXT, level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0, hp INTEGER DEFAULT 100, max_hp INTEGER DEFAULT 100,
        silver INTEGER DEFAULT 0, floor INTEGER DEFAULT 1,
        strength INTEGER DEFAULT 0, agility INTEGER DEFAULT 0, vitality INTEGER DEFAULT 0,
        stat_points INTEGER DEFAULT 0, weapon TEXT DEFAULT 'fists', armor TEXT DEFAULT 'none',
        kills INTEGER DEFAULT 0, energy INTEGER DEFAULT 50, max_energy INTEGER DEFAULT 50,
        copper INTEGER DEFAULT 0, iron INTEGER DEFAULT 0, gold INTEGER DEFAULT 0,
        mithril INTEGER DEFAULT 0, mine_count INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

FIELDS = ["uid","name","level","exp","hp","max_hp","silver","floor",
          "strength","agility","vitality","stat_points","weapon","armor","kills",
          "energy","max_energy","copper","iron","gold","mithril","mine_count"]

def get_player(uid, name="Игрок"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE uid=?", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO players (uid, name) VALUES (?, ?)", (uid, name))
        conn.commit()
        c.execute("SELECT * FROM players WHERE uid=?", (uid,))
        row = c.fetchone()
    conn.close()
    return dict(zip(FIELDS, row))

def save_player(p):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""UPDATE players SET level=?, exp=?, hp=?, max_hp=?, silver=?, floor=?,
        strength=?, agility=?, vitality=?, stat_points=?, weapon=?, armor=?, kills=?,
        energy=?, max_energy=?, copper=?, iron=?, gold=?, mithril=?, mine_count=?
        WHERE uid=?""",
        (p["level"],p["exp"],p["hp"],p["max_hp"],p["silver"],p["floor"],
         p["strength"],p["agility"],p["vitality"],p["stat_points"],
         p["weapon"],p["armor"],p["kills"],p["energy"],p["max_energy"],
         p["copper"],p["iron"],p["gold"],p["mithril"],p["mine_count"],p["uid"]))
    conn.commit()
    conn.close()

def exp_needed(level): return 50 + level * 30

def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
        types.InlineKeyboardButton("⛏ Шахта", callback_data="mine"),
        types.InlineKeyboardButton("🔨 Крафт", callback_data="craft"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"),
        types.InlineKeyboardButton("📊 Статы", callback_data="stats"),
    )
    return m

def menu_text(p):
    return (f"🎮 *ГЛАВНОЕ МЕНЮ*\n\n"
            f"👤 {p['name']}\n⭐ Ур: {p['level']}\n"
            f"💰 {p['silver']:,}\n⚡ {p['energy']}/{p['max_energy']}\n"
            f"🏰 Этаж: {p['floor']}/10")

@bot.message_handler(commands=['start'])
def start(m):
    p = get_player(m.from_user.id, m.from_user.first_name or "Игрок")
    bot.send_message(m.chat.id, menu_text(p), reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "menu")
def back_menu(c):
    p = get_player(c.from_user.id)
    try: bot.edit_message_text(menu_text(p), c.message.chat.id, c.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "profile")
def profile(c):
    p = get_player(c.from_user.id)
    w, a = WEAPONS[p["weapon"]], ARMORS[p["armor"]]
    text = (f"👤 *ПРОФИЛЬ*\n\n⭐ Ур: {p['level']}\n📈 {p['exp']}/{exp_needed(p['level'])}\n"
            f"❤️ {p['hp']}/{p['max_hp']}\n💰 {p['silver']:,}\n⚡ {p['energy']}/{p['max_energy']}\n"
            f"🏰 Этаж: {p['floor']}/10\n👹 Убийств: {p['kills']}\n⛏ Добыто: {p['mine_count']}\n\n"
            f"🗡 {w['name']} (+{w['dmg']})\n🛡 {a['name']} (+{a['def']})")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "stats")
def stats(c):
    p = get_player(c.from_user.id)
    text = (f"📊 *СТАТЫ*\n\n💪 Сила: {p['strength']} (+{p['strength']*2} dmg)\n"
            f"🏃 Ловк: {p['agility']} (+{p['agility']}% крит)\n"
            f"❤️ Вынос: {p['vitality']} (+{p['vitality']*10} HP)\n\n"
            f"🎯 Очков: *{p['stat_points']}*")
    m = types.InlineKeyboardMarkup(row_width=3)
    if p["stat_points"] > 0:
        m.add(types.InlineKeyboardButton("💪 +1", callback_data="up_str"),
              types.InlineKeyboardButton("🏃 +1", callback_data="up_agi"),
              types.InlineKeyboardButton("❤️ +1", callback_data="up_vit"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("up_"))
def upgrade(c):
    p = get_player(c.from_user.id)
    if p["stat_points"] <= 0:
        bot.answer_callback_query(c.id, "❌ Нет очков"); return
    s = c.data.split("_")[1]
    if s == "str": p["strength"] += 1
    elif s == "agi": p["agility"] += 1
    elif s == "vit": p["vitality"] += 1; p["max_hp"] += 10; p["hp"] += 10
    p["stat_points"] -= 1
    save_player(p)
    bot.answer_callback_query(c.id, "✅ Улучшено!")
    stats(c)

@bot.callback_query_handler(func=lambda c: c.data == "tower")
def tower(c):
    p = get_player(c.from_user.id)
    if p["floor"] > 10:
        text = "🏰 *БАШНЯ ПРОЙДЕНА!*\n\n👑 Владыка повержен!"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id); return
    mob = MOBS[p["floor"]]
    text = (f"🏰 *ЭТАЖ {p['floor']}*\n\n{mob['name']}\n❤️ HP: {mob['hp']}\n⚔️ Урон: {mob['dmg']}\n\n"
            f"Твой HP: {p['hp']}/{p['max_hp']}\n⚡ Энергия: {p['energy']}/{p['max_energy']}")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать (5⚡)", callback_data="fight"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight")
def fight(c):
    p = get_player(c.from_user.id)
    if p["energy"] < 5:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 5
    mob = MOBS[p["floor"]]
    mob_hp = mob["hp"]
    w, a = WEAPONS[p["weapon"]], ARMORS[p["armor"]]
    player_dmg = w["dmg"] + p["strength"] * 2
    crit_chance = 5 + p["agility"]
    while mob_hp > 0 and p["hp"] > 0:
        dmg = player_dmg
        crit = random.randint(1, 100) <= crit_chance
        if crit: dmg *= 2
        mob_hp -= dmg
        if mob_hp <= 0: break
        p["hp"] -= max(1, mob["dmg"] - a["def"])
    if p["hp"] <= 0:
        p["hp"] = p["max_hp"]; save_player(p)
        text = "💀 *ПОРАЖЕНИЕ*\n\n❤️ HP восстановлен"
    else:
        p["exp"] += mob["exp"]; p["silver"] += mob["silver"]; p["kills"] += 1; p["floor"] += 1
        lvl_up = False
        while p["exp"] >= exp_needed(p["level"]):
            p["exp"] -= exp_needed(p["level"]); p["level"] += 1
            p["stat_points"] += 3; p["max_hp"] += 20; p["hp"] = p["max_hp"]; lvl_up = True
        save_player(p)
        text = f"🎉 *ПОБЕДА!*\n\n{mob['name']} побеждён!\n📈 +{mob['exp']} опыта\n💰 +{mob['silver']} серебра"
        if lvl_up: text += f"\n\n⭐ *УРОВЕНЬ {p['level']}!*\n+3 очка статов"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
          types.InlineKeyboardButton("🔙 Меню", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "mine")
def mine(c):
    p = get_player(c.from_user.id)
    text = (f"⛏ *ШАХТА*\n\n⚡ Энергия: {p['energy']}/{p['max_energy']}\n"
            f"⛏ Добыто: {p['mine_count']}\n\nСтоимость: 2⚡")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Копать (2⚡)", callback_data="dig"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "dig")
def dig(c):
    p = get_player(c.from_user.id)
    if p["energy"] < 2:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 2
    roll = random.randint(1, 100)
    if roll <= 50: ore, amt = "copper", random.randint(1, 3)
    elif roll <= 80: ore, amt = "iron", random.randint(1, 2)
    elif roll <= 95: ore, amt = "gold", 1
    else: ore, amt = "mithril", 1
    p[ore] += amt
    p["mine_count"] += 1
    save_player(p)
    text = f"⛏ *ДОБЫЧА*\n\n{ORES[ore]['name']} × {amt}\n\n⚡ Осталось: {p['energy']}"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Копать ещё", callback_data="dig"),
          types.InlineKeyboardButton("🔙 Шахта", callback_data="mine"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "inv")
def inv(c):
    p = get_player(c.from_user.id)
    text = (f"🎒 *ИНВЕНТАРЬ*\n\n"
            f"🟠 Медь: {p['copper']}\n⚙️ Железо: {p['iron']}\n"
            f"🟡 Золото: {p['gold']}\n💠 Мифрил: {p['mithril']}")
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "craft")
def craft(c):
    p = get_player(c.from_user.id)
    text = (f"🔨 *КРАФТ*\n\n🟠 Медь: {p['copper']}\n⚙️ Железо: {p['iron']}\n"
            f"🟡 Золото: {p['gold']}\n💠 Мифрил: {p['mithril']}\n\nВыбери рецепт:")
    m = types.InlineKeyboardMarkup(row_width=1)
    for key, r in RECIPES.items():
        can = all(p.get(res, 0) >= amt for res, amt in r.items() if res in ORES)
        mark = "✅" if can else "🔒"
        m.add(types.InlineKeyboardButton(f"{mark} {r['name']}", callback_data=f"craft_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try: bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("craft_") and c.data != "craft")
def do_craft(c):
    key = c.data.replace("craft_", "")
    p = get_player(c.from_user.id)
    r = RECIPES[key]
    for res, amt in r.items():
        if res in ORES and p.get(res, 0) < amt:
            bot.answer_callback_query(c.id, "❌ Не хватает ресурсов"); return
    for res, amt in r.items():
        if res in ORES: p[res] -= amt
    if key in WEAPONS: p["weapon"] = key
    elif key in ARMORS: p["armor"] = key
    save_player(p)
    bot.answer_callback_query(c.id, f"✅ Скрафчено: {r['name']}")
    craft(c)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    print("RPG бот запущен...")
    bot.infinity_polling()
