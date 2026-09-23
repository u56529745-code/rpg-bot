import random
from data import (
    WEAPONS, ARMORS, ACCESSORIES, MOB_NAMES, MYSTIC_NAMES, BOSS_NAMES,
    HERBS, ORES, GEMS, MOB_LOOT, MINER_BONUS, BUFFS,
    ORE_TIER, GEM_TIER, ORE_EXP, GEM_EXP,
    roll_amount, ore_chances, gem_chances, pick_weighted,
)

def get_buff_value(p, buff_key, stat):
    """Возвращает суммарный бафф от надетого снаряжения."""
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

    # Баффы
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
                "boss": True, "mystic": False, "elite": False}

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
        # Элитный (×3)
        name = f"🔥 ЭЛИТА {random.choice(MOB_NAMES)}"
        base_hp = int(60 * scale) * 3
        base_dmg = int(8 * scale) * 3
        exp = int(30 * scale) * 3
        silver = int(120 * scale) * 3
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": False, "mystic": False, "elite": True}
    elif roll <= 5 + mystic_chance:
        name = random.choice(MYSTIC_NAMES)
        base_hp = int(60 * scale) * 2
        base_dmg = int(8 * scale) * 2
        exp = int(30 * scale) * 2
        silver = int(120 * scale) * 2
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": False, "mystic": True, "elite": False}

    name = random.choice(MOB_NAMES)
    base_hp = int(60 * scale)
    base_dmg = int(8 * scale)
    exp = int(30 * scale)
    silver = int(120 * scale)
    return {"name": name, "hp": base_hp, "max_hp": base_hp,
            "dmg": base_dmg, "exp": exp, "silver": silver,
            "boss": False, "mystic": False, "elite": False}

def player_turn(p, mob):
    dmg, defense, crit, _ = calc_player_stats(p)
    is_crit = random.randint(1, 100) <= crit
    if is_crit:
        dmg = int(dmg * 1.5)
    dodge = random.randint(1, 100) <= 10
    if dodge:
        return 0, is_crit, True
    mob["hp"] -= dmg
    return dmg, is_crit, False

def mob_turn(p, mob):
    dmg, defense, crit, _ = calc_player_stats(p)
    raw = mob["dmg"]
    final = max(1, raw - defense // 2)

    # Пассивка "впитать 50% урона"
    absorb = get_buff_value(p, None, "absorb")
    if absorb > 0 and random.randint(1, 100) <= absorb:
        final = int(final * 0.5)

    dodge = random.randint(1, 100) <= 5 + p["agility"]
    if dodge:
        return 0, True
    p["hp"] -= final
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

def battle_text(p, mob, player_dmg, is_crit, mob_dmg, dodged_mob, dodged_player):
    lines = []
    if dodged_player:
        lines.append(f"💨 {mob['name']} уклонился!")
    elif is_crit:
        lines.append(f"💥 КРИТ! Ты нанёс {player_dmg} урона")
    else:
        lines.append(f"⚔️ Ты нанёс {player_dmg} урона")

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
