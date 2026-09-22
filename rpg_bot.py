import telebot
from telebot import types
import threading, time, os, random
from flask import Flask
from data import *
from db import init_db, get_player, save_player, exp_needed
from battle import calc_player_stats, make_mob, player_turn, mob_turn, roll_herb, roll_ore, battle_text
from craft import can_craft, do_craft

TOKEN = "8620344298:AAHr_PhXczz08rhQHgd_DpQt13rwIA2XPgA"
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

def fmt(n):
    if n is None:
        return "—"
    if n >= 1e9:
        return f"{n/1e9:.3f} млрд"
    if n >= 1e6:
        return f"{n/1e6:.3f} млн"
    if n >= 1e3:
        return f"{n/1e3:.3f}к"
    return str(n)

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
        f"🏰 Этаж: {p['floor']}/10\n"
        f"🐾 Мобов: {p['mob_kill']}/100\n"
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
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "profile")
def profile(c):
    p = get_player(c.from_user.id)
    w = WEAPONS[p["weapon"]]
    a = ARMORS[p["armor"]]
    acc = ACCESSORIES[p["accessory"]]
    text = (
        f"👤 *ПРОФИЛЬ*\n{LINE}\n"
        f"⭐ Ур: {p['level']} ({p['exp']}/{exp_needed(p['level'])})\n"
        f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
        f"💰 Серебро: {p['silver']:,}\n"
        f"🏰 Этаж: {p['floor']}/10\n"
        f"🐾 Убито мобов: {p['mob_kill']}\n"
        f"👹 Всего убийств: {p['kills']}\n"
        f"🏆 Боссов: {p['boss_kills']}\n\n"
        f"🗡 {w['name']} (+{w['dmg']} dmg)\n"
        f"🛡 {a['name']} (+{a['def']} def)\n"
        f"💍 {acc['name']} (+{acc['bonus']} bonus)\n\n"
        f"⚒️ Кузнец: ур.{p['prof_smith']} ({p['exp_smith']})\n"
        f"🛡 Бронник: ур.{p['prof_armorer']} ({p['exp_armorer']})\n"
        f"💍 Ювелир: ур.{p['prof_jeweler']} ({p['exp_jeweler']})\n"
        f"⚗️ Алхимик: ур.{p['prof_alchemist']} ({p['exp_alchemist']})"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
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
        f"⚔️ Урон: {dmg}\n"
        f"🛡 Защита: {defense}\n"
        f"💥 Крит: {crit}%\n\n"
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
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("up_"))
def upgrade(c):
    p = get_player(c.from_user.id)
    if p["stat_points"] <= 0:
        bot.answer_callback_query(c.id, "❌ Нет очков")
        return
    s = c.data.split("_")[1]
    if s == "str":
        p["strength"] += 1
    elif s == "agi":
        p["agility"] += 1
    elif s == "vit":
        p["vitality"] += 1
        p["max_hp"] += 10
        p["hp"] += 10
    p["stat_points"] -= 1
    save_player(p)
    bot.answer_callback_query(c.id, "✅ Улучшено!")
    stats(c)

@bot.callback_query_handler(func=lambda c: c.data == "tower")
def tower(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    save_player(p)
    if p["floor"] > 10:
        text = "🏰 *БАШНЯ ПРОЙДЕНА!*\n\n👑 Все 10 этажей покорены!"
    else:
        text = (
            f"🏰 *ЭТАЖ {p['floor']}*\n{LINE}\n"
            f"🐾 Мобов: {p['mob_kill']}/100\n"
            f"🔑 Ключей: {p['keys']}\n"
            f"❤️ HP: {p['hp']}/{p['max_hp']}\n"
            f"⚡ Энергия: {p['energy']}/{p['max_energy']}"
        )
    m = types.InlineKeyboardMarkup()
    if p["energy"] >= 5 and p["floor"] <= 10:
        m.add(types.InlineKeyboardButton("⚔️ В бой (5⚡)", callback_data="fight_start"))
    if p["keys"] > 0 and p["floor"] <= 10:
        m.add(types.InlineKeyboardButton(f"🔑 Использовать ключ ({p['keys']})", callback_data="use_key"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight_start")
def fight_start(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    if p["energy"] < 5:
        bot.answer_callback_query(c.id, "❌ Нет энергии")
        return
    p["energy"] -= 5
    is_boss = p["mob_kill"] >= 99
    mob = make_mob(p["floor"], is_boss)
    battles[c.from_user.id] = {"mob": mob}
    save_player(p)
    text = (
        f"⚔️ *БОЙ НАЧАЛСЯ!*\n{LINE}\n"
        f"{mob['name']}\n"
        f"❤️ HP: {mob['hp']}/{mob['max_hp']}\n"
        f"⚔️ Урон: {mob['dmg']}\n\n"
        f"❤️ Твой HP: {p['hp']}/{p['max_hp']}"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать", callback_data="fight_turn"))
    m.add(types.InlineKeyboardButton("🏳️ Сбежать", callback_data="fight_run"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight_turn")
def fight_turn(c):
    uid = c.from_user.id
    if uid not in battles:
        bot.answer_callback_query(c.id, "❌ Бой не найден")
        return
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
        if mob.get("boss"):
            p["boss_kills"] += 1
        herb = roll_herb()
        p[herb] += 1
        key_drop = random.randint(1, 100) <= 3
        if key_drop:
            p["keys"] += 1
        if p["mob_kill"] >= 100:
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
            f"🌿 +1 {HERBS[herb]['name']}"
        )
        if key_drop:
            text += "\n🔑 *Ключ выпал!*"
        if lvl_up:
            text += f"\n\n⭐ *УРОВЕНЬ {p['level']}!* +3 очка"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
              types.InlineKeyboardButton("🔙 Меню", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                                  reply_markup=m, parse_mode="Markdown")
        except:
            pass
        bot.answer_callback_query(c.id)
        return
    if p["hp"] <= 0:
        p["hp"] = p["max_hp"]
        save_player(p)
        del battles[uid]
        text = "💀 *ПОРАЖЕНИЕ*\n\n❤️ HP восстановлен"
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("🏰 Башня", callback_data="tower"),
              types.InlineKeyboardButton("🔙 Меню", callback_data="menu"))
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                                  reply_markup=m, parse_mode="Markdown")
        except:
            pass
        bot.answer_callback_query(c.id)
        return
    save_player(p)
    text = (
        f"⚔️ *БОЙ*\n{LINE}\n{log}\n{LINE}\n"
        f"❤️ Твой HP: {p['hp']}/{p['max_hp']}\n"
        f"⚡ Энергия: {p['energy']}"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⚔️ Атаковать", callback_data="fight_turn"))
    m.add(types.InlineKeyboardButton("🏳️ Сбежать", callback_data="fight_run"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "fight_run")
def fight_run(c):
    uid = c.from_user.id
    if uid in battles:
        del battles[uid]
    bot.answer_callback_query(c.id, "🏳️ Сбежал!")
    tower(c)

@bot.callback_query_handler(func=lambda c: c.data == "use_key")
def use_key(c):
    p = get_player(c.from_user.id)
    if p["keys"] <= 0:
        bot.answer_callback_query(c.id, "❌ Нет ключей")
        return
    p["keys"] -= 1
    p["floor"] += 1
    p["mob_kill"] = 0
    save_player(p)
    bot.answer_callback_query(c.id, f"🔑 Этаж {p['floor']} открыт!")
    tower(c)

@bot.callback_query_handler(func=lambda c: c.data == "mine")
def mine(c):
    p = get_player(c.from_user.id)
    regen_energy(p)
    save_player(p)
    text = (
        f"⛏ *ШАХТА*\n{LINE}\n"
        f"⚡ Энергия: {p['energy']}/{p['max_energy']}\n"
        f"⛏ Добыто: {p['mine_count']}\n\n"
        f"Стоимость: 2⚡"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Копать (2⚡)", callback_data="dig"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "dig")
def dig(c):
    p = get_player(c.from_user.id)
    if p["energy"] < 2:
        bot.answer_callback_query(c.id, "❌ Нет энергии")
        return
    p["energy"] -= 2
    ore, amt = roll_ore()
    p[ore] += amt
    p["mine_count"] += 1
    save_player(p)
    text = f"⛏ *ДОБЫЧА*\n\n{ORES[ore]['name']} × {amt}\n\n⚡ Осталось: {p['energy']}"
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("⛏ Ещё", callback_data="dig"),
          types.InlineKeyboardButton("🔙 Шахта", callback_data="mine"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "inv")
def inv(c):
    p = get_player(c.from_user.id)
    text = (
        f"🎒 *ИНВЕНТАРЬ*\n{LINE}\n"
        f"🟠 Медь: {p['copper']}\n⚙️ Железо: {p['iron']}\n"
        f"🟡 Золото: {p['gold']}\n💠 Мифрил: {p['mithril']}\n"
        f"💎 Самоцветы: {p['gem']}\n\n"
        f"🌿 Штормовой келп: {p['storm_kelp']}\n"
        f"🪨 Кристалл соли: {p['salt_crystal']}\n"
        f"⚡ Громовая жемчужина: {p['thunder_pearl']}\n"
        f"🔥 Огнецвет: {p['fire_flower']}"
    )
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "craft")
def craft_menu(c):
    p = get_player(c.from_user.id)
    text = (
        f"🔨 *КРАФТ*\n{LINE}\n"
        f"⚒️ Кузнец: ур.{p['prof_smith']}\n"
        f"🛡 Бронник: ур.{p['prof_armorer']}\n"
        f"💍 Ювелир: ур.{p['prof_jeweler']}\n"
        f"⚗️ Алхимик: ур.{p['prof_alchemist']}\n\n"
        f"Выбери категорию:"
    )
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton("⚒️ Оружие", callback_data="craft_smith"),
        types.InlineKeyboardButton("🛡 Броня", callback_data="craft_armorer"),
        types.InlineKeyboardButton("💍 Бижутерия", callback_data="craft_jeweler"),
        types.InlineKeyboardButton("⚗️ Зелья", callback_data="craft_alchemist"),
    )
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="menu"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("craft_") and c.data.count("_") == 1)
def craft_category(c):
    prof = c.data.replace("craft_", "")
    p = get_player(c.from_user.id)
    text = f"🔨 *{PROFESSIONS[prof]}*\n{LINE}\nВыбери рецепт:"
    m = types.InlineKeyboardMarkup(row_width=1)
    for key, r in RECIPES.items():
        if r["prof"] != prof:
            continue
        can, _ = can_craft(p, key)
        mark = "✅" if can else "🔒"
        m.add(types.InlineKeyboardButton(f"{mark} {r['name']}", callback_data=f"make_{key}"))
    m.add(types.InlineKeyboardButton("🔙 Назад", callback_data="craft"))
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                              reply_markup=m, parse_mode="Markdown")
    except:
        pass
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("make_"))
def make_item(c):
    key = c.data.replace("make_", "")
    p = get_player(c.from_user.id)
    ok, msg = do_craft(p, key)
    if ok:
        if key in WEAPONS:
            p["weapon"] = key
        elif key in ARMORS:
            p["armor"] = key
        elif key in ACCESSORIES:
            p["accessory"] = key
    save_player(p)
    bot.answer_callback_query(c.id, msg)
    craft_category(c)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    print("RPG бот запущен...")
    bot.infinity_polling()
