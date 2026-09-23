import random
import time
from data import (
    WEAPONS, ARMORS, ACCESSORIES, MOB_NAMES, MYSTIC_NAMES, BOSS_NAMES,
    HERBS, ORES, GEMS, MOB_LOOT, MINER_BONUS, BUFFS,
    ORE_TIER, GEM_TIER, ORE_EXP, GEM_EXP,
    roll_amount, ore_chances, gem_chances, pick_weighted,
)

DEATH_TIME = 60

# Кровавая луна (глобальный флаг, ставится из rpg_bot.py)
BLOOD_MOON = False

def get_buff_value(p, buff_key, stat):
    total = 0
    for slot in ("weapon", "armor", "accessory"):
        key = p.get(slot, "none")
        item = WEAPONS.get(key) or ARMORS.get(key) or ACCESSORIES.get(key)
        if not item:
            continue
        buff_name = item.get("buff")
        if buff_name and buff_name in BUFFS:
            total += BUFFS[buff_name].get(stat, 0)
    return total

def calc_player_stats(p):
    w = WEAPONS.get(p["weapon"], WEAPONS["fists"])
    a = ARMORS.get(p["armor"], ARMORS["none"])
    acc = ACCESSORIES.get(p["accessory"], ACCESSORIES["none"])

    dmg = w["dmg"] + p["strength"] * 2 + acc["bonus"]
    defense = a["def"] + p["vitality"] * 1
    crit = 5 + p["agility"]

    dmg += dmg * get_buff_value(p, None, "dmg") / 100
    defense += defense * get_buff_value(p, None, "def") / 100
    crit += get_buff_value(p, None, "crit")
    max_hp_bonus = get_buff_value(p, None, "hp")
    agi_bonus = get_buff_value(p, None, "agi")
    crit += agi_bonus

    return int(dmg), int(defense), int(crit), int(max_hp_bonus)

def floor_scale(floor):
    return 1 + (floor - 1) * 0.35

def make_mob(floor, is_boss=False):
    scale = floor_scale(floor)
    if is_boss:
        name = random.choice(BOSS_NAMES)
        base_hp = int(200 * scale)
        base_dmg = int(15 * scale)
        exp = int(80 * scale)
        silver = int(300 * scale)
        return {"name": f"👑 {name}", "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": True, "mystic": False, "elite": False, "golden": False}

    # ЗОЛОТОЙ МОБ 0.5%
    if random.randint(1, 1000) <= 5:
        name = f"🌟 ЗОЛОТОЙ {random.choice(MOB_NAMES)}"
        base_hp = int(60 * scale) * 2
        base_dmg = int(8 * scale) * 2
        exp = int(30 * scale) * 5
        silver = int(120 * scale) * 5
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": False, "mystic": False, "elite": False, "golden": True}

    if floor <= 10:
        mystic_chance = 10
    elif floor <= 20:
        mystic_chance = 15
    elif floor <= 30:
        mystic_chance = 20
    elif floor <= 40:
        mystic_chance = 25
    else:
        mystic_chance = 30

    roll = random.randint(1, 100)
    if roll <= 5:
        name = f"🔥 ЭЛИТА {random.choice(MOB_NAMES)}"
        base_hp = int(60 * scale) * 3
        base_dmg = int(8 * scale) * 3
        exp = int(30 * scale) * 3
        silver = int(120 * scale) * 3
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": False, "mystic": False, "elite": True, "golden": False}
    elif roll <= 5 + mystic_chance:
        name = random.choice(MYSTIC_NAMES)
        base_hp = int(60 * scale) * 2
        base_dmg = int(8 * scale) * 2
        exp = int(30 * scale) * 2
        silver = int(120 * scale) * 2
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": False, "mystic": True, "elite": False, "golden": False}

    name = random.choice(MOB_NAMES)
    base_hp = int(60 * scale)
    base_dmg = int(8 * scale)
    exp = int(30 * scale)
    silver = int(120 * scale)
    return {"name": name, "hp": base_hp, "max_hp": base_hp,
            "dmg": base_dmg, "exp": exp, "silver": silver,
            "boss": False, "mystic": False, "elite": False, "golden": False}

def get_pet_dmg(p, turn_number):
    """
    Возвращает (dmg, is_pet_strike) — урон питомца.
    - is_pet_strike=True раз в 3 хода (доп. удар)
    """
    try:
        pets = __import__("json").loads(p.get("pet_data", "[]") or "[]")
    except:
        pets = []
    if not pets:
        return 0, False
    # Берём первого питомца
    pet = pets[0]
    base_dmg = pet.get("dmg", 0)
    # Базовый бонус к удару
    bonus = base_dmg // 2
    extra = 0
    is_strike = False
    if turn_number % 3 == 0:
        extra = base_dmg
        is_strike = True
    return bonus + extra, is_strike

def player_turn(p, mob, turn_number=1):
    dmg, defense, crit, _ = calc_player_stats(p)
    is_crit = random.randint(1, 100) <= crit
    if is_crit:
        dmg = int(dmg * 1.5)

    # Питомец
    pet_dmg, pet_strike = get_pet_dmg(p, turn_number)
    dmg += pet_dmg

    dodge = random.randint(1, 100) <= 10
    if dodge:
        return 0, is_crit, True, 0, False
    mob["hp"] -= dmg
    return dmg, is_crit, False, pet_dmg, pet_strike

def mob_turn(p, mob):
    dmg, defense, crit, _ = calc_player_stats(p)
    raw = mob["dmg"]
    final = max(1, raw - defense // 2)

    # Кровавая луна — ×2 урон
    if BLOOD_MOON:
        final = int(final * 2)

    absorb = get_buff_value(p, None, "absorb")
    if absorb > 0 and random.randint(1, 100) <= absorb:
        final = int(final * 0.5)

    dodge = random.randint(1, 100) <= 5 + p["agility"]
    if dodge:
        return 0, True
    p["hp"] -= final
    if p["hp"] <= 0:
        p["hp"] = 0
        p["death_time"] = time.time()
    return final, False

def roll_herb(floor=1):
    pool = list(HERBS.keys())
    max_idx = min(len(pool) - 1, max(0, (floor - 1) // 3))
    idx = random.randint(0, max_idx)
    return pool[idx]

def roll_ore_drop(miner_level):
    chances = ore_chances(miner_level)
    drops = []
    ore = pick_weighted(chances)
    amt = roll_amount()
    exp = ORE_EXP.get(ore, 1) * amt
    drops.append((ore, amt, exp))
    if random.randint(1, 100) <= 40:
        ore = pick_weighted(chances)
        amt = roll_amount()
        exp = ORE_EXP.get(ore, 1) * amt
        drops.append((ore, amt, exp))
    if random.randint(1, 100) <= 20:
        ore = pick_weighted(chances)
        amt = roll_amount()
        exp = ORE_EXP.get(ore, 1) * amt
        drops.append((ore, amt, exp))
    return drops

def roll_gem_drop(miner_level):
    chances = gem_chances(miner_level)
    drops = []
    gem = pick_weighted(chances)
    amt = roll_amount()
    exp = GEM_EXP.get(gem, 1) * amt
    drops.append((gem, amt, exp))
    if random.randint(1, 100) <= 40:
        gem = pick_weighted(chances)
        amt = roll_amount()
        exp = GEM_EXP.get(gem, 1) * amt
        drops.append((gem, amt, exp))
    if random.randint(1, 100) <= 20:
        gem = pick_weighted(chances)
        amt = roll_amount()
        exp = GEM_EXP.get(gem, 1) * amt
        drops.append((gem, amt, exp))
    return drops

def roll_loot(floor=1):
    pool = list(MOB_LOOT.keys())
    max_idx = min(len(pool) - 1, max(0, (floor - 1) // 3))
    idx = random.randint(0, max_idx)
    return pool[idx]

def roll_meat():
    """10% шанс на мясо с моба."""
    return random.randint(1, 100) <= 10

def battle_text(p, mob, player_dmg, is_crit, mob_dmg, dodged_mob, dodged_player, pet_dmg=0, pet_strike=False):
    lines = []
    if dodged_player:
        lines.append(f"💨 {mob['name']} уклонился!")
    elif is_crit:
        lines.append(f"💥 КРИТ! Ты нанёс {player_dmg} урона")
    else:
        lines.append(f"⚔️ Ты нанёс {player_dmg} урона")
    if pet_dmg > 0:
        if pet_strike:
            lines.append(f"🐾 Питомец атаковал! +{pet_dmg} урона")
        else:
            lines.append(f"🐾 Питомец помог: +{pet_dmg}")

    if mob["hp"] <= 0:
        lines.append(f"💀 {mob['name']} побеждён!")
    else:
        lines.append(f"❤️ {mob['name']}: {mob['hp']}/{mob['max_hp']}")
        if dodged_mob:
            lines.append(f"💨 Ты уклонился от атаки!")
        else:
            lines.append(f"🩸 {mob['name']} нанёс {mob_dmg} урона")
        lines.append(f"❤️ Твой HP: {p['hp']}/{p['max_hp']}")
    return "\n".join(lines)

def is_dead(p):
    if p.get("hp", 1) > 0:
        return False, 0
    dt = p.get("death_time", 0) or 0
    if dt == 0:
        return False, 0
    elapsed = time.time() - dt
    if elapsed >= DEATH_TIME:
        return False, 0
    return True, int(DEATH_TIME - elapsed)

def revive_if_possible(p):
    if p.get("hp", 1) > 0:
        return False
    dt = p.get("death_time", 0) or 0
    if dt == 0:
        return False
    if time.time() - dt >= DEATH_TIME:
        p["hp"] = p["max_hp"]
        p["death_time"] = 0
        return True
    return False
