from __future__ import annotations

import math
import random
from array import array

import pygame

SAMPLE_RATE = 44100


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _wave(phase: float, kind: str) -> float:
    if kind == "triangle":
        return 2.0 / math.pi * math.asin(math.sin(phase))
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "saw":
        cycle = phase / (2 * math.pi)
        return 2 * (cycle - math.floor(cycle + 0.5))
    return math.sin(phase)


def synthesize(
    start_freqs: list[float],
    duration: float,
    *,
    waveform: str = "sine",
    end_freqs: list[float] | None = None,
    volume: float = 0.32,
    noise: float = 0.0,
    attack: float = 0.08,
    release: float = 0.24,
    seed: int = 0,
) -> pygame.mixer.Sound:
    end_freqs = end_freqs or start_freqs
    total_samples = max(1, int(duration * SAMPLE_RATE))
    rng = random.Random(seed)
    pcm = array("h")

    for index in range(total_samples):
        progress = index / max(1, total_samples - 1)
        attack_env = clamp(progress / max(0.001, attack), 0.0, 1.0)
        release_start = max(0.0, 1.0 - release)
        release_env = 1.0 - clamp((progress - release_start) / max(0.001, release), 0.0, 1.0)
        envelope = attack_env * release_env

        sample = 0.0
        for start_freq, end_freq in zip(start_freqs, end_freqs):
            freq = start_freq + (end_freq - start_freq) * progress
            phase = 2 * math.pi * freq * (index / SAMPLE_RATE)
            sample += _wave(phase, waveform)
        sample /= max(1, len(start_freqs))

        if noise > 0:
            sample = sample * (1.0 - noise) + rng.uniform(-1.0, 1.0) * noise

        value = int(clamp(sample * envelope * volume, -1.0, 1.0) * 32767)
        pcm.extend((value, value))

    return pygame.mixer.Sound(buffer=pcm.tobytes())


class SoundBank:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.ambient: pygame.mixer.Sound | None = None

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        except pygame.error:
            return

        self.enabled = True
        pygame.mixer.set_num_channels(16)
        self.sounds = {
            "ui-select": synthesize([660.0, 990.0], 0.07, waveform="triangle", volume=0.22, seed=1),
            "ui-confirm": synthesize([520.0, 780.0], 0.09, waveform="triangle", end_freqs=[700.0, 980.0], volume=0.24, seed=2),
            "reset": synthesize([380.0, 250.0], 0.12, waveform="sine", end_freqs=[240.0, 150.0], volume=0.18, seed=3),
            "cast": synthesize([280.0, 420.0], 0.18, waveform="saw", end_freqs=[540.0, 760.0], volume=0.22, noise=0.08, seed=4),
            "hit": synthesize([170.0, 220.0], 0.15, waveform="square", end_freqs=[80.0, 110.0], volume=0.28, noise=0.18, seed=5),
            "hit-heavy": synthesize([120.0, 180.0], 0.22, waveform="square", end_freqs=[46.0, 70.0], volume=0.34, noise=0.24, seed=6),
            "shield": synthesize([430.0, 640.0], 0.18, waveform="sine", end_freqs=[660.0, 880.0], volume=0.23, seed=7),
            "stun": synthesize([980.0, 1330.0], 0.11, waveform="triangle", end_freqs=[560.0, 760.0], volume=0.18, seed=8),
            "victory": synthesize([392.0, 494.0, 587.0], 0.42, waveform="triangle", end_freqs=[523.0, 659.0, 784.0], volume=0.26, seed=9),
            "defeat": synthesize([262.0, 196.0], 0.34, waveform="sine", end_freqs=[196.0, 147.0], volume=0.22, seed=10),
        }
        self.ambient = synthesize(
            [110.0, 165.0, 220.0],
            1.8,
            waveform="sine",
            end_freqs=[124.0, 186.0, 248.0],
            volume=0.06,
            noise=0.01,
            attack=0.2,
            release=0.28,
            seed=11,
        )

    def play(self, sound_id: str) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(sound_id)
        if sound is not None:
            sound.play()

    def start_ambient(self) -> None:
        if not self.enabled or self.ambient is None:
            return
        channel = self.ambient.play(loops=-1)
        if channel is not None:
            channel.set_volume(0.45)
