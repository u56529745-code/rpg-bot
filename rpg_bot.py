import telebot
from telebot import types
import threading, time, os, random, json
from flask import Flask
from data import *
from db import init_db, get_player, save_player, exp_needed, prof_level_for_exp, get_conn, is_name_set
import battle as battle_module
from battle import (
    calc_player_stats, make_mob, player_turn, mob_turn,
    roll_herb, roll_ore_drop, roll_gem_drop, roll_loot, roll_meat, battle_text,
    is_dead, revive_if_possible, DEATH_TIME, get_armor_hp_bonus,
    apply_poison, tick_poison,
)
from craft import can_craft, do_craft, can_craft_void, do_craft_void

TOKEN = "8620344298:AAEYen6iM1Kjb4Gm4U3yHWGhEk7r2hG57k8"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "ok"

battles = {}
clan_boss = {"hp": 500000, "max_hp": 500000, "last_death": 0, "damage": {}}
world_boss = {"hp": 1500000, "max_hp": 1500000, "last_spawn": 0, "damage": {}}

awaiting_name = {}

FEED_HERB = 10
FEED_MEAT = 30
SATIETY_PER_LEVEL = 100
EVO_LEVEL = 10

LINE = "━━━━━━━━━━━━━━━━━━"

def safe_name(name):
    return str(name).replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

def get_inv(p):
    try:
        return json.loads(p.get("inventory_items", "[]") or "[]")
    except:
        return []

def set_inv(p, items):
    p["inventory_items"] = json.dumps(items)

def get_pets(p):
    try:
        return json.loads(p.get("pet_data", "[]") or "[]")
    except:
        return []

def set_pets(p, pets):
    p["pet_data"] = json.dumps(pets)

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

def item_tier(key):
    if key in WEAPON_TIER: return WEAPON_TIER[key]
    if key in ARMOR_TIER: return ARMOR_TIER[key]
    if key in ACCESSORY_TIER: return ACCESSORY_TIER[key]
    return "E"

def try_equip_if_better(p, key):
    t = item_type(key)
    if t is None: return False
    current = p.get(t, "none")
    if stat_of(key) > stat_of(current):
        p[t] = key
        return True
    return False

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
    revive_if_possible(p)

def check_dead(c, p):
    dead, remaining = is_dead(p)
    if dead:
        text = (
            f"💀 *ТЫ МЁРТВ*\n{LINE}\n"
            f"⏱ Восстановление через *{remaining} сек*\n\n"
            f"Пока недоступно:\n"
            f"🏰 Башня, ⛏ Шахта, ⚙️ Авто-шахта,\n"
            f"🔨 Крафт, 🐾 Питомцы, 🐉 Клановый босс,\n"
            f"🎰 Рулетка, 🌍 Мировой босс\n\n"
            f"✅ Доступно: профиль, инвентарь, топ"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
              types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"))
        m.add(types.InlineKeyboardButton("🏆 Топ", callback_data="top_menu"))
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

def get_current_event():
    now = time.localtime()
    wd = now.tm_wday
    hour = now.tm_hour
    if wd == 5 or wd == 6:
        return ("🎉 Выходные! ×2 дроп", 2.0, 1.0, False)
    msk_hour = (hour + 3) % 24
    if wd == 0 and 12 <= msk_hour < 17:
        return ("🌑 Кровавая луна! ×2 опыт, ×2 урон", 1.0, 2.0, True)
    return (None, 1.0, 1.0, False)

def update_event_flag():
    _, _, _, bm = get_current_event()
    battle_module.BLOOD_MOON = bm

def main_menu():
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
        types.InlineKeyboardButton("⛏ Шахта", callback_data="mine"),
        types.InlineKeyboardButton("🔨 Крафт", callback_data="craft"),
        types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"),
        types.InlineKeyboardButton("📊 Статы", callback_data="stats"),
        types.InlineKeyboardButton("⚙️ Авто-шахта", callback_data="auto_mine_menu"),
        types.InlineKeyboardButton("🌍 Мировой босс", callback_data="world_boss"),
        types.InlineKeyboardButton("🐉 Клановый босс", callback_data="clan_boss"),
        types.InlineKeyboardButton("🎰 Рулетка", callback_data="roulette"),
        types.InlineKeyboardButton("🐾 Питомцы", callback_data="pets"),
        types.InlineKeyboardButton("📖 Справочник", callback_data="handbook"),
        types.InlineKeyboardButton("🏆 Топы", callback_data="top_menu"),
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
    clan_str = f"\n🛡 Клан: {safe_name(p['clan'])}" if p.get("clan") else ""
    event_str = ""
    ev_name, _, _, _ = get_current_event()
    if ev_name:
        event_str = f"\n{ev_name}"
    return (
        f"🎮 *ГЛАВНОЕ МЕНЮ*\n{LINE}\n"
        f"👤 {safe_name(p['name'])}  [{rank}]{clan_str}{event_str}\n"
        f"⭐ Ур: {p['level']} ({p['exp']}/{exp_needed(p['level'])})\n"
        f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
        f"⚡ Энергия: {p['energy']}/{p['max_energy']}\n"
        f"💰 Серебро: {p['silver']:,}\n"
        f"🏰 Этаж: {p['floor']}/50\n"
        f"🐾 Мобов: {p['mob_kill']}/150\n"
        f"🔑 Ключей: {p['keys']}"
    )

def ask_name(uid, chat_id, reason="new"):
    awaiting_name[uid] = reason
    if reason == "new":
        text = (
            f"👋 *Привет!*\n{LINE}\n"
            f"Придумай имя своему персонажу.\n\n"
            f"✏️ Напиши имя (от 2 до 20 символов):"
        )
    else:
        text = (
            f"✏️ *Смена имени*\n{LINE}\n"
            f"Напиши новое имя (от 2 до 20 символов).\n"
            f"⚠️ Это можно сделать только 1 раз!"
        )
    bot.send_message(chat_id, text, parse_mode="Markdown")

def validate_name(text):
    if not text:
        return False, "Имя не может быть пустым."
    text = text.strip()
    if len(text) < 2:
        return False, "Имя слишком короткое (минимум 2 символа)."
    if len(text) > 20:
        return False, "Имя слишком длинное (максимум 20 символов)."
    return True, text

def require_name(c, p):
    if not is_name_set(p.get("name")):
        uid = c.from_user.id
        if uid not in awaiting_name:
            ask_name(uid, c.message.chat.id, "new")
        else:
            bot.answer_callback_query(c.id, "✏️ Сначала введи имя!")
        return True
    return False

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    p = get_player(uid, "Игрок")
    if uid in awaiting_name:
        ask_name(uid, m.chat.id, awaiting_name[uid])
        return
    if not is_name_set(p.get("name")):
        ask_name(uid, m.chat.id, "new")
        return
    regen_energy(p)
    save_player(p)
    bot.send_message(m.chat.id, menu_text(p), reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(m):
    uid = m.from_user.id
    if uid not in awaiting_name:
        p = get_player(uid, "Игрок")
        if not is_name_set(p.get("name")):
            ask_name(uid, m.chat.id, "new")
        else:
            bot.send_message(m.chat.id, "🤔 Не понимаю. Используй /start или кнопки меню.")
        return
    reason = awaiting_name[uid]
    ok, result = validate_name(m.text)
    if not ok:
        bot.send_message(m.chat.id, f"❌ {result}\nПопробуй ещё:")
        return
    p = get_player(uid, "Игрок")
    p["name"] = result
    if reason == "change":
        p["name_changed"] = 1
    save_player(p)
    del awaiting_name[uid]
    regen_energy(p)
    save_player(p)
    bot.send_message(
        m.chat.id,
        f"✅ *Имя сохранено:* {safe_name(result)}\n\n" + menu_text(p),
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda c: c.data == "menu")
def back_menu(c):
    p = get_player(c.from_user.id, "Игрок")
    if require_name(c, p):
        return
    regen_energy(p)
    save_player(p)
    update_event_flag()
    if check_dead(c, p):
        return
    try:
        bot.edit_message_text(menu_text(p), c.message.chat.id, c.message.message_id,
                              reply_markup=main_menu(), parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "profile")
def profile(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    w = WEAPONS.get(p["weapon"], WEAPONS["fists"])
    a = ARMORS.get(p["armor"], ARMORS["none"])
    acc = ACCESSORIES.get(p["accessory"], ACCESSORIES["none"])
    clan_str = f"🛡 Клан: {safe_name(p['clan'])}\n" if p.get("clan") else "🛡 Клан: —\n"
    text = (
        f"👤 *ПРОФИЛЬ*\n{LINE}\n"
        f"📛 Имя: {safe_name(p['name'])}\n"
        f"{clan_str}"
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
    m = types.InlineKeyboardMarkup(row_width=1)
    if p.get("name_changed", 0) == 0:
        m.add(types.InlineKeyboardButton("✏️ Сменить имя (1 раз)", callback_data="name_change"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "name_change")
def name_change(c):
    p = get_player(c.from_user.id)
    if p.get("name_changed", 0) != 0:
        bot.answer_callback_query(c.id, "❌ Ты уже менял имя!")
        return
    bot.answer_callback_query(c.id)
    ask_name(c.from_user.id, c.message.chat.id, "change")

@bot.callback_query_handler(func=lambda c: c.data == "stats")
def stats(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    dmg, defense, crit, hp_bonus = calc_player_stats(p)
    flow = p.get("energy_flow", 0) or 0
    regen = 3 + flow * 0.1
    armor_hp = get_armor_hp_bonus(p)
    text = (
        f"📊 *СТАТЫ*\n{LINE}\n"
        f"💪 Сила: {p['strength']}\n"
        f"🏃 Ловкость: {p['agility']}\n"
        f"❤️ Выносливость: {p['vitality']}\n"
        f"⚡ Энергопоток: {flow} (+{regen:.1f} / 20 сек)\n\n"
        f"⚔️ Урон: {dmg}\n🛡 Защита: {defense}\n💥 Крит: {crit}%\n"
        f"❤️ Бонус HP: +{hp_bonus}%\n"
        f"🛡 HP от брони: +{armor_hp}\n\n"
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
    if require_name(c, p):
        return
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

@bot.callback_query_handler(func=lambda c: c.data == "tower")
def tower(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p); save_player(p)
    update_event_flag()
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
    if require_name(c, p):
        return
    regen_energy(p)
    update_event_flag()
    if check_dead(c, p):
        return
    if p["energy"] < 5:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 5
    is_boss = p["mob_kill"] >= 149
    mob = make_mob(p["floor"], is_boss)
    battles[c.from_user.id] = {"mob": mob, "turn": 1}
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
    if require_name(c, p):
        return
    mob = battles[uid]["mob"]
    turn = battles[uid].get("turn", 1)

    pdmg, is_crit, p_dodged, pet_dmg, pet_strike, heal_msg, poison_applied = player_turn(p, mob, turn)

    if poison_applied:
        apply_poison(mob, pdmg)

    poison_tick = 0
    if mob["hp"] > 0:
        poison_tick = tick_poison(mob)

    m_dmg, m_dodged = 0, False
    if mob["hp"] > 0:
        m_dmg, m_dodged = mob_turn(p, mob)

    log = battle_text(p, mob, pdmg, is_crit, m_dmg, m_dodged, p_dodged,
                      pet_dmg, pet_strike, heal_msg, poison_applied, poison_tick)

    if mob["hp"] <= 0:
        _, drop_mult, exp_mult, _ = get_current_event()

        p["exp"] += int(mob["exp"] * exp_mult)
        p["silver"] += mob["silver"]
        p["kills"] += 1
        p["mob_kill"] += 1
        if mob.get("boss"): p["boss_kills"] += 1

        herb = roll_herb(p["floor"])
        p[herb] += 1
        loot = roll_loot(p["floor"])
        p[loot] = (p.get(loot, 0) or 0) + 1

        got_meat = roll_meat()
        if got_meat:
            p["raw_meat"] = (p.get("raw_meat", 0) or 0) + 1

        golden_bonus = ""
        if mob.get("golden"):
            extra_loot = roll_loot(p["floor"])
            p[extra_loot] = (p.get(extra_loot, 0) or 0) + 2
            p["raw_meat"] = (p.get("raw_meat", 0) or 0) + 2
            p["keys"] += 1
            golden_bonus = f"\n🌟 Бонус золотого: +2 {MOB_LOOT[extra_loot]['name']}, +2 🥩, +1 🔑"

        key_drop = random.randint(1, 100) <= 6
        if key_drop:
            p["keys"] += 1

        if p["mob_kill"] % 50 == 0 and p["mob_kill"] > 0:
            p["keys"] += 1
            golden_bonus += "\n🔑 Гарантированный ключ за 50 мобов!"

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
            f"📈 +{int(mob['exp'] * exp_mult)} опыта\n"
            f"💰 +{mob['silver']} серебра\n"
            f"🌿 +1 {HERBS[herb]['name']}\n"
            f"👹 +1 {MOB_LOOT[loot]['name']}"
        )
        if got_meat:
            text += "\n🥩 +1 Сырое мясо"
        if key_drop:
            text += "\n🔑 *Ключ выпал!*"
        text += golden_bonus
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
            f"✅ Доступно: профиль, инвентарь, топ"
        )
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
              types.InlineKeyboardButton("🎒 Инвентарь", callback_data="inv"))
        m.add(types.InlineKeyboardButton("🏆 Топы", callback_data="top_menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id); return

    battles[uid]["turn"] = turn + 1
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
    if require_name(c, p):
        return
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

@bot.callback_query_handler(func=lambda c: c.data == "mine")
def mine(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
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
    if require_name(c, p):
        return
    regen_energy(p)
    if check_dead(c, p):
        return
    if p["energy"] < 2:
        bot.answer_callback_query(c.id, "❌ Нет энергии"); return
    p["energy"] -= 2

    _, drop_mult, _, _ = get_current_event()

    ore_drops = roll_ore_drop(p["prof_miner"])
    gem_drops = []
    if random.randint(1, 100) <= 30:
        gem_drops = roll_gem_drop(p["prof_miner"])

    merged = {}
    for key, amt, exp in ore_drops:
        final_amt = int(amt * drop_mult)
        if key not in merged:
            merged[key] = {"amt": 0, "exp": 0, "is_gem": False}
        merged[key]["amt"] += final_amt
        merged[key]["exp"] += exp
    for key, amt, exp in gem_drops:
        final_amt = int(amt * drop_mult)
        if key not in merged:
            merged[key] = {"amt": 0, "exp": 0, "is_gem": True}
        merged[key]["amt"] += final_amt
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

    total_exp = int(total_exp * (1.5 if get_current_event()[2] > 1 else 1.0))

    p["exp_miner"] = (p.get("exp_miner", 0) or 0) + total_exp
    new_lvl = prof_level_for_exp(int(p["exp_miner"]))
    level_up = False
    if new_lvl > p["prof_miner"]:
        p["prof_miner"] = new_lvl
        level_up = True

    legend_msg = ""
    if p["prof_miner"] >= 100 and p.get("legend_chest_miner", 0) == 0:
        p["legend_chest_miner"] = 1
        p["chest_legend"] = (p.get("chest_legend", 0) or 0) + 1
        legend_msg = "\n👑 ЛЕГЕНДАРНЫЙ СУНДУК за 100 уровень шахтёра!"

    p["mine_count"] += 1
    save_player(p)
    text_lines.append("")
    text_lines.append(f"📈 +{total_exp} опыта")
    text_lines.append(f"⚡ Осталось: {p['energy']}")
    if level_up:
        text_lines.append(f"\n🎉 *Шахтёр → ур. {new_lvl}!*")
    if legend_msg:
        text_lines.append(legend_msg)
    text = "\n".join(text_lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Ещё", callback_data="dig"),
          types.InlineKeyboardButton("🔙 Шахта", callback_data="mine"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

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
    if require_name(c, p):
        return
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
    if require_name(c, p):
        return
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
    if require_name(c, p):
        return
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
    if require_name(c, p):
        return
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

INV_PAGE_SIZE = 7

@bot.callback_query_handler(func=lambda c: c.data == "inv")
def inv(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p); save_player(p)
    text = f"🎒 *ИНВЕНТАРЬ*\n{LINE}\nВыбери раздел:"
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("🪨 Руда", callback_data="inv_cat_ore_0"),
        types.InlineKeyboardButton("💎 Самоцветы", callback_data="inv_cat_gem_0"),
        types.InlineKeyboardButton("🌿 Травы", callback_data="inv_cat_herb_0"),
        types.InlineKeyboardButton("🥩 Мясо", callback_data="inv_cat_meat_0"),
        types.InlineKeyboardButton("👹 Лут", callback_data="inv_cat_loot_0"),
        types.InlineKeyboardButton("🖤 Бездна", callback_data="inv_cat_void_0"),
        types.InlineKeyboardButton("📦 Сундуки", callback_data="inv_chests"),
        types.InlineKeyboardButton("⚔️ Снаряжение", callback_data="inv_cat_gear_0"),
    )
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("inv_cat_"))
def inv_category(c):
    parts = c.data.split("_")
    cat = parts[2]
    page = int(parts[3])
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return

    items = []
    if cat == "ore":
        for k, v in ORES.items():
            if p.get(k, 0) > 0:
                tier = ORE_TIER.get(k, "?")
                items.append(f"{v['name']} ({tier}): {p[k]}")
    elif cat == "gem":
        for k, v in GEMS.items():
            if p.get(k, 0) > 0:
                tier = GEM_TIER.get(k, "?")
                items.append(f"{v['name']} ({tier}): {p[k]}")
    elif cat == "herb":
        for k, v in HERBS.items():
            if p.get(k, 0) > 0:
                items.append(f"{v['name']}: {p[k]}")
    elif cat == "meat":
        amt = p.get("raw_meat", 0)
        if amt > 0:
            items.append(f"🥩 Сырое мясо: {amt}")
    elif cat == "loot":
        for k, v in MOB_LOOT.items():
            if p.get(k, 0) > 0:
                items.append(f"{v['name']}: {p[k]}")
    elif cat == "void":
        for k, v in [("void_heart", VOID_HEART), ("void_shard", VOID_SHARD), ("void_soul", VOID_SOUL)]:
            if p.get(k, 0) > 0:
                items.append(f"{v['name']}: {p[k]}")
    elif cat == "gear":
        inv_items = get_inv(p)
        if not inv_items:
            items = ["_Пусто_"]
        else:
            for key in inv_items:
                items.append(f"{item_name(key)} (+{stat_of(key)})")
        total = len(inv_items)
        pages = max(1, (total + INV_PAGE_SIZE - 1) // INV_PAGE_SIZE)
        if page >= pages: page = 0
        start = page * INV_PAGE_SIZE
        end = start + INV_PAGE_SIZE
        page_items = inv_items[start:end]

        text = f"⚔️ *СНАРЯЖЕНИЕ* ({total})\n{LINE}"
        m = types.InlineKeyboardMarkup(row_width=1)
        for i, key in enumerate(page_items):
            real_idx = start + i
            tier = item_tier(key)
            m.add(types.InlineKeyboardButton(f"{item_name(key)} (+{stat_of(key)}) [{tier}]", callback_data=f"item_{real_idx}"))
        nav = []
        if pages > 1:
            if page > 0:
                nav.append(types.InlineKeyboardButton("◀️", callback_data=f"inv_cat_gear_{page-1}"))
            nav.append(types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data="ignore"))
            if page < pages - 1:
                nav.append(types.InlineKeyboardButton("▶️", callback_data=f"inv_cat_gear_{page+1}"))
        if nav:
            m.row(*nav)
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="inv"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id)
        return

    total = len(items)
    pages = max(1, (total + INV_PAGE_SIZE - 1) // INV_PAGE_SIZE)
    if page >= pages: page = 0
    start = page * INV_PAGE_SIZE
    end = start + INV_PAGE_SIZE
    page_items = items[start:end]

    cat_names = {
        "ore": "🪨 РУДА", "gem": "💎 САМОЦВЕТЫ", "herb": "🌿 ТРАВЫ",
        "meat": "🥩 МЯСО", "loot": "👹 ЛУТ", "void": "🖤 БЕЗДНА"
    }
    header = cat_names.get(cat, "📦")
    text = f"{header}\n{LINE}\n" + ("\n".join(page_items) if page_items else "_Пусто_")

    m = types.InlineKeyboardMarkup(row_width=3)
    nav = []
    if pages > 1:
        if page > 0:
            nav.append(types.InlineKeyboardButton("◀️", callback_data=f"inv_cat_{cat}_{page-1}"))
        nav.append(types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data="ignore"))
        if page < pages - 1:
            nav.append(types.InlineKeyboardButton("▶️", callback_data=f"inv_cat_{cat}_{page+1}"))
    if nav:
        m.row(*nav)
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="inv"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "ignore")
def ignore_btn(c):
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("item_"))
def item_action(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    idx = int(c.data.split("_")[1])
    inv_items = get_inv(p)
    if idx >= len(inv_items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = inv_items[idx]
    name = item_name(key)
    s = stat_of(key)
    tier = item_tier(key)
    buff_str = ""
    if key in WEAPONS and WEAPONS[key].get("buff"):
        buff_key = WEAPONS[key]["buff"]
        buff_str = f"\n✨ {BUFFS[buff_key]['name']}" if buff_key in BUFFS else ""
    elif key in ARMORS and ARMORS[key].get("buff"):
        buff_key = ARMORS[key]["buff"]
        buff_str = f"\n✨ {BUFFS[buff_key]['name']}" if buff_key in BUFFS else ""
    elif key in ACCESSORIES and ACCESSORIES[key].get("buff"):
        buff_key = ACCESSORIES[key]["buff"]
        buff_str = f"\n✨ {BUFFS[buff_key]['name']}" if buff_key in BUFFS else ""

    text = f"📦 *{name}* [{tier}]\n{LINE}\n📊 Бонус: +{s}{buff_str}\n\nЧто сделать?"
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("✅ Надеть", callback_data=f"equip_{idx}"),
          types.InlineKeyboardButton("💰 Продать", callback_data=f"sell_{idx}"))
    m.add(types.InlineKeyboardButton("🔧 Улучшить (100к)", callback_data=f"upgrade_{idx}"))
    m.add(types.InlineKeyboardButton("🛠 Разобрать", callback_data=f"dis_{idx}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="inv_cat_gear_0"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("equip_"))
def equip_item(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    idx = int(c.data.split("_")[1])
    inv_items = get_inv(p)
    if idx >= len(inv_items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = inv_items[idx]
    t = item_type(key)
    if not t:
        bot.answer_callback_query(c.id, "❌ Нельзя надеть")
        return

    old = p.get(t, "none")
    inv_items.pop(idx)
    if old and old not in ("none", "fists"):
        inv_items.append(old)

    p[t] = key

    if t == "armor":
        old_armor_hp = 0
        if old in ARMORS:
            old_armor_hp = ARMORS[old].get("def", 0) * 3
        new_armor_hp = ARMORS.get(key, {}).get("def", 0) * 3
        p["max_hp"] = p["max_hp"] - old_armor_hp + new_armor_hp
        if p["hp"] > p["max_hp"]:
            p["hp"] = p["max_hp"]
        if p["hp"] < 1:
            p["hp"] = 1

    set_inv(p, inv_items)
    save_player(p)
    bot.answer_callback_query(c.id, "✅ Надето!")
    inv_cat_gear_reload(c)

def inv_cat_gear_reload(c):
    c.data = "inv_cat_gear_0"
    inv_category(c)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sell_"))
def sell_item(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    idx = int(c.data.split("_")[1])
    inv_items = get_inv(p)
    if idx >= len(inv_items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = inv_items.pop(idx)
    price = max(50, stat_of(key) * 20)
    p["silver"] += price
    set_inv(p, inv_items)
    save_player(p)
    bot.answer_callback_query(c.id, f"💰 +{price}")
    inv_cat_gear_reload(c)

@bot.callback_query_handler(func=lambda c: c.data.startswith("dis_"))
def disassemble_item(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    idx = int(c.data.split("_")[1])
    inv_items = get_inv(p)
    if idx >= len(inv_items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    key = inv_items.pop(idx)
    price = max(25, stat_of(key) * 10)
    p["silver"] += price
    set_inv(p, inv_items)
    save_player(p)
    bot.answer_callback_query(c.id, f"🛠 +{price} серебра")
    inv_cat_gear_reload(c)

@bot.callback_query_handler(func=lambda c: c.data.startswith("upgrade_"))
def upgrade_item(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    idx = int(c.data.split("_")[1])
    if p["silver"] < 100000:
        bot.answer_callback_query(c.id, "❌ Нужно 100к"); return
    p["silver"] -= 100000
    inv_items = get_inv(p)
    if idx >= len(inv_items):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    roll = random.randint(1, 100)
    if roll <= 60:
        msg = "✅ Улучшено!"
    else:
        inv_items.pop(idx)
        msg = "💀 Предмет сломан!"
    set_inv(p, inv_items)
    save_player(p)
    bot.answer_callback_query(c.id, msg)
    inv_cat_gear_reload(c)
    
# ============ КРАФТ ============
CRAFT_PAGE_SIZE = 7

@bot.callback_query_handler(func=lambda c: c.data == "craft")
def craft_menu(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
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
        types.InlineKeyboardButton("⚒️ Оружие", callback_data="craftcat_smith_0_all"),
        types.InlineKeyboardButton("🛡 Броня", callback_data="craftcat_armorer_0_all"),
        types.InlineKeyboardButton("💎 Бижутерия", callback_data="craftcat_jeweler_0_all"),
        types.InlineKeyboardButton("⚗️ Зелья", callback_data="craftcat_alchemist_0_all"),
    )
    m.add(types.InlineKeyboardButton("🖤 Бездна", callback_data="craft_void"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("craftcat_"))
def craft_category(c):
    parts = c.data.split("_")
    prof = parts[1]
    page = int(parts[2])
    only_avail = parts[3] if len(parts) > 3 else "all"

    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p)
    if check_dead(c, p):
        return

    recipes = []
    for key, r in RECIPES.items():
        if r["prof"] != prof: continue
        can, _ = can_craft(p, key)
        if only_avail == "avail" and not can:
            continue
        recipes.append((key, r, can))

    total = len(recipes)
    pages = max(1, (total + CRAFT_PAGE_SIZE - 1) // CRAFT_PAGE_SIZE)
    if page >= pages: page = 0
    start = page * CRAFT_PAGE_SIZE
    end = start + CRAFT_PAGE_SIZE
    page_items = recipes[start:end]

    text = f"🔨 *{PROFESSIONS[prof]}* ({total})\n{LINE}"
    if only_avail == "avail":
        text += "\n_(только доступные)_"

    m = types.InlineKeyboardMarkup(row_width=1)
    for key, r, can in page_items:
        mark = "✅" if can else "🔒"
        tier = WEAPON_TIER.get(key) or ARMOR_TIER.get(key) or ACCESSORY_TIER.get(key) or POTION_TIER.get(key, "E")
        m.add(types.InlineKeyboardButton(f"{mark} {r['name']} (ур.{r['level']}) [{tier}]", callback_data=f"recipe_{key}"))

    filter_btn = "🔓 Показать все" if only_avail == "avail" else "🔒 Только доступные"
    next_filter = "all" if only_avail == "avail" else "avail"
    m.add(types.InlineKeyboardButton(filter_btn, callback_data=f"craftcat_{prof}_0_{next_filter}"))

    nav = []
    if pages > 1:
        if page > 0:
            nav.append(types.InlineKeyboardButton("◀️", callback_data=f"craftcat_{prof}_{page-1}_{only_avail}"))
        nav.append(types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data="ignore"))
        if page < pages - 1:
            nav.append(types.InlineKeyboardButton("▶️", callback_data=f"craftcat_{prof}_{page+1}_{only_avail}"))
    if nav:
        m.row(*nav)

    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("recipe_"))
def recipe_view(c):
    key = c.data.replace("recipe_", "")
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
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
    tier = WEAPON_TIER.get(key) or ARMOR_TIER.get(key) or ACCESSORY_TIER.get(key) or POTION_TIER.get(key, "E")

    buff_str = ""
    if key in WEAPONS and WEAPONS[key].get("buff"):
        buff_key = WEAPONS[key]["buff"]
        buff_str = f"\n✨ Эффект: {BUFFS[buff_key]['name']}" if buff_key in BUFFS else ""
    elif key in ARMORS and ARMORS[key].get("buff"):
        buff_key = ARMORS[key]["buff"]
        buff_str = f"\n✨ Эффект: {BUFFS[buff_key]['name']}" if buff_key in BUFFS else ""
    elif key in ACCESSORIES and ACCESSORIES[key].get("buff"):
        buff_key = ACCESSORIES[key]["buff"]
        buff_str = f"\n✨ Эффект: {BUFFS[buff_key]['name']}" if buff_key in BUFFS else ""

    lines = [f"🔨 *{r['name']}* [{tier}]", LINE,
             f"Профессия: {PROFESSIONS[prof]}",
             f"Уровень: {r['level']} (у тебя {p[f'prof_{prof}']}){buff_str}", ""]
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
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"craftcat_{prof}_0_all"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("make_"))
def make_item(c):
    key = c.data.replace("make_", "")
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
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
            c.data = f"craftcat_{r['prof']}_0_all"
        craft_category(c)

@bot.callback_query_handler(func=lambda c: c.data == "craft_void")
def craft_void_menu(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p)
    if check_dead(c, p):
        return
    if p["prof_smith"] < 100 and p["prof_armorer"] < 100 and p["prof_jeweler"] < 100:
        bot.answer_callback_query(c.id, "❌ Нужен 100 уровень профессии")
        return
    text = f"🖤 *БЕЗДНА*\n{LINE}\nВыбери предмет:"
    m = types.InlineKeyboardMarkup(row_width=1)
    for key in RECIPES_VOID.keys():
        name = WEAPONS.get(key, {}).get("name") or ARMORS.get(key, {}).get("name") or ACCESSORIES.get(key, {}).get("name", key)
        m.add(types.InlineKeyboardButton(name, callback_data=f"recipe_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# ============ СПРАВОЧНИК ============
@bot.callback_query_handler(func=lambda c: c.data == "handbook")
def handbook_menu(c):
    text = f"📖 *СПРАВОЧНИК*\n{LINE}\nВыбери раздел:"
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("⚔️ Оружие", callback_data="hb_weapons_0"),
        types.InlineKeyboardButton("🛡 Броня", callback_data="hb_armors_0"),
        types.InlineKeyboardButton("💍 Бижутерия", callback_data="hb_accessories_0"),
        types.InlineKeyboardButton("⚗️ Зелья", callback_data="hb_potions_0"),
        types.InlineKeyboardButton("🪨 Руда", callback_data="hb_ores_0"),
        types.InlineKeyboardButton("💎 Самоцветы", callback_data="hb_gems_0"),
        types.InlineKeyboardButton("🌿 Травы", callback_data="hb_herbs_0"),
        types.InlineKeyboardButton("👹 Лут", callback_data="hb_loot_0"),
        types.InlineKeyboardButton("🎁 Сундуки", callback_data="hb_chests_0"),
    )
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("hb_"))
def handbook_show(c):
    parts = c.data.split("_")
    cat = parts[1]
    page = int(parts[2])

    items = []

    if cat == "weapons":
        for k, v in WEAPONS.items():
            if k == "fists": continue
            buff = ""
            if v.get("buff") and v["buff"] in BUFFS:
                buff = f" | {BUFFS[v['buff']]['name']}"
            items.append(f"{v['name']} [{v['tier']}]\n  ⚔️ {v['dmg']} • ур.{v['level']}{buff}")
    elif cat == "armors":
        for k, v in ARMORS.items():
            items.append(f"{v['name']} [{v['tier']}]\n  🛡 {v['def']} • ур.{v['level']}")
    elif cat == "accessories":
        for k, v in ACCESSORIES.items():
            buff = ""
            if v.get("buff") and v["buff"] in BUFFS:
                buff = f" | {BUFFS[v['buff']]['name']}"
            items.append(f"{v['name']} [{v['tier']}]\n  💍 {v['bonus']} • ур.{v['level']}{buff}")
    elif cat == "potions":
        for k, v in POTIONS.items():
            items.append(f"{v['name']} [{v['tier']}]\n  ур.{v['level']}")
    elif cat == "ores":
        for k, v in ORES.items():
            items.append(f"{v['name']} [{v['tier']}] — {v['price']:,}💰")
    elif cat == "gems":
        for k, v in GEMS.items():
            items.append(f"{v['name']} [{v['tier']}] — {v['price']:,}💰")
    elif cat == "herbs":
        for k, v in HERBS.items():
            items.append(f"{v['name']} [{v['tier']}] — {v['price']:,}💰")
    elif cat == "loot":
        for k, v in MOB_LOOT.items():
            items.append(f"{v['name']} [{v['tier']}] — {v['price']:,}💰")
    elif cat == "chests":
        for k, v in CHEST_TYPES.items():
            items.append(
                f"{v['name']} [{v['tier']}]\n"
                f"  🎁 секрет: {v['secret_chance']}%\n"
                f"  🐾 питомец: {v['pet_chance']}%\n"
                f"  💰 {v['silver']:,} серебра"
            )

    total = len(items)
    pages = max(1, (total + INV_PAGE_SIZE - 1) // INV_PAGE_SIZE)
    if page >= pages: page = 0
    start = page * INV_PAGE_SIZE
    end = start + INV_PAGE_SIZE
    page_items = items[start:end]

    titles = {
        "weapons": "⚔️ ОРУЖИЕ", "armors": "🛡 БРОНЯ", "accessories": "💍 БИЖУТЕРИЯ",
        "potions": "⚗️ ЗЕЛЬЯ", "ores": "🪨 РУДА", "gems": "💎 САМОЦВЕТЫ",
        "herbs": "🌿 ТРАВЫ", "loot": "👹 ЛУТ", "chests": "🎁 СУНДУКИ"
    }
    header = titles.get(cat, "📖")
    text = f"{header} ({total})\n{LINE}\n" + ("\n\n".join(page_items) if page_items else "_Пусто_")

    m = types.InlineKeyboardMarkup(row_width=3)
    nav = []
    if pages > 1:
        if page > 0:
            nav.append(types.InlineKeyboardButton("◀️", callback_data=f"hb_{cat}_{page-1}"))
        nav.append(types.InlineKeyboardButton(f"{page+1}/{pages}", callback_data="ignore"))
        if page < pages - 1:
            nav.append(types.InlineKeyboardButton("▶️", callback_data=f"hb_{cat}_{page+1}"))
    if nav:
        m.row(*nav)
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="handbook"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# ============ СУНДУКИ ============
@bot.callback_query_handler(func=lambda c: c.data == "inv_chests")
def inv_chests(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    cc = p.get("chest_common", 0) or 0
    cr = p.get("chest_rare", 0) or 0
    cl = p.get("chest_legend", 0) or 0
    text = (
        f"📦 *СУНДУКИ*\n{LINE}\n"
        f"🎁 Обычные: {cc}\n"
        f"💎 Редкие: {cr}\n"
        f"👑 Легендарные: {cl}\n\n"
        f"Открой сундук, чтобы получить награды:"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    if cc > 0:
        m.add(types.InlineKeyboardButton(f"🎁 Открыть обычный ({cc})", callback_data="open_chest_common"))
    if cr > 0:
        m.add(types.InlineKeyboardButton(f"💎 Открыть редкий ({cr})", callback_data="open_chest_rare"))
    if cl > 0:
        m.add(types.InlineKeyboardButton(f"👑 Открыть легендарный ({cl})", callback_data="open_chest_legend"))
    if cc == 0 and cr == 0 and cl == 0:
        m.add(types.InlineKeyboardButton("❌ Нет сундуков", callback_data="ignore"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="inv"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("open_chest_"))
def open_chest(c):
    chest_type = c.data.replace("open_chest_", "")
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return

    field = f"chest_{chest_type}"
    if p.get(field, 0) <= 0:
        bot.answer_callback_query(c.id, "❌ Нет такого сундука")
        return

    p[field] -= 1
    cfg = CHEST_TYPES[chest_type]
    result_lines = [f"📦 *{cfg['name']}*\n{LINE}\n"]
    got_something = False

    if random.randint(1, 100) <= cfg["secret_chance"]:
        secret_key = random.choice(SECRET_ITEMS)
        inv = get_inv(p)
        inv.append(secret_key)
        set_inv(p, inv)
        name = item_name(secret_key)
        result_lines.append(f"🎁 СЕКРЕТНЫЙ: *{name}*!")
        got_something = True

    if random.randint(1, 100) <= cfg["pet_chance"]:
        pet_key = random.choice(PET_POOL)
        pets = get_pets(p)
        pets.append({"key": pet_key, "level": 1, "satiety": 0, "evolved": False})
        set_pets(p, pets)
        pt = PET_TYPES.get(pet_key, {})
        result_lines.append(f"🐾 ПИТОМЕЦ: *{pt.get('name', pet_key)}*!")
        got_something = True

    res_cfg = CHEST_RESOURCES[chest_type]
    ore_key = random.choice(res_cfg["ore"])
    ore_amt = random.randint(res_cfg["count_min"], res_cfg["count_max"])
    p[ore_key] = (p.get(ore_key, 0) or 0) + ore_amt
    result_lines.append(f"🪨 {ORES[ore_key]['name']} ×{ore_amt}")

    meat_amt = res_cfg["meat"]
    p["raw_meat"] = (p.get("raw_meat", 0) or 0) + meat_amt
    result_lines.append(f"🥩 Сырое мясо ×{meat_amt}")

    shard_amt = res_cfg["void_shard"]
    p["void_shard"] = (p.get("void_shard", 0) or 0) + shard_amt
    result_lines.append(f"💠 Осколок бездны ×{shard_amt}")

    silver_amt = cfg["silver"]
    p["silver"] += silver_amt
    result_lines.append(f"💰 Серебро +{silver_amt:,}")

    save_player(p)
    text = "\n".join(result_lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("📦 Ещё сундуки", callback_data="inv_chests"))
    m.add(types.InlineKeyboardButton("🔙 Инвентарь", callback_data="inv"))
    bot.answer_callback_query(c.id, "📦 Открыто!")
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except:
        bot.send_message(c.message.chat.id, text, reply_markup=m, parse_mode="Markdown")

# ============ ПИТОМЦЫ ============
@bot.callback_query_handler(func=lambda c: c.data == "pets")
def pets_menu(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p); save_player(p)
    if check_dead(c, p):
        return
    pets = get_pets(p)
    if not pets:
        text = "🐾 *ПИТОМЦЫ*\n\nУ тебя нет питомца.\nОткрывай яйца с боссов."
    else:
        lines = ["🐾 *ПИТОМЦЫ*", LINE, ""]
        for pet in pets:
            key = pet.get("key", "")
            lvl = pet.get("level", 1)
            sat = pet.get("satiety", 0)
            evolved = pet.get("evolved", False)
            pt = PET_TYPES.get(key, {})
            if evolved:
                name = pt.get("evo", key)
                dmg = pt.get("evo_dmg", 0)
            else:
                name = pt.get("name", key)
                dmg = pt.get("dmg", 0)
            lines.append(f"{name}")
            lines.append(f"  Ур: {lvl} | Сытость: {sat}/{SATIETY_PER_LEVEL}")
            lines.append(f"  +{dmg} dmg")
            lines.append("")
        text = "\n".join(lines)
    m = types.InlineKeyboardMarkup(row_width=1)
    m.add(types.InlineKeyboardButton("🎁 Открыть яйцо (50 💠)", callback_data="pet_hatch"))
    if pets:
        m.add(types.InlineKeyboardButton("🍖 Кормить", callback_data="pet_feed_menu"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "pet_hatch")
def pet_hatch(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    if check_dead(c, p):
        return
    if p.get("void_shard", 0) < 50:
        bot.answer_callback_query(c.id, "❌ Нужно 50 осколков"); return
    p["void_shard"] -= 50
    pet_key = random.choice(list(PET_TYPES.keys()))
    pets = get_pets(p)
    pets.append({
        "key": pet_key,
        "level": 1,
        "satiety": 0,
        "evolved": False,
    })
    set_pets(p, pets)
    save_player(p)
    pt = PET_TYPES[pet_key]
    bot.answer_callback_query(c.id, f"🎉 Ты получил {pt['name']}!")
    pets_menu(c)

@bot.callback_query_handler(func=lambda c: c.data == "pet_feed_menu")
def pet_feed_menu(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    pets = get_pets(p)
    if not pets:
        bot.answer_callback_query(c.id, "❌ Нет питомцев")
        return
    text = (
        f"🍖 *КОРМЛЕНИЕ ПИТОМЦА*\n{LINE}\n"
        f"🌿 Трава: +{FEED_HERB} сытости\n"
        f"🥩 Мясо: +{FEED_MEAT} сытости\n"
        f"📊 {SATIETY_PER_LEVEL} сытости = 1 уровень\n"
        f"⭐ {EVO_LEVEL} ур. = эволюция!\n\n"
        f"У тебя: 🌿{sum(p.get(h,0) for h in HERBS.keys())} трав, 🥩{p.get('raw_meat',0)} мяса\n\n"
        f"Выбери питомца:"
    )
    m = types.InlineKeyboardMarkup(row_width=1)
    for i, pet in enumerate(pets):
        key = pet.get("key", "")
        pt = PET_TYPES.get(key, {})
        name = pt.get("evo") if pet.get("evolved") else pt.get("name", key)
        m.add(types.InlineKeyboardButton(f"{name} (ур.{pet.get('level',1)})", callback_data=f"pet_choose_{i}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="pets"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pet_choose_"))
def pet_choose(c):
    idx = int(c.data.split("_")[2])
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    pets = get_pets(p)
    if idx >= len(pets):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    pet = pets[idx]
    key = pet.get("key", "")
    pt = PET_TYPES.get(key, {})
    name = pt.get("evo") if pet.get("evolved") else pt.get("name", key)
    text = (
        f"🍖 *{name}*\n{LINE}\n"
        f"Ур: {pet.get('level',1)} | Сытость: {pet.get('satiety',0)}/{SATIETY_PER_LEVEL}\n\n"
        f"Кормить:"
    )
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(types.InlineKeyboardButton("🌿 Трава (+10)", callback_data=f"pet_feed_h_{idx}"),
          types.InlineKeyboardButton("🥩 Мясо (+30)", callback_data=f"pet_feed_m_{idx}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="pet_feed_menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pet_feed_h_") or c.data.startswith("pet_feed_m_"))
def pet_feed(c):
    is_herb = "_h_" in c.data
    idx = int(c.data.split("_")[-1])
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    pets = get_pets(p)
    if idx >= len(pets):
        bot.answer_callback_query(c.id, "❌ Не найден"); return
    pet = pets[idx]

    if is_herb:
        available_herb = None
        for h in HERBS.keys():
            if p.get(h, 0) > 0:
                available_herb = h
                break
        if not available_herb:
            bot.answer_callback_query(c.id, "❌ Нет травы"); return
        p[available_herb] -= 1
        gain = FEED_HERB
    else:
        if p.get("raw_meat", 0) < 1:
            bot.answer_callback_query(c.id, "❌ Нет мяса"); return
        p["raw_meat"] -= 1
        gain = FEED_MEAT

    pet["satiety"] = pet.get("satiety", 0) + gain
    msg = f"🍖 +{gain} сытости"

    while pet["satiety"] >= SATIETY_PER_LEVEL and pet.get("level", 1) < EVO_LEVEL:
        pet["satiety"] -= SATIETY_PER_LEVEL
        pet["level"] = pet.get("level", 1) + 1
        msg += f"\n⭐ Уровень {pet['level']}!"

    if pet.get("level", 1) >= EVO_LEVEL and not pet.get("evolved", False):
        pet["evolved"] = True
        pt = PET_TYPES.get(pet.get("key", ""), {})
        msg += f"\n🎉 ЭВОЛЮЦИЯ! Теперь это {pt.get('evo', '???')}!"

    set_pets(p, pets)
    save_player(p)
    bot.answer_callback_query(c.id, msg[:200])
    pet_choose(c)

# ============ КЛАНЫ ============
@bot.callback_query_handler(func=lambda c: c.data == "clan_boss")
def clan_boss_menu(c):
    global clan_boss
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p); save_player(p)
    update_event_flag()
    if check_dead(c, p):
        return

    if not p.get("clan"):
        text = (
            f"🐉 *КЛАНОВЫЙ БОСС*\n{LINE}\n"
            f"⛔ У тебя нет клана!\n\n"
            f"Чтобы сразиться с клановым боссом,\n"
            f"сначала создай клан.\n\n"
            f"💰 Стоимость: 100 000 серебра\n"
            f"💼 У тебя: {p['silver']:,}"
        )
        m = types.InlineKeyboardMarkup(row_width=1)
        if p["silver"] >= 100000:
            m.add(types.InlineKeyboardButton("🏰 Создать клан (100к)", callback_data="clan_create"))
        else:
            m.add(types.InlineKeyboardButton("❌ Не хватает серебра", callback_data="clan_need_money"))
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
        bot.answer_callback_query(c.id)
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
        f"🛡 Клан: {safe_name(p['clan'])}\n\n"
        f"❤️ HP: {clan_boss['hp']:,}/{clan_boss['max_hp']:,}\n"
        f"⚔️ Урон: 500\n"
        f"🎯 Ловкость: 15%\n\n"
        f"Награда: 🎁 сундук (5% шанс)\n"
        f"Возрождение: 5 мин"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать (10⚡)", callback_data="clan_boss_hit"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "clan_need_money")
def clan_need_money(c):
    bot.answer_callback_query(c.id, "❌ Нужно 100 000 серебра")

@bot.callback_query_handler(func=lambda c: c.data == "clan_create")
def clan_create(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    if check_dead(c, p):
        return
    if p.get("clan"):
        bot.answer_callback_query(c.id, "❌ У тебя уже есть клан!")
        return
    if p["silver"] < 100000:
        bot.answer_callback_query(c.id, "❌ Нужно 100к"); return
    p["silver"] -= 100000
    clan_name = f"Клан_{p['name']}"
    p["clan"] = clan_name
    save_player(p)
    bot.answer_callback_query(c.id, f"✅ Клан {clan_name} создан!")
    clan_boss_menu(c)

@bot.callback_query_handler(func=lambda c: c.data == "clan_boss_hit")
def clan_boss_hit(c):
    global clan_boss
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    if not p.get("clan"):
        bot.answer_callback_query(c.id, "❌ У тебя нет клана!")
        return
    regen_energy(p)
    update_event_flag()
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
        p["hp"] -= 500
        if p["hp"] <= 0:
            p["hp"] = 0
            p["death_time"] = time.time()
            save_player(p)
            bot.answer_callback_query(c.id, "💀 Ты умер!")
            return
    save_player(p)

    clan_msg = ""
    if clan_boss["hp"] <= 0:
        clan_boss["last_death"] = time.time()
        if random.randint(1, 100) <= 5:
            p["chest_common"] = (p.get("chest_common", 0) or 0) + 1
            clan_msg = "\n🎁 Выпал ОБЫЧНЫЙ СУНДУК!"
        for _ in range(10):
            ore = random.choice(list(ORES.keys()))
            p[ore] = (p.get(ore, 0) or 0) + 1
        if random.randint(1, 100) <= 50:
            p["void_shard"] = (p.get("void_shard", 0) or 0) + 1
        save_player(p)
        bot.send_message(c.message.chat.id, f"🎉 Клановый босс побеждён! Награда получена!{clan_msg}")

    bot.answer_callback_query(c.id, f"⚔️ {dmg} урона!")
    clan_boss_menu(c)

# ============ РУЛЕТКА ============
@bot.callback_query_handler(func=lambda c: c.data == "roulette")
def roulette_menu(c):
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
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
    if require_name(c, p):
        return
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

# ============ ТОПЫ ============
@bot.callback_query_handler(func=lambda c: c.data == "top_menu")
def top_menu(c):
    text = f"🏆 *ТОПЫ*\n{LINE}\nВыбери категорию:"
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("💰 По серебру", callback_data="top_silver"),
        types.InlineKeyboardButton("⚔️ По убийствам", callback_data="top_kills"),
        types.InlineKeyboardButton("👑 По боссам", callback_data="top_bosses"),
        types.InlineKeyboardButton("⚒️ Кузнецы", callback_data="top_smith"),
        types.InlineKeyboardButton("🛡 Бронники", callback_data="top_armorer"),
        types.InlineKeyboardButton("💎 Ювелиры", callback_data="top_jeweler"),
        types.InlineKeyboardButton("⚗️ Алхимики", callback_data="top_alchemist"),
        types.InlineKeyboardButton("⛏ Шахтёры", callback_data="top_miner"),
    )
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

TOP_QUERIES = {
    "top_silver":   ("💰 ТОП-10 ПО СЕРЕБРУ",   "silver", "DESC"),
    "top_kills":    ("⚔️ ТОП-10 ПО УБИЙСТВАМ", "kills", "DESC"),
    "top_bosses":   ("👑 ТОП-10 ПО БОССАМ",    "boss_kills", "DESC"),
    "top_smith":    ("⚒️ ТОП-10 КУЗНЕЦОВ",     "prof_smith", "DESC"),
    "top_armorer":  ("🛡 ТОП-10 БРОННИКОВ",    "prof_armorer", "DESC"),
    "top_jeweler":  ("💎 ТОП-10 ЮВЕЛИРОВ",     "prof_jeweler", "DESC"),
    "top_alchemist":("⚗️ ТОП-10 АЛХИМИКОВ",    "prof_alchemist", "DESC"),
    "top_miner":    ("⛏ ТОП-10 ШАХТЁРОВ",      "prof_miner", "DESC"),
}

@bot.callback_query_handler(func=lambda c: c.data.startswith("top_") and c.data in TOP_QUERIES)
def top_show(c):
    title, field, order = TOP_QUERIES[c.data]
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT name, {field} FROM players WHERE name IS NOT NULL AND name != 'Игрок' AND name !~ '^[0-9]+$' ORDER BY {field} {order} LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        lines = [f"🏆 *{title}*", LINE, ""]
        if not rows:
            lines.append("_Пока никого нет_")
        else:
            for i, (name, val) in enumerate(rows, 1):
                lines.append(f"{i}. {safe_name(name)} — {val:,}")
        text = "\n".join(lines)
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="top_menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
        except: pass
    except Exception as e:
        bot.answer_callback_query(c.id, f"❌ Ошибка: {str(e)[:50]}")
        return
    bot.answer_callback_query(c.id)

# ============ МИРОВОЙ БОСС ============
@bot.callback_query_handler(func=lambda c: c.data == "world_boss")
def world_boss_menu(c):
    global world_boss
    p = get_player(c.from_user.id)
    if require_name(c, p):
        return
    regen_energy(p); save_player(p)
    update_event_flag()
    if check_dead(c, p):
        return
    now = time.time()
    if world_boss["hp"] <= 0:
        if now - world_boss["last_spawn"] < 10800:
            remaining = int((10800 - (now - world_boss["last_spawn"])) / 60)
            bot.answer_callback_query(c.id, f"⏱ Возрождение через ~{remaining} мин")
            return
        else:
            world_boss["hp"] = world_boss["max_hp"]
            world_boss["damage"] = {}
    text = (
        f"🌍 *МИРОВОЙ БОСС*\n{LINE}\n"
        f"❤️ HP: {world_boss['hp']:,}/{world_boss['max_hp']:,}\n"
        f"⚔️ Урон: 750\n\n"
        f"За удар: 📈 +50 опыта, 1% шанс на секретный предмет\n\n"
        f"Возрождение: каждые 3 часа"
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
    if require_name(c, p):
        return
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
        secret_key = random.choice(SECRET_ITEMS)
        inv = get_inv(p)
        inv.append(secret_key)
        set_inv(p, inv)
        name = item_name(secret_key)
        secret_msg = f"\n🎁 СЕКРЕТНЫЙ ДРОП: {name}!"

    if random.randint(1, 100) <= 20:
        p["hp"] -= 750
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
        p["silver"] += 50000
        p["void_shard"] = (p.get("void_shard", 0) or 0) + 5
        if random.randint(1, 100) <= 10:
            p["void_heart"] = (p.get("void_heart", 0) or 0) + 1
        chest_msg = ""
        if random.randint(1, 100) <= 3:
            p["chest_rare"] = (p.get("chest_rare", 0) or 0) + 1
            chest_msg = "\n💎 РЕДКИЙ СУНДУК выпал!"
        save_player(p)
        bot.send_message(c.message.chat.id, f"🎉 МИРОВОЙ БОСС ПОБЕЖДЁН! +50к серебра, +5 💠!{chest_msg}")

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
        lines.append(f"{i}. {safe_name(p['name'])} — {dmg:,}")
    text = "\n".join(lines)
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="world_boss"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=m, parse_mode="Markdown")
    except: pass
    bot.answer_callback_query(c.id)

# ============ АВТО-СОБЫТИЯ ============
def event_scheduler():
    while True:
        try:
            update_event_flag()
        except: pass
        time.sleep(60)

# ============ ФИНАЛ ============
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=event_scheduler, daemon=True).start()
    print("RPG бот запущен...")
    bot.infinity_polling()
