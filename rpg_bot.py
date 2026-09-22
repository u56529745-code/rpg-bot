import telebot
from telebot import types
import threading, time, os, random, json
from flask import Flask
from data import *
from db import init_db, get_player, save_player, exp_needed, prof_level_for_exp
from battle import (
    calc_player_stats, make_mob, player_turn, mob_turn,
    roll_herb, roll_ore_drop, roll_gem_drop, roll_loot, battle_text,
)
from craft import can_craft, do_craft

TOKEN = "8620344298:AAG4CvwDYP6bySc5ZLn5_tJTjpGpOPVHC6U"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "ok"

battles = {}

def regen_energy(p):
    now = time.time()
    last = p.get("last_energy_time", 0)
    if last == 0:
        p["last_energy_time"] = now
        return
    diff = now - last
    regen = int(diff / 20) * 3
    if regen > 0:
        p["energy"] = min(p["max_energy"], p["energy"] + regen)
        p["last_energy_time"] = now

def stat_of(key):
    if key in WEAPONS: return WEAPONS[key]["dmg"]
    if key in ARMORS: return ARMORS[key]["def"]
    if key in ACCESSORIES: return ACCESSORIES[key]["bonus"]
    return 0

def item_name(key):
    if key in WEAPONS: return WEAPONS[key]["name"]
    if key in ARMORS: return ARMORS[key]["name"]
    if key in ACCESSORIES: return ACCESSORIES[key]["name"]
    return key

def item_type(key):
    if key in WEAPONS: return "weapon"
    if key in ARMORS: return "armor"
    if key in ACCESSORIES: return "accessory"
    return None

def try_equip_if_better(p, key):
    t = item_type(key)
    if t is None: return False
    current = p.get(t, "none")
    if stat_of(key) > stat_of(current):
        p[t] = key
        return True
    return False

def format_drops(drops, is_gem=False):
    """Форматирует список дропов: (key, amt, exp)"""
    lines = []
    total_exp = 0
    for key, amt, exp in drops:
        tier = GEM_TIER.get(key, "?") if is_gem else ORE_TIER.get(key, "?")
        name = GEMS[key]["name"] if is_gem else ORES[key]["name"]
        lines.append(f"{name} ({tier}) × {amt}")
        total_exp += exp
    return "\n".join(lines), total_exp

LINE = "━━━━━━━━━━━━━━━━━━"

def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
        types.InlineKeyboardButton("⛏ Шахта", callback_data="mine"),
        types.InlineKeyboardButton("🔨 Крафт", callback_data="craft"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"),
        types.InlineKeyboardButton("📊 Статы", callback_data="stats"),
        types.InlineKeyboardButton("📦 Скрафчено", callback_data="crafted"),
        types.InlineKeyboardButton("⚙️ Авто-шахта", callback_data="auto_mine_menu"),
    )
    return m

def menu_text(p):
    return (
        f"🎮 *ГЛАВНОЕ МЕНЮ*\n{LINE}\n"
        f"👤 {p['name']}\n"
        f"⭐ Ур: {p['level']} ({p['exp']}/{exp_needed(p['level'])})\n"
        f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
        f"⚡ Энергия: {p['energy']}/{p['max_energy']}\n"
        f"💰 Серебро: {p['silver']:,}\n"
        f"🏰 Этаж: {p['floor']}/50\n"
        f"🐾 Мобов: {p['mob_kill']}/150\n"
        f"🔑 Ключей: {p['keys']}"
    )

@bot.message_handler(commands=['start'])
def start(m):
    p = get_player(m.from_user.id, m.from_user.first_name or "Игрок")
    regen_energy(p)
    save_player(p)
    bot.send_message(m.chat.id, menu_text(p), reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "menu")
def back_menu(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    save_player(p)
    try:
        bot.edit_message_text(menu_text(p), c.message.chat.id, c.message.message_id,
                              reply_markup=main_menu(), parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "profile")
def profile(c):
    p = get_player(c.from_user.id)
    w = WEAPONS.get(p["weapon"], WEAPONS["fists"])
    a = ARMORS.get(p["armor"], ARMORS["none"])
    acc = ACCESSORIES.get(p["accessory"], ACCESSORIES["none"])
    text = (
        f"👤 *ПРОФИЛЬ*\n{LINE}\n"
        f"⭐ Ур: {p['level']} ({p['exp']}/{exp_needed(p['level'])})\n"
        f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
        f"💰 Серебро: {p['silver']:,}\n"
        f"🏰 Этаж: {p['floor']}/50\n"
        f"🐾 Убито мобов: {p['mob_kill']}/150\n"
        f"👹 Всего убийств: {p['kills']}\n"
        f"🏆 Боссов: {p['boss_kills']}\n\n"
        f"🗡 {w['name']} (+{w['dmg']})\n"
        f"🛡 {a['name']} (+{a['def']})\n"
        f"💍 {acc['name']} (+{acc['bonus']})\n\n"
        f"⚒️ Кузнец: ур.{p['prof_smith']}\n"
        f"🛡 Бронник: ур.{p['prof_armorer']}\n"
        f"💎 Ювелир: ур.{p['prof_jeweler']}\n"
        f"⚗️ Алхимик: ур.{p['prof_alchemist']}\n"
        f"⛏ Шахтёр: ур.{p['prof_miner']}"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "stats")
def stats(c):
    p = get_player(c.from_user.id)
    dmg, defense, crit = calc_player_stats(p)
    text = (
        f"📊 *СТАТЫ*\n{LINE}\n"
        f"💪 Сила: {p['strength']}\n"
        f"🏃 Ловкость: {p['agility']}\n"
        f"❤️ Выносливость: {p['vitality']}\n\n"
        f"⚔️ Урон: {dmg}\n🛡 Защита: {defense}\n💥 Крит: {crit}%\n\n"
        f"🎯 Очков: *{p['stat_points']}*"
    )
    m = types.InlineKeyboardMarkup(row_width=3)
    if p["stat_points"] > 0:
        m.add(
            types.InlineKeyboardButton("💪 +1", callback_data="up_str"),
            types.InlineKeyboardButton("🏃 +1", callback_data="up_agi"),
            types.InlineKeyboardButton("❤️ +1", callback_data="up_vit"),
        )
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
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
    elif s == "vit":
        p["vitality"] += 1
        p["max_hp"] += 10
        p["hp"] += 10
    p["stat_points"] -= 1
    save_player(p)
    bot.answer_callback_query(c.id, "✅ Улучшено!")
    stats(c)

# БАШНЯ
@bot.callback_query_handler(func=lambda c: c.data == "tower")
def tower(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if p["floor"] > 50:
        text = "🏰 *БАШНЯ ПРОЙДЕНА!*\n\n👑 Все 50 этажей покорены!"
    else:
        text = (
            f"🏰 *ЭТАЖ {p['floor']}*\n{LINE}\n"
            f"🐾 Мобов: {p['mob_kill']}/150\n"
            f"🔑 Ключей: {p['keys']}\n"
            f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
            f"⚡ Энергия: {p['energy']}/{p['max_energy']}"
        )
    m = types.InlineKeyboardMarkup()
    if p["energy"] >= 5 and p["floor"] <= 50:
        m.add(types.InlineKeyboardButton("⚔️ В бой (5⚡)", callback_data="fight_start"))
    if p["keys"] > 0 and p["floor"] <= 50:
        m.add(types.InlineKeyboardButton(f"🔑 Ключ ({p['keys']})", callback_data="use_key"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight_start")
def fight_start(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    if p["energy"] < 5:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 5
    is_boss = p["mob_kill"] >= 149
    mob = make_mob(p["floor"], is_boss)
    battles[c.from_user.id] = {"mob": mob}
    save_player(p)
    text = (
        f"⚔️ *БОЙ НАЧАЛСЯ!*\n{LINE}\n{mob['name']}\n"
        f"❤️ HP: {mob['hp']}/{mob['max_hp']}\n"
        f"⚔️ Урон: {mob['dmg']}\n\n"
        f"❤️ Твой HP: {p['hp']}/{p['max_hp']}"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать", callback_data="fight_turn"))
    m.add(types.InlineKeyboardButton("🏳️ Сбежать", callback_data="fight_run"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight_turn")
def fight_turn(c):
    uid = c.from_user.id
    if uid not in battles:
        bot.answer_callback_query(c.id, "❌ Бой не найден"); return
    p = get_player(uid)
    mob = battles[uid]["mob"]
    pdmg, is_crit, p_dodged = player_turn(p, mob)
    m_dmg, m_dodged = 0, False
    if mob["hp"] > 0:
        m_dmg, m_dodged = mob_turn(p, mob)
    log = battle_text(p, mob, pdmg, is_crit, m_dmg, m_dodged, p_dodged)
    if mob["hp"] <= 0:
        p["exp"] += mob["exp"]
        p["silver"] += mob["silver"]
        p["kills"] += 1
        p["mob_kill"] += 1
        if mob.get("boss"): p["boss_kills"] += 1
        herb = roll_herb(p["floor"])
        p[herb] += 1
        loot = roll_loot(p["floor"])
        p[loot] = (p.get(loot, 0) or 0) + 1
        key_drop = random.randint(1, 100) <= 5
        if key_drop: p["keys"] += 1
        if p["mob_kill"] >= 150:
            p["keys"] += 1
            p["mob_kill"] = 0
        lvl_up = False
        while p["exp"] >= exp_needed(p["level"]):
            p["exp"] -= exp_needed(p["level"])
            p["level"] += 1
            p["stat_points"] += 3
            p["max_hp"] += 20
            p["hp"] = p["max_hp"]
            lvl_up = True
        save_player(p)
        del battles[uid]
        text = (
            f"🎉 *ПОБЕДА!*\n{LINE}\n"
            f"{mob['name']} побеждён!\n"
            f"📈 +{mob['exp']} опыта\n"
            f"💰 +{mob['silver']} серебра\n"
            f"🌿 +1 {HERBS[herb]['name']}\n"
            f"👹 +1 {MOB_LOOT[loot]['name']}"
        )
        if key_drop: text += "\n🔑 *Ключ выпал!*"
        if lvl_up: text += f"\n\n⭐ *УРОВЕНЬ {p['level']}!* +3 очка"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
              types.InlineKeyboardButton("🔙 Меню", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id); return
    if p["hp"] <= 0:
        p["hp"] = p["max_hp"]
        save_player(p); del battles[uid]
        text = "💀 *ПОРАЖЕНИЕ*\n\n❤️ HP восстановлен"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
              types.InlineKeyboardButton("🔙 Меню", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id); return
    save_player(p)
    text = f"⚔️ *БОЙ*\n{LINE}\n{log}\n{LINE}\n❤️ HP: {p['hp']}/{p['max_hp']}\n⚡ Энергия: {p['energy']}"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать", callback_data="fight_turn"))
    m.add(types.InlineKeyboardButton("🏳️ Сбежать", callback_data="fight_run"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight_run")
def fight_run(c):
    uid = c.from_user.id
    if uid in battles: del battles[uid]
    bot.answer_callback_query(c.id, "🏳️ Сбежал!")
    tower(c)

@bot.callback_query_handler(func=lambda c: c.data == "use_key")
def use_key(c):
    p = get_player(c.from_user.id)
    if p["keys"] <= 0:
        bot.answer_callback_query(c.id, "❌ Нет ключей"); return
    p["keys"] -= 1
    p["floor"] += 1
    p["mob_kill"] = 0
    save_player(p)
    bot.answer_callback_query(c.id, f"🔑 Этаж {p['floor']} открыт!")
    tower(c)

# ШАХТА
@bot.callback_query_handler(func=lambda c: c.data == "mine")
def mine(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    bonus = MINER_BONUS.get(p["prof_miner"], 0)
    text = (
        f"⛏ *ШАХТА*\n{LINE}\n"
        f"⚡ Энергия: {p['energy']}/{p['max_energy']}\n"
        f"⛏ Добыто: {p['mine_count']}\n"
        f"⛏ Шахтёр: ур.{p['prof_miner']} (+{bonus}%)\n\n"
        f"Стоимость: 2⚡"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Копать (2⚡)", callback_data="dig"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "dig")
def dig(c):
    p = get_player(c.from_user.id)
    if p["energy"] < 2:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 2
    ore_drops = roll_ore_drop(p["prof_miner"])
    gem_drops = []
    if random.randint(1, 100) <= 30:
        gem_drops = roll_gem_drop(p["prof_miner"])
    text_lines = ["⛏ *ДОБЫЧА*", ""]
    total_exp = 0
    for key, amt, exp in ore_drops:
        tier = ORE_TIER.get(key, "?")
        text_lines.append(f"{ORES[key]['name']} ({tier}) × {amt}")
        p[key] = (p.get(key, 0) or 0) + amt
        total_exp += exp
    for key, amt, exp in gem_drops:
        tier = GEM_TIER.get(key, "?")
        text_lines.append(f"{GEMS[key]['name']} ({tier}) × {amt}")
        p[key] = (p.get(key, 0) or 0) + amt
        total_exp += exp
    p["exp_miner"] = (p.get("exp_miner", 0) or 0) + total_exp
    new_lvl = prof_level_for_exp(int(p["exp_miner"]))
    level_up = False
    if new_lvl > p["prof_miner"]:
        p["prof_miner"] = new_lvl
        level_up = True
    p["mine_count"] += 1
    save_player(p)
    text_lines.append("")
    text_lines.append(f"📈 +{total_exp} опыта шахтёра")
    text_lines.append(f"⚡ Осталось: {p['energy']}")
    if level_up:
        text_lines.append(f"\n🎉 *Шахтёр → ур. {new_lvl}!*")
    text = "\n".join(text_lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Ещё", callback_data="dig"),
          types.InlineKeyboardButton("🔙 Шахта", callback_data="mine"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# АВТО-ШАХТА
def process_auto_mine(p):
    if not p.get("auto_mine_active"): return
    now = time.time()
    last = p.get("auto_mine_last_collect", 0) or p.get("auto_mine_started", now)
    elapsed = int(now - last)
    if elapsed < 5: return
    cycles = min(elapsed // 5, 8640)
    for _ in range(cycles):
        for key, amt, exp in roll_ore_drop(p["prof_miner"]):
            p[key] = (p.get(key, 0) or 0) + amt
        if random.randint(1, 100) <= 30:
            for key, amt, exp in roll_gem_drop(p["prof_miner"]):
                p[key] = (p.get(key, 0) or 0) + amt
    p["auto_mine_last_collect"] = now

def auto_mine_active_markup():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("🔄 Проверить", callback_data="auto_mine_check"),
        types.InlineKeyboardButton("💰 Забрать", callback_data="auto_mine_collect"),
        types.InlineKeyboardButton("❌ Отменить", callback_data="auto_mine_stop"),
    )
    return m

def auto_mine_start_markup():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⛏ Запустить", callback_data="auto_mine_start"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    return m

def auto_mine_text(p):
    totals = {}
    for key in list(ORES.keys()) + list(GEMS.keys()):
        val = p.get(key, 0) or 0
        if val > 0:
            totals[key] = val
    started = p.get("auto_mine_started", 0) or 0
    elapsed_min = int((time.time() - started) / 60) if started else 0
    hours = elapsed_min // 60
    minutes = elapsed_min % 60
    bonus = MINER_BONUS.get(p["prof_miner"], 0)
    lines = []
    for key, amt in totals.items():
        if key in ORES:
            tier = ORE_TIER.get(key, "?")
            lines.append(f"{ORES[key]['name']} ({tier}): {amt}")
        else:
            tier = GEM_TIER.get(key, "?")
            lines.append(f"{GEMS[key]['name']} ({tier}): {amt}")
    return (
        f"⚙️ *АВТО-ШАХТА*\n{LINE}\n"
        f"⏱ Работает: {hours}ч {minutes}мин\n"
        f"⛏ Шахтёр: ур.{p['prof_miner']} (+{bonus}%)\n\n"
        + ("\n".join(lines) if lines else "Пока пусто.")
    )

@bot.callback_query_handler(func=lambda c: c.data == "auto_mine_menu")
def auto_mine_menu(c):
    p = get_player(c.from_user.id)
    if p.get("auto_mine_active"):
        process_auto_mine(p); save_player(p)
        text = auto_mine_text(p)
        m = auto_mine_active_markup()
    else:
        text = (
            f"⚙️ *АВТО-ШАХТА*\n{LINE}\n"
            f"Копает в фоне (все руды + самоцветы).\n\n"
            f"⚡ 2⚡ / 5 сек\n"
            f"⏱ Макс: 12 часов\n"
            f"📈 Опыт шахтёра капает\n\n"
            f"Готов?"
        )
        m = auto_mine_start_markup()
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "auto_mine_start")
def auto_mine_start(c):
    p = get_player(c.from_user.id)
    now = time.time()
    p["auto_mine_active"] = 1
    p["auto_mine_started"] = now
    p["auto_mine_last_collect"] = now
    save_player(p)
    bot.answer_callback_query(c.id, "⛏ Запущена!")
    auto_mine_menu(c)

@bot.callback_query_handler(func=lambda c: c.data == "auto_mine_check")
def auto_mine_check(c):
    p = get_player(c.from_user.id)
    process_auto_mine(p); save_player(p)
    text = auto_mine_text(p)
    m = auto_mine_active_markup()
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id, "🔄")

@bot.callback_query_handler(func=lambda c: c.data in ("auto_mine_collect", "auto_mine_stop"))
def auto_mine_finish(c):
    p = get_player(c.from_user.id)
    process_auto_mine(p)
    p["auto_mine_active"] = 0
    p["auto_mine_started"] = 0
    p["auto_mine_last_collect"] = 0
    save_player(p)
    msg = "💰 Забрано!" if c.data == "auto_mine_collect" else "❌ Остановлено."
    bot.answer_callback_query(c.id, msg)
    auto_mine_menu(c)

# ИНВЕНТАРЬ
@bot.callback_query_handler(func=lambda c: c.data == "inv")
def inv(c):
    p = get_player(c.from_user.id)
    lines = [f"🎒 *ИНВЕНТАРЬ*\n{LINE}", "🪨 *Руда:*"]
    for k, v in ORES.items():
        if p.get(k, 0) > 0:
            tier = ORE_TIER.get(k, "?")
            lines.append(f"  {v['name']} ({tier}): {p[k]}")
    lines.append("\n💎 *Самоцветы:*")
    for k, v in GEMS.items():
        if p.get(k, 0) > 0:
            tier = GEM_TIER.get(k, "?")
            lines.append(f"  {v['name']} ({tier}): {p[k]}")
    lines.append("\n🌿 *Травы:*")
    for k, v in HERBS.items():
        if p.get(k, 0) > 0:
            lines.append(f"  {v['name']}: {p[k]}")
    lines.append("\n👹 *Лут:*")
    for k, v in MOB_LOOT.items():
        if p.get(k, 0) > 0:
            lines.append(f"  {v['name']}: {p[k]}")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "..."
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📦 Скрафчено", callback_data="crafted"),
          types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "crafted")
def crafted_menu(c):
    p = get_player(c.from_user.id)
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    if not items:
        text = "📦 *СКРАФЧЕНО*\n\nПока пусто."
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔨 Крафт", callback_data="craft"),
              types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id); return
    text = f"📦 *СКРАФЧЕНО* ({len(items)})\n{LINE}"
    m = types.InlineKeyboardMarkup(row_width=1)
    for i, key in enumerate(items):
        name = item_name(key)
        s = stat_of(key)
        m.add(types.InlineKeyboardButton(f"{name} (+{s})", callback_data=f"item_{i}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("item_"))
def item_action(c):
    p = get_player(c.from_user.id)
    idx = int(c.data.split("_")[1])
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    if idx >= len(items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = items[idx]
    name = item_name(key)
    s = stat_of(key)
    text = f"📦 *{name}*\n{LINE}\n📊 Бонус: +{s}\n\nЧто сделать?"
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✅ Надеть", callback_data=f"equip_{idx}"),
          types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{idx}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="crafted"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("equip_"))
def equip_item(c):
    p = get_player(c.from_user.id)
    idx = int(c.data.split("_")[1])
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    if idx >= len(items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = items[idx]
    t = item_type(key)
    if t:
        p[t] = key
        save_player(p)
        bot.answer_callback_query(c.id, "✅ Надето!")
    else:
        bot.answer_callback_query(c.id, "❌ Нельзя")
    crafted_menu(c)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sell_"))
def sell_item(c):
    p = get_player(c.from_user.id)
    idx = int(c.data.split("_")[1])
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    if idx >= len(items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = items.pop(idx)
    price = max(50, stat_of(key) * 20)
    p["silver"] += price
    p["crafted_items"] = json.dumps(items)
    save_player(p)
    bot.answer_callback_query(c.id, f"💰 +{price}")
    crafted_menu(c)

# КРАФТ
@bot.callback_query_handler(func=lambda c: c.data == "craft")
def craft_menu(c):
    p = get_player(c.from_user.id)
    text = (
        f"🔨 *КРАФТ*\n{LINE}\n"
        f"⚒️ Кузнец: ур.{p['prof_smith']}\n"
        f"🛡 Бронник: ур.{p['prof_armorer']}\n"
        f"💎 Ювелир: ур.{p['prof_jeweler']}\n"
        f"⚗️ Алхимик: ур.{p['prof_alchemist']}\n\n"
        f"Выбери категорию:"
    )
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("⚒️ Оружие", callback_data="craft_smith"),
        types.InlineKeyboardButton("🛡 Броня", callback_data="craft_armorer"),
        types.InlineKeyboardButton("💎 Бижутерия", callback_data="craft_jeweler"),
        types.InlineKeyboardButton("⚗️ Зелья", callback_data="craft_alchemist"),
    )
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("craft_") and c.data.count("_") == 1)
def craft_category(c):
    prof = c.data.replace("craft_", "")
    p = get_player(c.from_user.id)
    text = f"🔨 *{PROFESSIONS[prof]}*\n{LINE}\nВыбери рецепт:"
    m = types.InlineKeyboardMarkup(row_width=1)
    for key, r in RECIPES.items():
        if r["prof"] != prof: continue
        can, _ = can_craft(p, key)
        mark = "✅" if can else "🔒"
        m.add(types.InlineKeyboardButton(f"{mark} {r['name']} (ур.{r['level']})",
                                          callback_data=f"recipe_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("recipe_"))
def recipe_view(c):
    key = c.data.replace("recipe_", "")
    p = get_player(c.from_user.id)
    r = RECIPES.get(key)
    if not r:
        bot.answer_callback_query(c.id, "❌ Нет рецепта"); return
    prof = r["prof"]
    lines = [f"🔨 *{r['name']}*", LINE,
             f"Профессия: {PROFESSIONS[prof]}",
             f"Уровень: {r['level']} (у тебя {p[f'prof_{prof}']})", ""]
    if "ore" in r:
        lines.append("🪨 *Ресурсы:*")
        for res, amt in r["ore"].items():
            have = p.get(res, 0)
            mark = "✅" if have >= amt else "❌"
            name = ORES.get(res, {}).get("name") or GEMS.get(res, {}).get("name", res)
            lines.append(f"  {mark} {name}: {have}/{amt}")
    if "herb" in r:
        lines.append("🌿 *Травы:*")
        for res, amt in r["herb"].items():
            have = p.get(res, 0)
            mark = "✅" if have >= amt else "❌"
            name = HERBS.get(res, {}).get("name", res)
            lines.append(f"  {mark} {name}: {have}/{amt}")
    can, msg = can_craft(p, key)
    lines.append("")
    lines.append(LINE)
    lines.append("✅ Можно крафтить!" if can else f"🔒 {msg}")
    text = "\n".join(lines)
    m = types.InlineKeyboardMarkup(row_width=1)
    if can:
        m.add(types.InlineKeyboardButton("🔨 Скрафтить", callback_data=f"make_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"craft_{prof}"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("make_"))
def make_item(c):
    key = c.data.replace("make_", "")
    p = get_player(c.from_user.id)
    ok, msg = do_craft(p, key)
    if ok:
        equipped = try_equip_if_better(p, key)
        if equipped: msg += "\n🔥 Автонадето!"
    save_player(p)
    bot.answer_callback_query(c.id, msg[:200])
    r = RECIPES.get(key)
    if r:
        c.data = f"craft_{r['prof']}"
        craft_category(c)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    print("RPG бот запущен...")
    bot.infinity_polling()
