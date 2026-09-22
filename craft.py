from data import RECIPES, WEAPONS, ARMORS, ACCESSORIES, PROFESSIONS, PROF_EXP

def can_craft(p, recipe_key):
    r = RECIPES[recipe_key]
    prof = r["prof"]
    prof_level = p[f"prof_{prof}"]
    if prof_level < r["level"]:
        return False, f"❌ Нужен уровень {PROFESSIONS[prof]} {r['level']}"
    if "ore" in r:
        for ore, amt in r["ore"].items():
            if p.get(ore, 0) < amt:
                return False, f"❌ Не хватает {ore}"
    if "herb" in r:
        for herb, amt in r["herb"].items():
            if p.get(herb, 0) < amt:
                return False, f"❌ Не хватает {herb}"
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
    p[f"exp_{prof}"] += 10 + r["level"] * 5
    new_level = 1
    for lvl, need in sorted(PROF_EXP.items()):
        if p[f"exp_{prof}"] >= need:
            new_level = lvl
    if new_level > p[f"prof_{prof}"]:
        p[f"prof_{prof}"] = new_level
        msg = f"🎉 {PROFESSIONS[prof]} повышен до уровня {new_level}!"
    else:
        msg = f"✅ Скрафчено: {r['name']}"
    return True, msg

def recipe_text(key):
    r = RECIPES[key]
    parts = [f"🔨 {r['name']}"]
    parts.append(f"Профессия: {PROFESSIONS[r['prof']]} (ур. {r['level']})")
    if "ore" in r:
        parts.append("Ресурсы:")
        for ore, amt in r["ore"].items():
            parts.append(f"  {ore} × {amt}")
    if "herb" in r:
        parts.append("Травы:")
        for herb, amt in r["herb"].items():
            parts.append(f"  {herb} × {amt}")
    return "\n".join(parts)
