from __future__ import annotations

import math
import random
from array import array
from dataclasses import dataclass

import pygame

SAMPLE_RATE = 44100


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class ChampionSoundProfile:
    motif: tuple[float, ...]
    cast_freqs: tuple[float, ...]
    cast_end_freqs: tuple[float, ...]
    select_waveform: str = "triangle"
    cast_waveform: str = "saw"
    cast_noise: float = 0.0
    select_volume: float = 0.18
    cast_volume: float = 0.18


CHAMPION_SOUND_PROFILES: dict[str, ChampionSoundProfile] = {
    "blue-garen": ChampionSoundProfile((220.0, 330.0), (196.0, 294.0, 392.0), (246.0, 370.0, 494.0), cast_waveform="triangle", cast_volume=0.18),
    "blue-ahri": ChampionSoundProfile((440.0, 660.0), (392.0, 554.0, 784.0), (523.0, 659.0, 880.0), select_waveform="sine", cast_waveform="sine", cast_noise=0.03, cast_volume=0.17),
    "blue-jinx": ChampionSoundProfile((330.0, 495.0), (220.0, 330.0, 880.0), (294.0, 440.0, 990.0), cast_waveform="saw", cast_noise=0.24, cast_volume=0.2),
    "blue-lux": ChampionSoundProfile((523.0, 784.0), (587.0, 880.0, 1174.0), (659.0, 988.0, 1318.0), select_waveform="sine", cast_waveform="triangle", cast_volume=0.17),
    "blue-vi": ChampionSoundProfile((180.0, 240.0), (130.0, 180.0, 260.0), (110.0, 160.0, 220.0), select_waveform="square", cast_waveform="square", cast_noise=0.16, cast_volume=0.2),
    "blue-ezreal": ChampionSoundProfile((330.0, 495.0), (494.0, 740.0), (659.0, 988.0), select_waveform="triangle", cast_waveform="sine", cast_noise=0.05, cast_volume=0.17),
    "blue-leona": ChampionSoundProfile((262.0, 392.0), (220.0, 330.0, 440.0), (294.0, 440.0, 587.0), cast_waveform="triangle", cast_volume=0.19),
    "blue-ashe": ChampionSoundProfile((294.0, 440.0), (349.0, 523.0, 784.0), (392.0, 587.0, 880.0), select_waveform="sine", cast_waveform="triangle", cast_noise=0.02, cast_volume=0.17),
    "blue-braum": ChampionSoundProfile((165.0, 247.0), (131.0, 196.0, 262.0), (147.0, 220.0, 294.0), select_waveform="triangle", cast_waveform="square", cast_noise=0.1, cast_volume=0.19),
    "red-darius": ChampionSoundProfile((146.0, 220.0), (98.0, 147.0, 196.0), (82.0, 123.0, 165.0), select_waveform="square", cast_waveform="square", cast_noise=0.12, cast_volume=0.2),
    "red-annie": ChampionSoundProfile((392.0, 523.0), (330.0, 494.0, 698.0), (392.0, 587.0, 880.0), select_waveform="triangle", cast_waveform="square", cast_noise=0.2, cast_volume=0.18),
    "red-caitlyn": ChampionSoundProfile((370.0, 555.0), (280.0, 420.0, 840.0), (350.0, 525.0, 1050.0), select_waveform="triangle", cast_waveform="triangle", cast_noise=0.08, cast_volume=0.17),
    "red-morgana": ChampionSoundProfile((174.0, 261.0), (155.0, 233.0, 311.0), (130.0, 196.0, 262.0), select_waveform="sine", cast_waveform="sine", cast_noise=0.06, cast_volume=0.18),
    "red-yasuo": ChampionSoundProfile((247.0, 370.0), (294.0, 440.0, 660.0), (392.0, 587.0, 880.0), select_waveform="sine", cast_waveform="triangle", cast_noise=0.04, cast_volume=0.18),
    "red-zed": ChampionSoundProfile((155.0, 233.0), (138.0, 207.0, 311.0), (123.0, 185.0, 277.0), select_waveform="square", cast_waveform="saw", cast_noise=0.22, cast_volume=0.19),
    "red-lissandra": ChampionSoundProfile((349.0, 523.0), (392.0, 587.0, 880.0), (330.0, 494.0, 740.0), select_waveform="triangle", cast_waveform="sine", cast_noise=0.02, cast_volume=0.17),
    "red-katarina": ChampionSoundProfile((311.0, 466.0), (247.0, 370.0, 740.0), (294.0, 440.0, 880.0), select_waveform="triangle", cast_waveform="saw", cast_noise=0.18, cast_volume=0.19),
    "red-brand": ChampionSoundProfile((196.0, 294.0), (247.0, 370.0, 554.0), (294.0, 440.0, 659.0), select_waveform="square", cast_waveform="square", cast_noise=0.22, cast_volume=0.19),
}


def _scaled(freqs: tuple[float, ...], factor: float) -> list[float]:
    return [freq * factor for freq in freqs]


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
        self.champion_sounds: dict[tuple[str, str], pygame.mixer.Sound] = {}
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
            "cast": synthesize([280.0, 420.0], 0.18, waveform="saw", end_freqs=[540.0, 760.0], volume=0.16, noise=0.08, seed=4),
            "hit": synthesize([170.0, 220.0], 0.15, waveform="square", end_freqs=[80.0, 110.0], volume=0.28, noise=0.18, seed=5),
            "hit-heavy": synthesize([120.0, 180.0], 0.22, waveform="square", end_freqs=[46.0, 70.0], volume=0.34, noise=0.24, seed=6),
            "shield": synthesize([430.0, 640.0], 0.18, waveform="sine", end_freqs=[660.0, 880.0], volume=0.23, seed=7),
            "stun": synthesize([980.0, 1330.0], 0.11, waveform="triangle", end_freqs=[560.0, 760.0], volume=0.18, seed=8),
            "intro-rest": synthesize([294.0, 392.0, 494.0], 0.32, waveform="sine", end_freqs=[330.0, 440.0, 554.0], volume=0.18, attack=0.04, release=0.42, seed=12),
            "intro-event": synthesize([311.0, 466.0, 699.0], 0.3, waveform="triangle", end_freqs=[392.0, 587.0, 880.0], volume=0.18, noise=0.03, attack=0.03, release=0.36, seed=13),
            "intro-elite": synthesize([196.0, 247.0, 311.0], 0.28, waveform="square", end_freqs=[147.0, 196.0, 247.0], volume=0.2, noise=0.1, attack=0.02, release=0.32, seed=14),
            "intro-finale": synthesize([233.0, 349.0, 466.0], 0.44, waveform="saw", end_freqs=[311.0, 466.0, 622.0], volume=0.18, noise=0.06, attack=0.02, release=0.46, seed=15),
            "victory": synthesize([392.0, 494.0, 587.0], 0.42, waveform="triangle", end_freqs=[523.0, 659.0, 784.0], volume=0.26, seed=9),
            "defeat": synthesize([262.0, 196.0], 0.34, waveform="sine", end_freqs=[196.0, 147.0], volume=0.22, seed=10),
        }
        self.champion_sounds = self._build_champion_sounds()
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

    def _build_champion_sounds(self) -> dict[tuple[str, str], pygame.mixer.Sound]:
        sounds: dict[tuple[str, str], pygame.mixer.Sound] = {}
        for index, (champion_id, profile) in enumerate(CHAMPION_SOUND_PROFILES.items(), start=1):
            sounds[(champion_id, "ui-select")] = synthesize(
                list(profile.motif),
                0.08,
                waveform=profile.select_waveform,
                end_freqs=_scaled(profile.motif, 1.02),
                volume=profile.select_volume,
                seed=100 + index,
            )
            sounds[(champion_id, "ui-confirm")] = synthesize(
                list(profile.motif),
                0.1,
                waveform=profile.select_waveform,
                end_freqs=_scaled(profile.motif, 1.16),
                volume=min(0.26, profile.select_volume + 0.02),
                seed=200 + index,
            )
            sounds[(champion_id, "cast")] = synthesize(
                list(profile.cast_freqs),
                0.2,
                waveform=profile.cast_waveform,
                end_freqs=list(profile.cast_end_freqs),
                volume=profile.cast_volume,
                noise=profile.cast_noise,
                attack=0.05,
                release=0.3,
                seed=300 + index,
            )
        return sounds

    def play(self, sound_id: str, *, champion_id: str | None = None) -> None:
        if not self.enabled:
            return

        themed_sound = self.champion_sounds.get((champion_id, sound_id)) if champion_id else None
        if themed_sound is not None:
            if sound_id == "cast":
                base_cast = self.sounds.get(sound_id)
                if base_cast is not None:
                    base_cast.play()
            themed_sound.play()
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
