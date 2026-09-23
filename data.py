import random

# ============ РУДА (10) ============
ORES = {
    "copper": {"name": "🟠 Медь", "price": 30, "level": 1},
    "iron": {"name": "⚙️ Железо", "price": 80, "level": 2},
    "gold": {"name": "🟡 Золото", "price": 200, "level": 3},
    "mithril": {"name": "💠 Мифрил", "price": 800, "level": 4},
    "lead": {"name": "⚫ Свинец", "price": 1500, "level": 5},
    "silver_ore": {"name": "🔘 Серебро", "price": 3000, "level": 6},
    "platinum": {"name": "🔶 Платина", "price": 6000, "level": 7},
    "titanite": {"name": "🟣 Титанит", "price": 12000, "level": 8},
    "adamantite": {"name": "🔷 Адамантит", "price": 25000, "level": 9},
    "star_metal": {"name": "🌌 Звёздный металл", "price": 50000, "level": 10},
}

ORE_TIER = {
    "copper": "E", "iron": "D", "gold": "C", "mithril": "B", "lead": "A",
    "silver_ore": "S", "platinum": "SS", "titanite": "SSS",
    "adamantite": "SSS+", "star_metal": "SSS+",
}

ORE_EXP = {
    "copper": 2, "iron": 4, "gold": 8, "mithril": 14, "lead": 24,
    "silver_ore": 36, "platinum": 50, "titanite": 350,
    "adamantite": 500, "star_metal": 750,
}

# ============ САМОЦВЕТЫ (10) ============
GEMS = {
    "emerald": {"name": "🟢 Изумруд", "price": 100, "level": 1},
    "sapphire": {"name": "🔵 Сапфир", "price": 300, "level": 2},
    "amethyst": {"name": "🟣 Аметист", "price": 600, "level": 3},
    "topaz": {"name": "🟡 Топаз", "price": 1200, "level": 4},
    "ruby": {"name": "🔴 Рубин", "price": 2500, "level": 5},
    "diamond": {"name": "⚪ Алмаз", "price": 5000, "level": 6},
    "garnet": {"name": "🟠 Гранат", "price": 8000, "level": 7},
    "tanzanite": {"name": "💜 Танзанит", "price": 12000, "level": 8},
    "onyx": {"name": "🖤 Оникс", "price": 20000, "level": 9},
    "moonstone": {"name": "💎 Лунный камень", "price": 35000, "level": 10},
}

GEM_TIER = {
    "emerald": "E", "sapphire": "D", "amethyst": "C", "topaz": "B",
    "ruby": "A", "diamond": "S", "garnet": "SS", "tanzanite": "SSS",
    "onyx": "SSS", "moonstone": "SSS+",
}

GEM_EXP = {
    "emerald": 4, "sapphire": 8, "amethyst": 16, "topaz": 28,
    "ruby": 96, "diamond": 144, "garnet": 200, "tanzanite": 700,
    "onyx": 900, "moonstone": 1200,
}

# ============ ТРАВЫ (20) ============
HERBS = {
    "storm_kelp": {"name": "🌿 Штормовой келп", "price": 50, "level": 1},
    "salt_crystal": {"name": "🪨 Кристалл соли", "price": 100, "level": 2},
    "thunder_pearl": {"name": "⚡ Громовая жемчужина", "price": 300, "level": 3},
    "fire_flower": {"name": "🔥 Огнецвет", "price": 500, "level": 4},
    "glow_moss": {"name": "🍄 Светящийся мох", "price": 800, "level": 5},
    "blood_rose": {"name": "🌸 Кровавая роза", "price": 1200, "level": 6},
    "void_flower": {"name": "🌺 Цветок пустоты", "price": 1800, "level": 7},
    "ender_orchid": {"name": "🌷 Эндер-орхидея", "price": 2500, "level": 8},
    "black_sakura": {"name": "🥀 Чёрная сакура", "price": 4000, "level": 9},
    "star_clover": {"name": "🌟 Звёздный клевер", "price": 6000, "level": 10},
    "moon_fern": {"name": "🌙 Лунный папоротник", "price": 9000, "level": 11},
    "eye_cactus": {"name": "👁 Глазастый кактус", "price": 13000, "level": 12},
    "whisper_tree": {"name": "🌲 Дерево шёпота", "price": 18000, "level": 13},
    "weeping_lily": {"name": "🌺 Плачущая лилия", "price": 24000, "level": 14},
    "clock_mushroom": {"name": "🍄 Гриб-часовщик", "price": 32000, "level": 15},
    "fire_ivy": {"name": "🔥 Огненный плющ", "price": 42000, "level": 16},
    "frost_bell": {"name": "❄️ Морозный колокольчик", "price": 55000, "level": 17},
    "soul_tree": {"name": "🌳 Дерево душ", "price": 70000, "level": 18},
    "teleport_liana": {"name": "🌿 Лиана-телепорт", "price": 90000, "level": 19},
    "predator_plant": {"name": "🌱 Растение-хищник", "price": 120000, "level": 20},
}

# ============ ЛУТ (20) ============
MOB_LOOT = {
    "wolf_fang": {"name": "🦷 Клык волка", "price": 40},
    "spider_web": {"name": "🕸 Паутина", "price": 80},
    "scorpion_sting": {"name": "🦂 Жало скорпиона", "price": 150},
    "bear_claw": {"name": "🐻 Коготь медведя", "price": 250},
    "skeleton_bone": {"name": "💀 Кость скелета", "price": 400},
    "hunter_eye": {"name": "👁 Глаз ночного охотника", "price": 700},
    "dragon_scale": {"name": "🐉 Чешуя дракона", "price": 1200},
    "golem_heart": {"name": "❤️ Сердце голема", "price": 2000},
    "phoenix_feather": {"name": "🦅 Перо феникса", "price": 3500},
    "black_moon_shard": {"name": "🌑 Осколок чёрной луны", "price": 6000},
    "void_fang": {"name": "🦷 Клык пустотника", "price": 9000},
    "thunder_horn": {"name": "📯 Рог громового зверя", "price": 14000},
    "sky_feather": {"name": "🪶 Перо небесного моба", "price": 20000},
    "shadow_claw": {"name": "🐾 Коготь теневого волка", "price": 28000},
    "mini_dragon_scale": {"name": "🐲 Чешуя мини-дракона", "price": 40000},
    "poison_sting": {"name": "🐝 Жало ядовитой пчелы", "price": 55000},
    "mushroom_skull": {"name": "💀 Череп грибного монстра", "price": 75000},
    "chameleon_slime": {"name": "🟢 Слизь-хамелеон", "price": 100000},
    "lava_heart": {"name": "🔥 Сердце лавового слизня", "price": 140000},
    "ghost_raven_feather": {"name": "🖤 Чёрное перо ворона-призрака", "price": 200000},
}

# ============ РЕСУРСЫ БЕЗДНЫ ============
VOID_HEART = {"name": "🖤 Сердце бездны", "price": 5000000}
VOID_SHARD = {"name": "💠 Осколок бездны", "price": 500000}
VOID_SOUL = {"name": "🕯 Бездонная душа", "price": 100000}

# ============ ОРУЖИЕ (23) ============
WEAPONS = {
    "fists": {"name": "👊 Кулаки", "dmg": 5, "level": 0},
    "sword": {"name": "🗡 Меч", "dmg": 15, "level": 1},
    "knife": {"name": "🔪 Нож", "dmg": 20, "level": 2},
    "dagger": {"name": "🗡 Кинжал", "dmg": 25, "level": 3},
    "axe": {"name": "🪓 Топор", "dmg": 35, "level": 4},
    "spear": {"name": "🔱 Копьё", "dmg": 50, "level": 5},
    "revolver": {"name": "🔫 Револьвер", "dmg": 70, "level": 6},
    "magic": {"name": "🔮 Посох", "dmg": 90, "level": 7},
    "scythe_moon": {"name": "🌙 Коса лунного жнеца", "dmg": 130, "level": 8},
    "parasite_pick": {"name": "🪱 Кирка-паразит", "dmg": 180, "level": 9},
    "twisted_shovel": {"name": "⛏ Лопата искривлённой земли", "dmg": 240, "level": 10},
    "soul_hoe": {"name": "⚒ Мотыга садовника душ", "dmg": 320, "level": 12},
    "thunder_axe": {"name": "🪓 Топор громового дерева", "dmg": 420, "level": 14},
    "void_pick": {"name": "⚫ Кирка пустотного кристалла", "dmg": 550, "level": 16},
    "ice_drill": {"name": "❄️ Ледяной бур", "dmg": 700, "level": 18},
    "meteor_hammer": {"name": "☄️ Кувалда метеорита", "dmg": 900, "level": 20},
    "root_staff": {"name": "🌿 Посох корней", "dmg": 1150, "level": 25},
    "blood_sickle": {"name": "🌹 Серп кровавой розы", "dmg": 1450, "level": 30},
    "spirit_hammer": {"name": "🔨 Молот кузнечного духа", "dmg": 1800, "level": 35},
    "portal_shovel": {"name": "🌀 Лопата-портал", "dmg": 2200, "level": 40},
    "golden_trident": {"name": "🔱 Золотой трезубец", "dmg": 2700, "level": 45},
    "miner_claw": {"name": "🦾 Коготь шахтёра", "dmg": 3300, "level": 50},
    "time_pick": {"name": "⏳ Кирка времени", "dmg": 4000, "level": 60},
    "living_axe": {"name": "🪓 Топор с живым лезвием", "dmg": 4800, "level": 70},
    "eternal_hoe": {"name": "🌾 Мотыга вечной жатвы", "dmg": 5800, "level": 85},
    "legend": {"name": "⚔️ Легендарный клинок", "dmg": 7000, "level": 100},
    # СЕКРЕТНЫЕ (с боссов)
    "demon_mace": {"name": "🔨 Булава кровавого демона", "dmg": 35000, "level": 0, "buff": "crit25"},
    "dragon_katana": {"name": "🗡 Катана дракона", "dmg": 38000, "level": 0, "buff": "dmg25"},
    # БЕЗДНА
    "void_blade": {"name": "⚔️ Клинок бездны", "dmg": 40000, "level": 0, "buff": "agi25", "void": True},
}

# ============ БРОНЯ (20) ============
ARMORS = {
    "none": {"name": "🚫 Без брони", "def": 0, "level": 0},
    "leather": {"name": "🧥 Кожаная", "def": 3, "level": 1},
    "chain": {"name": "⛓ Кольчуга", "def": 8, "level": 3},
    "plate": {"name": "🛡 Латная", "def": 15, "level": 5},
    "dragon": {"name": "🐲 Драконья", "def": 25, "level": 8},
    "titan": {"name": "⚡ Титановая", "def": 40, "level": 12},
    "moon_knight": {"name": "🌙 Доспехи лунного рыцаря", "def": 60, "level": 16},
    "kraken_shell": {"name": "🐙 Броня из панцирей кракена", "def": 85, "level": 20},
    "forest_spirit": {"name": "🌲 Комплект лесного духа", "def": 115, "level": 25},
    "void_armor_old": {"name": "⚫ Доспехи пустотника", "def": 150, "level": 30},
    "crystal_golem": {"name": "💎 Броня кристального голема", "def": 195, "level": 35},
    "thunder_guard": {"name": "⚡ Комплект грозового стража", "def": 250, "level": 40},
    "ice_demon": {"name": "❄️ Доспехи ледяного демона", "def": 320, "level": 45},
    "mushroom_king": {"name": "🍄 Броня грибного короля", "def": 400, "level": 50},
    "sand_ghost": {"name": "🏜 Комплект песчаного призрака", "def": 500, "level": 55},
    "black_rose": {"name": "🌹 Доспехи чёрной розы", "def": 620, "level": 60},
    "dragon_heart": {"name": "🐉 Броня драконьего сердца", "def": 780, "level": 70},
    "sky_smith": {"name": "☁️ Доспехи небесного кузнеца", "def": 980, "level": 80},
    "dead_forest": {"name": "💀 Доспехи мёртвого леса", "def": 1250, "level": 90},
    "mirror_knight": {"name": "🪞 Броня зеркального рыцаря", "def": 1600, "level": 100},
    # СЕКРЕТНАЯ (с боссов)
    "god_flesh": {"name": "🩸 Броня из плоти бога", "def": 4000, "level": 0, "buff": "hp50_def30_heal10"},
    # БЕЗДНА
    "void_armor": {"name": "⚫ Броня бездны", "def": 4400, "level": 0, "buff": "hp60_def40_absorb20", "void": True},
}

# ============ БИЖУТЕРИЯ (20) ============
ACCESSORIES = {
    "none": {"name": "🚫 Нет", "bonus": 0, "level": 0},
    "ring_copper": {"name": "💍 Медное кольцо", "bonus": 5, "level": 1},
    "ring_iron": {"name": "💍 Железное кольцо", "bonus": 10, "level": 3},
    "amulet_gold": {"name": "📿 Золотой амулет", "bonus": 20, "level": 5},
    "ring_mithril": {"name": "💍 Мифриловое кольцо", "bonus": 35, "level": 8},
    "moon_necklace": {"name": "🌙 Ожерелье последней луны", "bonus": 55, "level": 12},
    "invisible_ring": {"name": "🕸 Кольцо невидимой нити", "bonus": 80, "level": 16},
    "ender_earrings": {"name": "👁 Серьги эндер-глаза", "bonus": 110, "level": 20},
    "living_bracelet": {"name": "🌿 Браслет живых корней", "bonus": 150, "level": 25},
    "dragon_pendant": {"name": "🐉 Кулон драконьего сердца", "bonus": 200, "level": 30},
    "time_ring": {"name": "⏳ Кольцо остановленного времени", "bonus": 270, "level": 35},
    "mushroom_crown": {"name": "👑 Венец грибного короля", "bonus": 360, "level": 40},
    "black_sun_amulet": {"name": "☀️ Амулет чёрного солнца", "bonus": 480, "level": 45},
    "bat_earrings": {"name": "🦇 Серьги летучей мыши", "bonus": 630, "level": 50},
    "thunder_bracelet": {"name": "⚡ Браслет грозы", "bonus": 820, "level": 55},
    "void_ring": {"name": "⚫ Кольцо пустоты", "bonus": 1080, "level": 60},
    "moon_pendant": {"name": "🌙 Кулон лунного осколка", "bonus": 1420, "level": 70},
    "lost_soul_amulet": {"name": "👻 Амулет потерянной души", "bonus": 1850, "level": 80},
    "night_flower_pendant": {"name": "🌸 Кулон цветка ночи", "bonus": 2400, "level": 90},
    "forgotten_god": {"name": "🏛 Медальон забытого бога", "bonus": 3200, "level": 100},
    # СЕКРЕТНЫЕ (с боссов)
    "eternity_ring": {"name": "💍 Кольцо вечности", "bonus": 6000, "level": 0, "buff": "exp25"},
    "demon_crown": {"name": "👑 Корона демона", "bonus": 7000, "level": 0, "buff": "dmg50_agi15"},
    # БЕЗДНА
    "void_amulet": {"name": "📿 Амулет бездны", "bonus": 6500, "level": 0, "buff": "silver25", "void": True},
}

# ============ ЗЕЛЬЯ (20) ============
POTIONS = {
    "moon_light": {"name": "🌙 Зелье лунного света", "level": 1},
    "shadow_form": {"name": "🌑 Зелье превращения в тень", "level": 2},
    "ceiling_walk": {"name": "🦶 Зелье ходьбы по потолку", "level": 3},
    "mob_invisibility": {"name": "👻 Зелье невидимости для мобов", "level": 4},
    "block_jump": {"name": "🦘 Зелье прыжка между блоками", "level": 5},
    "stone_skin": {"name": "🪨 Зелье каменной кожи", "level": 6},
    "animal_talk": {"name": "🐾 Зелье разговора с животными", "level": 7},
    "reverse_aging": {"name": "⏪ Зелье обратного старения", "level": 8},
    "night_vision": {"name": "👁 Зелье ночного зрения ×100", "level": 9},
    "water_freeze": {"name": "❄️ Зелье заморозки воды", "level": 10},
    "lightning_call": {"name": "⚡ Зелье призыва молнии", "level": 11},
    "mushroom_growth": {"name": "🍄 Зелье роста грибов", "level": 12},
    "slime_form": {"name": "🟢 Зелье превращения в слизь", "level": 13},
    "lava_breath": {"name": "🔥 Зелье дыхания в лаве", "level": 14},
    "miner_luck": {"name": "🍀 Зелье удачи шахтёра", "level": 15},
    "moon_teleport": {"name": "🌙 Зелье телепортации к луне", "level": 16},
    "damage_reflect": {"name": "🛡 Зелье отражения урона", "level": 17},
    "time_slow": {"name": "⏳ Зелье замедления времени", "level": 18},
    "ghost_form": {"name": "👻 Зелье превращения в призрака", "level": 19},
    "random_effect": {"name": "🎲 Зелье случайного эффекта", "level": 20},
}

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

# ============ ТИРЫ ДЛЯ БАФФОВ ============
BUFFS = {
    "crit25": {"name": "+25% крит", "crit": 25},
    "dmg25": {"name": "+25% урон", "dmg": 25},
    "agi25": {"name": "+25% ловкость", "agi": 25},
    "hp50_def30_heal10": {"name": "+50% HP, +30% защ, 10% хил", "hp": 50, "def": 30, "heal": 10},
    "hp60_def40_absorb20": {"name": "+60% HP, +40% защ, 20% впит", "hp": 60, "def": 40, "absorb": 20},
    "exp25": {"name": "+25% опыт", "exp": 25},
    "silver25": {"name": "+25% серебро", "silver": 25},
    "dmg50_agi15": {"name": "+50% урон, +15% ловк", "dmg": 50, "agi": 15},
}
