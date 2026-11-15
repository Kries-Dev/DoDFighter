#!/usr/bin/env python3
"""Our stage-mode file: readable source -> the encrypted .dat the engine reads.

    python tools/stage_dat.py mods/darthnox/stage.txt mods/darthnox/assets/stage.dat

mods/darthnox/stage.txt is LF2's data/stage.dat, decrypted, with our changes
(stage 1 on our stages: scroll bounds and item/prisoner x scaled to the stage,
our music; see the "# DoD" comments in it). Edit it, run this, and copy the mod.
The engine only reads stage files in LF2's encryption: 123 bytes of padding,
then each byte shifted by the key (the same as object .dat files).
"""
import sys

KEY = b'SiuHungIsAGoodBearBecauseHeIsVeryGood'


def encrypt(text):
    return bytes(123) + bytes((b + KEY[(n + 123) % len(KEY)]) % 256 for n, b in enumerate(text))


def decrypt(data):
    return bytes((data[n] - KEY[n % len(KEY)]) % 256 for n in range(123, len(data)))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    data = open(src, 'rb').read()
    if src.lower().endswith('.dat'):
        open(out, 'wb').write(decrypt(data))
    else:
        open(out, 'wb').write(encrypt(data.replace(b'\r\n', b'\n')))
    print(f'{out}: {len(data)} bytes in')
