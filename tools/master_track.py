#!/usr/bin/env python3
"""Master a Suno track towards a reference track's sound: match EQ + stereo width.

    python tools/master_track.py IN.wav REFERENCE.wav OUT.wav [--width 0.6] [--max-gain 9]

Suno's downloads are mono (left = right) and, next to the SFA3 soundtrack, dull and
boxy. This shapes IN's long-term spectrum towards REFERENCE's (third-octave bands,
gains limited to +-max-gain dB and smoothed, applied as a linear-phase filter), then
widens it: below 200 Hz stays centred (bass and kick), above it a decorrelated copy
of the signal (flat magnitude, random phase, ~25 ms) is added as the side channel,
so layers spread left and right while left + right stays exactly the original (mono
safe). Finally the level is matched to the reference with a soft peak limiter.
WAV in and out (16-bit); convert MP3 with tools/to_wav.ps1, then to WMA with
tools/to_wma.ps1. Needs numpy.
"""
import argparse
import wave
import numpy as np


def read(path):
    with wave.open(path) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        x = np.frombuffer(w.readframes(n), {2: np.int16, 4: np.int32}[sw]).astype(np.float64)
    x = x.reshape(-1, ch) / (2 ** (8 * sw - 1))
    return sr, x if ch == 2 else np.repeat(x, 2, axis=1)


def write(path, sr, x):
    y = np.clip(np.rint(x * 32767), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


def ltas(mono, n=8192):
    frames = np.lib.stride_tricks.sliding_window_view(mono, n)[::n // 2] * np.hanning(n)
    return np.mean(np.abs(np.fft.rfft(frames, axis=1)) ** 2, axis=0)


def fft_filter(x, h):
    n = len(x) + len(h) - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[:n]
    d = (len(h) - 1) // 2
    return y[d:d + len(x)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('ref'); ap.add_argument('out')
    ap.add_argument('--width', type=float, default=0.6, help='side level, 0 = mono, 1 = very wide')
    ap.add_argument('--max-gain', type=float, default=9.0, help='EQ limit in dB')
    a = ap.parse_args()
    sr, x = read(a.inp)
    rsr, ref = read(a.ref)
    assert sr == rsr, 'sample rates differ'
    mono = x.mean(axis=1)
    N = 8192
    f = np.fft.rfftfreq(N, 1 / sr)
    pin, pref = ltas(mono, N), ltas(ref.mean(axis=1), N)
    # third-octave smoothed ratio, loudness-neutral over 100 Hz - 10 kHz
    gain_db = np.zeros_like(f)
    for i, fc in enumerate(f):
        if fc < 25:
            continue
        sel = (f >= fc / 2 ** (1 / 6)) & (f <= fc * 2 ** (1 / 6))
        gain_db[i] = 10 * np.log10(pref[sel].mean() / max(pin[sel].mean(), 1e-20))
    body = (f > 100) & (f < 10000)
    gain_db -= np.average(gain_db[body], weights=pin[body])
    gain_db = np.clip(gain_db, -a.max_gain, a.max_gain)
    gain_db[f < 25] = gain_db[np.argmax(f >= 25)]
    k = np.exp(-0.5 * (np.arange(-40, 41) / 12) ** 2); k /= k.sum()
    gain_db = np.convolve(np.pad(gain_db, 40, mode='edge'), k, 'valid')
    h = np.fft.fftshift(np.fft.irfft(10 ** (gain_db / 20), N)) * np.hanning(N)
    eq = fft_filter(mono, h)
    # widening: decorrelated side above 200 Hz
    rng = np.random.default_rng(7)
    L = int(0.025 * sr)
    spec = np.exp(1j * rng.uniform(-np.pi, np.pi, L // 2 + 1)); spec[0] = 0
    dec = np.fft.irfft(spec, L) * np.hanning(L)
    dec /= np.sqrt(np.sum(dec ** 2))
    hp_spec = (np.fft.rfftfreq(4096, 1 / sr) > 200).astype(float)
    hp = np.fft.fftshift(np.fft.irfft(hp_spec, 4096)) * np.hanning(4096)
    side = fft_filter(fft_filter(eq, hp), dec) * a.width
    out = np.stack([eq + side, eq - side], axis=1)
    # level: match reference RMS, soft-limit peaks above -1 dBFS
    out *= np.sqrt(np.mean(ref ** 2)) / np.sqrt(np.mean(out ** 2))
    t = 10 ** (-1 / 20)
    over = np.abs(out) > t * 0.8
    out[over] = np.sign(out[over]) * (t * 0.8 + t * 0.2 * np.tanh((np.abs(out[over]) - t * 0.8) / (t * 0.2)))
    write(a.out, sr, out)
    bands = [(60, 250), (250, 500), (500, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
    print('EQ applied:', ', '.join(f'{lo}-{hi} Hz {np.mean(gain_db[(f >= lo) & (f < hi)]):+.1f} dB' for lo, hi in bands))
    print(f'L/R correlation {np.corrcoef(out[:, 0], out[:, 1])[0, 1]:.2f} (reference {np.corrcoef(ref[:, 0], ref[:, 1])[0, 1]:.2f})')


if __name__ == '__main__':
    main()
