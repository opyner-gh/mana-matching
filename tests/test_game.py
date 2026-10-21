"""
Automated verification tests for Echoes of Fa'Diel: A Mana Associations Journey.
Tests asset management, layered surface rendering, cross-level cache invalidation,
Wave-Stratified deal balance, and Solitaire Associations puzzle logic.
"""

import os
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.assets_manager import AssetManager, FontManager
from src.config import SCREEN_HEIGHT, SCREEN_WIDTH, TEMPLATES_DIR
from src.entities import RunePebble
from src.game_scene import GameScene
from src.lore_data import JOURNEY_CHAPTERS
from src.renderer import LayeredRenderer


class TestManaMatchingGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        cls.fonts = FontManager()
        cls.assets = AssetManager(cls.fonts)
        cls.assets.export_sprite_templates()
        cls.renderer = LayeredRenderer(cls.assets, cls.fonts)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_assets_and_templates_exported(self):
        self.assertIsNotNone(self.assets.background_surface)
        self.assertEqual(self.assets.background_surface.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        expected_templates = [
            "pebble_veiled.png",
            "pebble_word_element.png",
            "pebble_word_biome.png",
            "pebble_word_class.png",
            "pebble_keystone_element.png",
            "receptacle_empty.png",
            "receptacle_element.png",
        ]
        for fname in expected_templates:
            self.assertTrue(os.path.isfile(os.path.join(TEMPLATES_DIR, fname)), f"Missing template {fname}")

    def test_layered_surfaces_pipeline(self):
        scene = GameScene(self.assets, self.fonts, self.renderer)
        scene.update(0.016)
        scene.render(self.screen)
        self.assertEqual(self.renderer.bg_layer.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assertEqual(self.renderer.receptacle_layer.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assertEqual(self.renderer.pebble_layer.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assertEqual(self.renderer.drag_and_fx_layer.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assertEqual(self.renderer.hud_layer.get_size(), (SCREEN_WIDTH, SCREEN_HEIGHT))

    def test_level_transition_clears_pebble_cache_and_matches_categories(self):
        """
        Verifies that transitioning from Level 1 to Level 2 clears the pebble surface
        cache and that all stones dealt in every chapter strictly match that chapter's categories.
        """
        scene = GameScene(self.assets, self.fonts, self.renderer)
        # Reveal all stones in Level 1 and render so _pebble_render_cache is populated
        for col in scene.tableau:
            for p in col:
                p.reveal()
        scene.render(self.screen)
        self.assertGreater(len(self.renderer._pebble_render_cache), 0)

        # Now load Level 2 (index 1)
        scene.load_chapter(1)
        self.assertEqual(len(self.renderer._pebble_render_cache), 0)

        # Verify all capítulos (Levels 1..5) have 100% matching Keystones and Words
        for ch_idx in range(len(JOURNEY_CHAPTERS)):
            scene.load_chapter(ch_idx)
            expected_cats = set(JOURNEY_CHAPTERS[ch_idx]["categories"])
            words_per_cat = JOURNEY_CHAPTERS[ch_idx]["words_per_category"]

            all_stones = list(scene.stock) + list(scene.waste)
            for col in scene.tableau:
                all_stones.extend(col)

            keystones = [p for p in all_stones if p.is_keystone]
            words = [p for p in all_stones if not p.is_keystone]

            self.assertEqual({k.category_id for k in keystones}, expected_cats)
            self.assertEqual({w.category_id for w in words}, expected_cats)
            self.assertEqual(len(keystones), len(expected_cats))
            self.assertEqual(len(words), len(expected_cats) * words_per_cat)

            # Verify Wave 1 Keystones are present on the revealed Tableau tips at start
            revealed_tips = [col[-1] for col in scene.tableau if col]
            tip_keystones = [p for p in revealed_tips if p.is_keystone]
            self.assertGreaterEqual(len(tip_keystones), 2)

    def test_solitaire_associations_mechanics_and_cairn_harmonization(self):
        scene = GameScene(self.assets, self.fonts, self.renderer)
        pool = scene.receptacles[0]
        self.assertTrue(pool.is_empty)

        keystone = RunePebble(
            uid=900,
            category_id="mana_spirits",
            category_title="Fa'Diel Mana Spirits",
            pillar="pillar_element",
            symbol="spirit",
            origin="Legend of Mana",
            word="Fa'Diel Mana Spirits",
            is_keystone=True,
            required_count=3,
            revealed=True,
        )
        w1 = RunePebble(901, "mana_spirits", "Fa'Diel Mana Spirits", "pillar_element", "spirit", "Legend of Mana", "Salamander", False, 3, True)
        w2 = RunePebble(902, "mana_spirits", "Fa'Diel Mana Spirits", "pillar_element", "spirit", "Legend of Mana", "Undine", False, 3, True)
        w3 = RunePebble(903, "mana_spirits", "Fa'Diel Mana Spirits", "pillar_element", "spirit", "Legend of Mana", "Jinn", False, 3, True)
        other_w = RunePebble(904, "myst_linking_ages", "Linking Book Ages", "pillar_biome", "book", "Myst", "Channelwood", False, 3, True)

        scene.tableau[0] = [w1]
        scene.tableau[1] = [w2]
        scene.tableau[2] = [other_w]
        scene.tableau[3] = [keystone]
        scene.tableau[4] = [w3]

        # 1. Word pebble cannot consecrate an empty pool
        self.assertFalse(pool.can_accept_cluster([w1]))

        # 2. Discordant word pebble cannot stack on a different category
        self.assertFalse(scene.can_stack_on_column([other_w], 0))

        # 3. Matching word pebbles CAN stack in tableau and form a Resonant Cluster of size 2
        self.assertTrue(scene.execute_move_to_column(("tableau", 1), [w2], 0))
        cluster_col0 = scene.get_movable_cluster_at_column(0)
        self.assertEqual(len(cluster_col0), 2)

        # 4. Keystone consecrates the empty Magical Pool
        self.assertTrue(scene.execute_move_to_pool(("tableau", 3), [keystone], pool))
        self.assertFalse(pool.is_empty)
        self.assertEqual(pool.category_id, "mana_spirits")

        # 5. Move the Resonant Cluster [w1, w2] into the consecrated pool at once!
        self.assertTrue(scene.execute_move_to_pool(("tableau", 0), cluster_col0, pool))
        self.assertEqual(pool.current_count, 2)

        # 6. Infuse final word pebble w3 -> Pool Harmonizes and resets to empty!
        self.assertTrue(scene.execute_move_to_pool(("tableau", 4), [w3], pool))
        self.assertTrue(pool.is_empty)
        self.assertEqual(len(scene.harmonized_categories), 1)
        self.assertEqual(scene.harmonized_categories[0]["id"], "mana_spirits")

        # 7. Test Undo restores pool prior to final infusion
        scene.perform_undo()
        self.assertFalse(scene.receptacles[0].is_empty)
        self.assertEqual(scene.receptacles[0].current_count, 2)

        # 8. Test that a column cluster cannot stack onto its own column
        self.assertFalse(scene.can_stack_on_column([other_w], 2))
        self.assertFalse(scene.try_auto_channel(("tableau", 2), [other_w]))

        # 9. Test direct Cairn Harmonization when Keystone + all required words combine on a Tableau column
        k_myst = RunePebble(910, "myst_linking_ages", "Linking Book Ages", "pillar_biome", "book", "Myst", "Linking Book Ages", True, 2, True)
        m1 = RunePebble(911, "myst_linking_ages", "Linking Book Ages", "pillar_biome", "book", "Myst", "Channelwood", False, 2, True)
        m2 = RunePebble(912, "myst_linking_ages", "Linking Book Ages", "pillar_biome", "book", "Myst", "Riven", False, 2, True)
        scene.tableau[0] = [k_myst]
        scene.tableau[1] = [m1]
        scene.tableau[2] = [m2]
        self.assertTrue(scene.execute_move_to_column(("tableau", 1), [m1], 0))
        # Keystone should remain at the visible tip of column 0
        self.assertTrue(scene.tableau[0][-1].is_keystone)
        # Moving final word m2 onto column 0 should automatically harmonize the cluster on the Cairn!
        self.assertTrue(scene.execute_move_to_column(("tableau", 2), [m2], 0))
        self.assertEqual(len(scene.tableau[0]), 0)
        self.assertEqual(scene.harmonized_categories[-1]["id"], "myst_linking_ages")


if __name__ == "__main__":
    unittest.main()
