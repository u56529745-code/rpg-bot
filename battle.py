import random
from data import (
    WEAPONS, ARMORS, ACCESSORIES, MOB_NAMES, MYSTIC_NAMES, BOSS_NAMES,
    HERBS, ORES, GEMS, MOB_LOOT, MINER_BONUS,
    ORE_TIER, GEM_TIER, ORE_EXP, GEM_EXP,
    roll_amount, ore_chances, gem_chances, pick_weighted,
)

def calc_player_stats(p):
    w = WEAPONS.get(p["weapon"], WEAPONS["fists"])
    a = ARMORS.get(p["armor"], ARMORS["none"])
    acc = ACCESSORIES.get(p["accessory"], ACCESSORIES["none"])
    dmg = w["dmg"] + p["strength"] * 2 + acc["bonus"]
    defense = a["def"] + p["vitality"] * 1
    crit = 5 + p["agility"]
    return dmg, defense, crit

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
                "boss": True, "mystic": False}

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
    if roll <= mystic_chance:
        name = random.choice(MYSTIC_NAMES)
        base_hp = int(60 * scale) * 2
        base_dmg = int(8 * scale) * 2
        exp = int(30 * scale) * 2
        silver = int(120 * scale) * 2
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver,
                "boss": False, "mystic": True}

    name = random.choice(MOB_NAMES)
    base_hp = int(60 * scale)
    base_dmg = int(8 * scale)
    exp = int(30 * scale)
    silver = int(120 * scale)
    return {"name": name, "hp": base_hp, "max_hp": base_hp,
            "dmg": base_dmg, "exp": exp, "silver": silver,
            "boss": False, "mystic": False}

def player_turn(p, mob):
    dmg, defense, crit = calc_player_stats(p)
    is_crit = random.randint(1, 100) <= crit
    if is_crit:
        dmg *= 2
    dodge = random.randint(1, 100) <= 10
    if dodge:
        return 0, is_crit, True
    mob["hp"] -= dmg
    return dmg, is_crit, False

def mob_turn(p, mob):
    dmg, defense, crit = calc_player_stats(p)
    raw = mob["dmg"]
    final = max(1, raw - defense // 2)
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
    """Возвращает список (ресурс, количество, опыт) — до 3 ресурсов."""
    chances = ore_chances(miner_level)
    drops = []
    # 1-й ресурс — 100%
    ore = pick_weighted(chances)
    amt = roll_amount()
    exp = ORE_EXP.get(ore, 1) * amt
    drops.append((ore, amt, exp))
    # 2-й — 40%
    if random.randint(1, 100) <= 40:
        ore = pick_weighted(chances)
        amt = roll_amount()
        exp = ORE_EXP.get(ore, 1) * amt
        drops.append((ore, amt, exp))
    # 3-й — 20%
    if random.randint(1, 100) <= 20:
        ore = pick_weighted(chances)
        amt = roll_amount()
        exp = ORE_EXP.get(ore, 1) * amt
        drops.append((ore, amt, exp))
    return drops

def roll_gem_drop(miner_level):
    """Возвращает список (самоцвет, количество, опыт)."""
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
