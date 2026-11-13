#!/usr/bin/env python3
"""Make a sound effect game-ready: trim the silence before it starts, normalise
it to the same loudness as LF2's own effects, and cut it short with a fade.

    python tools/prepare_sfx.py IN.wav OUT.wav [MAX_SECONDS]

IN.wav is a PCM WAV (convert mp3s first with tools/to_wav.ps1). Frame sounds
play when a frame starts, so a sound that begins 0.4 s in feels missing, and a
quiet one is drowned by the game's own (near full-scale) effects.
"""
import struct, sys, wave

LEAD_THRESHOLD = 0.06   # of the peak: anything quieter before the onset is cut
TARGET_PEAK = 0.92      # of full scale
FADE_SECONDS = 0.08


def main(src, dst, max_seconds=1.2):
    w = wave.open(src)
    ch, rate, width = w.getnchannels(), w.getframerate(), w.getsampwidth()
    assert width == 2, 'expects 16-bit PCM'
    data = w.readframes(w.getnframes())
    samples = list(struct.unpack(f'<{len(data) // 2}h', data))
    peak = max(abs(x) for x in samples) or 1
    onset = next(i for i, x in enumerate(samples) if abs(x) > peak * LEAD_THRESHOLD)
    onset -= onset % ch
    onset = max(0, onset - int(rate * 0.01) * ch)          # keep 10 ms before the attack
    samples = samples[onset:onset + int(rate * max_seconds) * ch]
    gain = TARGET_PEAK * 32767 / peak
    fade = int(rate * FADE_SECONDS) * ch
    n = len(samples)
    out = []
    for i, x in enumerate(samples):
        k = gain * (min(1.0, (n - i) / fade) if n - i < fade else 1.0)
        out.append(max(-32768, min(32767, int(x * k))))
    o = wave.open(dst, 'wb')
    o.setnchannels(ch); o.setsampwidth(2); o.setframerate(rate)
    o.writeframes(struct.pack(f'<{len(out)}h', *out))
    o.close()
    print(f'{dst}: trimmed {onset / ch / rate:.2f}s of lead-in, x{gain:.2f} gain, {len(out) / ch / rate:.2f}s long')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) == 4 else 1.2)
