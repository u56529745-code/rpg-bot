import telebot
from telebot import types
import threading, time, os, random, json
from flask import Flask
from data import *
from db import init_db, get_player, save_player, exp_needed, prof_level_for_exp, get_conn
from battle import (
    calc_player_stats, make_mob, player_turn, mob_turn,
    roll_herb, roll_ore_drop, roll_gem_drop, roll_loot, battle_text,
    is_dead, revive_if_possible, DEATH_TIME,
)
from craft import can_craft, do_craft, can_craft_void, do_craft_void

TOKEN = "8620344298:AAEYen6iM1Kjb4Gm4U3yHWGhEk7r2hG57k8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "ok"

battles = {}
clans = {}
clan_boss = {"hp": 2000000, "max_hp": 2000000, "last_death": 0, "damage": {}}
world_boss = {"hp": 1000000, "max_hp": 1000000, "last_spawn": 0, "damage": {}}
PET_TYPES = {
    "wolf": {"name": "🐺 Волк", "dmg": 50, "level": 1},
    "dragon": {"name": "🐉 Дракон", "dmg": 150, "level": 3},
    "phoenix": {"name": "🔥 Феникс", "dmg": 300, "level": 5},
    "unicorn": {"name": "🦄 Единорог", "dmg": 500, "level": 8},
    "demon": {"name": "👹 Демон", "dmg": 1000, "level": 12},
}

# ============ РЕГЕНЕРАЦИЯ ============
def regen_energy(p):
    now = time.time()
    last = p.get("last_energy_time", 0)
    if last == 0:
        p["last_energy_time"] = now
        return
    diff = now - last
    flow = p.get("energy_flow", 0) or 0
    per_cycle = 3 + flow * 0.1
    cycles = int(diff / 20)
    if cycles > 0:
        regen = int(cycles * per_cycle)
        p["energy"] = min(p["max_energy"], p["energy"] + regen)
        p["last_energy_time"] = now
    # Восстановление после смерти
    revive_if_possible(p)

def check_dead(c, p):
    """Возвращает True, если игрок мёртв. Показывает сообщение."""
    dead, remaining = is_dead(p)
    if dead:
        text = (
            f"💀 *ТЫ МЁРТВ*\n{LINE}\n"
            f"⏱ Восстановление через *{remaining} сек*\n\n"
            f"Пока недоступно:\n"
            f"🏰 Башня, ⛏ Шахта, ⚙️ Авто-шахта,\n"
            f"🔨 Крафт, 🐾 Питомцы, 👥 Кланы,\n"
            f"🎰 Рулетка, 🌍 Мировой босс\n\n"
            f"✅ Доступно: профиль, инвентарь, топ"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
              types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"))
        m.add(types.InlineKeyboardButton("🏆 Топ", callback_data="top"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                                  reply_markup=m, parse_mode="Markdown")
        except:
            try:
                bot.send_message(c.message.chat.id, text, reply_markup=m, parse_mode="Markdown")
            except: pass
        bot.answer_callback_query(c.id, f"💀 Ждать {remaining} сек")
        return True
    return False

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
        types.InlineKeyboardButton("🌍 Мировой босс", callback_data="world_boss"),
        types.InlineKeyboardButton("🎰 Рулетка", callback_data="roulette"),
        types.InlineKeyboardButton("🐾 Питомцы", callback_data="pets"),
        types.InlineKeyboardButton("👥 Кланы", callback_data="clans"),
        types.InlineKeyboardButton("🏆 Топ", callback_data="top"),
    )
    return m

def menu_text(p):
    rank = "E"
    if p["level"] >= 90: rank = "SSS+"
    elif p["level"] >= 70: rank = "SSS"
    elif p["level"] >= 50: rank = "SS"
    elif p["level"] >= 35: rank = "S"
    elif p["level"] >= 25: rank = "A"
    elif p["level"] >= 15: rank = "B"
    elif p["level"] >= 10: rank = "C"
    elif p["level"] >= 5: rank = "D"
    return (
        f"🎮 *ГЛАВНОЕ МЕНЮ*\n{LINE}\n"
        f"👤 {p['name']}  [{rank}]\n"
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
    if check_dead(c, p):
        return
    try:
        bot.edit_message_text(menu_text(p), c.message.chat.id, c.message.message_id,
                              reply_markup=main_menu(), parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# ПРОФИЛЬ
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
        f"⚡ Энергия: {p['energy']}/{p['max_energy']}\n"
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

# СТАТЫ
@bot.callback_query_handler(func=lambda c: c.data == "stats")
def stats(c):
    p = get_player(c.from_user.id)
    dmg, defense, crit, hp_bonus = calc_player_stats(p)
    flow = p.get("energy_flow", 0) or 0
    regen = 3 + flow * 0.1
    text = (
        f"📊 *СТАТЫ*\n{LINE}\n"
        f"💪 Сила: {p['strength']}\n"
        f"🏃 Ловкость: {p['agility']}\n"
        f"❤️ Выносливость: {p['vitality']}\n"
        f"⚡ Энергопоток: {flow} (+{regen:.1f} / 20 сек)\n\n"
        f"⚔️ Урон: {dmg}\n🛡 Защита: {defense}\n💥 Крит: {crit}%\n"
        f"❤️ Бонус HP: +{hp_bonus}%\n\n"
        f"🎯 Очков: *{p['stat_points']}*"
    )
    m = types.InlineKeyboardMarkup(row_width=2)
    if p["stat_points"] > 0:
        m.add(
            types.InlineKeyboardButton("💪 +1", callback_data="up_str"),
            types.InlineKeyboardButton("🏃 +1", callback_data="up_agi"),
            types.InlineKeyboardButton("❤️ +1", callback_data="up_vit"),
            types.InlineKeyboardButton("⚡ +1", callback_data="up_flow"),
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
        p["max_energy"] += 10
    elif s == "flow":
        p["energy_flow"] += 1
    p["stat_points"] -= 1
    save_player(p)
    bot.answer_callback_query(c.id, "✅ Улучшено!")
    stats(c)
    
# ============ БАШНЯ ============
@bot.callback_query_handler(func=lambda c: c.data == "tower")
def tower(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
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
    if check_dead(c, p):
        return
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
        secret_msg = ""
        if mob.get("boss"):
            if random.randint(1, 100) <= 3:
                p["void_shard"] = (p.get("void_shard", 0) or 0) + 1
                secret_msg = "\n💠 +1 Осколок бездны!"
        lvl_up = False
        while p["exp"] >= exp_needed(p["level"]):
            p["exp"] -= exp_needed(p["level"])
            p["level"] += 1
            p["stat_points"] += 5
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
        if secret_msg: text += secret_msg
        if lvl_up: text += f"\n\n⭐ *УРОВЕНЬ {p['level']}!* +5 очков"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
              types.InlineKeyboardButton("🔙 Меню", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id); return
    if p["hp"] <= 0:
        save_player(p)
        del battles[uid]
        text = (
            f"💀 *ТЫ УМЕР!*\n{LINE}\n"
            f"⏱ Восстановление через *60 сек*\n\n"
            f"Пока недоступно:\n"
            f"🏰 Башня, ⛏ Шахта, ⚙️ Авто-шахта,\n"
            f"🔨 Крафт, 🐾 Питомцы, 👥 Кланы,\n"
            f"🎰 Рулетка, 🌍 Мировой босс\n\n"
            f"✅ Доступно: профиль, инвентарь, топ"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
              types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"))
        m.add(types.InlineKeyboardButton("🏆 Топ", callback_data="top"))
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
    regen_energy(p)
    if check_dead(c, p):
        return
    if p["keys"] <= 0:
        bot.answer_callback_query(c.id, "❌ Нет ключей"); return
    p["keys"] -= 1
    p["floor"] += 1
    p["mob_kill"] = 0
    save_player(p)
    bot.answer_callback_query(c.id, f"🔑 Этаж {p['floor']} открыт!")
    tower(c)

# ============ КЛАНОВЫЙ БОСС ============
@bot.callback_query_handler(func=lambda c: c.data == "clan_boss")
def clan_boss_menu(c):
    global clan_boss
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    now = time.time()
    if clan_boss["hp"] <= 0:
        if now - clan_boss["last_death"] < 300:
            remaining = int(300 - (now - clan_boss["last_death"]))
            bot.answer_callback_query(c.id, f"⏱ Возрождение через {remaining} сек")
            return
        else:
            clan_boss["hp"] = clan_boss["max_hp"]
            clan_boss["damage"] = {}
    text = (
        f"🐉 *КЛАНОВЫЙ БОСС*\n{LINE}\n"
        f"❤️ HP: {clan_boss['hp']:,}/{clan_boss['max_hp']:,}\n"
        f"⚔️ Урон: 1000\n"
        f"🎯 Ловкость: 15%\n\n"
        f"Награда: сундук (5% оружие, 10 руды)\n"
        f"Возрождение: 5 мин"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать (10⚡)", callback_data="clan_boss_hit"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="clans"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "clan_boss_hit")
def clan_boss_hit(c):
    global clan_boss
    p = get_player(c.from_user.id)
    regen_energy(p)
    if check_dead(c, p):
        return
    if p["energy"] < 10:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 10
    dmg, defense, crit, _ = calc_player_stats(p)
    is_crit = random.randint(1, 100) <= crit
    if is_crit: dmg = int(dmg * 1.5)
    clan_boss["hp"] = max(0, clan_boss["hp"] - dmg)
    clan_boss["damage"][p["uid"]] = clan_boss["damage"].get(p["uid"], 0) + dmg
    if random.randint(1, 100) <= 15:
        p["hp"] -= 1000
        if p["hp"] <= 0:
            p["hp"] = 0
            p["death_time"] = time.time()
            save_player(p)
            bot.answer_callback_query(c.id, "💀 Ты умер!")
            return
    save_player(p)
    if clan_boss["hp"] <= 0:
        clan_boss["last_death"] = time.time()
        if random.randint(1, 100) <= 5:
            p["void_shard"] = (p.get("void_shard", 0) or 0) + 5
        for _ in range(10):
            ore = random.choice(list(ORES.keys()))
            p[ore] = (p.get(ore, 0) or 0) + 1
        if random.randint(1, 100) <= 50:
            p["void_shard"] = (p.get("void_shard", 0) or 0) + 1
        save_player(p)
        bot.send_message(c.message.chat.id, "🎉 Клановый босс побеждён! Награда получена!")
    bot.answer_callback_query(c.id, f"⚔️ {dmg} урона!")
    clan_boss_menu(c)

# ============ ШАХТА ============
@bot.callback_query_handler(func=lambda c: c.data == "mine")
def mine(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
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
    regen_energy(p)
    if check_dead(c, p):
        return
    if p["energy"] < 2:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 2
    ore_drops = roll_ore_drop(p["prof_miner"])
    gem_drops = []
    if random.randint(1, 100) <= 30:
        gem_drops = roll_gem_drop(p["prof_miner"])

    merged = {}
    for key, amt, exp in ore_drops:
        if key not in merged:
            merged[key] = {"amt": 0, "exp": 0, "is_gem": False}
        merged[key]["amt"] += amt
        merged[key]["exp"] += exp
    for key, amt, exp in gem_drops:
        if key not in merged:
            merged[key] = {"amt": 0, "exp": 0, "is_gem": True}
        merged[key]["amt"] += amt
        merged[key]["exp"] += exp

    text_lines = ["⛏ *ДОБЫЧА*", ""]
    total_exp = 0
    for key, data in merged.items():
        if data["is_gem"]:
            tier = GEM_TIER.get(key, "?")
            name = GEMS[key]["name"]
        else:
            tier = ORE_TIER.get(key, "?")
            name = ORES[key]["name"]
        text_lines.append(f"{name} ({tier}) × {data['amt']}")
        p[key] = (p.get(key, 0) or 0) + data["amt"]
        total_exp += data["exp"]

    p["exp_miner"] = (p.get("exp_miner", 0) or 0) + total_exp
    new_lvl = prof_level_for_exp(int(p["exp_miner"]))
    level_up = False
    if new_lvl > p["prof_miner"]:
        p["prof_miner"] = new_lvl
        level_up = True
    p["mine_count"] += 1
    save_player(p)
    text_lines.append("")
    text_lines.append(f"📈 +{total_exp} опыта")
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

# ============ АВТО-ШАХТА ============
def process_auto_mine(p):
    if not p.get("auto_mine_active"): return
    now = time.time()
    last = p.get("auto_mine_last_collect", 0) or p.get("auto_mine_started", now)
    elapsed = int(now - last)
    if elapsed < 5: return
    cycles = min(elapsed // 5, 17280)
    for _ in range(cycles):
        for key, amt, exp in roll_ore_drop(p["prof_miner"]):
            field = f"auto_mine_{key}"
            if field in p:
                p[field] = (p.get(field, 0) or 0) + amt
        if random.randint(1, 100) <= 30:
            for key, amt, exp in roll_gem_drop(p["prof_miner"]):
                field = f"auto_mine_{key}"
                if field in p:
                    p[field] = (p.get(field, 0) or 0) + amt
    p["auto_mine_last_collect"] = now

def auto_mine_active_markup():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(
        types.InlineKeyboardButton("🔄 Проверить", callback_data="auto_mine_check"),
        types.InlineKeyboardButton("💰 Забрать", callback_data="auto_mine_collect"),
    )
    return m

def auto_mine_start_markup():
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("⛏ Запустить", callback_data="auto_mine_start"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    return m

def auto_mine_text(p):
    started = p.get("auto_mine_started", 0) or 0
    elapsed_min = int((time.time() - started) / 60) if started else 0
    hours = elapsed_min // 60
    minutes = elapsed_min % 60
    bonus = MINER_BONUS.get(p["prof_miner"], 0)
    lines = []
    for key in list(ORES.keys()) + list(GEMS.keys()):
        val = p.get(f"auto_mine_{key}", 0) or 0
        if val > 0:
            if key in ORES:
                tier = ORE_TIER.get(key, "?")
                name = ORES[key]["name"]
            else:
                tier = GEM_TIER.get(key, "?")
                name = GEMS[key]["name"]
            lines.append(f"{name} ({tier}): {val}")
    return (
        f"⚙️ *АВТО-ШАХТА*\n{LINE}\n"
        f"⏱ Работает: {hours}ч {minutes}мин\n"
        f"⛏ Шахтёр: ур.{p['prof_miner']} (+{bonus}%)\n\n"
        + ("\n".join(lines) if lines else "Пока пусто.")
    )

@bot.callback_query_handler(func=lambda c: c.data == "auto_mine_menu")
def auto_mine_menu(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    if p.get("auto_mine_active"):
        process_auto_mine(p); save_player(p)
        text = auto_mine_text(p)
        m = auto_mine_active_markup()
    else:
        text = (
            f"⚙️ *АВТО-ШАХТА*\n{LINE}\n"
            f"Копает в фоне (все руды + самоцветы).\n\n"
            f"⚡ 2⚡ / 5 сек\n"
            f"⏱ Макс: 24 часа\n"
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
    regen_energy(p)
    if check_dead(c, p):
        return
    now = time.time()
    p["auto_mine_active"] = 1
    p["auto_mine_started"] = now
    p["auto_mine_last_collect"] = now
    for key in list(ORES.keys()) + list(GEMS.keys()):
        field = f"auto_mine_{key}"
        if field in p:
            p[field] = 0
    save_player(p)
    bot.answer_callback_query(c.id, "⛏ Запущена!")
    auto_mine_menu(c)

@bot.callback_query_handler(func=lambda c: c.data == "auto_mine_check")
def auto_mine_check(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    if check_dead(c, p):
        return
    process_auto_mine(p); save_player(p)
    text = auto_mine_text(p)
    m = auto_mine_active_markup()
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id, "🔄")

@bot.callback_query_handler(func=lambda c: c.data == "auto_mine_collect")
def auto_mine_collect(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    if check_dead(c, p):
        return
    process_auto_mine(p)
    total = 0
    for key in list(ORES.keys()) + list(GEMS.keys()):
        field = f"auto_mine_{key}"
        amt = p.get(field, 0) or 0
        if amt > 0:
            p[key] = (p.get(key, 0) or 0) + amt
            p[field] = 0
            total += amt
    p["auto_mine_active"] = 0
    p["auto_mine_started"] = 0
    p["auto_mine_last_collect"] = 0
    save_player(p)
    bot.answer_callback_query(c.id, f"💰 Забрано: {total} шт.")
    auto_mine_menu(c)

# ============ КРАФТ ============
@bot.callback_query_handler(func=lambda c: c.data == "craft")
def craft_menu(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
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
    m.add(types.InlineKeyboardButton("🖤 Бездна", callback_data="craft_void"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("craft_") and c.data.count("_") == 1)
def craft_category(c):
    prof = c.data.replace("craft_", "")
    p = get_player(c.from_user.id)
    regen_energy(p)
    if check_dead(c, p):
        return
    if prof == "void":
        if p["prof_smith"] < 100 and p["prof_armorer"] < 100 and p["prof_jeweler"] < 100:
            bot.answer_callback_query(c.id, "❌ Нужен 100 уровень профессии")
            return
        text = f"🖤 *БЕЗДНА*\n{LINE}\nВыбери предмет:"
        m = types.InlineKeyboardMarkup(row_width=1)
        for key, r in RECIPES_VOID.items():
            name = WEAPONS.get(key, {}).get("name") or ARMORS.get(key, {}).get("name") or ACCESSORIES.get(key, {}).get("name", key)
            m.add(types.InlineKeyboardButton(name, callback_data=f"recipe_{key}"))
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id)
        return

    text = f"🔨 *{PROFESSIONS[prof]}*\n{LINE}\nВыбери рецепт:"
    m = types.InlineKeyboardMarkup(row_width=1)
    for key, r in RECIPES.items():
        if r["prof"] != prof: continue
        can, _ = can_craft(p, key)
        mark = "✅" if can else "🔒"
        m.add(types.InlineKeyboardButton(f"{mark} {r['name']} (ур.{r['level']})", callback_data=f"recipe_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("recipe_"))
def recipe_view(c):
    key = c.data.replace("recipe_", "")
    p = get_player(c.from_user.id)
    regen_energy(p)
    if check_dead(c, p):
        return
    if key in RECIPES_VOID:
        r = RECIPES_VOID[key]
        name = WEAPONS.get(key, {}).get("name") or ARMORS.get(key, {}).get("name") or ACCESSORIES.get(key, {}).get("name", key)
        lines = [f"🖤 *{name}*", LINE, "БЕЗДНА", ""]
        lines.append(f"🖤 Сердце бездны: {p.get('void_heart', 0)}/{r['void_heart']}")
        lines.append(f"💠 Осколков бездны: {p.get('void_shard', 0)}/{r['void_shard']}")
        lines.append(f"🕯 Бездонных душ: {p.get('void_soul', 0)}/{r['void_soul']}")
        lines.append(f"📦 Базовый предмет: {r['base_item']}")
        can, msg = can_craft_void(p, key)
        lines.append("")
        lines.append(LINE)
        lines.append("✅ Можно крафтить!" if can else f"🔒 {msg}")
        text = "\n".join(lines)
        m = types.InlineKeyboardMarkup(row_width=1)
        if can:
            m.add(types.InlineKeyboardButton("🖤 Скрафтить", callback_data=f"make_{key}"))
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft_void"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id)
        return
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
    lines.append("🎲 Шанс: 90% / 5% крит ×5 / 5% провал")
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
    regen_energy(p)
    if check_dead(c, p):
        return
    if key in RECIPES_VOID:
        ok, msg = do_craft_void(p, key)
    else:
        ok, msg = do_craft(p, key)
        if ok:
            equipped = try_equip_if_better(p, key)
            if equipped: msg += "\n🔥 Автонадето!"
    save_player(p)
    bot.answer_callback_query(c.id, msg[:200])
    r = RECIPES.get(key) or RECIPES_VOID.get(key)
    if r:
        if key in RECIPES_VOID:
            c.data = "craft_void"
        else:
            c.data = f"craft_{r['prof']}"
        craft_category(c)

# ============ ИНВЕНТАРЬ ============
@bot.callback_query_handler(func=lambda c: c.data == "inv")
def inv(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
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
    lines.append("\n🖤 *Ресурсы бездны:*")
    for k, v in [("void_heart", VOID_HEART), ("void_shard", VOID_SHARD), ("void_soul", VOID_SOUL)]:
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
    m.add(types.InlineKeyboardButton("🔧 Улучшить (100к)", callback_data=f"upgrade_{idx}"))
    m.add(types.InlineKeyboardButton("🛠 Разобрать", callback_data=f"dis_{idx}"))
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

@bot.callback_query_handler(func=lambda c: c.data.startswith("dis_"))
def disassemble_item(c):
    p = get_player(c.from_user.id)
    idx = int(c.data.split("_")[1])
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    if idx >= len(items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = items.pop(idx)
    p["crafted_items"] = json.dumps(items)
    price = max(25, stat_of(key) * 10)
    p["silver"] += price
    save_player(p)
    bot.answer_callback_query(c.id, f"🛠 +{price} серебра")
    crafted_menu(c)

@bot.callback_query_handler(func=lambda c: c.data.startswith("upgrade_"))
def upgrade_item(c):
    p = get_player(c.from_user.id)
    idx = int(c.data.split("_")[1])
    if p["silver"] < 100000:
        bot.answer_callback_query(c.id, "❌ Нужно 100к"); return
    p["silver"] -= 100000
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    if idx >= len(items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    roll = random.randint(1, 100)
    if roll <= 60:
        msg = "✅ Улучшено!"
    else:
        items.pop(idx)
        msg = "💀 Предмет сломан!"
    p["crafted_items"] = json.dumps(items)
    save_player(p)
    bot.answer_callback_query(c.id, msg)
    crafted_menu(c)
    
# ============ ИМПОРТ get_conn ============
# ВАЖНО: добавь в самый верх rpg_bot.py:
# from db import get_conn
# Если ещё нет — добавь в импорт.

# ============ ПИТОМЦЫ ============
@bot.callback_query_handler(func=lambda c: c.data == "pets")
def pets_menu(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    pets = [i for i in items if i.startswith("pet_")]
    if not pets:
        text = "🐾 *ПИТОМЦЫ*\n\nУ тебя нет питомца.\nПадают с боссов (яйца)."
    else:
        lines = ["🐾 *ПИТОМЦЫ*", LINE, ""]
        for pet in pets:
            key = pet.replace("pet_", "")
            pt = PET_TYPES.get(key, {})
            lines.append(f"{pt.get('name', key)} — +{pt.get('dmg', 0)} dmg")
        text = "\n".join(lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🎁 Открыть яйцо (50 💠)", callback_data="pet_hatch"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "pet_hatch")
def pet_hatch(c):
    p = get_player(c.from_user.id)
    if check_dead(c, p):
        return
    if p.get("void_shard", 0) < 50:
        bot.answer_callback_query(c.id, "❌ Нужно 50 осколков"); return
    p["void_shard"] -= 50
    pet_key = random.choice(list(PET_TYPES.keys()))
    try: items = json.loads(p.get("crafted_items", "[]") or "[]")
    except: items = []
    items.append(f"pet_{pet_key}")
    p["crafted_items"] = json.dumps(items)
    save_player(p)
    pt = PET_TYPES[pet_key]
    bot.answer_callback_query(c.id, f"🎉 Ты получил {pt['name']}!")
    pets_menu(c)

# ============ КЛАНЫ ============
@bot.callback_query_handler(func=lambda c: c.data == "clans")
def clans_menu(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    text = (
        f"👥 *КЛАНЫ*\n{LINE}\n"
        f"💰 Серебро: {p['silver']:,}\n\n"
        f"Создать клан — 100к серебра"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🏰 Создать клан (100к)", callback_data="clan_create"))
    m.add(types.InlineKeyboardButton("🐉 Клановый босс", callback_data="clan_boss"))
    m.add(types.InlineKeyboardButton("🏆 Топ кланов", callback_data="clan_top"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "clan_create")
def clan_create(c):
    p = get_player(c.from_user.id)
    if check_dead(c, p):
        return
    if p["silver"] < 100000:
        bot.answer_callback_query(c.id, "❌ Нужно 100к"); return
    p["silver"] -= 100000
    clan_name = f"Клан_{p['name']}"
    clans[clan_name] = {"leader": p["uid"], "members": [p["uid"]], "silver": 0}
    save_player(p)
    bot.answer_callback_query(c.id, f"✅ Клан {clan_name} создан!")
    clans_menu(c)

@bot.callback_query_handler(func=lambda c: c.data == "clan_top")
def clan_top(c):
    if not clans:
        bot.answer_callback_query(c.id, "❌ Нет кланов"); return
    sorted_clans = sorted(clans.items(), key=lambda x: len(x[1]["members"]), reverse=True)[:10]
    lines = ["🏆 *ТОП КЛАНОВ*", LINE, ""]
    for i, (name, data) in enumerate(sorted_clans, 1):
        lines.append(f"{i}. {name} — {len(data['members'])} чел.")
    text = "\n".join(lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="clans"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# ============ РУЛЕТКА ============
@bot.callback_query_handler(func=lambda c: c.data == "roulette")
def roulette_menu(c):
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    text = (
        f"🎰 *РУЛЕТКА*\n{LINE}\n"
        f"💰 Серебро: {p['silver']:,}\n\n"
        f"Стоимость: 10 000\n"
        f"65% — проигрыш\n"
        f"35% — выигрыш (×2–×10)"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🎰 Крутить (10к)", callback_data="roulette_spin"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "roulette_spin")
def roulette_spin(c):
    p = get_player(c.from_user.id)
    if check_dead(c, p):
        return
    if p["silver"] < 10000:
        bot.answer_callback_query(c.id, "❌ Нужно 10к"); return
    p["silver"] -= 10000
    roll = random.randint(1, 100)
    if roll <= 65:
        msg = "💀 Проигрыш!"
    else:
        mult = random.choice([2, 3, 5, 10])
        win = 10000 * mult
        p["silver"] += win
        msg = f"🎉 Выигрыш ×{mult}! +{win:,}"
    save_player(p)
    bot.answer_callback_query(c.id, msg)
    roulette_menu(c)

# ============ ТОП (ФИКС) ============
@bot.callback_query_handler(func=lambda c: c.data == "top")
def top_menu(c):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name, silver FROM players ORDER BY silver DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        lines = ["🏆 *ТОП-10 ПО СЕРЕБРУ*", LINE, ""]
        for i, (name, silver) in enumerate(rows, 1):
            lines.append(f"{i}. {name} — {silver:,}")
        text = "\n".join(lines)
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except Exception as e:
        bot.answer_callback_query(c.id, f"❌ Ошибка: {str(e)[:50]}")
    else:
        bot.answer_callback_query(c.id)

# ============ МИРОВОЙ БОСС ============
@bot.callback_query_handler(func=lambda c: c.data == "world_boss")
def world_boss_menu(c):
    global world_boss
    p = get_player(c.from_user.id)
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    now = time.time()
    if world_boss["hp"] <= 0:
        if now - world_boss["last_spawn"] < 86400:
            remaining = int((86400 - (now - world_boss["last_spawn"])) / 3600)
            bot.answer_callback_query(c.id, f"⏱ Возрождение через ~{remaining}ч")
            return
        else:
            world_boss["hp"] = world_boss["max_hp"]
            world_boss["damage"] = {}
    text = (
        f"🌍 *МИРОВОЙ БОСС*\n{LINE}\n"
        f"❤️ HP: {world_boss['hp']:,}/{world_boss['max_hp']:,}\n"
        f"⚔️ Урон: ОЧЕНЬ сильный\n\n"
        f"За удар: 📈 опыт + 1% шанс на секретный предмет\n\n"
        f"Возрождение: каждые 24ч в 16:00 МСК"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать (10⚡)", callback_data="world_boss_hit"))
    m.add(types.InlineKeyboardButton("🏆 Топ урона", callback_data="world_boss_top"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "world_boss_hit")
def world_boss_hit(c):
    global world_boss
    p = get_player(c.from_user.id)
    regen_energy(p)
    if check_dead(c, p):
        return
    if p["energy"] < 10:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 10
    dmg, defense, crit, _ = calc_player_stats(p)
    is_crit = random.randint(1, 100) <= crit
    if is_crit: dmg = int(dmg * 1.5)
    world_boss["hp"] = max(0, world_boss["hp"] - dmg)
    world_boss["damage"][p["uid"]] = world_boss["damage"].get(p["uid"], 0) + dmg
    exp_gain = 50
    p["exp"] += exp_gain
    lvl_up = False
    while p["exp"] >= exp_needed(p["level"]):
        p["exp"] -= exp_needed(p["level"])
        p["level"] += 1
        p["stat_points"] += 5
        p["max_hp"] += 20
        p["hp"] = p["max_hp"]
        lvl_up = True
    secret_msg = ""
    if random.randint(1, 100) <= 1:
        secret_key = random.choice(["demon_mace", "dragon_katana", "god_flesh", "eternity_ring", "demon_crown"])
        try: items = json.loads(p.get("crafted_items", "[]") or "[]")
        except: items = []
        items.append(secret_key)
        p["crafted_items"] = json.dumps(items)
        name = WEAPONS.get(secret_key, {}).get("name") or ARMORS.get(secret_key, {}).get("name") or ACCESSORIES.get(secret_key, {}).get("name", secret_key)
        secret_msg = f"\n🎁 СЕКРЕТНЫЙ ДРОП: {name}!"
    if random.randint(1, 100) <= 40:
        p["hp"] -= 500
        if p["hp"] <= 0:
            p["hp"] = 0
            p["death_time"] = time.time()
            save_player(p)
            bot.answer_callback_query(c.id, "💀 Ты умер!")
            return
    save_player(p)
    msg = f"⚔️ {dmg} урона! +{exp_gain} опыта{secret_msg}"
    if lvl_up: msg += f"\n⭐ Уровень {p['level']}!"
    if world_boss["hp"] <= 0:
        world_boss["last_spawn"] = time.time()
        bot.send_message(c.message.chat.id, "🎉 МИРОВОЙ БОСС ПОБЕЖДЁН!")
    bot.answer_callback_query(c.id, msg[:200])
    world_boss_menu(c)

@bot.callback_query_handler(func=lambda c: c.data == "world_boss_top")
def world_boss_top(c):
    if not world_boss["damage"]:
        bot.answer_callback_query(c.id, "Пока никто не бил"); return
    sorted_dmg = sorted(world_boss["damage"].items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ["🏆 *ТОП УРОНА*", LINE, ""]
    for i, (uid, dmg) in enumerate(sorted_dmg, 1):
        p = get_player(uid)
        lines.append(f"{i}. {p['name']} — {dmg:,}")
    text = "\n".join(lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="world_boss"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# ============ АВТО-БОСС ============
def world_boss_scheduler():
    while True:
        now = time.localtime()
        if now.tm_hour == 16 and now.tm_min == 0:
            global world_boss
            if world_boss["hp"] <= 0:
                world_boss["hp"] = world_boss["max_hp"]
                world_boss["damage"] = {}
        time.sleep(60)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=world_boss_scheduler, daemon=True).start()
    print("RPG бот запущен...")
    bot.infinity_polling()
