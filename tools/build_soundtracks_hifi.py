"""Compose & render ECHO-7's 8 chapter scores + Level 80 Finale Ascent cue in 44.1 kHz stereo.

Each chapter has a distinct meter/subdivision, harmonic mode, melodic contour, bass architecture,
percussion engine, and synthesis voice:
- Ch 1 (Awakening): 92 BPM, 4/4 Sparse Diagnostic Minimalism (D Phrygian Minor, glass piano + sonar pulse)
- Ch 2 (Mechanical Depths): 108 BPM, 6/8 Compound Industrial Meter (A Aeolian/Dorian, FM anvil + 3+3 piston bass)
- Ch 3 (Power Grid): 126 BPM, 4/4 Driving 16th-Note Sequencer (E Dorian, dual-panned arp pulse + filter bass)
- Ch 4 (Surveillance Grid): 105 BPM, 5/4 Asymmetric Watchful Meter (F# Locrian, staccato pluck + radar ping)
- Ch 5 (Flood Control): 88 BPM, 3/4 Submerged Hydraulic Waltz (C Minor/Dorian, submerged bell + brass swell)
- Ch 6 (Core Collapse): 134 BPM, 7/8 Urgent Polyrhythmic Meter (F Phrygian Dominant, reactor brass + industrial clang)
- Ch 7 (Broken Spire): 98 BPM, 4/4 Elegiac Broken-Time Harp & Cello (Bb Minor, spire harp + warm cello counterline)
- Ch 8 (Surface Breach): 118 BPM, 4/4 Nocturnal Horizon Synthwave (D Lydian -> D Major, nocturnal lead + tom cadence)
- Finale 80: 128 BPM, 4-Stage Progressive Ascent (D Dorian -> D Major resolution)
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
MUSIC = ROOT / "data" / "music"
PREVIEWS = ROOT / "soundtrack_previews"
FS = 44100

# (chapter, bpm, beats_per_bar, bars, root_midi, mode_name, lead_voice, counter_voice)
SPECS = [
    (1, 92, 4, 16, 50, "D_phrygian_diagnostic", "glass_piano", "telemetry_bell"),
    (2, 108, 6, 12, 45, "A_compound_foundry_6_8", "fm_anvil", "piston_brass"),
    (3, 126, 4, 16, 52, "E_dorian_sequencer", "arp_pulse", "sync_lead"),
    (4, 105, 5, 12, 54, "Fsharp_locrian_5_4", "staccato_pluck", "radar_ping"),
    (5, 88, 3, 20, 48, "C_hydraulic_waltz_3_4", "submerged_bell", "hydro_horn"),
    (6, 134, 7, 12, 41, "F_phrygian_dom_7_8", "reactor_brass", "alarm_fm"),
    (7, 98, 4, 16, 46, "Bb_elegiac_spire", "spire_harp", "cello_bow"),
    (8, 118, 4, 16, 50, "D_lydian_nocturne", "nocturnal_lead", "glass_piano"),
]

CHORD_PROGRESSIONS = {
    1: [(0, 7, 14), (1, 7, 12), (-2, 5, 10), (0, 7, 15),
        (3, 7, 14), (1, 8, 12), (-4, 3, 8), (-2, 5, 11)],
    2: [(0, 3, 7, 10), (5, 8, 12, 15), (3, 7, 10, 14), (7, 10, 14, 17),
        (8, 12, 15, 19), (6, 10, 13, 18), (5, 9, 12, 16), (7, 10, 14, 19)],
    3: [(0, 3, 7, 10), (2, 5, 9, 14), (5, 9, 12, 16), (7, 10, 14, 17),
        (3, 7, 10, 15), (5, 9, 12, 17), (8, 12, 15, 19), (10, 14, 17, 22)],
    4: [(0, 3, 6, 10), (1, 5, 8, 12), (-2, 1, 6, 9), (0, 6, 11, 13),
        (3, 6, 10, 15), (1, 4, 8, 13), (-3, 0, 6, 9), (-1, 3, 6, 11)],
    5: [(0, 3, 7, 12), (5, 8, 12, 15), (8, 12, 15, 19), (7, 10, 14, 17),
        (3, 7, 10, 15), (5, 8, 12, 17), (2, 5, 8, 14), (7, 11, 14, 17)],
    6: [(0, 4, 7, 10), (1, 5, 8, 13), (4, 7, 10, 15), (7, 10, 13, 18),
        (8, 12, 15, 19), (5, 8, 12, 17), (1, 5, 8, 13), (4, 7, 11, 16)],
    7: [(0, 3, 7, 14), (8, 12, 15, 19), (5, 8, 12, 17), (3, 7, 10, 15),
        (2, 5, 9, 14), (8, 12, 15, 20), (5, 9, 12, 17), (7, 10, 14, 17)],
    8: [(0, 4, 7, 11), (6, 9, 13, 18), (9, 13, 16, 21), (7, 11, 14, 19),
        (2, 6, 9, 14), (4, 7, 11, 16), (7, 11, 14, 19), (0, 4, 7, 14)],
}

# Distinct melodic contours (pitch offset, step_start_in_bar, duration_in_beats)
CHAPTER_MELODIES = {
    1: [
        (0, 0.0, 1.5), (7, 1.5, 1.0), (8, 2.5, 1.5),
        (5, 4.5, 1.5), (3, 6.0, 1.0), (1, 7.0, 1.0),
        (0, 8.0, 2.0), (12, 10.5, 1.5), (8, 12.0, 2.0), (7, 14.0, 2.0),
    ],
    2: [
        (0, 0.0, 1.0), (3, 1.0, 0.5), (7, 1.5, 1.5), (8, 3.0, 1.5), (7, 4.5, 1.5),
        (5, 6.0, 1.0), (3, 7.0, 0.5), (6, 7.5, 1.5), (5, 9.0, 1.5), (0, 10.5, 1.5),
    ],
    3: [
        (0, 0.0, 0.5), (7, 0.5, 0.5), (10, 1.0, 0.5), (12, 1.5, 0.75), (14, 2.25, 0.75), (10, 3.0, 1.0),
        (7, 4.0, 0.5), (12, 4.5, 0.5), (15, 5.0, 0.75), (14, 5.75, 0.75), (12, 6.5, 0.75), (9, 7.25, 0.75),
    ],
    4: [
        (0, 0.0, 1.0), (6, 1.0, 1.0), (7, 2.0, 1.0), (1, 3.0, 1.0), (0, 4.0, 1.0),
        (8, 5.0, 1.5), (6, 6.5, 1.5), (3, 8.0, 1.0), (1, 9.0, 1.0),
    ],
    5: [
        (0, 0.0, 1.5), (5, 1.5, 0.75), (7, 2.25, 0.75),
        (8, 3.0, 2.0), (7, 5.0, 1.0),
        (12, 6.0, 1.5), (10, 7.5, 0.75), (8, 8.25, 0.75),
        (7, 9.0, 2.0), (3, 11.0, 1.0),
    ],
    6: [
        (0, 0.0, 1.0), (4, 1.0, 1.0), (7, 2.0, 1.0), (8, 3.0, 1.5), (7, 4.5, 1.0), (4, 5.5, 1.5),
        (12, 7.0, 1.0), (10, 8.0, 1.0), (8, 9.0, 1.0), (7, 10.0, 1.5), (5, 11.5, 1.0), (4, 12.5, 1.5),
    ],
    7: [
        (12, 0.0, 1.25), (10, 1.25, 0.75), (7, 2.0, 1.5), (8, 3.5, 0.5),
        (5, 4.0, 1.5), (3, 5.5, 1.0), (2, 6.5, 1.5),
        (14, 8.0, 1.5), (12, 9.5, 1.0), (8, 10.5, 1.5), (7, 12.0, 2.5),
    ],
    8: [
        (0, 0.0, 1.0), (4, 1.0, 1.0), (7, 2.0, 1.0), (11, 3.0, 1.0),
        (12, 4.0, 1.5), (11, 5.5, 0.5), (9, 6.0, 1.0), (7, 7.0, 1.0),
        (14, 8.0, 1.5), (16, 9.5, 1.5), (11, 11.0, 1.0), (9, 12.0, 2.0), (7, 14.0, 2.0),
    ],
}


def hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


def add_voice(
    buf: np.ndarray,
    start: float,
    duration: float,
    midi: float,
    amp: float,
    pan: float = 0.0,
    voice: str = "glass_piano",
    attack: float = 0.015,
    release: float = 0.22,
) -> None:
    i = max(0, int(start * FS))
    n = min(len(buf) - i, max(0, int(duration * FS)))
    if n <= 0:
        return
    t = np.arange(n, dtype=np.float64) / FS
    f = hz(midi)
    w = 2.0 * np.pi * f * t

    if voice == "glass_piano":
        mod = 1.35 * np.exp(-t * 6.8) * np.sin(w * 2.0)
        sig = 0.68 * np.sin(w + mod) + 0.22 * np.sin(w * 3.0) * np.exp(-t * 9.0) + 0.10 * np.sin(w * 4.01)
    elif voice == "telemetry_bell":
        mod = 2.1 * np.exp(-t * 9.5) * np.sin(w * 3.5)
        sig = 0.64 * np.sin(w + mod) * np.exp(-t * 4.2) + 0.36 * np.sin(w * 2.0) * np.exp(-t * 6.0)
    elif voice == "fm_anvil":
        mod = 2.8 * np.exp(-t * 12.0) * np.sin(w * 2.76)
        sig = 0.62 * np.sin(w + mod) + 0.26 * np.sin(w * 1.414) * np.exp(-t * 8.0) + 0.12 * np.sin(w * 5.41)
    elif voice == "piston_brass":
        saw = 0.58 * np.sin(w) + 0.29 * np.sin(w * 2.0) + 0.14 * np.sin(w * 3.0)
        sig = np.tanh(saw * 1.55)
    elif voice == "arp_pulse":
        sig = 0.56 * np.tanh(2.1 * np.sin(w)) + 0.28 * np.sin(w * 2.0 + 0.4) + 0.16 * np.sin(w * 4.0)
    elif voice == "sync_lead":
        det = 2.0 * np.pi * (f * 1.005) * t
        sig = np.tanh(1.4 * (0.50 * np.sin(w) + 0.35 * np.sin(det) + 0.15 * np.sin(w * 3.0)))
    elif voice == "staccato_pluck":
        mod = 2.1 * np.exp(-t * 15.0) * np.sin(w * 3.01)
        sig = (0.72 * np.sin(w + mod) + 0.28 * np.sin(w * 2.5)) * np.exp(-t * 5.2)
    elif voice == "radar_ping":
        sig = (0.75 * np.sin(w) + 0.25 * np.sin(w * 4.0)) * np.exp(-t * 6.5)
    elif voice == "submerged_bell":
        vibr = 0.018 * np.sin(2.0 * np.pi * 4.4 * t)
        sig = 0.64 * np.sin(w * (1.0 + vibr)) + 0.24 * np.sin(w * 2.0) * np.exp(-t * 3.8) + 0.12 * np.sin(w * 3.0)
    elif voice == "hydro_horn":
        bend = 1.0 - 0.012 * np.exp(-t * 5.0)
        sig = 0.60 * np.sin(w * bend) + 0.28 * np.sin(w * 2.0 * bend) + 0.12 * np.sin(w * 3.0 * bend)
    elif voice == "reactor_brass":
        saw = 0.54 * np.sin(w) + 0.32 * np.sin(w * 2.0) + 0.20 * np.sin(w * 3.0) + 0.11 * np.sin(w * 4.0)
        sig = np.tanh(saw * 1.65)
    elif voice == "alarm_fm":
        lfo = 1.0 + 0.025 * np.sin(2.0 * np.pi * 6.0 * t)
        sig = 0.65 * np.sin(w * lfo + 1.2 * np.sin(w * 2.0)) + 0.35 * np.sin(w * 3.0)
    elif voice == "spire_harp":
        sig = (0.64 * np.sin(w) + 0.25 * np.sin(w * 2.0) + 0.11 * np.sin(w * 3.0)) * np.exp(-t * 3.0)
    elif voice == "cello_bow":
        vibr = 0.008 * np.sin(2.0 * np.pi * 5.2 * t)
        sig = np.tanh(1.3 * (0.58 * np.sin(w * (1.0 + vibr)) + 0.28 * np.sin(w * 2.0) + 0.14 * np.sin(w * 3.0)))
    elif voice == "nocturnal_lead":
        det1 = 2.0 * np.pi * (f * 1.0035) * t
        det2 = 2.0 * np.pi * (f * 0.9965) * t
        sig = 0.42 * np.sin(w) + 0.30 * np.sin(det1) + 0.28 * np.sin(det2) + 0.14 * np.sin(w * 2.0)
    elif voice == "sub_bass":
        sig = np.tanh(1.4 * (0.78 * np.sin(w) + 0.22 * np.sin(w * 2.0)))
    else:
        sig = 0.62 * np.sin(w) + 0.26 * np.sin(w * 2.004) + 0.12 * np.sin(w * 3.0)

    env = np.minimum(1.0, t / max(0.001, attack)) * np.minimum(1.0, np.maximum(0.0, duration - t) / max(0.001, release))
    out = (sig * env * amp).astype(np.float32)
    ang = (pan + 1.0) * np.pi / 4.0
    buf[i : i + n, 0] += np.cos(ang) * out
    buf[i : i + n, 1] += np.sin(ang) * out


def add_drum(
    buf: np.ndarray, start: float, kind: str, seed: int, vol: float = 0.12, pan: float = 0.0
) -> None:
    i = max(0, int(start * FS))
    if i >= len(buf):
        return
    dur = 0.28 if kind in ("kick", "tom") else (0.22 if kind in ("snare", "clang") else 0.08)
    n = min(int(dur * FS), len(buf) - i)
    t = np.arange(n, dtype=np.float64) / FS
    rng = np.random.default_rng(seed)

    if kind == "kick":
        phase = 2.0 * np.pi * (46.0 * t + 68.0 * (1.0 - np.exp(-36.0 * t)) / 36.0)
        sig = np.tanh(1.35 * np.sin(phase)) * np.exp(-15.0 * t)
    elif kind == "tom":
        phase = 2.0 * np.pi * (82.0 * t + 45.0 * (1.0 - np.exp(-24.0 * t)) / 24.0)
        sig = np.tanh(1.25 * np.sin(phase)) * np.exp(-11.0 * t)
    elif kind == "clang":
        sig = (
            0.50 * np.sin(2.0 * np.pi * 238.0 * t)
            + 0.33 * np.sin(2.0 * np.pi * 542.0 * t)
            + 0.24 * np.sin(2.0 * np.pi * 819.0 * t)
        ) * np.exp(-19.0 * t)
    elif kind == "snare":
        noise = rng.normal(0.0, 1.0, n)
        sig = (0.38 * np.sin(2.0 * np.pi * 188.0 * t) + 0.44 * noise) * np.exp(-21.0 * t)
    else:
        noise = rng.normal(0.0, 1.0, n)
        hp = np.r_[0.0, np.diff(noise)]
        sig = np.clip(hp, -2.0, 2.0) * np.exp(-54.0 * t) * 0.45

    ang = (pan + 1.0) * np.pi / 4.0
    buf[i : i + n, 0] += (sig * vol * np.cos(ang)).astype(np.float32)
    buf[i : i + n, 1] += (sig * vol * np.sin(ang)).astype(np.float32)


def finalize_pair(quiet: np.ndarray, rhythm: np.ndarray, ch: int, bpm: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    frames = len(quiet)
    duration = frames / FS
    for delay_s, fb, p_swap in ((0.27, 0.11, True), (0.41, 0.06, False)):
        shift = int(delay_s * FS)
        if p_swap:
            q_copy = quiet.copy()
            quiet[:, 0] += fb * np.roll(q_copy[:, 1], shift)
            quiet[:, 1] += fb * np.roll(q_copy[:, 0], shift)
        else:
            r_copy = rhythm.copy()
            rhythm[:, 0] += fb * np.roll(r_copy[:, 0], shift)
            rhythm[:, 1] += fb * np.roll(r_copy[:, 1], shift)

    both = quiet * 0.84 + rhythm * 0.67
    peak = float(np.max(np.abs(both)))
    gain = min(1.85, 0.78 / max(1e-7, peak))
    quiet = np.tanh(quiet * gain).astype(np.float32)
    rhythm = np.tanh(rhythm * gain).astype(np.float32)

    fade = min(int(0.11 * FS), frames // 12)
    ramp = (0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, fade))).astype(np.float32)
    for arr in (quiet, rhythm):
        arr[:fade] *= ramp[:, None]
        arr[-fade:] *= ramp[::-1, None]

    mix = np.tanh(0.84 * quiet + 0.67 * rhythm).astype(np.float32)
    metrics = {
        "chapter": ch,
        "bpm": bpm,
        "duration_seconds": round(duration, 4),
        "frames": frames,
        "rate": FS,
        "channels": 2,
        "quiet_peak": round(float(np.max(np.abs(quiet))), 4),
        "rhythm_peak": round(float(np.max(np.abs(rhythm))), 4),
        "mix_peak": round(float(np.max(np.abs(mix))), 4),
        "quiet_rms": round(float(np.sqrt(np.mean(quiet.astype(np.float64) ** 2))), 4),
        "preview_rms": round(float(np.sqrt(np.mean(mix.astype(np.float64) ** 2))), 4),
        "quiet_seam": round(float(np.max(np.abs(quiet[0] - quiet[-1]))), 6),
        "rhythm_seam": round(float(np.max(np.abs(rhythm[0] - rhythm[-1]))), 6),
    }
    return quiet, rhythm, mix, metrics


def render_chapter(spec: tuple) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    ch, bpm, beats_per_bar, bars, root, _mode_name, lead_voice, counter_voice = spec
    beat = 60.0 / bpm
    total_beats = beats_per_bar * bars
    frames = int(round(total_beats * beat * FS))
    quiet = np.zeros((frames, 2), dtype=np.float32)
    rhythm = np.zeros_like(quiet)

    chords = CHORD_PROGRESSIONS[ch]
    melody = CHAPTER_MELODIES[ch]

    # 1. Chapter-specific harmonic framing & meter-locked pad architecture
    for bar in range(bars):
        b_start = bar * beats_per_bar * beat
        bar_dur = beats_per_bar * beat
        chord = chords[bar % len(chords)]
        section = (bar * 4) // bars  # 0=Intro, 1=Theme A, 2=Bridge, 3=Climax
        pad_amp = (0.032, 0.042, 0.036, 0.048)[section]
        for idx, deg in enumerate(chord):
            oct_shift = -12 if idx == 0 else (12 if section == 3 and idx == len(chord) - 1 else 0)
            pan = -0.50 + 1.0 * (idx / max(1, len(chord) - 1))
            add_voice(
                quiet, b_start, bar_dur * 0.96, root + deg + oct_shift,
                pad_amp, pan=pan,
                voice="cello_bow" if ch == 7 else ("hydro_horn" if ch == 5 else "pad"),
                attack=0.28 * beat, release=0.40 * beat,
            )

    # 2. Chapter-specific Melodic Phrases & Counter-Melodies (2-bar or 4-bar phrases)
    phrase_beats = beats_per_bar * (4 if ch in (1, 7, 8) else 2)
    num_phrases = max(1, int(total_beats // phrase_beats))
    for p_idx in range(num_phrases):
        p_start = p_idx * phrase_beats * beat
        section = (p_idx * 4) // num_phrases
        transpose = 0 if section in (0, 1) else (5 if section == 2 else 12)
        for deg, rel_beat, dur_beats in melody:
            if rel_beat >= phrase_beats:
                continue
            t0 = p_start + rel_beat * beat
            pan = -0.35 if int(rel_beat * 2) % 2 == 0 else 0.35
            add_voice(
                quiet, t0, dur_beats * beat * 0.92,
                root + deg + (12 if section == 3 and ch not in (2, 6) else 0),
                0.054 if section == 3 else 0.043,
                pan=pan, voice=lead_voice, attack=0.010, release=0.20,
            )
            # Counter-voice answer in Development & Climax sections
            if section in (1, 3):
                add_voice(
                    rhythm, t0 + 0.5 * beat, dur_beats * beat * 0.65,
                    root + deg + transpose,
                    0.036, pan=-pan, voice=counter_voice, attack=0.008, release=0.14,
                )

    # 3. Chapter-Specific Bass & Percussion Groove by Meter
    for bar in range(bars):
        b_start = bar * beats_per_bar * beat
        section = (bar * 4) // bars
        chord_root = chords[bar % len(chords)][0]

        if ch == 1:
            # 4/4 Sparse Diagnostic: low heartbeat on beat 0 & 2.5, high sonar tick on 3.5
            add_voice(quiet, b_start, 1.8 * beat, root + chord_root - 24, 0.052, 0.0, "sub_bass", 0.03, 0.30)
            add_drum(rhythm, b_start, "kick", 1000 + bar, 0.085)
            add_drum(rhythm, b_start + 2.5 * beat, "kick", 1100 + bar, 0.065)
            if section >= 1:
                add_voice(rhythm, b_start + 3.5 * beat, 0.35 * beat, root + 24, 0.035, 0.40, "telemetry_bell", 0.004, 0.12)
                for sub in range(8):
                    if sub in (2, 5, 7):
                        add_drum(rhythm, b_start + sub * 0.5 * beat, "hat", 1200 + bar * 8 + sub, 0.028, -0.3)

        elif ch == 2:
            # 6/8 Compound Industrial Foundry (beats 0..5): heavy kick on 0, FM anvil clang on 3
            for b in range(6):
                t0 = b_start + b * beat
                b_note = (0, 3, 7, 0, 5, 3)[b]
                add_voice(rhythm, t0, 0.45 * beat, root + chord_root + b_note - 12, 0.048, (-0.2, 0.2)[b % 2], "sub_bass", 0.008, 0.12)
                if b == 0:
                    add_drum(rhythm, t0, "kick", 2000 + bar * 6 + b, 0.12)
                elif b == 3:
                    add_drum(rhythm, t0, "clang", 2100 + bar * 6 + b, 0.095, 0.25)
                elif b in (2, 5):
                    add_drum(rhythm, t0, "hat", 2200 + bar * 6 + b, 0.038, -0.25)

        elif ch == 3:
            # 4/4 Driving 16th-Note Power Grid Sequencer
            arp_steps = (0, 7, 10, 12, 7, 10, 14, 12, 0, 7, 10, 15, 14, 12, 10, 7)
            for s16 in range(16):
                t0 = b_start + s16 * 0.25 * beat
                deg = arp_steps[s16]
                add_voice(
                    rhythm if s16 % 2 == 1 else quiet,
                    t0, 0.22 * beat, root + chord_root + deg,
                    0.038 if s16 % 4 == 0 else 0.028,
                    pan=(-0.45 if s16 % 2 == 0 else 0.45),
                    voice="arp_pulse", attack=0.004, release=0.06,
                )
                if s16 % 2 == 0:
                    add_voice(rhythm, t0, 0.20 * beat, root + chord_root - 12 + (12 if s16 % 4 == 2 else 0), 0.046, 0.0, "sub_bass", 0.005, 0.08)
            for b in range(4):
                t0 = b_start + b * beat
                if b in (0, 2):
                    add_drum(rhythm, t0, "kick", 3000 + bar * 4 + b, 0.11)
                else:
                    add_drum(rhythm, t0, "snare", 3100 + bar * 4 + b, 0.070)
                add_drum(rhythm, t0 + 0.5 * beat, "hat", 3200 + bar * 4 + b, 0.036)

        elif ch == 4:
            # 5/4 Asymmetric Surveillance Grid (3+2 grouping: accents on beats 0 and 3)
            bass_5 = (0, 7, 6, 1, 3)
            for b in range(5):
                t0 = b_start + b * beat
                add_voice(
                    quiet if b in (0, 3) else rhythm,
                    t0, 0.42 * beat, root + chord_root + bass_5[b] - 12,
                    0.048, pan=(-0.25 if b < 3 else 0.25), voice="staccato_pluck", attack=0.006, release=0.14,
                )
                if b in (0, 3):
                    add_drum(rhythm, t0, "kick", 4000 + bar * 5 + b, 0.095)
                if b == 4:
                    add_drum(rhythm, t0, "snare", 4100 + bar * 5 + b, 0.060, 0.2)
                    add_voice(quiet, t0 + 0.5 * beat, 0.4 * beat, root + 18, 0.032, -0.4, "radar_ping", 0.005, 0.15)

        elif ch == 5:
            # 3/4 Submerged Hydraulic Waltz (deep swell on beat 0, metallic pipe resonance on beat 2)
            add_voice(quiet, b_start, 2.6 * beat, root + chord_root - 24, 0.056, 0.0, "sub_bass", 0.08, 0.45)
            add_drum(rhythm, b_start, "kick", 5000 + bar, 0.10)
            add_drum(rhythm, b_start + 2.0 * beat, "clang", 5100 + bar, 0.068, -0.3)
            if section >= 1:
                add_voice(rhythm, b_start + 1.0 * beat, 0.8 * beat, root + chord_root - 12 + 7, 0.040, 0.25, "submerged_bell", 0.01, 0.25)

        elif ch == 6:
            # 7/8 Urgent Core Collapse (2+2+3 eighth-note grouping: 0, 1.0, 2.0 beats in 3.5-beat bar, or 7 beats at 134 BPM)
            accents = (0, 2, 4)
            bass_7 = (0, 0, 4, 7, 8, 7, 4)
            for b in range(7):
                t0 = b_start + b * beat
                add_voice(
                    rhythm, t0, 0.40 * beat, root + chord_root + bass_7[b] - 12,
                    0.054 if b in accents else 0.038, pan=0.0, voice="reactor_brass", attack=0.005, release=0.10,
                )
                if b in (0, 2):
                    add_drum(rhythm, t0, "kick", 6000 + bar * 7 + b, 0.12)
                elif b == 4:
                    add_drum(rhythm, t0, "clang", 6100 + bar * 7 + b, 0.095, 0.2)
                elif b == 6:
                    add_drum(rhythm, t0, "snare", 6200 + bar * 7 + b, 0.075, -0.2)

        elif ch == 7:
            # 4/4 Elegiac Broken-Time Spire Harp Arpeggio & Cello Counter-Melody
            harp_arp = (0, 3, 7, 10, 14, 10, 7, 3)
            for s8 in range(8):
                t0 = b_start + s8 * 0.5 * beat
                add_voice(
                    quiet, t0, 0.65 * beat, root + chord_root + harp_arp[s8],
                    0.038, pan=-0.40 + 0.11 * s8, voice="spire_harp", attack=0.006, release=0.22,
                )
            add_voice(quiet, b_start, 3.6 * beat, root + chord_root - 12, 0.046, 0.25, "cello_bow", 0.25, 0.45)
            if section >= 1:
                add_drum(rhythm, b_start, "kick", 7000 + bar, 0.085)
                add_drum(rhythm, b_start + 1.75 * beat, "kick", 7100 + bar, 0.065)
                add_drum(rhythm, b_start + 2.5 * beat, "snare", 7200 + bar, 0.058)

        elif ch == 8:
            # 4/4 Nocturnal Horizon Synthwave (driving octave bass + tom/snare cadence)
            for s8 in range(8):
                t0 = b_start + s8 * 0.5 * beat
                octv = -12 if s8 % 2 == 1 else -24
                add_voice(rhythm, t0, 0.42 * beat, root + chord_root + octv, 0.048, 0.0, "sub_bass", 0.006, 0.12)
            for b in range(4):
                t0 = b_start + b * beat
                if b in (0, 2):
                    add_drum(rhythm, t0, "kick", 8000 + bar * 4 + b, 0.11)
                else:
                    add_drum(rhythm, t0, "snare", 8100 + bar * 4 + b, 0.075)
                if section == 3 and b == 3:
                    add_drum(rhythm, t0 + 0.5 * beat, "tom", 8200 + bar, 0.085, 0.3)

    # 4. Subtle Chapter Atmospheric Bed
    rng = np.random.default_rng(7700 + ch)
    noise = rng.normal(0.0, 1.0, (frames, 2)).astype(np.float32)
    cutoff = (210, 330, 580, 250, 390, 310, 490, 220)[ch - 1]
    lo = sosfilt(butter(2, cutoff, fs=FS, btype="lowpass", output="sos"), noise, axis=0).astype(np.float32)
    quiet += lo * 0.010

    return finalize_pair(quiet, rhythm, ch, bpm)


def render_finale_ascent() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Bespoke Level 80 Finale Ascent & Countdown score (128 BPM, D Dorian -> D Major resolution)."""
    bpm = 128
    root = 50
    beat = 60.0 / bpm
    total_beats = 64
    frames = int(round(total_beats * beat * FS))
    quiet = np.zeros((frames, 2), dtype=np.float32)
    rhythm = np.zeros_like(quiet)

    prog = [
        (0, 3, 7, 14), (5, 9, 12, 16), (7, 10, 14, 19), (8, 12, 15, 20),
        (0, 4, 7, 14), (5, 9, 12, 18), (9, 12, 16, 21), (7, 11, 14, 19),
    ]
    finale_hook = (0, 7, 8, 12, 10, 7, 5, 7, 0, 7, 11, 12, 14, 12, 9, 7)

    for bar in range(8):
        b_start = bar * 8.0 * beat
        for idx, deg in enumerate(prog[bar]):
            add_voice(
                quiet, b_start, 7.9 * beat, root + deg + (-12 if idx == 0 else 0),
                0.048, pan=(-0.5, -0.18, 0.18, 0.5)[idx], voice="nocturnal_lead",
                attack=0.22 * beat, release=0.40 * beat,
            )

    for step in range(total_beats * 2):
        t0 = step * 0.5 * beat
        bar = step // 16
        deg = finale_hook[step % 16]
        add_voice(
            quiet, t0, 0.45 * beat, root + deg + (12 if bar >= 4 else 0),
            0.054, pan=(-0.32 if step % 2 == 0 else 0.32), voice="glass_piano",
            attack=0.006, release=0.16,
        )
        add_voice(
            rhythm, t0, 0.38 * beat, root + prog[bar][step % 4] - 12,
            0.052, pan=0.0, voice="sub_bass", attack=0.006, release=0.12,
        )
        if step % 2 == 1:
            add_voice(
                rhythm, t0, 0.30 * beat, root + deg + 12,
                0.038, pan=(0.40 if step % 4 == 1 else -0.40), voice="arp_pulse",
                attack=0.005, release=0.10,
            )

    for b in range(total_beats):
        t0 = b * beat
        if b % 4 in (0, 2, 3):
            add_drum(rhythm, t0, "kick", seed=9000 + b, vol=0.12)
        if b % 4 in (1, 3):
            add_drum(rhythm, t0, "snare", seed=9500 + b, vol=0.075)
        for sub in (0.0, 0.5):
            add_drum(rhythm, t0 + sub * beat, "hat", seed=9800 + b * 2 + int(sub * 2), vol=0.036)

    return finalize_pair(quiet, rhythm, 80, bpm)


def emit_audio_pair(signal: np.ndarray, ogg_path: Path, temporary: Path, quality: str = "5", write_wav_copy: bool = True) -> None:
    ogg_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path = ogg_path.with_suffix(".wav") if write_wav_copy else (temporary / (ogg_path.stem + ".wav"))
    pcm = np.round(np.clip(signal, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(str(wav_path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(FS)
        out.writeframes(pcm.tobytes())
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required to encode OGG music; existing WAV fallbacks are left unchanged")
    if shutil.which("ffmpeg"):
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(wav_path), "-c:a", "libvorbis", "-q:a", quality, str(ogg_path),
            ],
            check=True,
        )
    if not write_wav_copy and wav_path.exists():
        wav_path.unlink()


def main() -> None:
    report = []
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        for spec in SPECS:
            ch = spec[0]
            q, r, m, metrics = render_chapter(spec)
            emit_audio_pair(q, MUSIC / f"chapter_{ch}_quiet.ogg", tmp, write_wav_copy=False)
            emit_audio_pair(r, MUSIC / f"chapter_{ch}_rhythm.ogg", tmp, write_wav_copy=False)
            emit_audio_pair(m, PREVIEWS / f"Chapter_{ch:02d}_preview.ogg", tmp, write_wav_copy=False)
            report.append(metrics)
            print(
                f"chapter {ch} ({spec[5]}): {metrics['duration_seconds']:.2f}s, stereo {FS} Hz, "
                f"peak {metrics['mix_peak']:.3f}, rms {metrics['preview_rms']:.3f}",
                flush=True,
            )
        fq, fr, fm, f_metrics = render_finale_ascent()
        emit_audio_pair(fq, MUSIC / "finale_ascent_quiet.ogg", tmp, write_wav_copy=False)
        emit_audio_pair(fr, MUSIC / "finale_ascent_rhythm.ogg", tmp, write_wav_copy=False)
        emit_audio_pair(fm, PREVIEWS / "Chapter_80_Finale_preview.ogg", tmp, write_wav_copy=False)
        print(
            f"finale 80: {f_metrics['duration_seconds']:.2f}s, stereo {FS} Hz, "
            f"peak {f_metrics['mix_peak']:.3f}, rms {f_metrics['preview_rms']:.3f}",
            flush=True,
        )

    qa_dir = ROOT / "docs" / "polish_qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    (qa_dir / "audio_metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
