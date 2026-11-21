# Autorstwo i źródła

## Wkład autorów

| Autor | Wykonane elementy | Lokalizacja w projekcie |
| --- | --- | --- |
| Marcin Kowalczyk (Pixel of Software) | wybór biblioteki, założenia, przegląd i akceptacja kodu, publikacja | całość |
| Asystent AI Claude (Anthropic) | wrapper, przykład, narzędzie do grafik, testy, generator plików testowych, skrypty budowania, dokumentacja | `app/`, `przyklady/`, `tests/`, `dane/`, `narzedzia/`, `build.py`, `run.py`, `README.md` |

## Wykorzystane materiały

| Materiał | Autor i źródło | Wersja lub data | Licencja | Sposób wykorzystania |
| --- | --- | --- | --- | --- |
| libpng | PNG Development Group, https://github.com/pnggroup/libpng | 1.6.50 (odniesienie z karty: 1.6.43) | PNG Reference Library License version 2 (https://github.com/pnggroup/libpng/blob/v1.6.43/LICENSE) | biblioteka łączona dynamicznie, nie jest dołączona; deklaracje funkcji, układ `struct png_image` i stałe przepisane ręcznie z `png.h` i sprawdzone programem w C |
| zlib | Jean-loup Gailly, Mark Adler | systemowa | licencja zlib | zależność wykonawcza libpng; generator `narzedzia/generuj_dane.py` używa modułu `zlib` z Pythona |
| Specyfikacja PNG | W3C, Portable Network Graphics (PNG) Specification | wyd. 3 | dokument W3C | budowa plików testowych (IHDR, PLTE, tRNS, IDAT, IEND, CRC, przeplot Adam7) |
| `build.py`, `run.py`, `LICENSE` | Fundacja Duckling, szablon projektu z materiałów na start DuckQuest | 2026 | MIT (plik `LICENSE`) | skrypty rozbudowane o dołączanie libpng, cel `przyklad` i kopiowanie `dane/`; licencja z dopisanym autorem |
| Duckling (kompilator i biblioteka standardowa) | ducktype-org/duckling | 0.3-alpha, commit 83882805a | licencja Ducklinga | zależność budowania |

Wszystkie pliki w `dane/` zostały wygenerowane dla tego projektu skryptem `narzedzia/generuj_dane.py`; grafiki (duszek, krajobraz) są własne.

## Narzędzia AI

Kod wrappera, przykładu, narzędzia do grafik i testów, generator plików testowych, zmiany skryptów budowania oraz dokumentację przygotowano z pomocą asystenta AI Claude (Anthropic). Autor ustalił zakres i wybór biblioteki, przejrzał wyniki, sprawdził działanie (budowa, 35 testów, przykład, narzędzie, `leaks`) i odpowiada za oddaną wersję.

## Licencja własnego projektu

MIT, treść w pliku `LICENSE` (szablon Fundacji Duckling z dopisaną linią `Copyright (c) 2026 Pixel of Software (Marcin Kowalczyk)`). Licencje libpng i zlib dotyczą samych bibliotek, instalowanych osobno.
