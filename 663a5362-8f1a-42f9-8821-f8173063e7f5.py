from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import asyncio
import base64
import copy
import html
import json
import math
import os
import random
import time
try:
    from PIL import Image
except Exception:
    Image = None
from nicegui import ui
APP_TITLE = 'MasterQuest'
ITEM_BUCKETS = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45]
RARITY_ORDER = ['Common', 'Fine', 'Rare', 'Epic', 'Mythic', 'Ancient', 'Relic', 'Ascendant', 'Legendary', 'Unspawnable']
RARITY_COLORS = {
    'Common': '#9ca3af',
    'Fine': '#34d399',
    'Rare': '#60a5fa',
    'Epic': '#a78bfa',
    'Mythic': '#f472b6',
    'Ancient': '#22d3ee',
    'Relic': '#fb923c',
    'Ascendant': '#f59e0b',
    'Legendary': '#facc15',
    'Unspawnable': '#ff7af6',
}
RARITY_STAT_COUNT = {
    'Common': 0,
    'Fine': 1,
    'Rare': 2,
    'Epic': 3,
    'Mythic': 4,
    'Ancient': 5,
    'Relic': 6,
    'Ascendant': 7,
    'Legendary': 8,
    'Unspawnable': 4,
}
RARITY_BASE_WEIGHTS = {
    'Common': 0.745,
    'Fine': 0.128,
    'Rare': 0.064,
    'Epic': 0.032,
    'Mythic': 0.016,
    'Ancient': 0.008,
    'Relic': 0.004,
    'Ascendant': 0.002,
    'Legendary': 0.001,
    'Unspawnable': 0.0,
}
CORE_STAT_KEYS = ['strength', 'dexterity', 'intelligence', 'vitality']
SECONDARY_AFFIX_KEYS = [
    'crit_chance', 'crit_damage', 'armor_penetration', 'lifesteal',
    'max_health', 'life_regen', 'life_per_kill', 'evasion',
    'max_mana', 'mana_regen', 'mana_per_kill', 'magic_find', 'xp_gain',
    'thorns', 'accuracy',
]
ITEM_SUBTYPES = {
    'weapon': ['Dagger', 'Axe', 'Staff'],
    'armor': ['Light', 'Medium', 'Heavy'],
    'charm': ['Fire', 'Lightning', 'Ice'],
}
CLASS_ORDER = ['Fighter', 'Mage', 'Samurai', 'Paladin', 'Monk', 'Ninja', 'Warlock', 'Headhunter', 'Alchemist']
CASTER_CLASSES = {'Mage', 'Warlock', 'Alchemist'}
CLASS_DESCRIPTIONS = {
    'Fighter': 'Higher HP and armor. Steady physical damage.',
    'Mage': 'Higher magic damage and mana. Better magic scaling.',
    'Samurai': 'Fast duelist with crit focus.',
    'Paladin': 'Balanced holy warrior. Tankier with strong sustain.',
    'Monk': 'Agile bruiser. Fast, evasive, and steady.',
    'Ninja': 'Very fast finisher. High crit and accuracy.',
    'Warlock': 'Dark caster. High mana and heavy magic hits.',
    'Headhunter': 'Precision killer. Excellent accuracy and crits.',
    'Alchemist': 'Hybrid master. Flexible offense and utility.',
}
CLASS_MASTERQUEST_NEXT = {
    'Fighter': 'Samurai',
    'Mage': 'Samurai',
    'Samurai': 'Paladin',
    'Paladin': 'Monk',
    'Monk': 'Ninja',
    'Ninja': 'Warlock',
    'Warlock': 'Headhunter',
    'Headhunter': 'Alchemist',
}
INNKEEPER_GREETINGS = [
    'Warm firelight spills across the room. The innkeeper offers a quiet nod.',
    'Beds are few, walls are sturdy, and the soup smells better than the road.',
    'The innkeeper polishes a mug and says, "Coin buys comfort. Comfort buys tomorrow."',
    'A low hearth crackles while the innkeeper gestures toward the open rooms.',
    'The common room is calm tonight. The innkeeper taps the counter and waits for your choice.',
]

CLASS_EQUIP_RULES = {
    'Fighter': {'weapon': None, 'armor': None},
    'Mage': {'weapon': None, 'armor': None},
    'Samurai': {'weapon': {'Dagger'}, 'armor': None},
    'Paladin': {'weapon': {'Axe', 'Staff'}, 'armor': {'Medium', 'Heavy'}},
    'Monk': {'weapon': {'Staff', 'Dagger'}, 'armor': {'Light', 'Medium'}},
    'Ninja': {'weapon': {'Dagger'}, 'armor': {'Light'}},
    'Warlock': {'weapon': {'Staff'}, 'armor': {'Light', 'Medium'}},
    'Headhunter': {'weapon': {'Axe'}, 'armor': {'Medium'}},
    'Alchemist': {'weapon': set(), 'armor': {'Light'}},
}
STAT_LABELS = {
    'strength': 'STR', 'dexterity': 'DEX', 'intelligence': 'INT', 'vitality': 'VIT',
    'crit_chance': 'Crit Chance', 'crit_damage': 'Crit Damage', 'armor_penetration': 'Armor Pen',
    'lifesteal': 'Lifesteal', 'max_health': 'Max Health', 'life_regen': 'Life Regen',
    'life_per_kill': 'Life / Kill', 'evasion': 'Evasion', 'max_mana': 'Max Mana',
    'mana_regen': 'Mana Regen', 'mana_per_kill': 'Mana / Kill', 'magic_find': 'Magic Find',
    'xp_gain': 'XP Gain', 'thorns': 'Thorns', 'accuracy': 'Accuracy', 'enhanced_effect': 'Enhanced Effect',
}
STAT_ORDER = ['enhanced_effect', 'strength', 'dexterity', 'intelligence', 'vitality', 'crit_chance', 'crit_damage', 'armor_penetration', 'lifesteal', 'max_health', 'life_regen', 'life_per_kill', 'evasion', 'max_mana', 'mana_regen', 'mana_per_kill', 'magic_find', 'xp_gain', 'thorns', 'accuracy', 'attack_damage', 'mana_cost', 'physical_armor', 'magic_resistance']
ATTRIBUTE_FILTER_OPTIONS = ['All attributes'] + [STAT_LABELS.get(key, key.replace('_', ' ').title()) for key in STAT_ORDER if key in STAT_LABELS or key in {'attack_damage', 'mana_cost', 'physical_armor', 'magic_resistance'}]
ATTRIBUTE_FILTER_KEY_BY_LABEL = {STAT_LABELS.get(key, key.replace('_', ' ').title()): key for key in STAT_ORDER if key in STAT_LABELS or key in {'attack_damage', 'mana_cost', 'physical_armor', 'magic_resistance'}}
PROFICIENCY_TYPES = ['Axe', 'Dagger', 'Staff', 'Fire Charm', 'Ice Charm', 'Lightning Charm']
def empty_proficiency_levels() -> Dict[str, int]:
    return {key: 0 for key in PROFICIENCY_TYPES}
def empty_proficiency_progress() -> Dict[str, int]:
    return {key: 0 for key in PROFICIENCY_TYPES}
def get_proficiency_key(slot: str, subtype: str) -> Optional[str]:
    if slot == 'weapon' and subtype in {'Axe', 'Staff', 'Dagger'}:
        return subtype
    if slot == 'charm' and subtype in {'Fire', 'Ice', 'Lightning'}:
        return f'{subtype} Charm'
    return None
def proficiency_threshold_for_level(level: int) -> int:
    return 1000 * (level + 1)
MONSTER_ARCHETYPES = [
    {"type": "Fallen", "school": "physical", "kit": "Ragged leathers + jagged blade", "visual": "fallen", "profile": "Glass raider: quick burst, paper guard", "hp_mult": 0.78, "damage_mult": 1.10, "variance_mult": 1.75, "phys_mult": 0.55, "mres_mult": 0.55, "speed_bonus": 3, "accuracy_bonus": 0.02, "crit_bonus": 0.04, "evasion_bonus": 0.06},
    {"type": "Skeleton", "school": "physical", "kit": "Bone mail + rust spear", "visual": "skeleton", "profile": "Bone wall: huge armor, brittle to spells", "hp_mult": 1.05, "damage_mult": 0.90, "variance_mult": 0.55, "phys_mult": 2.00, "mres_mult": 0.35, "speed_bonus": -2, "accuracy_bonus": -0.03, "crit_bonus": 0.00, "evasion_bonus": 0.00},
    {"type": "Bandit", "school": "physical", "kit": "Light armor + dagger", "visual": "bandit", "profile": "Cutpurse: very fast, precise, lightly kept", "hp_mult": 0.82, "damage_mult": 1.00, "variance_mult": 1.35, "phys_mult": 0.70, "mres_mult": 0.65, "speed_bonus": 4, "accuracy_bonus": 0.06, "crit_bonus": 0.03, "evasion_bonus": 0.10},
    {"type": "Ghoul", "school": "magic", "kit": "Torn wrappings + blight lantern", "visual": "ghoul", "profile": "Carrion brute: thick life, rot-warded, low steel", "hp_mult": 1.22, "damage_mult": 0.95, "variance_mult": 1.30, "phys_mult": 0.55, "mres_mult": 1.75, "speed_bonus": -1, "accuracy_bonus": -0.01, "crit_bonus": 0.01, "evasion_bonus": 0.02},
    {"type": "Dark Wolf", "school": "physical", "kit": "Shadow pelt + iron fangs", "visual": "dark_wolf", "profile": "Pouncer: savage leaps, almost no staying power", "hp_mult": 0.74, "damage_mult": 1.06, "variance_mult": 1.85, "phys_mult": 0.35, "mres_mult": 0.55, "speed_bonus": 6, "accuracy_bonus": 0.03, "crit_bonus": 0.05, "evasion_bonus": 0.14},
    {"type": "Cultist", "school": "magic", "kit": "Ritual robes + void staff", "visual": "cultist", "profile": "Glass hexer: razor spikes, almost no armor", "hp_mult": 0.72, "damage_mult": 1.08, "variance_mult": 1.95, "phys_mult": 0.25, "mres_mult": 1.85, "speed_bonus": 1, "accuracy_bonus": 0.04, "crit_bonus": 0.04, "evasion_bonus": 0.03},
    {"type": "Cave Spider", "school": "physical", "kit": "Chitin shell + venom fangs", "visual": "cave_spider", "profile": "Skitterer: tiny life, absurd evasion, nasty bursts", "hp_mult": 0.68, "damage_mult": 0.96, "variance_mult": 1.55, "phys_mult": 0.45, "mres_mult": 0.70, "speed_bonus": 5, "accuracy_bonus": 0.02, "crit_bonus": 0.04, "evasion_bonus": 0.18},
    {"type": "Murloc", "school": "magic", "kit": "Light armor + ice charm", "visual": "murloc", "profile": "Tide shaman: zero armor, absurd magic ward", "hp_mult": 1.10, "damage_mult": 0.90, "variance_mult": 0.80, "phys_mult": 0.00, "mres_mult": 2.30, "speed_bonus": 1, "accuracy_bonus": 0.01, "crit_bonus": 0.00, "evasion_bonus": 0.05},
    {"type": "Wraith", "school": "magic", "kit": "Tattered veil + soul ember", "visual": "wraith", "profile": "Phantom: spectral guard, nearly no body", "hp_mult": 0.62, "damage_mult": 1.08, "variance_mult": 1.85, "phys_mult": 0.05, "mres_mult": 2.60, "speed_bonus": 2, "accuracy_bonus": 0.03, "crit_bonus": 0.05, "evasion_bonus": 0.15},
    {"type": "Harpy", "school": "physical", "kit": "Feather guard + talon knives", "visual": "harpy", "profile": "Razorwind: blistering speed, almost untouchable", "hp_mult": 0.76, "damage_mult": 1.00, "variance_mult": 1.65, "phys_mult": 0.40, "mres_mult": 0.75, "speed_bonus": 7, "accuracy_bonus": 0.04, "crit_bonus": 0.03, "evasion_bonus": 0.13},
    {"type": "Templar", "school": "physical", "kit": "Heavy armor + sanctified mace", "visual": "templar", "profile": "Juggernaut: huge armor and life, weak arcane guard", "hp_mult": 1.32, "damage_mult": 0.88, "variance_mult": 0.50, "phys_mult": 2.10, "mres_mult": 0.45, "speed_bonus": -3, "accuracy_bonus": -0.01, "crit_bonus": 0.00, "evasion_bonus": 0.01},
    {"type": "Bogling", "school": "physical", "kit": "Mud-hide jerkin + hooked cleaver", "visual": "bogling", "profile": "Mire lump: huge life, dull swings, low pace", "hp_mult": 1.35, "damage_mult": 0.82, "variance_mult": 0.45, "phys_mult": 1.25, "mres_mult": 0.65, "speed_bonus": -3, "accuracy_bonus": -0.04, "crit_bonus": 0.00, "evasion_bonus": 0.00},
    {"type": "Salamander", "school": "magic", "kit": "Scaled hide + fire charm", "visual": "salamander", "profile": "Ember hunter: balanced shell, hot spikes", "hp_mult": 0.88, "damage_mult": 1.04, "variance_mult": 1.55, "phys_mult": 0.70, "mres_mult": 1.45, "speed_bonus": 2, "accuracy_bonus": 0.01, "crit_bonus": 0.03, "evasion_bonus": 0.04},
    {"type": "Mire Witch", "school": "magic", "kit": "Swamp robes + lightning charm", "visual": "mire_witch", "profile": "Storm crone: tiny low rolls, savage high rolls", "hp_mult": 0.70, "damage_mult": 1.00, "variance_mult": 2.80, "phys_mult": 0.20, "mres_mult": 1.70, "speed_bonus": 1, "accuracy_bonus": -0.02, "crit_bonus": 0.05, "evasion_bonus": 0.05},
    {"type": "Hollow Knight", "school": "physical", "kit": "Medium armor + long blade", "visual": "hollow_knight", "profile": "Veteran: disciplined guard, narrow damage spread", "hp_mult": 1.14, "damage_mult": 0.98, "variance_mult": 0.75, "phys_mult": 1.55, "mres_mult": 1.20, "speed_bonus": -1, "accuracy_bonus": 0.01, "crit_bonus": 0.00, "evasion_bonus": 0.03},
    {"type": "Ravager", "school": "physical", "kit": "Heavy furs + war axe", "visual": "ravager", "profile": "Berserker: brutal average hits, rotten magic guard", "hp_mult": 0.94, "damage_mult": 1.18, "variance_mult": 1.60, "phys_mult": 0.85, "mres_mult": 0.35, "speed_bonus": 2, "accuracy_bonus": 0.00, "crit_bonus": 0.06, "evasion_bonus": 0.03},
    {"type": "Shade Archer", "school": "magic", "kit": "Light armor + frost bow", "visual": "shade_archer", "profile": "Sniper: huge range spread, deadly aim, frail body", "hp_mult": 0.66, "damage_mult": 1.04, "variance_mult": 2.10, "phys_mult": 0.25, "mres_mult": 1.05, "speed_bonus": 6, "accuracy_bonus": 0.08, "crit_bonus": 0.04, "evasion_bonus": 0.14},
    {"type": "Succubus", "school": "magic", "kit": "Silken leathers + shadow charm", "visual": "succubus", "profile": "Temptress: quick hexes, evasive frame, wicked spikes", "hp_mult": 0.78, "damage_mult": 1.06, "variance_mult": 1.90, "phys_mult": 0.30, "mres_mult": 1.45, "speed_bonus": 4, "accuracy_bonus": 0.05, "crit_bonus": 0.05, "evasion_bonus": 0.11},
]
MONSTER_NAMES = ['Graag', 'Vorin', 'Mord', 'Skarn', 'Drez', 'Khal', 'Ruk', 'Thane', 'Varg', 'Nox', 'Bram', 'Kree', 'Dusk', 'Mirek', 'Zor', 'Vell', 'Grim', 'Tark', 'Raze', 'Vorn']
MONSTER_EPITHETS = ['the Hollow', 'the Ashen', 'the Grim', 'the Dire', 'the Ragged', 'the Crooked', 'the Scarred', 'the Pale', 'the Shadowed', 'the Unquiet']
MONSTER_DIALOGUE = {
    'Fallen': ['You still think trouble gives warnings.', 'Keep those eyes on my hands. My blade prefers surprises.'],
    'Skeleton': ['Discipline refuses to die.', 'Advance. The line has room for one more mistake.'],
    'Bandit': ['You look expensive in all the ways that matter to a knife.', 'I only need one good cut.'],
    'Ghoul': ['The living always smell louder than they think.', 'Come nearer and let the dark decide how much of you stays yours.'],
    'Dark Wolf': ['The growl means I have decided.', 'Teeth first. Questions never.'],
    'Cultist': ['The candles bent toward you the moment you entered.', 'The rite can begin properly now.'],
    'Cave Spider': ['The web was here first. You are the part that arrived too late.', 'Eight eyes say run.'],
    'Murloc': ['The tide remembers every trespass.', 'The spear only finishes what the marsh already started.'],
    'Wraith': ['The dead are light until they decide to touch you.', 'You cannot parry a haunting.'],
    'Harpy': ['She smiles like gravity is a personal joke.', 'The air is mine. You are merely visiting.'],
    'Templar': ['Faith hardens slower than steel but lasts longer.', 'Stand still and be corrected.'],
    'Bogling': ['The swamp keeps what sinks.', 'Mud has patience enough to drown anything.'],
    'Salamander': ['Heat is only fear that learned to glow.', 'Ash will suit you.'],
    'Mire Witch': ['I never promise thunder. I promise possibility.', 'The swamp is choosing a number.'],
    'Hollow Knight': ['Discipline survives the corpse that learned it.', 'My blade remembers every oath you forgot.'],
    'Ravager': ['I learned follow-through.', 'Big hits solve small doubts.'],
    'Shade Archer': ['Distance is mercy for the shooter, not the shot.', 'Hold still and let the dark aim.'],
    'Succubus': ['She wears temptation like armor.', 'Come closer. Bad decisions like good company.'],
}
MONSTER_THEME_MAP = {
    'Cultist': {'rgb': '168, 85, 247', 'shell': 'rgba(31, 17, 48, 0.94)', 'deep': 'rgba(11, 8, 22, 0.99)'},
    'Wraith': {'rgb': '125, 154, 255', 'shell': 'rgba(17, 24, 48, 0.94)', 'deep': 'rgba(8, 11, 24, 0.99)'},
    'Mire Witch': {'rgb': '132, 108, 255', 'shell': 'rgba(25, 18, 52, 0.94)', 'deep': 'rgba(10, 8, 23, 0.99)'},
    'Succubus': {'rgb': '236, 72, 153', 'shell': 'rgba(45, 16, 34, 0.94)', 'deep': 'rgba(18, 8, 15, 0.99)'},
    'Harpy': {'rgb': '94, 234, 212', 'shell': 'rgba(14, 35, 39, 0.94)', 'deep': 'rgba(8, 16, 18, 0.99)'},
    'Dark Wolf': {'rgb': '99, 102, 241', 'shell': 'rgba(18, 20, 46, 0.94)', 'deep': 'rgba(9, 10, 22, 0.99)'},
    'Cave Spider': {'rgb': '132, 204, 22', 'shell': 'rgba(24, 35, 12, 0.94)', 'deep': 'rgba(11, 17, 8, 0.99)'},
    'Bandit': {'rgb': '239, 68, 68', 'shell': 'rgba(44, 18, 22, 0.94)', 'deep': 'rgba(18, 8, 10, 0.99)'},
    'Fallen': {'rgb': '249, 115, 22', 'shell': 'rgba(44, 21, 13, 0.94)', 'deep': 'rgba(20, 10, 8, 0.99)'},
    'Ghoul': {'rgb': '132, 204, 22', 'shell': 'rgba(22, 34, 15, 0.94)', 'deep': 'rgba(10, 16, 9, 0.99)'},
    'Bogling': {'rgb': '101, 163, 13', 'shell': 'rgba(22, 30, 13, 0.94)', 'deep': 'rgba(9, 14, 8, 0.99)'},
    'Murloc': {'rgb': '34, 211, 238', 'shell': 'rgba(12, 30, 39, 0.94)', 'deep': 'rgba(8, 15, 18, 0.99)'},
    'Templar': {'rgb': '234, 179, 8', 'shell': 'rgba(40, 31, 12, 0.94)', 'deep': 'rgba(17, 13, 8, 0.99)'},
    'Hollow Knight': {'rgb': '148, 163, 184', 'shell': 'rgba(20, 24, 34, 0.94)', 'deep': 'rgba(9, 11, 18, 0.99)'},
    'Ravager': {'rgb': '251, 146, 60', 'shell': 'rgba(47, 24, 14, 0.94)', 'deep': 'rgba(19, 11, 8, 0.99)'},
    'Shade Archer': {'rgb': '129, 140, 248', 'shell': 'rgba(20, 18, 46, 0.94)', 'deep': 'rgba(9, 9, 22, 0.99)'},
    'Salamander': {'rgb': '249, 115, 22', 'shell': 'rgba(47, 23, 12, 0.94)', 'deep': 'rgba(18, 10, 8, 0.99)'},
    'Skeleton': {'rgb': '214, 211, 209', 'shell': 'rgba(36, 36, 34, 0.94)', 'deep': 'rgba(16, 16, 15, 0.99)'},
}
DEFAULT_MONSTER_THEME = {'rgb': '168, 176, 190', 'shell': 'rgba(22, 24, 32, 0.94)', 'deep': 'rgba(10, 12, 17, 0.99)'}

ui.add_head_html('''
<style>
:root {
  --mq-accent: #d8c77a;
  --mq-accent-rgb: 216, 199, 122;
  --mq-accent-soft: rgba(216, 199, 122, 0.18);
  --mq-accent-strong: rgba(216, 199, 122, 0.42);
  --mq-scene-core: rgba(22, 24, 32, 0.96);
  --mq-scene-edge: rgba(12, 14, 18, 0.98);
  --mq-panel-bg: rgba(17, 20, 27, 0.84);
  --mq-panel-border: rgba(255, 255, 255, 0.08);
  --mq-text-main: #f3f5f7;
  --mq-text-soft: #dbe3ed;
  --mq-text-muted: #98a6b7;
  --mq-scene-glow: rgba(216, 199, 122, 0.12);
}
html {
  scroll-behavior: smooth;
}
body {
  background:
    radial-gradient(circle at top, rgba(125, 38, 38, 0.22) 0%, rgba(19, 18, 24, 0.05) 30%),
    linear-gradient(180deg, #07090d 0%, #0b0e14 38%, #10141c 100%);
  color: var(--mq-text-main);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  letter-spacing: 0.01em;
}
.mq-page {
  min-height: 100vh;
  width: 100%;
  position: relative;
  isolation: isolate;
}
.mq-page::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -2;
  background:
    radial-gradient(circle at 16% 14%, var(--mq-scene-glow) 0%, rgba(0,0,0,0) 28%),
    radial-gradient(circle at 84% 10%, rgba(var(--mq-accent-rgb), 0.09) 0%, rgba(0,0,0,0) 24%),
    radial-gradient(circle at 50% 120%, rgba(60,72,102,0.16) 0%, rgba(0,0,0,0) 44%);
}
.mq-page::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: -1;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.025) 0%, rgba(255,255,255,0) 10%),
    linear-gradient(180deg, rgba(0,0,0,0) 74%, rgba(0,0,0,0.24) 100%);
  mix-blend-mode: screen;
}
.mq-screen-title,
.mq-scene-title {
  --mq-accent: #dcc48a;
  --mq-accent-rgb: 220, 196, 138;
  --mq-panel-bg: rgba(20, 18, 24, 0.86);
  --mq-scene-core: rgba(34, 28, 34, 0.98);
  --mq-scene-edge: rgba(11, 11, 14, 0.98);
  --mq-scene-glow: rgba(220, 196, 138, 0.13);
}
.mq-screen-class-select,
.mq-scene-class-select {
  --mq-accent: #ceb57d;
  --mq-accent-rgb: 206, 181, 125;
  --mq-panel-bg: rgba(19, 19, 26, 0.86);
  --mq-scene-core: rgba(29, 25, 34, 0.98);
  --mq-scene-edge: rgba(11, 11, 14, 0.99);
  --mq-scene-glow: rgba(138, 98, 177, 0.10);
}
.mq-screen-town,
.mq-scene-town {
  --mq-accent: #c8ced8;
  --mq-accent-rgb: 200, 206, 216;
  --mq-panel-bg: rgba(15, 17, 21, 0.90);
  --mq-scene-core: rgba(25, 27, 33, 0.98);
  --mq-scene-edge: rgba(8, 9, 12, 0.995);
  --mq-scene-glow: rgba(170, 178, 190, 0.10);
}
.mq-scene-arena {
  --mq-accent: #d9896f;
  --mq-accent-rgb: 217, 137, 111;
  --mq-panel-bg: rgba(25, 19, 20, 0.86);
  --mq-scene-core: rgba(44, 27, 28, 0.96);
  --mq-scene-edge: rgba(13, 11, 13, 0.99);
  --mq-scene-glow: rgba(158, 58, 48, 0.15);
}
.mq-scene-inventory {
  --mq-accent: #8ed5c1;
  --mq-accent-rgb: 142, 213, 193;
  --mq-panel-bg: rgba(17, 22, 27, 0.88);
  --mq-scene-core: rgba(22, 28, 32, 0.97);
  --mq-scene-edge: rgba(9, 12, 15, 0.99);
  --mq-scene-glow: rgba(66, 140, 124, 0.14);
}
.mq-scene-marketplace {
  --mq-accent: #9bd688;
  --mq-accent-rgb: 155, 214, 136;
  --mq-panel-bg: rgba(20, 28, 22, 0.86);
  --mq-scene-core: rgba(25, 38, 26, 0.96);
  --mq-scene-edge: rgba(10, 14, 10, 0.99);
  --mq-scene-glow: rgba(101, 176, 84, 0.14);
}
.mq-scene-transmute {
  --mq-accent: #d2a0ff;
  --mq-accent-rgb: 210, 160, 255;
  --mq-panel-bg: rgba(23, 18, 30, 0.86);
  --mq-scene-core: rgba(34, 23, 47, 0.96);
  --mq-scene-edge: rgba(11, 10, 17, 0.99);
  --mq-scene-glow: rgba(146, 91, 216, 0.16);
}
.mq-scene-well {
  --mq-accent: #ef7f97;
  --mq-accent-rgb: 239, 127, 151;
  --mq-panel-bg: rgba(30, 18, 25, 0.88);
  --mq-scene-core: rgba(46, 20, 32, 0.97);
  --mq-scene-edge: rgba(13, 8, 12, 0.99);
  --mq-scene-glow: rgba(186, 43, 86, 0.18);
}
.mq-scene-inn {
  --mq-accent: #e7b46b;
  --mq-accent-rgb: 231, 180, 107;
  --mq-panel-bg: rgba(32, 24, 17, 0.88);
  --mq-scene-core: rgba(52, 34, 20, 0.97);
  --mq-scene-edge: rgba(18, 12, 8, 0.99);
  --mq-scene-glow: rgba(203, 126, 38, 0.16);
}
.mq-scene-ladder {
  --mq-accent: #8fb2ff;
  --mq-accent-rgb: 143, 178, 255;
  --mq-panel-bg: rgba(17, 21, 34, 0.88);
  --mq-scene-core: rgba(21, 27, 44, 0.97);
  --mq-scene-edge: rgba(9, 11, 18, 0.99);
  --mq-scene-glow: rgba(65, 96, 188, 0.15);
}
.mq-scene-glossary {
  --mq-accent: #a8d2df;
  --mq-accent-rgb: 168, 210, 223;
  --mq-panel-bg: rgba(16, 24, 28, 0.88);
  --mq-scene-core: rgba(18, 30, 36, 0.97);
  --mq-scene-edge: rgba(9, 13, 16, 0.99);
  --mq-scene-glow: rgba(84, 145, 164, 0.14);
}
.mq-shell,
.mq-selection-shell,
.mq-town-shell {
  max-width: 1640px;
}
.mq-arena-shell {
  max-width: 1780px;
}
.mq-card,
.mq-side-card,
.mq-slot-card,
.mq-selection-hero,
.mq-selection-card,
.mq-town-header,
.mq-scene-card,
.mq-overview-card,
.mq-travel-card,
.mq-arena-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.025) 0%, rgba(255,255,255,0) 10%), var(--mq-panel-bg);
  border: 1px solid rgba(var(--mq-accent-rgb), 0.18);
  border-radius: 24px;
  box-shadow:
    0 22px 48px rgba(0,0,0,0.34),
    inset 0 1px 0 rgba(255,255,255,0.03),
    0 0 0 1px rgba(255,255,255,0.02);
  backdrop-filter: blur(12px);
}
.mq-side-card,
.mq-slot-card,
.mq-selection-card,
.mq-overview-card,
.mq-travel-card,
.mq-arena-card {
  border-radius: 22px;
}
.mq-panel,
.mq-panel-frame,
.mq-log {
  background: linear-gradient(180deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0) 16%), rgba(10, 13, 18, 0.72);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
}
.mq-panel-frame:hover,
.mq-card:hover,
.mq-selection-card:hover,
.mq-overview-card:hover,
.mq-travel-card:hover,
.mq-arena-card:hover,
.mq-item-card:hover {
  border-color: rgba(var(--mq-accent-rgb), 0.26);
}
.mq-log {
  background: linear-gradient(180deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0) 12%), rgba(6, 9, 14, 0.82);
}
.mq-panel-caption,
.mq-section-title,
.mq-monster-nameplate,
.mq-slot-badge,
.mq-path-pill {
  color: rgb(var(--mq-accent-rgb));
  text-shadow: 0 0 18px rgba(var(--mq-accent-rgb), 0.16);
}
.mq-section-title,
.mq-panel-caption {
  letter-spacing: 0.12em;
  font-size: 0.76rem;
  font-weight: 800;
}
.mq-title-card {
  background: linear-gradient(180deg, rgba(29, 23, 31, 0.97) 0%, rgba(16, 17, 22, 0.98) 100%);
  border-radius: 28px;
}
.mq-title-stage,
.mq-hero-art-frame,
.mq-arena-avatar-frame,
.mq-monster-stage,
.mq-scene-stage {
  position: relative;
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid rgba(var(--mq-accent-rgb), 0.18);
  background:
    radial-gradient(circle at 50% 18%, rgba(var(--mq-accent-rgb), 0.10) 0%, rgba(0,0,0,0) 30%),
    radial-gradient(circle at 50% 32%, var(--mq-scene-core) 0%, rgba(18, 20, 28, 0.96) 44%, var(--mq-scene-edge) 84%),
    linear-gradient(180deg, rgba(18, 20, 26, 0.98) 0%, rgba(11, 12, 16, 1) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.04),
    inset 0 -24px 56px rgba(0,0,0,0.42),
    0 22px 42px rgba(0,0,0,0.28);
}
.mq-title-stage { min-height: min(80vh, 780px); max-height: 80vh; display: flex; align-items: center; justify-content: center; padding: 12px 12px 82px; }
.mq-scene-stage { min-height: 560px; }
.mq-monster-stage { min-height: 360px; display: flex; align-items: center; justify-content: center; padding: 12px; overflow: hidden; }
.mq-title-stage::before,
.mq-hero-art-frame::before,
.mq-arena-avatar-frame::before,
.mq-monster-stage::before,
.mq-scene-stage::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 22%;
  background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0));
  pointer-events: none;
}
.mq-title-stage::after,
.mq-monster-stage::after,
.mq-scene-stage::after {
  content: '';
  position: absolute;
  inset: auto 0 0 0;
  height: 30%;
  background: linear-gradient(180deg, rgba(8,8,10,0) 0%, rgba(7,8,11,0.54) 50%, rgba(6,6,8,0.92) 100%);
  pointer-events: none;
}
.mq-title-image,
.mq-scene-image,
.mq-hero-art,
.mq-arena-avatar,
.mq-monster-image,
.mq-item-icon {
  filter: drop-shadow(0 28px 38px rgba(0,0,0,0.52)) drop-shadow(0 0 22px rgba(var(--mq-accent-rgb), 0.12));
}
.mq-title-caption {
  position: absolute;
  left: 50%;
  bottom: 24px;
  transform: translateX(-50%);
  z-index: 3;
  width: calc(100% - 56px);
  max-width: 760px;
  text-align: center;
  color: var(--mq-text-soft);
  font-style: italic;
  font-size: 0.98rem;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(8, 10, 14, 0.52);
  border: 1px solid rgba(var(--mq-accent-rgb), 0.16);
  box-shadow: 0 10px 20px rgba(0,0,0,0.28);
}
.mq-title-image-wrap {
  position: absolute;
  inset: 14px 18px 82px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.mq-title-image-static {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  margin: 0 auto;
  object-fit: contain;
  object-position: center center;
  filter: drop-shadow(0 28px 38px rgba(0,0,0,0.52)) drop-shadow(0 0 22px rgba(var(--mq-accent-rgb), 0.12));
  transform: translateZ(0);
}
.mq-scene-image-wrap,
.mq-monster-image-wrap {
  padding: 18px;
}
.mq-monster-image-wrap {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 344px;
  height: 100%;
  padding: 16px 14px;
}
.mq-scene-image,
.mq-title-image {
  object-fit: contain;
}
.mq-scene-fallback-pill,
.mq-item-icon-frame,
.mq-hero-art-fallback,
.mq-monster-fallback,
.mq-arena-avatar.empty {
  background: rgba(11, 14, 19, 0.68);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--mq-text-soft);
}
.mq-hero-art,
.mq-arena-avatar { padding-top: 6px; }
.mq-hover-name {
  display: inline-block;
  color: #f1f5f9;
  border-bottom: 1px dotted rgba(214, 221, 232, 0.34);
  cursor: help;
}
.mq-item-name-muted {
  color: #94a3b8;
}
.mq-arena-top {
  display: grid;
  grid-template-columns: minmax(620px, 1.38fr) minmax(360px, 0.82fr);
  gap: 20px;
  align-items: stretch;
}
.mq-arena-avatar-frame {
  width: 300px;
  min-width: 300px;
  min-height: 360px;
  max-width: 300px;
  margin: 0;
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-color: rgba(228, 190, 176, 0.26);
  background:
    radial-gradient(circle at 50% 28%, rgba(236, 239, 245, 0.08) 0%, rgba(236, 239, 245, 0.02) 24%, rgba(0,0,0,0) 46%),
    radial-gradient(circle at 50% 78%, rgba(78, 88, 112, 0.24) 0%, rgba(25, 31, 42, 0.18) 26%, rgba(0,0,0,0) 58%),
    linear-gradient(180deg, rgba(29, 34, 42, 0.98) 0%, rgba(15, 19, 26, 0.99) 54%, rgba(8, 11, 15, 1) 100%);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.05),
    inset 0 -26px 58px rgba(0,0,0,0.40),
    0 22px 42px rgba(0,0,0,0.30),
    0 0 0 1px rgba(236, 239, 245, 0.03);
}
.mq-arena-avatar,
.mq-arena-avatar-static {
  display: block;
  width: 100%;
  height: 100%;
  max-width: 260px;
  max-height: 320px;
  margin: 0 auto;
  object-fit: contain;
  object-position: center bottom;
  pointer-events: none;
  user-select: none;
  transform: translateZ(0);
}
.mq-inventory-popup-card {
  width: min(1240px, 96vw);
  max-width: 96vw;
  min-width: 920px;
  min-height: 640px;
  max-height: 92vh;
  padding: 18px;
  resize: both;
  overflow: auto;
}
@media (max-width: 980px) {
  .mq-inventory-popup-card {
    min-width: 0;
    width: 96vw;
    min-height: 72vh;
    resize: none;
  }
}
.mq-monster-image,
.mq-monster-image-static {
  display: block;
  width: auto;
  height: auto;
  max-width: min(92%, 400px);
  max-height: 328px;
  margin: 0 auto;
  object-fit: contain;
  object-position: center center;
  pointer-events: none;
  user-select: none;
  transform: translateZ(0);
  backface-visibility: hidden;
  will-change: transform;
}
.mq-combat-log {
  max-height: 300px;
}
.mq-player-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.mq-stat-chip {
  padding: 10px 12px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%), rgba(8, 11, 16, 0.76);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.mq-stat-chip-clickable {
  cursor: pointer;
  transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}
.mq-stat-chip-clickable:hover {
  transform: translateY(-1px);
  border-color: rgba(var(--mq-accent-rgb), 0.45);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.05),
    0 8px 18px rgba(0, 0, 0, 0.22),
    0 0 0 1px rgba(var(--mq-accent-rgb), 0.14);
  background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%), rgba(10, 14, 20, 0.84);
}
.mq-stat-chip-clickable:active {
  transform: translateY(0);
}
.mq-stat-chip-label {
  font-size: 0.70rem;
  letter-spacing: 0.10em;
  color: var(--mq-text-muted);
  text-transform: uppercase;
  margin-bottom: 4px;
}
.mq-stat-chip-value {
  color: var(--mq-text-main);
  font-size: 0.98rem;
  font-weight: 700;
}
.mq-player-side-layout {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
.mq-player-panels {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(300px, 1.15fr);
  gap: 14px;
  margin-top: 16px;
}
.mq-core-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 10px;
}
.mq-player-meters {
  margin-top: 16px;
  width: 100%;
}
.mq-player-meters .mq-meter-track,
.mq-player-meters .mq-meter {
  width: 100%;
}
.mq-player-meters .mq-meter-track {
  height: 30px;
}
.mq-monster-panel-grid {
  display: grid;
  grid-template-columns: minmax(300px, 0.95fr) minmax(0, 1.05fr);
  gap: 20px;
  align-items: center;
}
@media (max-width: 1180px) {
  .mq-arena-top {
    grid-template-columns: 1fr;
  }
  .mq-player-panels {
    grid-template-columns: 1fr;
  }
  .mq-core-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.mq-monster-details {
  display: grid;
  gap: 12px;
}
.mq-monster-quote {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(8, 10, 15, 0.58);
  border: 1px solid rgba(255,255,255,0.07);
}
.mq-monster-stage-themed {
  --mq-monster-rgb: var(--mq-accent-rgb);
  --mq-monster-shell: rgba(22, 24, 32, 0.94);
  --mq-monster-deep: rgba(10, 12, 17, 0.99);
  border: 3px solid rgba(var(--mq-monster-rgb), 0.78) !important;
  background:
    radial-gradient(circle at 50% 52%, rgba(var(--mq-monster-rgb), 0.24) 0%, rgba(var(--mq-monster-rgb), 0.11) 28%, rgba(0,0,0,0) 58%),
    radial-gradient(circle at 50% 18%, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 24%),
    linear-gradient(180deg, var(--mq-monster-shell) 0%, var(--mq-monster-deep) 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.04),
    inset 0 -24px 56px rgba(0,0,0,0.42),
    0 18px 34px rgba(0,0,0,0.30),
    0 0 0 1px rgba(var(--mq-monster-rgb), 0.34),
    0 0 22px rgba(var(--mq-monster-rgb), 0.20),
    0 0 56px rgba(var(--mq-monster-rgb), 0.16);
}
.mq-monster-stage-themed .mq-monster-image-static {
  filter: drop-shadow(0 24px 34px rgba(0,0,0,0.54)) drop-shadow(0 0 26px rgba(var(--mq-monster-rgb), 0.28));
}
.mq-title-image {
  display: block;
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  margin: 0 auto;
  object-fit: contain;
  object-position: center center;
}
.mq-scene-image {
  display: block;
  width: 100%;
  height: auto;
  max-height: 470px;
  margin: 0 auto;
}
.mq-selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 18px;
  align-items: start;
}
.mq-selection-card.locked {
  opacity: 0.62;
}
.mq-selection-hero-bubble {
  width: 136px;
  min-height: 136px;
  max-width: 136px;
  margin: 0 auto;
  border-radius: 999px;
  padding: 9px;
}
.mq-selection-hero-bubble .mq-hero-art {
  width: 100%;
  max-width: 110px;
  max-height: 110px;
  margin: auto;
  object-fit: contain;
}
.mq-selection-hero-bubble .mq-hero-art-fallback {
  min-height: 110px;
  border-radius: 999px;
}
.mq-town-dashboard {
  display: grid;
  grid-template-columns: minmax(250px, 0.9fr) minmax(0, 1.18fr) minmax(250px, 0.9fr);
  gap: 18px;
  align-items: start;
}
.mq-town-grid {
  display: contents;
}
.mq-town-comm-card {
  grid-column: 1 / -1;
}
.mq-comm-bubble {
  position: relative;
  padding: 18px 20px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.0) 14%), rgba(10, 12, 16, 0.86);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.mq-comm-bubble::before {
  content: '';
  position: absolute;
  top: -10px;
  left: 38px;
  width: 18px;
  height: 18px;
  background: rgba(10, 12, 16, 0.86);
  border-left: 1px solid rgba(255,255,255,0.08);
  border-top: 1px solid rgba(255,255,255,0.08);
  transform: rotate(45deg);
}
.mq-town-map-card .mq-scene-stage,
.mq-town-scene-stage {
  min-height: 285px;
  max-height: 345px;
}
.mq-town-scene-image-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 12px 14px 10px;
}
.mq-town-scene-image,
.mq-town-scene-image-static {
  max-height: 300px;
  width: auto;
  max-width: 100%;
  margin: 0 auto;
  object-fit: contain;
  object-position: center center;
  filter: grayscale(1) contrast(1.1) brightness(0.76) drop-shadow(0 24px 34px rgba(0,0,0,0.62));
  transform: translateZ(0);
}
.mq-town-shell .mq-log {
  max-height: 200px;
  overflow: auto;
}
.mq-route-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.mq-route-btn,
.mq-btn-gold,
.mq-arena-btn,
.mq-arena-btn.secondary,
.mq-arena-btn.danger {
  transition: transform 140ms ease, filter 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}
.mq-route-btn,
.mq-btn-gold,
.mq-arena-btn {
  background: linear-gradient(180deg, rgba(255,255,255,0.14) 0%, rgba(38, 42, 50, 0.96) 18%, rgba(12, 13, 17, 0.99) 100%) !important;
  color: #eef2f7 !important;
  border: 1px solid rgba(220, 226, 236, 0.20) !important;
  box-shadow: 0 12px 24px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}
.mq-arena-btn.secondary {
  background: linear-gradient(180deg, rgba(180, 186, 197, 0.12) 0%, rgba(32, 36, 43, 0.96) 22%, rgba(12, 13, 17, 0.99) 100%) !important;
  color: #e7ebf2 !important;
  border-color: rgba(176, 184, 197, 0.18) !important;
}
.mq-route-quit,
.mq-arena-btn.danger {
  background: linear-gradient(180deg, rgba(214, 137, 137, 0.16) 0%, rgba(52, 28, 30, 0.96) 24%, rgba(18, 10, 11, 0.985) 100%) !important;
  border-color: rgba(220, 150, 150, 0.18);
}
.mq-route-btn:hover,
.mq-btn-gold:hover,
.mq-arena-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.06);
  box-shadow: 0 18px 28px rgba(0,0,0,0.28), 0 0 0 1px rgba(var(--mq-accent-rgb), 0.10);
}
.mq-route-btn:disabled,
.mq-btn-gold:disabled,
.mq-arena-btn:disabled {
  opacity: 0.52;
  filter: grayscale(0.2);
}
.mq-combat-log {
  max-height: 480px;
  overflow: auto;
  overflow-anchor: none;
  overscroll-behavior: contain;
  scrollbar-gutter: stable both-edges;
  scroll-behavior: smooth;
  padding: 16px 18px;
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 12%),
    rgba(7, 10, 15, 0.90);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.mq-combat-log::-webkit-scrollbar {
  width: 10px;
}
.mq-combat-log::-webkit-scrollbar-thumb {
  background: rgba(var(--mq-accent-rgb), 0.24);
  border-radius: 999px;
}
.mq-log-line {
  color: var(--mq-text-soft);
  font-size: 0.96rem;
  line-height: 1.66;
  margin: 0;
  padding-left: 2px;
  white-space: pre-wrap;
}
.mq-log-line + .mq-log-line { margin-top: 6px; }
.mq-log-line.round {
  color: #a5c0d6;
  font-weight: 800;
  text-align: center;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-top: 10px;
}
.mq-log-line.quote {
  color: rgb(var(--mq-accent-rgb));
  font-style: italic;
  padding: 8px 10px;
  border-left: 2px solid rgba(var(--mq-accent-rgb), 0.26);
  background: rgba(var(--mq-accent-rgb), 0.06);
  border-radius: 10px;
}
.mq-log-line.success { color: #92e6b3; }
.mq-log-line.warning { color: #f1d17b; }
.mq-log-line.danger { color: #ff9a9a; }
.mq-log-line.system { color: #95a7ba; }
.mq-log-line.result { font-weight: 800; }
.mq-transition {
  min-height: 34px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(8, 10, 14, 0.44);
  border: 1px solid rgba(255,255,255,0.06);
  font-size: 1.22rem;
  line-height: 1.8rem;
}
.mq-transition.accent { color: rgb(var(--mq-accent-rgb)); }
.mq-transition.success { color: #92e6b3; }
.mq-transition.warning { color: #f1d17b; }
.mq-transition.danger { color: #ff9a9a; }
.mq-transition.muted { color: #9eabbb; }
.mq-meter-track {
  width: 100%;
  min-width: 100%;
  height: 26px;
  border-radius: 999px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(8,10,14,0.84) 100%);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: inset 0 1px 6px rgba(0,0,0,0.34), 0 10px 18px rgba(0,0,0,0.18);
}
.mq-meter {
  width: 100%;
  margin-top: 10px;
}
.mq-meter-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--mq-text-soft);
  font-size: 0.84rem;
  letter-spacing: 0.01em;
  margin-bottom: 6px;
}
.mq-meter-fill {
  height: 100%;
  border-radius: 999px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.24), 0 0 18px rgba(255,255,255,0.08);
}
.mq-meter-fill.hp { background: linear-gradient(90deg, #234036 0%, #31d48e 55%, #86f1bf 100%); }
.mq-meter-fill.mana { background: linear-gradient(90deg, #102d68 0%, #3f87ff 56%, #7ac0ff 100%); }
.mq-meter-fill.exp { background: linear-gradient(90deg, #6d5018 0%, #d8b24d 56%, #f4dfa1 100%); }
.mq-item-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.028) 0%, rgba(255,255,255,0) 10%), rgba(16, 19, 25, 0.97);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 18px;
  transition: border-color 140ms ease, transform 140ms ease, box-shadow 140ms ease, background 140ms ease;
}
.mq-item-card.selected {
  background: linear-gradient(180deg, rgba(var(--mq-accent-rgb), 0.10) 0%, rgba(var(--mq-accent-rgb), 0.03) 100%), rgba(17, 21, 28, 0.98);
  border-color: rgba(var(--mq-accent-rgb), 0.78);
  box-shadow: 0 18px 34px rgba(0,0,0,0.30), 0 0 0 2px rgba(var(--mq-accent-rgb), 0.22), inset 0 0 0 1px rgba(255,255,255,0.04);
}
.mq-item-card.previewing:not(.selected) {
  border-color: rgba(125, 211, 252, 0.48);
  box-shadow: 0 14px 24px rgba(0,0,0,0.24), 0 0 0 1px rgba(125, 211, 252, 0.14);
}
.mq-item-icon-frame {
  width: 78px;
  height: 78px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.mq-detail-text,
.mq-stat-block {
  color: var(--mq-text-soft);
  line-height: 1.72;
}
.mq-inv-title {
  font-size: 2.26rem;
  line-height: 1.12;
  font-weight: 800;
  color: #f8fbff;
  text-shadow: 0 0 18px rgba(var(--mq-accent-rgb), 0.08);
}
.mq-inv-subtitle {
  font-size: 1.10rem;
  line-height: 1.78;
  color: #dce6f1;
}
.mq-inv-section-title {
  font-size: 1.28rem;
  line-height: 1.24;
  font-weight: 780;
  color: #f8fbff;
}
.mq-inv-helper {
  font-size: 1.05rem;
  line-height: 1.74;
  color: #d7e1ec;
}
.mq-inv-empty {
  font-size: 1.10rem;
  line-height: 1.70;
  color: #dbe5f0;
}
.mq-inv-entry-title {
  font-size: 1.10rem;
  line-height: 1.48;
  font-weight: 760;
  color: #fbfdff;
}
.mq-inv-entry-sub,
.mq-inv-meta {
  font-size: 1.00rem;
  line-height: 1.66;
  color: #dce6f1;
}
.mq-inv-entry-base {
  font-size: 1.01rem;
  line-height: 1.62;
  color: #dce8f5;
  font-weight: 660;
}
.mq-inv-entry-affix {
  font-size: 1.03rem;
  line-height: 1.66;
  color: #eff6ff;
  font-weight: 700;
}
.mq-inv-detail-block {
  font-size: 1.08rem;
  line-height: 1.90;
  color: #e8eff7;
}
.mq-inv-summary-line {
  font-size: 1.04rem;
  line-height: 1.78;
  color: #dde7f1;
}
.mq-inv-summary-strong {
  color: #fbfdff;
  font-weight: 760;
}
.mq-inv-label-accent {
  color: rgb(var(--mq-accent-rgb));
  font-weight: 820;
}
.mq-inv-label-tier {
  color: #93c5fd;
  font-weight: 820;
}
.mq-inv-label-req {
  color: #fcd34d;
  font-weight: 820;
}
.mq-inv-label-gold {
  color: #86efac;
  font-weight: 820;
}
.mq-inv-label-set {
  color: #c4b5fd;
  font-weight: 820;
}
.mq-inv-label-info {
  color: #7dd3fc;
  font-weight: 820;
}
.mq-inv-pill {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.92rem;
  font-weight: 740;
  letter-spacing: 0.01em;
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.mq-inv-pill.rarity {
  background: rgba(255,255,255,0.05);
  color: #f3f7fb;
}
.mq-inv-pill.tier {
  background: rgba(96, 165, 250, 0.13);
  color: #bfdbfe;
}
.mq-inv-pill.req {
  background: rgba(250, 204, 21, 0.12);
  color: #fde68a;
}
.mq-inv-pill.sell {
  background: rgba(74, 222, 128, 0.12);
  color: #bbf7d0;
}
.mq-inv-pill.level {
  background: rgba(148, 163, 184, 0.12);
  color: #dbeafe;
}
.mq-inv-pill.set {
  background: rgba(192, 132, 252, 0.12);
  color: #e9d5ff;
}
.mq-manifest-flag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.88rem;
  font-weight: 820;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.mq-manifest-flag.selected {
  background: rgba(var(--mq-accent-rgb), 0.22);
  color: #ffe8a3;
  border: 1px solid rgba(var(--mq-accent-rgb), 0.34);
}
.mq-manifest-flag.preview {
  background: rgba(56, 189, 248, 0.18);
  color: #c8f5ff;
  border: 1px solid rgba(56, 189, 248, 0.30);
}
.mq-pack-manifest-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--mq-accent-rgb), 0.60) rgba(255,255,255,0.05);
}
.mq-pack-manifest-scroll::-webkit-scrollbar {
  width: 10px;
}
.mq-pack-manifest-scroll::-webkit-scrollbar-track {
  background: rgba(255,255,255,0.04);
  border-radius: 999px;
}
.mq-pack-manifest-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(var(--mq-accent-rgb), 0.88) 0%, rgba(125, 211, 252, 0.72) 100%);
  border-radius: 999px;
}
.mq-inv-block-title {
  font-size: 0.96rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 840;
  color: #b7c7d8;
}
.mq-base-stat-list,
.mq-affix-stat-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mq-base-line,
.mq-affix-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 14px;
  padding: 10px 12px;
}
.mq-base-line {
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.07);
}
.mq-base-label {
  color: #dbe7f3;
  font-size: 1.02rem;
  font-weight: 720;
}
.mq-base-value {
  color: #fbfdff;
  font-size: 1.04rem;
  font-weight: 820;
}
.mq-affix-line {
  border: 1px solid rgba(255,255,255,0.07);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.mq-affix-line .mq-affix-text {
  font-size: 1.07rem;
  line-height: 1.54;
  font-weight: 760;
}
.mq-affix-line.offense {
  background: linear-gradient(180deg, rgba(127, 29, 29, 0.34) 0%, rgba(68, 18, 18, 0.28) 100%);
  border-color: rgba(248, 113, 113, 0.24);
}
.mq-affix-line.offense .mq-affix-text { color: #fecaca; }
.mq-affix-line.finesse {
  background: linear-gradient(180deg, rgba(8, 47, 73, 0.36) 0%, rgba(8, 28, 47, 0.28) 100%);
  border-color: rgba(56, 189, 248, 0.22);
}
.mq-affix-line.finesse .mq-affix-text { color: #bae6fd; }
.mq-affix-line.vitality {
  background: linear-gradient(180deg, rgba(20, 83, 45, 0.34) 0%, rgba(17, 53, 33, 0.28) 100%);
  border-color: rgba(74, 222, 128, 0.22);
}
.mq-affix-line.vitality .mq-affix-text { color: #bbf7d0; }
.mq-affix-line.arcane {
  background: linear-gradient(180deg, rgba(59, 7, 100, 0.36) 0%, rgba(37, 11, 69, 0.28) 100%);
  border-color: rgba(192, 132, 252, 0.24);
}
.mq-affix-line.arcane .mq-affix-text { color: #e9d5ff; }
.mq-affix-line.utility {
  background: linear-gradient(180deg, rgba(97, 62, 11, 0.36) 0%, rgba(64, 39, 8, 0.28) 100%);
  border-color: rgba(250, 204, 21, 0.24);
}
.mq-affix-line.utility .mq-affix-text { color: #fde68a; }
.mq-affix-line.neutral {
  background: linear-gradient(180deg, rgba(51, 65, 85, 0.26) 0%, rgba(30, 41, 59, 0.22) 100%);
  border-color: rgba(148, 163, 184, 0.22);
}
.mq-affix-line.neutral .mq-affix-text { color: #dbeafe; }
.mq-scene-inventory .q-field__label {
  color: #d9e4ef !important;
  font-size: 1.00rem !important;
  font-weight: 760 !important;
}
.mq-scene-inventory .q-field__native,
.mq-scene-inventory .q-field__input,
.mq-scene-inventory .q-field__append,
.mq-scene-inventory .q-field__marginal {
  color: #f7fbff !important;
  font-size: 1.04rem !important;
  font-weight: 690 !important;
}
.mq-filter-grid .q-field__control,
.mq-arena-options .q-field__control,
.mq-filter-grid .q-field__native,
.mq-arena-options .q-field__native {
  color: var(--mq-text-main) !important;
}
.q-field__control {
  border-radius: 14px !important;
  background: rgba(9, 12, 17, 0.78) !important;
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
}
.q-field__label,
.q-field__marginal,
.q-field__native,
.q-field__input,
.q-select__dropdown-icon {
  color: var(--mq-text-soft) !important;
}
.q-menu,
.q-dialog__inner > div,
.q-table__container {
  background: rgba(14, 17, 24, 0.98) !important;
  color: var(--mq-text-main) !important;
  border: 1px solid rgba(var(--mq-accent-rgb), 0.18);
  border-radius: 18px;
  backdrop-filter: blur(12px);
}
.q-item__label,
.q-item {
  color: var(--mq-text-soft) !important;
}
.q-item.q-manual-focusable.q-hoverable:hover {
  background: rgba(var(--mq-accent-rgb), 0.08) !important;
}
.q-tab-panels,
.q-tab-panel,
.q-table tbody td,
.q-table thead th {
  color: var(--mq-text-soft) !important;
}
.q-separator {
  opacity: 0.18;
}
@media (max-width: 1180px) {
  .mq-title-stage { min-height: 620px; max-height: none; }
  .mq-scene-stage { min-height: 440px; }
  .mq-town-dashboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mq-town-comm-card { grid-column: 1 / -1; }
  .mq-arena-top { grid-template-columns: minmax(0, 1fr); }
  .mq-monster-panel-grid { grid-template-columns: minmax(0, 1fr); }
  .mq-player-panels { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 900px) {
  .mq-town-dashboard { grid-template-columns: minmax(0, 1fr); }
  .mq-town-grid { display: grid; grid-template-columns: repeat(1, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .mq-title-stage { min-height: 460px; max-height: none; }
  .mq-scene-stage { min-height: 400px; }
  .mq-title-caption { width: calc(100% - 28px); bottom: 14px; font-size: 0.9rem; }
  .mq-route-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
  .mq-player-side-layout { grid-template-columns: minmax(0, 1fr); }
  .mq-arena-avatar-frame { margin: 0 auto; }
  .mq-selection-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
  .mq-selection-hero-bubble { width: 120px; min-height: 120px; max-width: 120px; }
  .mq-town-map-card .mq-scene-stage, .mq-town-scene-stage { min-height: 250px; max-height: 290px; }
  .mq-town-scene-image { max-height: 240px; }
}

.mq-prof-tooltip-wrap {
  position: relative;
  display: inline-flex;
  isolation: isolate;
  z-index: 4200;
}
.mq-prof-tooltip-panel {
  position: absolute;
  bottom: calc(100% + 14px);
  top: auto;
  left: 50%;
  transform: translateX(-50%) translateY(8px);
  width: min(520px, 82vw);
  opacity: 0;
  pointer-events: none;
  transition: opacity 140ms ease, transform 140ms ease;
  z-index: 5000;
}
.mq-prof-tooltip-wrap:hover .mq-prof-tooltip-panel,
.mq-prof-tooltip-wrap:focus-within .mq-prof-tooltip-panel {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.mq-prof-tooltip-card,
.mq-prof-tooltip-empty {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0) 14%),
    rgba(17, 20, 27, 0.97);
  border: 1px solid rgba(var(--mq-accent-rgb), 0.24);
  border-radius: 20px;
  box-shadow:
    0 22px 44px rgba(0,0,0,0.38),
    0 0 0 1px rgba(255,255,255,0.03),
    inset 0 1px 0 rgba(255,255,255,0.05);
  backdrop-filter: blur(12px);
  padding: 16px 18px;
}
.mq-prof-title {
  font-size: 1.10rem;
  line-height: 1.2;
  font-weight: 820;
  color: #f8fbff;
}
.mq-prof-sub {
  margin-top: 8px;
  font-size: 0.96rem;
  line-height: 1.62;
  color: #dce6f1;
}
.mq-prof-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}
.mq-prof-row {
  display: grid;
  grid-template-columns: 26px minmax(0, 1.2fr) auto auto auto;
  gap: 10px;
  align-items: center;
  padding: 9px 11px;
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
}
.mq-prof-row.active {
  background: linear-gradient(180deg, rgba(var(--mq-accent-rgb), 0.16) 0%, rgba(var(--mq-accent-rgb), 0.06) 100%);
  border-color: rgba(var(--mq-accent-rgb), 0.34);
  box-shadow: 0 0 0 1px rgba(var(--mq-accent-rgb), 0.12);
}
.mq-prof-marker {
  color: rgb(var(--mq-accent-rgb));
  font-weight: 900;
  text-align: center;
}
.mq-prof-name {
  color: #f4f8fc;
  font-weight: 760;
  font-size: 0.98rem;
}
.mq-prof-level {
  color: #c4b5fd;
  font-weight: 760;
  font-size: 0.92rem;
}
.mq-prof-progress {
  color: #93c5fd;
  font-weight: 720;
  font-size: 0.90rem;
}
.mq-prof-bonus {
  color: #86efac;
  font-weight: 800;
  font-size: 0.90rem;
}
.mq-prof-active {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
}
.mq-prof-active-label {
  color: rgb(var(--mq-accent-rgb));
  font-size: 0.84rem;
  font-weight: 840;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.mq-prof-active-value {
  color: #eef5fc;
  font-size: 0.96rem;
  line-height: 1.6;
  font-weight: 700;
}
.mq-saved-type-header {
  background: linear-gradient(180deg, rgba(var(--mq-accent-rgb), 0.12) 0%, rgba(var(--mq-accent-rgb), 0.04) 100%), rgba(17, 20, 27, 0.94);
  border: 1px solid rgba(var(--mq-accent-rgb), 0.22);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.mq-saved-placeholder {
  background: linear-gradient(180deg, rgba(255,255,255,0.025) 0%, rgba(255,255,255,0.0) 100%), rgba(14, 17, 22, 0.88);
  border: 1px dashed rgba(255,255,255,0.16);
  border-radius: 18px;
}
.mq-saved-placeholder-title {
  font-size: 1.02rem;
  line-height: 1.4;
  color: #dfe8f2;
  font-weight: 740;
}
.mq-saved-placeholder-sub {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #9fb0c2;
}

</style>
<script>
window.mqScrollMemory = window.mqScrollMemory || {};
window.mqRememberScroll = function(id) {
  const el = document.getElementById(id);
  if (!el) return;
  window.mqScrollMemory[id] = el.scrollTop || 0;
};
window.mqBindScrollMemory = function(id) {
  const el = document.getElementById(id);
  if (!el || el.dataset.mqScrollBound === '1') return;
  el.dataset.mqScrollBound = '1';
  el.addEventListener('scroll', function() {
    window.mqScrollMemory[id] = el.scrollTop || 0;
  }, {passive: true});
};
window.mqRestoreScroll = function(id) {
  const apply = function() {
    const el = document.getElementById(id);
    if (!el) return false;
    el.scrollTop = window.mqScrollMemory[id] || 0;
    return true;
  };
  requestAnimationFrame(function() {
    apply();
    setTimeout(apply, 0);
    setTimeout(apply, 40);
    setTimeout(apply, 120);
    setTimeout(apply, 260);
    setTimeout(apply, 420);
    setTimeout(apply, 700);
  });
};
</script>
''', shared=True)
def _find_title_screen_path() -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_paths = [
        os.path.join(base_dir, 'Assets', 'Title Screen.png'),
        os.path.join(base_dir, 'Assets', 'Title_Screen.png'),
        os.path.join(base_dir, 'Assets', 'Title Screen', 'Title Screen.png'),
        os.path.join(base_dir, 'Assets', 'Title Screen', 'Title_Screen.png'),
        os.path.join(base_dir, 'Assets', 'Title Screen', 'title screen.png'),
        os.path.join(base_dir, 'Assets', 'Title Screen'),
        os.path.join(base_dir, 'Title Screen.png'),
        os.path.join(base_dir, 'Title_Screen.png'),
        '/mnt/data/Title Screen.png',
        '/mnt/data/Title_Screen.png',
        '/mnt/data/user-njaXU8PVqT5u76afI37TuN20/0b58707526d74981a1461c599519634a/mnt/data/Title Screen.png',
        '/mnt/data/user-njaXU8PVqT5u76afI37TuN20/0b58707526d74981a1461c599519634a/mnt/data/Title_Screen.png',
    ]
    for path in search_paths:
        if os.path.isfile(path):
            return path
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                if name.lower().endswith('.png'):
                    return os.path.join(path, name)
    asset_dir = os.path.join(base_dir, 'Assets')
    if os.path.isdir(asset_dir):
        for root, _dirs, files in os.walk(asset_dir):
            for name in sorted(files):
                lower = name.lower()
                if lower.endswith('.png') and 'title' in lower and 'screen' in lower:
                    return os.path.join(root, name)
    return None
def _image_path_to_data_uri(path: Optional[str], *, crop_alpha: bool = False) -> str:
    if path is None:
        return ''
    try:
        if crop_alpha and Image is not None:
            image = Image.open(path).convert('RGBA')
            alpha = image.getchannel('A')
            bbox = alpha.getbbox()
            if bbox:
                pad = 10
                left = max(0, bbox[0] - pad)
                top = max(0, bbox[1] - pad)
                right = min(image.width, bbox[2] + pad)
                bottom = min(image.height, bbox[3] + pad)
                image = image.crop((left, top, right, bottom))
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
            return f'data:image/png;base64,{encoded}'
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except Exception:
        return ''

def _title_screen_data_uri() -> str:
    return _image_path_to_data_uri(_find_title_screen_path(), crop_alpha=True)
TITLE_SCREEN_DATA_URI = _title_screen_data_uri()
HERO_ASSET_FILENAMES = {
    'Fighter': ['Fighter.png'],
    'Mage': ['Mage_Player.png', 'Mage.png'],
    'Samurai': ['Samurai.png'],
    'Paladin': ['Paladin.png'],
    'Monk': ['Monk.png'],
    'Ninja': ['Ninja.png'],
    'Warlock': ['Warlock.png'],
    'Headhunter': ['Headhunter.png'],
    'Alchemist': ['Alchemist.png'],
}
def format_class_equip_rules(player_class: str) -> str:
    rules = CLASS_EQUIP_RULES.get(player_class, {})
    weapon_rules = rules.get('weapon')
    armor_rules = rules.get('armor')
    if weapon_rules is None:
        weapon_text = 'all weapons'
    elif not weapon_rules:
        weapon_text = 'no weapons'
    else:
        weapon_text = '/'.join(sorted(weapon_rules))
    if armor_rules is None:
        armor_text = 'all armor'
    else:
        armor_text = '/'.join(sorted(armor_rules)) + ' armor'
    return f'Equipment: {weapon_text}; {armor_text}. Charms: all.'
def get_class_unlock_requirement(player_class: str) -> str:
    if player_class in {'Fighter', 'Mage'}:
        return 'Available from the start.'
    prerequisites = [source for source, target in CLASS_MASTERQUEST_NEXT.items() if target == player_class]
    if not prerequisites:
        return 'Hidden path.'
    if len(prerequisites) == 1:
        return f'Pass MasterQuest as {prerequisites[0]}.'
    return 'Pass MasterQuest as ' + ' or '.join(prerequisites) + '.'
def format_class_path_entry(player_class: str, unlocked_classes: set[str]) -> str:
    marker = '◆' if player_class in unlocked_classes else '◇'
    state = 'Ready' if player_class in unlocked_classes else get_class_unlock_requirement(player_class)
    return f'{marker} {player_class:<11} {state}'
def _find_hero_asset_path(player_class: str) -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_names = HERO_ASSET_FILENAMES.get(player_class, [f'{player_class}.png'])
    normalized_targets = set()
    candidate_names: List[str] = []
    for raw_name in raw_names + [f'{player_class}.png', f'{player_class}_Player.png', f'{player_class} Player.png']:
        if raw_name not in candidate_names:
            candidate_names.append(raw_name)
        stem = os.path.splitext(raw_name)[0]
        normalized_targets.add(''.join(ch.lower() for ch in stem if ch.isalnum()))
    normalized_targets.add(''.join(ch.lower() for ch in player_class if ch.isalnum()))
    search_dirs = [
        os.path.join(base_dir, 'Assets', 'Heroes'),
        os.path.join(base_dir, 'Assets', 'PlayerHeroes'),
        os.path.join(base_dir, 'Assets', 'Characters'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    for directory in search_dirs:
        if not os.path.isdir(directory):
            continue
        for name in candidate_names:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                return path
        for root, _dirs, files in os.walk(directory):
            for file_name in files:
                if not file_name.lower().endswith('.png'):
                    continue
                normalized_file = ''.join(ch.lower() for ch in os.path.splitext(file_name)[0] if ch.isalnum())
                if normalized_file in normalized_targets:
                    return os.path.join(root, file_name)
                if any(target in normalized_file for target in normalized_targets) and 'monster' not in normalized_file:
                    return os.path.join(root, file_name)
    return None
def _hero_data_uri(player_class: str) -> str:
    return _image_path_to_data_uri(_find_hero_asset_path(player_class))
HERO_DATA_URIS = {class_name: _hero_data_uri(class_name) for class_name in CLASS_ORDER}
def _find_town_scene_path() -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(base_dir, 'Assets', 'TownScene'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    preferred_names = [
        'Town.png',
        'Town Scene.png',
        'TownScene.png',
        'Town_Map.png',
        'TownMap.png',
    ]
    for directory in search_dirs:
        for name in preferred_names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    for directory in search_dirs:
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                if name.lower().endswith('.png') and 'town' in name.lower():
                    return os.path.join(directory, name)
    return None
def _town_scene_data_uri() -> str:
    return _image_path_to_data_uri(_find_town_scene_path())
TOWN_SCENE_DATA_URI = _town_scene_data_uri()
PERSISTENT_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'masterquest_nicegui_saves.json')

def clean_character_name(raw_name: str) -> str:
    cleaned = ' '.join((raw_name or '').strip().split())
    if not cleaned:
        return 'Hero'
    return cleaned[:24]

def normalize_unlocked_classes(value) -> set[str]:
    unlocked = {'Fighter', 'Mage'}
    if isinstance(value, (list, tuple, set)):
        for class_name in value:
            if isinstance(class_name, str) and class_name in CLASS_ORDER:
                unlocked.add(class_name)
    return unlocked

def build_default_slot_payload() -> Dict[str, object]:
    return {
        'player': None,
        'saved_item_sets': saved_item_sets_to_payload(empty_saved_item_sets()),
        'vault_items': [],
        'ladder_stats': build_default_ladder_stats(),
        'unlocked_classes': ['Fighter', 'Mage'],
        'selection_return_class': None,
    }

def load_persisted_slots() -> List[Dict[str, object]]:
    slots = [build_default_slot_payload() for _ in range(3)]
    if not os.path.exists(PERSISTENT_SAVE_PATH):
        return slots
    try:
        with open(PERSISTENT_SAVE_PATH, 'r', encoding='utf-8') as handle:
            payload = json.load(handle)
        raw_slots = payload.get('slots', []) if isinstance(payload, dict) else []
        if not isinstance(raw_slots, list):
            return slots
        for index in range(min(3, len(raw_slots))):
            raw_slot = raw_slots[index]
            if not isinstance(raw_slot, dict):
                continue
            slot = build_default_slot_payload()
            slot['player'] = raw_slot.get('player') if isinstance(raw_slot.get('player'), dict) else None
            slot['saved_item_sets'] = raw_slot.get('saved_item_sets', slot['saved_item_sets'])
            vault_items = raw_slot.get('vault_items', [])
            slot['vault_items'] = vault_items if isinstance(vault_items, list) else []
            slot['ladder_stats'] = raw_slot.get('ladder_stats', slot['ladder_stats'])
            slot['unlocked_classes'] = sorted(normalize_unlocked_classes(raw_slot.get('unlocked_classes')))
            selection_return_class = raw_slot.get('selection_return_class')
            slot['selection_return_class'] = selection_return_class if isinstance(selection_return_class, str) and selection_return_class in CLASS_ORDER else None
            slot['monster_chain_combo'] = int(raw_slot.get('monster_chain_combo', 0) or 0)
            slots[index] = slot
    except Exception:
        return slots
    return slots

def persist_slots(slots: List[Dict[str, object]]) -> None:
    try:
        with open(PERSISTENT_SAVE_PATH, 'w', encoding='utf-8') as handle:
            json.dump({'slots': slots}, handle, indent=2)
    except Exception:
        pass
def _find_marketplace_scene_path() -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(base_dir, 'Assets', 'Marketplace'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    preferred_names = [
        'Marketplace.png',
        'Marketplace Scene.png',
        'MarketplaceScene.png',
        'Market.png',
    ]
    for directory in search_dirs:
        for name in preferred_names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    for directory in search_dirs:
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                low = name.lower()
                if low.endswith('.png') and ('market' in low or 'bazaar' in low):
                    return os.path.join(directory, name)
    return None
def _marketplace_scene_data_uri() -> str:
    path = _find_marketplace_scene_path()
    if path is None:
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except Exception:
        return ''
MARKETPLACE_SCENE_DATA_URI = _marketplace_scene_data_uri()
def _find_transmutation_scene_path() -> Optional[str]:
    cwd = os.getcwd()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(cwd, 'Assets', 'Transmutation'),
        os.path.join(cwd, 'Assets'),
        os.path.join(base_dir, 'Assets', 'Transmutation'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    candidate_names = [
        'Transmutation.png',
        'transmutation.png',
        'Transmute.png',
        'transmute.png',
    ]
    for directory in search_dirs:
        for name in candidate_names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
        if os.path.isdir(directory):
            for name in os.listdir(directory):
                if name.lower().endswith('.png') and 'transmut' in name.lower():
                    return os.path.join(directory, name)
    return None
def _transmutation_scene_data_uri() -> str:
    path = _find_transmutation_scene_path()
    if path is None:
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except Exception:
        return ''
TRANSMUTATION_SCENE_DATA_URI = _transmutation_scene_data_uri()

def _find_well_scene_path() -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(base_dir, 'Assets', 'WellOfEvil'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    preferred_names = [
        'Well_Of_Evil.png',
        'Well_of_Evil.png',
        'Well of Evil.png',
        'WellOfEvil.png',
    ]
    for directory in search_dirs:
        for name in preferred_names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    for directory in search_dirs:
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                low = name.lower()
                if low.endswith('.png') and 'well' in low:
                    return os.path.join(directory, name)
    return None

def _well_scene_data_uri() -> str:
    path = _find_well_scene_path()
    if path is None:
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except Exception:
        return ''

WELL_SCENE_DATA_URI = _well_scene_data_uri()


def _find_inn_scene_path() -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        r'C:\Users\Pierre-Luc Purtell\Desktop\MasterQuest\NiceGUIVersion\Assets\Inn',
        os.path.join(base_dir, 'Assets', 'Inn'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    preferred_names = [
        'Inn.png',
        'Inn Scene.png',
        'InnScene.png',
        'The Inn.png',
    ]
    for directory in search_dirs:
        for name in preferred_names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    for directory in search_dirs:
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                low = name.lower()
                if low.endswith('.png') and 'inn' in low:
                    return os.path.join(directory, name)
    return None

def _inn_scene_data_uri() -> str:
    path = _find_inn_scene_path()
    if path is None:
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except Exception:
        return ''

INN_SCENE_DATA_URI = _inn_scene_data_uri()

def _find_well_monster_asset_path(index: int) -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(base_dir, 'Assets', 'WellMonsters'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    preferred_names = [
        f'Well_Monster{index + 1}.png',
        f'Well Monster {index + 1}.png',
        f'WellMonster{index + 1}.png',
    ]
    for directory in search_dirs:
        for name in preferred_names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    return None

def _well_monster_data_uri(index: int) -> str:
    key = f'__well__{int(index) % 5}'
    if key in MONSTER_DATA_URI_CACHE:
        return MONSTER_DATA_URI_CACHE[key]
    path = _find_well_monster_asset_path(int(index) % 5)
    if path is None:
        MONSTER_DATA_URI_CACHE[key] = ''
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        uri = f'data:image/png;base64,{encoded}'
    except Exception:
        uri = ''
    MONSTER_DATA_URI_CACHE[key] = uri
    return uri
MONSTER_ASSET_FILENAMES = {
    'Fallen': ['Fallen.png'],
    'Skeleton': ['Skeleton.png'],
    'Bandit': ['Bandit.png'],
    'Ghoul': ['Ghoul.png'],
    'Dark Wolf': ['Dark_Wolf.png', 'Dark Wolf.png'],
    'Cultist': ['Cultist.png'],
    'Harpy': ['Harpy.png'],
    'Mire Witch': ['Mire_Witch.png', 'Mire Witch.png'],
    'Ravager': ['Ravager.png'],
    'Succubus': ['Succubus.png'],
    'Bogling': ['Bogling.png'],
    'Cave Spider': ['Cave_spider.png', 'Cave Spider.png'],
    'Murloc': ['Murloc.png'],
    'Wraith': ['Wraith.png'],
    'Salamander': ['Salamander.png'],
    'Shade Archer': ['Shade_Archer.png', 'Shade Archer.png'],
    'Hollow Knight': ['Hollow_Knight.png', 'Hollow Knight.png'],
    'Templar': ['Templar.png'],
}
MONSTER_DATA_URI_CACHE: Dict[str, str] = {}
MONSTER_ASSET_PATH_CACHE: Dict[str, str] = {}
SAVED_ITEM_SET_ORDER = ['axe', 'dagger', 'staff', 'light_armor', 'medium_armor', 'heavy_armor', 'fire_charm', 'ice_charm', 'lightning_charm']
SAVED_ITEM_SET_LABELS = {
    'axe': 'Axe',
    'dagger': 'Dagger',
    'staff': 'Staff',
    'light_armor': 'Light Armor',
    'medium_armor': 'Medium Armor',
    'heavy_armor': 'Heavy Armor',
    'fire_charm': 'Fire Charm',
    'ice_charm': 'Ice Charm',
    'lightning_charm': 'Lightning Charm',
}
MASTERQUEST_PASS_DENOMINATORS = {
    'Fighter': 3,
    'Mage': 3,
    'Samurai': 6,
    'Paladin': 10,
    'Monk': 15,
    'Ninja': 21,
    'Warlock': 28,
    'Headhunter': 36,
    'Alchemist': 45,
}
INVENTORY_VIEW_OPTIONS = ['Inventory', 'Saved Sets']
ITEM_TYPE_FILTER_OPTIONS = ['All types'] + [SAVED_ITEM_SET_LABELS[key] for key in SAVED_ITEM_SET_ORDER]
INVENTORY_SORT_OPTIONS = ['Level (High-Low)', 'Level (Low-High)', 'Rarity', 'Name', 'Sell Value']
EQUIPMENT_ASSET_FILENAMES = {
    ('weapon', 'Axe'): ['Axe.png'],
    ('weapon', 'Dagger'): ['Dagger.png'],
    ('weapon', 'Staff'): ['Staff.png'],
    ('armor', 'Light'): ['Light_Armour.png', 'Light_Armor.png'],
    ('armor', 'Medium'): ['Medium_Armour.png', 'Medium_Armor.png'],
    ('armor', 'Heavy'): ['Heavy_Armour.png', 'Heavy_Armor.png'],
    ('charm', 'Fire'): ['Fire_Charm.png', 'Fire Charm.png'],
    ('charm', 'Ice'): ['Ice_Charm.png', 'Ice Charm.png'],
    ('charm', 'Lightning'): ['Lightning_Charm.png', 'Lightning Charm.png'],
}
EQUIPMENT_DATA_URI_CACHE: Dict[Tuple[str, str], str] = {}
def empty_saved_item_sets() -> Dict[str, Dict[int, Item]]:
    return {slot: {} for slot in SAVED_ITEM_SET_ORDER}
def _equipment_candidate_filenames(slot: str, subtype: str) -> List[str]:
    names = list(EQUIPMENT_ASSET_FILENAMES.get((slot, subtype), []))
    if not names:
        compact = subtype.replace(' ', '_') if subtype else slot.title()
        names.extend([f'{compact}.png', f'{slot.title()}.png'])
    seen: List[str] = []
    for name in names:
        if name not in seen:
            seen.append(name)
    return seen
def _find_equipment_asset_path(slot: str, subtype: str) -> Optional[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(base_dir, 'Assets', 'Equipment'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        '/mnt/data',
    ]
    for directory in search_dirs:
        for name in _equipment_candidate_filenames(slot, subtype):
            path = os.path.join(directory, name)
            if os.path.exists(path):
                return path
    return None
def _equipment_data_uri(slot: str, subtype: str) -> str:
    key = (slot or '', subtype or '')
    if key in EQUIPMENT_DATA_URI_CACHE:
        return EQUIPMENT_DATA_URI_CACHE[key]
    path = _find_equipment_asset_path(slot, subtype)
    if path is None:
        EQUIPMENT_DATA_URI_CACHE[key] = ''
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        uri = f'data:image/png;base64,{encoded}'
    except Exception:
        uri = ''
    EQUIPMENT_DATA_URI_CACHE[key] = uri
    return uri
def item_icon_uri(item: Optional[Item]) -> str:
    if item is None:
        return ''
    return _equipment_data_uri(item.slot, item.subtype)
def equipped_summary_text(player: Optional[Player]) -> str:
    if player is None:
        return 'No adventurer is currently active.'
    weapon = player.equipped.get('weapon')
    armor = player.equipped.get('armor')
    charm = player.equipped.get('charm')
    return (
        f'Weapon: {weapon.summary() if weapon else "Empty"}\n'
        f'Armor: {armor.summary() if armor else "Empty"}\n'
        f'Charm: {charm.summary() if charm else "Empty"}'
    )
def saved_item_set_key(slot: str, subtype: str) -> Optional[str]:
    slot = str(slot or '').lower()
    subtype = str(subtype or '').lower()
    if slot == 'weapon':
        mapping = {'axe': 'axe', 'dagger': 'dagger', 'staff': 'staff'}
        return mapping.get(subtype)
    if slot == 'armor':
        mapping = {'light': 'light_armor', 'medium': 'medium_armor', 'heavy': 'heavy_armor'}
        return mapping.get(subtype)
    if slot == 'charm':
        mapping = {'fire': 'fire_charm', 'ice': 'ice_charm', 'lightning': 'lightning_charm'}
        return mapping.get(subtype)
    return None

def saved_item_type_label(item: Optional[Item]) -> str:
    if item is None:
        return ''
    key = saved_item_set_key(getattr(item, 'slot', ''), getattr(item, 'subtype', ''))
    return SAVED_ITEM_SET_LABELS.get(key, getattr(item, 'subtype', '') or getattr(item, 'slot', '').title())

def get_saved_item_category(item: Item) -> Optional[str]:
    return saved_item_set_key(getattr(item, 'slot', ''), getattr(item, 'subtype', ''))

def masterquest_pass_denominator(player_class: str) -> int:
    return int(MASTERQUEST_PASS_DENOMINATORS.get(str(player_class or ''), 999999))
def item_matches_attribute(item: Item, attribute_key: str) -> bool:
    if attribute_key == 'attack_damage':
        return item.slot in {'weapon', 'charm'}
    if attribute_key == 'physical_armor':
        return item.slot == 'armor'
    if attribute_key == 'magic_resistance':
        return item.slot == 'armor'
    if attribute_key == 'mana_cost':
        return item.slot == 'charm'
    if attribute_key == 'enhanced_effect':
        return 'enhanced_effect' in item.affix_stats
    return attribute_key in item.affix_stats
def item_detail_lines(item: Optional[Item]) -> List[str]:
    if item is None:
        return ['No item selected.']
    lines: List[str] = [item.summary(), f'Rarity {item.rarity}']
    if item.slot in {'weapon', 'charm'}:
        low, high = item.get_scaled_base_range('attack_damage')
        lines.append(f'Damage {low}-{high}')
    if item.slot == 'armor':
        low, high = item.get_scaled_base_range('physical_armor')
        r_low, r_high = item.get_scaled_base_range('magic_resistance')
        lines.append(f'Physical Armor {low}-{high}')
        lines.append(f'Magic Resistance {r_low}-{r_high}')
    if item.slot == 'charm':
        lines.append(f'Mana Cost {get_charm_mana_cost(bucket_item_level(item.level))}')
    if item.affix_stats:
        for key in STAT_ORDER:
            if key in item.affix_stats:
                lines.append(format_stat_value(key, item.affix_stats[key], int(getattr(item, 'level', 1) or 1)))
    else:
        lines.append('No affix bonuses')
    lines.append(f'Sell Value {item.sell_value()} gold')
    return lines
def tooltip_title_text(text: str) -> str:
    return html.escape((text or '').replace('\r', ''), quote=True).replace('\n', '&#10;')
def hoverable_item_name_html(item: Optional[Item], empty_text: str = 'None') -> str:
    if item is None:
        return f"<span class='mq-item-name-muted'>{html.escape(empty_text)}</span>"
    title = tooltip_title_text('\n'.join(item_detail_lines(item)))
    return f"<span class='mq-hover-name' title=\"{title}\">{html.escape(item.name)}</span>"
def coerce_item(item: object) -> Optional[Item]:
    if isinstance(item, Item):
        return item
    if isinstance(item, dict):
        try:
            return Item.from_dict(item)
        except Exception:
            return None
    return None
def safe_item_summary(item: Optional[Item], empty_text: str = 'No item selected.') -> str:
    if item is None:
        return empty_text
    try:
        return item.summary()
    except Exception:
        return getattr(item, 'name', empty_text) or empty_text
def safe_item_short_stat_text(item: Optional[Item], empty_text: str = 'No bonuses') -> str:
    if item is None:
        return empty_text
    try:
        return item.short_stat_text()
    except Exception:
        return empty_text
def safe_item_base_stat_text(item: Optional[Item], empty_text: str = 'No base stats') -> str:
    if item is None:
        return empty_text
    try:
        parts: List[str] = []
        if item.slot in {'weapon', 'charm'}:
            low, high = item.get_scaled_base_range('attack_damage')
            parts.append(f'DMG {low}-{high}')
        if item.slot == 'armor':
            low, high = item.get_scaled_base_range('physical_armor')
            r_low, r_high = item.get_scaled_base_range('magic_resistance')
            parts.append(f'ARM {low}-{high}')
            parts.append(f'MRES {r_low}-{r_high}')
        if item.slot == 'charm':
            parts.append(f'Mana {get_charm_mana_cost(item_required_level(item))}')
        return ' • '.join(parts) if parts else empty_text
    except Exception:
        return empty_text
def safe_item_affix_preview_text(item: Optional[Item], empty_text: str = 'No affixes') -> str:
    if item is None:
        return empty_text
    try:
        parts: List[str] = []
        for key in STAT_ORDER:
            if key in getattr(item, 'affix_stats', {}):
                parts.append(format_stat_value(key, item.affix_stats[key], int(getattr(item, 'level', 1) or 1)))
        return ' • '.join(parts[:2]) if parts else empty_text
    except Exception:
        return empty_text
def inventory_base_detail_rows(item: Optional[Item]) -> List[Tuple[str, str]]:
    if item is None:
        return []
    rows: List[Tuple[str, str]] = []
    if item.slot in {'weapon', 'charm'}:
        low, high = item.get_scaled_base_range('attack_damage')
        rows.append(('Base Damage', f'{low}-{high}'))
    if item.slot == 'armor':
        low, high = item.get_scaled_base_range('physical_armor')
        r_low, r_high = item.get_scaled_base_range('magic_resistance')
        rows.append(('Physical Armor', f'{low}-{high}'))
        rows.append(('Magic Resistance', f'{r_low}-{r_high}'))
    if item.slot == 'charm':
        rows.append(('Mana Cost', str(get_charm_mana_cost(item_required_level(item)))))
    return rows
def inventory_affix_theme_class(stat_key: str) -> str:
    if stat_key in {'strength', 'crit_chance', 'crit_damage', 'armor_penetration', 'attack_damage', 'accuracy'}:
        return 'offense'
    if stat_key in {'dexterity', 'lifesteal', 'evasion'}:
        return 'finesse'
    if stat_key in {'vitality', 'max_health', 'life_regen', 'life_per_kill', 'thorns', 'physical_armor', 'magic_resistance'}:
        return 'vitality'
    if stat_key in {'intelligence', 'max_mana', 'mana_regen', 'mana_per_kill', 'mana_cost', 'enhanced_effect'}:
        return 'arcane'
    if stat_key in {'magic_find', 'xp_gain'}:
        return 'utility'
    return 'neutral'
def inventory_affix_rows(item: Optional[Item]) -> List[Tuple[str, str, str]]:
    if item is None:
        return []
    rows: List[Tuple[str, str, str]] = []
    affix_stats = getattr(item, 'affix_stats', {}) or {}
    for key in STAT_ORDER:
        if key in affix_stats:
            rows.append((key, format_stat_value(key, affix_stats[key], int(getattr(item, 'level', 1) or 1)), inventory_affix_theme_class(key)))
    return rows
def inventory_base_detail_html(item: Optional[Item]) -> str:
    rows = inventory_base_detail_rows(item)
    if not rows:
        return "<div class='mq-base-stat-list'><div class='mq-base-line'><span class='mq-base-label'>Base Profile</span><span class='mq-base-value'>None</span></div></div>"
    html_rows = ''.join(
        f"<div class='mq-base-line'><span class='mq-base-label'>{html.escape(label)}</span><span class='mq-base-value'>{html.escape(value)}</span></div>"
        for label, value in rows
    )
    return f"<div class='mq-base-stat-list'>{html_rows}</div>"
def inventory_affix_detail_html(item: Optional[Item]) -> str:
    rows = inventory_affix_rows(item)
    if not rows:
        return "<div class='mq-affix-stat-list'><div class='mq-affix-line neutral'><span class='mq-affix-text'>No affixes on this item.</span></div></div>"
    html_rows = ''.join(
        f"<div class='mq-affix-line {css_class}'><span class='mq-affix-text'>{html.escape(text)}</span></div>"
        for _key, text, css_class in rows
    )
    return f"<div class='mq-affix-stat-list'>{html_rows}</div>"
def safe_item_detail_text(item: Optional[Item]) -> str:
    try:
        return '\n'.join(item_detail_lines(item))
    except Exception:
        return 'No item selected.' if item is None else safe_item_summary(item)
def safe_item_name(item: Optional[Item], empty_text: str = 'Unknown Item') -> str:
    if item is None:
        return empty_text
    name = getattr(item, 'name', '')
    return str(name).strip() or empty_text
def safe_item_sell_value(item: Optional[Item]) -> int:
    if item is None:
        return 0
    try:
        return int(item.sell_value())
    except Exception:
        return 0
def safe_rarity_badge_html(item: Optional[Item]) -> str:
    rarity = getattr(item, 'rarity', 'Unknown') if item is not None else 'Unknown'
    return rarity_badge_html(str(rarity))

def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
    color = str(color or '').strip().lstrip('#')
    if len(color) != 6:
        return (156, 163, 175)
    try:
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (156, 163, 175)

def rarity_edge_style(item: Optional[Item]) -> str:
    rarity = str(getattr(item, 'rarity', 'Common') or 'Common') if item is not None else 'Common'
    color = RARITY_COLORS.get(rarity, '#9ca3af')
    r, g, b = _hex_to_rgb(color)
    return f'border-color: rgba({r}, {g}, {b}, 0.88); box-shadow: inset 0 0 0 1px rgba({r}, {g}, {b}, 0.22);'
ITEM_SLOT_SORT_ORDER = {'weapon': 0, 'armor': 1, 'charm': 2}
def item_required_level(item: Optional[Item]) -> int:
    if item is None:
        return 1
    try:
        return bucket_item_level(int(getattr(item, 'level', 1) or 1))
    except Exception:
        return 1
def can_player_equip_item(player: Optional['Player'], item: Optional[Item]) -> Tuple[bool, str]:
    if player is None or item is None:
        return (False, 'No item is selected.')
    required_level = item_required_level(item)
    if int(getattr(player, 'level', 1) or 1) < required_level:
        return (False, f'Requires level {required_level}.')
    rules = CLASS_EQUIP_RULES.get(getattr(player, 'player_class', ''), {})
    slot = str(getattr(item, 'slot', '') or '')
    subtype = str(getattr(item, 'subtype', '') or '')
    if slot == 'weapon':
        allowed = rules.get('weapon')
        if allowed is not None and subtype not in allowed:
            return (False, f'{player.player_class} cannot equip {subtype or slot.title()} weapons.')
    elif slot == 'armor':
        allowed = rules.get('armor')
        if allowed is not None and subtype not in allowed:
            return (False, f'{player.player_class} cannot equip {subtype or slot.title()} armor.')
    return (True, '')
def inventory_tier_spread_text(items: List[Item]) -> str:
    counts: Dict[int, int] = {}
    for item in items:
        try:
            tier = item_required_level(item)
        except Exception:
            tier = 1
        counts[tier] = counts.get(tier, 0) + 1
    parts = [f'T{tier}×{counts[tier]}' for tier in ITEM_BUCKETS if counts.get(tier)]
    return ' • '.join(parts) if parts else 'No items in your bag.'
def saved_set_summary_text(saved_item_sets: Dict[str, Dict[int, Item]]) -> str:
    parts: List[str] = []
    total = 0
    for slot in SAVED_ITEM_SET_ORDER:
        slot_items = saved_item_sets.get(slot, {})
        count = len(slot_items) if isinstance(slot_items, dict) else 0
        total += count
        parts.append(f"{SAVED_ITEM_SET_LABELS.get(slot, slot.title())} {count}")
    return f"{' • '.join(parts)} • Total {total}"
def inventory_item_compare_lines(item: Optional[Item]) -> List[str]:
    if item is None:
        return ['No item selected.']
    lines: List[str] = []
    if item.slot in {'weapon', 'charm'}:
        low, high = item.get_scaled_base_range('attack_damage')
        lines.append(f'Damage {low}-{high}')
    if item.slot == 'armor':
        low, high = item.get_scaled_base_range('physical_armor')
        r_low, r_high = item.get_scaled_base_range('magic_resistance')
        lines.append(f'Physical Armor {low}-{high}')
        lines.append(f'Magic Resistance {r_low}-{r_high}')
    if item.slot == 'charm':
        lines.append(f'Mana Cost {get_charm_mana_cost(item_required_level(item))}')
    if item.affix_stats:
        for key in STAT_ORDER:
            if key in item.affix_stats:
                lines.append(format_stat_value(key, item.affix_stats[key], int(getattr(item, 'level', 1) or 1)))
    else:
        lines.append('No affix bonuses')
    return lines
def active_proficiency_keys(player: Optional['Player']) -> List[str]:
    if player is None:
        return []
    active: List[str] = []
    for slot in ('weapon', 'charm'):
        item = player.equipped.get(slot)
        if item is None:
            continue
        key = get_proficiency_key(item.slot, item.subtype)
        if key and key not in active:
            active.append(key)
    return active
def build_proficiency_tooltip_text(player: Optional['Player']) -> str:
    if player is None:
        return 'No active adventurer.'
    levels = getattr(player, 'proficiency_levels', empty_proficiency_levels())
    progress = getattr(player, 'proficiency_progress', empty_proficiency_progress())
    active_keys = set(active_proficiency_keys(player))
    lines = [
        'Each level grants +1% Enhanced Effect with that weapon or charm family.',
        'You gain 1 proficiency point on each successful player hit.',
        '',
    ]
    for key in PROFICIENCY_TYPES:
        level = int(levels.get(key, 0))
        current = int(progress.get(key, 0))
        needed = proficiency_threshold_for_level(level)
        marker = '◆' if key in active_keys else '·'
        lines.append(f"{marker} {key:<16} Lv {level:<3}   {current:>4}/{needed:<4}   (+{level}% EE)")
    if active_keys:
        lines.append('')
        lines.append('Active loadout')
        lines.append('  ' + ' • '.join(active_proficiency_keys(player)))
    return '\n'.join(lines)

def build_proficiency_tooltip_html(player: Optional['Player']) -> str:
    if player is None:
        return "<div class='mq-prof-tooltip-empty'>No active adventurer.</div>"
    levels = getattr(player, 'proficiency_levels', empty_proficiency_levels())
    progress = getattr(player, 'proficiency_progress', empty_proficiency_progress())
    active_keys = set(active_proficiency_keys(player))
    rows: List[str] = []
    for key in PROFICIENCY_TYPES:
        level = int(levels.get(key, 0) or 0)
        current = int(progress.get(key, 0) or 0)
        needed = int(proficiency_threshold_for_level(level))
        row_class = ' active' if key in active_keys else ''
        marker = '◆' if key in active_keys else '◇'
        rows.append(
            "<div class='mq-prof-row%s'>"
            "<span class='mq-prof-marker'>%s</span>"
            "<span class='mq-prof-name'>%s</span>"
            "<span class='mq-prof-level'>Lv %s</span>"
            "<span class='mq-prof-progress'>%s / %s</span>"
            "<span class='mq-prof-bonus'>+%s%% EE</span>"
            "</div>"
            % (
                row_class,
                marker,
                html.escape(key),
                level,
                current,
                needed,
                level,
            )
        )
    if active_keys:
        active_text = html.escape(' • '.join(active_proficiency_keys(player)))
    else:
        active_text = 'No active weapon or charm proficiency'
    return (
        "<div class='mq-prof-tooltip-card'>"
        "<div class='mq-prof-title'>Proficiency Ledger</div>"
        "<div class='mq-prof-sub'>Each successful player hit grants 1 proficiency point. Every level in that family adds +1%% Enhanced Effect.</div>"
        "<div class='mq-prof-grid'>%s</div>"
        "<div class='mq-prof-active'><span class='mq-prof-active-label'>Active Loadout</span><span class='mq-prof-active-value'>%s</span></div>"
        "</div>"
    ) % (''.join(rows), active_text)

def active_proficiency_summary(player: Optional['Player']) -> str:
    keys = active_proficiency_keys(player)
    if not keys:
        return 'No active weapon or charm proficiency'
    parts = []
    levels = getattr(player, 'proficiency_levels', empty_proficiency_levels()) if player is not None else {}
    for key in keys:
        level = int(levels.get(key, 0))
        parts.append(f"{key} Lv {level}")
    return ' • '.join(parts)

def item_rarity_sort_key(item: Item) -> int:
    try:
        return RARITY_ORDER.index(item.rarity)
    except ValueError:
        return -1
def saved_item_sets_to_payload(saved_item_sets: Dict[str, Dict[int, Item]]) -> Dict[str, Dict[str, Dict]]:
    payload: Dict[str, Dict[str, Dict]] = {}
    for slot, items in saved_item_sets.items():
        normalized_items: Dict[str, Dict] = {}
        if not isinstance(items, dict):
            payload[slot] = normalized_items
            continue
        for level, raw_item in items.items():
            item = coerce_item(raw_item)
            if item is None:
                continue
            try:
                level_key = str(int(level))
            except Exception:
                level_key = str(bucket_item_level(int(getattr(item, 'level', 1) or 1)))
            normalized_items[level_key] = item.to_dict()
        payload[slot] = normalized_items
    return payload
def saved_item_sets_from_payload(payload: Optional[Dict[str, Dict[str, Dict]]]) -> Dict[str, Dict[int, Item]]:
    data = empty_saved_item_sets()
    if not payload:
        return data
    for category, items in payload.items():
        if not isinstance(items, dict):
            continue
        for level, item_data in items.items():
            try:
                item = Item.from_dict(item_data)
            except Exception:
                continue
            normalized_category = category if category in data else get_saved_item_category(item)
            if normalized_category is None:
                continue
            try:
                level_key = int(level)
            except Exception:
                level_key = bucket_item_level(int(getattr(item, 'level', 1) or 1))
            data[normalized_category][level_key] = item
    return data
def monster_species_name(monster_type: str) -> str:
    if not monster_type:
        return ''
    return str(monster_type).split(' Lv ')[0].strip()

def monster_theme_style(monster_type: str) -> str:
    species = monster_species_name(monster_type)
    theme = MONSTER_THEME_MAP.get(species, DEFAULT_MONSTER_THEME)
    rgb = theme.get('rgb', DEFAULT_MONSTER_THEME['rgb'])
    shell = theme.get('shell', DEFAULT_MONSTER_THEME['shell'])
    deep = theme.get('deep', DEFAULT_MONSTER_THEME['deep'])
    return '; '.join([
        f'--mq-monster-rgb: {rgb}',
        f'--mq-monster-shell: {shell}',
        f'--mq-monster-deep: {deep}',
    ])

def _monster_asset_token(text: str) -> str:
    return ''.join(ch.lower() for ch in str(text or '') if ch.isalnum())

def _candidate_monster_filenames(monster_type: str) -> List[str]:
    species = monster_species_name(monster_type)
    preset = MONSTER_ASSET_FILENAMES.get(species, [])
    compact = species.replace(' ', '_')
    dashed = species.replace(' ', '-')
    flat = ''.join(ch for ch in species if ch.isalnum())
    raw = [
        f'{species}.png',
        f'{compact}.png',
        f'{compact.lower()}.png',
        f'{dashed}.png',
        f'{species.lower()}.png',
        f'{flat}.png',
        f'{flat.lower()}.png',
        f'{compact}_Monster.png',
        f'{compact.lower()}_monster.png',
        f'{compact}Monster.png',
        f'{compact.lower()}monster.png',
    ]
    seen: List[str] = []
    for name in preset + raw:
        if name not in seen:
            seen.append(name)
    return seen

def _arena_monster_search_dirs() -> List[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    explicit_windows_dir = r'C:\Users\Pierre-Luc Purtell\Desktop\MasterQuest\NiceGUIVersion\Assets\ArenaMonsters'
    candidates = [
        os.path.join(base_dir, 'Assets', 'ArenaMonsters'),
        os.path.join(base_dir, 'Assets', 'Arena Monsters'),
        os.path.join(base_dir, 'Assets'),
        base_dir,
        os.path.join(cwd, 'Assets', 'ArenaMonsters'),
        os.path.join(cwd, 'Assets', 'Arena Monsters'),
        os.path.join(cwd, 'Assets'),
        cwd,
        explicit_windows_dir,
        '/mnt/data',
    ]
    seen: List[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        normalized = os.path.normpath(candidate)
        if normalized not in seen:
            seen.append(normalized)
    return seen

def _find_arena_monster_asset_path(monster_type: str) -> Optional[str]:
    species = monster_species_name(monster_type)
    if not species:
        return None
    cached_path = MONSTER_ASSET_PATH_CACHE.get(species)
    if cached_path and os.path.isfile(cached_path):
        return cached_path
    candidate_names = _candidate_monster_filenames(species)
    candidate_lowers = {name.lower() for name in candidate_names}
    candidate_stems = {_monster_asset_token(os.path.splitext(name)[0]) for name in candidate_names}
    species_tokens = [token.lower() for token in species.replace('-', ' ').replace('_', ' ').split() if token]
    valid_exts = {'.png', '.webp', '.jpg', '.jpeg'}
    for directory in _arena_monster_search_dirs():
        if not os.path.isdir(directory):
            continue
        for name in candidate_names:
            exact_path = os.path.join(directory, name)
            if os.path.isfile(exact_path):
                MONSTER_ASSET_PATH_CACHE[species] = exact_path
                return exact_path
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in valid_exts:
                    continue
                lower_name = file_name.lower()
                if lower_name in candidate_lowers:
                    resolved = os.path.join(root, file_name)
                    MONSTER_ASSET_PATH_CACHE[species] = resolved
                    return resolved
                normalized = _monster_asset_token(os.path.splitext(file_name)[0])
                if normalized in candidate_stems:
                    resolved = os.path.join(root, file_name)
                    MONSTER_ASSET_PATH_CACHE[species] = resolved
                    return resolved
                if species_tokens:
                    spaced_name = lower_name.replace('_', ' ').replace('-', ' ')
                    if all(token in spaced_name for token in species_tokens):
                        resolved = os.path.join(root, file_name)
                        MONSTER_ASSET_PATH_CACHE[species] = resolved
                        return resolved
    return None

def _arena_monster_data_uri(monster_type: str) -> str:
    species = monster_species_name(monster_type)
    if not species:
        return ''
    cached = MONSTER_DATA_URI_CACHE.get(species)
    if cached:
        return cached
    path = _find_arena_monster_asset_path(species)
    if path is None:
        return ''
    try:
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        ext = os.path.splitext(path)[1].lower()
        mime = 'image/png'
        if ext == '.webp':
            mime = 'image/webp'
        elif ext in {'.jpg', '.jpeg'}:
            mime = 'image/jpeg'
        uri = f'data:{mime};base64,{encoded}'
    except Exception:
        uri = ''
    if uri:
        MONSTER_DATA_URI_CACHE[species] = uri
    return uri

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
def meter_fill_pct(current: int, maximum: int) -> float:
    if maximum <= 0:
        return 0.0
    return clamp((current / maximum) * 100.0, 0.0, 100.0)
def attack_mode_label(player: Player) -> str:
    if player.damage_school == 'magic' and player.spell_attack_max > 0 and player.mana >= player.cast_mana_cost > 0:
        return f'Spell {player.spell_attack_min}-{player.spell_attack_max} • Cost {player.cast_mana_cost}'
    if player.weapon_attack_max > 0:
        return f'Weapon {player.weapon_attack_min}-{player.weapon_attack_max}'
    return f'Base {player.attack_min}-{player.attack_max}'
def format_log_html(event: CombatEvent) -> str:
    text = html.escape(event.text)
    classes = ['mq-log-line']
    if event.text.startswith('-- Round '):
        label = html.escape(event.text.strip().strip('-').strip())
        text = f'────────  {label}  ────────'
        classes.append('round')
    elif event.text.startswith('Enemy says:'):
        classes.append('quote')
    elif event.tag == 'muted':
        classes.append('system')
    if event.text.startswith('You defeated') or event.text.startswith('You were slain') or 'timed out in a draw' in event.text:
        classes.append('result')
    tone = {
        'success': 'success',
        'danger': 'danger',
        'warning': 'warning',
        'muted': 'system',
    }.get(event.tag)
    if tone:
        classes.append(tone)
    return f"<div class='{' '.join(classes)}'>{text}</div>"
def combat_log_widget_html(events: List[CombatEvent]) -> str:
    lines = ''.join(format_log_html(event) for event in events)
    return f"<div id='mq-combat-log' class='mq-combat-log w-full'>{lines}</div>"

def bucket_item_level(level: int) -> int:
    for bucket in reversed(ITEM_BUCKETS):
        if level >= bucket:
            return bucket
    return 1
def base_monster_xp(level: int) -> int:
    return 44 + (level * 18)

def xp_to_next_for_level(level: int) -> int:
    return base_monster_xp(level) * 6

def xp_multiplier_for_level_difference(player_level: int, monster_level: int) -> float:
    level_gap = max(0, player_level - monster_level)
    return max(0.0, 1.0 - (level_gap * 0.10))

def get_monster_chain_bonus_fraction(combo: int) -> float:
    return min(max(0, combo), 15) * 0.01
def get_base_item_roll_range(bucket_level: int) -> Tuple[int, int]:
    low = max(2, 2 + int(bucket_level * 1.7))
    high = max(low + 1, 5 + int(bucket_level * 2.4))
    return low, high
def get_charm_mana_cost(bucket_level: int) -> int:
    return 15 + ((bucket_level - 1) // 5) * 10
def get_core_stat_cap(bucket_level: int) -> int:
    return 1 + max(1, bucket_level // 5)
def get_enhanced_effect_cap(bucket_level: int) -> float:
    return round(min(1.35, 0.10 + (bucket_level / 5) * 0.06), 2)
def get_secondary_affix_roll_bounds(stat_key: str, item_level: int) -> Tuple[float, float]:
    ranges: Dict[str, Tuple[float, float]] = {
        'crit_chance': (0.0, min(0.03 + (item_level / 5) * 0.005, 0.16)),
        'crit_damage': (0.0, min(0.12 + (item_level / 5) * 0.05, 0.70)),
        'armor_penetration': (0.0, 1 + int(item_level / 4)),
        'lifesteal': (0.0, min(0.03 + (item_level / 5) * 0.01, 0.18)),
        'max_health': (0.0, 6 + int(item_level * 1.8)),
        'life_regen': (0.0, max(1, item_level // 10)),
        'life_per_kill': (0.0, 2 + int(item_level / 4)),
        'evasion': (0.0, min(0.025 + (item_level / 5) * 0.006, 0.18)),
        'max_mana': (0.0, 6 + int(item_level * 1.8)),
        'mana_regen': (0.0, max(1, item_level // 10)),
        'mana_per_kill': (0.0, 1 + int(item_level / 4)),
        'magic_find': (0.0, min(0.05 + (item_level / 5) * 0.012, 0.30)),
        'xp_gain': (0.0, min(0.05 + (item_level / 5) * 0.012, 0.30)),
        'thorns': (0.0, min(0.08 + (item_level / 5) * 0.012, 0.30)),
        'accuracy': (0.0, min(0.03 + (item_level / 5) * 0.006, 0.20)),
    }
    return ranges[stat_key]
def format_stat_value(stat_key: str, value: float, item_level: Optional[int] = None) -> str:
    label = STAT_LABELS.get(stat_key, stat_key.replace('_', ' ').title())
    if stat_key in {'crit_chance', 'lifesteal', 'evasion', 'magic_find', 'xp_gain', 'thorns', 'accuracy', 'enhanced_effect'}:
        display = int(round(value * 100.0))
        if display <= 0:
            display = max(1, int(math.ceil(abs(value) * 100.0))) if value else 1
        return f'{label} +{display}%'
    if stat_key == 'crit_damage':
        display = int(round(value * 100.0))
        if display <= 0:
            display = max(1, int(math.ceil(abs(value) * 100.0))) if value else 1
        return f'{label} +{display}%'
    display = int(round(value))
    if display <= 0:
        display = 1
    return f'{label} +{display}'
@dataclass
class Item:
    name: str
    slot: str
    level: int
    rarity: str
    subtype: str = ''
    base_stats: Dict[str, float] = field(default_factory=dict)
    affix_stats: Dict[str, float] = field(default_factory=dict)
    is_starter: bool = False
    def summary(self) -> str:
        prefix = f'{self.subtype} ' if self.subtype else ''
        return f'{self.name} [Lv {self.level} {prefix}{self.slot.title()}]'
    def enhanced_multiplier(self) -> float:
        return 1.0 + float(self.affix_stats.get('enhanced_effect', 0.0))
    def get_scaled_base_range(self, stat_key: str, extra_enhanced: float = 0.0) -> Tuple[int, int]:
        mult = self.enhanced_multiplier() + extra_enhanced
        low_key = f'{stat_key}_min'
        high_key = f'{stat_key}_max'
        if low_key in self.base_stats or high_key in self.base_stats:
            low = self.base_stats.get(low_key, self.base_stats.get(high_key, 0)) * mult
            high = self.base_stats.get(high_key, self.base_stats.get(low_key, 0)) * mult
        else:
            val = self.base_stats.get(stat_key, 0) * mult
            low = val
            high = val
        low_i = int(round(low))
        high_i = int(round(high))
        return (min(low_i, high_i), max(low_i, high_i))
    def total_stats(self) -> Dict[str, float]:
        return {k: v for k, v in self.affix_stats.items() if k != 'enhanced_effect'}
    def short_stat_text(self) -> str:
        parts: List[str] = []
        if self.slot in {'weapon', 'charm'}:
            low, high = self.get_scaled_base_range('attack_damage')
            parts.append(f'DMG {low}-{high}')
        if self.slot == 'armor':
            low, high = self.get_scaled_base_range('physical_armor')
            r_low, r_high = self.get_scaled_base_range('magic_resistance')
            parts.append(f'ARM {low}-{high}')
            parts.append(f'MRES {r_low}-{r_high}')
        if self.slot == 'charm':
            parts.append(f'Mana {get_charm_mana_cost(self.level)}')
        affixes = [format_stat_value(k, v, self.level) for k, v in self.affix_stats.items()]
        parts.extend(affixes[:3])
        return ' • '.join(parts) if parts else 'No bonuses'
    def sell_value(self) -> int:
        base = {'Common': 1, 'Fine': 2, 'Rare': 4, 'Epic': 7, 'Mythic': 11, 'Ancient': 16, 'Relic': 22, 'Ascendant': 29, 'Legendary': 37, 'Unspawnable': 55}[self.rarity]
        return base + max(0, self.level // 5)
    def to_dict(self) -> Dict:
        return asdict(self)
    @classmethod
    def from_dict(cls, data: Dict) -> 'Item':
        return cls(**data)
@dataclass
class Fighter:
    name: str
    level: int
    max_hp: int
    hp: int
    attack_min: int
    attack_max: int
    physical_armor: int
    magic_resistance: int
    speed: int
    accuracy: float
    crit_chance: float
    crit_damage: float
    armor_penetration: int
    lifesteal: float
    evasion: float
    thorns: float
    max_mana: int = 0
    mana: int = 0
    mana_regen: int = 0
    life_regen: int = 0
    mana_per_kill: int = 0
    life_per_kill: int = 0
    magic_find: float = 0.0
    damage_school: str = 'physical'
    monster_type: str = ''
    monster_personal_name: str = ''
    monster_kit: str = ''
    monster_profile: str = ''
    monster_dialogue: str = ''
    def is_alive(self) -> bool:
        return self.hp > 0
@dataclass
class Player(Fighter):
    player_class: str = 'Fighter'
    xp: int = 0
    xp_to_next: int = 100
    gold: int = 0
    wins: int = 0
    losses: int = 0
    base_strength: int = 0
    base_dexterity: int = 0
    base_intelligence: int = 0
    base_vitality: int = 0
    strength: int = 0
    dexterity: int = 0
    intelligence: int = 0
    vitality: int = 0
    unspent_stat_points: int = 0
    base_attack_min: int = 0
    base_attack_max: int = 0
    base_max_hp: int = 0
    base_physical_armor: int = 0
    base_magic_resistance: int = 0
    base_speed: int = 0
    base_accuracy: float = 0.85
    base_crit_chance: float = 0.10
    base_crit_damage: float = 1.50
    base_armor_penetration: int = 0
    base_lifesteal: float = 0.0
    base_evasion: float = 0.0
    base_max_mana: int = 0
    base_mana_regen: int = 0
    base_life_regen: int = 0
    base_mana_per_kill: int = 0
    base_life_per_kill: int = 0
    base_magic_find: float = 0.0
    base_xp_gain: float = 0.0
    base_thorns: float = 0.0
    xp_gain: float = 0.0
    cast_mana_cost: int = 0
    weapon_attack_min: int = 0
    weapon_attack_max: int = 0
    spell_attack_min: int = 0
    spell_attack_max: int = 0
    inventory: List[Item] = field(default_factory=list)
    equipped: Dict[str, Optional[Item]] = field(default_factory=lambda: {'weapon': None, 'armor': None, 'charm': None})
    proficiency_levels: Dict[str, int] = field(default_factory=empty_proficiency_levels)
    proficiency_progress: Dict[str, int] = field(default_factory=empty_proficiency_progress)
    def get_item_proficiency_bonus(self, item: Optional[Item]) -> float:
        if item is None:
            return 0.0
        key = get_proficiency_key(item.slot, item.subtype)
        if key is None:
            return 0.0
        return self.proficiency_levels.get(key, 0) * 0.01
    def grant_proficiency_point(self, proficiency_key: Optional[str], amount: int = 1) -> Tuple[int, int]:
        if proficiency_key is None or amount <= 0:
            return (0, 0)
        if proficiency_key not in self.proficiency_levels:
            self.proficiency_levels[proficiency_key] = 0
            self.proficiency_progress[proficiency_key] = 0
        old_level = self.proficiency_levels[proficiency_key]
        self.proficiency_progress[proficiency_key] += amount
        while self.proficiency_progress[proficiency_key] >= proficiency_threshold_for_level(self.proficiency_levels[proficiency_key]):
            threshold = proficiency_threshold_for_level(self.proficiency_levels[proficiency_key])
            self.proficiency_progress[proficiency_key] -= threshold
            self.proficiency_levels[proficiency_key] += 1
        new_level = self.proficiency_levels[proficiency_key]
        if new_level != old_level:
            self.recalculate_stats()
        return old_level, new_level
    def recalculate_stats(self) -> None:
        hp_ratio = self.hp / max(1, self.max_hp) if self.max_hp else 1.0
        mana_ratio = self.mana / max(1, self.max_mana) if self.max_mana else 1.0
        bonuses = {k: 0.0 for k in CORE_STAT_KEYS + SECONDARY_AFFIX_KEYS}
        for item in self.equipped.values():
            if item is None:
                continue
            for key, value in item.total_stats().items():
                bonuses[key] = bonuses.get(key, 0.0) + value
        self.strength = self.base_strength + int(round(bonuses.get('strength', 0)))
        self.dexterity = self.base_dexterity + int(round(bonuses.get('dexterity', 0)))
        self.intelligence = self.base_intelligence + int(round(bonuses.get('intelligence', 0)))
        self.vitality = self.base_vitality + int(round(bonuses.get('vitality', 0)))
        self.max_hp = max(1, self.base_max_hp + (self.vitality * 5) + int(round(bonuses.get('max_health', 0))))
        self.max_mana = max(0, self.base_max_mana + (self.intelligence * 5) + int(round(bonuses.get('max_mana', 0))))
        self.physical_armor = max(0, int(round(self.base_physical_armor + (self.vitality * 0.5) + bonuses.get('physical_armor', 0))))
        self.magic_resistance = max(0, int(round(self.base_magic_resistance + (self.intelligence * 0.5) + bonuses.get('magic_resistance', 0))))
        self.speed = max(1, int(round(self.base_speed + (self.dexterity * 0.2))))
        self.accuracy = clamp(self.base_accuracy + bonuses.get('accuracy', 0.0), 0.10, 0.99)
        self.crit_chance = clamp(self.base_crit_chance + bonuses.get('crit_chance', 0.0), 0.0, 0.85)
        self.crit_damage = clamp(self.base_crit_damage + bonuses.get('crit_damage', 0.0), 1.25, 4.0)
        self.armor_penetration = max(0, int(round(self.base_armor_penetration + bonuses.get('armor_penetration', 0))))
        self.lifesteal = clamp(self.base_lifesteal + bonuses.get('lifesteal', 0.0), 0.0, 0.5)
        self.evasion = clamp(self.base_evasion + bonuses.get('evasion', 0.0), 0.0, 0.35)
        self.thorns = clamp(self.base_thorns + bonuses.get('thorns', 0.0), 0.0, 0.5)
        self.magic_find = self.base_magic_find + bonuses.get('magic_find', 0.0)
        self.xp_gain = self.base_xp_gain + bonuses.get('xp_gain', 0.0)
        self.life_regen = max(0, self.base_life_regen + int(round(bonuses.get('life_regen', 0))))
        self.mana_regen = max(0, self.base_mana_regen + int(round(bonuses.get('mana_regen', 0))))
        self.life_per_kill = max(0, self.base_life_per_kill + int(round(bonuses.get('life_per_kill', 0))))
        self.mana_per_kill = max(0, self.base_mana_per_kill + int(round(bonuses.get('mana_per_kill', 0))))
        self.attack_min = self.base_attack_min
        self.attack_max = self.base_attack_max
        self.weapon_attack_min = self.base_attack_min
        self.weapon_attack_max = self.base_attack_max
        self.spell_attack_min = 0
        self.spell_attack_max = 0
        self.cast_mana_cost = 0
        weapon = self.equipped.get('weapon')
        if weapon is not None:
            w_low, w_high = weapon.get_scaled_base_range('attack_damage', self.get_item_proficiency_bonus(weapon))
            if weapon.subtype == 'Axe':
                bonus = self.strength * 0.95 + self.dexterity * 0.15
            elif weapon.subtype == 'Dagger':
                bonus = self.strength * 0.15 + self.dexterity * 0.95
            else:
                bonus = self.strength * 0.50 + self.dexterity * 0.50
            avg_base = max(1.0, (w_low + w_high) / 2.0)
            scale = 1.0 + (bonus / avg_base)
            scaled_low = max(0, int(round(w_low * scale)))
            scaled_high = max(scaled_low + 1, int(round(w_high * scale)))
            self.weapon_attack_min = self.base_attack_min + scaled_low
            self.weapon_attack_max = self.base_attack_max + scaled_high
        armor = self.equipped.get('armor')
        if armor is not None:
            a_low, a_high = armor.get_scaled_base_range('physical_armor')
            r_low, r_high = armor.get_scaled_base_range('magic_resistance')
            self.physical_armor += int(round((a_low + a_high) / 2))
            self.magic_resistance += int(round((r_low + r_high) / 2))
        charm = self.equipped.get('charm')
        if charm is not None:
            c_low, c_high = charm.get_scaled_base_range('attack_damage', self.get_item_proficiency_bonus(charm))
            spell_bonus = int(round(self.intelligence * 1.25))
            self.spell_attack_min = self.base_attack_min + max(0, int(round(c_low))) + spell_bonus
            self.spell_attack_max = self.base_attack_max + max(max(0, int(round(c_low))) + 1, int(round(c_high))) + spell_bonus
            self.cast_mana_cost = get_charm_mana_cost(charm.level)
        self.hp = max(1, min(self.max_hp, int(round(self.max_hp * hp_ratio)))) if self.hp > 0 else 0
        self.mana = max(0, min(self.max_mana, int(round(self.max_mana * mana_ratio))))
    def allocate_core_stat(self, key: str) -> str:
        if self.unspent_stat_points <= 0:
            return 'No unspent stat points.'
        if key not in {'strength', 'dexterity', 'intelligence', 'vitality'}:
            return 'Unknown stat.'
        self.unspent_stat_points -= 1
        setattr(self, f'base_{key}', getattr(self, f'base_{key}') + 1)
        self.recalculate_stats()
        return f'Allocated 1 point to {STAT_LABELS[key]}.'
    def to_dict(self) -> Dict:
        payload = asdict(self)
        normalized_inventory: List[Dict] = []
        for raw_item in self.inventory:
            item = coerce_item(raw_item)
            if item is not None:
                normalized_inventory.append(item.to_dict())
        payload['inventory'] = normalized_inventory
        normalized_equipped: Dict[str, Optional[Dict]] = {}
        for slot, raw_item in self.equipped.items():
            item = coerce_item(raw_item) if raw_item is not None else None
            normalized_equipped[slot] = item.to_dict() if item is not None else None
        payload['equipped'] = normalized_equipped
        return payload
    @classmethod
    def from_dict(cls, data: Dict) -> 'Player':
        payload = dict(data)
        payload['inventory'] = [Item.from_dict(item) for item in payload.get('inventory', [])]
        payload['equipped'] = {slot: Item.from_dict(item) if item else None for slot, item in payload.get('equipped', {}).items()}
        payload['proficiency_levels'] = dict(payload.get('proficiency_levels', empty_proficiency_levels()))
        payload['proficiency_progress'] = dict(payload.get('proficiency_progress', empty_proficiency_progress()))
        player = cls(**payload)
        player.recalculate_stats()
        player.hp = min(player.max_hp, player.hp)
        player.mana = min(player.max_mana, player.mana)
        return player
@dataclass
class CombatEvent:
    text: str
    tag: str = 'info'
@dataclass
class MarketplaceOffer:
    item: Item
    price: int
    sold: bool = False
CLASS_CONFIGS = {
    'Fighter': dict(max_hp=80, attack_min=2, attack_max=4, physical_armor=2, magic_resistance=1, speed=10, accuracy=0.86, crit_chance=0.08, crit_damage=1.50, armor_penetration=0, lifesteal=0.0, evasion=0.02, thorns=0.0, max_mana=10, mana_per_kill=0, life_per_kill=1, magic_find=0.0, damage_school='physical', core=dict(strength=12, dexterity=8, intelligence=4, vitality=6), gear=dict(weapon=('Training Axe', 'weapon', 'Axe'), armor=('Padded Medium Armor', 'armor', 'Medium'), charm=('Plain Fire Charm', 'charm', 'Fire'))),
    'Mage': dict(max_hp=74, attack_min=5, attack_max=8, physical_armor=1, magic_resistance=2, speed=11, accuracy=0.89, crit_chance=0.12, crit_damage=1.60, armor_penetration=0, lifesteal=0.0, evasion=0.03, thorns=0.0, max_mana=28, mana_per_kill=2, life_per_kill=0, magic_find=0.02, damage_school='magic', core=dict(strength=4, dexterity=6, intelligence=12, vitality=8), gear=dict(weapon=('Apprentice Staff', 'weapon', 'Staff'), armor=('Cloth Light Armor', 'armor', 'Light'), charm=('Faded Ice Charm', 'charm', 'Ice'))),
    'Samurai': dict(max_hp=76, attack_min=4, attack_max=6, physical_armor=2, magic_resistance=1, speed=13, accuracy=0.88, crit_chance=0.14, crit_damage=1.65, armor_penetration=1, lifesteal=0.0, evasion=0.04, thorns=0.0, max_mana=14, mana_per_kill=1, life_per_kill=1, magic_find=0.02, damage_school='physical', core=dict(strength=10, dexterity=12, intelligence=5, vitality=8), gear=dict(weapon=('Novice Dagger', 'weapon', 'Dagger'), armor=('Lamellar Medium Armor', 'armor', 'Medium'), charm=('War Lightning Charm', 'charm', 'Lightning'))),
    'Paladin': dict(max_hp=88, attack_min=4, attack_max=6, physical_armor=3, magic_resistance=3, speed=10, accuracy=0.87, crit_chance=0.10, crit_damage=1.55, armor_penetration=1, lifesteal=0.0, evasion=0.02, thorns=0.02, max_mana=18, mana_per_kill=1, life_per_kill=2, magic_find=0.02, damage_school='physical', core=dict(strength=14, dexterity=8, intelligence=7, vitality=11), gear=dict(weapon=('Initiate Axe', 'weapon', 'Axe'), armor=('Sanctified Heavy Armor', 'armor', 'Heavy'), charm=('Blessed Fire Charm', 'charm', 'Fire'))),
    'Monk': dict(max_hp=82, attack_min=5, attack_max=7, physical_armor=2, magic_resistance=3, speed=14, accuracy=0.90, crit_chance=0.12, crit_damage=1.60, armor_penetration=1, lifesteal=0.0, evasion=0.05, thorns=0.0, max_mana=20, mana_per_kill=1, life_per_kill=2, magic_find=0.02, damage_school='physical', core=dict(strength=10, dexterity=14, intelligence=8, vitality=13), gear=dict(weapon=('Pilgrim Staff', 'weapon', 'Staff'), armor=('Disciple Light Armor', 'armor', 'Light'), charm=('Meditation Ice Charm', 'charm', 'Ice'))),
    'Ninja': dict(max_hp=78, attack_min=6, attack_max=8, physical_armor=2, magic_resistance=2, speed=16, accuracy=0.92, crit_chance=0.16, crit_damage=1.70, armor_penetration=1, lifesteal=0.0, evasion=0.08, thorns=0.0, max_mana=18, mana_per_kill=1, life_per_kill=1, magic_find=0.03, damage_school='physical', core=dict(strength=11, dexterity=18, intelligence=7, vitality=14), gear=dict(weapon=('Shadow Dagger', 'weapon', 'Dagger'), armor=('Silent Light Armor', 'armor', 'Light'), charm=('Silent Lightning Charm', 'charm', 'Lightning'))),
    'Warlock': dict(max_hp=80, attack_min=7, attack_max=10, physical_armor=1, magic_resistance=4, speed=11, accuracy=0.90, crit_chance=0.15, crit_damage=1.75, armor_penetration=0, lifesteal=0.0, evasion=0.03, thorns=0.0, max_mana=36, mana_per_kill=3, life_per_kill=0, magic_find=0.03, damage_school='magic', core=dict(strength=8, dexterity=10, intelligence=22, vitality=15), gear=dict(weapon=('Hex Staff', 'weapon', 'Staff'), armor=('Shroud Light Armor', 'armor', 'Light'), charm=('Hex Fire Charm', 'charm', 'Fire'))),
    'Headhunter': dict(max_hp=86, attack_min=7, attack_max=10, physical_armor=3, magic_resistance=2, speed=15, accuracy=0.94, crit_chance=0.18, crit_damage=1.80, armor_penetration=2, lifesteal=0.0, evasion=0.06, thorns=0.0, max_mana=20, mana_per_kill=1, life_per_kill=2, magic_find=0.03, damage_school='physical', core=dict(strength=18, dexterity=20, intelligence=8, vitality=14), gear=dict(weapon=('Hunter Axe', 'weapon', 'Axe'), armor=('Tracker Medium Armor', 'armor', 'Medium'), charm=('Target Lightning Charm', 'charm', 'Lightning'))),
    'Alchemist': dict(max_hp=90, attack_min=8, attack_max=11, physical_armor=3, magic_resistance=4, speed=13, accuracy=0.93, crit_chance=0.16, crit_damage=1.75, armor_penetration=1, lifesteal=0.0, evasion=0.05, thorns=0.0, max_mana=34, mana_per_kill=3, life_per_kill=1, magic_find=0.05, damage_school='magic', core=dict(strength=14, dexterity=14, intelligence=20, vitality=17), gear=dict(weapon=('Catalyst Staff', 'weapon', 'Staff'), armor=('Experiment Light Armor', 'armor', 'Light'), charm=('Reactive Ice Charm', 'charm', 'Ice'))),
}
def build_item_base_stats(slot: str, subtype: str, bucket_level: int) -> Dict[str, float]:
    low, high = get_base_item_roll_range(bucket_level)
    if slot == 'weapon':
        return {'attack_damage_min': low, 'attack_damage_max': high}
    if slot == 'charm':
        return {'attack_damage_min': low, 'attack_damage_max': high}
    armor_scale = {'Light': 0.85, 'Medium': 1.00, 'Heavy': 1.15}.get(subtype, 1.0)
    resist_scale = {'Light': 1.15, 'Medium': 1.0, 'Heavy': 0.90}.get(subtype, 1.0)
    return {
        'physical_armor_min': int(round(low * armor_scale)),
        'physical_armor_max': int(round(high * armor_scale)),
        'magic_resistance_min': int(round(low * resist_scale * 0.45)),
        'magic_resistance_max': int(round(high * resist_scale * 0.45)),
    }
def starter_item(name: str, slot: str, subtype: str) -> Item:
    return Item(name=name, slot=slot, level=1, rarity='Common', subtype=subtype, base_stats=build_item_base_stats(slot, subtype, 1), affix_stats={}, is_starter=True)
def create_player(player_class: str) -> Player:
    cfg = copy.deepcopy(CLASS_CONFIGS[player_class])
    core = cfg.pop('core')
    gear = cfg.pop('gear')
    player = Player(
        name='Hero',
        level=1,
        hp=cfg['max_hp'],
        max_hp=cfg['max_hp'],
        attack_min=cfg['attack_min'],
        attack_max=cfg['attack_max'],
        physical_armor=cfg['physical_armor'],
        magic_resistance=cfg['magic_resistance'],
        speed=cfg['speed'],
        accuracy=cfg['accuracy'],
        crit_chance=cfg['crit_chance'],
        crit_damage=cfg['crit_damage'],
        armor_penetration=cfg['armor_penetration'],
        lifesteal=cfg['lifesteal'],
        evasion=cfg['evasion'],
        thorns=cfg['thorns'],
        max_mana=cfg['max_mana'],
        mana=cfg['max_mana'],
        mana_regen=0,
        life_regen=0,
        mana_per_kill=cfg['mana_per_kill'],
        life_per_kill=cfg['life_per_kill'],
        magic_find=cfg['magic_find'],
        damage_school=cfg['damage_school'],
        player_class=player_class,
        xp_to_next=xp_to_next_for_level(1),
    )
    player.base_strength = core['strength']
    player.base_dexterity = core['dexterity']
    player.base_intelligence = core['intelligence']
    player.base_vitality = core['vitality']
    player.base_attack_min = player.attack_min
    player.base_attack_max = player.attack_max
    player.base_max_hp = player.max_hp - (player.base_vitality * 5)
    player.base_physical_armor = player.physical_armor
    player.base_magic_resistance = player.magic_resistance
    player.base_speed = player.speed
    player.base_accuracy = player.accuracy
    player.base_crit_chance = player.crit_chance
    player.base_crit_damage = player.crit_damage
    player.base_armor_penetration = player.armor_penetration
    player.base_lifesteal = player.lifesteal
    player.base_evasion = player.evasion
    player.base_max_mana = player.max_mana
    player.base_mana_regen = 0
    player.base_life_regen = 0
    player.base_mana_per_kill = player.mana_per_kill
    player.base_life_per_kill = player.life_per_kill
    player.base_magic_find = player.magic_find
    player.base_xp_gain = 0.0
    player.base_thorns = player.thorns
    player.equipped = {
        'weapon': starter_item(*gear['weapon']),
        'armor': starter_item(*gear['armor']),
        'charm': starter_item(*gear['charm']),
    }
    player.recalculate_stats()
    player.hp = player.max_hp
    player.mana = player.max_mana
    return player
def build_monster_personal_name() -> str:
    return f"{random.choice(MONSTER_NAMES)} {random.choice(MONSTER_EPITHETS)}"
def build_monster_dialogue(species: str) -> str:
    options = MONSTER_DIALOGUE.get(species, ['The enemy watches you in silence.'])
    return random.choice(options)
def estimate_monster_power(max_hp: int, attack_min: int, attack_max: int, physical_armor: int, magic_resistance: int, speed: int, accuracy: float, crit_chance: float, crit_damage: float, evasion: float) -> float:
    avg_attack = max(1.0, (attack_min + attack_max) / 2.0)
    offense = avg_attack * max(0.60, accuracy) * (1.0 + max(0.0, crit_chance) * max(0.0, crit_damage - 1.0)) * (1.0 + max(-0.08, (speed - 10) * 0.012))
    durability = max(1.0, max_hp) * (1.0 + max(0.0, physical_armor + magic_resistance) * 0.028 + max(0.0, evasion) * 2.0)
    return offense * (durability ** 0.5)
def generate_monster(player_level: int, difficulty_multiplier: float = 1.0, encounter_name: Optional[str] = None, forced_level: Optional[int] = None) -> Tuple[Fighter, int]:
    archetype = random.choice(MONSTER_ARCHETYPES)
    damage_school = archetype['school']
    level = max(1, min(60, forced_level if forced_level is not None else (player_level + random.choice([-1, 0, 0, 1]))))
    max_hp = random.randint(28, 40) + (level - 1) * random.randint(8, 11)
    attack_min = 4 + (level - 1) * 2
    attack_max = 8 + (level - 1) * 3
    physical_armor = 1 + (level - 1)
    magic_resistance = 1 + max(0, (level - 1) // 2)
    speed = 8 + level + (2 if difficulty_multiplier > 1.0 else 0)
    accuracy = 0.80 + min(0.12, level * 0.01) + (0.02 if difficulty_multiplier > 1.0 else 0.0)
    crit_chance = 0.05 + min(0.10, level * 0.01) + (0.02 if difficulty_multiplier > 1.0 else 0.0)
    crit_damage = 1.50 + (0.15 if difficulty_multiplier > 1.0 else 0.0)
    evasion = 0.0
    if damage_school == 'magic':
        attack_min += 1
        attack_max += 2
        magic_resistance += 1
    if difficulty_multiplier != 1.0:
        max_hp = int(round(max_hp * difficulty_multiplier))
        attack_min = max(1, int(round(attack_min * difficulty_multiplier)))
        attack_max = max(attack_min + 1, int(round(attack_max * difficulty_multiplier)))
        armor_scale = 1.0 + (difficulty_multiplier - 1.0) * 0.75
        physical_armor = max(1, int(round(physical_armor * armor_scale)))
        magic_resistance = max(1, int(round(magic_resistance * armor_scale)))
    base_power = estimate_monster_power(max_hp, attack_min, attack_max, physical_armor, magic_resistance, speed, accuracy, crit_chance, crit_damage, evasion)
    avg_attack = (attack_min + attack_max) / 2.0
    attack_span = max(2.0, float(attack_max - attack_min))
    avg_attack *= float(archetype.get('damage_mult', 1.0))
    attack_span *= float(archetype.get('variance_mult', 1.0))
    max_hp = max(10, int(round(max_hp * float(archetype.get('hp_mult', 1.0)))))
    physical_armor = max(0, int(round(physical_armor * float(archetype.get('phys_mult', 1.0)))))
    magic_resistance = max(0, int(round(magic_resistance * float(archetype.get('mres_mult', 1.0)))))
    speed = max(4, speed + int(archetype.get('speed_bonus', 0)))
    accuracy = max(0.65, min(0.98, accuracy + float(archetype.get('accuracy_bonus', 0.0))))
    crit_chance = max(0.02, min(0.30, crit_chance + float(archetype.get('crit_bonus', 0.0))))
    evasion = max(0.0, min(0.18, evasion + float(archetype.get('evasion_bonus', 0.0))))
    attack_min = max(1, int(round(avg_attack - attack_span / 2.0)))
    attack_max = max(attack_min + 1, int(round(avg_attack + attack_span / 2.0)))
    modified_power = estimate_monster_power(max_hp, attack_min, attack_max, physical_armor, magic_resistance, speed, accuracy, crit_chance, crit_damage, evasion)
    for _ in range(4):
        if modified_power <= 0:
            break
        balance_scale = base_power / modified_power
        if 0.995 <= balance_scale <= 1.005:
            break
        hp_scale = max(0.55, min(1.85, balance_scale ** 0.42))
        atk_scale = max(0.55, min(1.85, balance_scale ** 0.58))
        max_hp = max(10, int(round(max_hp * hp_scale)))
        avg_attack = max(1.0, ((attack_min + attack_max) / 2.0) * atk_scale)
        attack_min = max(1, int(round(avg_attack - attack_span / 2.0)))
        attack_max = max(attack_min + 1, int(round(avg_attack + attack_span / 2.0)))
        modified_power = estimate_monster_power(max_hp, attack_min, attack_max, physical_armor, magic_resistance, speed, accuracy, crit_chance, crit_damage, evasion)
    max_hp = max(10, int(round(max_hp * monster_bonus_health_scale(level))))
    species = encounter_name or archetype['type']
    personal_name = build_monster_personal_name()
    monster = Fighter(
        name=personal_name,
        level=level,
        max_hp=max_hp,
        hp=max_hp,
        attack_min=attack_min,
        attack_max=attack_max,
        physical_armor=physical_armor,
        magic_resistance=magic_resistance,
        speed=speed,
        accuracy=accuracy,
        crit_chance=crit_chance,
        crit_damage=crit_damage,
        armor_penetration=max(0, level // 15) + (1 if difficulty_multiplier > 1.0 else 0),
        lifesteal=0.0,
        evasion=evasion,
        thorns=0.0,
        damage_school=damage_school,
        monster_type=f'{species} Lv {level}',
        monster_personal_name=personal_name,
        monster_kit=archetype['kit'],
        monster_profile=archetype['profile'],
        monster_dialogue=build_monster_dialogue(archetype['type']),
    )
    xp_reward = int(round(base_monster_xp(level) * random.uniform(0.92, 1.08) * (1.18 if difficulty_multiplier > 1.0 else 1.0)))
    return monster, xp_reward

def roll_value_for_stat(stat_key: str, item_level: int) -> float:
    if stat_key == 'enhanced_effect':
        return round(random.uniform(0.0, get_enhanced_effect_cap(item_level)), 2)
    if stat_key in CORE_STAT_KEYS:
        return random.randint(0, get_core_stat_cap(item_level))
    low, high = get_secondary_affix_roll_bounds(stat_key, item_level)
    if stat_key in {'armor_penetration', 'max_health', 'life_regen', 'life_per_kill', 'max_mana', 'mana_regen', 'mana_per_kill'}:
        return random.randint(int(round(low)), int(round(high)))
    return round(random.uniform(low, high), 3)
def choose_rarity_with_magic_find(magic_find: float) -> str:
    weights: List[float] = []
    boost_factor = magic_find * 0.75
    for rarity in RARITY_ORDER:
        base_weight = RARITY_BASE_WEIGHTS[rarity]
        idx = RARITY_ORDER.index(rarity)
        if rarity == 'Common':
            weight = max(0.05, base_weight / (1.0 + boost_factor))
        else:
            weight = base_weight * (1.0 + (boost_factor * (1.0 + idx * 0.18)))
        weights.append(weight)
    return random.choices(RARITY_ORDER, weights=weights, k=1)[0]
def build_item_name(rarity: str, slot: str, subtype: str) -> str:
    suffix = {'weapon': 'Weapon', 'armor': 'Armor', 'charm': 'Charm'}[slot]
    return f'{rarity} {subtype} {suffix}'
def generate_item_drop(monster_level: int, player_class: str, magic_find: float) -> Item:
    available_buckets = get_available_drop_buckets(monster_level)
    item_level = random.choice(available_buckets or [1])
    rarity = choose_rarity_with_magic_find(magic_find)
    slot = random.choice(['weapon', 'armor', 'charm'])
    subtype = random.choice(ITEM_SUBTYPES[slot])
    base_stats = build_item_base_stats(slot, subtype, item_level)
    affix_pool = ['enhanced_effect'] + CORE_STAT_KEYS + SECONDARY_AFFIX_KEYS
    affix_count = RARITY_STAT_COUNT[rarity]
    chosen = random.sample(affix_pool, affix_count) if affix_count else []
    affix_stats = {key: roll_value_for_stat(key, item_level) for key in chosen}
    return Item(
        name=build_item_name(rarity, slot, subtype),
        slot=slot,
        level=item_level,
        rarity=rarity,
        subtype=subtype,
        base_stats=base_stats,
        affix_stats=affix_stats,
    )
def get_available_drop_buckets(level: int) -> List[int]:
    max_bucket = bucket_item_level(level)
    return [bucket for bucket in ITEM_BUCKETS if bucket <= max_bucket]

def monster_bonus_health_scale(level: int) -> float:
    if level <= 1:
        return 1.5
    return 1.5 + (((clamp(level, 1, 60) - 1) / 59.0) * 1.5)

def marketplace_refresh_breakpoint(level: int) -> int:
    if level >= 60:
        return 60
    if level >= 50:
        return 50
    if level >= 40:
        return 40
    if level >= 30:
        return 30
    if level >= 20:
        return 20
    if level >= 10:
        return 10
    return 1
def generate_specific_item(item_level: int, slot: str, subtype: str, rarity: str) -> Item:
    item_level = bucket_item_level(item_level)
    base_stats = build_item_base_stats(slot, subtype, item_level)
    affix_pool = ['enhanced_effect'] + CORE_STAT_KEYS + SECONDARY_AFFIX_KEYS
    affix_count = min(RARITY_STAT_COUNT.get(rarity, 0), len(affix_pool))
    chosen = random.sample(affix_pool, affix_count) if affix_count else []
    affix_stats = {key: roll_value_for_stat(key, item_level) for key in chosen}
    return Item(
        name=build_item_name(rarity, slot, subtype),
        slot=slot,
        level=item_level,
        rarity=rarity,
        subtype=subtype,
        base_stats=base_stats,
        affix_stats=affix_stats,
    )
def shift_rarity(rarity: str, delta: int) -> str:
    try:
        index = RARITY_ORDER.index(rarity) + delta
    except ValueError:
        index = 0
    index = max(0, min(len(RARITY_ORDER) - 1, index))
    return RARITY_ORDER[index]
def determine_transmute_rarity(first: Item, second: Item) -> str:
    try:
        first_index = RARITY_ORDER.index(first.rarity)
        second_index = RARITY_ORDER.index(second.rarity)
    except ValueError:
        return first.rarity
    low_index = min(first_index, second_index)
    high_index = max(first_index, second_index)
    upgrade_rarity = RARITY_ORDER[min(len(RARITY_ORDER) - 1, low_index + 1)]
    same_rarity = RARITY_ORDER[high_index]
    downgrade_rarity = RARITY_ORDER[max(0, high_index - 1)]
    roll = random.random()
    if roll < 0.35:
        return upgrade_rarity
    if roll < 0.85:
        return same_rarity
    return downgrade_rarity
def choose_weighted_rarity(options: List[str]) -> str:
    weights = [max(0.0, RARITY_BASE_WEIGHTS.get(rarity, 0.0)) for rarity in options]
    if sum(weights) <= 0:
        weights = [1.0 for _ in options]
    return random.choices(options, weights=weights, k=1)[0]
def lerp_int(start: int, end: int, factor: float) -> int:
    return int(round(start + ((end - start) * clamp(factor, 0.0, 1.0))))
def price_from_level(level: int, low: int, high: int) -> int:
    level_factor = (clamp(level, 1, 45) - 1) / 44.0
    return lerp_int(low, high, level_factor)
MARKETPLACE_STALL_TITLES = ['Cheap Utility', 'Premium Rare Goods', 'Special Stall']
MARKETPLACE_STALL_DESCRIPTIONS = [
    'A clean Fine piece with a simple Enhanced Effect roll. Cheap, tidy, and useful.',
    'An aspirational rare-goods slot tied to your unlocked progression buckets.',
    'A strange jackpot curio that can ignore normal progression expectations.',
]
def marketplace_stall_title(slot_index: int) -> str:
    return MARKETPLACE_STALL_TITLES[max(0, min(slot_index, len(MARKETPLACE_STALL_TITLES) - 1))]
def marketplace_stall_description(slot_index: int) -> str:
    return MARKETPLACE_STALL_DESCRIPTIONS[max(0, min(slot_index, len(MARKETPLACE_STALL_DESCRIPTIONS) - 1))]
def generate_marketplace_offer(slot_index: int, player_level: int) -> MarketplaceOffer:
    available_buckets = get_available_drop_buckets(player_level)
    if not available_buckets:
        available_buckets = [1]
    if slot_index == 0:
        item_level = random.choice(available_buckets)
        slot = random.choice(['weapon', 'armor', 'charm'])
        subtype = random.choice(ITEM_SUBTYPES[slot])
        item = generate_specific_item(item_level, slot, subtype, 'Fine')
        enhanced_cap = get_enhanced_effect_cap(item_level)
        item.affix_stats = {'enhanced_effect': round(max(0.01, random.uniform(0.01, max(0.01, enhanced_cap * 0.20))), 2)}
        price = price_from_level(item_level, 100, 250)
        return MarketplaceOffer(item=item, price=price)
    if slot_index == 1:
        item_level = random.choice(available_buckets)
        rarity = choose_weighted_rarity(['Mythic', 'Ancient', 'Relic', 'Ascendant', 'Legendary'])
        slot = random.choice(['weapon', 'armor', 'charm'])
        subtype = random.choice(ITEM_SUBTYPES[slot])
        item = generate_specific_item(item_level, slot, subtype, rarity)
        rarity_factor = ['Mythic', 'Ancient', 'Relic', 'Ascendant', 'Legendary'].index(rarity) / 4.0
        combined_factor = clamp((((item_level - 1) / 44.0) * 0.55) + (rarity_factor * 0.45), 0.0, 1.0)
        price = lerp_int(1000, 9999, combined_factor)
        return MarketplaceOffer(item=item, price=price)
    item_level = random.randint(1, 45)
    slot = random.choice(['weapon', 'armor', 'charm'])
    subtype = random.choice(ITEM_SUBTYPES[slot])
    item = generate_specific_item(item_level, slot, subtype, 'Unspawnable')
    affix_pool = ['enhanced_effect'] + CORE_STAT_KEYS + SECONDARY_AFFIX_KEYS
    affix_count = random.randint(1, 4)
    chosen_keys = random.sample(affix_pool, k=affix_count)
    item.affix_stats = {key: roll_value_for_stat(key, 45) for key in chosen_keys}
    item.name = f'Unspawnable {subtype} {item.slot.title()}'
    level_factor = clamp((item_level - 1) / 44.0, 0.0, 1.0)
    affix_factor = (affix_count - 1) / 3.0
    price = lerp_int(10000, 35000, clamp((affix_factor * 0.70) + (level_factor * 0.30), 0.0, 1.0))
    return MarketplaceOffer(item=item, price=price)
def hit_success(attacker: Fighter, defender: Fighter) -> bool:
    if isinstance(attacker, Player):
        chance = clamp(attacker.accuracy, 0.08, 0.95)
        return random.random() <= chance
    speed_delta = attacker.speed - defender.speed
    chance = attacker.accuracy + (speed_delta * 0.01) - defender.evasion
    return random.random() <= clamp(chance, 0.08, 0.95)

def get_attack_context(attacker: Fighter) -> Tuple[int, int, str, bool, Optional[str]]:
    proficiency_key: Optional[str] = None
    if isinstance(attacker, Player):
        is_caster = attacker.player_class in CASTER_CLASSES
        can_cast = is_caster and attacker.spell_attack_max > 0 and attacker.mana >= attacker.cast_mana_cost > 0
        if can_cast:
            charm = attacker.equipped.get('charm')
            if charm is not None:
                proficiency_key = get_proficiency_key(charm.slot, charm.subtype)
            return attacker.spell_attack_min, attacker.spell_attack_max, 'magic', True, proficiency_key
        weapon = attacker.equipped.get('weapon')
        if weapon is not None:
            proficiency_key = get_proficiency_key(weapon.slot, weapon.subtype)
        return attacker.weapon_attack_min, attacker.weapon_attack_max, 'physical', False, proficiency_key
    return attacker.attack_min, attacker.attack_max, attacker.damage_school, False, None

def apply_damage(attacker: Fighter, defender: Fighter, low: int, high: int, school: str) -> Tuple[int, bool, int, int]:
    raw = random.randint(low, high)
    crit = random.random() <= attacker.crit_chance
    if crit:
        raw = int(round(raw * attacker.crit_damage))
    if school == 'magic':
        mitigation = random.randint(0, max(0, int(round(defender.magic_resistance))))
    else:
        armor_roll = random.randint(0, max(0, int(round(defender.physical_armor))))
        mitigation = max(0, armor_roll - attacker.armor_penetration)
    damage = max(1, raw - int(round(mitigation)))
    defender.hp = max(0, defender.hp - damage)
    reflected = 0
    if damage > 0 and defender.thorns > 0 and attacker.is_alive():
        reflected = max(1, int(round(damage * defender.thorns)))
        attacker.hp = max(0, attacker.hp - reflected)
    healed = 0
    if damage > 0 and attacker.lifesteal > 0 and attacker.is_alive():
        healed = int(round(damage * attacker.lifesteal))
        if healed > 0:
            attacker.hp = min(attacker.max_hp, attacker.hp + healed)
    return damage, crit, healed, reflected

def apply_regeneration(fighter: Fighter) -> Tuple[int, int]:
    hp_gain = 0
    if fighter.life_regen > 0 and fighter.hp > 0:
        hp_gain = min(fighter.life_regen, fighter.max_hp - fighter.hp)
        fighter.hp += hp_gain
    return hp_gain, 0
def resolve_turn(attacker: Fighter, defender: Fighter) -> CombatEvent:
    low, high, school, used_spell, proficiency_key = get_attack_context(attacker)
    if used_spell and isinstance(attacker, Player):
        attacker.mana = max(0, attacker.mana - attacker.cast_mana_cost)
    if not hit_success(attacker, defender):
        action = 'casts and misses' if used_spell else 'misses'
        return CombatEvent(f'{attacker.name} {action} {defender.name}.', 'warning')
    damage, crit, healed, reflected = apply_damage(attacker, defender, low, high, school)
    school_text = 'magic' if school == 'magic' else 'physical'
    verb = 'casts into' if used_spell else 'hits'
    text = f'{attacker.name} {verb} {defender.name} for {damage} {school_text} damage'
    if crit:
        text += ' (CRIT)'
    text += '.'
    if healed > 0:
        text += f' {attacker.name} steals {healed} life.'
    if reflected > 0:
        text += f' {defender.name} reflects {reflected} damage.'
    if isinstance(attacker, Player):
        old_level, new_level = attacker.grant_proficiency_point(proficiency_key, 1)
        if proficiency_key and new_level > old_level:
            text += f' {proficiency_key} proficiency reaches {new_level} (+{new_level}% enhanced effect).'
    return CombatEvent(text, 'danger' if crit else 'info')
def gain_xp(player: Player, amount: int) -> List[str]:
    messages: List[str] = []
    if amount <= 0:
        messages.append('You gain no XP from this fight.')
        return messages
    player.xp += amount
    hp_gain_by_class = {'Fighter': 8, 'Mage': 5, 'Samurai': 7, 'Paladin': 9, 'Monk': 7, 'Ninja': 6, 'Warlock': 6, 'Headhunter': 7, 'Alchemist': 8}
    mana_gain_by_class = {'Fighter': 0, 'Mage': 2, 'Samurai': 1, 'Paladin': 1, 'Monk': 1, 'Ninja': 1, 'Warlock': 3, 'Headhunter': 1, 'Alchemist': 2}
    while player.level < 60 and player.xp >= player.xp_to_next:
        player.xp -= player.xp_to_next
        player.level += 1
        player.unspent_stat_points += 1
        hp_gain = hp_gain_by_class.get(player.player_class, 7) + (player.base_vitality * 5)
        mana_gain = mana_gain_by_class.get(player.player_class, 1) + (player.base_intelligence * 5)
        player.base_max_hp += hp_gain
        player.base_attack_min += 1 + max(0, player.base_strength // 10)
        player.base_attack_max += 2 + max(0, player.base_strength // 8)
        player.base_physical_armor += 1
        player.base_magic_resistance += 1
        player.base_max_mana += mana_gain
        player.base_accuracy = min(0.97, player.base_accuracy + 0.002)
        player.base_crit_chance = min(0.35, player.base_crit_chance + 0.003)
        player.xp_to_next = xp_to_next_for_level(player.level)
        player.recalculate_stats()
        player.hp = player.max_hp
        player.mana = player.max_mana
        message = f'Level up! You reached level {player.level} and gained 1 stat point, +{hp_gain} HP'
        if mana_gain > 0:
            message += f', +{mana_gain} Mana'
        message += '.'
        messages.append(message)
    return messages

def build_combat_events(player: Player, monster: Fighter) -> List[CombatEvent]:
    events: List[CombatEvent] = []
    round_no = 1
    while player.is_alive() and monster.is_alive() and round_no <= 100:
        events.append(CombatEvent(f'-- Round {round_no} --', 'round'))
        player_goes_first = player.speed > monster.speed or (player.speed == monster.speed and random.random() < 0.5)
        if player_goes_first:
            events.append(resolve_turn(player, monster))
            if monster.is_alive():
                events.append(resolve_turn(monster, player))
        else:
            events.append(resolve_turn(monster, player))
            if player.is_alive():
                events.append(resolve_turn(player, monster))
        if player.is_alive() and (player.life_regen > 0 or player.mana_regen > 0):
            hp_gained, mana_gained = apply_regeneration(player)
            if hp_gained or mana_gained:
                parts = []
                if hp_gained:
                    parts.append(f'{hp_gained} life')
                if mana_gained:
                    parts.append(f'{mana_gained} mana')
                events.append(CombatEvent(f'{player.name} regenerates {' and '.join(parts)}.', 'success'))
        round_no += 1
    if player.is_alive() and not monster.is_alive():
        player.wins += 1
        events.append(CombatEvent(f'You defeated {monster.monster_personal_name} ({monster.monster_type})!', 'success'))
    elif monster.is_alive() and not player.is_alive():
        player.losses += 1
        events.append(CombatEvent(f'You were slain by {monster.monster_personal_name} ({monster.monster_type})...', 'danger'))
    else:
        player.losses += 1
        events.append(CombatEvent('The fight timed out in a draw. Counted as a loss.', 'warning'))
    return events
def build_combat_timeline(player: Player, monster: Fighter) -> List[Tuple[CombatEvent, int, int, int, int, int]]:
    timeline: List[Tuple[CombatEvent, int, int, int, int, int]] = []
    round_no = 1
    while player.is_alive() and monster.is_alive() and round_no <= 100:
        round_event = CombatEvent(f'-- Round {round_no} --', 'round')
        timeline.append((round_event, player.hp, player.mana, monster.hp, player.wins, player.losses))
        player_goes_first = player.speed > monster.speed or (player.speed == monster.speed and random.random() < 0.5)
        if player_goes_first:
            event = resolve_turn(player, monster)
            timeline.append((event, player.hp, player.mana, monster.hp, player.wins, player.losses))
            if monster.is_alive():
                event = resolve_turn(monster, player)
                timeline.append((event, player.hp, player.mana, monster.hp, player.wins, player.losses))
        else:
            event = resolve_turn(monster, player)
            timeline.append((event, player.hp, player.mana, monster.hp, player.wins, player.losses))
            if player.is_alive():
                event = resolve_turn(player, monster)
                timeline.append((event, player.hp, player.mana, monster.hp, player.wins, player.losses))
        if player.is_alive() and (player.life_regen > 0 or player.mana_regen > 0):
            hp_gained, mana_gained = apply_regeneration(player)
            if hp_gained or mana_gained:
                parts = []
                if hp_gained:
                    parts.append(f'{hp_gained} life')
                if mana_gained:
                    parts.append(f'{mana_gained} mana')
                event = CombatEvent(f'{player.name} regenerates {' and '.join(parts)}.', 'success')
                timeline.append((event, player.hp, player.mana, monster.hp, player.wins, player.losses))
        round_no += 1
    if player.is_alive() and not monster.is_alive():
        player.wins += 1
        event = CombatEvent(f'You defeated {monster.monster_personal_name} ({monster.monster_type})!', 'success')
    elif monster.is_alive() and not player.is_alive():
        player.losses += 1
        event = CombatEvent(f'You were slain by {monster.monster_personal_name} ({monster.monster_type})...', 'danger')
    else:
        player.losses += 1
        event = CombatEvent('The fight timed out in a draw. Counted as a loss.', 'warning')
    timeline.append((event, player.hp, player.mana, monster.hp, player.wins, player.losses))
    return timeline

def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return '—'
    total = max(0, int(round(float(seconds))))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def build_default_ladder_stats() -> Dict[str, Dict[str, Optional[float]]]:
    return {
        class_name: {
            'masterquest_attempts': 0,
            'fastest_masterquest_seconds': None,
            'enemy_kills': 0,
            'total_deaths': 0,
            'wellspawns_killed': 0,
        }
        for class_name in CLASS_ORDER
    }

def normalize_ladder_stats(data: Optional[Dict[str, Dict[str, Optional[float]]]]) -> Dict[str, Dict[str, Optional[float]]]:
    normalized = build_default_ladder_stats()
    if isinstance(data, dict):
        for class_name, stats in data.items():
            if class_name not in normalized or not isinstance(stats, dict):
                continue
            normalized[class_name]['masterquest_attempts'] = int(stats.get('masterquest_attempts', 0) or 0)
            normalized[class_name]['enemy_kills'] = int(stats.get('enemy_kills', 0) or 0)
            normalized[class_name]['total_deaths'] = int(stats.get('total_deaths', 0) or 0)
            normalized[class_name]['wellspawns_killed'] = int(stats.get('wellspawns_killed', 0) or 0)
            fastest = stats.get('fastest_masterquest_seconds')
            normalized[class_name]['fastest_masterquest_seconds'] = None if fastest in (None, '') else float(fastest)
    return normalized

def build_glossary_text() -> str:
    lines: List[str] = []
    lines.append('MASTERQUEST GLOSSARY')
    lines.append('=' * 96)
    lines.append('')
    lines.append('Equipment Types')
    lines.append('-' * 96)
    lines.append('Weapons: Dagger, Axe, Staff')
    lines.append('Armor:   Light Armor, Medium Armor, Heavy Armor')
    lines.append('Charms:  Fire Charm, Lightning Charm, Ice Charm')
    lines.append('')
    lines.append('Rarity -> number of random affix modifiers')
    lines.append('-' * 96)
    for rarity in RARITY_ORDER:
        lines.append(f"{rarity:<10} {RARITY_STAT_COUNT[rarity]} modifier(s)")
    lines.append('')
    lines.append('Approximate base rarity chances')
    lines.append('-' * 96)
    for rarity in reversed(RARITY_ORDER):
        chance = RARITY_BASE_WEIGHTS[rarity]
        if chance <= 0:
            continue
        if rarity == 'Common':
            lines.append(f"{rarity:<10} ~{int(round(chance * 100))}% of item drops")
        else:
            lines.append(f"{rarity:<10} ~1 in {int(round(1.0 / chance))} item drops")
    lines.append('')
    lines.append('Drop Tier Breakpoints')
    lines.append('-' * 96)
    lines.append('Any eligible drop tier is rolled with equal weight.')
    for index, bucket in enumerate(ITEM_BUCKETS):
        if index == 0:
            level_label = ' 1-4 '
        elif index < len(ITEM_BUCKETS) - 1:
            level_label = f"{bucket:>2}-{ITEM_BUCKETS[index + 1] - 1:<2}"
        else:
            level_label = f"{bucket:>2}+"
        eligible = ', '.join(f"T{value}" for value in get_available_drop_buckets(bucket))
        lines.append(f"Monster Lv {level_label} -> {eligible}")
    lines.append('')
    lines.append('Base Weapon Damage by Tier')
    lines.append('-' * 96)
    lines.append('Tier  Dagger        Axe           Staff')
    for bucket in ITEM_BUCKETS:
        dagger = build_item_base_stats('weapon', 'Dagger', bucket)
        axe = build_item_base_stats('weapon', 'Axe', bucket)
        staff = build_item_base_stats('weapon', 'Staff', bucket)
        lines.append(
            f"{bucket:>4}  {int(dagger['attack_damage_min']):>3}-{int(dagger['attack_damage_max']):<3}      "
            f"{int(axe['attack_damage_min']):>3}-{int(axe['attack_damage_max']):<3}      "
            f"{int(staff['attack_damage_min']):>3}-{int(staff['attack_damage_max']):<3}"
        )
    lines.append('')
    lines.append('Base Charm Damage and Mana Cost by Tier')
    lines.append('-' * 96)
    lines.append('Tier  Ice           Lightning     Fire          Mana Cost')
    for bucket in ITEM_BUCKETS:
        ice = build_item_base_stats('charm', 'Ice', bucket)
        light = build_item_base_stats('charm', 'Lightning', bucket)
        fire = build_item_base_stats('charm', 'Fire', bucket)
        mana_cost = get_charm_mana_cost(bucket)
        lines.append(
            f"{bucket:>4}  {int(ice['attack_damage_min']):>3}-{int(ice['attack_damage_max']):<3}      "
            f"{int(light['attack_damage_min']):>3}-{int(light['attack_damage_max']):<3}      "
            f"{int(fire['attack_damage_min']):>3}-{int(fire['attack_damage_max']):<3}      {mana_cost:>3}"
        )
    lines.append('')
    lines.append('Base Armor Values by Tier')
    lines.append('-' * 96)
    lines.append('Tier  Light Armor          Medium Armor         Heavy Armor')
    lines.append('      P.Arm   M.Res        P.Arm   M.Res        P.Arm   M.Res')
    for bucket in ITEM_BUCKETS:
        light = build_item_base_stats('armor', 'Light', bucket)
        medium = build_item_base_stats('armor', 'Medium', bucket)
        heavy = build_item_base_stats('armor', 'Heavy', bucket)
        lines.append(
            f"{bucket:>4}  {int(light['physical_armor_min']):>3}-{int(light['physical_armor_max']):<3}  {int(light['magic_resistance_min']):>3}-{int(light['magic_resistance_max']):<3}    "
            f"{int(medium['physical_armor_min']):>3}-{int(medium['physical_armor_max']):<3}  {int(medium['magic_resistance_min']):>3}-{int(medium['magic_resistance_max']):<3}    "
            f"{int(heavy['physical_armor_min']):>3}-{int(heavy['physical_armor_max']):<3}  {int(heavy['magic_resistance_min']):>3}-{int(heavy['magic_resistance_max']):<3}"
        )
    lines.append('')
    lines.append('Affix Maximum Values by Tier')
    lines.append('-' * 96)
    lines.append('Enhanced Effect and core attributes')
    for bucket in ITEM_BUCKETS:
        ee_max = format_stat_value('enhanced_effect', get_enhanced_effect_cap(bucket))
        core_max = format_stat_value('strength', get_core_stat_cap(bucket))
        lines.append(f"Tier {bucket:<2}  {ee_max:<28}  {core_max} to each core stat")
    lines.append('')
    lines.append('Secondary affix maximums')
    stat_keys = [
        'crit_chance', 'crit_damage', 'armor_penetration', 'lifesteal', 'max_health', 'life_regen',
        'life_per_kill', 'evasion', 'max_mana', 'mana_regen', 'mana_per_kill', 'magic_find',
        'xp_gain', 'thorns', 'accuracy',
    ]
    for bucket in ITEM_BUCKETS:
        lines.append(f"Tier {bucket}")
        for key in stat_keys:
            _low, high = get_secondary_affix_roll_bounds(key, bucket)
            lines.append(f"  - {STAT_LABELS[key]:<22} {format_stat_value(key, high)}")
        lines.append('')
    lines.append('Notes')
    lines.append('-' * 96)
    lines.append('• Common items have only base item stats and no random affixes.')
    lines.append("• Items can only be equipped once your hero reaches that tier's matching level.")
    lines.append('• Weapons, armor, and charms all scale by subtype and tier.')
    lines.append('• Wellspawn fights cost 10 gold, are stronger than arena fights, and always drop loot.')
    lines.append('• The Inn Vault stores up to 20 items. Storage costs 5 gold and withdrawals are free.')
    return '\n'.join(lines)

class SessionState:
    def __init__(self) -> None:
        self.player: Optional[Player] = None
        self.current_monster: Optional[Fighter] = None
        self.current_monster_xp: int = 0
        self.log: List[CombatEvent] = [CombatEvent('Welcome to MasterQuest. Choose a chronicle slot to begin.', 'info')]
        self.export_code: str = ''
        self.import_code: str = ''
        self.screen: str = 'title'
        self.active_slot_index: Optional[int] = None
        self.selection_return_class: Optional[str] = None
        self.pending_character_name: str = 'Hero'
        self.shared_gold: int = 0
        self.shared_inventory: List[Item] = []
        self.vault_items: List[Item] = []
        self.masterquest_pity_bonus: int = 0
        self.test_mode: bool = False
        self.game_tab: str = 'arena'
        self.fight_in_progress: bool = False
        self.log_delay_ms: int = 1000
        self.monster_chain_combo: int = 0
        self.mana_regen_progress: float = 0.0
        self.arena_transition_text: str = 'Choose when to call the next challenger.'
        self.arena_transition_tone: str = 'muted'
        self.arena_same_level: bool = True
        self.arena_selected_level: int = 1
        self.last_monster_snapshot: Optional[Fighter] = None
        self.last_fight_outcome: str = 'idle'
        self.current_arena_monster_uri: str = ''
        self.current_arena_monster_species: str = ''
        self.last_arena_monster_uri: str = ''
        self.last_arena_monster_species: str = ''
        self.monster_page_turn_active: bool = False
        self.monster_page_turn_progress: float = 0.0
        self.page_turn_previous_monster: Optional[Fighter] = None
        self.inventory_view: str = 'Inventory'
        self.tier_filter: str = 'All tiers'
        self.type_filter: str = 'All types'
        self.attribute_filter: str = 'All attributes'
        self.inventory_sort: str = 'Level (High-Low)'
        self.inventory_search: str = ''
        self.selected_inventory_source: str = 'inventory'
        self.selected_inventory_key: str = ''
        self.hovered_inventory_key: str = ''
        self.inventory_return_screen: str = 'game'
        self.inventory_return_tab: str = 'arena'
        self.marketplace_offers: List[MarketplaceOffer] = []
        self.marketplace_offer_refresh_level: int = 0
        self.current_marketplace_line: str = ''
        self.marketplace_selected_index: int = 0
        self.marketplace_hovered_index: int = -1
        self.marketplace_pending_purchase_index: int = -1
        self.current_transmute_line: str = ''
        self.transmute_message: str = ''
        self.transmute_choice_one: str = ''
        self.transmute_choice_two: str = ''
        self.current_well_scene_line: str = ''
        self.current_inn_line: str = ''
        self.inn_vault_inventory_selected_index: int = -1
        self.inn_vault_selected_index: int = -1
        self.current_ladder_line: str = ''
        self.current_run_started_at: float = 0.0
        self.ladder_stats: Dict[str, Dict[str, Optional[float]]] = build_default_ladder_stats()
        self.well_monster_cycle_index: int = 0
        self.current_well_monster_asset_index: int = 0
        self.current_encounter_type: str = 'normal'
        self.last_encounter_type: str = 'normal'
        self.class_compendium_open: bool = False
        self.saved_item_sets: Dict[str, Dict[int, Item]] = empty_saved_item_sets()
        self.unlocked_classes: set[str] = {'Fighter', 'Mage'}
        self.class_select_notice: str = ''
        self.slots: List[Dict[str, object]] = load_persisted_slots()
    def slot_summary(self, index: int) -> str:
        slot = self.slots[index]
        player_data = slot.get('player')
        if not player_data:
            return 'No chronicle is etched here yet. Open this slot to create a new hero and begin the climb.'
        try:
            player = Player.from_dict(copy.deepcopy(player_data))
            return (
                f'{player.player_class} • Level {player.level}\n'
                f'HP {player.hp}/{player.max_hp} • Gold {player.gold} • XP {player.xp}/{player.xp_to_next}\n'
                f'Wins {player.wins} • Losses {player.losses} • Inventory {len(player.inventory)} items • Vault {len(slot.get('vault_items', []))}'
            )
        except Exception:
            return 'The chronicle is damaged. Opening this slot will begin a fresh hero.'
    def slot_is_occupied(self, index: int) -> bool:
        return bool(self.slots[index].get('player'))
    def persist_to_disk(self) -> None:
        persist_slots(self.slots)

    def sync_active_slot(self) -> None:
        if self.active_slot_index is None:
            self.persist_to_disk()
            return
        slot = self.slots[self.active_slot_index]
        slot['saved_item_sets'] = saved_item_sets_to_payload(self.saved_item_sets)
        slot['vault_items'] = [asdict(item) for item in self.vault_items]
        slot['ladder_stats'] = copy.deepcopy(self.ladder_stats)
        slot['unlocked_classes'] = sorted(normalize_unlocked_classes(self.unlocked_classes))
        slot['selection_return_class'] = self.selection_return_class if self.selection_return_class in CLASS_ORDER else None
        slot['monster_chain_combo'] = int(self.monster_chain_combo)
        if self.player is None:
            slot['player'] = None
            self.persist_to_disk()
            return
        slot['player'] = copy.deepcopy(self.player.to_dict())
        self.persist_to_disk()
    def open_slot(self, index: int) -> None:
        self.active_slot_index = index
        self.current_monster = None
        self.current_monster_xp = 0
        self.monster_chain_combo = int(self.slots[index].get('monster_chain_combo', 0) or 0)
        self.mana_regen_progress = 0.0
        self.clear_arena_monster_art(True)
        self.saved_item_sets = saved_item_sets_from_payload(self.slots[index].get('saved_item_sets'))
        self.unlocked_classes = normalize_unlocked_classes(self.slots[index].get('unlocked_classes'))
        self.selection_return_class = self.slots[index].get('selection_return_class') if self.slots[index].get('selection_return_class') in CLASS_ORDER else None
        self.vault_items = []
        for vault_item_data in self.slots[index].get('vault_items', []):
            if isinstance(vault_item_data, dict):
                try:
                    self.vault_items.append(Item(**vault_item_data))
                except Exception:
                    pass
        self.ladder_stats = normalize_ladder_stats(self.slots[index].get('ladder_stats'))
        self.selected_inventory_source = 'inventory'
        self.selected_inventory_key = ''
        self.marketplace_offers = []
        self.marketplace_offer_refresh_level = 0
        self.current_marketplace_line = ''
        self.marketplace_selected_index = 0
        self.marketplace_hovered_index = -1
        self.marketplace_pending_purchase_index = -1
        self.current_transmute_line = ''
        self.transmute_message = ''
        self.transmute_choice_one = ''
        self.transmute_choice_two = ''
        self.current_well_scene_line = ''
        self.current_inn_line = ''
        self.current_ladder_line = ''
        self.current_well_monster_asset_index = 0
        self.current_encounter_type = 'normal'
        self.last_encounter_type = 'normal'
        self.class_compendium_open = False
        slot_player = self.slots[index].get('player')
        if slot_player:
            self.player = Player.from_dict(copy.deepcopy(slot_player))
            self.selection_return_class = self.player.player_class
            self.pending_character_name = clean_character_name(self.player.name)
            self.monster_chain_combo = int(self.slots[index].get('monster_chain_combo', 0) or 0)
            self.unlocked_classes.add(self.player.player_class)
            self.game_tab = 'arena'
            self.screen = 'town'
            self.log = [CombatEvent(f'Chronicle Slot {index + 1} reopened. Welcome back, level {self.player.level} {self.player.player_class}.', 'success')]
        else:
            self.player = None
            self.saved_item_sets = saved_item_sets_from_payload(self.slots[index].get('saved_item_sets'))
            self.pending_character_name = clean_character_name(self.pending_character_name)
            self.screen = 'class_select'
            self.log = [CombatEvent(f'Slot {index + 1} stands empty. Choose a class to begin your ascent.', 'info')]
    def return_to_title(self) -> None:
        self.sync_active_slot()
        self.player = None
        self.current_monster = None
        self.current_monster_xp = 0
        self.monster_chain_combo = 0
        self.mana_regen_progress = 0.0
        self.clear_arena_monster_art(True)
        self.selection_return_class = None
        if self.player is not None:
            self.pending_character_name = clean_character_name(self.player.name)
        self.game_tab = 'arena'
        self.marketplace_offers = []
        self.marketplace_offer_refresh_level = 0
        self.current_marketplace_line = ''
        self.marketplace_selected_index = 0
        self.marketplace_hovered_index = -1
        self.marketplace_pending_purchase_index = -1
        self.current_transmute_line = ''
        self.transmute_message = ''
        self.transmute_choice_one = ''
        self.transmute_choice_two = ''
        self.current_well_scene_line = ''
        self.current_inn_line = ''
        self.current_ladder_line = ''
        self.current_well_monster_asset_index = 0
        self.current_encounter_type = 'normal'
        self.last_encounter_type = 'normal'
        self.class_compendium_open = False
        self.screen = 'title'
    def back_to_class_select(self) -> None:
        self.sync_active_slot()
        if self.player is not None:
            self.selection_return_class = self.player.player_class
            self.pending_character_name = clean_character_name(self.player.name)
            self.unlocked_classes.add(self.player.player_class)
        self.player = None
        self.current_monster = None
        self.current_monster_xp = 0
        self.clear_arena_monster_art(True)
        self.game_tab = 'arena'
        self.current_transmute_line = ''
        self.transmute_message = ''
        self.transmute_choice_one = ''
        self.transmute_choice_two = ''
        self.current_well_scene_line = ''
        self.current_inn_line = ''
        self.current_ladder_line = ''
        self.current_well_monster_asset_index = 0
        self.current_encounter_type = 'normal'
        self.last_encounter_type = 'normal'
        self.class_compendium_open = False
        self.screen = 'class_select'

    def complete_masterquest(self) -> None:
        if self.player is None:
            return
        current_class = self.player.player_class
        self.selection_return_class = current_class
        self.pending_character_name = clean_character_name(self.player.name)
        self.unlocked_classes.add(current_class)
        class_stats = self.ladder_stats.setdefault(current_class, build_default_ladder_stats().get(current_class, {}))
        class_stats['masterquest_attempts'] = int(class_stats.get('masterquest_attempts', 0) or 0) + 1
        denominator = masterquest_pass_denominator(current_class)
        passed = bool(self.test_mode) or (random.randint(1, max(1, denominator)) == 1)
        unlocked_next = None
        if passed:
            unlocked_next = CLASS_MASTERQUEST_NEXT.get(current_class)
            if unlocked_next:
                self.unlocked_classes.add(unlocked_next)
            elapsed = self.current_run_elapsed_seconds()
            if elapsed > 0 and current_class in self.ladder_stats:
                fastest = self.ladder_stats[current_class].get('fastest_masterquest_seconds')
                if fastest is None or float(elapsed) < float(fastest):
                    self.ladder_stats[current_class]['fastest_masterquest_seconds'] = float(elapsed)
        chance_text = 'guaranteed in Test Mode' if self.test_mode else f'1 in {denominator}'
        if passed and unlocked_next:
            self.class_select_notice = f'MasterQuest passed. {current_class} cleared the ritual and unlocked {unlocked_next}. Pass chance was {chance_text}.'
        elif passed:
            self.class_select_notice = f'MasterQuest passed. {current_class} cleared the ritual. Pass chance was {chance_text}.'
        else:
            self.class_select_notice = f'MasterQuest failed. {current_class} did not pass the ritual. Pass chance was {chance_text}. Return to character selection and try again.'
        self.player = None
        self.current_monster = None
        self.current_monster_xp = 0
        self.monster_chain_combo = 0
        self.mana_regen_progress = 0.0
        self.clear_arena_monster_art(True)
        self.game_tab = 'arena'
        self.marketplace_offers = []
        self.marketplace_offer_refresh_level = 0
        self.current_marketplace_line = ''
        self.marketplace_selected_index = 0
        self.marketplace_hovered_index = -1
        self.marketplace_pending_purchase_index = -1
        self.current_transmute_line = ''
        self.transmute_message = ''
        self.transmute_choice_one = ''
        self.transmute_choice_two = ''
        self.current_well_scene_line = ''
        self.current_inn_line = ''
        self.current_ladder_line = ''
        self.current_well_monster_asset_index = 0
        self.current_encounter_type = 'normal'
        self.last_encounter_type = 'normal'
        self.class_compendium_open = False
        self.screen = 'class_select'
        self.add_log(self.class_select_notice, 'success' if passed else 'warning')
        self.sync_active_slot()
    def enter_town(self, note: Optional[str] = None) -> None:
        if self.player is None:
            return
        self.screen = 'town'
        if note:
            self.add_log(note, 'info')
        self.sync_active_slot()
    def open_game_tab(self, tab_name: str, note: Optional[str] = None) -> None:
        if self.player is None:
            return
        self.class_compendium_open = False
        self.game_tab = tab_name
        self.screen = 'game'
        if tab_name == 'inn':
            self.ensure_inn_scene_state(True)
        elif tab_name == 'well':
            self.ensure_well_scene_state(True)
        if note:
            self.add_log(note, 'info')
        self.sync_active_slot()
    def visit_placeholder_route(self, route_name: str, description: str) -> None:
        if self.player is None:
            return
        self.screen = 'town'
        self.add_log(f'{route_name}: {description}', 'muted')
        self.sync_active_slot()
def toggle_class_compendium(self) -> None:
    self.class_compendium_open = not self.class_compendium_open

def ensure_well_scene_state(self, new_visit: bool = False) -> None:
    if self.player is None:
        return
    flirt_lines = [
        "The handmaiden smiles. 'Drop the coin, darling. The well always remembers a brave face.'",
        "She traces the well stones with one finger. 'Ten gold for terror, and perhaps a prettier treasure than last time.'",
        "The handmaiden leans close. 'Most heroes flinch after the first scream. You do not strike me as most heroes.'",
        "A low laugh escapes her. 'Feed the well and it will cough up something wicked... and possibly useful.'",
        "She bats her lashes at the darkness below. 'The well adores confidence. Lucky for you, it also accepts gold.'",
    ]
    if new_visit or not self.current_well_scene_line:
        self.current_well_scene_line = random.choice(flirt_lines)

def well_status_text(self) -> str:
    if self.player is None:
        return ''
    return (
        f"{self.player.name} the {self.player.player_class}  •  Gold {self.player.gold}  •  HP {self.player.hp}/{self.player.max_hp}  •  Mana {self.player.mana}/{self.player.max_mana}\n"
        f"Toss 10 gold into the well to summon a stronger foe with guaranteed loot and higher rarity rewards."
    )

def arena_monster_uri(self, display_monster: Optional[Fighter]) -> str:
    if display_monster is None:
        return ''
    encounter_type = self.current_encounter_type if self.current_monster is not None else self.last_encounter_type
    if encounter_type == 'well':
        return _well_monster_data_uri(self.current_well_monster_asset_index)
    if self.current_monster is not None and self.current_arena_monster_uri:
        return self.current_arena_monster_uri
    if self.current_monster is None and self.last_arena_monster_uri:
        return self.last_arena_monster_uri
    fallback = _arena_monster_data_uri(display_monster.monster_type)
    if self.current_monster is not None and fallback:
        self.current_arena_monster_uri = fallback
        self.current_arena_monster_species = monster_species_name(display_monster.monster_type)
    elif fallback:
        self.last_arena_monster_uri = fallback
        self.last_arena_monster_species = monster_species_name(display_monster.monster_type)
    return fallback

def set_current_arena_monster_art(self, monster: Optional[Fighter]) -> None:
    if monster is None:
        self.current_arena_monster_uri = ''
        self.current_arena_monster_species = ''
        return
    self.current_arena_monster_species = monster_species_name(monster.monster_type)
    self.current_arena_monster_uri = _arena_monster_data_uri(monster.monster_type)

def clear_arena_monster_art(self, clear_last: bool = False) -> None:
    self.current_arena_monster_uri = ''
    self.current_arena_monster_species = ''
    if clear_last:
        self.last_arena_monster_uri = ''
        self.last_arena_monster_species = ''

def current_xp_multiplier(self) -> float:
    return 31.0 if self.test_mode else 1.0

def passive_regen_tick(self) -> bool:
    if self.player is None or self.fight_in_progress:
        return False
    if self.player.max_mana <= 0 or self.player.mana >= self.player.max_mana or self.player.mana_regen <= 0:
        return False
    self.mana_regen_progress += self.player.mana_regen / 5.0
    mana_gain = int(self.mana_regen_progress)
    if mana_gain <= 0:
        return False
    self.mana_regen_progress -= mana_gain
    old_mana = self.player.mana
    self.player.mana = min(self.player.max_mana, self.player.mana + mana_gain)
    return self.player.mana != old_mana

def generate_well_monster(player_level: int) -> Tuple[Fighter, int]:
    monster, xp_reward = generate_monster(player_level, difficulty_multiplier=1.75, encounter_name='Wellspawn')
    monster.monster_personal_name = f"{monster.monster_personal_name}, Wellspawn"
    xp_reward = int(round(xp_reward * 1.40))
    return monster, xp_reward

def generate_well_item_drop(monster_level: int, player_class: str, magic_find: float) -> Item:
    item = generate_item_drop(monster_level, player_class, magic_find)
    boosted_rarity = shift_rarity(item.rarity, 1)
    return generate_specific_item(item.level, item.slot, item.subtype, boosted_rarity)

async def queue_well_encounter_async(self, refresh) -> None:
    if self.player is None or self.fight_in_progress:
        return
    if self.player.gold < 10:
        self.add_log('The Well of Evil demands 10 gold.', 'warning')
        refresh()
        return
    self.player.gold -= 10
    self.current_well_monster_asset_index = self.well_monster_cycle_index % 5
    self.well_monster_cycle_index += 1
    previous_monster = copy.deepcopy(self.last_monster_snapshot) if self.last_fight_outcome == 'victory' and self.last_monster_snapshot is not None else None
    self.current_encounter_type = 'well'
    self._set_arena_transition('The well churns. Something wicked claws its way toward the surface...', 'warning')
    self.add_log('You cast 10 gold into the Well of Evil. Something wicked answers.', 'warning')
    refresh()
    await asyncio.sleep(0)
    monster, xp_reward = generate_well_monster(self.player.level)
    self.current_monster = monster
    self.current_monster_xp = xp_reward
    self.last_monster_snapshot = None
    self.last_fight_outcome = 'idle'
    self.mana_regen_progress = 0.0
    self._set_arena_transition('')
    school = 'Magic' if monster.damage_school == 'magic' else 'Physical'
    self.add_log(f'A vile {monster.monster_type} appears!', 'warning')
    self.add_log(f'It answers to {monster.monster_personal_name}.', 'warning')
    self.add_log(f'{monster.monster_type} | Type {school} | Armor {monster.physical_armor} | M.Res {monster.magic_resistance}', 'muted')
    self.add_log(f'Enemy says: "{monster.monster_dialogue}"', 'muted')
    self.fight_in_progress = True
    if previous_monster is not None:
        self.page_turn_previous_monster = previous_monster
        await self._animate_monster_page_turn_async(refresh)
    else:
        refresh()
    await self._run_arena_combat_async(refresh)

def normalize_inventory_state(self) -> None:
    if self.player is not None:
        normalized_inventory: List[Item] = []
        for raw_item in list(self.player.inventory):
            item = coerce_item(raw_item)
            if item is not None:
                normalized_inventory.append(item)
        self.player.inventory = normalized_inventory
        normalized_equipped: Dict[str, Optional[Item]] = {}
        for slot in ('weapon', 'armor', 'charm'):
            normalized_equipped[slot] = coerce_item(self.player.equipped.get(slot))
        self.player.equipped = normalized_equipped
        self.player.recalculate_stats()
    normalized_saved_sets = empty_saved_item_sets()
    for category, slot_items in list((self.saved_item_sets or {}).items()):
        if not isinstance(slot_items, dict):
            continue
        for level, raw_item in list(slot_items.items()):
            item = coerce_item(raw_item)
            if item is None:
                continue
            normalized_category = category if category in normalized_saved_sets else get_saved_item_category(item)
            if normalized_category is None:
                continue
            try:
                level_key = int(level)
            except Exception:
                level_key = bucket_item_level(int(getattr(item, 'level', 1) or 1))
            normalized_saved_sets[normalized_category][level_key] = item
    self.saved_item_sets = normalized_saved_sets
    if self.selected_inventory_key:
        try:
            if self.selected_inventory_entry() is None:
                self.selected_inventory_source = 'inventory'
                self.selected_inventory_key = ''
        except Exception:
            self.selected_inventory_source = 'inventory'
            self.selected_inventory_key = ''
    if getattr(self, 'hovered_inventory_key', ''):
        try:
            valid_tokens = {self.inventory_selection_token(source, key) for source, key, _item in self.inventory_entries()}
            if self.hovered_inventory_key not in valid_tokens:
                self.hovered_inventory_key = ''
        except Exception:
            self.hovered_inventory_key = ''

def reset_inventory_filters(self) -> None:
    self.tier_filter = 'All tiers'
    self.type_filter = 'All types'
    self.attribute_filter = 'All attributes'
    self.inventory_sort = 'Level (High-Low)'
    self.inventory_search = ''
    self.selected_inventory_source = 'inventory'
    self.selected_inventory_key = ''
    self.hovered_inventory_key = ''
def inventory_entries(self) -> List[Tuple[str, object, Item]]:
    if self.player is None:
        return []
    entries: List[Tuple[str, object, Item]] = []
    if self.inventory_view == 'Saved Sets':
        for category in SAVED_ITEM_SET_ORDER:
            slot_items = self.saved_item_sets.get(category, {})
            if not isinstance(slot_items, dict):
                continue
            normalized_slot_items: Dict[int, Item] = {}
            for level, raw_item in list(slot_items.items()):
                item = coerce_item(raw_item)
                if item is None:
                    continue
                try:
                    level_key = int(level)
                except Exception:
                    level_key = bucket_item_level(getattr(item, 'level', 1))
                normalized_slot_items[level_key] = item
                entries.append(('saved', (category, level_key), item))
            self.saved_item_sets[category] = normalized_slot_items
    else:
        normalized_inventory: List[Item] = []
        for index, raw_item in enumerate(list(self.player.inventory)):
            item = coerce_item(raw_item)
            if item is None:
                continue
            normalized_inventory.append(item)
            entries.append(('inventory', len(normalized_inventory) - 1, item))
        if len(normalized_inventory) != len(self.player.inventory):
            self.player.inventory = normalized_inventory
    search = self.inventory_search.strip().lower()
    attribute_key = ATTRIBUTE_FILTER_KEY_BY_LABEL.get(self.attribute_filter)
    tier_bucket: Optional[int] = None
    if self.tier_filter != 'All tiers':
        try:
            tier_bucket = int(self.tier_filter.replace('Tier', '').strip())
        except Exception:
            tier_bucket = None
    filtered: List[Tuple[str, object, Item]] = []
    for source, key, item in entries:
        try:
            item_level = int(getattr(item, 'level', 1) or 1)
            if tier_bucket is not None and bucket_item_level(item_level) != tier_bucket:
                continue
            item_slot = str(getattr(item, 'slot', '') or '')
            item_type_label = saved_item_type_label(item)
            if self.type_filter != 'All types' and item_type_label != self.type_filter:
                continue
            if attribute_key and not item_matches_attribute(item, attribute_key):
                continue
            if search:
                haystack = f"{safe_item_name(item)} {safe_item_summary(item)} {safe_item_short_stat_text(item)} {getattr(item, 'rarity', '')} {getattr(item, 'subtype', '')} {item_slot} {item_type_label}".lower()
                if search not in haystack:
                    continue
            filtered.append((source, key, item))
        except Exception:
            continue
    if self.inventory_view == 'Saved Sets':
        filtered.sort(
            key=lambda entry: (
                SAVED_ITEM_SET_ORDER.index(get_saved_item_category(entry[2])) if get_saved_item_category(entry[2]) in SAVED_ITEM_SET_ORDER else 999,
                -int(getattr(entry[2], 'level', 1) or 1),
                -item_rarity_sort_key(entry[2]),
                ITEM_SLOT_SORT_ORDER.get(str(getattr(entry[2], 'slot', '') or ''), 99),
                safe_item_name(entry[2]).lower(),
            )
        )
    else:
        filtered.sort(
            key=lambda entry: (
                -int(getattr(entry[2], 'level', 1) or 1),
                -item_rarity_sort_key(entry[2]),
                ITEM_SLOT_SORT_ORDER.get(str(getattr(entry[2], 'slot', '') or ''), 99),
                safe_item_name(entry[2]).lower(),
            )
        )
    return filtered
def inventory_selection_token(self, source: str, key: object) -> str:
    if source == 'saved' and isinstance(key, tuple):
        return f'saved:{key[0]}:{key[1]}'
    return f'{source}:{key}'
def selected_inventory_entry(self) -> Optional[Tuple[str, object, Item]]:
    entries = self.inventory_entries()
    if not entries:
        return None
    for source, key, item in entries:
        if self.inventory_selection_token(source, key) == self.selected_inventory_key:
            return (source, key, item)
    source, key, item = entries[0]
    self.selected_inventory_source = source
    self.selected_inventory_key = self.inventory_selection_token(source, key)
    return (source, key, item)
def select_inventory_entry(self, source: str, key: object) -> None:
    self.selected_inventory_source = source
    self.selected_inventory_key = self.inventory_selection_token(source, key)
    self.hovered_inventory_key = ''
def equip_saved_item(self, slot: str, bucket: int) -> None:
    if self.player is None:
        return
    slot_items = self.saved_item_sets.get(slot, {})
    item = slot_items.get(bucket)
    if item is None:
        self.add_log('Select a saved item first.', 'warning')
        return
    can_equip, reason = can_player_equip_item(self.player, item)
    if not can_equip:
        self.add_log(f'Cannot equip {item.summary()}. {reason}', 'warning')
        return
    item = slot_items.pop(bucket, None)
    if item is None:
        self.add_log('That saved item no longer exists.', 'warning')
        return
    previous = self.player.equipped.get(item.slot)
    self.player.equipped[item.slot] = item
    if previous is not None:
        self.player.inventory.append(previous)
    self.player.recalculate_stats()
    self.selected_inventory_key = ''
    self.hovered_inventory_key = ''
    self.add_log(f'Equipped saved item {item.summary()}.', 'success')
    self.sync_active_slot()
def save_selected_item_to_set(self, inventory_index: int) -> None:
    if self.player is None:
        return
    if inventory_index < 0 or inventory_index >= len(self.player.inventory):
        self.add_log('Select an inventory item first.', 'warning')
        return
    item = self.player.inventory[inventory_index]
    if item.is_starter:
        self.add_log('Starter items cannot be saved into protected sets.', 'warning')
        return
    category = get_saved_item_category(item)
    if category is None:
        self.add_log('That item does not fit one of the protected set categories.', 'warning')
        return
    bucket = bucket_item_level(item.level)
    item = self.player.inventory.pop(inventory_index)
    replaced_item = self.saved_item_sets.setdefault(category, {}).get(bucket)
    self.saved_item_sets[category][bucket] = item
    if replaced_item is not None:
        self.player.inventory.append(replaced_item)
        self.add_log(f'Saved {item.summary()} into {SAVED_ITEM_SET_LABELS[category]} tier {bucket}. Returned the previous saved item to inventory.', 'success')
    else:
        self.add_log(f'Saved {item.summary()} into {SAVED_ITEM_SET_LABELS[category]} tier {bucket}.', 'success')
    self.inventory_view = 'Inventory'
    self.selected_inventory_source = 'inventory'
    self.selected_inventory_key = ''
    self.hovered_inventory_key = ''
    self.sync_active_slot()
def retrieve_saved_item_to_inventory(self, slot: str, bucket: int) -> None:
    if self.player is None:
        return
    slot_items = self.saved_item_sets.get(slot, {})
    item = slot_items.pop(bucket, None)
    if item is None:
        self.add_log('No saved item exists in that type.', 'warning')
        return
    self.player.inventory.append(item)
    self.add_log(f'Returned {item.summary()} from {SAVED_ITEM_SET_LABELS.get(slot, slot.title())} tier {bucket} to inventory.', 'success')
    self.inventory_view = 'Inventory'
    self.selected_inventory_source = 'inventory'
    self.selected_inventory_key = ''
    self.hovered_inventory_key = ''
    self.sync_active_slot()
def delete_inventory_item(self, inventory_index: int) -> None:
    if self.player is None:
        return
    if inventory_index < 0 or inventory_index >= len(self.player.inventory):
        return
    item = self.player.inventory.pop(inventory_index)
    self.add_log(f'Deleted {item.summary()}.', 'warning')
    self.selected_inventory_key = ''
    self.hovered_inventory_key = ''
    self.sync_active_slot()
def delete_saved_item(self, slot: str, bucket: int) -> None:
    item = self.saved_item_sets.get(slot, {}).pop(bucket, None)
    if item is None:
        return
    self.add_log(f'Removed saved set item {item.summary()} from {SAVED_ITEM_SET_LABELS.get(slot, slot.title())} tier {bucket}.', 'warning')
    self.selected_inventory_key = ''
    self.hovered_inventory_key = ''
    self.sync_active_slot()
def unequip_slot(self, slot: str) -> None:
    if self.player is None:
        return
    item = self.player.equipped.get(slot)
    if item is None:
        self.add_log(f'No {slot} is equipped.', 'warning')
        return
    self.player.equipped[slot] = None
    self.player.inventory.append(item)
    self.player.recalculate_stats()
    self.add_log(f'Unequipped {item.summary()}.', 'success')
    self.sync_active_slot()
def _set_arena_transition(self, text: str = '', tone: str = 'muted') -> None:
    self.arena_transition_text = text
    self.arena_transition_tone = tone
def arena_target_level(self) -> int:
    if self.player is None:
        return 1
    if self.arena_same_level:
        self.arena_selected_level = self.player.level
        return self.player.level
    self.arena_selected_level = max(1, min(self.player.level, int(self.arena_selected_level or self.player.level)))
    return self.arena_selected_level
def arena_display_monster(self) -> Optional[Fighter]:
    if self.monster_page_turn_active and self.page_turn_previous_monster is not None and self.monster_page_turn_progress < 0.5:
        return self.page_turn_previous_monster
    if self.current_monster is not None:
        return self.current_monster
    return self.last_monster_snapshot
def log_status(self) -> None:
    if self.player is None:
        return
    arena_target_label = 'Hero Level' if self.arena_same_level else f'Lv {self.arena_target_level()}'
    self.add_log(
        f'STATUS | Class {self.player.player_class} | Level {self.player.level} | HP {self.player.hp}/{self.player.max_hp} | Mana {self.player.mana}/{self.player.max_mana} | {attack_mode_label(self.player)} | Armor {self.player.physical_armor} | M.Res {self.player.magic_resistance} | Gold {self.player.gold} | XP {self.player.xp}/{self.player.xp_to_next}',
        'muted',
    )
    self.add_log(
        f'CORE | STR {self.player.strength} | DEX {self.player.dexterity} | INT {self.player.intelligence} | VIT {self.player.vitality} | Unspent {self.player.unspent_stat_points}',
        'muted',
    )
    self.add_log(
        f'COMBAT | Crit {int(round(self.player.crit_chance * 100))}% | Crit Dmg {int(round(self.player.crit_damage * 100))}% | Armor Pen {self.player.armor_penetration} | Lifesteal {int(round(self.player.lifesteal * 100))}% | Magic Find {int(round(self.player.magic_find * 100))}% | XP Gain {int(round(self.player.xp_gain * 100))}% | Chain x{self.monster_chain_combo} (+{int(round(get_monster_chain_bonus_fraction(self.monster_chain_combo) * 100))}% XP) | Arena Target {arena_target_label}',
        'muted',
    )
    weapon = self.player.equipped.get('weapon')
    armor = self.player.equipped.get('armor')
    charm = self.player.equipped.get('charm')
    self.add_log(
        f'EQUIPPED | Weapon: {weapon.name if weapon else "None"} | Armor: {armor.name if armor else "None"} | Charm: {charm.name if charm else "None"}',
        'muted',
    )
async def rest_async(self, refresh) -> None:
    try:
        self.rest()
    except Exception as exc:
        self.add_log(f'Rest failed, but your run was preserved: {exc}', 'danger')
    refresh()
async def _animate_monster_page_turn_async(self, refresh) -> None:
    self.monster_page_turn_active = False
    self.monster_page_turn_progress = 0.0
    self.page_turn_previous_monster = None
    refresh()
    await asyncio.sleep(0)
async def queue_arena_encounter_async(self, refresh) -> None:
    try:
        if self.player is None or self.fight_in_progress:
            return
        target_level = self.arena_target_level()
        previous_monster = copy.deepcopy(self.last_monster_snapshot) if self.last_fight_outcome == 'victory' and self.last_monster_snapshot is not None else None
        if target_level < self.player.level:
            penalty_pct = max(0, self.player.level - target_level) * 10
            self.add_log(f'You call out a weaker foe at level {target_level}. XP reward will be reduced by {penalty_pct}%.', 'warning')
        self._set_arena_transition('The arena gates grind open and the next challenger takes shape...', 'accent')
        refresh()
        await asyncio.sleep(0)
        monster, xp_reward = generate_monster(self.player.level, forced_level=target_level)
        self.current_encounter_type = 'normal'
        self.current_monster = monster
        self.current_monster_xp = xp_reward
        self.set_current_arena_monster_art(monster)
        self.last_monster_snapshot = None
        self.last_arena_monster_uri = ''
        self.last_arena_monster_species = ''
        self.last_fight_outcome = 'idle'
        self.mana_regen_progress = 0.0
        self._set_arena_transition('')
        prefix = 'A wild'
        school = 'Magic' if monster.damage_school == 'magic' else 'Physical'
        self.add_log(f'{prefix} {monster.monster_type} appears!', 'muted')
        self.add_log(f'It answers to {monster.monster_personal_name}.', 'muted')
        self.add_log(f'{monster.monster_type} | Type {school} | Armor {monster.physical_armor} | M.Res {monster.magic_resistance}', 'muted')
        self.add_log(f'Enemy says: "{monster.monster_dialogue}"', 'muted')
        self.fight_in_progress = True
        if previous_monster is not None:
            self.page_turn_previous_monster = previous_monster
            await self._animate_monster_page_turn_async(refresh)
        else:
            refresh()
        await self._run_arena_combat_async(refresh)
    except Exception as exc:
        self.fight_in_progress = False
        self.current_monster = None
        self.current_monster_xp = 0
        self.clear_arena_monster_art(False)
        self._set_arena_transition('Encounter error. Your run was preserved.', 'danger')
        self.add_log(f'Encounter error: {exc}', 'danger')
        self.sync_active_slot()
        refresh()
async def _run_arena_combat_async(self, refresh) -> None:
    if self.player is None or self.current_monster is None:
        self.fight_in_progress = False
        return
    sim_player = copy.deepcopy(self.player)
    sim_monster = copy.deepcopy(self.current_monster)
    timeline = build_combat_timeline(sim_player, sim_monster)
    pending_rounds = 0
    for index, (event, player_hp, player_mana, monster_hp, player_wins, player_losses) in enumerate(timeline):
        if self.player is None or self.current_monster is None:
            self.fight_in_progress = False
            return
        self.player.hp = player_hp
        self.player.mana = player_mana
        self.player.wins = player_wins
        self.player.losses = player_losses
        self.current_monster.hp = monster_hp
        self.add_log(event.text, event.tag)
        if event.tag == 'round':
            pending_rounds += 1
        next_tag = timeline[index + 1][0].tag if index + 1 < len(timeline) else None
        end_of_chunk = next_tag == 'round' or index == len(timeline) - 1
        if end_of_chunk and pending_rounds > 0:
            refresh()
            await asyncio.sleep(self.log_delay_ms / 1000.0)
            pending_rounds = 0
    self.player = sim_player
    self.current_monster = sim_monster
    await self._finish_arena_fight_async(refresh)
async def _finish_arena_fight_async(self, refresh) -> None:
    if self.player is None or self.current_monster is None:
        self.fight_in_progress = False
        refresh()
        return
    defeated_monster = copy.deepcopy(self.current_monster)
    encounter_type = self.current_encounter_type
    if self.player.is_alive() and not self.current_monster.is_alive():
        class_stats = self.ladder_stats.setdefault(self.player.player_class, build_default_ladder_stats().get(self.player.player_class, {}))
        class_stats['enemy_kills'] = int(class_stats.get('enemy_kills', 0) or 0) + 1
        if encounter_type == 'well':
            class_stats['wellspawns_killed'] = int(class_stats.get('wellspawns_killed', 0) or 0) + 1
        if encounter_type == 'normal':
            self.monster_chain_combo += 1
            combo_bonus = get_monster_chain_bonus_fraction(self.monster_chain_combo)
            combo_bonus_pct = int(round(combo_bonus * 100))
            self.add_log(f'Monster Chain Combo x{self.monster_chain_combo}! +{combo_bonus_pct}% XP (max 15%).', 'success')
        else:
            combo_bonus = 0.0
        level_xp_multiplier = xp_multiplier_for_level_difference(self.player.level, self.current_monster.level)
        gained_xp = int(round(self.current_monster_xp * (1.0 + combo_bonus + self.player.xp_gain) * self.current_xp_multiplier() * level_xp_multiplier))
        self.add_log(f'You gain {gained_xp} XP.', 'success')
        if level_xp_multiplier < 1.0:
            penalty_pct = int(round((1.0 - level_xp_multiplier) * 100))
            self.add_log(f'Lower-level fight penalty: -{penalty_pct}% XP for fighting below your level.', 'warning')
        for msg in gain_xp(self.player, gained_xp):
            self.add_log(msg, 'success')
        if self.player.life_per_kill > 0:
            gain = min(self.player.max_hp - self.player.hp, self.player.life_per_kill)
            if gain > 0:
                self.player.hp += gain
                self.add_log(f'Life per kill restores {gain} HP.', 'success')
        if self.player.mana_per_kill > 0:
            gain = min(self.player.max_mana - self.player.mana, self.player.mana_per_kill)
            if gain > 0:
                self.player.mana += gain
                self.add_log(f'Mana per kill restores {gain} Mana.', 'success')
        if encounter_type == 'well':
            item = generate_well_item_drop(self.current_monster.level, self.player.player_class, self.player.magic_find)
            self.player.inventory.append(item)
            self.add_log('The Well of Evil yields a guaranteed treasure.', 'warning')
            self.add_log(f'Loot found: {item.summary()}.', 'success')
        else:
            drop_chance = clamp(0.333 + self.player.magic_find * 0.10, 0.333, 0.60)
            if random.random() < drop_chance:
                item = generate_item_drop(self.current_monster.level, self.player.player_class, self.player.magic_find)
                self.player.inventory.append(item)
                self.add_log(f'Loot found: {item.summary()}.', 'success')
            else:
                self.add_log('No item dropped this time.', 'muted')
        self.last_fight_outcome = 'victory'
        self._set_arena_transition('Victory settles over the sand. The next gate awaits your call.', 'success')
        self.add_log('Victory settles over the sand.', 'success')
    else:
        class_stats = self.ladder_stats.setdefault(self.player.player_class, build_default_ladder_stats().get(self.player.player_class, {}))
        class_stats['total_deaths'] = int(class_stats.get('total_deaths', 0) or 0) + 1
        lost_xp = int(round(self.player.xp * 0.25)) if self.player.level < 60 and self.player.xp_to_next > 0 else 0
        if lost_xp > 0:
            self.player.xp = max(0, self.player.xp - lost_xp)
            self.add_log(f'You lose {lost_xp} XP progress.', 'danger')
        self.player.hp = max(1, self.player.hp)
        self.monster_chain_combo = 0
        self.last_fight_outcome = 'defeat'
        self._set_arena_transition('You survive. The next gate awaits when you are ready.', 'danger')
        self.add_log('You drag yourself upright and the arena waits.', 'warning')
    self.last_monster_snapshot = defeated_monster
    self.last_encounter_type = encounter_type
    if encounter_type != 'well':
        self.last_arena_monster_uri = self.current_arena_monster_uri
        self.last_arena_monster_species = self.current_arena_monster_species
    refresh()
    await asyncio.sleep(0)
    self.current_monster = None
    self.current_monster_xp = 0
    self.clear_arena_monster_art(False)
    self.fight_in_progress = False
    self.current_encounter_type = 'normal'
    if self.last_fight_outcome == 'victory':
        self._set_arena_transition('The fallen challenger sinks into the dark. Call the next foe when you are ready.', 'muted')
    elif self.last_fight_outcome == 'defeat':
        self._set_arena_transition('You steady your breathing. Call the next foe when you are ready.', 'muted')
    else:
        self._set_arena_transition('Choose when to call the next challenger.', 'muted')
    if encounter_type == 'well':
        self.game_tab = 'well'
        self.ensure_well_scene_state(False)
    self.sync_active_slot()
    refresh()
def add_log(self, text: str, tag: str = 'info') -> None:
    self.log.append(CombatEvent(text, tag))
    self.log = self.log[-120:]
def start_game(self, player_class: str) -> None:
    if player_class not in self.unlocked_classes:
        self.add_log(f'{player_class} is still locked on this chronicle.', 'warning')
        return
    self.selection_return_class = player_class
    self.pending_character_name = clean_character_name(self.pending_character_name)
    self.player = create_player(player_class)
    self.player.name = self.pending_character_name
    self.current_run_started_at = time.monotonic()
    self.current_monster = None
    self.current_monster_xp = 0
    self.monster_chain_combo = 0
    self.mana_regen_progress = 0.0
    self.marketplace_offers = []
    self.marketplace_offer_refresh_level = 0
    self.current_marketplace_line = ''
    self.marketplace_selected_index = 0
    self.current_well_scene_line = ''
    self.current_well_monster_asset_index = 0
    self.current_encounter_type = 'normal'
    self.last_encounter_type = 'normal'
    self.class_compendium_open = False
    self.class_select_notice = ''
    self.reset_inventory_filters()
    if self.active_slot_index is not None and not self.slots[self.active_slot_index].get('player'):
        self.saved_item_sets = empty_saved_item_sets()
    self.game_tab = 'arena'
    self.screen = 'town'
    self.log = [CombatEvent(f'You begin your journey as a {player_class}.', 'success')]
    self.sync_active_slot()
def spawn_monster(self) -> None:
    if self.player is None:
        return
    self.current_monster, self.current_monster_xp = generate_monster(self.player.level, forced_level=self.player.level)
    self.add_log(f'A new foe appears: {self.current_monster.monster_personal_name} ({self.current_monster.monster_type}).', 'warning')
    if self.current_monster.monster_dialogue:
        self.add_log(f'"{self.current_monster.monster_dialogue}"', 'muted')
    self.sync_active_slot()
def rest(self) -> None:
    if self.player is None:
        return
    cost = 1
    if self.player.gold < cost:
        self.add_log('You need 1 gold to rest.', 'warning')
        return
    self.player.gold -= cost
    self.monster_chain_combo = 0
    heal = max(10, int(self.player.max_hp * 0.35))
    mana_gain = max(4, int(max(1, self.player.max_mana) * 0.35))
    old_hp = self.player.hp
    old_mana = self.player.mana
    self.player.hp = min(self.player.max_hp, self.player.hp + heal)
    self.player.mana = min(self.player.max_mana, self.player.mana + mana_gain)
    self.add_log(f'You rest at the inn and recover {self.player.hp - old_hp} HP and {self.player.mana - old_mana} Mana. Monster Chain Combo reset.', 'success')
    self.sync_active_slot()
def fight(self) -> None:
    if self.player is None:
        self.add_log('Start a game first.', 'warning')
        return
    if self.current_monster is None:
        self.spawn_monster()
        return
    events = build_combat_events(self.player, self.current_monster)
    self.log.extend(events)
    if self.player.is_alive() and not self.current_monster.is_alive():
        if self.current_encounter_type == 'normal':
            self.monster_chain_combo += 1
        combo_bonus = get_monster_chain_bonus_fraction(self.monster_chain_combo if self.current_encounter_type == 'normal' else 0)
        level_xp_multiplier = xp_multiplier_for_level_difference(self.player.level, self.current_monster.level)
        gained_xp = int(round(self.current_monster_xp * (1.0 + combo_bonus + self.player.xp_gain) * self.current_xp_multiplier() * level_xp_multiplier))
        xp_messages = gain_xp(self.player, gained_xp)
        self.add_log(f'You gain {gained_xp} XP.', 'success')
        for msg in xp_messages:
            self.add_log(msg, 'success')
        if self.player.life_per_kill > 0:
            self.player.hp = min(self.player.max_hp, self.player.hp + self.player.life_per_kill)
        if self.player.mana_per_kill > 0:
            self.player.mana = min(self.player.max_mana, self.player.mana + self.player.mana_per_kill)
        if random.random() < 0.88:
            item = generate_item_drop(self.current_monster.level, self.player.player_class, self.player.magic_find)
            self.player.inventory.append(item)
            self.add_log(f'Loot found: {item.summary()}.', 'success')
        self.current_monster = None
        self.current_monster_xp = 0
        self.sync_active_slot()
    else:
        self.current_monster = None
        self.current_monster_xp = 0
        self.monster_chain_combo = 0
        slot_number = (self.active_slot_index + 1) if self.active_slot_index is not None else 1
        self.add_log('Your current run has ended. The slot has been cleared for a new hero.', 'danger')
        self.player = None
        if self.active_slot_index is not None:
            self.slots[self.active_slot_index]['player'] = None
            self.slots[self.active_slot_index]['selection_return_class'] = None
        self.screen = 'title'
        self.log = [CombatEvent(f'Chronicle Slot {slot_number} has fallen. Choose a slot to begin again.', 'danger')]
        self.persist_to_disk()
def equip_item(self, inventory_index: int) -> None:
    if self.player is None:
        return
    if inventory_index < 0 or inventory_index >= len(self.player.inventory):
        return
    item = self.player.inventory[inventory_index]
    can_equip, reason = can_player_equip_item(self.player, item)
    if not can_equip:
        self.add_log(f'Cannot equip {item.summary()}. {reason}', 'warning')
        return
    item = self.player.inventory.pop(inventory_index)
    previous = self.player.equipped.get(item.slot)
    self.player.equipped[item.slot] = item
    if previous is not None:
        self.player.inventory.append(previous)
    self.player.recalculate_stats()
    self.add_log(f'Equipped {item.summary()}.', 'success')
    self.sync_active_slot()
def sell_item(self, inventory_index: int) -> None:
    if self.player is None:
        return
    if inventory_index < 0 or inventory_index >= len(self.player.inventory):
        return
    item = self.player.inventory.pop(inventory_index)
    value = item.sell_value()
    self.player.gold += value
    self.add_log(f'Sold {item.summary()} for {value} gold.', 'warning')
    self.sync_active_slot()
def allocate(self, stat_key: str) -> None:
    if self.player is None:
        return
    msg = self.player.allocate_core_stat(stat_key)
    self.add_log(msg, 'success' if msg.startswith('Allocated') else 'warning')
    self.sync_active_slot()
def allocate_multiple(self, stat_key: str, amount: int = 1) -> None:
    if self.player is None:
        return
    try:
        spend_target = max(1, int(amount))
    except Exception:
        spend_target = 1
    allocated = 0
    last_msg = ''
    for _ in range(spend_target):
        msg = self.player.allocate_core_stat(stat_key)
        last_msg = msg
        if not msg.startswith('Allocated'):
            break
        allocated += 1
    if allocated > 0:
        label = STAT_LABELS.get(stat_key, stat_key.upper())
        suffix = '' if allocated == 1 else 's'
        self.add_log(f'Allocated {allocated} point{suffix} to {label}.', 'success')
    elif last_msg:
        self.add_log(last_msg, 'warning')
    self.sync_active_slot()
def export_save(self) -> None:
    if self.player is None:
        self.export_code = ''
        self.add_log('Nothing to export yet.', 'warning')
        return
    payload = {
        'player': self.player.to_dict(),
        'vault_items': [asdict(item) for item in self.vault_items],
        'saved_item_sets': saved_item_sets_to_payload(self.saved_item_sets),
        'ladder_stats': copy.deepcopy(self.ladder_stats),
        'unlocked_classes': sorted(self.unlocked_classes),
        'selection_return_class': self.selection_return_class,
    }
    raw = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    self.export_code = base64.urlsafe_b64encode(raw).decode('utf-8')
    self.add_log('Save code generated. Copy it from the Save tab.', 'success')
    self.sync_active_slot()
def import_save(self) -> None:
    code = self.import_code.strip()
    if not code:
        self.add_log('Paste a save code first.', 'warning')
        return
    try:
        raw = base64.urlsafe_b64decode(code.encode('utf-8'))
        payload = json.loads(raw.decode('utf-8'))
        self.player = Player.from_dict(payload['player'])
        self.vault_items = []
        for vault_item_data in payload.get('vault_items', []):
            if isinstance(vault_item_data, dict):
                try:
                    self.vault_items.append(Item(**vault_item_data))
                except Exception:
                    pass
        self.saved_item_sets = saved_item_sets_from_payload(payload.get('saved_item_sets'))
        self.ladder_stats = normalize_ladder_stats(payload.get('ladder_stats'))
        for class_name in payload.get('unlocked_classes', []):
            if isinstance(class_name, str):
                self.unlocked_classes.add(class_name)
        self.selection_return_class = payload.get('selection_return_class') or self.player.player_class
        self.pending_character_name = clean_character_name(self.player.name)
        self.current_run_started_at = time.monotonic()
        self.current_monster = None
        self.current_monster_xp = 0
        self.game_tab = 'arena'
        self.screen = 'town'
        self.log = [CombatEvent(f'Save imported. Welcome back, level {self.player.level} {self.player.player_class}.', 'success')]
        self.sync_active_slot()
    except Exception as exc:
        self.add_log(f'Could not import save code: {exc}', 'danger')
def ensure_inn_scene_state(self, new_visit: bool = False) -> None:
    if self.player is None:
        return
    innkeeper_greetings = globals().get('INNKEEPER_GREETINGS') or [
        'Warm firelight spills across the room. The innkeeper offers a quiet nod.',
        'Beds are few, walls are sturdy, and the soup smells better than the road.',
        'The innkeeper polishes a mug and says, "Coin buys comfort. Comfort buys tomorrow."',
        'A low hearth crackles while the innkeeper gestures toward the open rooms.',
        'The common room is calm tonight. The innkeeper taps the counter and waits for your choice.',
    ]
    if new_visit or not self.current_inn_line:
        self.current_inn_line = random.choice(innkeeper_greetings)

def inn_status_text(self) -> str:
    if self.player is None:
        return ''
    return (
        f"{self.player.name} the {self.player.player_class}  •  Gold {self.player.gold}  •  HP {self.player.hp}/{self.player.max_hp}  •  Mana {self.player.mana}/{self.player.max_mana}\n"
        f"A room costs 1 gold. Resting restores 35% HP (min 10), 35% Mana (min 4), and resets your Monster Chain Combo. Vault: {len(self.vault_items)}/20 items. Storage costs 5 gold; withdrawals are free."
    )

def inn_rest(self) -> None:
    if self.player is None:
        return
    if self.player.gold < 1:
        self.current_inn_line = 'No coin, no pillow. Even kindness needs kindling, traveler.'
        self.add_log('You need 1 gold to rest at the inn.', 'warning')
        return
    old_hp = self.player.hp
    old_mana = self.player.mana
    self.player.gold -= 1
    self.monster_chain_combo = 0
    heal = max(10, int(self.player.max_hp * 0.35))
    mana_gain = max(4, int(max(1, self.player.max_mana) * 0.35))
    self.player.hp = min(self.player.max_hp, self.player.hp + heal)
    self.player.mana = min(self.player.max_mana, self.player.mana + mana_gain)
    self.current_inn_line = random.choice([
        'There now. Even doom looks smaller after a proper rest.',
        'Fresh sheets, warm stew, and not a single goblin under the bed. Probably.',
        'You look less haunted already. That will be 1 gold well spent.',
        'Rest easy. The darkness will still be there in the morning.',
    ])
    self.add_log(f'You rest for 1 gold and recover {self.player.hp - old_hp} HP and {self.player.mana - old_mana} Mana. Monster Chain Combo reset.', 'success')
    self.sync_active_slot()

def store_vault_item(self, inventory_index: int) -> None:
    if self.player is None:
        return
    if inventory_index < 0 or inventory_index >= len(self.player.inventory):
        return
    if len(self.vault_items) >= 20:
        self.add_log('The vault is full. Withdraw something before storing more.', 'warning')
        return
    if self.player.gold < 5:
        self.add_log('You need 5 gold to store an item in the vault.', 'warning')
        return
    item = self.player.inventory.pop(inventory_index)
    self.player.gold -= 5
    self.vault_items.append(item)
    self.add_log(f'Stored {item.summary()} in the Inn Vault for 5 gold.', 'success')
    self.sync_active_slot()

def withdraw_vault_item(self, vault_index: int) -> None:
    if self.player is None:
        return
    if vault_index < 0 or vault_index >= len(self.vault_items):
        return
    item = self.vault_items.pop(vault_index)
    self.player.inventory.append(item)
    self.add_log(f'Withdrew {item.summary()} from the Inn Vault.', 'success')
    self.sync_active_slot()

def current_run_elapsed_seconds(self) -> float:
    if self.current_run_started_at <= 0:
        return 0.0
    return max(0.0, time.monotonic() - self.current_run_started_at)

def ensure_ladder_scene_state(self, new_visit: bool = False) -> None:
    if new_visit or not self.current_ladder_line:
        self.current_ladder_line = 'The registrar records speed, ruin, and stubbornness with exactly the same expression.'

def ladder_totals_text(self) -> str:
    total_attempts = sum(int(stats['masterquest_attempts']) for stats in self.ladder_stats.values())
    total_kills = sum(int(stats['enemy_kills']) for stats in self.ladder_stats.values())
    total_deaths = sum(int(stats['total_deaths']) for stats in self.ladder_stats.values())
    total_wellspawns = sum(int(stats['wellspawns_killed']) for stats in self.ladder_stats.values())
    return f'MasterQuest Attempts {total_attempts}  •  Enemy Kills {total_kills}\nDeaths {total_deaths}  •  Wellspawns {total_wellspawns}'

def ladder_fastest_rows(self) -> List[Tuple[str, float]]:
    fastest = [(class_name, stats['fastest_masterquest_seconds']) for class_name, stats in self.ladder_stats.items() if stats.get('fastest_masterquest_seconds') is not None]
    fastest.sort(key=lambda entry: float(entry[1]))
    return fastest

def ladder_table_rows(self) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    current_class = self.player.player_class if self.player is not None else None
    for class_name in CLASS_ORDER:
        stats = self.ladder_stats.get(class_name, {})
        rows.append({
            'class_name': class_name,
            'masterquest_attempts': int(stats.get('masterquest_attempts', 0) or 0),
            'fastest_masterquest_seconds': stats.get('fastest_masterquest_seconds'),
            'enemy_kills': int(stats.get('enemy_kills', 0) or 0),
            'total_deaths': int(stats.get('total_deaths', 0) or 0),
            'wellspawns_killed': int(stats.get('wellspawns_killed', 0) or 0),
            'current': class_name == current_class,
        })
    return rows

def glossary_lines(self) -> str:
    return build_glossary_text()

# Bind the arena/state helpers onto SessionState.
# These functions are defined with a self parameter and are intended to behave as
# instance methods in the browser port.
def get_transmute_item_refs(self) -> List[Tuple[str, object, Item]]:
    if self.player is None:
        return []
    return [('inventory', index, item) for index, item in enumerate(self.player.inventory)]
def format_transmute_choice(self, source: str, key: object, item: Item) -> str:
    source_label = f'INV {int(key) + 1}' if source == 'inventory' else f'EQ {str(key).title()}'
    return f'{source_label} • T{item.level} • {item.rarity} • {item.subtype} {item.slot.title()}'
def transmute_items_match(self, first: Item, second: Item) -> bool:
    return first.level == second.level and first.slot == second.slot and first.subtype == second.subtype
def transmute_item_map(self) -> Dict[str, Tuple[str, object, Item]]:
    item_map: Dict[str, Tuple[str, object, Item]] = {}
    for source, key, item in self.get_transmute_item_refs():
        base_label = self.format_transmute_choice(source, key, item)
        label = base_label
        suffix = 2
        while label in item_map:
            label = f'{base_label} #{suffix}'
            suffix += 1
        item_map[label] = (source, key, item)
    return item_map
def available_transmute_first_labels(self) -> List[str]:
    item_map = self.transmute_item_map()
    labels: List[str] = []
    for label, (_source, _key, item) in item_map.items():
        if any(other_label != label and self.transmute_items_match(item, other_item) for other_label, (_s2, _k2, other_item) in item_map.items()):
            labels.append(label)
    return labels
def available_transmute_second_labels(self) -> List[str]:
    item_map = self.transmute_item_map()
    first_ref = item_map.get(self.transmute_choice_one)
    if first_ref is None:
        return []
    first_source, first_key, first_item = first_ref
    labels: List[str] = []
    for label, (source, key, item) in item_map.items():
        if source == first_source and key == first_key:
            continue
        if self.transmute_items_match(first_item, item):
            labels.append(label)
    return labels
def sync_transmute_selection(self) -> None:
    first_labels = self.available_transmute_first_labels()
    if self.transmute_choice_one not in first_labels:
        self.transmute_choice_one = first_labels[0] if first_labels else ''
    second_labels = self.available_transmute_second_labels()
    if self.transmute_choice_two not in second_labels:
        self.transmute_choice_two = second_labels[0] if second_labels else ''
def selected_transmute_refs(self) -> Tuple[Optional[Tuple[str, object, Item]], Optional[Tuple[str, object, Item]]]:
    item_map = self.transmute_item_map()
    return item_map.get(self.transmute_choice_one), item_map.get(self.transmute_choice_two)
def ensure_transmute_scene_state(self, new_visit: bool = False) -> None:
    if self.player is None:
        return
    jaguar_lines = [
        "Varkesh flicks his tail. 'I am not irritated. I am simply burdened by standards no one else here can comprehend.'",
        "'Yes, I sighed,' the jaguar says. 'That was not about you specifically. It was about the tragedy of mediocre offerings as a concept.'",
        "Varkesh adjusts a brass ring with theatrical annoyance. 'Bring me matching relics, not emotional complications disguised as equipment.'",
        "'I do not have an attitude,' he mutters, already offended. 'I have discernment, and it suffers in your presence more than either of us deserve.'",
        "The jaguar looks wounded by your existence for a moment, then clears his throat. 'Two matching items. Twenty-five gold. Try to make this difficult in a more interesting way.'",
    ]
    if new_visit or not self.current_transmute_line:
        self.current_transmute_line = random.choice(jaguar_lines)
    refs = self.get_transmute_item_refs()
    has_pair = any(self.transmute_items_match(first[2], second[2]) for i, first in enumerate(refs) for second in refs[i + 1:])
    if self.player.gold < 25:
        self.transmute_message = 'You need 25 gold before Varkesh will even pretend to tolerate the process.'
    elif len(refs) < 2:
        self.transmute_message = 'You need at least two inventory items to transmute.'
    elif not has_pair:
        self.transmute_message = 'No matching inventory pair is available right now.'
    elif new_visit or not self.transmute_message:
        self.transmute_message = 'Choose two matching offerings.'
    self.sync_transmute_selection()
def transmute_selected(self) -> None:
    if self.player is None:
        return
    self.ensure_transmute_scene_state(False)
    first_ref, second_ref = self.selected_transmute_refs()
    if first_ref is None or second_ref is None:
        self.transmute_message = 'Choose two offerings first.'
        return
    if first_ref[0] == second_ref[0] and first_ref[1] == second_ref[1]:
        self.transmute_message = 'You must offer two different items.'
        return
    first_item = first_ref[2]
    second_item = second_ref[2]
    if not self.transmute_items_match(first_item, second_item):
        self.transmute_message = 'Those offerings do not match. Both items must share tier, slot, and subtype.'
        return
    if self.player.gold < 25:
        self.transmute_message = "Varkesh folds his arms. 'No gold, no miracle.'"
        return
    self.player.gold -= 25
    removals = sorted([first_ref, second_ref], key=lambda ref: int(ref[1]), reverse=True)
    for source, key, _item in removals:
        if source == 'inventory':
            index = int(key)
            if 0 <= index < len(self.player.inventory):
                self.player.inventory.pop(index)
    result_rarity = determine_transmute_rarity(first_item, second_item)
    new_item = generate_specific_item(first_item.level, first_item.slot, first_item.subtype, result_rarity)
    self.player.inventory.append(new_item)
    self.player.recalculate_stats()
    self.current_transmute_line = random.choice([
        "'There,' the jaguar says defensively. 'An excellent result. Obviously. You looked surprised, which is insulting.'",
        "Varkesh exhales through his nose. 'I made that look easy. It was not easy. You are welcome, though I resent needing to say so.'",
        "'Do not stare at me like that,' he mutters. 'The transmutation was flawless. Your expectations were the problem.'",
    ])
    self.transmute_message = f'Varkesh hisses at the sparks and unveils {new_item.summary()}. Another transmutation may begin at once.'
    self.add_log(f'Transmutation: {first_item.summary()} + {second_item.summary()} → {new_item.summary()} for 25 gold.', 'success')
    self.transmute_choice_one = ''
    self.transmute_choice_two = ''
    self.sync_active_slot()
    self.ensure_transmute_scene_state(False)
def ensure_marketplace_offers(self, force_reroll: bool = False) -> None:
    if self.player is None:
        return
    refresh_level = marketplace_refresh_breakpoint(self.player.level)
    banter_lines = [
        "Liora twirls a ribbon around one finger. 'You should buy something dazzling.' Senna grins. 'Or stay and let us keep complimenting you.'",
        "Senna leans on the counter. 'Item 1 is perfect for a dangerous little legend.' Liora hums, 'And Item 2 matches your eyes better.'",
        "The two fairies begin debating which trinket makes you look more heroic, then get distracted complimenting each other halfway through.",
        "Liora whispers, 'We stock only the finest curiosities.' Senna adds, 'And the finest gossip. Hers is sweeter, mine is sharper.'",
        "'Do not rush,' Senna says. Liora laughs softly. 'Love and shopping both deserve lingering.'",
    ]
    if force_reroll or refresh_level != self.marketplace_offer_refresh_level or len(self.marketplace_offers) != 3:
        self.marketplace_offer_refresh_level = refresh_level
        self.marketplace_offers = [generate_marketplace_offer(index, self.player.level) for index in range(3)]
        self.marketplace_selected_index = 0
        self.marketplace_hovered_index = -1
        self.marketplace_pending_purchase_index = -1
    if not self.current_marketplace_line:
        self.current_marketplace_line = random.choice(banter_lines)
def get_next_marketplace_reroll_level(self) -> Optional[int]:
    if self.player is None:
        return None
    for level in (10, 20, 30, 40, 50, 60):
        if self.player.level < level:
            return level
    return None
def selected_marketplace_offer(self) -> Optional[MarketplaceOffer]:
    if not self.marketplace_offers:
        return None
    idx = max(0, min(self.marketplace_selected_index, len(self.marketplace_offers) - 1))
    self.marketplace_selected_index = idx
    return self.marketplace_offers[idx]
def displayed_marketplace_offer_index(self) -> int:
    if not self.marketplace_offers:
        return 0
    hovered = int(getattr(self, 'marketplace_hovered_index', -1) or -1)
    if 0 <= hovered < len(self.marketplace_offers):
        return hovered
    idx = max(0, min(self.marketplace_selected_index, len(self.marketplace_offers) - 1))
    self.marketplace_selected_index = idx
    return idx
def displayed_marketplace_offer(self) -> Optional[MarketplaceOffer]:
    if not self.marketplace_offers:
        return None
    return self.marketplace_offers[self.displayed_marketplace_offer_index()]
def select_marketplace_offer(self, index: int) -> None:
    self.marketplace_selected_index = max(0, min(index, max(0, len(self.marketplace_offers) - 1)))
    self.marketplace_hovered_index = -1
def hover_marketplace_offer(self, index: int) -> None:
    if not self.marketplace_offers:
        self.marketplace_hovered_index = -1
        return
    self.marketplace_hovered_index = max(0, min(index, len(self.marketplace_offers) - 1))
def clear_marketplace_hover(self) -> None:
    self.marketplace_hovered_index = -1
def buy_marketplace_offer(self, offer_index: int) -> None:
    if self.player is None or offer_index < 0 or offer_index >= len(self.marketplace_offers):
        return
    offer = self.marketplace_offers[offer_index]
    self.marketplace_selected_index = offer_index
    self.marketplace_hovered_index = -1
    if offer.sold:
        self.add_log('That stall is sold out until the next level-based reroll.', 'warning')
        return
    if self.player.gold < offer.price:
        self.add_log(f'You need {offer.price} gold to buy {offer.item.summary()}.', 'warning')
        return
    self.player.gold -= offer.price
    self.player.inventory.append(offer.item)
    offer.sold = True
    self.add_log(f'Purchased {offer.item.summary()} for {offer.price} gold.', 'success')
    self.sync_active_slot()
SessionState._set_arena_transition = _set_arena_transition
SessionState.arena_target_level = arena_target_level
SessionState.arena_display_monster = arena_display_monster
SessionState.log_status = log_status
SessionState.rest_async = rest_async
SessionState._animate_monster_page_turn_async = _animate_monster_page_turn_async
SessionState.queue_arena_encounter_async = queue_arena_encounter_async
SessionState._run_arena_combat_async = _run_arena_combat_async
SessionState._finish_arena_fight_async = _finish_arena_fight_async
SessionState.add_log = add_log
SessionState.start_game = start_game
SessionState.spawn_monster = spawn_monster
SessionState.rest = rest
SessionState.fight = fight
SessionState.equip_item = equip_item
SessionState.sell_item = sell_item
SessionState.allocate = allocate
SessionState.allocate_multiple = allocate_multiple
SessionState.export_save = export_save
SessionState.ensure_marketplace_offers = ensure_marketplace_offers
SessionState.get_next_marketplace_reroll_level = get_next_marketplace_reroll_level
SessionState.selected_marketplace_offer = selected_marketplace_offer
SessionState.displayed_marketplace_offer_index = displayed_marketplace_offer_index
SessionState.displayed_marketplace_offer = displayed_marketplace_offer
SessionState.select_marketplace_offer = select_marketplace_offer
SessionState.hover_marketplace_offer = hover_marketplace_offer
SessionState.clear_marketplace_hover = clear_marketplace_hover
SessionState.buy_marketplace_offer = buy_marketplace_offer
SessionState.get_transmute_item_refs = get_transmute_item_refs
SessionState.format_transmute_choice = format_transmute_choice
SessionState.transmute_items_match = transmute_items_match
SessionState.transmute_item_map = transmute_item_map
SessionState.available_transmute_first_labels = available_transmute_first_labels
SessionState.available_transmute_second_labels = available_transmute_second_labels
SessionState.sync_transmute_selection = sync_transmute_selection
SessionState.selected_transmute_refs = selected_transmute_refs
SessionState.ensure_transmute_scene_state = ensure_transmute_scene_state
SessionState.transmute_selected = transmute_selected
SessionState.toggle_class_compendium = toggle_class_compendium
SessionState.ensure_well_scene_state = ensure_well_scene_state
SessionState.well_status_text = well_status_text
SessionState.arena_monster_uri = arena_monster_uri
SessionState.set_current_arena_monster_art = set_current_arena_monster_art
SessionState.clear_arena_monster_art = clear_arena_monster_art
SessionState.current_xp_multiplier = current_xp_multiplier
SessionState.passive_regen_tick = passive_regen_tick
SessionState.queue_well_encounter_async = queue_well_encounter_async
SessionState.ensure_inn_scene_state = ensure_inn_scene_state
SessionState.inn_status_text = inn_status_text
SessionState.inn_rest = inn_rest
SessionState.store_vault_item = store_vault_item
SessionState.withdraw_vault_item = withdraw_vault_item
SessionState.current_run_elapsed_seconds = current_run_elapsed_seconds
SessionState.ensure_ladder_scene_state = ensure_ladder_scene_state
SessionState.ladder_totals_text = ladder_totals_text
SessionState.ladder_fastest_rows = ladder_fastest_rows
SessionState.ladder_table_rows = ladder_table_rows
SessionState.glossary_lines = glossary_lines
SessionState.normalize_inventory_state = normalize_inventory_state
SessionState.reset_inventory_filters = reset_inventory_filters
SessionState.inventory_entries = inventory_entries
SessionState.inventory_selection_token = inventory_selection_token
SessionState.selected_inventory_entry = selected_inventory_entry
SessionState.select_inventory_entry = select_inventory_entry
SessionState.equip_saved_item = equip_saved_item
SessionState.save_selected_item_to_set = save_selected_item_to_set
SessionState.retrieve_saved_item_to_inventory = retrieve_saved_item_to_inventory
SessionState.delete_inventory_item = delete_inventory_item
SessionState.delete_saved_item = delete_saved_item
SessionState.unequip_slot = unequip_slot
def rarity_badge_html(rarity: str) -> str:
    color = RARITY_COLORS.get(rarity, '#cbd5e1')
    return f'<span style="display:inline-block;padding:4px 8px;border-radius:999px;background:{color}22;border:1px solid {color}66;color:{color};font-size:12px;font-weight:700;">{rarity}</span>'
@ui.page('/')
def main_page() -> None:
    state = SessionState()
    def action_button(label: str, handler, color: Optional[str] = None) -> None:
        button = ui.button(label, on_click=handler).classes('w-full font-semibold tracking-wide rounded-xl py-3')
        if color == 'gold':
            button.classes('mq-btn-gold')
        elif color == 'green':
            button.props('color=green')
        elif color == 'orange':
            button.props('color=orange')
    inventory_dialog = ui.dialog().props('persistent')
    class_select_warning_dialog = ui.dialog()


    def render_inventory_panel(player: Player, popup: bool = False) -> None:
        state.normalize_inventory_state()

        def current_inventory_state() -> Dict[str, object]:
            state.normalize_inventory_state()
            try:
                entries = state.inventory_entries()
            except Exception:
                state.reset_inventory_filters()
                state.normalize_inventory_state()
                entries = state.inventory_entries()

            selected_entry: Optional[Tuple[str, object, Item]] = None
            if entries:
                try:
                    selected_entry = state.selected_inventory_entry()
                except Exception:
                    state.selected_inventory_key = ''
                    state.selected_inventory_source = 'inventory'
                    selected_entry = None
                if selected_entry is None:
                    source, key, item = entries[0]
                    state.select_inventory_entry(source, key)
                    selected_entry = (source, key, item)
            else:
                state.selected_inventory_key = ''
                state.hovered_inventory_key = ''

            preview_entry = None
            hovered_token = getattr(state, 'hovered_inventory_key', '')
            if hovered_token:
                for source, key, item in entries:
                    if state.inventory_selection_token(source, key) == hovered_token:
                        preview_entry = (source, key, item)
                        break
                if preview_entry is None:
                    state.hovered_inventory_key = ''

            selected_item = selected_entry[2] if selected_entry else None
            comparison_source_item = preview_entry[2] if preview_entry else selected_item
            selected_slot = getattr(comparison_source_item, 'slot', '') if comparison_source_item is not None else ''
            comparison_item = player.equipped.get(selected_slot) if selected_slot else None
            inventory_mode = state.inventory_view == 'Inventory'
            has_selected_inventory_item = selected_entry is not None and selected_entry[0] == 'inventory'
            has_selected_saved_item = selected_entry is not None and selected_entry[0] == 'saved'
            return {
                'entries': entries,
                'selected_entry': selected_entry,
                'preview_entry': preview_entry,
                'selected_item': selected_item,
                'comparison_item': comparison_item,
                'selected_slot': selected_slot,
                'inventory_mode': inventory_mode,
                'has_selected_inventory_item': has_selected_inventory_item,
                'has_selected_saved_item': has_selected_saved_item,
            }

        def remember_manifest_scroll() -> None:
            ui.run_javascript("window.mqRememberScroll && window.mqRememberScroll('mq-pack-manifest-scroll')")

        def restore_manifest_scroll() -> None:
            ui.run_javascript("window.mqBindScrollMemory && window.mqBindScrollMemory('mq-pack-manifest-scroll'); window.mqRestoreScroll && window.mqRestoreScroll('mq-pack-manifest-scroll')")

        refresh_manifest = None
        refresh_detail = None
        refresh_top = None
        refresh_actions = None

        def refresh_inventory_views(*, preserve_scroll: bool = True, refresh_manifest_view: bool = True) -> None:
            if preserve_scroll:
                remember_manifest_scroll()
            if refresh_manifest_view and refresh_manifest is not None:
                refresh_manifest.refresh()
            if refresh_top is not None:
                refresh_top.refresh()
            if refresh_detail is not None:
                refresh_detail.refresh()
            if refresh_actions is not None:
                refresh_actions.refresh()
            if preserve_scroll:
                restore_manifest_scroll()

        def select_manifest_entry_by_position(position: int, preferred_source: Optional[str] = None) -> None:
            try:
                entries = state.inventory_entries()
            except Exception:
                entries = []
            if preferred_source:
                source_entries = [entry for entry in entries if entry[0] == preferred_source]
            else:
                source_entries = list(entries)
            target_entries = source_entries if source_entries else entries
            if not target_entries:
                state.selected_inventory_key = ''
                state.hovered_inventory_key = ''
                return
            target_index = max(0, min(int(position), len(target_entries) - 1))
            source, key, _item = target_entries[target_index]
            state.select_inventory_entry(source, key)

        def switch_inventory_view(view_name: str) -> None:
            remember_manifest_scroll()
            state.inventory_view = view_name
            state.selected_inventory_source = 'inventory' if view_name == 'Inventory' else 'saved'
            state.selected_inventory_key = ''
            state.hovered_inventory_key = ''
            render.refresh()

        def reset_manifest_filters() -> None:
            remember_manifest_scroll()
            state.reset_inventory_filters()
            render.refresh()

        def require_selected_inventory() -> Optional[int]:
            view = current_inventory_state()
            entry = view['selected_entry']
            if entry is None or entry[0] != 'inventory':
                state.add_log('Select an inventory item first.', 'warning')
                refresh_inventory_views(preserve_scroll=False)
                return None
            return int(entry[1])

        def require_selected_saved() -> Optional[Tuple[str, int]]:
            view = current_inventory_state()
            entry = view['selected_entry']
            if entry is None or entry[0] != 'saved' or not isinstance(entry[1], tuple):
                state.add_log('Select a saved item first.', 'warning')
                refresh_inventory_views(preserve_scroll=False)
                return None
            slot, bucket = entry[1]
            return (str(slot), int(bucket))

        def equip_selected_inventory() -> None:
            idx = require_selected_inventory()
            if idx is None:
                return
            remember_manifest_scroll()
            state.equip_item(idx)
            state.normalize_inventory_state()
            refresh_inventory_views()

        def sell_selected_inventory() -> None:
            idx = require_selected_inventory()
            if idx is None:
                return
            view = current_inventory_state()
            entries = list(view['entries'])
            selected_position = 0
            selected_entry = view.get('selected_entry')
            if selected_entry is not None:
                for pos, entry in enumerate(entries):
                    if entry[0] == selected_entry[0] and entry[1] == selected_entry[1]:
                        selected_position = pos
                        break
            remember_manifest_scroll()
            state.sell_item(idx)
            state.normalize_inventory_state()
            select_manifest_entry_by_position(selected_position, preferred_source='inventory')
            refresh_inventory_views()

        def delete_selected_inventory() -> None:
            idx = require_selected_inventory()
            if idx is None:
                return
            view = current_inventory_state()
            entries = list(view['entries'])
            selected_position = 0
            selected_entry = view.get('selected_entry')
            if selected_entry is not None:
                for pos, entry in enumerate(entries):
                    if entry[0] == selected_entry[0] and entry[1] == selected_entry[1]:
                        selected_position = pos
                        break
            remember_manifest_scroll()
            state.delete_inventory_item(idx)
            state.normalize_inventory_state()
            select_manifest_entry_by_position(selected_position, preferred_source='inventory')
            refresh_inventory_views()

        def save_selected_inventory() -> None:
            idx = require_selected_inventory()
            if idx is None:
                return
            view = current_inventory_state()
            entries = list(view['entries'])
            selected_position = 0
            selected_entry = view.get('selected_entry')
            if selected_entry is not None:
                for pos, entry in enumerate(entries):
                    if entry[0] == selected_entry[0] and entry[1] == selected_entry[1]:
                        selected_position = pos
                        break
            remember_manifest_scroll()
            state.save_selected_item_to_set(idx)
            state.normalize_inventory_state()
            select_manifest_entry_by_position(selected_position, preferred_source='inventory')
            refresh_inventory_views()

        def equip_selected_saved() -> None:
            ref = require_selected_saved()
            if ref is None:
                return
            remember_manifest_scroll()
            slot, bucket = ref
            state.equip_saved_item(slot, bucket)
            state.normalize_inventory_state()
            render.refresh()

        def restore_selected_saved() -> None:
            ref = require_selected_saved()
            if ref is None:
                return
            remember_manifest_scroll()
            slot, bucket = ref
            state.retrieve_saved_item_to_inventory(slot, bucket)
            state.normalize_inventory_state()
            render.refresh()

        def delete_selected_saved() -> None:
            ref = require_selected_saved()
            if ref is None:
                return
            remember_manifest_scroll()
            slot, bucket = ref
            state.delete_saved_item(slot, bucket)
            state.normalize_inventory_state()
            render.refresh()

        def render_manifest_entry(source: str, key: object, item: Item) -> None:
            token = state.inventory_selection_token(source, key)
            is_selected = token == state.selected_inventory_key
            is_preview = token == getattr(state, 'hovered_inventory_key', '')
            row_classes = 'mq-item-card selected' if is_selected else ('mq-item-card previewing' if is_preview else 'mq-item-card')
            card = ui.card().classes(f'{row_classes} w-full p-3').style(rarity_edge_style(item))

            def select_entry() -> None:
                state.select_inventory_entry(source, key)
                refresh_inventory_views()

            def start_preview() -> None:
                token_value = state.inventory_selection_token(source, key)
                if getattr(state, 'hovered_inventory_key', '') == token_value:
                    return
                state.hovered_inventory_key = token_value
                refresh_inventory_views(refresh_manifest_view=False)

            def clear_preview() -> None:
                if not getattr(state, 'hovered_inventory_key', ''):
                    return
                state.hovered_inventory_key = ''
                refresh_inventory_views(refresh_manifest_view=False)

            card.on('click', lambda _e: select_entry())
            card.on('mouseenter', lambda _e: start_preview())
            card.on('mouseleave', lambda _e: clear_preview())
            with card:
                with ui.row().classes('w-full items-start justify-between gap-3 max-[900px]:flex-wrap'):
                    with ui.column().classes('gap-1 flex-grow'):
                        ui.html(safe_rarity_badge_html(item))
                        ui.label(safe_item_name(item)).classes('mq-inv-entry-title')
                        ui.html(f"<div class='mq-inv-entry-sub'><span class='mq-inv-label-accent'>{html.escape(str(getattr(item, 'subtype', '') or item.slot.title()))}</span> • <span class='mq-inv-label-tier'>Tier {item_required_level(item)}</span></div>")
                        ui.label(safe_item_base_stat_text(item)).classes('mq-inv-entry-base')
                        ui.label(safe_item_affix_preview_text(item)).classes('mq-inv-entry-affix')
                    with ui.column().classes('items-end gap-2 max-[900px]:items-start'):
                        ui.html(f"<div class='mq-inv-meta'><span class='mq-inv-label-gold'>Sell</span> {safe_item_sell_value(item)}g</div>")
                        if is_selected:
                            ui.html("<span class='mq-manifest-flag selected'>Selected</span>")
                        elif is_preview:
                            ui.html("<span class='mq-manifest-flag preview'>Preview</span>")

        def render_item_pane(title: str, item: Optional[Item], empty_text: str) -> None:
            with ui.card().classes('mq-card w-full p-2 h-full'):
                ui.label(title).classes('mq-inv-section-title mb-2')
                if item is None:
                    ui.label(empty_text).classes('mq-inv-empty')
                    return
                ui.label(safe_item_name(item)).classes('mq-inv-section-title mt-1')
                with ui.row().classes('gap-2 mt-1 flex-wrap'):
                    ui.label(f'Tier {item_required_level(item)}').classes('mq-inv-pill tier')
                    ui.label(f'Sell {safe_item_sell_value(item)}g').classes('mq-inv-pill sell')
                    category = get_saved_item_category(item)
                    if category is not None:
                        ui.label(f'Set {SAVED_ITEM_SET_LABELS[category]}').classes('mq-inv-pill set')
                ui.separator().classes('my-1 opacity-20')
                ui.label('Base Profile').classes('mq-inv-block-title mb-2')
                ui.html(inventory_base_detail_html(item))
                ui.separator().classes('my-1 opacity-20')
                ui.label('Affixes').classes('mq-inv-block-title mb-2')
                ui.html(inventory_affix_detail_html(item))

        with ui.column().classes('w-full gap-4'):
            with ui.card().classes('mq-card w-full p-5'):
                with ui.row().classes('w-full items-start justify-between gap-4 max-[1100px]:flex-wrap'):
                    with ui.column().classes('gap-1 flex-grow'):
                        ui.label('Inventory & Equipment').classes('mq-inv-title')
                        
                    with ui.row().classes('gap-2 flex-wrap'):
                        inventory_view_btn = ui.button('Inventory', on_click=lambda: switch_inventory_view('Inventory')).classes('rounded-lg')
                        saved_view_btn = ui.button('Saved Sets', on_click=lambda: switch_inventory_view('Saved Sets')).classes('rounded-lg')
                        reset_btn = ui.button('Reset Filters', on_click=reset_manifest_filters).classes('rounded-lg')
                        if state.inventory_view == 'Inventory':
                            inventory_view_btn.classes('mq-btn-gold')
                        else:
                            saved_view_btn.classes('mq-btn-gold')

                @ui.refreshable
                def render_inventory_top_summary() -> None:
                    view = current_inventory_state()
                    entries = view['entries']
                    selected_item = view['selected_item']
                    with ui.row().classes('w-full gap-4 mt-4 max-[1200px]:flex-wrap'):
                        with ui.card().classes('mq-panel-frame p-4 flex-1 min-w-[260px]'):
                            ui.label('EQUIPPED GEAR').classes('mq-panel-caption')
                            ui.html(f"<div class='mq-inv-summary-line mt-2'><span class='mq-inv-label-accent'>Weapon</span>: <span class='mq-inv-summary-strong'>{html.escape(safe_item_summary(player.equipped.get('weapon'), 'Empty'))}</span></div>")
                            ui.html(f"<div class='mq-inv-summary-line'><span class='mq-inv-label-accent'>Armor</span>: <span class='mq-inv-summary-strong'>{html.escape(safe_item_summary(player.equipped.get('armor'), 'Empty'))}</span></div>")
                            ui.html(f"<div class='mq-inv-summary-line'><span class='mq-inv-label-accent'>Charm</span>: <span class='mq-inv-summary-strong'>{html.escape(safe_item_summary(player.equipped.get('charm'), 'Empty'))}</span></div>")
                        with ui.card().classes('mq-panel-frame p-4 flex-1 min-w-[260px]'):
                            ui.label('PACK SPREAD').classes('mq-panel-caption')
                            ui.html(f"<div class='mq-inv-summary-line mt-2'><span class='mq-inv-label-info'>Bag Items</span> <span class='mq-inv-summary-strong'>{len(player.inventory)}</span> • <span class='mq-inv-label-gold'>Gold</span> <span class='mq-inv-summary-strong'>{player.gold}</span></div>")
                            ui.label(inventory_tier_spread_text(player.inventory)).classes('mq-inv-detail-block mt-1')
                        with ui.card().classes('mq-panel-frame p-4 flex-1 min-w-[260px]'):
                            ui.label('VIEW STATE').classes('mq-panel-caption')
                            ui.html(f"<div class='mq-inv-summary-line mt-2'><span class='mq-inv-label-info'>Mode</span> <span class='mq-inv-summary-strong'>{html.escape(state.inventory_view)}</span> • <span class='mq-inv-label-tier'>Matches</span> <span class='mq-inv-summary-strong'>{len(entries)}</span></div>")
                            ui.html(f"<div class='mq-inv-summary-line'><span class='mq-inv-label-accent'>Selected</span>: <span class='mq-inv-summary-strong'>{html.escape(safe_item_summary(selected_item, 'None'))}</span></div>")
                            ui.html(f"<div class='mq-inv-summary-line'><span class='mq-inv-label-set'>Filters</span>: <span class='mq-inv-summary-strong'>{html.escape(state.tier_filter)}</span> • <span class='mq-inv-summary-strong'>{html.escape(state.type_filter)}</span> • <span class='mq-inv-summary-strong'>{html.escape(state.attribute_filter)}</span></div>")
                render_inventory_top_summary()
                refresh_top = render_inventory_top_summary

            with ui.row().classes('w-full items-stretch gap-4 max-[1250px]:flex-wrap'):
                with ui.column().classes('w-full gap-4' if state.inventory_view == 'Saved Sets' else 'flex-[1.2] min-w-[350px] gap-4'):
                    with ui.card().classes('mq-card w-full p-4'):
                        ui.label('Pack Manifest').classes('mq-inv-section-title')
                        
                        with ui.row().classes('w-full gap-3 mt-4 flex-wrap'):
                            tier_select = ui.select([f'All tiers'] + [f'Tier {tier}' for tier in ITEM_BUCKETS], value=state.tier_filter, label='Tier')
                            tier_select.classes('min-w-[140px] flex-1')
                            tier_select.on_value_change(lambda e: (remember_manifest_scroll(), setattr(state, 'tier_filter', e.value or 'All tiers'), setattr(state, 'selected_inventory_key', ''), setattr(state, 'hovered_inventory_key', ''), render.refresh()))
                            type_select = ui.select(ITEM_TYPE_FILTER_OPTIONS, value=state.type_filter, label='Type')
                            type_select.classes('min-w-[160px] flex-1')
                            type_select.on_value_change(lambda e: (remember_manifest_scroll(), setattr(state, 'type_filter', e.value or 'All types'), setattr(state, 'selected_inventory_key', ''), setattr(state, 'hovered_inventory_key', ''), render.refresh()))
                            attribute_select = ui.select(ATTRIBUTE_FILTER_OPTIONS, value=state.attribute_filter, label='Attribute')
                            attribute_select.classes('min-w-[180px] flex-1')
                            attribute_select.on_value_change(lambda e: (remember_manifest_scroll(), setattr(state, 'attribute_filter', e.value or 'All attributes'), setattr(state, 'selected_inventory_key', ''), setattr(state, 'hovered_inventory_key', ''), render.refresh()))

                        with ui.element('div').props('id=mq-pack-manifest-scroll onscroll=window.mqRememberScroll&&window.mqRememberScroll("mq-pack-manifest-scroll")').classes('w-full mt-4 mq-pack-manifest-scroll').style('max-height: 620px; overflow-y: auto; padding-right: 6px;'):
                            @ui.refreshable
                            def render_inventory_manifest_entries() -> None:
                                view = current_inventory_state()
                                entries = view['entries']
                                inventory_mode = view['inventory_mode']
                                if not entries:
                                    empty_text = 'No items match the current filter.' if inventory_mode else 'No saved items match the current filter.'
                                    with ui.card().classes('mq-item-card w-full p-4'):
                                        ui.label(empty_text).classes('mq-inv-empty')
                                elif inventory_mode:
                                    with ui.column().classes('w-full gap-2'):
                                        for source, key, item in entries:
                                            render_manifest_entry(source, key, item)
                                else:
                                    search = state.inventory_search.strip().lower()
                                    attribute_key = ATTRIBUTE_FILTER_KEY_BY_LABEL.get(state.attribute_filter)
                                    visible_slots = SAVED_ITEM_SET_ORDER if state.type_filter == 'All types' else [slot for slot in SAVED_ITEM_SET_ORDER if SAVED_ITEM_SET_LABELS.get(slot) == state.type_filter]
                                    if state.tier_filter == 'All tiers':
                                        visible_buckets = list(sorted(ITEM_BUCKETS, reverse=True))
                                    else:
                                        try:
                                            visible_buckets = [int(state.tier_filter.replace('Tier', '').strip())]
                                        except Exception:
                                            visible_buckets = list(sorted(ITEM_BUCKETS, reverse=True))

                                    def saved_item_matches_filters(category_name: str, bucket_value: int, raw_item: Optional[Item]) -> bool:
                                        if raw_item is None:
                                            return False
                                        item = coerce_item(raw_item)
                                        if item is None:
                                            return False
                                        if attribute_key and not item_matches_attribute(item, attribute_key):
                                            return False
                                        if search:
                                            haystack = f"{safe_item_name(item)} {safe_item_summary(item)} {safe_item_short_stat_text(item)} {getattr(item, 'rarity', '')} {getattr(item, 'subtype', '')} {category_name} {SAVED_ITEM_SET_LABELS.get(category_name, category_name)}".lower()
                                            if search not in haystack:
                                                return False
                                        return True

                                    shown_any = False
                                    with ui.column().classes('w-full gap-3'):
                                        for slot in visible_slots:
                                            with ui.card().classes('mq-saved-type-header p-3'):
                                                ui.label(SAVED_ITEM_SET_LABELS[slot]).classes('mq-inv-section-title')
                                                ui.label('Saved benchmarks by tier bucket.').classes('mq-inv-meta mt-1')
                                            slot_items = state.saved_item_sets.get(slot, {}) if isinstance(state.saved_item_sets.get(slot, {}), dict) else {}
                                            for bucket in visible_buckets:
                                                raw_item = slot_items.get(bucket)
                                                item = coerce_item(raw_item) if raw_item is not None else None
                                                if raw_item is not None and item is None:
                                                    state.saved_item_sets.get(slot, {}).pop(bucket, None)
                                                if item is not None and saved_item_matches_filters(slot, bucket, item):
                                                    shown_any = True
                                                    render_manifest_entry('saved', (slot, bucket), item)
                                                elif raw_item is None and not search and attribute_key is None:
                                                    shown_any = True
                                                    with ui.card().classes('mq-saved-placeholder w-full p-3'):
                                                        ui.html(f"<div class='mq-saved-placeholder-title'><span class='mq-inv-label-accent'>{html.escape(SAVED_ITEM_SET_LABELS[slot])}</span> • <span class='mq-inv-label-tier'>Tier {bucket}</span></div>")
                                                        ui.label('No saved item for this type and tier yet.').classes('mq-saved-placeholder-sub mt-1')
                                    if not shown_any:
                                        with ui.card().classes('mq-item-card w-full p-4'):
                                            ui.label('No saved items match the current filter.').classes('mq-inv-empty')
                            render_inventory_manifest_entries()
                            refresh_manifest = render_inventory_manifest_entries

                if state.inventory_view == 'Inventory':
                    @ui.refreshable
                    def render_inventory_detail_columns() -> None:
                        view = current_inventory_state()
                        selected_item = view['selected_item']
                        comparison_item = view['comparison_item']
                        selected_slot = view['selected_slot']
                        with ui.column().classes('flex-1 min-w-[320px] gap-3'):
                            render_item_pane('Selected Item', selected_item, 'No item selected.')
                        with ui.column().classes('flex-1 min-w-[320px] gap-3'):
                            comparison_empty = 'No item selected.' if not selected_slot else 'No item equipped in that slot.'
                            render_item_pane('Equipped Comparison', comparison_item, comparison_empty)
                    render_inventory_detail_columns()
                    refresh_detail = render_inventory_detail_columns

            @ui.refreshable
            def render_inventory_action_bar() -> None:
                view = current_inventory_state()
                inventory_mode = view['inventory_mode']
                has_selected_inventory_item = view['has_selected_inventory_item']
                has_selected_saved_item = view['has_selected_saved_item']
                with ui.card().classes('mq-card w-full p-4'):
                    ui.label('Action Bar').classes('mq-inv-section-title')
                    with ui.row().classes('w-full gap-2 mt-4 flex-wrap'):
                        equip_selected_btn = ui.button('Equip Selected', on_click=equip_selected_inventory).classes('mq-btn-gold rounded-lg')
                        sell_selected_btn = ui.button('Sell Selected', on_click=sell_selected_inventory).props('color=orange').classes('rounded-lg')
                        delete_selected_btn = ui.button('Delete Selected', on_click=delete_selected_inventory).props('color=red').classes('rounded-lg')
                        save_selected_btn = ui.button('Save Selected', on_click=save_selected_inventory).classes('rounded-lg')
                        equip_saved_btn = ui.button('Equip Saved', on_click=equip_selected_saved).classes('mq-btn-gold rounded-lg')
                        restore_saved_btn = ui.button('Restore Saved', on_click=restore_selected_saved).classes('rounded-lg')
                        delete_saved_btn = ui.button('Delete Saved', on_click=delete_selected_saved).props('color=red').classes('rounded-lg')
                        close_btn = ui.button('Close', on_click=lambda: (inventory_dialog.close() if popup else close_inventory_scene(), render.refresh())).classes('rounded-lg')

                        if state.fight_in_progress or not inventory_mode or not has_selected_inventory_item:
                            equip_selected_btn.disable()
                            sell_selected_btn.disable()
                            delete_selected_btn.disable()
                            save_selected_btn.disable()
                        if state.fight_in_progress or inventory_mode or not has_selected_saved_item:
                            equip_saved_btn.disable()
                            restore_saved_btn.disable()
                            delete_saved_btn.disable()
            render_inventory_action_bar()
            refresh_actions = render_inventory_action_bar

        restore_manifest_scroll()
    with inventory_dialog:
        @ui.refreshable
        def render_inventory_dialog() -> None:
            current_player = state.player
            with ui.card().classes('mq-inventory-popup-card'):
                if current_player is None:
                    ui.label('No active run is open.').classes('text-xl font-semibold text-slate-100')
                    ui.label('Open a chronicle slot to use the inventory window.').classes('text-slate-300 mt-2')
                    ui.button('Close', on_click=lambda: inventory_dialog.close()).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold mt-4')
                else:
                    render_inventory_panel(current_player, popup=True)


    marketplace_purchase_dialog = ui.dialog()
    with marketplace_purchase_dialog:
        @ui.refreshable
        def render_marketplace_purchase_dialog() -> None:
            pending_index = int(getattr(state, 'marketplace_pending_purchase_index', -1) or -1)
            offer = state.marketplace_offers[pending_index] if 0 <= pending_index < len(state.marketplace_offers) else None
            with ui.card().classes('mq-card max-w-[620px] w-[92vw] p-5'):
                ui.label('Buy This Offer?').classes('text-2xl font-semibold text-slate-100')
                if offer is None or state.player is None:
                    ui.label('No marketplace offer is currently selected for purchase.').classes('text-slate-300 mt-2')
                    ui.button('Close', on_click=lambda: (setattr(state, 'marketplace_pending_purchase_index', -1), marketplace_purchase_dialog.close())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold mt-4')
                else:
                    required_level = item_required_level(offer.item)
                    can_equip_now = state.player.level >= required_level
                    ui.label(offer.item.summary()).classes('text-slate-100 text-lg mt-2')
                    ui.label(offer.item.short_stat_text()).classes('text-slate-300 leading-6 mt-2')
                    ui.label(f'Required level: {required_level}. ' + ('You can equip it now.' if can_equip_now else 'You can still buy it now and bank it in inventory for later.')).classes('text-amber-300 text-sm mt-2')
                    ui.label(f'Price: {offer.price} gold').classes('text-slate-100 font-semibold mt-2')
                    with ui.row().classes('gap-3 mt-5 justify-end max-[640px]:w-full max-[640px]:flex-wrap'):
                        ui.button('Cancel', on_click=lambda: (setattr(state, 'marketplace_pending_purchase_index', -1), marketplace_purchase_dialog.close())).classes('mq-arena-btn secondary max-[640px]:w-full')
                        ui.button('Confirm Purchase', on_click=lambda: (state.buy_marketplace_offer(state.marketplace_pending_purchase_index), setattr(state, 'marketplace_pending_purchase_index', -1), marketplace_purchase_dialog.close(), render.refresh())).classes('mq-arena-btn max-[640px]:w-full')

    inn_vault_dialog = ui.dialog().props('persistent')

    def sync_inn_vault_selection() -> None:
        if state.player is None:
            state.inn_vault_inventory_selected_index = -1
            state.inn_vault_selected_index = -1
            return
        inv_len = len(state.player.inventory)
        vault_len = len(state.vault_items)
        state.inn_vault_inventory_selected_index = max(-1, min(int(getattr(state, 'inn_vault_inventory_selected_index', -1) or -1), inv_len - 1)) if inv_len else -1
        state.inn_vault_selected_index = max(-1, min(int(getattr(state, 'inn_vault_selected_index', -1) or -1), vault_len - 1)) if vault_len else -1

    def refresh_inn_vault_views() -> None:
        sync_inn_vault_selection()
        render_inn_vault_dialog.refresh()

    def open_inn_vault_dialog() -> None:
        sync_inn_vault_selection()
        render_inn_vault_dialog.refresh()
        inn_vault_dialog.open()

    def store_selected_inn_vault_item() -> None:
        if state.player is None:
            return
        sync_inn_vault_selection()
        idx = int(getattr(state, 'inn_vault_inventory_selected_index', -1) or -1)
        if idx < 0:
            state.add_log('Select an inventory item to store.', 'warning')
            render.refresh()
            refresh_inn_vault_views()
            return
        state.store_vault_item(idx)
        state.inn_vault_inventory_selected_index = idx
        state.inn_vault_selected_index = -1
        render.refresh()
        refresh_inn_vault_views()

    def withdraw_selected_inn_vault_item() -> None:
        if state.player is None:
            return
        sync_inn_vault_selection()
        idx = int(getattr(state, 'inn_vault_selected_index', -1) or -1)
        if idx < 0:
            state.add_log('Select a vault item to withdraw.', 'warning')
            render.refresh()
            refresh_inn_vault_views()
            return
        state.withdraw_vault_item(idx)
        state.inn_vault_selected_index = idx
        render.refresh()
        refresh_inn_vault_views()

    def select_inn_vault_inventory(index: int) -> None:
        state.inn_vault_inventory_selected_index = int(index)
        state.inn_vault_selected_index = -1
        refresh_inn_vault_views()

    def select_inn_vault_item(index: int) -> None:
        state.inn_vault_selected_index = int(index)
        state.inn_vault_inventory_selected_index = -1
        refresh_inn_vault_views()

    with inn_vault_dialog:
        @ui.refreshable
        def render_inn_vault_dialog() -> None:
            sync_inn_vault_selection()
            selected_inv = int(getattr(state, 'inn_vault_inventory_selected_index', -1) or -1)
            selected_vault = int(getattr(state, 'inn_vault_selected_index', -1) or -1)
            with ui.card().classes('mq-card max-w-[1380px] w-[96vw] p-5'):
                ui.label('Inn Vault').classes('mq-inv-title')
                if state.player is None:
                    ui.label('No active adventurer is available.').classes('mq-inv-empty mt-3')
                    ui.button('Close', on_click=inn_vault_dialog.close).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold mt-4')
                    return
                ui.label('Store Selected costs 5 gold. Withdraw Selected is free. Vault capacity: 20 items.').classes('text-slate-300 text-base leading-7 mt-2')
                with ui.row().classes('w-full items-stretch gap-4 mt-4 no-wrap max-[1180px]:flex-wrap'):
                    with ui.card().classes('mq-card flex-1 min-w-[340px] p-4'):
                        ui.label(f'Inventory ({len(state.player.inventory)})').classes('mq-inv-section-title mb-3')
                        with ui.element('div').classes('w-full').style('max-height: 520px; overflow-y: auto; padding-right: 6px;'):
                            if not state.player.inventory:
                                ui.label('No inventory items to store.').classes('mq-inv-empty')
                            else:
                                with ui.column().classes('w-full gap-2'):
                                    for idx, item in enumerate(state.player.inventory):
                                        selected = idx == selected_inv
                                        card = ui.card().classes(f"{'mq-item-card selected' if selected else 'mq-item-card'} w-full p-3").style(rarity_edge_style(item))
                                        card.on('click', lambda _e, i=idx: select_inn_vault_inventory(i))
                                        with card:
                                            with ui.row().classes('w-full items-start justify-between gap-3 max-[860px]:flex-wrap'):
                                                with ui.column().classes('gap-1 flex-grow'):
                                                    ui.html(safe_rarity_badge_html(item))
                                                    ui.label(safe_item_name(item)).classes('mq-inv-entry-title')
                                                    ui.label(safe_item_base_stat_text(item)).classes('mq-inv-entry-base')
                                                    ui.label(safe_item_affix_preview_text(item)).classes('mq-inv-entry-affix')
                                                if selected:
                                                    ui.html("<span class='mq-manifest-flag selected'>Selected</span>")
                    with ui.column().classes('w-full max-w-[260px] gap-4 items-stretch justify-center'):
                        with ui.card().classes('mq-card p-4'):
                            ui.label('Vault Actions').classes('mq-inv-section-title mb-3 text-center')
                            ui.button('Store Selected (5 Gold)', on_click=store_selected_inn_vault_item).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold w-full')
                            ui.button('Withdraw Selected', on_click=withdraw_selected_inn_vault_item).classes('rounded-xl px-5 py-3 font-semibold w-full mt-3')
                            ui.button('Close', on_click=inn_vault_dialog.close).classes('rounded-xl px-5 py-3 font-semibold w-full mt-3')
                            ui.separator().classes('my-4 opacity-20')
                            ui.label(f'Gold {state.player.gold}').classes('mq-detail-text text-center')
                            ui.label(f'Vault {len(state.vault_items)}/20').classes('mq-detail-text text-center')
                    with ui.card().classes('mq-card flex-1 min-w-[340px] p-4'):
                        ui.label(f'Vault Storage ({len(state.vault_items)}/20)').classes('mq-inv-section-title mb-3')
                        with ui.element('div').classes('w-full').style('max-height: 520px; overflow-y: auto; padding-right: 6px;'):
                            if not state.vault_items:
                                ui.label('The vault is empty.').classes('mq-inv-empty')
                            else:
                                with ui.column().classes('w-full gap-2'):
                                    for idx, item in enumerate(state.vault_items):
                                        selected = idx == selected_vault
                                        card = ui.card().classes(f"{'mq-item-card selected' if selected else 'mq-item-card'} w-full p-3").style(rarity_edge_style(item))
                                        card.on('click', lambda _e, i=idx: select_inn_vault_item(i))
                                        with card:
                                            with ui.row().classes('w-full items-start justify-between gap-3 max-[860px]:flex-wrap'):
                                                with ui.column().classes('gap-1 flex-grow'):
                                                    ui.html(safe_rarity_badge_html(item))
                                                    ui.label(safe_item_name(item)).classes('mq-inv-entry-title')
                                                    ui.label(safe_item_base_stat_text(item)).classes('mq-inv-entry-base')
                                                    ui.label(safe_item_affix_preview_text(item)).classes('mq-inv-entry-affix')
                                                if selected:
                                                    ui.html("<span class='mq-manifest-flag selected'>Selected</span>")

    with class_select_warning_dialog:
        with ui.card().classes('mq-card max-w-[520px] w-[92vw] p-5'):
            ui.label('Return to Character Selection?').classes('text-2xl font-semibold text-slate-100')
            ui.label('Warning: going back to character selection will reset your current hero and end the active run in this slot.').classes('text-slate-300 leading-7 mt-2')
            ui.label('Your shared stash progress remains, but this current adventurer will be cleared.').classes('text-amber-300 text-sm mt-2')
            with ui.row().classes('gap-3 mt-5 justify-end max-[640px]:w-full max-[640px]:flex-wrap'):
                ui.button('Cancel', on_click=lambda: class_select_warning_dialog.close()).classes('mq-arena-btn secondary max-[640px]:w-full')
                ui.button('Yes, Reset Hero', on_click=lambda: (class_select_warning_dialog.close(), state.back_to_class_select(), render.refresh())).classes('mq-arena-btn danger max-[640px]:w-full')

    def open_class_select_warning() -> None:
        class_select_warning_dialog.open()

    def open_marketplace_buy_dialog(index: int) -> None:
        state.marketplace_pending_purchase_index = int(index)
        render_marketplace_purchase_dialog.refresh()
        marketplace_purchase_dialog.open()

    def close_inventory_scene() -> None:
        if state.player is None:
            return
        state.hovered_inventory_key = ''
        if getattr(state, 'inventory_return_screen', 'game') == 'town':
            state.enter_town('You close the gear ledger and step back into town.')
        else:
            return_tab = getattr(state, 'inventory_return_tab', 'arena') or 'arena'
            state.open_game_tab(return_tab, 'You close the gear ledger and return to your previous route.')

    def open_inventory_scene(note: Optional[str] = None) -> None:
        if state.player is None:
            return
        try:
            inventory_dialog.close()
        except Exception:
            pass
        state.inventory_return_screen = state.screen
        state.inventory_return_tab = state.game_tab if state.screen == 'game' and state.game_tab != 'inventory' else 'arena'
        try:
            state.normalize_inventory_state()
        except Exception:
            state.selected_inventory_key = ''
            state.selected_inventory_source = 'inventory'
            state.hovered_inventory_key = ''
        state.inventory_view = 'Inventory'
        state.reset_inventory_filters()
        try:
            state.open_game_tab('inventory', note)
        except Exception as exc:
            state.add_log(f'Could not open inventory: {exc}', 'warning')
            state.game_tab = 'arena'
            state.screen = 'game'
        render.refresh()

    @ui.refreshable
    def render() -> None:
        if state.player is None:
            inventory_dialog.close()
        active_scene = state.screen
        if active_scene not in ('title', 'class_select', 'town'):
            active_scene = state.game_tab or 'arena'
        screen_class = state.screen.replace('_', '-')
        scene_class = active_scene.replace('_', '-')
        with ui.column().classes(f'mq-page mq-screen-{screen_class} mq-scene-{scene_class} w-full items-center px-4 py-5 md:px-6 lg:px-8'):
            if state.screen == 'title':
                with ui.row().classes('mq-shell w-full items-stretch gap-6 no-wrap max-[1200px]:flex-wrap'):
                    with ui.card().classes('mq-title-card w-full flex-1 p-4 lg:p-5'):
                        with ui.element('div').classes('mq-title-stage w-full'):
                            if TITLE_SCREEN_DATA_URI:
                                with ui.element('div').classes('mq-title-image-wrap'):
                                    ui.html(f"<img src='{html.escape(TITLE_SCREEN_DATA_URI, quote=True)}' alt='MasterQuest title art' class='mq-title-image-static' loading='eager' decoding='sync' draggable='false'>")
                            else:
                                with ui.column().classes('absolute inset-0 items-center justify-center gap-4'):
                                    ui.label('MASTERQUEST').classes('text-5xl font-bold text-slate-100 tracking-[0.18em]')
                                    ui.label('Place Title Screen.png into Assets to restore the original title art.').classes('text-slate-400')
                            ui.label('Choose a save slot to begin or resume your ascent.').classes('mq-title-caption')
                    with ui.column().classes('w-full max-w-[470px] gap-4'):
                        with ui.card().classes('mq-side-card p-5'):
                            ui.label('Chronicle Slots').classes('text-2xl font-semibold text-slate-100')
                            ui.label('The Arena’s ledger remembers each doomed climb. Choose a save slot to continue the one you trust most.').classes('text-slate-300 mt-2 leading-6')
                        for index in range(3):
                            occupied = state.slot_is_occupied(index)
                            with ui.card().classes('mq-slot-card p-4'):
                                with ui.row().classes('w-full items-center justify-between gap-3'):
                                    ui.label(f'SLOT {index + 1}').classes('mq-section-title')
                                    ui.html(
                                        f'<span class="mq-slot-badge {'mq-slot-active' if occupied else 'mq-slot-empty'}">'
                                        f"{'ACTIVE RECORD' if occupied else 'EMPTY RECORD'}"
                                        '</span>'
                                    )
                                ui.label(state.slot_summary(index)).classes('text-slate-300 text-sm whitespace-pre-line leading-6 mt-3 min-h-[88px]')
                                button_label = f'Open Slot {index + 1}'
                                button = ui.button(button_label, on_click=lambda idx=index: (state.open_slot(idx), render.refresh()))
                                button.classes('w-full font-semibold tracking-wide rounded-xl py-3 mt-3 mq-btn-gold')
                        with ui.card().classes('mq-side-card p-4'):
                            ui.label('Progress is saved into the currently open slot and now persists between quits and reloads. Save codes still work from inside the game if you want to move a hero elsewhere.').classes('text-slate-400 leading-6')
                return
            if state.screen == 'class_select':
                active_slot_text = f'Slot {((state.active_slot_index or 0) + 1)}'
                stash_line = (
                    f'Gold {state.shared_gold}   •   Inventory relics {len(state.shared_inventory)}   •   '
                    f'Vault items {len(state.vault_items)}   •   Pity bonus +{state.masterquest_pity_bonus} stat point(s)'
                )
                reroll_line = (
                    f'Current class on file: {state.selection_return_class}. You may reroll it instantly if you want a fresh run without taking MasterQuest.'
                    if state.selection_return_class
                    else 'No active run is currently waiting in town. Pick any unlocked class to begin a new ascent.'
                )
                with ui.column().classes('mq-selection-shell w-full gap-5'): 
                    with ui.card().classes('mq-selection-hero w-full p-4 md:p-5 lg:p-6'):
                        with ui.row().classes('w-full items-stretch gap-5 no-wrap max-[1180px]:flex-wrap'):
                            with ui.column().classes('w-full flex-[3] gap-4'):
                                ui.label('Class Selection').classes('text-3xl md:text-4xl font-semibold text-slate-100')
                                ui.label(f'{active_slot_text}  •  Choose the next face of your ascent.').classes('text-slate-300 text-base md:text-lg')
                                if state.class_select_notice:
                                    ui.html(f"<div class='mq-state-banner {'success' if 'passed' in state.class_select_notice.lower() else 'warning'}'>{html.escape(state.class_select_notice)}</div>")
                                with ui.card().classes('mq-panel-frame p-4'):
                                    ui.label('NAME & THREAD').classes('mq-panel-caption')
                                    name_input = ui.input('Character Name', value=state.pending_character_name).classes('w-full mt-2')
                                    name_input.props('outlined dense clearable maxlength=24 input-style=color: var(--mq-text-main);')
                                    def _update_character_name(e):
                                        state.pending_character_name = clean_character_name(e.value or '')
                                    name_input.on_value_change(_update_character_name)
                                    ui.label(reroll_line).classes('text-slate-300 leading-6 mt-3')
                                    ui.separator().classes('my-3 opacity-20')
                                    ui.label('SHARED STASH').classes('mq-panel-caption')
                                    ui.label(stash_line).classes('text-slate-300 leading-6 mt-1')
                                    ui.separator().classes('my-3 opacity-20')
                                    ui.label('TEST MODE').classes('mq-panel-caption')
                                    ui.label('Test Mode grants +100 all core stats, +3000% XP, +3000% Magic Find, Legendary drops, and guaranteed MasterQuest success.').classes('text-slate-400 italic leading-6 mt-1')
                                with ui.row().classes('w-full items-center justify-between gap-3 max-[800px]:flex-wrap'):
                                    with ui.row().classes('gap-2 max-[800px]:w-full'):
                                        back = ui.button('Back to Title', on_click=lambda: (state.return_to_title(), render.refresh()))
                                        back.classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[800px]:w-full')
                                        compendium = ui.button('Class Compendium', on_click=lambda: (state.toggle_class_compendium(), render.refresh()))
                                        compendium.classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[800px]:w-full')
                                        if state.selection_return_class and state.selection_return_class in state.unlocked_classes:
                                            reroll = ui.button(f'Reroll {state.selection_return_class}', on_click=lambda c=state.selection_return_class: (state.start_game(c), render.refresh()))
                                            reroll.classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[800px]:w-full')
                                    test_toggle = ui.switch('Test Mode', value=state.test_mode).props('color=amber')
                                    def _toggle_test(e):
                                        state.test_mode = bool(e.value)
                                    test_toggle.on_value_change(_toggle_test)
                            with ui.card().classes('mq-panel-frame w-full max-w-[420px] p-4 flex-[2]'):
                                ui.label('Ascension Path').classes('text-2xl font-semibold text-slate-100')
                                ui.label('UNLOCK TRACK').classes('mq-panel-caption mt-2')
                                for class_name in CLASS_ORDER:
                                    unlocked = class_name in state.unlocked_classes
                                    with ui.row().classes('w-full items-center justify-between gap-3 mt-2'):
                                        ui.label(f"{'◆' if unlocked else '◇'} {class_name}").classes('text-slate-200')
                                        ui.label('Ready' if unlocked else get_class_unlock_requirement(class_name)).classes('text-right text-sm ' + ('text-amber-300' if unlocked else 'text-slate-500'))
                                ui.separator().classes('my-3 opacity-20')
                                ui.label('RITUAL NOTE').classes('mq-panel-caption')
                                ui.label('Fighter and Mage both lead into Samurai. From there, the path tightens one class at a time until Alchemist.').classes('text-slate-400 italic leading-6 mt-1')
                    with ui.element('div').classes('mq-selection-grid w-full'):
                        selectable_classes = [player_class for player_class in CLASS_ORDER if player_class in state.unlocked_classes]
                        for player_class in selectable_classes:
                            preview = create_player(player_class)
                            unlocked = True
                            starter_weapon = preview.equipped.get('weapon')
                            starter_armor = preview.equipped.get('armor')
                            starter_charm = preview.equipped.get('charm')
                            with ui.card().classes(f'mq-selection-card p-4 {'locked' if not unlocked else ''}'):
                                hero_uri = _hero_data_uri(player_class)
                                with ui.element('div').classes('mq-hero-art-frame mq-selection-hero-bubble w-full'):
                                    if hero_uri:
                                        ui.image(hero_uri).classes('mq-hero-art')
                                    else:
                                        with ui.element('div').classes('mq-hero-art-fallback'):
                                            ui.label(f'{player_class} art missing')
                                with ui.row().classes('w-full items-start justify-between gap-3 mt-4'):
                                    with ui.column().classes('gap-1'): 
                                        ui.label(player_class).classes('text-2xl font-semibold text-slate-100')
                                        ui.label(CLASS_DESCRIPTIONS[player_class]).classes('text-slate-300 text-sm leading-6')
                                    ui.html(f'<span class="mq-path-pill {'locked' if not unlocked else ''}">{'READY' if unlocked else 'LOCKED'}</span>')
                                with ui.column().classes('w-full gap-3 mt-4'):
                                    with ui.card().classes('mq-panel-frame p-3'):
                                        ui.label('PATH').classes('mq-panel-caption')
                                        ui.label(get_class_unlock_requirement(player_class)).classes('text-slate-300 text-sm leading-6 mt-1')
                                    with ui.card().classes('mq-panel-frame p-3'):
                                        ui.label('EQUIPMENT').classes('mq-panel-caption')
                                        ui.label(format_class_equip_rules(player_class)).classes('text-slate-300 text-sm leading-6 mt-1')
                                    with ui.card().classes('mq-panel-frame p-3'):
                                        ui.label('OPENING PROFILE').classes('mq-panel-caption')
                                        ui.label(
                                            f'HP {preview.max_hp} • Mana {preview.max_mana} • Speed {preview.speed}\n'
                                            f'STR {preview.strength} • DEX {preview.dexterity} • INT {preview.intelligence} • VIT {preview.vitality}\n'
                                            f"Start: {starter_weapon.name if starter_weapon else 'None'} / {starter_armor.name if starter_armor else 'None'} / {starter_charm.name if starter_charm else 'None'}"
                                        ).classes('mq-stat-block mt-1')
                                choose = ui.button(f'Enter the ascent as {player_class}', on_click=lambda c=player_class: (state.start_game(c), render.refresh()))
                                choose.classes('w-full font-semibold tracking-wide rounded-xl py-3 mt-4 mq-btn-gold')
                                if not unlocked:
                                    choose.disable()
                    if state.class_compendium_open:
                        with ui.card().classes('mq-selection-hero w-full p-4 md:p-5 lg:p-6'):
                            with ui.row().classes('w-full items-center justify-between gap-3 mb-4 max-[800px]:flex-wrap'):
                                with ui.column().classes('gap-1'):
                                    ui.label('Class Compendium').classes('text-3xl font-semibold text-slate-100')
                                    ui.label('Every class, every unlock path, every restriction, and the opening stats you carry into a new ascent.').classes('text-slate-300 leading-6')
                                ui.button('Hide Compendium', on_click=lambda: (state.toggle_class_compendium(), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                            with ui.column().classes('w-full gap-4'):
                                for class_name in CLASS_ORDER:
                                    preview = create_player(class_name)
                                    unlocked = class_name in state.unlocked_classes
                                    weapon = preview.equipped.get('weapon')
                                    armor = preview.equipped.get('armor')
                                    charm = preview.equipped.get('charm')
                                    with ui.card().classes('mq-selection-card w-full p-4'):
                                        with ui.row().classes('w-full items-start gap-4 no-wrap max-[980px]:flex-wrap'):
                                            with ui.column().classes('w-full max-w-[230px] gap-3'):
                                                hero_uri = _hero_data_uri(class_name)
                                                with ui.element('div').classes('mq-hero-art-frame w-full'):
                                                    if hero_uri:
                                                        ui.image(hero_uri).classes('mq-hero-art')
                                                    else:
                                                        with ui.element('div').classes('mq-hero-art-fallback'):
                                                            ui.label(f'{class_name} art missing')
                                                ui.html(f"<span class='mq-path-pill {'locked' if not unlocked else ''}'>{'Unlocked' if unlocked else 'Locked'}</span>")
                                            with ui.column().classes('w-full flex-1 gap-3'):
                                                with ui.row().classes('w-full items-center justify-between gap-3 max-[700px]:flex-wrap'):
                                                    ui.label(class_name).classes('text-2xl font-semibold text-slate-100')
                                                    ui.label('Ready' if unlocked else get_class_unlock_requirement(class_name)).classes('text-sm ' + ('text-amber-300' if unlocked else 'text-slate-400'))
                                                ui.label(CLASS_DESCRIPTIONS[class_name]).classes('text-slate-300 leading-6')
                                                with ui.element('div').classes('mq-inventory-shell w-full'):
                                                    with ui.card().classes('mq-panel-frame p-4'):
                                                        ui.label('Path & Restrictions').classes('mq-panel-caption')
                                                        ui.label('UNLOCK').classes('text-slate-200 text-sm mt-3')
                                                        ui.label(get_class_unlock_requirement(class_name)).classes('mq-detail-text mt-1')
                                                        ui.label('GEAR').classes('text-slate-200 text-sm mt-3')
                                                        ui.label(format_class_equip_rules(class_name)).classes('mq-detail-text mt-1')
                                                    with ui.card().classes('mq-panel-frame p-4'):
                                                        ui.label('Starting Profile').classes('mq-panel-caption')
                                                        lines = [
                                                            f'HP {preview.max_hp}   •   Mana {preview.max_mana}   •   Speed {preview.speed}',
                                                            f'Accuracy {int(round(preview.accuracy * 100))}%   •   Crit {int(round(preview.crit_chance * 100))}%   •   Crit Dmg {preview.crit_damage:.2f}x',
                                                            f'STR {preview.strength}   •   DEX {preview.dexterity}   •   INT {preview.intelligence}   •   VIT {preview.vitality}',
                                                        ]
                                                        ui.label('\n'.join(lines)).classes('mq-detail-text mt-2')
                                                with ui.card().classes('mq-panel-frame p-4'):
                                                    ui.label('Starter Loadout').classes('mq-panel-caption')
                                                    loadout_lines = [
                                                        f'Weapon: {weapon.summary() if weapon else "None"}',
                                                        f'Armor: {armor.summary() if armor else "None"}',
                                                        f'Charm: {charm.summary() if charm else "None"}',
                                                    ]
                                                    ui.label('\n'.join(loadout_lines)).classes('mq-detail-text mt-2')
                    with ui.card().classes('mq-log p-4'):
                        ui.label('Recent Log').classes('text-lg font-semibold text-slate-100 mb-2')
                        for event in reversed(state.log[-8:]):
                            ui.label(event.text).classes('text-slate-300 text-sm leading-6')
                return
            if state.screen == 'town':
                player = state.player
                assert player is not None
                slot_label = f'Chronicle Slot {((state.active_slot_index or 0) + 1)}'
                primary = f'{player.name} the {player.player_class}  •  Level {player.level}\nGold {player.gold}  •  HP {player.hp}/{player.max_hp}  •  Mana {player.mana}/{player.max_mana}'
                class_ladder = state.ladder_stats.get(player.player_class, {})
                secondary = f'Wins {player.wins}  •  Losses {player.losses}  •  Chain x{state.monster_chain_combo}  •  Inventory {len(player.inventory)}  •  Vault {len(state.vault_items)}  •  MQ Attempts {int(class_ladder.get('masterquest_attempts', 0))}'
                hint = state.log[-1].text if state.log else 'The board is quiet for now. Pick a route below and keep the run moving.'
                with ui.column().classes('mq-town-shell w-full gap-5'):
                    with ui.card().classes('mq-town-header w-full p-5 md:p-6'):
                        with ui.row().classes('w-full items-center justify-between gap-3 max-[900px]:flex-wrap'):
                            with ui.column().classes('gap-1'):
                                ui.label('Town').classes('text-3xl md:text-4xl font-semibold text-slate-100')
                                ui.label('Choose where to travel next.').classes('text-slate-300 text-base md:text-lg')
                            with ui.row().classes('gap-2 max-[900px]:w-full'):
                                ui.button('Return to Chronicle Slots', on_click=lambda: (state.return_to_title(), render.refresh())).classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[900px]:w-full')
                                ui.button('Class Selection', on_click=open_class_select_warning).classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[900px]:w-full')
                    with ui.element('div').classes('mq-town-dashboard w-full'):
                        with ui.card().classes('mq-overview-card p-4 md:p-5'):
                            ui.label('Overview').classes('text-2xl font-semibold text-slate-100')
                            with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                ui.label('ADVENTURER').classes('mq-panel-caption')
                                ui.label(primary).classes('mq-stat-block mt-2')
                            with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                ui.label('LEDGER').classes('mq-panel-caption')
                                ui.label(secondary).classes('mq-stat-block mt-2')
                        with ui.card().classes('mq-scene-card mq-town-map-card w-full p-4'):
                            ui.label('Town Map').classes('text-2xl font-semibold text-slate-100 mb-2 text-center')
                            ui.label(slot_label).classes('mq-panel-caption mb-3 text-center')
                            with ui.element('div').classes('mq-scene-stage mq-town-scene-stage w-full'):
                                if TOWN_SCENE_DATA_URI:
                                    with ui.element('div').classes('mq-scene-image-wrap mq-town-scene-image-wrap'):
                                        ui.html(f"<img src='{html.escape(TOWN_SCENE_DATA_URI, quote=True)}' alt='Town map' class='mq-town-scene-image-static' loading='eager' decoding='sync' draggable='false'>")
                                else:
                                    with ui.element('div').classes('mq-scene-fallback w-full h-full'):
                                        for label in ['Arena', 'Marketplace', 'Transmutation', 'Ladder', 'Well of Evil', 'Inn']:
                                            ui.label(label).classes('mq-scene-fallback-pill')
                        with ui.card().classes('mq-travel-card p-4 md:p-5'):
                            ui.label('Travel Board').classes('text-2xl font-semibold text-slate-100')
                            ui.label('ROUTES').classes('mq-panel-caption mt-3')
                            with ui.element('div').classes('mq-route-grid w-full mt-4'):
                                ui.button('Arena', on_click=lambda: (state.open_game_tab('arena', 'You leave the safety of town and step into the arena.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Inventory', on_click=lambda: open_inventory_scene('You check your pack before setting out again.')).classes('mq-route-btn')
                                ui.button('Marketplace', on_click=lambda: (state.open_game_tab('marketplace', 'Lanternlight and bargaining voices drift from the fairy bazaar.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Transmutation', on_click=lambda: (state.open_game_tab('transmute', 'Brass rings hum softly as Varkesh sizes up your offerings.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Ladder', on_click=lambda: (state.open_game_tab('ladder', 'The registrar lifts the ledger and marks your place in the climb.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Well of Evil', on_click=lambda: (state.open_game_tab('well', 'You approach the cursed stones and feel the well looking back.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Inn', on_click=lambda: (state.open_game_tab('inn', 'Warm firelight spills out from the inn.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Glossary', on_click=lambda: (state.open_game_tab('glossary', 'You unseal the brass-bound ledger of systems and secrets.'), render.refresh())).classes('mq-route-btn')
                                ui.button('Class Select', on_click=open_class_select_warning).classes('mq-route-btn')
                                masterquest_town_btn = ui.button('MasterQuest', on_click=lambda: (state.complete_masterquest(), render.refresh())).classes('mq-route-btn')
                                if int(player.level) < 60:
                                    masterquest_town_btn.classes('opacity-70')
                                    masterquest_town_btn.disable()
                            ui.button('Quit to Title', on_click=lambda: (state.return_to_title(), render.refresh())).classes('mq-route-btn mq-route-quit w-full mt-4')
                        with ui.card().classes('mq-log mq-town-comm-card p-4'):
                            ui.label('Communications').classes('text-lg font-semibold text-slate-100 mb-2')
                            with ui.element('div').classes('mq-comm-bubble'):
                                ui.label(hint).classes('text-slate-300 italic leading-6 whitespace-pre-line')
                                if state.log:
                                    ui.separator().classes('my-3 opacity-20')
                                    for event in reversed(state.log[-4:]):
                                        ui.label(event.text).classes('text-slate-300 text-sm leading-6')
                return
            player = state.player
            assert player is not None
            async def handle_fight() -> None:
                await state.queue_arena_encounter_async(render.refresh)
            async def handle_rest() -> None:
                await state.rest_async(render.refresh)
            def handle_status() -> None:
                state.log_status()
                render.refresh()
            with ui.column().classes('mq-arena-shell w-full gap-4'):
                with ui.row().classes('w-full items-center justify-between gap-3 max-[900px]:flex-wrap'):
                    with ui.column().classes('gap-1'):
                        slot_label = f'Chronicle Slot {((state.active_slot_index or 0) + 1)}'
                        ui.label(slot_label).classes('mq-section-title')
                        ui.label(f'{player.player_class} • Level {player.level}').classes('text-3xl font-semibold text-slate-100')
                    with ui.row().classes('gap-2 max-[700px]:w-full'):
                        town_btn = ui.button('Return to Town', on_click=lambda: (state.enter_town('You return to town to choose your next route.'), render.refresh()))
                        town_btn.classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[700px]:w-full')
                        back_to_slots = ui.button('Return to Chronicle Slots', on_click=lambda: (state.return_to_title(), render.refresh()))
                        back_to_slots.classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[700px]:w-full')
                        reroll = ui.button('Class Selection', on_click=open_class_select_warning)
                        reroll.classes('font-semibold tracking-wide rounded-xl py-3 px-5 mq-btn-gold max-[700px]:w-full')
                if state.game_tab != 'arena':
                    if state.game_tab != 'inventory':
                        with ui.row().classes('w-full items-center gap-2 flex-wrap'):
                            arena_back = ui.button('Return to Arena', on_click=lambda: (state.open_game_tab('arena'), render.refresh()))
                            arena_back.classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                    if state.game_tab == 'inventory':
                        render_inventory_panel(player, popup=False)
                        return
                    elif state.game_tab == 'marketplace':
                        state.ensure_marketplace_offers(force_reroll=False)
                        next_reroll = state.get_next_marketplace_reroll_level()
                        next_reroll_text = f'Next shop reroll at level {next_reroll}.' if next_reroll is not None else 'You have reached the final shop reroll tier.'

                        def render_market_offer_card(index: int, offer: MarketplaceOffer) -> None:
                            sold = bool(offer.sold)
                            with ui.card().classes('mq-item-card w-full p-4').style(rarity_edge_style(offer.item)):
                                with ui.row().classes('w-full items-start gap-3 max-[860px]:flex-wrap'):
                                    with ui.element('div').classes('mq-item-icon-frame'):
                                        icon_uri = item_icon_uri(offer.item)
                                        if icon_uri:
                                            ui.image(icon_uri).classes('mq-item-icon')
                                        else:
                                            ui.label(offer.item.subtype[:2].upper() if offer.item.subtype else offer.item.slot[:2].upper()).classes('mq-item-icon-fallback')
                                    with ui.column().classes('gap-1 flex-grow'):
                                        ui.html(safe_rarity_badge_html(offer.item))
                                        ui.label(safe_item_name(offer.item)).classes('mq-inv-entry-title')
                                        ui.html(f"<div class='mq-inv-entry-sub'><span class='mq-inv-label-accent'>Offer {index + 1}</span> • <span class='mq-inv-label-tier'>Tier {item_required_level(offer.item)}</span></div>")
                                        ui.label(safe_item_base_stat_text(offer.item)).classes('mq-inv-entry-base')
                                        ui.html(inventory_affix_detail_html(offer.item))
                                    with ui.column().classes('items-end max-[860px]:items-start gap-2 min-w-[160px]'):
                                        ui.html(f"<div class='mq-inv-meta'><span class='mq-inv-label-gold'>Price</span> {offer.price}g</div>")
                                        if sold:
                                            ui.html("<span class='mq-manifest-flag selected'>Sold Out</span>")
                                        buy = ui.button('Sold Out' if sold else f'Buy Offer {index + 1}', on_click=lambda i=index: open_marketplace_buy_dialog(i))
                                        buy.classes('mq-btn-gold rounded-lg')
                                        if sold:
                                            buy.disable()

                        with ui.column().classes('w-full gap-4'):
                            with ui.card().classes('mq-card w-full p-5'):
                                ui.label('Marketplace').classes('mq-inv-title')
                                
                                ui.label(state.current_marketplace_line or 'Liora and Senna lean across the counter, already discussing which relic would look best in your hands.').classes('text-slate-100 text-xl leading-9 mt-2 italic')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('MARKET STATUS').classes('mq-panel-caption')
                                    ui.html(f"<div class='mq-inv-summary-line mt-2'><span class='mq-inv-label-gold'>Gold</span> <span class='mq-inv-summary-strong'>{player.gold}</span> • <span class='mq-inv-label-tier'>Shop Tier</span> <span class='mq-inv-summary-strong'>{state.marketplace_offer_refresh_level}</span></div>")
                                    
                            with ui.row().classes('w-full items-start gap-4 max-[1250px]:flex-wrap'):
                                with ui.column().classes('flex-[0.95] min-w-[350px] gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Bazaar Floor').classes('mq-inv-section-title mb-3')
                                        if MARKETPLACE_SCENE_DATA_URI:
                                            with ui.element('div').classes('mq-scene-stage w-full'):
                                                with ui.element('div').classes('mq-scene-image-wrap'):
                                                    ui.html(f"<img src='{html.escape(MARKETPLACE_SCENE_DATA_URI, quote=True)}' alt='Marketplace scene' class='mq-scene-image' loading='eager' decoding='sync' draggable='false'>")
                                        else:
                                            with ui.element('div').classes('mq-scene-fallback w-full h-full'):
                                                for label in ['Marketplace', 'Lanterns', 'Stalls']:
                                                    ui.label(label).classes('mq-scene-fallback-pill')
                                with ui.column().classes('flex-1 min-w-[380px] gap-3'):
                                    @ui.refreshable
                                    def render_marketplace_offer_list() -> None:
                                        with ui.card().classes('mq-card w-full p-4'):
                                            ui.label('Curated Offers').classes('mq-inv-section-title')
                                            
                                            with ui.column().classes('w-full gap-3'):
                                                for index, offer in enumerate(state.marketplace_offers):
                                                    render_market_offer_card(index, offer)
                                        with ui.card().classes('mq-card w-full p-4'):
                                            ui.label('Routes').classes('mq-inv-section-title mb-3')
                                            with ui.row().classes('gap-2 flex-wrap'):
                                                ui.button('Return to Arena', on_click=lambda: (state.open_game_tab('arena'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                                ui.button('Return to Town', on_click=lambda: (state.enter_town('You leave the fairy stall behind and return to the town square.'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                    render_marketplace_offer_list()
                            return
                    elif state.game_tab == 'transmute':
                        state.ensure_transmute_scene_state(False)
                        first_ref, second_ref = state.selected_transmute_refs()
                        first_item = first_ref[2] if first_ref else None
                        second_item = second_ref[2] if second_ref else None
                        item_map = state.transmute_item_map()
                        first_options = state.available_transmute_first_labels()
                        second_options = state.available_transmute_second_labels()
                        lower_item = None
                        higher_item = None
                        upgrade_rarity = same_rarity = downgrade_rarity = None
                        if first_item is not None and second_item is not None and state.transmute_items_match(first_item, second_item):
                            lower_item = first_item if RARITY_ORDER.index(first_item.rarity) <= RARITY_ORDER.index(second_item.rarity) else second_item
                            higher_item = first_item if RARITY_ORDER.index(first_item.rarity) >= RARITY_ORDER.index(second_item.rarity) else second_item
                            upgrade_rarity = shift_rarity(lower_item.rarity, 1)
                            same_rarity = higher_item.rarity
                            downgrade_rarity = shift_rarity(higher_item.rarity, -1)
                        with ui.column().classes('w-full gap-4'):
                            with ui.card().classes('mq-card w-full p-5'):
                                ui.label('Transmutation').classes('text-2xl font-semibold text-slate-100')
                                ui.label("A brass-ringed sanctum where old gear is broken down into new possibility, provided you can survive the jaguar's mood.").classes('mq-panel-caption mt-2')
                                ui.label(state.current_transmute_line or 'Varkesh watches your hands and your relics with equal contempt.').classes('text-slate-300 leading-7 mt-2 italic')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('SANCTUM STATUS').classes('mq-panel-caption')
                                    ui.label(f'Gold {player.gold}  •  Inventory items {len(player.inventory)}  •  Cost 25 gold per ritual').classes('mq-detail-text mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('VARKESH').classes('mq-panel-caption')
                                    ui.label(state.transmute_message).classes('mq-detail-text mt-2')
                            with ui.card().classes('mq-card w-full p-4'):
                                ui.label('Transmutation Sanctum').classes('text-xl font-semibold text-slate-100 mb-3')
                                with ui.element('div').classes('mq-scene-stage w-full'):
                                    if TRANSMUTATION_SCENE_DATA_URI:
                                        with ui.element('div').classes('mq-scene-image-wrap'):
                                            ui.image(TRANSMUTATION_SCENE_DATA_URI).classes('mq-scene-image')
                                    else:
                                        with ui.element('div').classes('mq-scene-fallback w-full h-full'):
                                            for label in ['Ritual Circle', 'Brass Rings', 'Varkesh']:
                                                ui.label(label).classes('mq-scene-fallback-pill')
                            with ui.element('div').classes('mq-inventory-shell w-full'):
                                with ui.column().classes('w-full gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Ritual Selection').classes('text-xl font-semibold text-slate-100 mb-3')
                                        ui.select(first_options or [''], value=state.transmute_choice_one if state.transmute_choice_one in first_options else (first_options[0] if first_options else ''), label='OFFERING ONE', on_change=lambda e: (setattr(state, 'transmute_choice_one', e.value or ''), setattr(state, 'transmute_choice_two', ''), state.ensure_transmute_scene_state(False), render.refresh())).classes('w-full')
                                        ui.select(second_options or [''], value=state.transmute_choice_two if state.transmute_choice_two in second_options else (second_options[0] if second_options else ''), label='OFFERING TWO', on_change=lambda e: (setattr(state, 'transmute_choice_two', e.value or ''), render.refresh())).classes('w-full mt-3')
                                        with ui.row().classes('gap-2 mt-4 flex-wrap'):
                                            action = ui.button('Begin Transmutation', on_click=lambda: (state.transmute_selected(), render.refresh()))
                                            action.classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            if player.gold < 25 or first_item is None or second_item is None or not state.transmute_items_match(first_item, second_item):
                                                action.disable()
                                            ui.button('Open Inventory', on_click=lambda: open_inventory_scene()).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label(f'Available Offerings ({len(item_map)})').classes('text-xl font-semibold text-slate-100 mb-3')
                                        if not item_map:
                                            ui.label('Your pack is empty.').classes('text-slate-300')
                                        else:
                                            for label_text, (_source, key, item) in item_map.items():
                                                selected_a = state.transmute_choice_one == label_text
                                                selected_b = state.transmute_choice_two == label_text
                                                row_classes = 'mq-item-card selected' if selected_a or selected_b else 'mq-item-card'
                                                with ui.card().classes(f'{row_classes} w-full p-3 mb-2'):
                                                    with ui.row().classes('w-full items-center gap-3 max-[860px]:flex-wrap'):
                                                        with ui.element('div').classes('mq-item-icon-frame'):
                                                            icon_uri = item_icon_uri(item)
                                                            if icon_uri:
                                                                ui.image(icon_uri).classes('mq-item-icon')
                                                            else:
                                                                ui.label(item.subtype[:2].upper() if item.subtype else item.slot[:2].upper()).classes('mq-item-icon-fallback')
                                                        with ui.column().classes('gap-1 flex-grow'):
                                                            ui.html(rarity_badge_html(item.rarity))
                                                            ui.label(f'{label_text} • {item.summary()}').classes('text-slate-100 font-medium')
                                                            ui.label(item.short_stat_text()).classes('text-slate-300 text-xs leading-6')
                                                        with ui.row().classes('gap-2 flex-wrap justify-end max-[860px]:justify-start'):
                                                            ui.button('Set as One', on_click=lambda l=label_text: (setattr(state, 'transmute_choice_one', l), setattr(state, 'transmute_choice_two', ''), state.ensure_transmute_scene_state(False), render.refresh())).classes('mq-btn-gold rounded-lg')
                                                            set_two = ui.button('Set as Two', on_click=lambda l=label_text: (setattr(state, 'transmute_choice_two', l), render.refresh()))
                                                            set_two.classes('mq-btn-gold rounded-lg')
                                                            if label_text not in second_options:
                                                                set_two.disable()
                                with ui.column().classes('w-full gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Offering One').classes('text-xl font-semibold text-slate-100 mb-3')
                                        with ui.row().classes('items-start gap-3 mt-1'):
                                            with ui.element('div').classes('mq-item-icon-frame'):
                                                icon_uri = item_icon_uri(first_item)
                                                if icon_uri:
                                                    ui.image(icon_uri).classes('mq-item-icon')
                                                else:
                                                    ui.label('--').classes('mq-item-icon-fallback')
                                            ui.label('\n'.join(item_detail_lines(first_item))).classes('mq-detail-text flex-grow')
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Offering Two').classes('text-xl font-semibold text-slate-100 mb-3')
                                        with ui.row().classes('items-start gap-3 mt-1'):
                                            with ui.element('div').classes('mq-item-icon-frame'):
                                                icon_uri = item_icon_uri(second_item)
                                                if icon_uri:
                                                    ui.image(icon_uri).classes('mq-item-icon')
                                                else:
                                                    ui.label('--').classes('mq-item-icon-fallback')
                                            ui.label('\n'.join(item_detail_lines(second_item))).classes('mq-detail-text flex-grow')
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Projected Outcome').classes('text-xl font-semibold text-slate-100 mb-3')
                                        if first_item is None or second_item is None:
                                            ui.label('Select two offerings to see the outcome rules.').classes('text-slate-300')
                                        elif not state.transmute_items_match(first_item, second_item):
                                            ui.label('Offerings do not match. Both items must share the same tier, slot, and subtype.').classes('text-rose-300')
                                        else:
                                            lines = [
                                                f'Tier: {first_item.level}',
                                                f'Type: {first_item.subtype} {first_item.slot.title()}',
                                                'Cost: 25 gold',
                                                '',
                                                f'35% chance: {upgrade_rarity}',
                                                'One rarity above the lower offering.',
                                                '',
                                                f'50% chance: {same_rarity}',
                                                "Hold the line at the higher offering's rarity.",
                                                '',
                                                f'15% chance: {downgrade_rarity}',
                                                'One rarity below the higher offering.',
                                            ]
                                            ui.label('\n'.join(lines)).classes('mq-detail-text')
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Routes').classes('text-xl font-semibold text-slate-100 mb-3')
                                        with ui.row().classes('gap-2 flex-wrap'):
                                            ui.button('Return to Town', on_click=lambda: (state.enter_town('You leave the sanctum and return to the town square.'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            ui.button('Return to Arena', on_click=lambda: (state.open_game_tab('arena'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                            return
                    elif state.game_tab == 'well':
                        state.ensure_well_scene_state(False)
                        tempt_line = state.current_well_scene_line or "The handmaiden waits beside the well, smiling at the sound of coin."
                        status_text = state.well_status_text()
                        with ui.column().classes('w-full gap-4'):
                            with ui.card().classes('mq-card w-full p-5'):
                                ui.label('Well of Evil').classes('mq-inv-title')
                                ui.label('A cursed well whispers promises of treasure to anyone reckless enough to feed it coin.').classes('text-slate-300 text-lg leading-8 mt-2')
                                ui.label("'Ten gold, darling. Toss it in and the well will send something dreadful to adore your blade.'").classes('text-slate-100 text-xl leading-9 mt-2 italic')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('TEMPTATION').classes('mq-panel-caption')
                                    ui.label(tempt_line).classes('text-slate-100 text-xl leading-9 mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('STATUS').classes('mq-panel-caption')
                                    ui.label(status_text).classes('text-slate-200 text-lg leading-8 mt-2')
                            with ui.row().classes('w-full items-start gap-4 max-[1250px]:flex-wrap'):
                                with ui.column().classes('flex-[0.95] min-w-[350px] gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('The Well').classes('mq-inv-section-title mb-3')
                                        with ui.element('div').classes('mq-scene-stage w-full'):
                                            if WELL_SCENE_DATA_URI:
                                                with ui.element('div').classes('mq-scene-image-wrap'):
                                                    ui.html(f"<img src='{html.escape(WELL_SCENE_DATA_URI, quote=True)}' alt='Well of Evil scene' class='mq-scene-image' loading='eager' decoding='sync' draggable='false'>")
                                            else:
                                                with ui.element('div').classes('mq-scene-fallback w-full h-full'):
                                                    for label in ['The Well', 'Handmaiden', 'Moonlit Stones']:
                                                        ui.label(label).classes('mq-scene-fallback-pill')
                                with ui.column().classes('flex-1 min-w-[380px] gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Offering').classes('mq-inv-section-title mb-3')
                                        ui.label('Feed the well 10 gold to summon a stronger foe. Wellspawns pay out more XP and always drop treasure.').classes('text-slate-200 text-lg leading-8')
                                        with ui.row().classes('gap-2 mt-4 flex-wrap'):
                                            async def handle_well_fight() -> None:
                                                state.open_game_tab('arena', 'The well churns. Something wicked claws its way toward the surface...')
                                                render.refresh()
                                                await state.queue_well_encounter_async(render.refresh)
                                            fight_btn = ui.button('Fight (Pay 10 Gold)', on_click=handle_well_fight)
                                            fight_btn.classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            if player.gold < 10 or state.fight_in_progress:
                                                fight_btn.disable()
                                            ui.button('Return to Town', on_click=lambda: (state.enter_town('You step away from the well and return to the town square.'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            ui.button('Return to Arena', on_click=lambda: (state.open_game_tab('arena'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Ritual Terms').classes('mq-inv-section-title mb-3')
                                        lines = [
                                            'Cost: 10 gold',
                                            'Difficulty: stronger than a normal arena foe',
                                            'Reward: guaranteed item drop',
                                            'Rarity: boosted compared with normal arena kills',
                                        ]
                                        ui.label('\n'.join(lines)).classes('text-slate-200 text-lg leading-8')
                            return
                    elif state.game_tab == 'inn':
                        state.ensure_inn_scene_state(False)
                        status_text = state.inn_status_text()
                        with ui.column().classes('w-full gap-4'):
                            with ui.card().classes('mq-card w-full p-5'):
                                ui.label('Inn').classes('text-2xl font-semibold text-slate-100')
                                ui.label('A room costs 1 gold. Resting restores 35% HP and 35% mana while resetting your Monster Chain Combo. The Inn Vault stores up to 20 items and charges 5 gold only when you store something.').classes('text-slate-300 leading-7 mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('INNKEEPER').classes('mq-panel-caption')
                                    ui.label(state.current_inn_line or 'The hearth is quiet, but welcoming.').classes('mq-detail-text mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('STATUS').classes('mq-panel-caption')
                                    ui.label(status_text).classes('mq-detail-text mt-2 whitespace-pre-line')
                            with ui.row().classes('w-full items-start gap-4 max-[1250px]:flex-wrap'):
                                with ui.column().classes('flex-[0.95] min-w-[350px] gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Inn Hearth').classes('mq-inv-section-title mb-3')
                                        with ui.element('div').classes('mq-scene-stage w-full'):
                                            if INN_SCENE_DATA_URI:
                                                with ui.element('div').classes('mq-scene-image-wrap'):
                                                    ui.html(f"<img src='{html.escape(INN_SCENE_DATA_URI, quote=True)}' alt='Inn scene' class='mq-scene-image' loading='eager' decoding='sync' draggable='false'>")
                                            else:
                                                with ui.element('div').classes('mq-scene-fallback w-full h-full'):
                                                    for label in ['Inn', 'Hearth', 'Innkeeper']:
                                                        ui.label(label).classes('mq-scene-fallback-pill')
                                with ui.column().classes('flex-1 min-w-[380px] gap-4'):
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Lodgings').classes('mq-inv-section-title mb-3')
                                        ui.label('Resting is a cheap survival reset, not a free upside. You recover health and mana, but your Monster Chain Combo falls back to 0.').classes('mq-detail-text')
                                        with ui.row().classes('gap-2 mt-4 flex-wrap'):
                                            rest_btn = ui.button('Rest (1 Gold)', on_click=lambda: (state.inn_rest(), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            if player.gold < 1:
                                                rest_btn.disable()
                                            ui.button('Open Inn Vault', on_click=open_inn_vault_dialog).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            ui.button('Open Inventory', on_click=lambda: open_inventory_scene('You look through your pack beside the hearth.')).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                            ui.button('Return to Town', on_click=lambda: (state.enter_town('You leave the inn and step back into the town square.'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                    with ui.card().classes('mq-card w-full p-4'):
                                        ui.label('Inn Vault').classes('mq-inv-section-title mb-3')
                                        ui.label('A separate vault window lets you browse inventory on the left, vault storage on the right, and manage transfers from the center action bar.').classes('mq-detail-text')
                                        ui.label(f'Capacity {len(state.vault_items)}/20 • Store cost 5 gold • Withdrawals free').classes('text-slate-300 text-base mt-3')
                            return
                    elif state.game_tab == 'ladder':
                        state.ensure_ladder_scene_state(False)
                        current_run = format_duration(state.current_run_elapsed_seconds()) if player is not None else '—'
                        with ui.column().classes('w-full gap-4'):
                            with ui.card().classes('mq-card w-full p-5'):
                                ui.label('Ladder').classes('text-2xl font-semibold text-slate-100')
                                ui.label('The registrar tallies speed, survival, and stubbornness across every class that has dared the climb.').classes('text-slate-300 leading-7 mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('ATTEMPT').classes('mq-panel-caption')
                                    ui.label(f'{player.name}  •  {player.player_class}  •  Current run {current_run}').classes('mq-detail-text mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('LEDGER').classes('mq-panel-caption')
                                    ui.label(state.ladder_totals_text()).classes('mq-detail-text mt-2')
                                with ui.card().classes('mq-panel-frame p-4 mt-4'):
                                    ui.label('REGISTRAR').classes('mq-panel-caption')
                                    ui.label(state.current_ladder_line).classes('mq-detail-text mt-2')
                            with ui.card().classes('mq-card w-full p-4'):
                                ui.label('Fastest MasterQuest Clears').classes('text-xl font-semibold text-slate-100 mb-3')
                                fastest_rows = state.ladder_fastest_rows()
                                if not fastest_rows:
                                    ui.label('No class has logged a browser-side MasterQuest clear yet. The registrar is still waiting for the first perfect run.').classes('text-slate-300')
                                else:
                                    for rank, (class_name, seconds) in enumerate(fastest_rows[:5], start=1):
                                        with ui.row().classes('justify-between items-center mq-panel p-3 mb-2'):
                                            ui.label(f'#{rank}  {class_name}').classes('text-slate-100 font-medium')
                                            ui.label(format_duration(seconds)).classes('text-amber-300 font-semibold')
                            with ui.card().classes('mq-card w-full p-4'):
                                ui.label('Lifetime Records by Class').classes('text-xl font-semibold text-slate-100 mb-3')
                                rows = [{**row, 'fastest_masterquest_seconds': format_duration(row['fastest_masterquest_seconds'])} for row in state.ladder_table_rows()]
                                ui.table(columns=[
                                    {'name':'class_name','label':'Class','field':'class_name'},
                                    {'name':'masterquest_attempts','label':'MQ Att.','field':'masterquest_attempts'},
                                    {'name':'fastest_masterquest_seconds','label':'Fastest','field':'fastest_masterquest_seconds'},
                                    {'name':'enemy_kills','label':'Kills','field':'enemy_kills'},
                                    {'name':'total_deaths','label':'Deaths','field':'total_deaths'},
                                    {'name':'wellspawns_killed','label':'Wellsp.','field':'wellspawns_killed'},
                                ], rows=rows, row_key='class_name').classes('w-full')
                                with ui.row().classes('gap-2 mt-4 flex-wrap'):
                                    ui.button('Return to Town', on_click=lambda: (state.enter_town("You step away from the registrar's desk."), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                    ui.button('Return to Arena', on_click=lambda: (state.open_game_tab('arena'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                            return
                    elif state.game_tab == 'glossary':
                        glossary_text = state.glossary_lines()
                        with ui.column().classes('w-full gap-4'):
                            with ui.card().classes('mq-card w-full p-5'):
                                ui.label('Glossary').classes('text-2xl font-semibold text-slate-100')
                                ui.label('Tier breakpoints, subtype bases, rarity weights, affix caps, and drop rules — all in one place.').classes('text-slate-300 leading-7 mt-2')
                                with ui.row().classes('gap-2 mt-4 flex-wrap'):
                                    ui.button('Return to Town', on_click=lambda: (state.enter_town('You close the brass-bound glossary.'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                                    ui.button('Return to Arena', on_click=lambda: (state.open_game_tab('arena'), render.refresh())).classes('mq-btn-gold rounded-xl px-5 py-3 font-semibold')
                            with ui.card().classes('mq-card w-full p-4'):
                                ui.label('Systems Ledger').classes('text-xl font-semibold text-slate-100 mb-3')
                                ui.code(glossary_text).classes('w-full whitespace-pre-wrap text-sm leading-6')
                            return
                    elif state.game_tab == 'stats':
                        with ui.card().classes('mq-card w-full p-5'):
                            ui.label('Core Stats').classes('text-xl font-semibold text-slate-100 mb-3')
                            stats = [
                                ('strength', player.strength, player.base_strength),
                                ('dexterity', player.dexterity, player.base_dexterity),
                                ('intelligence', player.intelligence, player.base_intelligence),
                                ('vitality', player.vitality, player.base_vitality),
                            ]
                            for key, total, base in stats:
                                with ui.row().classes('w-full items-center justify-between mq-panel p-3 mb-2 max-[640px]:flex-wrap gap-2'):
                                    ui.label(f'{STAT_LABELS[key]} • Allocated {base} • Total {total}').classes('text-slate-200')
                                    plus = ui.button('+1', on_click=lambda k=key: (state.allocate(k), render.refresh()))
                                    plus.classes('mq-btn-gold rounded-lg')
                                    if state.fight_in_progress or player.unspent_stat_points <= 0:
                                        plus.disable()
                            ui.separator().classes('my-4')
                            ui.label('Class Notes').classes('text-xl font-semibold text-slate-100 mb-2')
                            ui.label(CLASS_DESCRIPTIONS[player.player_class]).classes('text-slate-300')
                            ui.label('Magic classes automatically cast when they have enough mana and a charm equipped; otherwise they fall back to weapon/base attacks.').classes('text-slate-400 text-sm mt-3')
                    else:
                        with ui.card().classes('mq-card w-full p-5'):
                            ui.label('Save Codes').classes('text-xl font-semibold text-slate-100 mb-3')
                            ui.label('This browser build still supports export/import save codes, so you can move a hero between machines or browsers.').classes('text-slate-300 mb-3')
                            ui.textarea(label='Exported Save Code', value=state.export_code).props('readonly autogrow').classes('w-full')
                            ui.textarea(label='Paste Save Code To Import', value=state.import_code, on_change=lambda e: setattr(state, 'import_code', e.value)).props('autogrow').classes('w-full')
                            with ui.row().classes('gap-2 mt-2 max-[700px]:w-full'):
                                refresh_save = ui.button('Generate / Refresh Save Code', on_click=lambda: (state.export_save(), render.refresh()))
                                refresh_save.classes('mq-btn-gold max-[700px]:w-full')
                                import_save = ui.button('Import Save Code', on_click=lambda: (state.import_save(), render.refresh())).props('color=green')
                                import_save.classes('max-[700px]:w-full')
                    return
                display_monster = state.arena_display_monster()
                monster_uri = state.arena_monster_uri(display_monster) if display_monster else ''
                hero_uri = _hero_data_uri(player.player_class)
                current_target = state.arena_target_level()
                arena_target_options = {level: f'Monster Lv {level}' for level in range(1, player.level + 1)}
                level_penalty = max(0, player.level - current_target) * 10
                transition_class = state.arena_transition_tone or 'muted'
                monster_state_label = 'Current Enemy'
                if state.current_monster is not None and state.current_encounter_type == 'well':
                    monster_state_label = 'Wellspawn'
                if state.current_monster is None and display_monster is not None:
                    monster_state_label = 'Defeated' if state.last_fight_outcome == 'victory' else ('Last Opponent' if state.last_fight_outcome == 'defeat' else 'Between Rounds')
                with ui.element('div').classes('mq-arena-top w-full'):
                    with ui.card().classes('mq-arena-card w-full p-5'):
                        with ui.element('div').classes('mq-player-side-layout'):
                            with ui.element('div').classes('mq-arena-avatar-frame'):
                                if hero_uri:
                                    ui.html(f"<img src='{html.escape(hero_uri, quote=True)}' alt='{html.escape(player.player_class)} hero art' class='mq-arena-avatar-static' loading='eager' decoding='sync' draggable='false'>")
                                else:
                                    ui.label(player.player_class).classes('mq-arena-avatar empty')
                            with ui.column().classes('gap-2 min-w-0 w-full'):
                                ui.label(player.name).classes('text-2xl font-semibold text-slate-100')
                                ui.label(f'{player.player_class}  •  Level {player.level}').classes('text-slate-300')
                                def handle_arena_stat_click(stat_key: str, shift_all: bool = False) -> None:
                                    if state.fight_in_progress or player.unspent_stat_points <= 0:
                                        return
                                    amount = player.unspent_stat_points if shift_all else 1
                                    state.allocate_multiple(stat_key, amount)
                                    render.refresh()
                                def arena_core_stat_chip(stat_key: str, label: str, value: int) -> None:
                                    can_allocate_here = (not state.fight_in_progress and player.unspent_stat_points > 0)
                                    chip_classes = 'mq-stat-chip mq-stat-chip-clickable' if can_allocate_here else 'mq-stat-chip'
                                    chip = ui.element('div').classes(chip_classes)
                                    if can_allocate_here:
                                        chip.on('click', lambda e, k=stat_key: handle_arena_stat_click(k, bool((e.args or {}).get('shiftKey'))), ['shiftKey'])
                                    with chip:
                                        ui.label(label).classes('mq-stat-chip-label')
                                        value_text = f'{value}  •  +1' if can_allocate_here else str(value)
                                        ui.label(value_text).classes('mq-stat-chip-value')
                                with ui.element('div').classes('mq-core-stat-grid mt-2'):
                                    arena_core_stat_chip('strength', 'STR', player.strength)
                                    arena_core_stat_chip('dexterity', 'DEX', player.dexterity)
                                    arena_core_stat_chip('vitality', 'VIT', player.vitality)
                                    arena_core_stat_chip('intelligence', 'INT', player.intelligence)
                                with ui.element('div').classes('mq-player-summary-grid mt-2'):
                                    ui.html(f"<div class='mq-stat-chip'><div class='mq-stat-chip-label'>Attack</div><div class='mq-stat-chip-value'>{player.attack_min}-{player.attack_max}</div></div>")
                                    ui.html(f"<div class='mq-stat-chip'><div class='mq-stat-chip-label'>Attack Mode</div><div class='mq-stat-chip-value'>{html.escape(attack_mode_label(player))}</div></div>")
                                    ui.html(f"<div class='mq-stat-chip'><div class='mq-stat-chip-label'>Defense</div><div class='mq-stat-chip-value'>Armor {player.physical_armor} • M.Res {player.magic_resistance}</div></div>")
                                    ui.html(f"<div class='mq-stat-chip'><div class='mq-stat-chip-label'>Precision</div><div class='mq-stat-chip-value'>ACC {player.accuracy:.2f} • EVA {int(round(player.evasion * 100))}%</div></div>")
                                    ui.html(f"<div class='mq-stat-chip'><div class='mq-stat-chip-label'>Critical</div><div class='mq-stat-chip-value'>{int(round(player.crit_chance * 100))}% @ {player.crit_damage:.2f}x</div></div>")
                                    ui.html(f"<div class='mq-stat-chip'><div class='mq-stat-chip-label'>Run</div><div class='mq-stat-chip-value'>Gold {player.gold} • W {player.wins} / L {player.losses}</div></div>")
                        with ui.element('div').classes('mq-player-panels'):
                            with ui.card().classes('mq-panel-frame p-4 h-full'):
                                ui.label('LOADOUT').classes('mq-panel-caption')
                                ui.html(f"<div class='text-slate-300 text-sm mt-2'>Weapon&nbsp;&nbsp;{hoverable_item_name_html(player.equipped.get('weapon'))}</div>")
                                ui.html(f"<div class='text-slate-300 text-sm mt-1'>Armor&nbsp;&nbsp;&nbsp;{hoverable_item_name_html(player.equipped.get('armor'))}</div>")
                                ui.html(f"<div class='text-slate-300 text-sm mt-1'>Charm&nbsp;&nbsp;&nbsp;{hoverable_item_name_html(player.equipped.get('charm'))}</div>")
                            with ui.card().classes('mq-panel-frame p-4 h-full'):
                                ui.label('ADVENTURER').classes('mq-panel-caption')
                                ui.label(f'Unspent Stat Points: {player.unspent_stat_points}').classes('text-amber-300 text-sm mt-2')
                        with ui.element('div').classes('mq-player-meters'):
                            ui.html(f"<div class='mq-meter'><div class='mq-meter-row'><span>HP</span><span>{player.hp}/{player.max_hp}</span></div><div class='mq-meter-track'><div class='mq-meter-fill hp' style='width:{meter_fill_pct(player.hp, player.max_hp):.2f}%'></div></div></div>")
                            ui.html(f"<div class='mq-meter'><div class='mq-meter-row'><span>Mana</span><span>{player.mana}/{player.max_mana}</span></div><div class='mq-meter-track'><div class='mq-meter-fill mana' style='width:{meter_fill_pct(player.mana, max(1, player.max_mana)):.2f}%'></div></div></div>")
                            ui.html(f"<div class='mq-meter'><div class='mq-meter-row'><span>XP</span><span>{player.xp}/{player.xp_to_next}</span></div><div class='mq-meter-track'><div class='mq-meter-fill exp' style='width:{meter_fill_pct(player.xp, max(1, player.xp_to_next)):.2f}%'></div></div></div>")
                    with ui.card().classes('mq-arena-card w-full p-5'):
                        ui.label('Current Enemy').classes('text-xl font-semibold text-slate-100 mb-3')
                        with ui.element('div').classes('mq-monster-panel-grid w-full'):
                            with ui.column().classes('w-full gap-3 items-center'):
                                with ui.element('div').classes('mq-monster-stage mq-monster-stage-themed w-full').style(monster_theme_style(display_monster.monster_type if display_monster is not None else '')):
                                    if monster_uri:
                                        monster_alt = html.escape(display_monster.monster_type if display_monster is not None else 'Monster')
                                        with ui.element('div').classes('mq-monster-image-wrap'):
                                            ui.html(f"<img src='{html.escape(monster_uri, quote=True)}' alt='{monster_alt}' class='mq-monster-image-static' loading='eager' decoding='sync' draggable='false'>")
                                    elif display_monster is None:
                                        ui.label('No active target').classes('mq-monster-fallback')
                                    else:
                                        ui.label(display_monster.monster_type).classes('mq-monster-fallback')
                                quote_text = f'“{display_monster.monster_dialogue}”' if display_monster is not None and state.current_monster is not None and display_monster.monster_dialogue else (state.arena_transition_text or 'The arena waits in the hush between clashes.')
                                ui.label(quote_text).classes('mq-monster-quote text-slate-200 italic whitespace-pre-line w-full text-center text-xl leading-9')
                            with ui.column().classes('mq-monster-details w-full'):
                                if display_monster is None:
                                    ui.label('No active enemy.').classes('text-2xl font-semibold text-slate-100')
                                    ui.label('Choose when to call the next challenger.').classes('text-slate-300')
                                else:
                                    ui.html(f"<span class='mq-monster-nameplate'>{html.escape(monster_state_label)}</span>")
                                    ui.label(monster_species_name(display_monster.monster_type)).classes('text-3xl font-semibold text-slate-100')
                                    secondary = f'{display_monster.monster_personal_name}  •  Level {display_monster.level}' if state.current_monster is not None else f'{display_monster.monster_personal_name}  •  {monster_state_label}'
                                    ui.label(secondary).classes('text-slate-200')
                                    with ui.card().classes('mq-panel-frame p-4'):
                                        ui.label('COMBAT').classes('mq-panel-caption')
                                        ui.label(f'ATK  {display_monster.attack_min}-{display_monster.attack_max}  •  SPD {display_monster.speed}').classes('text-slate-300 text-sm mt-2')
                                        ui.label(f'DEF  Armor {display_monster.physical_armor}  •  M.Res {display_monster.magic_resistance}').classes('text-slate-300 text-sm mt-1')
                                        ui.label(f'ACC  {display_monster.accuracy:.2f}  •  EVA {int(round(display_monster.evasion * 100))}%  •  CRIT {int(round(display_monster.crit_chance * 100))}% @ {display_monster.crit_damage:.2f}x').classes('text-slate-300 text-sm mt-1')
                                        ui.label(f'Damage Type  {"Magic" if display_monster.damage_school == "magic" else "Physical"}').classes('text-slate-300 text-sm mt-1')
                                    with ui.element('div').classes('mq-meters'):
                                        current_hp = display_monster.hp
                                        ui.html(f"<div class='mq-meter'><div class='mq-meter-row'><span>HP</span><span>{current_hp}/{display_monster.max_hp}</span></div><div class='mq-meter-track'><div class='mq-meter-fill hp' style='width:{meter_fill_pct(current_hp, display_monster.max_hp):.2f}%'></div></div></div>")
                with ui.card().classes('mq-arena-card w-full p-5'):
                    with ui.row().classes('mq-arena-options w-full'):
                        ui.label('Arena target:').classes('text-slate-300')
                        target_select = ui.select(arena_target_options, value=current_target, on_change=lambda e: setattr(state, 'arena_selected_level', int(e.value))).props('dense outlined')
                        target_select.classes('bg-transparent')
                        if state.fight_in_progress or state.arena_same_level:
                            target_select.disable()
                        same_level = ui.checkbox('Always fight your level', value=state.arena_same_level)
                        def _toggle_same(e):
                            state.arena_same_level = bool(e.value)
                            if state.player is not None and state.arena_same_level:
                                state.arena_selected_level = state.player.level
                            render.refresh()
                        same_level.on_value_change(_toggle_same)
                        if state.fight_in_progress:
                            same_level.disable()
                        penalty_text = 'Hero Level' if state.arena_same_level else f'Lv {current_target} ({level_penalty}% lower-level XP penalty)'
                        ui.label(f'Target {penalty_text}').classes('text-slate-400 text-sm')
                    with ui.row().classes('mq-arena-buttons w-full mt-4'):
                        fight_btn = ui.button('Fight', on_click=handle_fight).classes('mq-arena-btn')
                        if state.fight_in_progress:
                            fight_btn.disable()
                        status_btn = ui.button('Status', on_click=handle_status).classes('mq-arena-btn secondary')
                        inventory_btn = ui.button('Inventory', on_click=lambda: open_inventory_scene()).classes('mq-arena-btn secondary')
                        if state.fight_in_progress:
                            inventory_btn.disable()
                        player_stats_btn = ui.button('Player Stats', on_click=lambda: (state.open_game_tab('stats'), render.refresh())).classes('mq-arena-btn secondary')
                        with ui.element('div').classes('mq-prof-tooltip-wrap'):
                            proficiency_btn = ui.button('Proficiency', on_click=lambda: None).classes('mq-arena-btn secondary')
                            ui.html(build_proficiency_tooltip_html(player)).classes('mq-prof-tooltip-panel')
                        return_town = ui.button('Return to Town', on_click=lambda: (state.enter_town('You return to town to choose your next route.'), render.refresh())).classes('mq-arena-btn secondary')
                        if state.fight_in_progress:
                            return_town.disable()
                    ui.label(state.arena_transition_text or '').classes(f'mq-transition {transition_class} mt-3')
                with ui.card().classes('mq-arena-card w-full p-5'):
                    ui.label('Combat Log').classes('text-xl font-semibold text-slate-100 mb-3')
                    ui.html(combat_log_widget_html(state.log[-40:]))
                    ui.run_javascript(f"""
(() => {{
  const el = document.getElementById('mq-combat-log');
  if (!el) return;
  window.mqCombatLogState = window.mqCombatLogState || {{ stickToBottom: true }};
  if (!el.dataset.followBound) {{
    el.addEventListener('scroll', () => {{
      const nearBottom = (el.scrollHeight - el.clientHeight - el.scrollTop) < 140;
      window.mqCombatLogState.stickToBottom = nearBottom;
    }}, {{ passive: true }});
    el.dataset.followBound = '1';
  }}
  const shouldStick = {str(state.fight_in_progress).lower()} || !!window.mqCombatLogState.stickToBottom;
  requestAnimationFrame(() => {{
    if (!shouldStick) return;
    el.scrollTo({{ top: el.scrollHeight, behavior: {"'smooth'" if state.fight_in_progress else "'auto'"} }});
  }});
}})();
""")
    ui.timer(0.2, lambda: (render.refresh() if state.passive_regen_tick() else None))
    render()
ui.run(title=APP_TITLE, reload=False)