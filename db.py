import sqlite3
from data import PROF_EXP

DB = "rpg.db"

FIELDS = [
    "uid", "name", "level", "exp", "hp", "max_hp", "silver", "floor",
    "mob_kill", "keys", "strength", "agility", "vitality", "stat_points",
    "weapon", "armor", "accessory",
    "prof_smith", "prof_armorer", "prof_jeweler", "prof_alchemist", "prof_miner",
    "exp_smith", "exp_armorer", "exp_jeweler", "exp_alchemist", "exp_miner",
    "energy", "max_energy", "last_energy_time",
    "copper", "iron", "gold", "mithril", "gem",
    "storm_kelp", "salt_crystal", "thunder_pearl", "fire_flower",
    "hp_small", "hp_big", "str_potion", "def_potion",
    "kills", "mine_count", "boss_kills",
    "crafted_items",
    "auto_mine_active", "auto_mine_started", "auto_mine_last_collect",
    "auto_mine_copper", "auto_mine_iron", "auto_mine_gold",
    "auto_mine_mithril", "auto_mine_gem",
]

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS players (
        uid INTEGER PRIMARY KEY,
        name TEXT,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        silver INTEGER DEFAULT 150,
        floor INTEGER DEFAULT 1,
        mob_kill INTEGER DEFAULT 0,
        keys INTEGER DEFAULT 0,
        strength INTEGER DEFAULT 0,
        agility INTEGER DEFAULT 0,
        vitality INTEGER DEFAULT 0,
        stat_points INTEGER DEFAULT 0,
        weapon TEXT DEFAULT 'fists',
        armor TEXT DEFAULT 'none',
        accessory TEXT DEFAULT 'none',
        prof_smith INTEGER DEFAULT 1,
        prof_armorer INTEGER DEFAULT 1,
        prof_jeweler INTEGER DEFAULT 1,
        prof_alchemist INTEGER DEFAULT 1,
        prof_miner INTEGER DEFAULT 1,
        exp_smith INTEGER DEFAULT 0,
        exp_armorer INTEGER DEFAULT 0,
        exp_jeweler INTEGER DEFAULT 0,
        exp_alchemist INTEGER DEFAULT 0,
        exp_miner INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 250,
        max_energy INTEGER DEFAULT 250,
        last_energy_time REAL DEFAULT 0,
        copper INTEGER DEFAULT 0,
        iron INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 0,
        mithril INTEGER DEFAULT 0,
        gem INTEGER DEFAULT 0,
        storm_kelp INTEGER DEFAULT 0,
        salt_crystal INTEGER DEFAULT 0,
        thunder_pearl INTEGER DEFAULT 0,
        fire_flower INTEGER DEFAULT 0,
        hp_small INTEGER DEFAULT 0,
        hp_big INTEGER DEFAULT 0,
        str_potion INTEGER DEFAULT 0,
        def_potion INTEGER DEFAULT 0,
        kills INTEGER DEFAULT 0,
        mine_count INTEGER DEFAULT 0,
        boss_kills INTEGER DEFAULT 0,
        crafted_items TEXT DEFAULT '[]',
        auto_mine_active INTEGER DEFAULT 0,
        auto_mine_started REAL DEFAULT 0,
        auto_mine_last_collect REAL DEFAULT 0,
        auto_mine_copper INTEGER DEFAULT 0,
        auto_mine_iron INTEGER DEFAULT 0,
        auto_mine_gold INTEGER DEFAULT 0,
        auto_mine_mithril INTEGER DEFAULT 0,
        auto_mine_gem INTEGER DEFAULT 0
    )""")

    # Миграция: добавляем новые поля, если их нет
    migrations = [
        ("prof_miner", "INTEGER DEFAULT 1"),
        ("exp_miner", "INTEGER DEFAULT 0"),
        ("auto_mine_active", "INTEGER DEFAULT 0"),
        ("auto_mine_started", "REAL DEFAULT 0"),
        ("auto_mine_last_collect", "REAL DEFAULT 0"),
        ("auto_mine_copper", "INTEGER DEFAULT 0"),
        ("auto_mine_iron", "INTEGER DEFAULT 0"),
        ("auto_mine_gold", "INTEGER DEFAULT 0"),
        ("auto_mine_mithril", "INTEGER DEFAULT 0"),
        ("auto_mine_gem", "INTEGER DEFAULT 0"),
    ]
    for col, definition in migrations:
        try:
            c.execute(f"ALTER TABLE players ADD COLUMN {col} {definition}")
        except:
            pass

    conn.commit()
    conn.close()

def get_player(uid, name="Игрок"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE uid=?", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO players (uid, name) VALUES (?, ?)", (uid, name))
        conn.commit()
        c.execute("SELECT * FROM players WHERE uid=?", (uid,))
        row = c.fetchone()
    conn.close()
    return dict(zip(FIELDS, row))

def save_player(p):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    placeholders = ", ".join(f"{f}=?" for f in FIELDS if f != "uid")
    values = [p[f] for f in FIELDS if f != "uid"]
    values.append(p["uid"])
    c.execute(f"UPDATE players SET {placeholders} WHERE uid=?", values)
    conn.commit()
    conn.close()

def exp_needed(level):
    return 50 + level * 30

def prof_level_for_exp(exp):
    lvl = 1
    for l, need in sorted(PROF_EXP.items()):
        if exp >= need:
            lvl = l
    return lvl

def prof_next_exp(exp):
    for l, need in sorted(PROF_EXP.items()):
        if exp < need:
            return need
    return None
