"""
LayeredRenderer for Echoes of Fa'Diel.
Implements a multi-surface rendering pipeline:
1. bg_layer          - Hand-drawn Legend of Mana style background art
2. ambient_fx_layer  - Floating mana spores and sunbeam shimmer
3. receptacle_layer  - Mana Spring, Divination Basin, Sacred Receptacles & Cairn bases
4. pebble_layer      - Veiled stones, engraved Word Pebbles, Keystones & Cluster badges
5. drag_and_fx_layer - Active dragged cluster, water ripples, particle bursts & banners
6. hud_layer         - Storybook HUD bar, buttons, bottom lore bar, and modal overlays
"""

import math
import pygame

from src.assets_manager import AssetManager, FontManager
from src.config import (
    KEYSTONE_HEIGHT,
    KEYSTONE_WIDTH,
    PALETTE,
    PEBBLE_HEIGHT,
    PEBBLE_WIDTH,
    RECEPTACLE_HEIGHT,
    RECEPTACLE_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STOCK_POS,
    WASTE_POS,
)
from src.entities import MagicalReceptacle, RunePebble
from src.lore_data import CATEGORY_BY_ID


class LayeredRenderer:
    """Manages independent pygame.Surface layers and composites them each frame."""

    def __init__(self, assets: AssetManager, fonts: FontManager):
        self.assets = assets
        self.fonts = fonts

        # Explicit Layered Surfaces
        self.bg_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.ambient_fx_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.receptacle_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.pebble_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.drag_and_fx_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.hud_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Cache for rendered pebble face surfaces keyed by (uid, revealed, is_highlighted, cluster_size)
        self._pebble_render_cache = {}

        # Initialize static background layer
        self.bg_layer.blit(self.assets.background_surface, (0, 0))

    def clear_pebble_cache(self):
        """Clears cached pebble surfaces when loading a new chapter or re-dealing."""
        self._pebble_render_cache.clear()

    def clear_dynamic_layers(self):
        self.ambient_fx_layer.fill((0, 0, 0, 0))
        self.receptacle_layer.fill((0, 0, 0, 0))
        self.pebble_layer.fill((0, 0, 0, 0))
        self.drag_and_fx_layer.fill((0, 0, 0, 0))
        self.hud_layer.fill((0, 0, 0, 0))

    def composite_to(self, target_surface: pygame.Surface):
        """Composites all 6 layers in back-to-front order onto the main screen."""
        target_surface.blit(self.bg_layer, (0, 0))
        target_surface.blit(self.ambient_fx_layer, (0, 0))
        target_surface.blit(self.receptacle_layer, (0, 0))
        target_surface.blit(self.pebble_layer, (0, 0))
        target_surface.blit(self.drag_and_fx_layer, (0, 0))
        target_surface.blit(self.hud_layer, (0, 0))

    # =========================================================================
    # TEXT WRAPPING & FORMATTING HELPERS
    # =========================================================================

    def _draw_wrapped_centered_text(
        self,
        surface: pygame.Surface,
        text: str,
        role: str,
        base_size: int,
        color: tuple,
        center_x: int,
        center_y: int,
        max_width: int,
        shadow_color: tuple | None = None,
    ):
        """Draws 1 or 2 lines of centered text scaled to fit neatly inside `max_width`."""
        font = self.fonts.get(role, base_size)
        single_w, _ = font.size(text)

        if single_w <= max_width or " " not in text:
            # Fit on 1 line, shrinking font slightly if needed
            sz = base_size
            while sz > 11 and self.fonts.get(role, sz).size(text)[0] > max_width:
                sz -= 1
            f = self.fonts.get(role, sz)
            if shadow_color:
                sh = f.render(text, True, shadow_color)
                surface.blit(sh, sh.get_rect(center=(center_x + 1, center_y + 1)))
            fg = f.render(text, True, color)
            surface.blit(fg, fg.get_rect(center=(center_x, center_y)))
            return

        # Split into 2 balanced lines
        words = text.split(" ")
        best_split = 1
        best_diff = 9999
        for i in range(1, len(words)):
            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:])
            diff = abs(len(l1) - len(l2))
            if diff < best_diff:
                best_diff = diff
                best_split = i
        line1 = " ".join(words[:best_split])
        line2 = " ".join(words[best_split:])

        sz = base_size - 1
        while sz > 11 and (
            self.fonts.get(role, sz).size(line1)[0] > max_width
            or self.fonts.get(role, sz).size(line2)[0] > max_width
        ):
            sz -= 1

        f = self.fonts.get(role, sz)
        line_gap = f.get_linesize() - 2
        y1 = center_y - line_gap // 2 + 1
        y2 = center_y + line_gap // 2

        for ly, ltxt in [(y1, line1), (y2, line2)]:
            if shadow_color:
                sh = f.render(ltxt, True, shadow_color)
                surface.blit(sh, sh.get_rect(center=(center_x + 1, ly + 1)))
            fg = f.render(ltxt, True, color)
            surface.blit(fg, fg.get_rect(center=(center_x, ly)))

    # =========================================================================
    # PEBBLE & KEYSTONE SURFACE RENDERING
    # =========================================================================

    def render_pebble_to_layer(
        self,
        layer: pygame.Surface,
        pebble: RunePebble,
        pos: tuple[int, int] | None = None,
        is_selected: bool = False,
        is_valid_target: bool = False,
        is_hinted: bool = False,
        cluster_count: int = 1,
        elevated: bool = False,
    ):
        """Renders a single Veiled Pebble, Word Pebble, or Keystone Rune onto `layer`."""
        rect = pebble.get_rect()
        x, y = pos if pos is not None else (rect.x, rect.y)
        w, h = pebble.width, pebble.height

        # Elevated drop shadow when dragging
        if elevated:
            shadow_surf = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (8, 10, 8, 130), (6, 10, w, h))
            layer.blit(shadow_surf, (x - 4, y + 6))

        # Highlight aura for selection, valid target, or hint
        if is_selected or is_valid_target or is_hinted:
            aura_surf = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
            if is_hinted:
                aura_col = (255, 230, 110, 195)
            elif is_valid_target:
                aura_col = (120, 248, 210, 180)
            else:
                aura_col = (255, 215, 125, 195)
            pygame.draw.rect(aura_surf, aura_col, (2, 2, w + 12, h + 12), width=3, border_radius=24)
            layer.blit(aura_surf, (x - 8, y - 8))

        if not pebble.revealed:
            base = self.assets.get_surface("pebble_veiled")
            layer.blit(base, (x, y))
            return

        # Cache static face of revealed pebble (keyed by full identity so chapters never collide)
        cache_key = (pebble.uid, pebble.category_id, pebble.word, pebble.revealed, pebble.is_keystone)
        if cache_key not in self._pebble_render_cache:
            face = pygame.Surface((w, h), pygame.SRCALPHA)
            p_cfg = PALETTE[pebble.pillar]
            cat_meta = CATEGORY_BY_ID.get(pebble.category_id, {})

            if pebble.is_keystone:
                base = self.assets.get_surface(f"pebble_keystone_{pebble.pillar}")
                face.blit(base, (0, 0))

                # Draw Keystone header tag ("KEYSTONE" + origin/pillar)
                tag_font = self.fonts.get("ui", 10)
                hint_short = cat_meta.get("hint_tag", p_cfg["name"]).upper()
                tag_surf = tag_font.render(f"• {hint_short} •", True, PALETTE["gold_bright"])
                face.blit(tag_surf, tag_surf.get_rect(center=(w // 2, 19)))

                # Category Title
                self._draw_wrapped_centered_text(
                    face,
                    pebble.category_title,
                    role="keystone_title",
                    base_size=14,
                    color=(255, 246, 224),
                    center_x=w // 2,
                    center_y=h // 2 + 3,
                    max_width=w - 30,
                    shadow_color=(20, 14, 10),
                )

                # Bottom crown indicator showing required words count
                req_font = self.fonts.get("ui", 11)
                req_txt = req_font.render(f"Pool Keystone ({pebble.required_count} Runes)", True, p_cfg["text_accent"])
                face.blit(req_txt, req_txt.get_rect(center=(w // 2, h - 13)))
            else:
                base = self.assets.get_surface(f"pebble_word_{pebble.pillar}")
                face.blit(base, (0, 0))

                # Small lore pillar icon on left of tablet
                self.assets.draw_symbol_icon(face, pebble.symbol, (25, h // 2), 6, p_cfg["stone_fill"])

                # Engraved Word text in center of tablet
                self._draw_wrapped_centered_text(
                    face,
                    pebble.word,
                    role="rune_word",
                    base_size=15,
                    color=PALETTE["ink_dark"],
                    center_x=w // 2 + 5,
                    center_y=h // 2 - 3,
                    max_width=w - 48,
                )

                # Specific hint_tag at bottom of tablet so players can distinguish categories clearly
                sub_font = self.fonts.get("lore", 10)
                sub_str = cat_meta.get("hint_tag", p_cfg["name"].split(" ")[-1])
                sub_surf = sub_font.render(sub_str, True, p_cfg["stone_fill"])
                face.blit(sub_surf, sub_surf.get_rect(center=(w // 2 + 5, h - 16)))

            self._pebble_render_cache[cache_key] = face

        layer.blit(self._pebble_render_cache[cache_key], (x, y))

        # If this pebble is the tip of a multi-rune Resonant Cluster, draw a glowing count badge at bottom-right
        if cluster_count > 1:
            badge_rect = pygame.Rect(x + w - 28, y + h - 22, 28, 20)
            pygame.draw.rect(layer, PALETTE["gold_rim"], badge_rect, border_radius=10)
            pygame.draw.rect(layer, (34, 24, 16), badge_rect.inflate(-3, -3), border_radius=8)
            b_font = self.fonts.get("ui", 11)
            b_txt = b_font.render(f"×{cluster_count}", True, PALETTE["gold_bright"])
            layer.blit(b_txt, b_txt.get_rect(center=badge_rect.center))

    # =========================================================================
    # MAGICAL RECEPTACLES (FOUNDATION POOLS) & STOCK/WASTE RENDERING
    # =========================================================================

    def render_receptacles_and_springs(
        self,
        receptacles: list[MagicalReceptacle],
        stock_count: int,
        waste_count: int,
        cairn_positions: list[tuple[int, int]],
        valid_pool_indices: set[int],
        valid_cairn_indices: set[int],
        time_sec: float,
    ):
        """Renders the Mana Spring, Divination Basin, Sacred Receptacles, and empty Cairn bases."""
        layer = self.receptacle_layer

        # 1. Mana Spring (Stock)
        spring_base = self.assets.get_surface("mana_spring_base")
        sx, sy = STOCK_POS
        layer.blit(spring_base, (sx - 8, sy - 14))

        lbl_font = self.fonts.get("ui", 11)
        s_lbl = lbl_font.render("MANA SPRING", True, PALETTE["mana_glow"])
        layer.blit(s_lbl, s_lbl.get_rect(center=(sx + PEBBLE_WIDTH // 2, sy - 22)))

        if stock_count > 0:
            # Stack effect for veiled pebbles in the spring
            stack_layers = min(3, stock_count)
            for i in range(stack_layers):
                veiled = self.assets.get_surface("pebble_veiled")
                layer.blit(veiled, (sx - i * 2, sy - i * 2))
            # Count pill
            cnt_rect = pygame.Rect(sx + PEBBLE_WIDTH - 34, sy + PEBBLE_HEIGHT - 16, 34, 20)
            pygame.draw.rect(layer, (26, 42, 40, 235), cnt_rect, border_radius=10)
            pygame.draw.rect(layer, PALETTE["mana_cyan"], cnt_rect, width=1, border_radius=10)
            c_txt = lbl_font.render(str(stock_count), True, PALETTE["mana_glow"])
            layer.blit(c_txt, c_txt.get_rect(center=cnt_rect.center))
        else:
            # Re-channel icon when empty
            cx, cy = sx + PEBBLE_WIDTH // 2, sy + PEBBLE_HEIGHT // 2
            pygame.draw.circle(layer, (110, 225, 215, 130), (cx, cy), 20, width=2)
            r_txt = lbl_font.render("Re-Channel" if waste_count > 0 else "Depleted", True, PALETTE["mana_glow"])
            layer.blit(r_txt, r_txt.get_rect(center=(cx, cy)))

        # 2. Divination Basin (Waste)
        basin_base = self.assets.get_surface("divination_basin_base")
        wx, wy = WASTE_POS
        layer.blit(basin_base, (wx - 8, wy - 14))
        w_lbl = lbl_font.render("DIVINATION BASIN", True, PALETTE["parchment_mid"])
        layer.blit(w_lbl, w_lbl.get_rect(center=(wx + PEBBLE_WIDTH // 2, wy - 22)))

        # 3. Sacred Receptacles (Magical Pools)
        for pool in receptacles:
            px, py = pool.x, pool.y
            w, h = RECEPTACLE_WIDTH, RECEPTACLE_HEIGHT

            if pool.is_empty:
                surf = self.assets.get_surface("receptacle_empty")
                layer.blit(surf, (px, py))

                # Gentle animated water shimmer ring
                shimmer_r = int(26 + 6 * math.sin(pool.pulse_phase))
                shimmer_rect = pygame.Rect(
                    px + w // 2 - shimmer_r,
                    py + h // 2 - int(shimmer_r * 0.6),
                    shimmer_r * 2,
                    int(shimmer_r * 1.2),
                )
                pygame.draw.ellipse(layer, (140, 230, 240, 75), shimmer_rect, width=1)

                # Prompt text inside empty pool
                p_font = self.fonts.get("lore", 12)
                t1 = p_font.render("Sacred Pool", True, (175, 230, 235))
                t2 = self.fonts.get("lore", 11).render("Place Keystone Rune", True, (135, 192, 200))
                layer.blit(t1, t1.get_rect(center=(px + w // 2, py + h // 2 - 8)))
                layer.blit(t2, t2.get_rect(center=(px + w // 2, py + h // 2 + 10)))
            else:
                p_cfg = PALETTE[pool.pillar]
                surf = self.assets.get_surface(f"receptacle_{pool.pillar}")
                layer.blit(surf, (px, py))

                # Animated elemental aura ring inside pool
                shimmer_r = int(52 + 4 * math.sin(pool.pulse_phase))
                shimmer_rect = pygame.Rect(
                    px + w // 2 - shimmer_r,
                    py + h // 2 - int(shimmer_r * 0.48),
                    shimmer_r * 2,
                    int(shimmer_r * 0.96),
                )
                pygame.draw.ellipse(layer, (*p_cfg["glow"], 55), shimmer_rect, width=1)

                # Soft dark water-depth plate so pool text is super crisp
                plate_rect = pygame.Rect(px + 24, py + 28, w - 48, 46)
                pygame.draw.rect(layer, (18, 16, 14, 125), plate_rect, border_radius=16)

                # Hint tag header matching the Word Pebble subtitle
                cat_meta = CATEGORY_BY_ID.get(pool.category_id, {})
                hint_tag = cat_meta.get("hint_tag", pool.keystone.origin).upper()
                orig_font = self.fonts.get("ui", 10)
                orig_surf = orig_font.render(f"• {hint_tag} •", True, PALETTE["gold_bright"])
                layer.blit(orig_surf, orig_surf.get_rect(center=(px + w // 2, py + 21)))

                # Category Title inside the consecrated pool
                self._draw_wrapped_centered_text(
                    layer,
                    pool.keystone.category_title,
                    role="keystone_title",
                    base_size=14,
                    color=(255, 248, 228),
                    center_x=px + w // 2,
                    center_y=py + h // 2 - 4,
                    max_width=w - 48,
                    shadow_color=(18, 14, 12),
                )

                # Latest infused word preview
                if pool.collected_pebbles:
                    last_word = pool.collected_pebbles[-1].word
                    w_font = self.fonts.get("lore", 11)
                    w_surf = w_font.render(f"• {last_word} •", True, PALETTE["gold_bright"])
                    layer.blit(w_surf, w_surf.get_rect(center=(px + w // 2, py + h // 2 + 18)))

                # Socketed Mana Progress Gems along bottom rim of the pool
                req = pool.required_count
                cur = pool.current_count
                gem_spacing = 18
                start_gx = px + w // 2 - ((req - 1) * gem_spacing) // 2
                gy = py + h - 18
                for gi in range(req):
                    gx = start_gx + gi * gem_spacing
                    pygame.draw.circle(layer, (26, 22, 20), (gx, gy), 6)
                    if gi < cur:
                        pygame.draw.circle(layer, p_cfg["gem"], (gx, gy), 5)
                        pygame.draw.circle(layer, (255, 245, 220), (gx - 1, gy - 1), 2)
                    else:
                        pygame.draw.circle(layer, (68, 72, 70), (gx, gy), 4)
                    pygame.draw.circle(layer, PALETTE["gold_rim"], (gx, gy), 6, width=1)

            # Highlight if this pool is a valid drop target for the currently selected/dragged cluster
            if pool.slot_index in valid_pool_indices:
                glow_alpha = int(150 + 65 * math.sin(time_sec * 6.0))
                pygame.draw.ellipse(
                    layer,
                    (140, 255, 215, glow_alpha),
                    pygame.Rect(px, py + 2, w, h - 4),
                    width=3,
                )

            # Flash overlay when a pool just harmonized
            if pool.harmonize_flash > 0:
                fl_alpha = int(200 * pool.harmonize_flash)
                fl_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.ellipse(fl_surf, (255, 240, 180, fl_alpha), (4, 6, w - 8, h - 10))
                layer.blit(fl_surf, (px, py))

        # 4. Tableau Cairn Base Stones (Mossy sanctuaries where columns rest)
        for idx, (cx, cy) in enumerate(cairn_positions):
            cairn_rect = pygame.Rect(cx, cy, PEBBLE_WIDTH, PEBBLE_HEIGHT)
            pygame.draw.rect(layer, (28, 36, 30, 115), cairn_rect, border_radius=20)
            pygame.draw.rect(layer, (96, 134, 84, 130), cairn_rect, width=2, border_radius=20)

            # Subtle carved rune circle inside empty cairn slot
            center = cairn_rect.center
            pygame.draw.circle(layer, (118, 158, 102, 75), center, 16, width=1)

            if idx in valid_cairn_indices:
                glow_alpha = int(140 + 60 * math.sin(time_sec * 6.0))
                pygame.draw.rect(
                    layer,
                    (140, 255, 215, glow_alpha),
                    cairn_rect.inflate(6, 6),
                    width=2,
                    border_radius=22,
                )
