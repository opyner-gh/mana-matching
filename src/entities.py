"""
Game entities for Echoes of Fa'Diel:
- RunePebble (Word Pebbles & Category Keystone Runes)
- MagicalReceptacle (Sacred Pools / Foundations)
- WaterRipple, ManaParticle, FloatingBanner (Visual feedback & ambient atmosphere)
"""

import math
import random
import pygame

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
)


class RunePebble:
    """
    Represents either a Word Pebble or a Category Keystone Rune.
    Includes smooth spring interpolation for position and shake feedback.
    """

    def __init__(
        self,
        uid: int,
        category_id: str,
        category_title: str,
        pillar: str,
        symbol: str,
        origin: str,
        word: str,
        is_keystone: bool = False,
        required_count: int = 4,
        revealed: bool = False,
    ):
        self.uid = uid
        self.category_id = category_id
        self.category_title = category_title
        self.pillar = pillar
        self.symbol = symbol
        self.origin = origin
        self.word = word
        self.is_keystone = is_keystone
        self.required_count = required_count
        self.revealed = revealed

        # Target logical position and smoothly interpolated visual position
        self.target_x = 0.0
        self.target_y = 0.0
        self.vis_x = 0.0
        self.vis_y = 0.0
        self.shake_timer = 0.0
        self.flip_glow = 0.0

    @property
    def width(self) -> int:
        return KEYSTONE_WIDTH if self.is_keystone else PEBBLE_WIDTH

    @property
    def height(self) -> int:
        return KEYSTONE_HEIGHT if self.is_keystone else PEBBLE_HEIGHT

    def set_pos(self, x: float, y: float, instant: bool = False):
        self.target_x = float(x)
        self.target_y = float(y)
        if instant:
            self.vis_x = float(x)
            self.vis_y = float(y)

    def reveal(self):
        if not self.revealed:
            self.revealed = True
            self.flip_glow = 1.0

    def trigger_shake(self):
        self.shake_timer = 0.42

    def update(self, dt: float):
        # Smooth exponential damping toward target position
        speed = min(1.0, dt * 15.0)
        self.vis_x += (self.target_x - self.vis_x) * speed
        self.vis_y += (self.target_y - self.vis_y) * speed

        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
        if self.flip_glow > 0:
            self.flip_glow = max(0.0, self.flip_glow - dt * 2.2)

    def get_rect(self) -> pygame.Rect:
        ox = 0
        if self.shake_timer > 0:
            ox = int(math.sin(self.shake_timer * 55.0) * 6.0 * (self.shake_timer / 0.42))
        return pygame.Rect(int(self.vis_x) + ox, int(self.vis_y), self.width, self.height)


class MagicalReceptacle:
    """
    A sacred stone-rimmed water pool (Category Foundation).
    Must first be consecrated by a Category Keystone Rune, then collects
    all Word Pebbles of that Category until it Harmonizes and clears.
    """

    def __init__(self, slot_index: int, x: int, y: int):
        self.slot_index = slot_index
        self.x = x
        self.y = y
        self.keystone: RunePebble | None = None
        self.collected_pebbles: list[RunePebble] = []
        self.pulse_phase = random.uniform(0, math.pi * 2)
        self.harmonize_flash = 0.0

    @property
    def is_empty(self) -> bool:
        return self.keystone is None

    @property
    def category_id(self) -> str | None:
        return self.keystone.category_id if self.keystone else None

    @property
    def pillar(self) -> str | None:
        return self.keystone.pillar if self.keystone else None

    @property
    def current_count(self) -> int:
        return len(self.collected_pebbles)

    @property
    def required_count(self) -> int:
        return self.keystone.required_count if self.keystone else 0

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, RECEPTACLE_WIDTH, RECEPTACLE_HEIGHT)

    def can_accept_cluster(self, cluster: list[RunePebble]) -> bool:
        """
        Checks if a dragged pebble or resonant cluster can be placed in this pool:
        - If the pool is empty, the cluster MUST contain a Keystone Rune (and all pebbles
          in the cluster share that Keystone's category_id).
        - If the pool is already consecrated with a Keystone, all pebbles in the cluster
          must be Word Pebbles matching `self.category_id`.
        """
        if not cluster:
            return False
        cat_ids = {p.category_id for p in cluster}
        if len(cat_ids) != 1:
            return False

        if self.is_empty:
            return any(p.is_keystone for p in cluster)
        else:
            cluster_cat = next(iter(cat_ids))
            return cluster_cat == self.category_id and not any(p.is_keystone for p in cluster)

    def update(self, dt: float):
        self.pulse_phase += dt * 2.4
        if self.harmonize_flash > 0:
            self.harmonize_flash = max(0.0, self.harmonize_flash - dt * 1.8)


class WaterRipple:
    """Expanding concentric water ring inside a Magical Receptacle or on the board."""

    def __init__(self, x: float, y: float, color: tuple, max_radius: float = 75.0, duration: float = 0.85):
        self.x = x
        self.y = y
        self.color = color
        self.max_radius = max_radius
        self.duration = duration
        self.age = 0.0

    @property
    def alive(self) -> bool:
        return self.age < self.duration

    def update(self, dt: float):
        self.age += dt

    def draw(self, surface: pygame.Surface):
        t = min(1.0, self.age / self.duration)
        rx = int(12 + (self.max_radius - 12) * (t ** 0.7))
        ry = max(6, int(rx * 0.62))
        alpha = int(210 * (1.0 - t))
        if alpha <= 4:
            return
        rect = pygame.Rect(int(self.x - rx), int(self.y - ry), rx * 2, ry * 2)
        pygame.draw.ellipse(surface, (*self.color[:3], alpha), rect, width=2)


class ManaParticle:
    """Ambient mana spores near the Great Tree & celebratory bursts when runes harmonize."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: tuple,
        size: float = 3.5,
        lifetime: float = 2.0,
        ambient: bool = False,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.age = 0.0
        self.ambient = ambient
        self.phase = random.uniform(0, math.pi * 2)

    @property
    def alive(self) -> bool:
        return self.age < self.lifetime

    def update(self, dt: float):
        self.age += dt
        if self.ambient:
            self.x += self.vx * dt + math.sin(self.age * 1.8 + self.phase) * 8.0 * dt
            self.y += self.vy * dt
        else:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vy += 35.0 * dt  # gentle drift

    def draw(self, surface: pygame.Surface):
        t = min(1.0, self.age / self.lifetime)
        if self.ambient:
            # Smooth fade-in and fade-out for floating forest spores
            alpha = int(165 * math.sin(t * math.pi))
        else:
            alpha = int(245 * (1.0 - t ** 1.3))
        if alpha <= 5:
            return
        r = max(1, int(self.size * (1.0 - 0.3 * t)))
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(surface, (*self.color[:3], alpha // 3), pos, r + 3)
        pygame.draw.circle(surface, (*self.color[:3], alpha), pos, r)


class FloatingBanner:
    """Floating storybook notification or score/harmony text."""

    def __init__(self, text: str, x: float, y: float, color: tuple, duration: float = 1.9):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.age = 0.0

    @property
    def alive(self) -> bool:
        return self.age < self.duration

    def update(self, dt: float):
        self.age += dt
        self.y -= 22.0 * dt

