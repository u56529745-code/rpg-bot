import json
import random
from data import (
    RECIPES, RECIPES_VOID, WEAPONS, ARMORS, ACCESSORIES, POTIONS,
    PROFESSIONS, prof_exp_needed, VOID_HEART, VOID_SHARD, VOID_SOUL,
)

def craft_exp_for_level(level):
    """Базовый опыт за крафт (×1.5 увеличен)."""
    if level <= 6:
        base = random.randint(12, 18)
    elif level <= 8:
        base = random.randint(25, 45)
    elif level <= 21:
        base = random.randint(50, 110)
    elif level <= 56:
        base = random.randint(150, 350)
    else:
        base = random.randint(500, 1100)
    return int(base * 1.5)

def prof_level_from_exp(exp):
    lvl = 1
    total = 0
    for i in range(1, 100):
        total += prof_exp_needed(i)
        if exp >= total:
            lvl = i + 1
        else:
            break
    return min(lvl, 100)

def get_inventory(p):
    try:
        return json.loads(p.get("inventory_items", "[]") or "[]")
    except:
        return []

def set_inventory(p, items):
    p["inventory_items"] = json.dumps(items)

def can_craft(p, recipe_key):
    r = RECIPES[recipe_key]
    prof = r["prof"]
    prof_level = p[f"prof_{prof}"]
    if prof_level < r["level"]:
        return False, f"❌ Нужен уровень {PROFESSIONS[prof]} {r['level']}"
    if "ore" in r:
        for ore, amt in r["ore"].items():
            if p.get(ore, 0) < amt:
                return False, f"❌ Не хватает ресурса"
    if "herb" in r:
        for herb, amt in r["herb"].items():
            if p.get(herb, 0) < amt:
                return False, f"❌ Не хватает травы"
    return True, "ok"

def can_craft_void(p, recipe_key):
    r = RECIPES_VOID[recipe_key]
    if p.get("void_heart", 0) < r["void_heart"]:
        return False, "❌ Нужно Сердце бездны"
    if p.get("void_shard", 0) < r["void_shard"]:
        return False, "❌ Нужно 50 Осколков бездны"
    if p.get("void_soul", 0) < r["void_soul"]:
        return False, "❌ Нужно 100 Бездонных душ"
    base = r["base_item"]
    items = get_inventory(p)
    if base not in items and p.get("weapon") != base and p.get("armor") != base and p.get("accessory") != base:
        return False, f"❌ Нужен предмет 100 ур."
    return True, "ok"

def do_craft(p, recipe_key):
    ok, msg = can_craft(p, recipe_key)
    if not ok:
        return False, msg
    r = RECIPES[recipe_key]

    if "ore" in r:
        for ore, amt in r["ore"].items():
            p[ore] -= amt
    if "herb" in r:
        for herb, amt in r["herb"].items():
            p[herb] -= amt

    roll = random.randint(1, 100)
    if roll <= 5:
        # КРИТ ×5
        prof = r["prof"]
        exp_gain = craft_exp_for_level(r["level"]) * 5
        p[f"exp_{prof}"] = (p.get(f"exp_{prof}", 0) or 0) + exp_gain
        inv = get_inventory(p)
        for _ in range(5):
            inv.append(recipe_key)
        set_inventory(p, inv)
        new_level = prof_level_from_exp(p[f"exp_{prof}"])
        if new_level > p[f"prof_{prof}"]:
            p[f"prof_{prof}"] = new_level
        return True, f"🎰 КРИТ! ×5 {r['name']}!\n📈 +{exp_gain}"
    elif roll <= 10:
        # ПРОВАЛ
        return False, f"❌ Провал! Ресурсы сгорели."
    else:
        # УСПЕХ
        prof = r["prof"]
        exp_gain = craft_exp_for_level(r["level"])
        p[f"exp_{prof}"] = (p.get(f"exp_{prof}", 0) or 0) + exp_gain
        inv = get_inventory(p)
        inv.append(recipe_key)
        set_inventory(p, inv)
        new_level = prof_level_from_exp(p[f"exp_{prof}"])
        level_up = False
        if new_level > p[f"prof_{prof}"]:
            p[f"prof_{prof}"] = new_level
            level_up = True
        if level_up:
            return True, f"✅ {r['name']}!\n📈 +{exp_gain}\n🎉 {PROFESSIONS[prof]} → ур.{new_level}!"
        return True, f"✅ {r['name']}!\n📈 +{exp_gain}"

def do_craft_void(p, recipe_key):
    ok, msg = can_craft_void(p, recipe_key)
    if not ok:
        return False, msg
    r = RECIPES_VOID[recipe_key]
    p["void_heart"] -= r["void_heart"]
    p["void_shard"] -= r["void_shard"]
    p["void_soul"] -= r["void_soul"]
    inv = get_inventory(p)
    inv.append(recipe_key)
    set_inventory(p, inv)
    return True, f"🖤 {recipe_key} скрафчен!"
