"""
Configuration, palettes, layer definitions, and asset paths for
Echoes of Fa'Diel: A Mana Associations Journey.
"""

import os

# Base Directories
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
BG_DIR = os.path.join(ASSETS_DIR, "backgrounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
PEBBLE_SPRITES_DIR = os.path.join(SPRITES_DIR, "pebbles")
RECEPTACLE_SPRITES_DIR = os.path.join(SPRITES_DIR, "receptacles")
ICON_SPRITES_DIR = os.path.join(SPRITES_DIR, "icons")
TEMPLATES_DIR = os.path.join(SPRITES_DIR, "templates")

# Window & Display Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Echoes of Fa'Diel — A Mana Associations Journey"

# Stone / Pebble & Receptacle Dimensions (also used for PNG sprite templates)
PEBBLE_WIDTH = 148
PEBBLE_HEIGHT = 68
KEYSTONE_WIDTH = 152
KEYSTONE_HEIGHT = 76

RECEPTACLE_WIDTH = 178
RECEPTACLE_HEIGHT = 116

# Board Layout Coordinates
TOP_BAR_HEIGHT = 54
POOL_AREA_Y = 66
TABLEAU_AREA_Y = 212

# Stock & Waste (Mana Spring & Divination Basin) on Top-Left
STOCK_POS = (52, POOL_AREA_Y + 18)
WASTE_POS = (224, POOL_AREA_Y + 18)

# Magical Pools / Receptacles on Top-Right
RECEPTACLE_START_X = 468
RECEPTACLE_SPACING_X = 196

# Tableau Cairns (Columns)
TABLEAU_START_X = 68
TABLEAU_SPACING_X = 192
VEILED_OFFSET_Y = 24       # Vertical spacing between veiled pebbles
REVEALED_OFFSET_Y = 34     # Vertical spacing between revealed pebbles in a cluster

# Nostalgic Watercolor & Storybook Palette (Legend of Mana / 90s Fantasy aesthetic)
PALETTE = {
    # UI Parchment & Wood / Stone frames
    "parchment_light": (246, 238, 218),
    "parchment_mid": (226, 212, 182),
    "parchment_dark": (184, 164, 130),
    "ink_dark": (42, 33, 27),
    "ink_warm": (78, 58, 42),
    "ink_gold": (235, 198, 112),
    "gold_bright": (255, 224, 130),
    "gold_rim": (198, 156, 78),
    "bronze_rim": (138, 102, 58),

    # Moss & Ancient Stone
    "stone_base": (72, 78, 74),
    "stone_light": (108, 116, 108),
    "stone_dark": (44, 48, 46),
    "moss_green": (94, 138, 78),
    "moss_bright": (136, 184, 96),
    "mana_cyan": (110, 225, 215),
    "mana_glow": (165, 248, 230),
    "water_deep": (36, 76, 94),
    "water_mid": (64, 128, 146),
    "water_shimmer": (155, 222, 232),

    # Three Major Lore Pillars (Elements, Biomes, Classes)
    "pillar_element": {
        "name": "Magical Elements",
        "stone_fill": (74, 54, 68),
        "stone_highlight": (118, 84, 106),
        "stone_border": (218, 138, 94),
        "glow": (255, 168, 108),
        "gem": (245, 112, 78),
        "water_tint": (185, 95, 80),
        "text_accent": (255, 218, 185),
    },
    "pillar_biome": {
        "name": "Mythical Biomes",
        "stone_fill": (52, 74, 66),
        "stone_highlight": (82, 114, 100),
        "stone_border": (124, 192, 136),
        "glow": (148, 235, 168),
        "gem": (92, 204, 132),
        "water_tint": (72, 164, 128),
        "text_accent": (212, 246, 218),
    },
    "pillar_class": {
        "name": "Classes & Relics",
        "stone_fill": (56, 62, 84),
        "stone_highlight": (88, 96, 128),
        "stone_border": (154, 168, 228),
        "glow": (182, 198, 255),
        "gem": (132, 152, 240),
        "water_tint": (96, 118, 196),
        "text_accent": (222, 228, 255),
    },
}

# Custom Font Configuration
# Users can drop .ttf or .otf files into assets/fonts/ with these filenames,
# or any single custom .ttf/.otf file in assets/fonts/ will be picked up automatically.
FONT_CONFIG = {
    "title": {
        "custom_files": ["title.ttf", "title.otf", "mana_title.ttf", "fantasy.ttf"],
        "system_fallbacks": ["Georgia", "Palatino Linotype", "Book Antiqua", "Garamond", "Times New Roman"],
        "bold": True,
    },
    "subtitle": {
        "custom_files": ["subtitle.ttf", "body.ttf", "mana_body.ttf", "fantasy.ttf"],
        "system_fallbacks": ["Palatino Linotype", "Georgia", "Book Antiqua", "Garamond"],
        "bold": False,
    },
    "rune_word": {
        "custom_files": ["rune.ttf", "pebble.ttf", "body.ttf", "fantasy.ttf"],
        "system_fallbacks": ["Georgia", "Book Antiqua", "Palatino Linotype", "Garamond"],
        "bold": True,
    },
    "keystone_title": {
        "custom_files": ["keystone.ttf", "title.ttf", "fantasy.ttf"],
        "system_fallbacks": ["Georgia", "Palatino Linotype", "Book Antiqua"],
        "bold": True,
    },
    "ui": {
        "custom_files": ["ui.ttf", "body.ttf", "fantasy.ttf"],
        "system_fallbacks": ["Georgia", "Palatino Linotype", "Segoe UI", "Arial"],
        "bold": True,
    },
    "lore": {
        "custom_files": ["lore.ttf", "body.ttf", "fantasy.ttf"],
        "system_fallbacks": ["Palatino Linotype", "Georgia", "Book Antiqua", "Garamond"],
        "bold": False,
    },
}
