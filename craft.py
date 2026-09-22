import json
from data import RECIPES, WEAPONS, ARMORS, ACCESSORIES, PROFESSIONS, prof_exp_needed

CRAFT_EXP = {1: 15, 2: 30, 3: 55, 4: 90, 5: 140, 6: 200, 7: 280, 8: 380, 9: 500, 10: 650}

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

    prof = r["prof"]
    exp_gain = CRAFT_EXP.get(r["level"], 15)
    p[f"exp_{prof}"] += exp_gain
    new_level = prof_level_from_exp(p[f"exp_{prof}"])
    level_up = False
    if new_level > p[f"prof_{prof}"]:
        p[f"prof_{prof}"] = new_level
        level_up = True

    crafted = json.loads(p.get("crafted_items", "[]") or "[]")
    crafted.append(recipe_key)
    p["crafted_items"] = json.dumps(crafted)

    if level_up:
        msg = f"✅ {r['name']}!\n📈 +{exp_gain}\n🎉 {PROFESSIONS[prof]} → ур.{new_level}!"
    else:
        msg = f"✅ {r['name']}!\n📈 +{exp_gain}"

    return True, msg
