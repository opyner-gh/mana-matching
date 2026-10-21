"""
AssetManager and FontManager for Echoes of Fa'Diel.
Supports:
- Custom PNG sprites for pebbles/runes, keystones, and magical receptacles
- Procedural hand-drawn fantasy stone/pool surface generation as fallback
- Exporting reference PNG templates so artists can paint custom sprites later
- Custom .ttf / .otf font loading from assets/fonts/ with graceful fallback
"""

import math
import os
import pygame

from src.config import (
    BG_DIR,
    FONT_CONFIG,
    FONTS_DIR,
    ICON_SPRITES_DIR,
    KEYSTONE_HEIGHT,
    KEYSTONE_WIDTH,
    PALETTE,
    PEBBLE_HEIGHT,
    PEBBLE_SPRITES_DIR,
    PEBBLE_WIDTH,
    RECEPTACLE_HEIGHT,
    RECEPTACLE_SPRITES_DIR,
    RECEPTACLE_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEMPLATES_DIR,
)


class FontManager:
    """
    Manages custom .ttf/.otf fonts in assets/fonts/ with automatic discovery
    and fallback to classic storybook serif fonts.
    """

    def __init__(self):
        pygame.font.init()
        self._cache = {}
        self._discovered_custom_fonts = self._scan_custom_fonts()

    def _scan_custom_fonts(self):
        found = {}
        if not os.path.isdir(FONTS_DIR):
            return found

        all_ttf_files = [
            f for f in os.listdir(FONTS_DIR)
            if f.lower().endswith((".ttf", ".otf"))
        ]

        for role, cfg in FONT_CONFIG.items():
            for candidate in cfg["custom_files"]:
                full_path = os.path.join(FONTS_DIR, candidate)
                if os.path.isfile(full_path):
                    found[role] = full_path
                    break
            # If the user dropped any single custom font into assets/fonts/, use it!
            if role not in found and all_ttf_files:
                found[role] = os.path.join(FONTS_DIR, all_ttf_files[0])
        return found

    def reload_fonts(self):
        """Re-scans assets/fonts/ and clears the font cache."""
        self._cache.clear()
        self._discovered_custom_fonts = self._scan_custom_fonts()

    def get(self, role: str, size: int) -> pygame.font.Font:
        key = (role, size)
        if key in self._cache:
            return self._cache[key]

        cfg = FONT_CONFIG.get(role, FONT_CONFIG["ui"])
        font_obj = None

        # 1. Try custom font file in assets/fonts/
        if role in self._discovered_custom_fonts:
            try:
                font_obj = pygame.font.Font(self._discovered_custom_fonts[role], size)
            except Exception:
                font_obj = None

        # 2. Fallback to system serif/fantasy fonts
        if font_obj is None:
            fallback_names = ",".join(cfg["system_fallbacks"])
            font_obj = pygame.font.SysFont(fallback_names, size, bold=cfg.get("bold", False))

        self._cache[key] = font_obj
        return font_obj

    def render_text_with_shadow(
        self,
        role: str,
        size: int,
        text: str,
        color: tuple,
        shadow_color: tuple = (22, 16, 12),
        shadow_offset: tuple = (1, 2),
    ) -> pygame.Surface:
        """Renders crisp anti-aliased text with a soft storybook drop shadow."""
        font = self.get(role, size)
        fg = font.render(text, True, color)
        sh = font.render(text, True, shadow_color)

        w = fg.get_width() + abs(shadow_offset[0]) + 2
        h = fg.get_height() + abs(shadow_offset[1]) + 2
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.blit(sh, (max(0, shadow_offset[0]), max(0, shadow_offset[1])))
        surf.blit(fg, (max(0, -shadow_offset[0]), max(0, -shadow_offset[1])))
        return surf


class AssetManager:
    """
    Loads custom PNG sprites for pebbles, keystones, and receptacles when present,
    and otherwise generates hand-crafted layered surfaces with organic stone shapes,
    carved runes, moss accents, and shimmering water pools.
    """

    def __init__(self, font_manager: FontManager):
        self.fonts = font_manager
        self._surface_cache = {}
        self.custom_sprites_loaded = set()
        self.background_surface = None
        self._load_background()
        self._prebuild_base_surfaces()

    def _load_background(self):
        bg_candidates = [
            os.path.join(BG_DIR, "mana_valley.jpg"),
            os.path.join(BG_DIR, "background.png"),
            os.path.join(BG_DIR, "background.jpg"),
        ]
        if os.path.isdir(BG_DIR):
            for fname in os.listdir(BG_DIR):
                if fname.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    bg_candidates.append(os.path.join(BG_DIR, fname))

        loaded_img = None
        for path in bg_candidates:
            if os.path.isfile(path):
                try:
                    raw = pygame.image.load(path)
                    if pygame.display.get_surface() is not None:
                        raw = raw.convert()
                    loaded_img = pygame.transform.smoothscale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    break
                except Exception:
                    continue

        if loaded_img is None:
            # Fallback painted gradient if image is missing
            loaded_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                t = y / SCREEN_HEIGHT
                r = int(68 * (1 - t) + 38 * t)
                g = int(96 * (1 - t) + 64 * t)
                b = int(78 * (1 - t) + 46 * t)
                pygame.draw.line(loaded_img, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Apply a subtle storybook warm glaze so UI and runes stay readable
        # while keeping the lush background artwork vibrant
        glaze = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Top bar subtle darkening for header & pools
        for y in range(210):
            alpha = int(72 * (1.0 - (y / 210.0) ** 1.4))
            pygame.draw.line(glaze, (24, 20, 16, alpha), (0, y), (SCREEN_WIDTH, y))
        # Subtle lower-board contrast veil
        pygame.draw.rect(
            glaze,
            (22, 26, 20, 32),
            pygame.Rect(36, 200, SCREEN_WIDTH - 72, SCREEN_HEIGHT - 220),
            border_radius=22,
        )
        loaded_img.blit(glaze, (0, 0))
        self.background_surface = loaded_img

    def _try_load_custom_png(self, directory: str, filenames: list, target_size: tuple):
        """Checks a list of candidate PNG filenames in `directory` and scales if found."""
        if not os.path.isdir(directory):
            return None
        for fname in filenames:
            path = os.path.join(directory, fname)
            if os.path.isfile(path):
                try:
                    surf = pygame.image.load(path)
                    if pygame.display.get_surface() is not None:
                        surf = surf.convert_alpha()
                    if surf.get_size() != target_size:
                        surf = pygame.transform.smoothscale(surf, target_size)
                    self.custom_sprites_loaded.add(path)
                    return surf
                except Exception:
                    continue
        return None

    def _prebuild_base_surfaces(self):
        """Builds or loads base sprite surfaces for pebbles, keystones, and receptacles."""
        # 1. Veiled (face-down) pebble
        veiled = self._try_load_custom_png(
            PEBBLE_SPRITES_DIR,
            ["pebble_veiled.png", "veiled.png", "card_back.png"],
            (PEBBLE_WIDTH, PEBBLE_HEIGHT),
        )
        if veiled is None:
            veiled = self._generate_veiled_pebble_surface()
        self._surface_cache["pebble_veiled"] = veiled

        # 2. Word pebbles & Keystone runes per pillar
        for pillar in ("pillar_element", "pillar_biome", "pillar_class"):
            short = pillar.replace("pillar_", "")
            word_surf = self._try_load_custom_png(
                PEBBLE_SPRITES_DIR,
                [f"pebble_word_{short}.png", f"pebble_{short}.png", "pebble_word.png"],
                (PEBBLE_WIDTH, PEBBLE_HEIGHT),
            )
            if word_surf is None:
                word_surf = self._generate_word_pebble_surface(pillar)
            self._surface_cache[f"pebble_word_{pillar}"] = word_surf

            key_surf = self._try_load_custom_png(
                PEBBLE_SPRITES_DIR,
                [f"pebble_keystone_{short}.png", f"keystone_{short}.png", "pebble_keystone.png"],
                (KEYSTONE_WIDTH, KEYSTONE_HEIGHT),
            )
            if key_surf is None:
                key_surf = self._generate_keystone_surface(pillar)
            self._surface_cache[f"pebble_keystone_{pillar}"] = key_surf

            rec_active = self._try_load_custom_png(
                RECEPTACLE_SPRITES_DIR,
                [f"receptacle_{short}.png", "receptacle_active.png", "receptacle.png"],
                (RECEPTACLE_WIDTH, RECEPTACLE_HEIGHT),
            )
            if rec_active is None:
                rec_active = self._generate_receptacle_surface(pillar=pillar)
            self._surface_cache[f"receptacle_{pillar}"] = rec_active

        # 3. Empty Magical Pool / Receptacle
        rec_empty = self._try_load_custom_png(
            RECEPTACLE_SPRITES_DIR,
            ["receptacle_empty.png", "pool_empty.png", "receptacle.png"],
            (RECEPTACLE_WIDTH, RECEPTACLE_HEIGHT),
        )
        if rec_empty is None:
            rec_empty = self._generate_receptacle_surface(pillar=None)
        self._surface_cache["receptacle_empty"] = rec_empty

        # 4. Mana Spring (Stock) & Divination Basin (Waste) bases
        spring_surf = self._try_load_custom_png(
            RECEPTACLE_SPRITES_DIR,
            ["mana_spring.png", "stock_pool.png"],
            (PEBBLE_WIDTH + 16, PEBBLE_HEIGHT + 28),
        )
        if spring_surf is None:
            spring_surf = self._generate_spring_base_surface(is_spring=True)
        self._surface_cache["mana_spring_base"] = spring_surf

        basin_surf = self._try_load_custom_png(
            RECEPTACLE_SPRITES_DIR,
            ["divination_basin.png", "waste_pool.png"],
            (PEBBLE_WIDTH + 16, PEBBLE_HEIGHT + 28),
        )
        if basin_surf is None:
            basin_surf = self._generate_spring_base_surface(is_spring=False)
        self._surface_cache["divination_basin_base"] = basin_surf

    def get_surface(self, key: str) -> pygame.Surface:
        return self._surface_cache[key]

    # =========================================================================
    # PROCEDURAL HAND-DRAWN FANTASY SURFACE GENERATORS
    # =========================================================================

    def _draw_organic_pebble_polygon(self, w: int, h: int, inset: int = 0) -> list:
        """Returns vertices for an organic, slightly faceted river-stone / runestone shape."""
        cx, cy = w / 2.0, h / 2.0
        rx = (w / 2.0) - inset - 3
        ry = (h / 2.0) - inset - 3
        pts = []
        num_pts = 28
        for i in range(num_pts):
            ang = (2 * math.pi * i) / num_pts
            # Squircle / superellipse blend for a smooth carved stone feel
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            # Subtle organic asymmetry
            wobble = 1.0 + 0.025 * math.sin(3 * ang + 0.6) - 0.018 * math.cos(5 * ang)
            px = cx + rx * (abs(cos_a) ** 0.72) * (1 if cos_a >= 0 else -1) * wobble
            py = cy + ry * (abs(sin_a) ** 0.78) * (1 if sin_a >= 0 else -1) * wobble
            pts.append((px, py))
        return pts

    def _generate_veiled_pebble_surface(self) -> pygame.Surface:
        """Generates a moss-draped dormant rune pebble with a glowing mana spiral."""
        w, h = PEBBLE_WIDTH, PEBBLE_HEIGHT
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Drop shadow
        shadow_pts = [(x + 2, y + 3) for (x, y) in self._draw_organic_pebble_polygon(w, h, inset=1)]
        pygame.draw.polygon(surf, (14, 18, 15, 160), shadow_pts)

        # Outer stone body
        outer_pts = self._draw_organic_pebble_polygon(w, h, inset=2)
        pygame.draw.polygon(surf, (58, 66, 60, 248), outer_pts)

        # Inner stone bevel
        inner_pts = self._draw_organic_pebble_polygon(w, h, inset=6)
        pygame.draw.polygon(surf, (74, 84, 76, 255), inner_pts)

        # Moss patches along top-left and bottom-right
        pygame.draw.circle(surf, (92, 136, 74, 210), (26, 18), 11)
        pygame.draw.circle(surf, (118, 164, 86, 190), (35, 14), 7)
        pygame.draw.circle(surf, (84, 128, 68, 200), (w - 28, h - 16), 10)
        pygame.draw.circle(surf, (112, 156, 82, 180), (w - 38, h - 13), 6)

        # Glowing dormant mana sigil in center
        cx, cy = w // 2, h // 2
        pygame.draw.circle(surf, (110, 215, 198, 75), (cx, cy), 16, width=2)
        pygame.draw.circle(surf, (150, 240, 220, 140), (cx, cy), 10, width=1)
        # Diamond rune inside
        diamond = [(cx, cy - 9), (cx + 9, cy), (cx, cy + 9), (cx - 9, cy)]
        pygame.draw.polygon(surf, (140, 232, 212, 155), diamond, width=2)
        pygame.draw.circle(surf, (190, 255, 240, 210), (cx, cy), 3)

        # Inked hand-drawn outline
        pygame.draw.polygon(surf, (30, 36, 32, 245), outer_pts, width=2)
        return surf

    def _generate_word_pebble_surface(self, pillar: str) -> pygame.Surface:
        """Generates an engraved river-stone word rune tinted by its Lore Pillar."""
        w, h = PEBBLE_WIDTH, PEBBLE_HEIGHT
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        p_cfg = PALETTE[pillar]

        # Soft shadow
        shadow_pts = [(x + 2, y + 4) for (x, y) in self._draw_organic_pebble_polygon(w, h, inset=1)]
        pygame.draw.polygon(surf, (16, 14, 12, 175), shadow_pts)

        # Stone rim
        outer_pts = self._draw_organic_pebble_polygon(w, h, inset=2)
        pygame.draw.polygon(surf, p_cfg["stone_fill"], outer_pts)

        # Carved upper highlight bevel
        mid_pts = self._draw_organic_pebble_polygon(w, h, inset=5)
        pygame.draw.polygon(surf, p_cfg["stone_highlight"], mid_pts)

        # Warm parchment-stone tablet face in the center for high contrast word reading
        face_rect = pygame.Rect(12, 10, w - 24, h - 20)
        pygame.draw.rect(surf, (238, 229, 208), face_rect, border_radius=18)
        pygame.draw.rect(surf, (224, 212, 186), face_rect.inflate(-4, -4), border_radius=15)

        # Colored runic border around the tablet face
        pygame.draw.rect(surf, p_cfg["stone_border"], face_rect, width=2, border_radius=18)

        # Small corner mana studs
        for sx, sy in [(20, 18), (w - 20, 18), (20, h - 18), (w - 20, h - 18)]:
            pygame.draw.circle(surf, p_cfg["gem"], (sx, sy), 3)
            pygame.draw.circle(surf, (45, 36, 28), (sx, sy), 3, width=1)

        # Hand-inked outer stone contour
        pygame.draw.polygon(surf, (32, 26, 22, 250), outer_pts, width=2)
        return surf

    def _generate_keystone_surface(self, pillar: str) -> pygame.Surface:
        """Generates an ornate faceted Keystone Rune (Category Foundation card)."""
        w, h = KEYSTONE_WIDTH, KEYSTONE_HEIGHT
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        p_cfg = PALETTE[pillar]

        # Octagonal/faceted crest points
        def crest_pts(inset):
            l, r = 4 + inset, w - 4 - inset
            t, b = 4 + inset, h - 4 - inset
            cut_x, cut_y = 18, 14
            return [
                (l + cut_x, t),
                (r - cut_x, t),
                (r, t + cut_y),
                (r, b - cut_y),
                (r - cut_x, b),
                (l + cut_x, b),
                (l, b - cut_y),
                (l, t + cut_y),
            ]

        # Drop shadow
        sh_pts = [(x + 2, y + 4) for (x, y) in crest_pts(0)]
        pygame.draw.polygon(surf, (14, 12, 10, 190), sh_pts)

        # Golden-bronze outer filigree frame
        outer = crest_pts(1)
        pygame.draw.polygon(surf, PALETTE["gold_rim"], outer)
        pygame.draw.polygon(surf, PALETTE["gold_bright"], crest_pts(3), width=2)

        # Rich dark-tinted inner sanctuary plate
        inner = crest_pts(6)
        pygame.draw.polygon(surf, p_cfg["stone_fill"], inner)
        pygame.draw.polygon(surf, p_cfg["stone_border"], inner, width=2)

        # Top crown jewel accent
        cx = w // 2
        crown_diamond = [(cx, 3), (cx + 7, 10), (cx, 17), (cx - 7, 10)]
        pygame.draw.polygon(surf, p_cfg["gem"], crown_diamond)
        pygame.draw.polygon(surf, PALETTE["gold_bright"], crown_diamond, width=1)

        # Hand-inked outline
        pygame.draw.polygon(surf, (28, 22, 18, 255), outer, width=2)
        return surf

    def _generate_receptacle_surface(self, pillar=None) -> pygame.Surface:
        """
        Generates a stone-rimmed Magical Pool / Receptacle with mossy stones
        and a translucent shimmering water basin.
        """
        w, h = RECEPTACLE_WIDTH, RECEPTACLE_HEIGHT
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        rect = pygame.Rect(4, 6, w - 8, h - 10)
        # Outer shadow
        pygame.draw.ellipse(surf, (12, 16, 14, 165), rect.move(2, 5))

        # Ancient carved stone basin rim (ring of overlapping river stones)
        pygame.draw.ellipse(surf, PALETTE["stone_dark"], rect)
        pygame.draw.ellipse(surf, PALETTE["stone_base"], rect.inflate(-4, -4))
        pygame.draw.ellipse(surf, PALETTE["stone_light"], rect.inflate(-8, -8), width=3)

        # Individual carved rim notches around the stone basin
        cx, cy = w // 2, h // 2
        rx, ry = (w - 16) / 2.0, (h - 20) / 2.0
        for i in range(12):
            ang = (2 * math.pi * i) / 12
            nx = int(cx + rx * math.cos(ang))
            ny = int(cy + ry * math.sin(ang))
            pygame.draw.circle(surf, (46, 52, 48), (nx, ny), 3)

        # Moss clusters on the stone rim
        for mx, my, mr in [(26, 22, 9), (36, 16, 6), (w - 28, h - 22, 8), (24, h - 26, 7), (w - 32, 20, 7)]:
            pygame.draw.circle(surf, (88, 134, 72, 220), (mx, my), mr)
            pygame.draw.circle(surf, (126, 174, 92, 190), (mx - 2, my - 2), max(3, mr - 3))

        # Inner Magical Water Pool
        water_rect = rect.inflate(-24, -22)
        if pillar is None:
            # Calm un-consecrated spring water
            pygame.draw.ellipse(surf, (34, 72, 88, 215), water_rect)
            pygame.draw.ellipse(surf, (58, 114, 132, 195), water_rect.inflate(-10, -8))
            pygame.draw.ellipse(surf, (125, 204, 214, 110), water_rect.inflate(-28, -22), width=2)
        else:
            p_cfg = PALETTE[pillar]
            wt = p_cfg["water_tint"]
            pygame.draw.ellipse(surf, (wt[0] // 2, wt[1] // 2, wt[2] // 2, 230), water_rect)
            pygame.draw.ellipse(surf, (wt[0], wt[1], wt[2], 210), water_rect.inflate(-10, -8))
            pygame.draw.ellipse(surf, (*p_cfg["glow"], 155), water_rect.inflate(-2, -2), width=2)

        # Outer inked outline
        pygame.draw.ellipse(surf, (26, 30, 28, 245), rect, width=2)
        return surf

    def _generate_spring_base_surface(self, is_spring: bool) -> pygame.Surface:
        """Generates the stone cradle for the Mana Spring (Stock) and Divination Basin (Waste)."""
        w, h = PEBBLE_WIDTH + 16, PEBBLE_HEIGHT + 28
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        rect = pygame.Rect(4, 4, w - 8, h - 8)

        pygame.draw.rect(surf, (16, 20, 18, 150), rect.move(2, 4), border_radius=24)
        if is_spring:
            pygame.draw.rect(surf, (46, 68, 66, 215), rect, border_radius=24)
            pygame.draw.rect(surf, (108, 208, 196, 180), rect.inflate(-6, -6), width=2, border_radius=20)
        else:
            pygame.draw.rect(surf, (56, 52, 46, 190), rect, border_radius=24)
            pygame.draw.rect(surf, (168, 148, 116, 160), rect.inflate(-6, -6), width=2, border_radius=20)
        pygame.draw.rect(surf, (28, 32, 28, 230), rect, width=2, border_radius=24)
        return surf

    def draw_symbol_icon(self, surface: pygame.Surface, symbol: str, center: tuple, size: int, color: tuple):
        """
        Draws a crisp hand-drawn style lore icon (or blits a custom icon PNG from assets/sprites/icons/).
        """
        custom_icon = self._try_load_custom_png(
            ICON_SPRITES_DIR,
            [f"{symbol}.png", f"icon_{symbol}.png"],
            (size * 2, size * 2),
        )
        if custom_icon is not None:
            rect = custom_icon.get_rect(center=center)
            surface.blit(custom_icon, rect)
            return

        cx, cy = center
        r = size
        if symbol in ("spirit", "flame", "spark"):
            pts = [(cx, cy - r), (cx + r * 0.65, cy + r * 0.2), (cx, cy + r), (cx - r * 0.65, cy + r * 0.2)]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.circle(surface, (255, 248, 220), (cx, cy + 1), max(2, r // 3))
        elif symbol in ("tree", "leaf", "mushroom"):
            pygame.draw.circle(surface, color, (cx, cy - 2), int(r * 0.75))
            pygame.draw.line(surface, color, (cx, cy), (cx, cy + r), 2)
        elif symbol in ("sword", "staff", "crest", "anvil"):
            pygame.draw.line(surface, color, (cx, cy - r), (cx, cy + r), 2)
            pygame.draw.line(surface, color, (cx - r * 0.6, cy - r * 0.2), (cx + r * 0.6, cy - r * 0.2), 2)
            pygame.draw.circle(surface, color, (cx, cy - r), 2)
        elif symbol in ("book", "arch", "ruin", "portal"):
            rect = pygame.Rect(cx - int(r * 0.7), cy - int(r * 0.7), int(r * 1.4), int(r * 1.4))
            pygame.draw.rect(surface, color, rect, width=2, border_top_left_radius=r, border_top_right_radius=r)
        else:
            # Star / Gem / Dice / Moon sigil
            pts = [
                (cx, cy - r),
                (cx + int(r * 0.35), cy - int(r * 0.35)),
                (cx + r, cy),
                (cx + int(r * 0.35), cy + int(r * 0.35)),
                (cx, cy + r),
                (cx - int(r * 0.35), cy + int(r * 0.35)),
                (cx - r, cy),
                (cx - int(r * 0.35), cy - int(r * 0.35)),
            ]
            pygame.draw.polygon(surface, color, pts)

    def export_sprite_templates(self):
        """
        Exports the procedural pebble, keystone, and receptacle surfaces to
        assets/sprites/templates/ so an artist can easily paint over them or drop
        replacements into assets/sprites/pebbles/ and assets/sprites/receptacles/.
        """
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        exports = {
            "pebble_veiled.png": self._surface_cache["pebble_veiled"],
            "pebble_word_element.png": self._surface_cache["pebble_word_pillar_element"],
            "pebble_word_biome.png": self._surface_cache["pebble_word_pillar_biome"],
            "pebble_word_class.png": self._surface_cache["pebble_word_pillar_class"],
            "pebble_keystone_element.png": self._surface_cache["pebble_keystone_pillar_element"],
            "pebble_keystone_biome.png": self._surface_cache["pebble_keystone_pillar_biome"],
            "pebble_keystone_class.png": self._surface_cache["pebble_keystone_pillar_class"],
            "receptacle_empty.png": self._surface_cache["receptacle_empty"],
            "receptacle_element.png": self._surface_cache["receptacle_pillar_element"],
            "receptacle_biome.png": self._surface_cache["receptacle_pillar_biome"],
            "receptacle_class.png": self._surface_cache["receptacle_pillar_class"],
        }
        for filename, surf in exports.items():
            out_path = os.path.join(TEMPLATES_DIR, filename)
            if not os.path.isfile(out_path):
                pygame.image.save(surf, out_path)

