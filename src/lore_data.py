"""
Lore categories, nostalgic 90s fantasy word associations, and Journey chapters.
Inspired by Legend of Mana, Magic: The Gathering, Dungeons & Dragons,
Myst, and The Elder Scrolls III: Morrowind.
"""

import random

# Three Major Pillars:
# - "pillar_element": Magical Elements, Mana Spirits, Spells & Colors of Magic
# - "pillar_biome":   Mythical Biomes, Nostalgic Realms, Ages & Sacred Lands
# - "pillar_class":   Character Classes, Guilds, Factions & Iconic Relics

LORE_CATEGORIES = [
    # =========================================================================
    # PILLAR 1: MAGICAL ELEMENTS
    # =========================================================================
    {
        "id": "mana_spirits",
        "title": "Fa'Diel Mana Spirits",
        "pillar": "pillar_element",
        "symbol": "spirit",
        "origin": "Legend of Mana",
        "lore_note": "The eight elemental spirits whose resonance shapes the world of Fa'Diel.",
        "words": ["Salamander", "Undine", "Gnome", "Jinn", "Dryad", "Wisp", "Shade", "Aura"],
    },
    {
        "id": "mtg_five_colors",
        "title": "Five Colors of Mana",
        "pillar": "pillar_element",
        "symbol": "flame",
        "origin": "Magic: The Gathering",
        "lore_note": "The five leyline affinities drawn from lands across the Multiverse.",
        "words": ["White Mana", "Blue Mana", "Black Mana", "Red Mana", "Green Mana"],
    },
    {
        "id": "mtg_iconic_instants",
        "title": "90s Spellbook Classics",
        "pillar": "pillar_element",
        "symbol": "spark",
        "origin": "Magic: The Gathering",
        "lore_note": "Timeless incantations cast across kitchen tables in the golden age of duelists.",
        "words": ["Counterspell", "Lightning Bolt", "Dark Ritual", "Giant Growth", "Swords to Plowshares", "Brainstorm"],
    },
    {
        "id": "dnd_arcane_schools",
        "title": "Schools of Arcane Magic",
        "pillar": "pillar_element",
        "symbol": "sigil",
        "origin": "Dungeons & Dragons",
        "lore_note": "The eight classical traditions studied by wizards of the high towers.",
        "words": ["Evocation", "Abjuration", "Necromancy", "Illusion", "Divination", "Conjuration", "Transmutation", "Enchantment"],
    },
    {
        "id": "morrowind_magic_arts",
        "title": "Mages Guild Disciplines",
        "pillar": "pillar_element",
        "symbol": "star",
        "origin": "TES III: Morrowind",
        "lore_note": "Mystical arts taught in the guildhalls of Vvardenfell, including Levitation and Recall.",
        "words": ["Mysticism", "Alteration", "Destruction", "Restoration", "Alchemy", "Illusionism"],
    },
    {
        "id": "alchemical_reagents",
        "title": "Vvardenfell Alchemy",
        "pillar": "pillar_element",
        "symbol": "potion",
        "origin": "TES III: Morrowind",
        "lore_note": "Exotic flora and salts ground with mortar and pestle for potent elixirs.",
        "words": ["Marshmerrow", "Wickwheat", "Frost Salts", "Void Salts", "Bittergreen", "Luminous Russula"],
    },
    {
        "id": "elemental_invocations",
        "title": "Archmage Invocations",
        "pillar": "pillar_element",
        "symbol": "flame",
        "origin": "Dungeons & Dragons",
        "lore_note": "High-circle spells inscribed on ancient vellum scrolls.",
        "words": ["Fireball", "Magic Missile", "Cone of Cold", "Chain Lightning", "Time Stop", "Meteor Swarm"],
    },
    {
        "id": "celestial_omens",
        "title": "Astral & Lunar Tides",
        "pillar": "pillar_element",
        "symbol": "moon",
        "origin": "Morrowind & Fa'Diel",
        "lore_note": "Twin moons and celestial phenomena heralding prophecies and mana surges.",
        "words": ["Masser", "Secunda", "Eclipse", "Starfall", "Sunbeam", "Aetherius"],
    },

    # =========================================================================
    # PILLAR 2: MYTHICAL BIOMES
    # =========================================================================
    {
        "id": "vvardenfell_realms",
        "title": "Vvardenfell Biomes",
        "pillar": "pillar_biome",
        "symbol": "mushroom",
        "origin": "TES III: Morrowind",
        "lore_note": "From giant mushroom coasts and muddy swamps to the blighted slopes of Red Mountain.",
        "words": ["Bitter Coast", "Ashlands", "Grazelands", "Ascadian Isles", "Red Mountain", "Azura's Coast"],
    },
    {
        "id": "morrowind_settlements",
        "title": "Ports & Strongholds",
        "pillar": "pillar_biome",
        "symbol": "arch",
        "origin": "TES III: Morrowind",
        "lore_note": "Iconic towns connected by Silt Striders, guild guides, and coastal ferries.",
        "words": ["Seyda Neen", "Balmora", "Vivec City", "Ald'ruhn", "Sadrith Mora", "Caldera"],
    },
    {
        "id": "myst_linking_ages",
        "title": "Linking Book Ages",
        "pillar": "pillar_biome",
        "symbol": "book",
        "origin": "Myst & Riven",
        "lore_note": "Silent, enigmatic worlds reached by placing a hand upon a glowing descriptive panel.",
        "words": ["Myst Island", "Channelwood", "Stoneship Age", "Mechanical Age", "Selenitic Age", "Riven"],
    },
    {
        "id": "fadiel_artifacts_lands",
        "title": "Sanctums of Fa'Diel",
        "pillar": "pillar_biome",
        "symbol": "tree",
        "origin": "Legend of Mana",
        "lore_note": "Wondrous lands restored to the world map by placing enchanted Artifacts.",
        "words": ["Domina", "Tree of Mana", "Luon Highway", "Lumina", "Norn Peaks", "Bejeweled City"],
    },
    {
        "id": "mtg_basic_taplands",
        "title": "Sacred Lands of Mana",
        "pillar": "pillar_biome",
        "symbol": "leaf",
        "origin": "Magic: The Gathering",
        "lore_note": "The five primordial terrains from which planeswalkers draw earthly power.",
        "words": ["Plains", "Island", "Swamp", "Mountain", "Forest"],
    },
    {
        "id": "mtg_legendary_realms",
        "title": "Planes & Sanctuaries",
        "pillar": "pillar_biome",
        "symbol": "arch",
        "origin": "Magic: The Gathering",
        "lore_note": "Storied planes and fabled academies from the Weatherlight and Urza sagas.",
        "words": ["Dominaria", "Tolaria", "Serra's Realm", "Phyrexia", "Shandalar", "Rath"],
    },
    {
        "id": "dwemer_and_ancient_ruins",
        "title": "Forgotten Sanctuaries",
        "pillar": "pillar_biome",
        "symbol": "ruin",
        "origin": "90s RPG Lore",
        "lore_note": "Subterranean brass citadels, sunken D'ni caverns, and moss-grown elven arches.",
        "words": ["Arkngthand", "D'ni Cavern", "Underdark", "Mind's Eye", "Bonechill Ruins", "Sunken Fane"],
    },
    {
        "id": "dnd_planes_of_existence",
        "title": "Great Wheel Cosmology",
        "pillar": "pillar_biome",
        "symbol": "portal",
        "origin": "Dungeons & Dragons",
        "lore_note": "Outer and Inner planes traversed via Sigil, the City of Doors.",
        "words": ["Sigil", "Feywild", "Astral Plane", "Ethereal Plane", "Shadowfell", "Elemental Chaos"],
    },

    # =========================================================================
    # PILLAR 3: CHARACTER CLASSES & RELICS
    # =========================================================================
    {
        "id": "dnd_martial_classes",
        "title": "Vanguard Classes",
        "pillar": "pillar_class",
        "symbol": "sword",
        "origin": "Dungeons & Dragons",
        "lore_note": "Sworn protectors, woodland trackers, and martial champions of the party.",
        "words": ["Paladin", "Ranger", "Barbarian", "Monk", "Fighter", "Cavalier"],
    },
    {
        "id": "dnd_mystic_classes",
        "title": "Spellcaster & Rogue Arts",
        "pillar": "pillar_class",
        "symbol": "staff",
        "origin": "Dungeons & Dragons",
        "lore_note": "Weavers of song, divine prayer, wild shape, and shadow craft.",
        "words": ["Druid", "Sorcerer", "Bard", "Cleric", "Warlock", "Shadowdancer"],
    },
    {
        "id": "morrowind_factions",
        "title": "Houses & Guilds of Resdayn",
        "pillar": "pillar_class",
        "symbol": "crest",
        "origin": "TES III: Morrowind",
        "lore_note": "Ancient Dunmer Great Houses and clandestine orders vying for influence.",
        "words": ["House Telvanni", "House Redoran", "House Hlaalu", "Morag Tong", "Ashlanders", "The Blades"],
    },
    {
        "id": "dnd_classic_monsters",
        "title": "Dungeon Denizens",
        "pillar": "pillar_class",
        "symbol": "eye",
        "origin": "Dungeons & Dragons",
        "lore_note": "Iconic aberrations and beasts lurking in torchlit subterranean labyrinths.",
        "words": ["Beholder", "Mind Flayer", "Owlbear", "Gelatinous Cube", "Mimic", "Displacer Beast"],
    },
    {
        "id": "mtg_vintage_relics",
        "title": "Urza's & Vintage Relics",
        "pillar": "pillar_class",
        "symbol": "gem",
        "origin": "Magic: The Gathering",
        "lore_note": "Mythic artifacts of immeasurable mana from the Antiquities war and Alpha.",
        "words": ["Black Lotus", "Sol Ring", "Mox Sapphire", "Icy Manipulator", "Nevinyrral's Disk", "Mox Jet"],
    },
    {
        "id": "dnd_wondrous_items",
        "title": "Wondrous D&D Treasure",
        "pillar": "pillar_class",
        "symbol": "chalice",
        "origin": "Dungeons & Dragons",
        "lore_note": "Enchanted heirlooms discovered inside a dragon's hoard.",
        "words": ["Bag of Holding", "Vorpal Sword", "Cloak of Elvenkind", "Deck of Many Things", "Immovable Rod", "Holy Avenger"],
    },
    {
        "id": "tabletop_rpg_lexicon",
        "title": "Tabletop Guild Lexicon",
        "pillar": "pillar_class",
        "symbol": "dice",
        "origin": "AD&D & 90s CRPGs",
        "lore_note": "Sacred polyhedrals and time-honored rules of pen-and-paper adventure.",
        "words": ["Natural 20", "THAC0", "Saving Throw", "Initiative", "Cantrip", "Dungeon Master"],
    },
    {
        "id": "fadiel_craft_materials",
        "title": "Watts' Forge Materials",
        "pillar": "pillar_class",
        "symbol": "anvil",
        "origin": "Legend of Mana",
        "lore_note": "Rare metals, scales, and woods tempered into masterwork blades and instruments.",
        "words": ["Lorimar Iron", "Dragon Scales", "Dior Wood", "Orihalcon", "Altena Alloy", "Swallowtail"],
    },
]

CATEGORY_BY_ID = {cat["id"]: cat for cat in LORE_CATEGORIES}


# Curated Journey Chapters (Levels)
JOURNEY_CHAPTERS = [
    {
        "level": 1,
        "title": "I. Beneath the Mana Tree",
        "subtitle": "Awaken the Sanctuary Pools with foundational Elements, Lands, and Classes.",
        "num_receptacles": 3,
        "num_columns": 5,
        "words_per_category": 4,
        "max_turns": 48,
        "categories": [
            "mana_spirits",
            "mtg_basic_taplands",
            "dnd_martial_classes",
            "fadiel_artifacts_lands",
            "mtg_iconic_instants",
        ],
    },
    {
        "level": 2,
        "title": "II. Mist Over Seyda Neen",
        "subtitle": "Cross the ash-swept waters of Vvardenfell and decipher the Linking Books.",
        "num_receptacles": 3,
        "num_columns": 5,
        "words_per_category": 4,
        "max_turns": 56,
        "categories": [
            "vvardenfell_realms",
            "morrowind_settlements",
            "myst_linking_ages",
            "morrowind_factions",
            "alchemical_reagents",
            "celestial_omens",
        ],
    },
    {
        "level": 3,
        "title": "III. The Archmage's Sanctum",
        "subtitle": "Balance three Receptacles across seven ancient traditions of spell and relic.",
        "num_receptacles": 3,
        "num_columns": 6,
        "words_per_category": 4,
        "max_turns": 68,
        "categories": [
            "dnd_arcane_schools",
            "mtg_vintage_relics",
            "dnd_wondrous_items",
            "mtg_legendary_realms",
            "dnd_mystic_classes",
            "elemental_invocations",
            "tabletop_rpg_lexicon",
        ],
    },
    {
        "level": 4,
        "title": "IV. Echoes of the Multiverse",
        "subtitle": "Four Sacred Pools open as deeper ruins and dungeon denizens emerge.",
        "num_receptacles": 4,
        "num_columns": 6,
        "words_per_category": 5,
        "max_turns": 82,
        "categories": [
            "mana_spirits",
            "vvardenfell_realms",
            "myst_linking_ages",
            "dnd_classic_monsters",
            "mtg_five_colors",
            "dwemer_and_ancient_ruins",
            "fadiel_craft_materials",
        ],
    },
    {
        "level": 5,
        "title": "V. Grand Grimoire of the 90s",
        "subtitle": "A masterwork trial of eight nostalgic realms and only three Receptacles.",
        "num_receptacles": 3,
        "num_columns": 6,
        "words_per_category": 5,
        "max_turns": 95,
        "categories": [
            "morrowind_magic_arts",
            "morrowind_settlements",
            "mtg_iconic_instants",
            "mtg_vintage_relics",
            "dnd_planes_of_existence",
            "dnd_wondrous_items",
            "fadiel_artifacts_lands",
            "morrowind_factions",
        ],
    },
]


def build_procedural_chapter(seed=None, difficulty="standard"):
    """
    Weaves a custom or procedural puzzle level ensuring balanced representation
    from Magical Elements, Mythical Biomes, and Character Classes.
    """
    rng = random.Random(seed)
    elements = [c for c in LORE_CATEGORIES if c["pillar"] == "pillar_element"]
    biomes = [c for c in LORE_CATEGORIES if c["pillar"] == "pillar_biome"]
    classes = [c for c in LORE_CATEGORIES if c["pillar"] == "pillar_class"]

    if difficulty == "relaxed":
        picked = (
            rng.sample(elements, 2)
            + rng.sample(biomes, 2)
            + rng.sample(classes, 2)
        )
        words_per_cat = 4
        receptacles = 4
        columns = 5
        turns = 70
    else:
        picked = (
            rng.sample(elements, 3)
            + rng.sample(biomes, 2)
            + rng.sample(classes, 2)
        )
        words_per_cat = 4
        receptacles = 3
        columns = 6
        turns = 74

    rng.shuffle(picked)
    return {
        "level": 0,
        "title": "Endless Mana Weaver",
        "subtitle": "A newly woven tapestry of Elements, Biomes, and Classes.",
        "num_receptacles": receptacles,
        "num_columns": columns,
        "words_per_category": words_per_cat,
        "max_turns": turns,
        "categories": [c["id"] for c in picked],
    }

