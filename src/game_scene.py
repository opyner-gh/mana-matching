"""
Core gameplay scene and Solitaire Associations Journey puzzle logic for
Echoes of Fa'Diel.
"""

import copy
import math
import random
import pygame

from src.assets_manager import AssetManager, FontManager
from src.config import (
    PALETTE,
    PEBBLE_HEIGHT,
    PEBBLE_WIDTH,
    POOL_AREA_Y,
    RECEPTACLE_HEIGHT,
    RECEPTACLE_SPACING_X,
    RECEPTACLE_START_X,
    RECEPTACLE_WIDTH,
    REVEALED_OFFSET_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STOCK_POS,
    TABLEAU_AREA_Y,
    TABLEAU_SPACING_X,
    TABLEAU_START_X,
    VEILED_OFFSET_Y,
    WASTE_POS,
)
from src.entities import FloatingBanner, MagicalReceptacle, ManaParticle, RunePebble, WaterRipple
from src.lore_data import CATEGORY_BY_ID, JOURNEY_CHAPTERS, build_procedural_chapter
from src.renderer import LayeredRenderer


class UIButton:
    """Storybook parchment/bronze button for the top HUD and modal dialogs."""

    def __init__(self, key: str, label: str, rect: pygame.Rect, accent_color: tuple | None = None):
        self.key = key
        self.label = label
        self.rect = rect
        self.accent_color = accent_color or PALETTE["gold_rim"]
        self.hovered = False


class GameScene:
    """
    Manages the board state, user interactions (drag & drop, click-to-move,
    double-click auto-channel), animations, Undo stack, Hint solver, and modals.
    """

    def __init__(self, assets: AssetManager, fonts: FontManager, renderer: LayeredRenderer):
        self.assets = assets
        self.fonts = fonts
        self.renderer = renderer

        self.time_sec = 0.0
        self.relaxed_mode = False

        # Current Chapter / Level state
        self.current_chapter_idx = 0
        self.chapter_cfg = JOURNEY_CHAPTERS[0]

        # Board containers
        self.stock: list[RunePebble] = []
        self.waste: list[RunePebble] = []
        self.receptacles: list[MagicalReceptacle] = []
        self.tableau: list[list[RunePebble]] = []
        self.cairn_positions: list[tuple[int, int]] = []

        # Progress & Turn counters
        self.turns_remaining = 50
        self.moves_made = 0
        self.harmonized_categories: list[dict] = []
        self.total_categories_in_chapter = 0

        # Drag / Selection State
        self.selected_source = None        # ("waste", None) or ("tableau", col_idx)
        self.selected_cluster: list[RunePebble] = []
        self.is_dragging = False
        self.drag_offset = (0, 0)
        self.drag_mouse_pos = (0, 0)
        self.last_click_time = 0
        self.last_clicked_uid = -1

        # Hint & Status Whisper
        self.hint_uids: set[int] = set()
        self.hint_timer = 0.0
        self.whisper_text = "Welcome to Fa'Diel. Place a Keystone Rune into a Sacred Pool, or stack words of shared lore."
        self.whisper_color = PALETTE["parchment_light"]

        # Undo History
        self.undo_stack: list[dict] = []

        # Visual FX
        self.ripples: list[WaterRipple] = []
        self.particles: list[ManaParticle] = []
        self.banners: list[FloatingBanner] = []

        # Modal state: None, "grimoire", "realms", "victory", "out_of_turns"
        self.active_modal: str | None = None

        # Top HUD Buttons
        self.hud_buttons = [
            UIButton("realms", "Realms (M)", pygame.Rect(16, 10, 108, 34)),
            UIButton("mode", "Mode: Strategic", pygame.Rect(706, 10, 136, 34)),
            UIButton("undo", "Undo (Z)", pygame.Rect(852, 10, 92, 34)),
            UIButton("hint", "Hint (H)", pygame.Rect(952, 10, 92, 34)),
            UIButton("grimoire", "Grimoire (G)", pygame.Rect(1052, 10, 114, 34)),
            UIButton("restart", "Re-Deal (R)", pygame.Rect(1174, 10, 92, 34)),
        ]
        self.modal_buttons: list[UIButton] = []

        self._spawn_initial_ambient_spores()
        self.load_chapter(self.current_chapter_idx)

    # =========================================================================
    # CHAPTER SETUP & FAIR DEAL ALGORITHM
    # =========================================================================

    def load_chapter(self, chapter_idx: int | None = None, custom_chapter: dict | None = None):
        if custom_chapter is not None:
            self.chapter_cfg = custom_chapter
        else:
            if chapter_idx is not None:
                self.current_chapter_idx = chapter_idx % len(JOURNEY_CHAPTERS)
            self.chapter_cfg = JOURNEY_CHAPTERS[self.current_chapter_idx]

        self.active_modal = None
        self.undo_stack.clear()
        self.selected_source = None
        self.selected_cluster = []
        self.is_dragging = False
        self.hint_uids.clear()
        self.harmonized_categories.clear()
        self.moves_made = 0
        self.turns_remaining = self.chapter_cfg["max_turns"]

        cat_ids = self.chapter_cfg["categories"]
        self.total_categories_in_chapter = len(cat_ids)
        words_per_cat = self.chapter_cfg["words_per_category"]

        # Build Keystone Runes and Word Pebbles for each category in the chapter
        uid_counter = 1
        keystones: list[RunePebble] = []
        word_pebbles: list[RunePebble] = []

        for cid in cat_ids:
            cat = CATEGORY_BY_ID[cid]
            chosen_words = random.sample(cat["words"], min(words_per_cat, len(cat["words"])))

            keystone = RunePebble(
                uid=uid_counter,
                category_id=cid,
                category_title=cat["title"],
                pillar=cat["pillar"],
                symbol=cat["symbol"],
                origin=cat["origin"],
                word=cat["title"],
                is_keystone=True,
                required_count=len(chosen_words),
                revealed=False,
            )
            uid_counter += 1
            keystones.append(keystone)

            for w in chosen_words:
                pebble = RunePebble(
                    uid=uid_counter,
                    category_id=cid,
                    category_title=cat["title"],
                    pillar=cat["pillar"],
                    symbol=cat["symbol"],
                    origin=cat["origin"],
                    word=w,
                    is_keystone=False,
                    required_count=len(chosen_words),
                    revealed=False,
                )
                uid_counter += 1
                word_pebbles.append(pebble)

        # Configure Sacred Receptacles (Magical Pools)
        num_pools = self.chapter_cfg["num_receptacles"]
        self.receptacles = []
        # Center the receptacles nicely on the right half of the upper board
        total_pools_w = num_pools * RECEPTACLE_WIDTH + (num_pools - 1) * (RECEPTACLE_SPACING_X - RECEPTACLE_WIDTH)
        start_rx = max(RECEPTACLE_START_X, SCREEN_WIDTH - total_pools_w - 48)
        for i in range(num_pools):
            rx = start_rx + i * RECEPTACLE_SPACING_X
            ry = POOL_AREA_Y
            self.receptacles.append(MagicalReceptacle(i, rx, ry))

        # Configure Tableau Cairns (Columns)
        num_cols = self.chapter_cfg["num_columns"]
        self.tableau = [[] for _ in range(num_cols)]
        self.cairn_positions = []
        total_cols_w = num_cols * PEBBLE_WIDTH + (num_cols - 1) * (TABLEAU_SPACING_X - PEBBLE_WIDTH)
        start_cx = (SCREEN_WIDTH - total_cols_w) // 2
        for c in range(num_cols):
            self.cairn_positions.append((start_cx + c * TABLEAU_SPACING_X, TABLEAU_AREA_Y))

        # Fair Deal Distribution:
        # Ensure at least 2 Keystones start immediately accessible (on top of Tableau Cairns
        # or near the top of the Mana Spring), and distribute the rest across upper/mid tableau & stock.
        random.shuffle(keystones)
        random.shuffle(word_pebbles)

        immediate_keystones = keystones[:2]
        other_stones = keystones[2:] + word_pebbles
        random.shuffle(other_stones)

        # Column depths (e.g. 3 to 4 stones per column)
        col_depths = [3 + (c % 2) for c in range(num_cols)]
        for c in range(num_cols):
            depth = col_depths[c]
            for d in range(depth - 1):
                if other_stones:
                    p = other_stones.pop()
                    p.revealed = False
                    self.tableau[c].append(p)

        # Place the immediate keystones on top of 2 random columns, and fill remaining column tips
        top_candidates = immediate_keystones + [other_stones.pop() for _ in range(max(0, num_cols - len(immediate_keystones))) if other_stones]
        random.shuffle(top_candidates)
        for c in range(num_cols):
            if top_candidates:
                tip = top_candidates.pop()
                tip.revealed = True
                self.tableau[c].append(tip)

        # Remaining stones go into the Mana Spring (Stock)
        self.stock = top_candidates + other_stones
        random.shuffle(self.stock)
        for p in self.stock:
            p.revealed = False
            p.set_pos(STOCK_POS[0], STOCK_POS[1], instant=True)

        self.waste = []
        self._sync_target_positions(instant=True)
        # Deal slide-in animation from the Mana Spring
        for c, col in enumerate(self.tableau):
            for p in col:
                p.vis_x = float(STOCK_POS[0])
                p.vis_y = float(STOCK_POS[1])

        self.whisper_text = f"{self.chapter_cfg['title']}: {self.chapter_cfg['subtitle']}"
        self.whisper_color = PALETTE["gold_bright"]

    def _sync_target_positions(self, instant: bool = False):
        """Updates target (x, y) coordinates for all pebbles in Stock, Waste, and Tableau."""
        for p in self.stock:
            p.set_pos(STOCK_POS[0], STOCK_POS[1], instant=instant)

        for idx, p in enumerate(self.waste):
            # Show slight fan of top 3 stones in the Divination Basin
            fan_offset = max(0, idx - max(0, len(self.waste) - 3)) * 10
            p.set_pos(WASTE_POS[0] + fan_offset, WASTE_POS[1], instant=instant)

        for c_idx, col in enumerate(self.tableau):
            cx, cy = self.cairn_positions[c_idx]
            curr_y = cy
            for p_idx, p in enumerate(col):
                p.set_pos(cx, curr_y, instant=instant)
                if p.revealed:
                    curr_y += REVEALED_OFFSET_Y
                else:
                    curr_y += VEILED_OFFSET_Y

    # =========================================================================
    # CLUSTER & MOVE VALIDATION RULES (SOLITAIRE ASSOCIATIONS JOURNEY)
    # =========================================================================

    def get_movable_cluster_at_column(self, col_idx: int) -> list[RunePebble]:
        """
        Returns the contiguous Resonant Cluster of revealed pebbles sharing the same
        category_id at the tip (bottom) of tableau column `col_idx`.
        """
        col = self.tableau[col_idx]
        if not col:
            return []
        tip = col[-1]
        if not tip.revealed:
            tip.reveal()
        cluster = [tip]
        for i in range(len(col) - 2, -1, -1):
            cand = col[i]
            if cand.revealed and cand.category_id == tip.category_id:
                cluster.insert(0, cand)
            else:
                break
        return cluster

    def can_stack_on_column(self, cluster: list[RunePebble], target_col_idx: int) -> bool:
        """
        Checks if `cluster` can be placed onto tableau column `target_col_idx`:
        - Empty column: Any movable pebble or cluster can be placed on an empty Cairn.
        - Non-empty column: The revealed tip pebble of `target_col_idx` must belong to
          the EXACT SAME `category_id` as `cluster[0]`.
        """
        if not cluster:
            return False
        if self.selected_source == ("tableau", target_col_idx):
            return False
        target_col = self.tableau[target_col_idx]
        if not target_col:
            return True
        if any(p.uid == target_col[-1].uid for p in cluster):
            return False
        tip = target_col[-1]
        return tip.revealed and tip.category_id == cluster[0].category_id

    def get_valid_destinations(self, cluster: list[RunePebble]) -> tuple[set[int], set[int]]:
        """Returns (valid_pool_indices, valid_cairn_indices) for a given cluster."""
        valid_pools = set()
        valid_cairns = set()
        if not cluster:
            return valid_pools, valid_cairns

        for pool in self.receptacles:
            if pool.can_accept_cluster(cluster):
                valid_pools.add(pool.slot_index)

        for c_idx in range(len(self.tableau)):
            if self.can_stack_on_column(cluster, c_idx):
                valid_cairns.add(c_idx)

        return valid_pools, valid_cairns

    # =========================================================================
    # STATE SNAPSHOT FOR UNDO
    # =========================================================================

    def _save_undo_snapshot(self):
        """Pushes a lightweight deep copy of the board state onto the Undo stack."""
        snapshot = {
            "stock": copy.deepcopy(self.stock),
            "waste": copy.deepcopy(self.waste),
            "receptacles": copy.deepcopy(self.receptacles),
            "tableau": copy.deepcopy(self.tableau),
            "turns_remaining": self.turns_remaining,
            "moves_made": self.moves_made,
            "harmonized_categories": copy.deepcopy(self.harmonized_categories),
        }
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 40:
            self.undo_stack.pop(0)

    def perform_undo(self):
        if not self.undo_stack:
            self.whisper_text = "No earlier turns to recall in the Mana stream."
            self.whisper_color = PALETTE["parchment_mid"]
            return
        snap = self.undo_stack.pop()
        self.stock = snap["stock"]
        self.waste = snap["waste"]
        self.receptacles = snap["receptacles"]
        self.tableau = snap["tableau"]
        self.turns_remaining = snap["turns_remaining"]
        self.moves_made = snap["moves_made"]
        self.harmonized_categories = snap["harmonized_categories"]
        self.selected_source = None
        self.selected_cluster = []
        self.is_dragging = False
        self._sync_target_positions(instant=False)
        self.whisper_text = "Time rewound by one turn through the Chrono-Stream."
        self.whisper_color = PALETTE["mana_glow"]

    # =========================================================================
    # EXECUTING MOVES & POOL HARMONIZATION
    # =========================================================================

    def _consume_turn(self):
        self.moves_made += 1
        if not self.relaxed_mode:
            self.turns_remaining = max(0, self.turns_remaining - 1)

    def _remove_cluster_from_source(self, source, cluster: list[RunePebble]):
        src_type, src_idx = source
        uids = {p.uid for p in cluster}
        if src_type == "waste":
            self.waste = [p for p in self.waste if p.uid not in uids]
        elif src_type == "tableau":
            col = self.tableau[src_idx]
            self.tableau[src_idx] = [p for p in col if p.uid not in uids]
            # Automatically reveal newly uncovered stone!
            if self.tableau[src_idx] and not self.tableau[src_idx][-1].revealed:
                uncovered = self.tableau[src_idx][-1]
                uncovered.reveal()
                rect = uncovered.get_rect()
                self._spawn_particle_burst(rect.centerx, rect.centery, PALETTE["mana_cyan"], count=10)

    def execute_move_to_pool(self, source, cluster: list[RunePebble], pool: MagicalReceptacle) -> bool:
        if not pool.can_accept_cluster(cluster):
            return False

        self._save_undo_snapshot()
        self._remove_cluster_from_source(source, cluster)

        # Separate Keystone (if present in cluster) from Word Pebbles
        keystone_pebbles = [p for p in cluster if p.is_keystone]
        word_pebbles = [p for p in cluster if not p.is_keystone]

        if pool.is_empty and keystone_pebbles:
            pool.keystone = keystone_pebbles[0]

        for wp in word_pebbles:
            pool.collected_pebbles.append(wp)

        self._consume_turn()
        self._sync_target_positions()

        # Spawn water ripples in the pool
        pr = pool.get_rect()
        p_cfg = PALETTE[pool.pillar]
        self.ripples.append(WaterRipple(pr.centerx, pr.centery, p_cfg["glow"], max_radius=78.0))
        self._spawn_particle_burst(pr.centerx, pr.centery, p_cfg["glow"], count=16)

        cat_info = CATEGORY_BY_ID[pool.category_id]
        if keystone_pebbles and not word_pebbles:
            self.whisper_text = f"Sacred Pool consecrated to '{cat_info['title']}' ({cat_info['origin']})!"
            self.whisper_color = p_cfg["text_accent"]
        else:
            words_str = ", ".join(w.word for w in word_pebbles)
            self.whisper_text = f"Infused [{words_str}] into {cat_info['title']} ({pool.current_count}/{pool.required_count})."
            self.whisper_color = p_cfg["text_accent"]

        # Check if the Magical Pool has collected all required words -> HARMONIZE!
        if pool.current_count >= pool.required_count:
            self._harmonize_pool(pool)

        self._check_end_conditions()
        return True

    def execute_move_to_column(self, source, cluster: list[RunePebble], target_col_idx: int) -> bool:
        if not self.can_stack_on_column(cluster, target_col_idx):
            return False

        self._save_undo_snapshot()
        target_was_empty = len(self.tableau[target_col_idx]) == 0
        self._remove_cluster_from_source(source, cluster)

        for p in cluster:
            self.tableau[target_col_idx].append(p)

        self._consume_turn()
        self._sync_target_positions()

        tip_rect = self.tableau[target_col_idx][-1].get_rect()
        p_cfg = PALETTE[cluster[0].pillar]
        if not target_was_empty:
            self.ripples.append(WaterRipple(tip_rect.centerx, tip_rect.centery, p_cfg["glow"], max_radius=54.0))
            self._spawn_particle_burst(tip_rect.centerx, tip_rect.centery, p_cfg["glow"], count=12)
            new_cluster = self.get_movable_cluster_at_column(target_col_idx)
            self.whisper_text = (
                f"Resonant Lore Match! Bound {len(new_cluster)} runes of '{cluster[0].category_title}'."
            )
            self.whisper_color = PALETTE["gold_bright"]
        else:
            self.whisper_text = f"Placed '{cluster[0].word}' onto an open mossy Cairn."
            self.whisper_color = PALETTE["parchment_light"]

        self._check_end_conditions()
        return True

    def _harmonize_pool(self, pool: MagicalReceptacle):
        """Completes a category pool, logs it in the Grimoire, grants bonus mana turns, and frees the pool."""
        cat_id = pool.category_id
        cat_info = CATEGORY_BY_ID[cat_id]
        p_cfg = PALETTE[pool.pillar]

        self.harmonized_categories.append({
            "id": cat_id,
            "title": cat_info["title"],
            "origin": cat_info["origin"],
            "pillar": cat_info["pillar"],
            "words": [p.word for p in pool.collected_pebbles],
            "lore_note": cat_info["lore_note"],
        })

        pr = pool.get_rect()
        for r_delay in (65.0, 92.0, 118.0):
            self.ripples.append(WaterRipple(pr.centerx, pr.centery, PALETTE["gold_bright"], max_radius=r_delay, duration=1.1))
        self._spawn_particle_burst(pr.centerx, pr.centery, PALETTE["gold_bright"], count=38)
        self._spawn_particle_burst(pr.centerx, pr.centery, p_cfg["glow"], count=24)

        bonus_msg = ""
        if not self.relaxed_mode:
            self.turns_remaining += 4
            bonus_msg = " (+4 Mana Turns)"

        self.banners.append(
            FloatingBanner(
                f"✦ {cat_info['title']} Harmonized!{bonus_msg} ✦",
                pr.centerx,
                pr.centery - 10,
                PALETTE["gold_bright"],
            )
        )
        self.whisper_text = f"✦ {cat_info['title']} Harmonized! Sacred Pool freed for a new Keystone Rune!{bonus_msg}"
        self.whisper_color = PALETTE["gold_bright"]

        # Empty the pool so a new Keystone Rune can consecrate it!
        pool.keystone = None
        pool.collected_pebbles = []
        pool.harmonize_flash = 1.0

    def draw_from_mana_spring(self):
        """Draws a veiled stone from the Mana Spring into the Divination Basin, or recycles Waste."""
        if self.stock:
            self._save_undo_snapshot()
            pebble = self.stock.pop()
            pebble.reveal()
            self.waste.append(pebble)
            self._consume_turn()
            self._sync_target_positions()
            self.ripples.append(WaterRipple(STOCK_POS[0] + PEBBLE_WIDTH // 2, STOCK_POS[1] + PEBBLE_HEIGHT // 2, PALETTE["mana_cyan"], 52.0))
            self.whisper_text = f"Drawn from Mana Spring: '{pebble.word}' ({PALETTE[pebble.pillar]['name']})."
            self.whisper_color = PALETTE["mana_glow"]
            self._check_end_conditions()
        elif self.waste:
            self._save_undo_snapshot()
            # Recycle waste back into stock in order
            while self.waste:
                p = self.waste.pop()
                p.revealed = False
                self.stock.append(p)
            self._consume_turn()
            self._sync_target_positions()
            self.ripples.append(WaterRipple(STOCK_POS[0] + PEBBLE_WIDTH // 2, STOCK_POS[1] + PEBBLE_HEIGHT // 2, PALETTE["mana_glow"], 68.0))
            self.whisper_text = "Re-channeled the Divination Basin back into the Mana Spring."
            self.whisper_color = PALETTE["mana_glow"]
            self._check_end_conditions()
        else:
            self.whisper_text = "The Mana Spring and Divination Basin are both empty."
            self.whisper_color = PALETTE["parchment_mid"]

    def _check_end_conditions(self):
        if len(self.harmonized_categories) >= self.total_categories_in_chapter:
            self.active_modal = "victory"
        elif not self.relaxed_mode and self.turns_remaining <= 0:
            self.active_modal = "out_of_turns"

    # =========================================================================
    # HINT SYSTEM (STRATEGIC SOLITAIRE ASSOCIATIONS FINDER)
    # =========================================================================

    def trigger_hint(self):
        """Finds the highest-priority strategic move and highlights the involved stones."""
        self.hint_uids.clear()
        self.hint_timer = 3.2

        # Collect all movable sources: ("waste", None, [waste[-1]]) and ("tableau", c, cluster)
        sources = []
        if self.waste:
            sources.append(("waste", None, [self.waste[-1]]))
        for c_idx in range(len(self.tableau)):
            cl = self.get_movable_cluster_at_column(c_idx)
            if cl:
                sources.append(("tableau", c_idx, cl))

        # Priority 1: Can any cluster go directly into a Magical Pool?
        for src_type, src_idx, cluster in sources:
            for pool in self.receptacles:
                if pool.can_accept_cluster(cluster):
                    for p in cluster:
                        self.hint_uids.add(p.uid)
                    if pool.is_empty:
                        self.whisper_text = f"Hint: Place Keystone '{cluster[0].category_title}' into an empty Sacred Pool!"
                    else:
                        self.whisper_text = f"Hint: Infuse '{cluster[0].word}' into the '{pool.keystone.category_title}' Pool!"
                    self.whisper_color = PALETTE["gold_bright"]
                    return

        # Priority 2: Can two revealed clusters of the SAME category combine on the Tableau?
        for src_type, src_idx, cluster in sources:
            for c_idx in range(len(self.tableau)):
                if self.tableau[c_idx] and self.can_stack_on_column(cluster, c_idx):
                    target_tip = self.tableau[c_idx][-1]
                    for p in cluster:
                        self.hint_uids.add(p.uid)
                    self.hint_uids.add(target_tip.uid)
                    self.whisper_text = (
                        f"Hint: '{cluster[0].word}' and '{target_tip.word}' both belong to {cluster[0].category_title}!"
                    )
                    self.whisper_color = PALETTE["gold_bright"]
                    return

        # Priority 3: Move a cluster off a veiled stone onto an empty Cairn
        empty_cairns = [i for i, col in enumerate(self.tableau) if not col]
        if empty_cairns:
            for src_type, src_idx, cluster in sources:
                if src_type == "tableau":
                    col = self.tableau[src_idx]
                    if len(col) > len(cluster):  # Has veiled stones underneath!
                        for p in cluster:
                            self.hint_uids.add(p.uid)
                        self.whisper_text = f"Hint: Move '{cluster[0].word}' to an empty Cairn to unveil the stone beneath it."
                        self.whisper_color = PALETTE["mana_glow"]
                        return

        # Priority 4: Draw from the Mana Spring
        if self.stock or self.waste:
            self.whisper_text = "Hint: Channel a new rune from the Mana Spring (top-left)."
            self.whisper_color = PALETTE["mana_glow"]
        else:
            self.whisper_text = "Hint: Try using Undo (Z) or moving clusters to free a Keystone Rune."
            self.whisper_color = PALETTE["parchment_mid"]

    # =========================================================================
    # AUTO-CHANNEL (DOUBLE-CLICK OR RIGHT-CLICK)
    # =========================================================================

    def try_auto_channel(self, source, cluster: list[RunePebble]) -> bool:
        """Automatically sends `cluster` to a matching Sacred Pool or resonant Tableau stack."""
        # 1. Try Sacred Pools first
        for pool in self.receptacles:
            if pool.can_accept_cluster(cluster):
                return self.execute_move_to_pool(source, cluster, pool)

        # 2. Try stacking onto a matching non-empty Tableau column
        for c_idx in range(len(self.tableau)):
            if self.tableau[c_idx] and self.can_stack_on_column(cluster, c_idx):
                return self.execute_move_to_column(source, cluster, c_idx)

        return False

    # =========================================================================
    # INPUT HANDLING
    # =========================================================================

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.active_modal is not None:
                    self.active_modal = None
                else:
                    self.selected_source = None
                    self.selected_cluster = []
                    self.is_dragging = False
            elif event.key == pygame.K_z:
                self.perform_undo()
            elif event.key == pygame.K_h:
                self.trigger_hint()
            elif event.key == pygame.K_g:
                self.active_modal = None if self.active_modal == "grimoire" else "grimoire"
            elif event.key == pygame.K_m:
                self.active_modal = None if self.active_modal == "realms" else "realms"
            elif event.key == pygame.K_r:
                self.load_chapter(self.current_chapter_idx)
            return

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.drag_mouse_pos = (mx, my)
            for b in self.hud_buttons:
                b.hovered = b.rect.collidepoint(mx, my)
            for b in self.modal_buttons:
                b.hovered = b.rect.collidepoint(mx, my)

            if not self.is_dragging and self.active_modal is None:
                self._update_hover_whisper(mx, my)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Handle active modal clicks first
            if self.active_modal is not None:
                self._handle_modal_click(mx, my)
                return

            # Check top HUD buttons
            for b in self.hud_buttons:
                if b.rect.collidepoint(mx, my):
                    self._trigger_hud_button(b.key)
                    return

            # Right-click -> quick auto-channel
            if event.button == 3:
                hit_src, hit_cluster = self._hit_test_movable_cluster(mx, my)
                if hit_src and hit_cluster:
                    if not self.try_auto_channel(hit_src, hit_cluster):
                        hit_cluster[-1].trigger_shake()
                return

            if event.button == 1:
                self._handle_left_mouse_down(mx, my)
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self._handle_drag_release(*event.pos)

    def _trigger_hud_button(self, key: str):
        if key == "undo":
            self.perform_undo()
        elif key == "hint":
            self.trigger_hint()
        elif key == "grimoire":
            self.active_modal = "grimoire"
        elif key == "realms":
            self.active_modal = "realms"
        elif key == "restart":
            self.load_chapter(self.current_chapter_idx)
        elif key == "mode":
            self.relaxed_mode = not self.relaxed_mode
            for b in self.hud_buttons:
                if b.key == "mode":
                    b.label = "Mode: Relaxed" if self.relaxed_mode else "Mode: Strategic"

    def _hit_test_movable_cluster(self, mx: int, my: int):
        """Returns (source_tuple, cluster_list) if (mx, my) hits a movable pebble/cluster."""
        # 1. Check Waste top pebble
        if self.waste:
            top_w = self.waste[-1]
            if top_w.get_rect().collidepoint(mx, my):
                return ("waste", None), [top_w]

        # 2. Check Tableau Cairns (from bottom-most tip upward within movable cluster)
        for c_idx, col in enumerate(self.tableau):
            if not col:
                continue
            cluster = self.get_movable_cluster_at_column(c_idx)
            # Check from front-most (bottom tip) upward
            for p in reversed(cluster):
                if p.get_rect().collidepoint(mx, my):
                    return ("tableau", c_idx), cluster

        return None, []

    def _handle_left_mouse_down(self, mx: int, my: int):
        # 1. Check Mana Spring (Stock) click
        stock_rect = pygame.Rect(STOCK_POS[0] - 8, STOCK_POS[1] - 14, PEBBLE_WIDTH + 16, PEBBLE_HEIGHT + 28)
        if stock_rect.collidepoint(mx, my):
            self.selected_source = None
            self.selected_cluster = []
            self.draw_from_mana_spring()
            return

        # 2. Check if clicking a movable cluster
        hit_src, hit_cluster = self._hit_test_movable_cluster(mx, my)
        now_ms = pygame.time.get_ticks()

        if hit_src and hit_cluster:
            clicked_uid = hit_cluster[-1].uid
            # Double-click detection -> Auto-Channel!
            if clicked_uid == self.last_clicked_uid and (now_ms - self.last_click_time) < 380:
                self.last_clicked_uid = -1
                if self.try_auto_channel(hit_src, hit_cluster):
                    self.selected_source = None
                    self.selected_cluster = []
                    return

            self.last_clicked_uid = clicked_uid
            self.last_click_time = now_ms

            # If we already had a cluster selected from a DIFFERENT column, check if the player is
            # clicking this pebble to stack their selected cluster onto it!
            if self.selected_cluster and self.selected_source != hit_src:
                if hit_src[0] == "tableau":
                    target_col_idx = hit_src[1]
                    if self.can_stack_on_column(self.selected_cluster, target_col_idx):
                        self.execute_move_to_column(self.selected_source, self.selected_cluster, target_col_idx)
                        self.selected_source = None
                        self.selected_cluster = []
                        return
                    else:
                        # Discordant association feedback!
                        self._trigger_discordant_feedback(self.selected_cluster, hit_cluster[-1])
                        self.selected_source = None
                        self.selected_cluster = []
                        return

            # Start dragging / selecting this cluster
            self.selected_source = hit_src
            self.selected_cluster = hit_cluster
            self.is_dragging = True
            lead_rect = hit_cluster[0].get_rect()
            self.drag_offset = (mx - lead_rect.x, my - lead_rect.y)
            self.drag_mouse_pos = (mx, my)
            return

        # 3. If a cluster is already selected, check if clicking a Sacred Pool or Empty Cairn
        if self.selected_cluster:
            for pool in self.receptacles:
                if pool.get_rect().collidepoint(mx, my):
                    if not self.execute_move_to_pool(self.selected_source, self.selected_cluster, pool):
                        self._trigger_pool_mismatch_feedback(self.selected_cluster, pool)
                    self.selected_source = None
                    self.selected_cluster = []
                    return

            for c_idx, (cx, cy) in enumerate(self.cairn_positions):
                cairn_rect = pygame.Rect(cx, cy, PEBBLE_WIDTH, PEBBLE_HEIGHT + 240)
                if cairn_rect.collidepoint(mx, my):
                    if not self.execute_move_to_column(self.selected_source, self.selected_cluster, c_idx):
                        if self.tableau[c_idx]:
                            self._trigger_discordant_feedback(self.selected_cluster, self.tableau[c_idx][-1])
                    self.selected_source = None
                    self.selected_cluster = []
                    return

            # Clicked empty background -> deselect
            self.selected_source = None
            self.selected_cluster = []

    def _handle_drag_release(self, mx: int, my: int):
        self.is_dragging = False
        if not self.selected_cluster:
            return

        # Build bounding box of the dragged lead stone
        lead_x = mx - self.drag_offset[0]
        lead_y = my - self.drag_offset[1]
        drag_rect = pygame.Rect(lead_x, lead_y, PEBBLE_WIDTH, PEBBLE_HEIGHT)

        # 1. Check overlap with any Sacred Receptacle
        for pool in self.receptacles:
            if pool.get_rect().colliderect(drag_rect) or pool.get_rect().collidepoint(mx, my):
                if self.execute_move_to_pool(self.selected_source, self.selected_cluster, pool):
                    self.selected_source = None
                    self.selected_cluster = []
                    return
                else:
                    self._trigger_pool_mismatch_feedback(self.selected_cluster, pool)
                    return

        # 2. Check overlap with any Tableau Cairn
        for c_idx, col in enumerate(self.tableau):
            if self.selected_source == ("tableau", c_idx):
                continue
            if col:
                tip_rect = col[-1].get_rect().inflate(18, 18)
            else:
                cx, cy = self.cairn_positions[c_idx]
                tip_rect = pygame.Rect(cx - 8, cy - 8, PEBBLE_WIDTH + 16, PEBBLE_HEIGHT + 24)

            if tip_rect.colliderect(drag_rect) or tip_rect.collidepoint(mx, my):
                if self.execute_move_to_column(self.selected_source, self.selected_cluster, c_idx):
                    self.selected_source = None
                    self.selected_cluster = []
                    return
                else:
                    if col:
                        self._trigger_discordant_feedback(self.selected_cluster, col[-1])
                    return

    def _trigger_discordant_feedback(self, moving_cluster: list[RunePebble], target_pebble: RunePebble):
        for p in moving_cluster:
            p.trigger_shake()
        target_pebble.trigger_shake()
        tr = target_pebble.get_rect()
        self.ripples.append(WaterRipple(tr.centerx, tr.centery, (240, 95, 95), max_radius=46.0))
        self.whisper_text = (
            f"Discordant Essence: '{moving_cluster[0].word}' and '{target_pebble.word}' belong to different lore categories."
        )
        self.whisper_color = (255, 165, 150)

    def _trigger_pool_mismatch_feedback(self, moving_cluster: list[RunePebble], pool: MagicalReceptacle):
        for p in moving_cluster:
            p.trigger_shake()
        pr = pool.get_rect()
        self.ripples.append(WaterRipple(pr.centerx, pr.centery, (240, 95, 95), max_radius=58.0))
        if pool.is_empty:
            self.whisper_text = "An empty Sacred Pool must first be consecrated with a Category Keystone Rune!"
        elif any(p.is_keystone for p in moving_cluster):
            self.whisper_text = f"This Sacred Pool is already consecrated to '{pool.keystone.category_title}'."
        else:
            self.whisper_text = (
                f"Discordant Pool: '{moving_cluster[0].word}' does not belong to '{pool.keystone.category_title}'."
            )
        self.whisper_color = (255, 165, 150)

    def _update_hover_whisper(self, mx: int, my: int):
        """Updates the bottom lore whisper bar when hovering over revealed runes or pools."""
        for pool in self.receptacles:
            if not pool.is_empty and pool.get_rect().collidepoint(mx, my):
                cat = CATEGORY_BY_ID[pool.category_id]
                words_in_pool = ", ".join(p.word for p in pool.collected_pebbles) or "None yet"
                self.whisper_text = (
                    f"[{cat['origin']}] {cat['title']} ({pool.current_count}/{pool.required_count}): "
                    f"{cat['lore_note']} | Infused: {words_in_pool}"
                )
                self.whisper_color = PALETTE[pool.pillar]["text_accent"]
                return

        hit_src, hit_cluster = self._hit_test_movable_cluster(mx, my)
        if hit_cluster:
            lead = hit_cluster[-1]
            cat = CATEGORY_BY_ID[lead.category_id]
            p_name = PALETTE[lead.pillar]["name"]
            if lead.is_keystone:
                self.whisper_text = (
                    f"Keystone Rune — {cat['title']} ({cat['origin']}): {cat['lore_note']} "
                    f"Place in an empty Sacred Pool!"
                )
            else:
                cluster_words = " + ".join(p.word for p in hit_cluster)
                self.whisper_text = (
                    f"Rune: {cluster_words}  •  Pillar: {p_name}  •  Origin Hint: {cat['origin']}"
                )
            self.whisper_color = PALETTE[lead.pillar]["text_accent"]

    # =========================================================================
    # AMBIENT & BURST PARTICLES
    # =========================================================================

    def _spawn_initial_ambient_spores(self):
        for _ in range(28):
            self.particles.append(
                ManaParticle(
                    x=random.uniform(40, SCREEN_WIDTH - 40),
                    y=random.uniform(80, SCREEN_HEIGHT - 40),
                    vx=random.uniform(-6, 8),
                    vy=random.uniform(-16, -6),
                    color=random.choice([(180, 248, 210), (255, 232, 145), (155, 228, 245)]),
                    size=random.uniform(2.2, 4.2),
                    lifetime=random.uniform(3.0, 6.5),
                    ambient=True,
                )
            )

    def _spawn_particle_burst(self, x: float, y: float, color: tuple, count: int = 16):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(28.0, 115.0)
            self.particles.append(
                ManaParticle(
                    x=x,
                    y=y,
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd - 20.0,
                    color=color,
                    size=random.uniform(2.8, 5.2),
                    lifetime=random.uniform(0.55, 1.15),
                    ambient=False,
                )
            )

    # =========================================================================
    # UPDATE LOOP
    # =========================================================================

    def update(self, dt: float):
        self.time_sec += dt
        if self.hint_timer > 0:
            self.hint_timer = max(0.0, self.hint_timer - dt)
            if self.hint_timer == 0:
                self.hint_uids.clear()

        for pool in self.receptacles:
            pool.update(dt)
        for p in self.stock:
            p.update(dt)
        for p in self.waste:
            p.update(dt)
        for col in self.tableau:
            for p in col:
                p.update(dt)

        for r in self.ripples:
            r.update(dt)
        self.ripples = [r for r in self.ripples if r.alive]

        for pt in self.particles:
            pt.update(dt)
        self.particles = [pt for pt in self.particles if pt.alive]

        # Maintain lush floating forest spores
        if len([p for p in self.particles if p.ambient]) < 26:
            # Spawn predominantly near the Great Mana Tree (left) and ruins (right)
            spawn_x = random.choice([
                random.uniform(40, 420),
                random.uniform(420, 860),
                random.uniform(860, SCREEN_WIDTH - 40),
            ])
            self.particles.append(
                ManaParticle(
                    x=spawn_x,
                    y=SCREEN_HEIGHT + 10,
                    vx=random.uniform(-5, 7),
                    vy=random.uniform(-22, -9),
                    color=random.choice([(185, 252, 215), (255, 234, 155), (160, 230, 250)]),
                    size=random.uniform(2.2, 4.4),
                    lifetime=random.uniform(4.5, 8.0),
                    ambient=True,
                )
            )

        for b in self.banners:
            b.update(dt)
        self.banners = [b for b in self.banners if b.alive]

    # =========================================================================
    # MULTI-LAYER RENDERING PIPELINE
    # =========================================================================

    def render(self, screen: pygame.Surface):
        self.renderer.clear_dynamic_layers()

        # Determine valid drop targets for currently selected/dragged cluster
        valid_pools, valid_cairns = self.get_valid_destinations(self.selected_cluster)

        # LAYER 2: Ambient Mana Spores
        for pt in self.particles:
            if pt.ambient:
                pt.draw(self.renderer.ambient_fx_layer)

        # LAYER 3: Sacred Receptacles (Magical Pools), Mana Spring & Cairn Bases
        self.renderer.render_receptacles_and_springs(
            receptacles=self.receptacles,
            stock_count=len(self.stock),
            waste_count=len(self.waste),
            cairn_positions=self.cairn_positions,
            valid_pool_indices=valid_pools,
            valid_cairn_indices=valid_cairns,
            time_sec=self.time_sec,
        )

        # LAYER 4: Stationary Pebbles & Keystones in Waste & Tableau Cairns
        dragged_uids = {p.uid for p in self.selected_cluster} if self.is_dragging else set()
        selected_uids = {p.uid for p in self.selected_cluster}

        # Render Divination Basin (Waste) pebbles (show up to top 3 fanned)
        visible_waste = self.waste[-3:]
        for p in visible_waste:
            if p.uid in dragged_uids:
                continue
            self.renderer.render_pebble_to_layer(
                self.renderer.pebble_layer,
                p,
                is_selected=(p.uid in selected_uids),
                is_hinted=(p.uid in self.hint_uids),
            )

        # Render Tableau Cairns
        for c_idx, col in enumerate(self.tableau):
            movable_cluster = self.get_movable_cluster_at_column(c_idx)
            cluster_size = len(movable_cluster)
            for p_idx, p in enumerate(col):
                if p.uid in dragged_uids:
                    continue
                is_tip = (p_idx == len(col) - 1)
                self.renderer.render_pebble_to_layer(
                    self.renderer.pebble_layer,
                    p,
                    is_selected=(p.uid in selected_uids),
                    is_valid_target=(is_tip and c_idx in valid_cairns),
                    is_hinted=(p.uid in self.hint_uids),
                    cluster_count=(cluster_size if is_tip else 1),
                )

        # LAYER 5: Dragged Cluster, Water Ripples, Particle Bursts & Floating Banners
        fx_layer = self.renderer.drag_and_fx_layer
        for r in self.ripples:
            r.draw(fx_layer)
        for pt in self.particles:
            if not pt.ambient:
                pt.draw(fx_layer)

        if self.is_dragging and self.selected_cluster:
            mx, my = self.drag_mouse_pos
            base_x = mx - self.drag_offset[0]
            base_y = my - self.drag_offset[1]
            for idx, p in enumerate(self.selected_cluster):
                is_tip = (idx == len(self.selected_cluster) - 1)
                self.renderer.render_pebble_to_layer(
                    fx_layer,
                    p,
                    pos=(base_x, base_y + idx * REVEALED_OFFSET_Y),
                    is_selected=True,
                    cluster_count=(len(self.selected_cluster) if is_tip else 1),
                    elevated=True,
                )

        for banner in self.banners:
            t = min(1.0, banner.age / banner.duration)
            alpha = int(255 * (1.0 - t ** 1.6))
            if alpha > 10:
                txt_surf = self.fonts.render_text_with_shadow("title", 20, banner.text, banner.color)
                txt_surf.set_alpha(alpha)
                fx_layer.blit(txt_surf, txt_surf.get_rect(center=(int(banner.x), int(banner.y))))

        # LAYER 6: Storybook HUD, Bottom Lore Whisper Bar, and Modals
        self._render_hud_layer(self.renderer.hud_layer)
        if self.active_modal is not None:
            self._render_modal_overlay(self.renderer.hud_layer)

        # Composite all 6 layers to the screen
        self.renderer.composite_to(screen)

    # =========================================================================
    # STORYBOOK HUD & MODAL OVERLAYS
    # =========================================================================

    def _render_hud_layer(self, layer: pygame.Surface):
        # Top storybook header bar
        pygame.draw.rect(layer, (24, 20, 16, 215), (0, 0, SCREEN_WIDTH, 52))
        pygame.draw.line(layer, PALETTE["gold_rim"], (0, 52), (SCREEN_WIDTH, 52), 2)

        # Chapter Title
        ch_surf = self.fonts.render_text_with_shadow(
            "title", 19, self.chapter_cfg["title"], PALETTE["gold_bright"]
        )
        layer.blit(ch_surf, (136, 14))

        # Harmonized Progress & Mana Turns Pill
        prog_str = f"Harmonized: {len(self.harmonized_categories)} / {self.total_categories_in_chapter}"
        turns_str = "Mana Turns: ∞" if self.relaxed_mode else f"Mana Turns: {self.turns_remaining}"
        stat_font = self.fonts.get("ui", 13)

        p_surf = stat_font.render(prog_str, True, PALETTE["mana_glow"])
        t_col = (255, 130, 115) if (not self.relaxed_mode and self.turns_remaining <= 8) else PALETTE["parchment_light"]
        t_surf = stat_font.render(turns_str, True, t_col)

        layer.blit(p_surf, (415, 17))
        layer.blit(t_surf, (568, 17))

        # Top HUD Buttons
        btn_font = self.fonts.get("ui", 12)
        for b in self.hud_buttons:
            bg_col = (74, 58, 42, 240) if b.hovered else (46, 36, 28, 225)
            border_col = PALETTE["gold_bright"] if b.hovered else b.accent_color
            pygame.draw.rect(layer, bg_col, b.rect, border_radius=9)
            pygame.draw.rect(layer, border_col, b.rect, width=2, border_radius=9)
            lbl = btn_font.render(b.label, True, PALETTE["parchment_light"])
            layer.blit(lbl, lbl.get_rect(center=b.rect.center))

        # Bottom Lore & Association Whisper Bar
        bar_rect = pygame.Rect(24, SCREEN_HEIGHT - 42, SCREEN_WIDTH - 48, 34)
        pygame.draw.rect(layer, (24, 20, 16, 215), bar_rect, border_radius=12)
        pygame.draw.rect(layer, PALETTE["bronze_rim"], bar_rect, width=2, border_radius=12)

        w_font = self.fonts.get("lore", 14)
        w_surf = w_font.render(self.whisper_text, True, self.whisper_color)
        layer.blit(w_surf, w_surf.get_rect(center=bar_rect.center))

    def _render_modal_overlay(self, layer: pygame.Surface):
        # Dimmed backdrop
        pygame.draw.rect(layer, (12, 10, 8, 195), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.modal_buttons.clear()

        panel = pygame.Rect(96, 66, SCREEN_WIDTH - 192, SCREEN_HEIGHT - 132)
        pygame.draw.rect(layer, (38, 31, 25, 248), panel, border_radius=20)
        pygame.draw.rect(layer, PALETTE["gold_rim"], panel, width=3, border_radius=20)
        pygame.draw.rect(layer, PALETTE["bronze_rim"], panel.inflate(-10, -10), width=1, border_radius=16)

        if self.active_modal == "grimoire":
            self._render_grimoire_modal(layer, panel)
        elif self.active_modal == "realms":
            self._render_realms_modal(layer, panel)
        elif self.active_modal in ("victory", "out_of_turns"):
            self._render_endgame_modal(layer, panel)

        # Render modal buttons
        btn_font = self.fonts.get("ui", 14)
        for b in self.modal_buttons:
            bg_col = (88, 68, 48) if b.hovered else (56, 44, 32)
            pygame.draw.rect(layer, bg_col, b.rect, border_radius=10)
            pygame.draw.rect(layer, PALETTE["gold_bright"] if b.hovered else b.accent_color, b.rect, width=2, border_radius=10)
            lbl = btn_font.render(b.label, True, PALETTE["parchment_light"])
            layer.blit(lbl, lbl.get_rect(center=b.rect.center))

    def _render_grimoire_modal(self, layer: pygame.Surface, panel: pygame.Rect):
        title = self.fonts.render_text_with_shadow(
            "title", 26, "Grimoire of Associations & Realm Lore", PALETTE["gold_bright"]
        )
        layer.blit(title, title.get_rect(center=(panel.centerx, panel.top + 36)))

        rules_font = self.fonts.get("lore", 14)
        rules_lines = [
            "• Place a Category Keystone Rune into an empty Sacred Pool to consecrate it.",
            "• Stack Word Pebbles of the SAME Lore Category onto each other in the Cairns, or infuse them into their Pool.",
            "• When a Sacred Pool collects all its words, it Harmonizes and clears—freeing the Pool for a new Keystone!",
            "• Double-click or Right-click any revealed rune to Auto-Channel it to a valid Pool or resonant stack.",
        ]
        for i, line in enumerate(rules_lines):
            s = rules_font.render(line, True, PALETTE["parchment_light"])
            layer.blit(s, (panel.left + 36, panel.top + 68 + i * 22))

        # Categories in current chapter
        sub = self.fonts.get("title", 18).render("Current Chapter Lore Foundations:", True, PALETTE["mana_glow"])
        layer.blit(sub, (panel.left + 36, panel.top + 168))

        harmonized_ids = {h["id"] for h in self.harmonized_categories}
        cat_ids = self.chapter_cfg["categories"]
        col_w = (panel.width - 84) // 2

        for idx, cid in enumerate(cat_ids):
            cat = CATEGORY_BY_ID[cid]
            p_cfg = PALETTE[cat["pillar"]]
            cx = panel.left + 36 + (idx % 2) * (col_w + 12)
            cy = panel.top + 202 + (idx // 2) * 74
            card_rect = pygame.Rect(cx, cy, col_w, 66)

            is_done = cid in harmonized_ids
            bg = (52, 68, 54) if is_done else (48, 40, 34)
            pygame.draw.rect(layer, bg, card_rect, border_radius=10)
            pygame.draw.rect(layer, p_cfg["stone_border"], card_rect, width=2, border_radius=10)

            status = "✓ HARMONIZED" if is_done else f"Pillar: {p_cfg['name']}"
            h_txt = self.fonts.get("ui", 12).render(
                f"{cat['title']}  [{cat['origin']}] — {status}", True, PALETTE["gold_bright"] if is_done else p_cfg["text_accent"]
            )
            layer.blit(h_txt, (cx + 12, cy + 8))

            n_txt = self.fonts.get("lore", 12).render(cat["lore_note"], True, PALETTE["parchment_mid"])
            layer.blit(n_txt, (cx + 12, cy + 28))

            sample_words = ", ".join(cat["words"][:5])
            w_txt = self.fonts.get("lore", 11).render(f"Runes: {sample_words}...", True, (195, 185, 165))
            layer.blit(w_txt, (cx + 12, cy + 46))

        close_btn = UIButton("close_modal", "Return to Sanctuary (Esc)", pygame.Rect(panel.centerx - 120, panel.bottom - 52, 240, 36))
        self.modal_buttons.append(close_btn)

    def _render_realms_modal(self, layer: pygame.Surface, panel: pygame.Rect):
        title = self.fonts.render_text_with_shadow(
            "title", 26, "Chronicles of Fa'Diel — Select a Journey Chapter", PALETTE["gold_bright"]
        )
        layer.blit(title, title.get_rect(center=(panel.centerx, panel.top + 38)))

        for idx, ch in enumerate(JOURNEY_CHAPTERS):
            by = panel.top + 82 + idx * 68
            b_rect = pygame.Rect(panel.left + 48, by, panel.width - 96, 56)
            label = (
                f"{ch['title']}  —  {len(ch['categories'])} Categories | "
                f"{ch['num_receptacles']} Pools | {ch['words_per_category']} Runes each"
            )
            self.modal_buttons.append(UIButton(f"chapter_{idx}", label, b_rect))

        # Procedural Weaver button
        proc_rect = pygame.Rect(panel.left + 48, panel.top + 82 + len(JOURNEY_CHAPTERS) * 68, (panel.width - 112) // 2, 46)
        close_rect = pygame.Rect(panel.centerx + 8, panel.top + 82 + len(JOURNEY_CHAPTERS) * 68, (panel.width - 112) // 2, 46)
        self.modal_buttons.append(UIButton("procedural", "✦ Weave Random Nostalgic Realm ✦", proc_rect, PALETTE["mana_cyan"]))
        self.modal_buttons.append(UIButton("close_modal", "Resume Current Journey", close_rect))

    def _render_endgame_modal(self, layer: pygame.Surface, panel: pygame.Rect):
        is_win = self.active_modal == "victory"
        heading = "✦ All Sacred Pools Harmonized! ✦" if is_win else "The Mana Stream Has Ebbed..."
        h_col = PALETTE["gold_bright"] if is_win else (255, 150, 130)

        title = self.fonts.render_text_with_shadow("title", 30, heading, h_col)
        layer.blit(title, title.get_rect(center=(panel.centerx, panel.top + 56)))

        sub_str = (
            f"You restored harmony to {self.chapter_cfg['title']} in {self.moves_made} moves!"
            if is_win
            else "You ran out of Mana Turns in Strategic Mode. You can Undo, switch to Relaxed Mode, or Re-Deal!"
        )
        sub = self.fonts.get("lore", 16).render(sub_str, True, PALETTE["parchment_light"])
        layer.blit(sub, sub.get_rect(center=(panel.centerx, panel.top + 102)))

        # List harmonized categories
        y_cursor = panel.top + 144
        for h in self.harmonized_categories[:6]:
            line = f"✦ {h['title']} ({h['origin']}): {', '.join(h['words'])}"
            l_surf = self.fonts.get("lore", 14).render(line, True, PALETTE["mana_glow"])
            layer.blit(l_surf, l_surf.get_rect(center=(panel.centerx, y_cursor)))
            y_cursor += 28

        btn_y = panel.bottom - 68
        if is_win:
            next_btn = UIButton("next_chapter", "Next Chapter →", pygame.Rect(panel.centerx - 230, btn_y, 210, 42), PALETTE["mana_cyan"])
            proc_btn = UIButton("procedural", "Weave Endless Realm", pygame.Rect(panel.centerx + 20, btn_y, 210, 42))
            self.modal_buttons.extend([next_btn, proc_btn])
        else:
            undo_btn = UIButton("undo_from_modal", "Undo Last Turn", pygame.Rect(panel.centerx - 320, btn_y, 195, 42))
            relax_btn = UIButton("continue_relaxed", "Continue in Relaxed Mode", pygame.Rect(panel.centerx - 105, btn_y, 225, 42), PALETTE["mana_cyan"])
            retry_btn = UIButton("restart_from_modal", "Re-Deal Chapter", pygame.Rect(panel.centerx + 140, btn_y, 185, 42))
            self.modal_buttons.extend([undo_btn, relax_btn, retry_btn])

    def _handle_modal_click(self, mx: int, my: int):
        for b in self.modal_buttons:
            if b.rect.collidepoint(mx, my):
                if b.key == "close_modal":
                    self.active_modal = None
                elif b.key.startswith("chapter_"):
                    idx = int(b.key.split("_")[1])
                    self.load_chapter(idx)
                elif b.key == "procedural":
                    self.load_chapter(custom_chapter=build_procedural_chapter())
                elif b.key == "next_chapter":
                    self.load_chapter(self.current_chapter_idx + 1)
                elif b.key == "undo_from_modal":
                    self.active_modal = None
                    self.perform_undo()
                elif b.key == "continue_relaxed":
                    self.relaxed_mode = True
                    self.active_modal = None
                    for hb in self.hud_buttons:
                        if hb.key == "mode":
                            hb.label = "Mode: Relaxed"
                elif b.key == "restart_from_modal":
                    self.load_chapter(self.current_chapter_idx)
                return
