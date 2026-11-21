#!/usr/bin/env python3
"""Wygeneruj pliki testowe w dane/ (czysty Python: struct + zlib, bez libpng).

Pliki są w repozytorium; skrypt pozwala je odtworzyć i pokazuje, z czego wynikają
oczekiwane wartości pikseli w testach. Uruchom: python3 narzedzia/generuj_dane.py
"""

from pathlib import Path
import struct
import zlib

DANE = Path(__file__).resolve().parent.parent / "dane"


def chunk(typ, dane):
    return struct.pack(">I", len(dane)) + typ + dane + struct.pack(">I", zlib.crc32(typ + dane) & 0xFFFFFFFF)


def png(szer, wys, glebia, typ_koloru, wiersze, przeplot=0, dodatkowe=()):
    """wiersze: lista bajtów każdego wiersza (bez bajtu filtra); przeplot=1 to Adam7."""
    ihdr = struct.pack(">IIBBBBB", szer, wys, glebia, typ_koloru, 0, 0, przeplot)
    if przeplot == 0:
        surowe = b"".join(b"\x00" + w for w in wiersze)
    else:
        bpp = len(wiersze[0]) // szer  # bajtów na piksel (tylko głębie >= 8)
        przebiegi = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))
        surowe = b""
        for x0, y0, dx, dy in przebiegi:
            for y in range(y0, wys, dy):
                xs = range(x0, szer, dx)
                if len(xs) == 0:
                    continue
                surowe += b"\x00" + b"".join(wiersze[y][x * bpp:(x + 1) * bpp] for x in xs)
    tresc = chunk(b"IHDR", ihdr)
    for typ, dane in dodatkowe:
        tresc += chunk(typ, dane)
    tresc += chunk(b"IDAT", zlib.compress(surowe, 9)) + chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + tresc


def zapisz(nazwa, dane):
    (DANE / nazwa).write_bytes(dane)
    print(f"{nazwa}: {len(dane)} B")


def main():
    DANE.mkdir(exist_ok=True)

    # Paleta 4x2 z przezroczystością (tRNS): czerwony a=255, zielony a=128, niebieski a=0, biały a=255.
    paleta = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255])
    zapisz("paleta.png", png(4, 2, 8, 3, [bytes([0, 1, 2, 3]), bytes([3, 2, 1, 0])],
                             dodatkowe=[(b"PLTE", paleta), (b"tRNS", bytes([255, 128, 0]))]))

    # Szarość z alpha 3x1: (0, a=255), (128, a=128), (255, a=0).
    zapisz("szarosc_alpha.png", png(3, 1, 8, 4, [bytes([0, 255, 128, 128, 255, 0])]))

    # RGB 16 bitów 3x1, bez gAMA; wartości to wielokrotności 257, więc w 8 bitach dają dokładnie k:
    # (0,0,0), (65535, 128*257, 64*257) -> (255,128,64), (200*257, 65535, 0) -> (200,255,0).
    zapisz("rgb16.png", png(3, 1, 16, 2, [struct.pack(">9H", 0, 0, 0, 65535, 128 * 257, 64 * 257, 200 * 257, 65535, 0)]))

    # Przeplot Adam7, RGBA 5x5: piksel (x, y) = (50x, 50y, 20(x+y), 255-10x).
    wiersze = [bytes(v for x in range(5) for v in (50 * x, 50 * y, 20 * (x + y), 255 - 10 * x)) for y in range(5)]
    zapisz("przeplot.png", png(5, 5, 8, 6, wiersze, przeplot=1))

    # Duszek 16x16 RGB (bez alpha) na tle magenta FF00FF - wejście dla polecenia "klucz".
    tlo, zolty, pomarancz, czarny, bialy = (255, 0, 255), (250, 210, 40), (240, 130, 20), (20, 20, 20), (255, 255, 255)
    rysunek = [
        "................",
        "......YYYY......",
        ".....YYYYYY.....",
        "....YYYYWBYY....",
        "....YYYYBBYYOO..",
        "....YYYYYYYYOOO.",
        ".....YYYYYYOO...",
        "......YYYY......",
        "...YYYYYYYYYY...",
        "..YYYYYYYYYYYY..",
        "..YYYYYYYYYYYYY.",
        "..YYYYYYYYYYYY..",
        "...YYYYYYYYYY...",
        "....YYYYYYYY....",
        ".....OO..OO.....",
        "................",
    ]
    kolory = {".": tlo, "Y": zolty, "O": pomarancz, "B": czarny, "W": bialy}
    zapisz("duszek.png", png(16, 16, 8, 2, [bytes(v for z in w for v in kolory[z]) for w in rysunek]))

    # Krajobraz 64x40 RGBA: gradient nieba, półprzezroczyste słońce, zielona ziemia.
    wiersze = []
    for y in range(40):
        w = b""
        for x in range(64):
            if y >= 28:
                p = (40, 140 + (x % 8) * 4, 50, 255)
            elif (x - 46) ** 2 + (y - 10) ** 2 <= 49:
                p = (255, 220, 60, 200)
            else:
                p = (60 + y * 3, 120 + y * 3, 230, 255)
            w += bytes(p)
        wiersze.append(w)
    poprawny = png(64, 40, 8, 6, wiersze)
    zapisz("krajobraz.png", poprawny)

    # Uszkodzony: jeden bajt skompresowanych danych IDAT zmieniony (zepsuty strumień zlib, zła też suma CRC).
    poz = poprawny.index(b"IDAT") + 4 + 10
    zapisz("uszkodzony.png", poprawny[:poz] + bytes([poprawny[poz] ^ 0xFF]) + poprawny[poz + 1:])

    # Zła suma CRC: dane IDAT poprawne, zmieniony ostatni bajt CRC tego fragmentu.
    koniec_idat = poprawny.index(b"IEND") - 4
    zapisz("zle_crc.png", poprawny[:koniec_idat - 1] + bytes([poprawny[koniec_idat - 1] ^ 0xFF]) + poprawny[koniec_idat:])

    # Ucięty: plik kończy się w środku danych IDAT.
    zapisz("uciety.png", poprawny[:poprawny.index(b"IDAT") + 40])

    # Nie PNG: zwykły tekst z rozszerzeniem .png.
    zapisz("nie_png.png", "To nie jest plik PNG.\n".encode())

    # Bomba wymiarów: poprawny nagłówek 100000x100000 RGBA (40 GB pikseli), dane prawie puste.
    ihdr = struct.pack(">IIBBBBB", 100000, 100000, 8, 6, 0, 0, 0)
    zapisz("bomba.png", b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(b"\x00" * 16)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    main()
