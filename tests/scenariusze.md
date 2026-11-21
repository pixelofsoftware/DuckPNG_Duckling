# Scenariusze sprawdzenia

Próby z 2026-11-21 na macOS 27.2 (Apple Silicon), `duckc 0.3-alpha (83882805a 2026-11-20)`, libpng 1.6.50 (Homebrew), wariant natywny, po `python3 build.py --target all --output build`.

| Scenariusz | Dane lub czynności | Oczekiwany wynik | Komenda lub procedura | Otrzymany wynik |
| --- | --- | --- | --- | --- |
| Zapis i ponowny odczyt | obraz 4x3 z alpha 0, 1, 128, 254, 255; obraz 37x23 z losowymi kanałami; obraz 1x1 | identyczne wymiary i wszystkie bajty; plik w formacie kolor + alpha | `run.py --target tests`, przykład | zgodny - OK |
| Alpha nieprzemnożona | piksel (200, 100, 50, 0) | po odczycie (200, 100, 50, 0) | testy | zgodny - OK |
| Konwersje do RGBA8 | `paleta.png` (tRNS), `szarosc_alpha.png`, `rgb16.png`, `przeplot.png` (Adam7), `duszek.png` (RGB) | wartości z `narzedzia/generuj_dane.py`; 16 bitów: v·255/65535; brak alpha = 255 | testy | zgodny - OK |
| Sprawdzenie rozmiaru | 536870911/536870912 x 1; 500000000 x 2^62; 1 x 2^31; 8192 x 8192/8193 | 2147483644 / poza zakresem; poza zakresem (przed mnożeniem); poza zakresem; 268435456 / ponad limit | testy, przykład | zgodny - OK |
| Bomba wymiarów | `dane/bomba.png`: poprawny nagłówek 100000x100000, 68 bajtów | `ZA_DUZY` bez przydziału 40 GB; narzędzie: kod 4 | testy; `printf 'info\ndane/bomba.png\n' \| python3 run.py --build build --workdir .` | `obraz 100000x100000 RGBA8 potrzebuje 40000000000 bajtow, limit to 268435456`, kod 4 - OK |
| Brakujący plik | `dane/nie_ma_takiego.png` | `BRAK_PLIKU` z komunikatem libpng; narzędzie: kod 3 | testy, narzędzie | `No such file or directory`, kod 3 - OK |
| Niepoprawny PNG | plik tekstowy; zepsute dane IDAT; zła suma CRC; ucięty plik | `NIEPOPRAWNY_PNG` ze skopiowanym komunikatem; narzędzie: kod 4 | testy, narzędzie | `Not a PNG file`, `IDAT: invalid code lengths set`, `IDAT: CRC error`, `Read Error` - OK |
| Błędy zapisu | bufor 1 bajt dla 2x2; obraz 0x0; katalog nie istnieje | `BLEDNE_PARAMETRY` bez wywołania biblioteki (plik nie powstaje); `BLAD_ZAPISU` z komunikatem; narzędzie: kod 5 | testy, narzędzie | zgodny, `No such file or directory`, kod 5 - OK |
| Zwalnianie zasobów | testy (w tym 500 cykli odczytu, 3 rodzajów błędów i zapisu) pod `leaks --atExit` | 0 wycieków | `cd build && leaks --atExit -- ./tests-native/package_llvm.exe` | `0 leaks for 0 total leaked bytes` - OK |
| Kontrola ujemna sprawdzenia wycieków | kopia z usuniętym `png_image_free` po odrzuceniu nagłówka | `leaks` wykrywa wycieki | jak wyżej, na zmienionej kopii | `1506 leaks for 867456 total leaked bytes` - sprawdzenie działa |
| Praktyczne zastosowanie | `klucz FF00FF` na `dane/duszek.png`; `pomniejsz` na `dane/krajobraz.png`; `szarosc` na `dane/paleta.png` | 136 z 256 pikseli przezroczystych; 64x40 → 32x20; zapisane pliki wczytują się do identycznych bajtów; `sips` widzi alpha | narzędzie, `sips -g hasAlpha` | zgodny, kod 0 - OK |
| Złe parametry narzędzia | `klucz XYZ` | komunikat, kod 2 | narzędzie | zgodny - OK |
| Testy | 35 sprawdzeń | `Bledy: 0`, kod 0 | `python3 run.py --build build --target tests` | `Bledy: 0` - OK |
| Odtworzenie w nowym katalogu | świeży klon repozytorium | budowa, przykład, narzędzie i testy zgodne z README; pliki `dane/` bajtowo zgodne | `git clone`, komendy z README | macOS: OK; Linux x86_64 (Ubuntu 24.04, libpng 1.6.43): nie sprawdzono |
