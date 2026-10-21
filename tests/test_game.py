"""
Automated verification tests for Echoes of Fa'Diel: A Mana Associations Journey.
Tests asset management, layered surface rendering, and Solitaire Associations puzzle logic.
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

    def test_solitaire_associations_mechanics(self):
        scene = GameScene(self.assets, self.fonts, self.renderer)
        pool = scene.receptacles[0]
        self.assertTrue(pool.is_empty)

        # Create a test category keystone and 3 matching word pebbles, plus 1 non-matching word pebble
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


if __name__ == "__main__":
    unittest.main()
