"""
Main entry point for Echoes of Fa'Diel: A Mana Associations Journey.
Run with:
    python main.py
"""

import sys
import pygame

from src.assets_manager import AssetManager, FontManager
from src.config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, WINDOW_TITLE
from src.game_scene import GameScene
from src.renderer import LayeredRenderer


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    fonts = FontManager()
    assets = AssetManager(fonts)
    # Export reference PNG templates to assets/sprites/templates/ on first run
    assets.export_sprite_templates()

    renderer = LayeredRenderer(assets, fonts)
    scene = GameScene(assets, fonts, renderer)

    running = True
    while running:
        dt = min(0.05, clock.tick(FPS) / 1000.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                scene.handle_event(event)

        scene.update(dt)
        scene.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()

