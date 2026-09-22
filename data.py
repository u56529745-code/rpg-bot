# МОБЫ (100 на этаж)
MOB_NAMES = [
    "🐀 Крыса", "🦇 Летучая мышь", "🐺 Волк", "🐗 Кабан", "🐻 Медведь",
    "🦂 Скорпион", "🕷 Паук", "🐍 Змея", "🦊 Лиса", "🐆 Леопард",
    "🐊 Крокодил", "🦅 Орёл", "🐉 Дракончик", "👹 Гоблин", "🧟 Зомби",
]

MYSTIC_NAMES = [
    "🌟 Мистический волк", "🌟 Мистический медведь", "🌟 Мистический дракон",
    "🌟 Мистический феникс", "🌟 Мистический единорог",
]

BOSS_NAMES = [
    "👑 Владыка этажа", "💀 Король мертвых", "🐲 Древний дракон",
    "👺 Повелитель демонов", "🧙 Архимаг",
]

# РЕСУРСЫ
ORES = {
    "copper": {"name": "🟠 Медь", "price": 30},
    "iron": {"name": "⚙️ Железо", "price": 80},
    "gold": {"name": "🟡 Золото", "price": 200},
    "mithril": {"name": "💠 Мифрил", "price": 800},
    "gem": {"name": "💎 Самоцвет", "price": 1500},
}

HERBS = {
    "storm_kelp": {"name": "🌿 Штормовой келп", "price": 50},
    "salt_crystal": {"name": "🪨 Кристалл соли", "price": 100},
    "thunder_pearl": {"name": "⚡ Громовая жемчужина", "price": 300},
    "fire_flower": {"name": "🔥 Огнецвет", "price": 500},
}

# ОРУЖИЕ
WEAPONS = {
    "fists": {"name": "👊 Кулаки", "dmg": 5, "level": 0},
    "sword": {"name": "🗡 Меч", "dmg": 15, "level": 1},
    "axe": {"name": "🪓 Топор", "dmg": 25, "level": 2},
    "spear": {"name": "🔱 Копьё", "dmg": 40, "level": 3},
    "magic": {"name": "🔮 Посох", "dmg": 60, "level": 4},
    "legend": {"name": "⚔️ Легендарный клинок", "dmg": 100, "level": 5},
}

# БРОНЯ
ARMORS = {
    "none": {"name": "🚫 Без брони", "def": 0, "level": 0},
    "leather": {"name": "🧥 Кожаная", "def": 3, "level": 1},
    "chain": {"name": "⛓ Кольчуга", "def": 8, "level": 2},
    "plate": {"name": "🛡 Латная", "def": 15, "level": 3},
    "dragon": {"name": "🐲 Драконья", "def": 25, "level": 4},
    "titan": {"name": "⚡ Титановая", "def": 40, "level": 5},
}

# АКСЕССУАРЫ
ACCESSORIES = {
    "none": {"name": "🚫 Нет", "bonus": 0, "level": 0},
    "ring_copper": {"name": "💍 Медное кольцо", "bonus": 5, "level": 1},
    "ring_iron": {"name": "💍 Железное кольцо", "bonus": 10, "level": 2},
    "amulet_gold": {"name": "📿 Золотой амулет", "bonus": 20, "level": 3},
    "ring_mithril": {"name": "💍 Мифриловое кольцо", "bonus": 35, "level": 4},
    "amulet_legend": {"name": "📿 Легендарный амулет", "bonus": 50, "level": 5},
}

# РЕЦЕПТЫ (профессия: кузнец, бронник, ювелир, алхимик)
RECIPES = {
    # Оружие (кузнец)
    "sword": {"name": "🗡 Меч", "prof": "smith", "level": 1, "ore": {"copper": 5, "iron": 2}},
    "axe": {"name": "🪓 Топор", "prof": "smith", "level": 1, "ore": {"copper": 3, "iron": 4}},
    "spear": {"name": "🔱 Копьё", "prof": "smith", "level": 2, "ore": {"iron": 5, "gold": 2}},
    "magic": {"name": "🔮 Посох", "prof": "smith", "level": 3, "ore": {"iron": 3, "gold": 4, "mithril": 1}},
    "legend": {"name": "⚔️ Легендарный клинок", "prof": "smith", "level": 4, "ore": {"gold": 5, "mithril": 3, "gem": 1}},
    # Броня (бронник)
    "leather": {"name": "🧥 Кожаная", "prof": "armorer", "level": 1, "ore": {"copper": 4}},
    "chain": {"name": "⛓ Кольчуга", "prof": "armorer", "level": 1, "ore": {"copper": 3, "iron": 3}},
    "plate": {"name": "🛡 Латная", "prof": "armorer", "level": 2, "ore": {"iron": 6}},
    "dragon": {"name": "🐲 Драконья", "prof": "armorer", "level": 3, "ore": {"gold": 5, "mithril": 2}},
    "titan": {"name": "⚡ Титановая", "prof": "armorer", "level": 4, "ore": {"mithril": 5, "gem": 2}},
    # Аксессуары (ювелир)
    "ring_copper": {"name": "💍 Медное кольцо", "prof": "jeweler", "level": 1, "ore": {"copper": 3, "gem": 1}},
    "ring_iron": {"name": "💍 Железное кольцо", "prof": "jeweler", "level": 2, "ore": {"iron": 4, "gem": 2}},
    "amulet_gold": {"name": "📿 Золотой амулет", "prof": "jeweler", "level": 3, "ore": {"gold": 5, "gem": 3}},
    "ring_mithril": {"name": "💍 Мифриловое кольцо", "prof": "jeweler", "level": 4, "ore": {"mithril": 3, "gem": 5}},
    "amulet_legend": {"name": "📿 Легендарный амулет", "prof": "jeweler", "level": 5, "ore": {"mithril": 5, "gem": 10}},
    # Зелья (алхимик)
    "hp_small": {"name": "🧪 Малое зелье HP", "prof": "alchemist", "level": 1, "herb": {"storm_kelp": 3, "salt_crystal": 1}},
    "hp_big": {"name": "🧪 Большое зелье HP", "prof": "alchemist", "level": 2, "herb": {"salt_crystal": 3, "thunder_pearl": 1}},
    "str_potion": {"name": "🧪 Зелье силы", "prof": "alchemist", "level": 3, "herb": {"thunder_pearl": 2, "fire_flower": 1}},
    "def_potion": {"name": "🧪 Зелье защиты", "prof": "alchemist", "level": 3, "herb": {"salt_crystal": 2, "fire_flower": 2}},
}

# ПРОФЕССИИ
PROFESSIONS = {
    "smith": "⚒️ Кузнец",
    "armorer": "🛡 Бронник",
    "jeweler": "💍 Ювелир",
    "alchemist": "⚗️ Алхимик",
}

# ОПЫТ ПРОФЕССИЙ (уровень: нужный опыт)
PROF_EXP = {1: 0, 2: 100, 3: 300, 4: 700, 5: 1500}

# НАГРАДЫ ЗА ЭТАЖ
FLOOR_REWARDS = {
    1: {"silver": 500, "exp": 100},
    2: {"silver": 1000, "exp": 200},
    3: {"silver": 2000, "exp": 400},
    4: {"silver": 4000, "exp": 800},
    5: {"silver": 8000, "exp": 1600},
    6: {"silver": 16000, "exp": 3200},
    7: {"silver": 32000, "exp": 6400},
    8: {"silver": 64000, "exp": 12800},
    9: {"silver": 128000, "exp": 25600},
    10: {"silver": 256000, "exp": 51200},
}
