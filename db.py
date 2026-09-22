import os
import psycopg2
from data import prof_exp_needed, total_prof_exp

DATABASE_URL = os.environ.get("DATABASE_URL")

ORES_LIST = ["copper", "iron", "gold", "mithril", "lead", "silver_ore",
             "platinum", "titanite", "adamantite", "star_metal"]
GEMS_LIST = ["emerald", "sapphire", "amethyst", "topaz", "ruby",
             "diamond", "garnet", "tanzanite", "onyx", "moonstone"]
HERBS_LIST = ["storm_kelp", "salt_crystal", "thunder_pearl", "fire_flower",
              "glow_moss", "blood_rose", "void_flower", "ender_orchid",
              "black_sakura", "star_clover", "moon_fern", "eye_cactus",
              "whisper_tree", "weeping_lily", "clock_mushroom", "fire_ivy",
              "frost_bell", "soul_tree", "teleport_liana", "predator_plant"]
LOOT_LIST = ["wolf_fang", "spider_web", "scorpion_sting", "bear_claw",
             "skeleton_bone", "hunter_eye", "dragon_scale", "golem_heart",
             "phoenix_feather", "black_moon_shard", "void_fang", "thunder_horn",
             "sky_feather", "shadow_claw", "mini_dragon_scale", "poison_sting",
             "mushroom_skull", "chameleon_slime", "lava_heart", "ghost_raven_feather"]

# Поля auto_mine_* для авто-шахты
AUTO_MINE_LIST = [f"auto_mine_{r}" for r in ORES_LIST + GEMS_LIST]

FIELDS = (
    ["uid", "name", "level", "exp", "hp", "max_hp", "silver", "floor",
     "mob_kill", "keys", "strength", "agility", "vitality", "stat_points",
     "weapon", "armor", "accessory",
     "prof_smith", "prof_armorer", "prof_jeweler", "prof_alchemist", "prof_miner",
     "exp_smith", "exp_armorer", "exp_jeweler", "exp_alchemist", "exp_miner",
     "energy", "max_energy", "last_energy_time",
     "hp_small", "hp_big", "str_potion", "def_potion",
     "kills", "mine_count", "boss_kills",
     "crafted_items",
     "auto_mine_active", "auto_mine_started", "auto_mine_last_collect"]
    + ORES_LIST + GEMS_LIST + HERBS_LIST + LOOT_LIST
    + AUTO_MINE_LIST
)

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def _build_create_sql():
    parts = [
        "uid BIGINT PRIMARY KEY", "name TEXT",
        "level INTEGER DEFAULT 1", "exp INTEGER DEFAULT 0",
        "hp INTEGER DEFAULT 100", "max_hp INTEGER DEFAULT 100",
        "silver BIGINT DEFAULT 150", "floor INTEGER DEFAULT 1",
        "mob_kill INTEGER DEFAULT 0", "keys INTEGER DEFAULT 0",
        "strength INTEGER DEFAULT 0", "agility INTEGER DEFAULT 0",
        "vitality INTEGER DEFAULT 0", "stat_points INTEGER DEFAULT 0",
        "weapon TEXT DEFAULT 'fists'", "armor TEXT DEFAULT 'none'",
        "accessory TEXT DEFAULT 'none'",
        "prof_smith INTEGER DEFAULT 1", "prof_armorer INTEGER DEFAULT 1",
        "prof_jeweler INTEGER DEFAULT 1", "prof_alchemist INTEGER DEFAULT 1",
        "prof_miner INTEGER DEFAULT 1",
        "exp_smith INTEGER DEFAULT 0", "exp_armorer INTEGER DEFAULT 0",
        "exp_jeweler INTEGER DEFAULT 0", "exp_alchemist INTEGER DEFAULT 0",
        "exp_miner INTEGER DEFAULT 0",
        "energy INTEGER DEFAULT 250", "max_energy INTEGER DEFAULT 250",
        "last_energy_time DOUBLE PRECISION DEFAULT 0",
        "hp_small INTEGER DEFAULT 0", "hp_big INTEGER DEFAULT 0",
        "str_potion INTEGER DEFAULT 0", "def_potion INTEGER DEFAULT 0",
        "kills INTEGER DEFAULT 0", "mine_count INTEGER DEFAULT 0",
        "boss_kills INTEGER DEFAULT 0",
        "crafted_items TEXT DEFAULT '[]'",
        "auto_mine_active INTEGER DEFAULT 0",
        "auto_mine_started DOUBLE PRECISION DEFAULT 0",
        "auto_mine_last_collect DOUBLE PRECISION DEFAULT 0",
    ]
    for r in ORES_LIST + GEMS_LIST + HERBS_LIST + LOOT_LIST:
        parts.append(f"{r} INTEGER DEFAULT 0")
    for r in AUTO_MINE_LIST:
        parts.append(f"{r} INTEGER DEFAULT 0")
    return "CREATE TABLE IF NOT EXISTS players (" + ", ".join(parts) + ")"

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(_build_create_sql())

    migrations = [
        ("prof_miner", "INTEGER DEFAULT 1"),
        ("exp_miner", "INTEGER DEFAULT 0"),
        ("auto_mine_active", "INTEGER DEFAULT 0"),
        ("auto_mine_started", "DOUBLE PRECISION DEFAULT 0"),
        ("auto_mine_last_collect", "DOUBLE PRECISION DEFAULT 0"),
    ]
    for r in ORES_LIST + GEMS_LIST + HERBS_LIST + LOOT_LIST:
        migrations.append((r, "INTEGER DEFAULT 0"))
    for r in AUTO_MINE_LIST:
        migrations.append((r, "INTEGER DEFAULT 0"))

    for col, definition in migrations:
        try:
            c.execute(f"ALTER TABLE players ADD COLUMN {col} {definition}")
        except:
            conn.rollback()
            continue

    conn.commit()
    conn.close()

def get_player(uid, name="Игрок"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE uid=%s", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO players (uid, name) VALUES (%s, %s)", (uid, name))
        conn.commit()
        c.execute("SELECT * FROM players WHERE uid=%s", (uid,))
        row = c.fetchone()
    conn.close()
    return dict(zip(FIELDS, row))

def save_player(p):
    conn = get_conn()
    c = conn.cursor()
    placeholders = ", ".join(f"{f}=%s" for f in FIELDS if f != "uid")
    values = [p[f] for f in FIELDS if f != "uid"]
    values.append(p["uid"])
    c.execute(f"UPDATE players SET {placeholders} WHERE uid=%s", values)
    conn.commit()
    conn.close()

def exp_needed(level):
    return 50 + level * 30

def prof_level_for_exp(exp):
    lvl = 1
    total = 0
    for i in range(1, 100):
        total += prof_exp_needed(i)
        if exp >= total:
            lvl = i + 1
        else:
            break
    return min(lvl, 100)
