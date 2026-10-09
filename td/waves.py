"""Wave scheduling: a timeline of spawn events, scaled for infinite mode."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List

import pygame

from td.entities import Enemy
from td.settings import ENEMY_TEMPLATES

Vec2 = tuple[float, float]


@dataclass
class SpawnEvent:
    """Spawn `count` enemies of `enemy_type` every `interval` seconds,
    starting at `when` seconds, optionally with a per-enemy stagger `spread`.
    """
    when: float          # seconds from level start
    count: int
    enemy_type: str
    interval: float      # seconds between each enemy in this event
    spread: float        # extra random jitter per enemy spawn time
    hp_scale: float = 1.0
    speed_scale: float = 1.0
    reward_scale: float = 1.0


@dataclass
class WaveTimeline:
    """A sequence of spawn events defining one level / one infinite wave pack."""
    events: List[SpawnEvent] = field(default_factory=list)
    duration: float = 0.0     # seconds until the last event finishes spawning

    @classmethod
    def from_events(cls, events: List[dict]) -> "WaveTimeline":
        out: List[SpawnEvent] = []
        for ev in events:
            out.append(
                SpawnEvent(
                    when=float(ev.get("when", 0)),
                    count=int(ev.get("count", 1)),
                    enemy_type=str(ev.get("type", "basic")),
                    interval=float(ev.get("interval", 0.6)),
                    spread=float(ev.get("spread", 0.0)),
                    hp_scale=float(ev.get("hp_scale", 1.0)),
                    speed_scale=float(ev.get("speed_scale", 1.0)),
                    reward_scale=float(ev.get("reward_scale", 1.0)),
                )
            )
        # compute duration: last event start + its spawn tail
        duration = 0.0
        for ev in out:
            tail = (ev.count - 1) * ev.interval + ev.spread * ev.count
            finish = ev.when + tail
            if finish > duration:
                duration = finish
        return cls(events=out, duration=duration)


class Spawner:
    """Drives spawning from a WaveTimeline.

    In infinite mode, the same timeline is reused with scaling applied per
    wave cycle.
    """

    def __init__(self, timeline: WaveTimeline) -> None:
        self.timeline = timeline
        self.clock = 0.0
        self.active: List[Enemy] = []
        self._index = 0
        self._event_progress: Dict[int, int] = {}  # event index -> spawned count
        self._finished = False

    @property
    def finished(self) -> bool:
        return self._finished

    def reset(self) -> None:
        self.clock = 0.0
        self._index = 0
        self._event_progress.clear()
        self._finished = False

    def update(self, dt: float, spawn_fn) -> None:
        """Advance the spawner clock. Calls spawn_fn(type, hp, speed, reward)
        whenever an enemy should appear."""
        if self._finished:
            return
        self.clock += dt
        # process events in order
        while self._index < len(self.timeline.events):
            ev = self.timeline.events[self._index]
            # scheduled spawn times for this event
            spawned = self._event_progress.get(self._index, 0)
            if spawned >= ev.count:
                self._index += 1
                continue
            # time of the next spawn in this event
            base_when = ev.when + spawned * ev.interval
            jitter = ev.spread * (2.0 * random.random() - 1.0) if ev.spread > 0 else 0.0
            next_when = base_when + jitter
            if self.clock >= next_when:
                hp = _scale_stat(ENEMY_TEMPLATES[ev.enemy_type]["hp"], ev.hp_scale)
                spd = _scale_stat(ENEMY_TEMPLATES[ev.enemy_type]["speed"], ev.speed_scale)
                rew = _scale_stat(ENEMY_TEMPLATES[ev.enemy_type]["reward"], ev.reward_scale)
                spawn_fn(ev.enemy_type, hp, spd, rew)
                self._event_progress[self._index] = spawned + 1
            else:
                break
        if self._index >= len(self.timeline.events):
            # all events processed; check if any remain unspawned
            all_done = True
            for i in range(len(self.timeline.events)):
                if self._event_progress.get(i, 0) < self.timeline.events[i].count:
                    all_done = False
                    break
            if all_done:
                self._finished = True

    def set_enemies_near(self, enemies: List[Enemy]) -> None:
        """Stash current live enemy list so projectiles can query splash targets."""
        # used by Tower if needed; kept simple: towers access the scene list directly
        pass


def _scale_stat(base: float, scale: float, variance: float = 0.0) -> float:
    val = base * scale
    if variance > 0:
        val *= random.uniform(1.0 - variance, 1.0 + variance)
    return max(1.0, val)


def make_infinite_timeline(
    base_events: List[dict],
    wave_index: int,
    ramp: float = 0.12,
    boss_every: int = 5,
    boss_scale: float = 1.6,
) -> WaveTimeline:
    """Build a WaveTimeline for the given infinite-wave index.

    Each cycle, enemy counts, HP, and speed ramp up. Every `boss_every`
    waves, a boss event is appended at the end.
    """
    scale = 1.0 + ramp * wave_index
    count_scale = 1.0 + ramp * wave_index * 0.8
    events: List[dict] = []
    for ev in base_events:
        events.append({
            "when": ev.get("when", 0) * min(1.0 + 0.02 * wave_index, 1.6),
            "count": max(1, int(ev.get("count", 1) * count_scale)),
            "type": ev.get("type", "basic"),
            "interval": max(0.25, ev.get("interval", 0.6) / (1.0 + 0.03 * wave_index)),
            "spread": ev.get("spread", 0.0),
            "hp_scale": 1.0 + (scale - 1.0) * 0.9,
            "speed_scale": 1.0 + (scale - 1.0) * 0.25,
            "reward_scale": 1.0 + (scale - 1.0) * 0.5,
        })
    # boss injection
    if wave_index > 0 and wave_index % boss_every == 0:
        boss_count = 1 + wave_index // boss_every
        events.append({
            "when": events[-1]["when"] + events[-1].get("interval", 0.6) * events[-1]["count"] + 3.0,
            "count": boss_count,
            "type": "boss",
            "interval": 1.5,
            "spread": 0.0,
            "hp_scale": boss_scale * (1.0 + 0.15 * (wave_index // boss_every)),
            "speed_scale": 1.0,
            "reward_scale": boss_scale * 1.2,
        })
    return WaveTimeline.from_events(events)
