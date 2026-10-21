# Custom PNG Sprites Guide

`Echoes of Fa'Diel` automatically detects and loads custom `.png` sprites dropped into the subfolders below.
Reference templates with exact pixel dimensions and transparency are automatically exported to `assets/sprites/templates/` when you run the game.

## 1. Pebble & Keystone Runes (`assets/sprites/pebbles/`)
- **Veiled (Face-down) Pebble** (`148 x 68` px):
  - `pebble_veiled.png`
- **Word Pebbles** (`148 x 68` px):
  - `pebble_word_element.png` (Magical Elements pillar)
  - `pebble_word_biome.png` (Mythical Biomes pillar)
  - `pebble_word_class.png` (Character Classes & Relics pillar)
  - Or a single shared `pebble_word.png`
- **Category Keystone Runes** (`152 x 76` px):
  - `pebble_keystone_element.png`
  - `pebble_keystone_biome.png`
  - `pebble_keystone_class.png`
  - Or a single shared `pebble_keystone.png`

## 2. Magical Pools / Receptacles (`assets/sprites/receptacles/`)
- **Empty Sacred Pool** (`178 x 116` px):
  - `receptacle_empty.png`
- **Consecrated Sacred Pools** (`178 x 116` px):
  - `receptacle_element.png`
  - `receptacle_biome.png`
  - `receptacle_class.png`
  - Or a single shared `receptacle_active.png`
- **Mana Spring & Divination Basin Bases** (`164 x 96` px):
  - `mana_spring.png`
  - `divination_basin.png`

