# Echoes of Fa'Diel — A Mana Associations Journey

A hand-drawn fantasy word-matching solitaire puzzle game built in **Pygame**, emulating the strategic mechanics of *Solitaire Associations Journey* with a lush storybook aesthetic inspired by **Legend of Mana** and nostalgic 90s fantasy classics (**Magic: The Gathering**, **Dungeons & Dragons**, **Myst**, and **The Elder Scrolls III: Morrowind**).

---

## ✨ Features & Theme

- **Pebbles, Keystone Runes & Sacred Pools**: Instead of traditional playing cards, players channel engraved river-stone **Word Pebbles** and faceted **Keystone Runes** into stone-rimmed **Sacred Receptacles (Magical Pools)**.
- **Three Nostalgic Lore Pillars**:
  1. **Magical Elements**: *Fa'Diel Mana Spirits*, *Five Colors of Mana*, *90s Spellbook Classics*, *Schools of Arcane Magic*, *Mages Guild Disciplines*, *Vvardenfell Alchemy*, *Archmage Invocations*, and *Astral & Lunar Tides*.
  2. **Mythical Biomes**: *Vvardenfell Biomes*, *Ports & Strongholds*, *Linking Book Ages (Myst & Riven)*, *Sanctums of Fa'Diel*, *Sacred Lands of Mana*, *Planes & Sanctuaries*, *Forgotten Sanctuaries*, and *Great Wheel Cosmology*.
  3. **Character Classes & Relics**: *Vanguard Classes*, *Spellcaster & Rogue Arts*, *Houses & Guilds of Resdayn*, *Dungeon Denizens*, *Urza's & Vintage Relics*, *Wondrous D&D Treasure*, *Tabletop Guild Lexicon*, and *Watts' Forge Materials*.
- **5 Curated Journey Chapters + Endless Procedural Weaver**: Progress through five hand-crafted chapters or weave infinite randomized realms.
- **6-Layer Surface Pipeline**: Built with independent `pygame.Surface` layers for background art, ambient mana spores, sacred pools, tableau pebbles, active drag/ripple effects, and the storybook HUD/Grimoire.
- **Drop-In Custom PNG Sprites & Fonts**: Automatically loads custom `.png` sprites and `.ttf`/`.otf` fonts when placed in `assets/`, with procedural hand-drawn fallback rendering and exported PNG templates.

---

## 🎮 How to Play

1. **Consecrate a Sacred Pool**:
   - Sacred Pools (top-right) begin empty. Only a **Category Keystone Rune** (faceted gold-rimmed runestone) can be placed into an empty Sacred Pool to consecrate it.
2. **Bind Resonant Word Clusters**:
   - In the **Mossy Cairns (Tableau)** below, lower stones start **veiled** (moss-covered) and top stones are **revealed**.
   - You can stack revealed **Word Pebbles** onto each other in the Tableau **only if they share the exact same Lore Category**.
   - Matching pebbles stacked together fuse into a **Resonant Cluster** (displaying a `×2`, `×3` badge) and move together as one unit.
   - Moving a stone or cluster off a veiled stone automatically unveils it. Empty Cairns can hold any movable stone or cluster.
3. **Infuse & Harmonize**:
   - Move matching Word Pebbles (or an entire Resonant Cluster at once) into their consecrated Sacred Pool.
   - When a Sacred Pool collects all of its required runes (tracked by the socketed mana gems along the bottom rim of the pool), it **Harmonizes** in a burst of water ripples and mana spores, records the completed category in your **Grimoire**, grants **+4 bonus Mana Turns**, and **empties the Sacred Pool** so a new Keystone Rune can take its place.
4. **Mana Spring & Divination Basin**:
   - Click the **Mana Spring** (top-left) to draw veiled runes into the **Divination Basin**. When the Mana Spring is depleted, click it again to re-channel the Divination Basin back into the Spring.

### Controls & Shortcuts

| Input | Action |
| :--- | :--- |
| **Left-Click + Drag** | Drag a revealed pebble or Resonant Cluster to a Cairn or Sacred Pool |
| **Left-Click → Left-Click** | Select a pebble/cluster, then click a highlighted destination |
| **Double-Click / Right-Click** | **Auto-Channel** a revealed pebble/cluster to a valid Pool or resonant stack |
| **`Z`** | **Undo** the previous turn |
| **`H`** | **Hint** — highlights the highest-priority strategic move on the board |
| **`G`** | Toggle the **Lore Grimoire & Rules Compendium** |
| **`M`** | Open **Realm Select** (choose a Chapter or weave a Procedural Realm) |
| **`R`** | **Re-Deal** the current chapter |
| **`Esc`** | Close active modal overlay or clear current selection |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- `pygame` (2.5+)

### Installation & Running

```bash
# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install pygame if not already installed
pip install pygame

# Launch the game
python main.py
```

### Running Unit Tests

```bash
python tests/test_game.py -v
```

---

## 🎨 Custom PNG Sprites & Custom Fonts

### Adding Custom Sprites (`assets/sprites/`)
On first launch, reference PNG templates with exact pixel dimensions and alpha channels are exported to [`assets/sprites/templates/`](assets/sprites/templates/). To override the procedural art with your own illustrations, drop `.png` files into:

- **`assets/sprites/pebbles/`**:
  - `pebble_veiled.png` (`148×68` px)
  - `pebble_word_element.png`, `pebble_word_biome.png`, `pebble_word_class.png` (or shared `pebble_word.png`, `148×68` px)
  - `pebble_keystone_element.png`, `pebble_keystone_biome.png`, `pebble_keystone_class.png` (or shared `pebble_keystone.png`, `152×76` px)
- **`assets/sprites/receptacles/`**:
  - `receptacle_empty.png` (`178×116` px)
  - `receptacle_element.png`, `receptacle_biome.png`, `receptacle_class.png` (or shared `receptacle_active.png`, `178×116` px)
  - `mana_spring.png`, `divination_basin.png` (`164×96` px)

See [`assets/sprites/README.md`](assets/sprites/README.md) for full details.

### Adding Custom Fonts (`assets/fonts/`)
Drop any `.ttf` or `.otf` font file into [`assets/fonts/`](assets/fonts/).
- A single `.ttf`/`.otf` file in `assets/fonts/` will automatically be used across the game.
- Or provide role-specific fonts (`title.ttf`, `rune.ttf`, `keystone.ttf`, `lore.ttf`, `ui.ttf`). See [`assets/fonts/README.md`](assets/fonts/README.md).

---

## 📁 Project Structure

```text
mana-matching/
├── assets/
│   ├── backgrounds/
│   │   └── mana_valley.jpg        # Hand-drawn fantasy valley background
│   ├── fonts/
│   │   └── README.md              # Guide for dropping in custom .ttf/.otf fonts
│   └── sprites/
│       ├── pebbles/               # Drop custom pebble/keystone PNGs here
│       ├── receptacles/           # Drop custom pool/spring PNGs here
│       ├── icons/                 # Optional custom symbol icon PNGs
│       ├── templates/             # Auto-exported reference PNG templates
│       └── README.md              # Sprite naming & pixel dimensions guide
├── src/
│   ├── __init__.py
│   ├── config.py                  # Resolution, layout constants, palettes & font config
│   ├── lore_data.py               # 24 nostalgic categories, 5 chapters & procedural weaver
│   ├── assets_manager.py          # AssetManager & FontManager with PNG/TTF auto-discovery
│   ├── entities.py                # RunePebble, MagicalReceptacle, WaterRipple & ManaParticle
│   ├── renderer.py                # 6-layer pygame.Surface rendering pipeline
│   └── game_scene.py              # Solitaire Associations rules, input, undo, hints & modals
├── tests/
│   └── test_game.py               # Automated tests for assets, layers, and puzzle rules
└── main.py                        # Game entry point
```
