import random
from data import WEAPONS, ARMORS, ACCESSORIES, MOB_NAMES, MYSTIC_NAMES, BOSS_NAMES, HERBS, ORES

def calc_player_stats(p):
    w = WEAPONS[p["weapon"]]
    a = ARMORS[p["armor"]]
    acc = ACCESSORIES[p["accessory"]]
    dmg = w["dmg"] + p["strength"] * 2 + acc["bonus"]
    defense = a["def"] + p["vitality"] * 1
    crit = 5 + p["agility"]
    return dmg, defense, crit

def make_mob(floor, is_boss=False):
    if is_boss:
        name = random.choice(BOSS_NAMES)
        base_hp = 500 * floor
        base_dmg = 20 * floor
        exp = 200 * floor
        silver = 500 * floor
        return {"name": f"👑 {name}", "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver, "boss": True, "mystic": False}

    roll = random.randint(1, 100)
    if roll <= 10:
        name = random.choice(MYSTIC_NAMES)
        base_hp = (30 + 20 * floor) * 2
        base_dmg = (5 + 3 * floor) * 2
        exp = (15 + 10 * floor) * 2
        silver = (60 + 40 * floor) * 2
        return {"name": name, "hp": base_hp, "max_hp": base_hp,
                "dmg": base_dmg, "exp": exp, "silver": silver, "boss": False, "mystic": True}

    name = random.choice(MOB_NAMES)
    base_hp = 30 + 20 * floor
    base_dmg = 5 + 3 * floor
    exp = 15 + 10 * floor
    silver = 60 + 40 * floor
    return {"name": name, "hp": base_hp, "max_hp": base_hp,
            "dmg": base_dmg, "exp": exp, "silver": silver, "boss": False, "mystic": False}

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

def roll_herb():
    roll = random.randint(1, 100)
    if roll <= 50: return "storm_kelp"
    if roll <= 80: return "salt_crystal"
    if roll <= 95: return "thunder_pearl"
    return "fire_flower"

def roll_ore():
    roll = random.randint(1, 100)
    if roll <= 40: return "copper", random.randint(1, 3)
    if roll <= 70: return "iron", random.randint(1, 2)
    if roll <= 88: return "gold", 1
    if roll <= 96: return "mithril", 1
    return "gem", 1

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
