import random

# ============ ТИРЫ ============
TIER_NAMES = {
    "E": "E", "D": "D", "C": "C", "B": "B", "A": "A",
    "S": "S", "SS": "SS", "SSS": "SSS", "SSS+": "SSS+"
}

# ============ РУДА (10) ============
ORES = {
    "copper": {"name": "🟠 Медь", "price": 30, "level": 1, "tier": "E"},
    "iron": {"name": "⚙️ Железо", "price": 80, "level": 2, "tier": "D"},
    "gold": {"name": "🟡 Золото", "price": 200, "level": 3, "tier": "C"},
    "mithril": {"name": "💠 Мифрил", "price": 800, "level": 4, "tier": "B"},
    "lead": {"name": "⚫ Свинец", "price": 1500, "level": 5, "tier": "A"},
    "silver_ore": {"name": "🔘 Серебро", "price": 3000, "level": 6, "tier": "S"},
    "platinum": {"name": "🔶 Платина", "price": 6000, "level": 7, "tier": "SS"},
    "titanite": {"name": "🟣 Титанит", "price": 12000, "level": 8, "tier": "SSS"},
    "adamantite": {"name": "🔷 Адамантит", "price": 25000, "level": 9, "tier": "SSS+"},
    "star_metal": {"name": "🌌 Звёздный металл", "price": 50000, "level": 10, "tier": "SSS+"},
}

ORE_TIER = {k: v["tier"] for k, v in ORES.items()}

ORE_EXP = {
    "copper": 2, "iron": 4, "gold": 8, "mithril": 14, "lead": 24,
    "silver_ore": 36, "platinum": 50, "titanite": 350,
    "adamantite": 500, "star_metal": 750,
}

# ============ САМОЦВЕТЫ (10) ============
GEMS = {
    "emerald": {"name": "🟢 Изумруд", "price": 100, "level": 1, "tier": "E"},
    "sapphire": {"name": "🔵 Сапфир", "price": 300, "level": 2, "tier": "D"},
    "amethyst": {"name": "🟣 Аметист", "price": 600, "level": 3, "tier": "C"},
    "topaz": {"name": "🟡 Топаз", "price": 1200, "level": 4, "tier": "B"},
    "ruby": {"name": "🔴 Рубин", "price": 2500, "level": 5, "tier": "A"},
    "diamond": {"name": "⚪ Алмаз", "price": 5000, "level": 6, "tier": "S"},
    "garnet": {"name": "🟠 Гранат", "price": 8000, "level": 7, "tier": "SS"},
    "tanzanite": {"name": "💜 Танзанит", "price": 12000, "level": 8, "tier": "SSS"},
    "onyx": {"name": "🖤 Оникс", "price": 20000, "level": 9, "tier": "SSS"},
    "moonstone": {"name": "💎 Лунный камень", "price": 35000, "level": 10, "tier": "SSS+"},
}

GEM_TIER = {k: v["tier"] for k, v in GEMS.items()}

GEM_EXP = {
    "emerald": 4, "sapphire": 8, "amethyst": 16, "topaz": 28,
    "ruby": 96, "diamond": 144, "garnet": 200, "tanzanite": 700,
    "onyx": 900, "moonstone": 1200,
}

# ============ ТРАВЫ (20) ============
HERBS = {
    "storm_kelp": {"name": "🌿 Штормовой келп", "price": 50, "level": 1, "tier": "E"},
    "salt_crystal": {"name": "🪨 Кристалл соли", "price": 100, "level": 2, "tier": "E"},
    "thunder_pearl": {"name": "⚡ Громовая жемчужина", "price": 300, "level": 3, "tier": "D"},
    "fire_flower": {"name": "🔥 Огнецвет", "price": 500, "level": 4, "tier": "D"},
    "glow_moss": {"name": "🍄 Светящийся мох", "price": 800, "level": 5, "tier": "C"},
    "blood_rose": {"name": "🌸 Кровавая роза", "price": 1200, "level": 6, "tier": "C"},
    "void_flower": {"name": "🌺 Цветок пустоты", "price": 1800, "level": 7, "tier": "B"},
    "ender_orchid": {"name": "🌷 Эндер-орхидея", "price": 2500, "level": 8, "tier": "B"},
    "black_sakura": {"name": "🥀 Чёрная сакура", "price": 4000, "level": 9, "tier": "A"},
    "star_clover": {"name": "🌟 Звёздный клевер", "price": 6000, "level": 10, "tier": "A"},
    "moon_fern": {"name": "🌙 Лунный папоротник", "price": 9000, "level": 11, "tier": "S"},
    "eye_cactus": {"name": "👁 Глазастый кактус", "price": 13000, "level": 12, "tier": "S"},
    "whisper_tree": {"name": "🌲 Дерево шёпота", "price": 18000, "level": 13, "tier": "SS"},
    "weeping_lily": {"name": "🌺 Плачущая лилия", "price": 24000, "level": 14, "tier": "SS"},
    "clock_mushroom": {"name": "🍄 Гриб-часовщик", "price": 32000, "level": 15, "tier": "SS"},
    "fire_ivy": {"name": "🔥 Огненный плющ", "price": 42000, "level": 16, "tier": "SSS"},
    "frost_bell": {"name": "❄️ Морозный колокольчик", "price": 55000, "level": 17, "tier": "SSS"},
    "soul_tree": {"name": "🌳 Дерево душ", "price": 70000, "level": 18, "tier": "SSS"},
    "teleport_liana": {"name": "🌿 Лиана-телепорт", "price": 90000, "level": 19, "tier": "SSS+"},
    "predator_plant": {"name": "🌱 Растение-хищник", "price": 120000, "level": 20, "tier": "SSS+"},
}

HERB_TIER = {k: v["tier"] for k, v in HERBS.items()}

# ============ ЛУТ (20) ============
MOB_LOOT = {
    "wolf_fang": {"name": "🦷 Клык волка", "price": 40, "tier": "E"},
    "spider_web": {"name": "🕸 Паутина", "price": 80, "tier": "E"},
    "scorpion_sting": {"name": "🦂 Жало скорпиона", "price": 150, "tier": "D"},
    "bear_claw": {"name": "🐻 Коготь медведя", "price": 250, "tier": "D"},
    "skeleton_bone": {"name": "💀 Кость скелета", "price": 400, "tier": "D"},
    "hunter_eye": {"name": "👁 Глаз ночного охотника", "price": 700, "tier": "C"},
    "dragon_scale": {"name": "🐉 Чешуя дракона", "price": 1200, "tier": "C"},
    "golem_heart": {"name": "❤️ Сердце голема", "price": 2000, "tier": "B"},
    "phoenix_feather": {"name": "🦅 Перо феникса", "price": 3500, "tier": "B"},
    "black_moon_shard": {"name": "🌑 Осколок чёрной луны", "price": 6000, "tier": "A"},
    "void_fang": {"name": "🦷 Клык пустотника", "price": 9000, "tier": "A"},
    "thunder_horn": {"name": "📯 Рог громового зверя", "price": 14000, "tier": "S"},
    "sky_feather": {"name": "🪶 Перо небесного моба", "price": 20000, "tier": "S"},
    "shadow_claw": {"name": "🐾 Коготь теневого волка", "price": 28000, "tier": "SS"},
    "mini_dragon_scale": {"name": "🐲 Чешуя мини-дракона", "price": 40000, "tier": "SS"},
    "poison_sting": {"name": "🐝 Жало ядовитой пчелы", "price": 55000, "tier": "SS"},
    "mushroom_skull": {"name": "💀 Череп грибного монстра", "price": 75000, "tier": "SSS"},
    "chameleon_slime": {"name": "🟢 Слизь-хамелеон", "price": 100000, "tier": "SSS"},
    "lava_heart": {"name": "🔥 Сердце лавового слизня", "price": 140000, "tier": "SSS+"},
    "ghost_raven_feather": {"name": "🖤 Чёрное перо ворона-призрака", "price": 200000, "tier": "SSS+"},
}

LOOT_TIER = {k: v["tier"] for k, v in MOB_LOOT.items()}

# ============ МЯСО ============
MEAT = {
    "raw_meat": {"name": "🥩 Сырое мясо", "price": 100, "tier": "E"},
}
MEAT_TIER = {k: v["tier"] for k, v in MEAT.items()}

# ============ РЕСУРСЫ БЕЗДНЫ ============
VOID_HEART = {"name": "🖤 Сердце бездны", "price": 5000000, "tier": "SSS+"}
VOID_SHARD = {"name": "💠 Осколок бездны", "price": 500000, "tier": "SSS+"}
VOID_SOUL = {"name": "🕯 Бездонная душа", "price": 100000, "tier": "SSS+"}

VOID_TIER = {
    "void_heart": "SSS+",
    "void_shard": "SSS+",
    "void_soul": "SSS+",
}

# ============ ОРУЖИЕ ============
WEAPONS = {
    "fists": {"name": "👊 Кулаки", "dmg": 5, "level": 0, "tier": "E"},
    "sword": {"name": "🗡 Меч", "dmg": 15, "level": 1, "tier": "E", "buff": "dmg10"},
    "knife": {"name": "🔪 Нож", "dmg": 20, "level": 2, "tier": "E", "buff": "crit10"},
    "dagger": {"name": "🗡 Кинжал", "dmg": 25, "level": 3, "tier": "D", "buff": "crit15"},
    "axe": {"name": "🪓 Топор", "dmg": 35, "level": 4, "tier": "D", "buff": "dmg15"},
    "spear": {"name": "🔱 Копьё", "dmg": 50, "level": 5, "tier": "D", "buff": "hp10"},
    "revolver": {"name": "🔫 Револьвер", "dmg": 70, "level": 6, "tier": "C", "buff": "crit10"},
    "magic": {"name": "🔮 Посох", "dmg": 90, "level": 7, "tier": "C", "buff": "dmg10"},
    "scythe_moon": {"name": "🌙 Коса лунного жнеца", "dmg": 130, "level": 8, "tier": "B", "buff": "crit15"},
    "parasite_pick": {"name": "🪱 Кирка-паразит", "dmg": 180, "level": 9, "tier": "B", "buff": "heal5_20"},
    "twisted_shovel": {"name": "⛏ Лопата искривлённой земли", "dmg": 240, "level": 10, "tier": "A", "buff": "dmg15"},
    "soul_hoe": {"name": "⚒ Мотыга садовника душ", "dmg": 320, "level": 12, "tier": "A", "buff": "exp15"},
    "thunder_axe": {"name": "🪓 Топор громового дерева", "dmg": 420, "level": 14, "tier": "S", "buff": "crit15"},
    "void_pick": {"name": "⚫ Кирка пустотного кристалла", "dmg": 550, "level": 16, "tier": "S", "buff": "dmg15"},
    "ice_drill": {"name": "❄️ Ледяной бур", "dmg": 700, "level": 18, "tier": "SS", "buff": "agi15"},
    "meteor_hammer": {"name": "☄️ Кувалда метеорита", "dmg": 900, "level": 20, "tier": "SS", "buff": "dmg20"},
    "root_staff": {"name": "🌿 Посох корней", "dmg": 1150, "level": 25, "tier": "SS", "buff": "hp20"},
    "blood_sickle": {"name": "🌹 Серп кровавой розы", "dmg": 1450, "level": 30, "tier": "SSS", "buff": "heal5_20"},
    "spirit_hammer": {"name": "🔨 Молот кузнечного духа", "dmg": 1800, "level": 35, "tier": "SSS", "buff": "silver15"},
    "portal_shovel": {"name": "🌀 Лопата-портал", "dmg": 2200, "level": 40, "tier": "SSS", "buff": "agi15"},
    "golden_trident": {"name": "🔱 Золотой трезубец", "dmg": 2700, "level": 45, "tier": "SSS", "buff": "silver15"},
    "miner_claw": {"name": "🦾 Коготь шахтёра", "dmg": 3300, "level": 50, "tier": "SSS", "buff": "dmg15"},
    "time_pick": {"name": "⏳ Кирка времени", "dmg": 4000, "level": 60, "tier": "SSS+", "buff": "exp15"},
    "living_axe": {"name": "🪓 Топор с живым лезвием", "dmg": 4800, "level": 70, "tier": "SSS+", "buff": "hp20"},
    "eternal_hoe": {"name": "🌾 Мотыга вечной жатвы", "dmg": 5800, "level": 85, "tier": "SSS+", "buff": "exp15"},
    "legend": {"name": "⚔️ Легендарный клинок", "dmg": 7000, "level": 100, "tier": "SSS+"},
    # СЕКРЕТНЫЕ
    "demon_mace": {"name": "🔨 Булава кровавого демона", "dmg": 35000, "level": 0, "tier": "SSS+", "buff": "crit25"},
    "dragon_katana": {"name": "🗡 Катана дракона", "dmg": 38000, "level": 0, "tier": "SSS+", "buff": "dmg25"},
    "blood_spear": {"name": "🩸 Кровавое копьё", "dmg": 36000, "level": 0, "tier": "SSS+", "buff": "heal5_20"},
    # БЕЗДНА
    "void_blade": {"name": "⚔️ Клинок бездны", "dmg": 40000, "level": 0, "tier": "SSS+", "buff": "agi25", "void": True},
}

WEAPON_TIER = {k: v.get("tier", "E") for k, v in WEAPONS.items()}

# ============ БРОНЯ (С ФИКСОМ `none`) ============
ARMORS = {
    "none": {"name": "🚫 Без брони", "def": 0, "level": 0, "tier": "E"},
    "leather": {"name": "🧥 Кожаная", "def": 3, "level": 1, "tier": "E"},
    "chain": {"name": "⛓ Кольчуга", "def": 8, "level": 3, "tier": "D"},
    "plate": {"name": "🛡 Латная", "def": 15, "level": 5, "tier": "C"},
    "dragon": {"name": "🐲 Драконья", "def": 25, "level": 8, "tier": "B"},
    "titan": {"name": "⚡ Титановая", "def": 40, "level": 12, "tier": "B"},
    "moon_knight": {"name": "🌙 Доспехи лунного рыцаря", "def": 60, "level": 16, "tier": "A"},
    "kraken_shell": {"name": "🐙 Броня из панцирей кракена", "def": 85, "level": 20, "tier": "A"},
    "forest_spirit": {"name": "🌲 Комплект лесного духа", "def": 115, "level": 25, "tier": "S"},
    "void_armor_old": {"name": "⚫ Доспехи пустотника", "def": 150, "level": 30, "tier": "S"},
    "crystal_golem": {"name": "💎 Броня кристального голема", "def": 195, "level": 35, "tier": "SS"},
    "thunder_guard": {"name": "⚡ Комплект грозового стража", "def": 250, "level": 40, "tier": "SS"},
    "ice_demon": {"name": "❄️ Доспехи ледяного демона", "def": 320, "level": 45, "tier": "SS"},
    "mushroom_king": {"name": "🍄 Броня грибного короля", "def": 400, "level": 50, "tier": "SSS"},
    "sand_ghost": {"name": "🏜 Комплект песчаного призрака", "def": 500, "level": 55, "tier": "SSS"},
    "black_rose": {"name": "🌹 Доспехи чёрной розы", "def": 620, "level": 60, "tier": "SSS"},
    "dragon_heart": {"name": "🐉 Броня драконьего сердца", "def": 780, "level": 70, "tier": "SSS+"},
    "sky_smith": {"name": "☁️ Доспехи небесного кузнеца", "def": 980, "level": 80, "tier": "SSS+"},
    "dead_forest": {"name": "💀 Доспехи мёртвого леса", "def": 1250, "level": 90, "tier": "SSS+"},
    "mirror_knight": {"name": "🪞 Броня зеркального рыцаря", "def": 1600, "level": 100, "tier": "SSS+"},
    # СЕКРЕТНАЯ
    "god_flesh": {"name": "🩸 Броня из плоти бога", "def": 4000, "level": 0, "tier": "SSS+", "buff": "hp50_def30_heal10"},
    # БЕЗДНА
    "void_armor": {"name": "⚫ Броня бездны", "def": 4400, "level": 0, "tier": "SSS+", "buff": "hp60_def40_absorb20", "void": True},
}

ARMOR_TIER = {k: v.get("tier", "E") for k, v in ARMORS.items()}

# ============ БИЖУТЕРИЯ (С ФИКСОМ `none`) ============
ACCESSORIES = {
    "none": {"name": "🚫 Нет", "bonus": 0, "level": 0, "tier": "E"},
    "ring_copper": {"name": "💍 Медное кольцо", "bonus": 5, "level": 1, "tier": "E"},
    "ring_iron": {"name": "💍 Железное кольцо", "bonus": 10, "level": 3, "tier": "D"},
    "amulet_gold": {"name": "📿 Золотой амулет", "bonus": 20, "level": 5, "tier": "C"},
    "ring_mithril": {"name": "💍 Мифриловое кольцо", "bonus": 35, "level": 8, "tier": "B"},
    "moon_necklace": {"name": "🌙 Ожерелье последней луны", "bonus": 55, "level": 12, "tier": "B"},
    "invisible_ring": {"name": "🕸 Кольцо невидимой нити", "bonus": 80, "level": 16, "tier": "A"},
    "ender_earrings": {"name": "👁 Серьги эндер-глаза", "bonus": 110, "level": 20, "tier": "A"},
    "living_bracelet": {"name": "🌿 Браслет живых корней", "bonus": 150, "level": 25, "tier": "S"},
    "dragon_pendant": {"name": "🐉 Кулон драконьего сердца", "bonus": 200, "level": 30, "tier": "S"},
    "time_ring": {"name": "⏳ Кольцо остановленного времени", "bonus": 270, "level": 35, "tier": "SS"},
    "mushroom_crown": {"name": "👑 Венец грибного короля", "bonus": 360, "level": 40, "tier": "SS"},
    "black_sun_amulet": {"name": "☀️ Амулет чёрного солнца", "bonus": 480, "level": 45, "tier": "SS"},
    "bat_earrings": {"name": "🦇 Серьги летучей мыши", "bonus": 630, "level": 50, "tier": "SSS"},
    "thunder_bracelet": {"name": "⚡ Браслет грозы", "bonus": 820, "level": 55, "tier": "SSS"},
    "void_ring": {"name": "⚫ Кольцо пустоты", "bonus": 1080, "level": 60, "tier": "SSS"},
    "moon_pendant": {"name": "🌙 Кулон лунного осколка", "bonus": 1420, "level": 70, "tier": "SSS+"},
    "lost_soul_amulet": {"name": "👻 Амулет потерянной души", "bonus": 1850, "level": 80, "tier": "SSS+"},
    "night_flower_pendant": {"name": "🌸 Кулон цветка ночи", "bonus": 2400, "level": 90, "tier": "SSS+"},
    "forgotten_god": {"name": "🏛 Медальон забытого бога", "bonus": 3200, "level": 100, "tier": "SSS+"},
    # СЕКРЕТНЫЕ
    "eternity_ring": {"name": "💍 Кольцо вечности", "bonus": 6000, "level": 0, "tier": "SSS+", "buff": "exp25"},
    "demon_crown": {"name": "👑 Корона демона", "bonus": 7000, "level": 0, "tier": "SSS+", "buff": "dmg50_agi15"},
    # БЕЗДНА
    "void_amulet": {"name": "📿 Амулет бездны", "bonus": 6500, "level": 0, "tier": "SSS+", "buff": "silver25", "void": True},
}

ACCESSORY_TIER = {k: v.get("tier", "E") for k, v in ACCESSORIES.items()}

# ============ ЗЕЛЬЯ (20) ============
POTIONS = {
    "moon_light": {"name": "🌙 Зелье лунного света", "level": 1, "tier": "E"},
    "shadow_form": {"name": "🌑 Зелье превращения в тень", "level": 2, "tier": "E"},
    "ceiling_walk": {"name": "🦶 Зелье ходьбы по потолку", "level": 3, "tier": "D"},
    "mob_invisibility": {"name": "👻 Зелье невидимости для мобов", "level": 4, "tier": "D"},
    "block_jump": {"name": "🦘 Зелье прыжка между блоками", "level": 5, "tier": "C"},
    "stone_skin": {"name": "🪨 Зелье каменной кожи", "level": 6, "tier": "C"},
    "animal_talk": {"name": "🐾 Зелье разговора с животными", "level": 7, "tier": "B"},
    "reverse_aging": {"name": "⏪ Зелье обратного старения", "level": 8, "tier": "B"},
    "night_vision": {"name": "👁 Зелье ночного зрения ×100", "level": 9, "tier": "A"},
    "water_freeze": {"name": "❄️ Зелье заморозки воды", "level": 10, "tier": "A"},
    "lightning_call": {"name": "⚡ Зелье призыва молнии", "level": 11, "tier": "S"},
    "mushroom_growth": {"name": "🍄 Зелье роста грибов", "level": 12, "tier": "S"},
    "slime_form": {"name": "🟢 Зелье превращения в слизь", "level": 13, "tier": "SS"},
    "lava_breath": {"name": "🔥 Зелье дыхания в лаве", "level": 14, "tier": "SS"},
    "miner_luck": {"name": "🍀 Зелье удачи шахтёра", "level": 15, "tier": "SS"},
    "moon_teleport": {"name": "🌙 Зелье телепортации к луне", "level": 16, "tier": "SSS"},
    "damage_reflect": {"name": "🛡 Зелье отражения урона", "level": 17, "tier": "SSS"},
    "time_slow": {"name": "⏳ Зелье замедления времени", "level": 18, "tier": "SSS"},
    "ghost_form": {"name": "👻 Зелье превращения в призрака", "level": 19, "tier": "SSS+"},
    "random_effect": {"name": "🎲 Зелье случайного эффекта", "level": 20, "tier": "SSS+"},
}

POTION_TIER = {k: v.get("tier", "E") for k, v in POTIONS.items()}

# ============ РЕЦЕПТЫ ОРУЖИЯ ============
RECIPES_WEAPONS = {
    "sword": {"copper": 5, "iron": 2},
    "knife": {"copper": 3, "iron": 3},
    "dagger": {"iron": 5, "emerald": 1},
    "axe": {"iron": 4, "copper": 3},
    "spear": {"iron": 5, "gold": 2},
    "revolver": {"gold": 4, "iron": 5, "sapphire": 2},
    "magic": {"gold": 4, "mithril": 1, "amethyst": 2},
    "scythe_moon": {"mithril": 3, "topaz": 2, "gold": 5},
    "parasite_pick": {"mithril": 4, "topaz": 3},
    "twisted_shovel": {"mithril": 5, "ruby": 2, "lead": 3},
    "soul_hoe": {"lead": 5, "ruby": 3, "silver_ore": 2},
    "thunder_axe": {"silver_ore": 4, "ruby": 4, "diamond": 2},
    "void_pick": {"platinum": 5, "diamond": 3, "silver_ore": 4},
    "ice_drill": {"platinum": 4, "garnet": 3, "diamond": 3},
    "meteor_hammer": {"platinum": 5, "tanzanite": 3, "garnet": 4},
    "root_staff": {"titanite": 5, "onyx": 3, "tanzanite": 3},
    "blood_sickle": {"titanite": 4, "onyx": 4, "garnet": 3},
    "spirit_hammer": {"adamantite": 5, "onyx": 3, "moonstone": 2},
    "portal_shovel": {"adamantite": 4, "moonstone": 3, "onyx": 4},
    "golden_trident": {"adamantite": 5, "moonstone": 5, "onyx": 3},
    "miner_claw": {"star_metal": 3, "moonstone": 4, "adamantite": 5},
    "time_pick": {"star_metal": 5, "moonstone": 5, "onyx": 5},
    "living_axe": {"star_metal": 6, "moonstone": 6, "adamantite": 5},
    "eternal_hoe": {"star_metal": 8, "moonstone": 8, "onyx": 6},
    "legend": {"star_metal": 10, "moonstone": 10, "adamantite": 8, "onyx": 8},
}

# ============ РЕЦЕПТЫ БРОНИ ============
RECIPES_ARMORS = {
    "leather": {"copper": 4},
    "chain": {"copper": 3, "iron": 3},
    "plate": {"iron": 6, "emerald": 1},
    "dragon": {"gold": 5, "sapphire": 2, "iron": 4},
    "titan": {"mithril": 5, "amethyst": 2},
    "moon_knight": {"mithril": 4, "topaz": 2, "gold": 5},
    "kraken_shell": {"mithril": 5, "ruby": 3, "topaz": 3},
    "forest_spirit": {"lead": 5, "ruby": 2, "emerald": 4},
    "void_armor_old": {"lead": 4, "diamond": 3, "silver_ore": 3},
    "crystal_golem": {"silver_ore": 5, "diamond": 4, "garnet": 2},
    "thunder_guard": {"platinum": 4, "garnet": 4, "diamond": 3},
    "ice_demon": {"platinum": 5, "tanzanite": 3, "garnet": 4},
    "mushroom_king": {"platinum": 4, "onyx": 3, "tanzanite": 3},
    "sand_ghost": {"titanite": 5, "onyx": 4, "garnet": 3},
    "black_rose": {"titanite": 4, "onyx": 5, "tanzanite": 4},
    "dragon_heart": {"adamantite": 5, "moonstone": 3, "onyx": 4},
    "sky_smith": {"adamantite": 6, "moonstone": 4, "onyx": 5},
    "dead_forest": {"adamantite": 5, "star_metal": 3, "moonstone": 5},
    "mirror_knight": {"star_metal": 8, "moonstone": 8, "onyx": 6},
}

# ============ РЕЦЕПТЫ БИЖУТЕРИИ ============
RECIPES_ACCESSORIES = {
    "ring_copper": {"copper": 3, "emerald": 1},
    "ring_iron": {"iron": 4, "emerald": 2},
    "amulet_gold": {"gold": 5, "sapphire": 2},
    "ring_mithril": {"mithril": 3, "amethyst": 3},
    "moon_necklace": {"mithril": 4, "topaz": 3},
    "invisible_ring": {"lead": 4, "ruby": 2, "topaz": 3},
    "ender_earrings": {"lead": 5, "ruby": 4},
    "living_bracelet": {"silver_ore": 5, "diamond": 3},
    "dragon_pendant": {"silver_ore": 4, "garnet": 4, "diamond": 3},
    "time_ring": {"platinum": 5, "tanzanite": 3, "garnet": 4},
    "mushroom_crown": {"platinum": 4, "onyx": 4, "tanzanite": 3},
    "black_sun_amulet": {"titanite": 5, "onyx": 4, "garnet": 4},
    "bat_earrings": {"titanite": 4, "onyx": 5, "moonstone": 2},
    "thunder_bracelet": {"adamantite": 5, "moonstone": 3, "onyx": 4},
    "void_ring": {"adamantite": 4, "moonstone": 5, "onyx": 5},
    "moon_pendant": {"adamantite": 5, "star_metal": 3, "moonstone": 5},
    "lost_soul_amulet": {"star_metal": 5, "moonstone": 6, "onyx": 5},
    "night_flower_pendant": {"star_metal": 6, "moonstone": 8, "onyx": 6},
    "forgotten_god": {"star_metal": 10, "moonstone": 10, "onyx": 8, "adamantite": 8},
}

# ============ РЕЦЕПТЫ ЗЕЛИЙ ============
RECIPES_POTIONS = {
    "moon_light": {"storm_kelp": 3, "salt_crystal": 1},
    "shadow_form": {"salt_crystal": 3, "thunder_pearl": 1},
    "ceiling_walk": {"thunder_pearl": 3, "fire_flower": 1},
    "mob_invisibility": {"fire_flower": 3, "glow_moss": 1},
    "block_jump": {"glow_moss": 3, "blood_rose": 1},
    "stone_skin": {"blood_rose": 3, "void_flower": 1},
    "animal_talk": {"void_flower": 3, "ender_orchid": 1},
    "reverse_aging": {"ender_orchid": 3, "black_sakura": 1},
    "night_vision": {"black_sakura": 3, "star_clover": 1},
    "water_freeze": {"star_clover": 3, "moon_fern": 1},
    "lightning_call": {"moon_fern": 3, "eye_cactus": 1},
    "mushroom_growth": {"eye_cactus": 3, "whisper_tree": 1},
    "slime_form": {"whisper_tree": 3, "weeping_lily": 1},
    "lava_breath": {"weeping_lily": 3, "clock_mushroom": 1},
    "miner_luck": {"clock_mushroom": 3, "fire_ivy": 1},
    "moon_teleport": {"fire_ivy": 3, "frost_bell": 1},
    "damage_reflect": {"frost_bell": 3, "soul_tree": 1},
    "time_slow": {"soul_tree": 3, "teleport_liana": 1},
    "ghost_form": {"teleport_liana": 3, "predator_plant": 1},
    "random_effect": {"predator_plant": 3, "star_clover": 2},
}

# ============ РЕЦЕПТЫ БЕЗДНЫ ============
RECIPES_VOID = {
    "void_blade": {"void_heart": 1, "void_shard": 50, "void_soul": 100, "base_item": "legend"},
    "void_armor": {"void_heart": 1, "void_shard": 50, "void_soul": 100, "base_item": "mirror_knight"},
    "void_amulet": {"void_heart": 1, "void_shard": 50, "void_soul": 100, "base_item": "forgotten_god"},
}

# ============ ОБЩИЕ РЕЦЕПТЫ ============
RECIPES = {}
for k, v in RECIPES_WEAPONS.items():
    if k in WEAPONS:
        RECIPES[k] = {"name": WEAPONS[k]["name"], "prof": "smith", "level": WEAPONS[k]["level"], "ore": v}
for k, v in RECIPES_ARMORS.items():
    if k in ARMORS:
        RECIPES[k] = {"name": ARMORS[k]["name"], "prof": "armorer", "level": ARMORS[k]["level"], "ore": v}
for k, v in RECIPES_ACCESSORIES.items():
    if k in ACCESSORIES:
        RECIPES[k] = {"name": ACCESSORIES[k]["name"], "prof": "jeweler", "level": ACCESSORIES[k]["level"], "ore": v}
for k, v in RECIPES_POTIONS.items():
    if k in POTIONS:
        RECIPES[k] = {"name": POTIONS[k]["name"], "prof": "alchemist", "level": POTIONS[k]["level"], "herb": v}

# ============ ПРОФЕССИИ ============
PROFESSIONS = {
    "smith": "⚒️ Кузнец",
    "armorer": "🛡 Бронник",
    "jeweler": "💎 Ювелир",
    "alchemist": "⚗️ Алхимик",
    "miner": "⛏ Шахтёр",
}

# ============ ОПЫТ ПРОФЕССИЙ ============
def prof_exp_needed(level):
    return 50 + level * 20

def total_prof_exp(level):
    total = 0
    for i in range(1, level):
        total += prof_exp_needed(i)
    return total

# ============ БОНУС ШАХТЁРА ============
def miner_bonus(level):
    if level <= 10:
        return level
    elif level <= 30:
        return 10 + (level - 10) // 2
    elif level <= 60:
        return 20 + (level - 30) // 3
    else:
        return 30 + (level - 60) // 4

MINER_BONUS = {i: miner_bonus(i) for i in range(1, 101)}

# ============ МОБЫ ============
MOB_NAMES = [
    "🐀 Крыса", "🦇 Летучая мышь", "🐺 Волк", "🐗 Кабан", "🐻 Медведь",
    "🦂 Скорпион", "🕷 Паук", "🐍 Змея", "🦊 Лиса", "🐆 Леопард",
    "🐊 Крокодил", "🦅 Орёл", "🐉 Дракончик", "👹 Гоблин", "🧟 Зомби",
    "🦌 Олень", "🐗 Дикий кабан", "🦍 Горилла", "🐅 Тигр", "🦏 Носорог",
    "👾 Лунный пожиратель", "💎 Кристальный голем", "🦊 Теневой лис",
    "🍄 Грибной рыцарь", "🌌 Пустотный скиталец", "📦 Мимик-сундук",
    "🏮 Болотный фонарщик", "🪞 Зеркальный двойник", "🪱 Пещерный пожиратель",
    "🔥 Огненный ворон", "❄️ Ледяная ведьма", "🏘 Деревенька-бродяга",
    "🦋 Эндер-бабочка", "🎭 Кукольник", "🌸 Глазастый цветок",
    "🌩 Грозовой олень", "🐉 Костяной дракончик", "🏜 Песочный призрак",
    "👑 Король слизней", "🌑 Чёрная луна",
]

MYSTIC_NAMES = [
    "🌟 Мистический волк", "🌟 Мистический медведь", "🌟 Мистический дракон",
    "🌟 Мистический феникс", "🌟 Мистический единорог",
]

BOSS_NAMES = [
    "👑 Владыка этажа", "💀 Король мертвых", "🐲 Древний дракон",
    "👺 Повелитель демонов", "🧙 Архимаг", "🦁 Царь зверей",
    "🐙 Кракен", "🔥 Владыка огня", "❄️ Ледяной король",
    "⚡ Повелитель гроз", "🌑 Тёмный лорд", "🕷 Королева пауков",
    "🐉 Древний вирм", "👹 Демон бездны", "💎 Кристальный титан",
    "🌪 Владыка ветров", "🌊 Морской царь", "🏔 Горный гигант",
    "🦅 Владыка небес", "🐺 Альфа-волк", "🌋 Огненный голем",
    "👻 Король призраков", "🌌 Владыка пустоты", "💀 Смерть",
    "👑 Верховный бог",
]

# ============ НАГРАДЫ ЗА ЭТАЖ ============
FLOOR_REWARDS = {
    1: {"silver": 500, "exp": 100}, 2: {"silver": 1000, "exp": 200},
    3: {"silver": 2000, "exp": 400}, 4: {"silver": 4000, "exp": 800},
    5: {"silver": 8000, "exp": 1600}, 6: {"silver": 16000, "exp": 3200},
    7: {"silver": 32000, "exp": 6400}, 8: {"silver": 64000, "exp": 12800},
    9: {"silver": 128000, "exp": 25600}, 10: {"silver": 256000, "exp": 51200},
}

# ============ ШАНСЫ РЕСУРСОВ ============
def ore_chances(miner_level):
    if miner_level <= 10:
        return {"copper": 70, "iron": 25, "gold": 5}
    elif miner_level <= 30:
        return {"copper": 50, "iron": 30, "gold": 15, "mithril": 5}
    elif miner_level <= 60:
        return {"copper": 30, "iron": 30, "gold": 25, "mithril": 10, "lead": 5}
    elif miner_level <= 90:
        return {"copper": 15, "iron": 25, "gold": 25, "mithril": 15, "lead": 12, "silver_ore": 6, "platinum": 2}
    else:
        return {"copper": 8, "iron": 17, "gold": 25, "mithril": 18, "lead": 15, "silver_ore": 10, "platinum": 5, "titanite": 1.5, "adamantite": 0.4, "star_metal": 0.1}

def gem_chances(miner_level):
    if miner_level <= 10:
        return {"emerald": 70, "sapphire": 25, "amethyst": 5}
    elif miner_level <= 30:
        return {"emerald": 50, "sapphire": 30, "amethyst": 15, "topaz": 5}
    elif miner_level <= 60:
        return {"emerald": 30, "sapphire": 30, "amethyst": 25, "topaz": 10, "ruby": 5}
    elif miner_level <= 90:
        return {"emerald": 15, "sapphire": 25, "amethyst": 25, "topaz": 15, "ruby": 12, "diamond": 6, "garnet": 2}
    else:
        return {"emerald": 8, "sapphire": 17, "amethyst": 25, "topaz": 18, "ruby": 15, "diamond": 10, "garnet": 5, "tanzanite": 1.5, "onyx": 0.4, "moonstone": 0.1}

def pick_weighted(chances):
    roll = random.random() * 100
    acc = 0
    for key, weight in chances.items():
        acc += weight
        if roll < acc:
            return key
    return list(chances.keys())[-1]

def roll_amount():
    roll = random.random() * 100
    if roll < 73.5:
        return random.randint(1, 5)
    elif roll < 93.5:
        return random.randint(6, 10)
    elif roll < 98.5:
        return random.randint(11, 20)
    elif roll < 99.4:
        return random.randint(21, 35)
    elif roll < 99.9:
        return random.randint(36, 49)
    return 50

# ============ БАФФЫ ============
BUFFS = {
    "crit25": {"name": "+25% крит", "crit": 25},
    "dmg25": {"name": "+25% урон", "dmg": 25},
    "agi25": {"name": "+25% ловкость", "agi": 25},
    "hp50_def30_heal10": {"name": "+50% HP, +30% защ, 10% хил", "hp": 50, "def": 30, "heal": 10},
    "hp60_def40_absorb20": {"name": "+60% HP, +40% защ, 20% впит", "hp": 60, "def": 40, "absorb": 20},
    "exp25": {"name": "+25% опыт", "exp": 25},
    "silver25": {"name": "+25% серебро", "silver": 25},
    "dmg50_agi15": {"name": "+50% урон, +15% ловк", "dmg": 50, "agi": 15},
    "dmg10": {"name": "+10% урон", "dmg": 10},
    "dmg15": {"name": "+15% урон", "dmg": 15},
    "dmg20": {"name": "+20% урон", "dmg": 20},
    "crit10": {"name": "+10% крит", "crit": 10},
    "crit15": {"name": "+15% крит", "crit": 15},
    "hp10": {"name": "+10% HP", "hp": 10},
    "hp15": {"name": "+15% HP", "hp": 15},
    "hp20": {"name": "+20% HP", "hp": 20},
    "agi10": {"name": "+10% ловкость", "agi": 10},
    "agi15": {"name": "+15% ловкость", "agi": 15},
    "exp10": {"name": "+10% опыт", "exp": 10},
    "exp15": {"name": "+15% опыт", "exp": 15},
    "silver10": {"name": "+10% серебро", "silver": 10},
    "silver15": {"name": "+15% серебро", "silver": 15},
    "heal5_20": {"name": "5% шанс отхила 20% урона", "heal": 5, "heal_pct": 20},
    "poison15": {"name": "15% шанс яда", "poison": 15},
}

# ============ СУНДУКИ ============
CHEST_TYPES = {
    "common": {
        "name": "🎁 Обычный сундук",
        "tier": "E",
        "secret_chance": 3,
        "pet_chance": 10,
        "silver": 5000,
    },
    "rare": {
        "name": "💎 Редкий сундук",
        "tier": "SS",
        "secret_chance": 8,
        "pet_chance": 25,
        "silver": 25000,
    },
    "legend": {
        "name": "👑 Легендарный сундук",
        "tier": "SSS",
        "secret_chance": 100,
        "pet_chance": 100,
        "silver": 200000,
    },
}

SECRET_ITEMS = [
    "demon_mace",
    "dragon_katana",
    "blood_spear",
    "god_flesh",
    "eternity_ring",
    "demon_crown",
]

PET_POOL = ["wolf", "dragon", "phoenix", "unicorn", "demon"]

CHEST_RESOURCES = {
    "common": {
        "ore": ["copper", "iron", "gold"],
        "count_min": 5, "count_max": 10,
        "meat": 2,
        "void_shard": 1,
    },
    "rare": {
        "ore": ["mithril", "lead", "silver_ore"],
        "count_min": 10, "count_max": 20,
        "meat": 5,
        "void_shard": 3,
    },
    "legend": {
        "ore": ["platinum", "titanite", "adamantite", "star_metal"],
        "count_min": 20, "count_max": 40,
        "meat": 10,
        "void_shard": 10,
    },
}


# ============ ПИТОМЦЫ (для battle.py) ============
PET_TYPES = {
    "wolf":    {"name": "🐺 Волк",           "dmg": 50,   "evo": "🌑 Теневой волк",         "evo_dmg": 150},
    "dragon":  {"name": "🐉 Дракон",         "dmg": 150,  "evo": "🐲 Небесный дракон",      "evo_dmg": 400},
    "phoenix": {"name": "🔥 Феникс",         "dmg": 300,  "evo": "🌋 Алый феникс",          "evo_dmg": 750},
    "unicorn": {"name": "🦄 Единорог",       "dmg": 500,  "evo": "🌸 Единорог-хранитель",   "evo_dmg": 1200},
    "demon":   {"name": "👹 Демон",          "dmg": 1000, "evo": "🩸 Демон крови",          "evo_dmg": 2500},
}
