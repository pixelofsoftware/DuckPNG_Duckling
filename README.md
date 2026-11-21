# DuckPNG: wrapper libpng dla Ducklinga

Zespół: Pixel of Software (Marcin Kowalczyk). Temat: P02 DuckBridge, biblioteka libpng (poziom 3). Skład: 1 osoba.

Moduł `png` (`app/png.dk`) wczytuje i zapisuje obrazy PNG przez uproszczone API libpng (`png_image`). Każdy obsługiwany PNG trafia do jednego publicznego typu `Obraz` z buforem RGBA8. Dotyczy to szarości, palety, RGB, plików z alpha, 16-bitowych i z przeplotem. Zapis tworzy PNG 8-bitowy z kolorem i alpha.

Wrapper:
* sprawdza rozmiar i zakres liczb przed przydziałem pamięci i przed wywołaniem biblioteki;
* zwalnia zasoby libpng na każdej ścieżce, także przy błędzie;
* zwraca kopię komunikatu błędu biblioteki.

Całe minimum karty libpng działa i jest sprawdzone testami. Do tego są dwa przykłady: podstawowy i narzędzie do grafik gry jako praktyczne zastosowanie. Rozszerzenia:
* własny limit pamięci;
* informacja o formacie zapisanym w pliku;
* odczyt i zapis pojedynczych pikseli;
* generator plików testowych bez libpng (`narzedzia/generuj_dane.py`).

## Uruchomienie

Wymagane są:
* Python 3;
* Duckling (`duckc` w `PATH`, instalacja według tutoriala);
* libpng 1.6 z uproszczonym API (pakiety systemowe mają je włączone).

| System | Instalacja libpng |
| --- | --- |
| Ubuntu | `sudo apt install libpng16-16t64` |
| macOS | `brew install libpng` |

Z katalogu projektu:

```bash
python3 build.py --target all --output build      # aplikacja, przykład i testy; kopiuje dane/ do build/
python3 run.py --build build --target tests       # testy: PASS/FAIL, kod = liczba błędów
python3 run.py --build build --target przyklad    # przykład podstawowy
printf 'klucz FF00FF\ndane/duszek.png\nduszek-przezroczysty.png\n' | python3 run.py --build build --workdir .
```

Narzędzie do grafik czyta trzy wiersze ze standardowego wejścia:
1. polecenie;
2. plik wejściowy PNG;
3. plik wyjściowy (dla `info` pomijany).

| Polecenie | Działanie |
| --- | --- |
| `info` | wymiary, format pliku, liczba pikseli przezroczystych i półprzezroczystych, średni kolor |
| `klucz RRGGBB` | piksele w kolorze tła (np. `FF00FF`) dostają alpha 0, co jest typowe dla duszków gry |
| `szarosc` | odcienie szarości, alpha bez zmian |
| `pomniejsz` | zmniejszenie 2 razy; kolor jest średnią ważoną przezroczystością, więc tło nie przyciemnia krawędzi |

Po zapisie narzędzie wczytuje plik wynikowy i porównuje go bajt po bajcie z obrazem w pamięci. Kody zakończenia:

| Kod | Znaczenie |
| --- | --- |
| 0 | sukces |
| 2 | złe parametry |
| 3 | brak pliku |
| 4 | niepoprawny lub za duży PNG |
| 5 | błąd zapisu albo niezgodność |

`build.py` szuka biblioteki w tej kolejności:
1. ścieżka z opcji `--png /sciezka/libpng16.so.16`;
2. `pkg-config libpng16`;
3. typowe miejsca: `/usr/lib/x86_64-linux-gnu/libpng16.so.16` oraz `/opt/homebrew/lib/libpng16.dylib`;
4. `ctypes.util.find_library`.

`build.py` i `run.py` powstały z szablonu konkursu: doszła obsługa biblioteki, cel `przyklad` i kopiowanie `dane/` do katalogu budowy, a został tylko wariant natywny.

## Funkcje i demonstracja

| Funkcja z minimum karty | Sposób uruchomienia | Oczekiwany rezultat |
| --- | --- | --- |
| Wczytanie PNG do bufora RGBA8 i zapis z takiego bufora, z wymiarami | przykład | obraz 3x2 zapisany do `przyklad.png` i wczytany ponownie: `3x2, format pliku: kolor + alpha, bajty identyczne: true` |
| Publiczny typ obrazu z jednoznacznym układem | przykład, sekcja „Typ Obraz” | piksele wypisane jako `(R,G,B,A)` wierszami od góry |
| Sprawdzenie szer. × wys. × 4 względem zakresu liczb i limitu przed przydziałem | przykład; narzędzie: `info` na `dane/bomba.png` | `8192x8193: -3 (ponad limit 256 MiB)`, `600000000x10: -2 (poza zakresem liczb)`; plik z nagłówkiem 100000x100000: `ZA_DUZY: ... potrzebuje 40000000000 bajtow, limit to 268435456`, kod 4, bez przydziału 40 GB |
| Inicjalizacja `png_image`, zwolnienie przy błędzie, skopiowany komunikat | przykład, testy, `leaks` (macOS) | `NIEPOPRAWNY_PNG: dane/nie_png.png: Not a PNG file`; `leaks --atExit` na testach: 0 wycieków |
| Testy: kolory i alpha, ponowny odczyt, brakujący plik, niepoprawny PNG | `run.py --target tests` | 35 sprawdzeń, `Bledy: 0` |
| Praktyczne zastosowanie | narzędzie, `klucz FF00FF` na `dane/duszek.png` | `136 z 256 pikseli stalo sie przezroczystych`; `info` na wyniku: 120 nieprzezroczystych, 136 przezroczystych |

**Demonstracja:**
1. Uruchom przykład.
2. Uruchom narzędzie z `info` dla `dane/duszek.png`. To duszek RGB bez alpha na tle magenta.
3. Uruchom `klucz FF00FF`, a na wyniku ponownie `info`: tło jest przezroczyste.
4. Uruchom `pomniejsz` dla `dane/krajobraz.png`, który ma półprzezroczyste słońce. Wynik ma 32x20.
5. Spróbuj `info` dla `dane/bomba.png` (nagłówek 100000x100000) i `dane/nie_png.png`. Dostaniesz kontrolowany błąd, bez awarii.

## Typ `Obraz`

```
class Obraz {
    szerokosc: i64;
    wysokosc: i64;
    piksele: List[u8];   # RGBA8
}
```

| Cecha | Ustalenie |
| --- | --- |
| Układ pikseli | wierszami od lewego górnego rogu, bez odstępów: krok wiersza = `szerokosc * 4` bajty |
| Piksel (x, y) | zaczyna się na bajcie `(y * szerokosc + x) * 4` |
| Kanały | 4 bajty w kolejności R, G, B, A, po 8 bitów |
| Kolory | sRGB, tak jak są zapisane w typowym pliku PNG |
| Przezroczystość | A = 0 to obraz całkiem przezroczysty, A = 255 nieprzezroczysty; alpha **nie jest przemnożona** przez kolor, więc piksel `(200, 100, 50, 0)` zachowuje kolor przy zapisie i odczycie |
| Poprawność | `poprawny(o)`: wymiary dodatnie i `piksele.length() == szerokosc * wysokosc * 4` |

Konwersje przy wczytywaniu wykonuje libpng:
* szarość daje R = G = B;
* paleta daje kolory z PLTE i alpha z tRNS (bez tRNS alpha = 255);
* brak kanału alpha w pliku daje alpha = 255;
* przeplot Adam7 jest rozwijany;
* 16 bitów przechodzi na 8 bitów: plik 16-bitowy bez informacji o gammie jest traktowany jak sRGB (flaga `PNG_IMAGE_FLAG_16BIT_sRGB`), więc składowa v daje v·255/65535.

Bez tej flagi libpng uznałaby takie dane za liniowe i przeliczyłaby je na sRGB, co rozjaśnia średnie tony. Pole `Wynik.formatPliku` mówi, jaki był format w pliku, a `opisFormatu` zamienia je na tekst, np. „paleta + alpha”.

## API modułu `png`

| Funkcja | Zwraca | Błąd (`Wynik.rodzaj`) |
| --- | --- | --- |
| `wczytaj(sciezka) -> Wynik` | `obraz` RGBA8, `formatPliku` | `BRAK_PLIKU`, `NIEPOPRAWNY_PNG`, `ZA_DUZY` (ponad 256 MiB albo poza zakresem), `BRAK_PAMIECI` |
| `wczytajZLimitem(sciezka, limit) -> Wynik` | jak wyżej, z własnym limitem bajtów | dodatkowo `BLEDNE_PARAMETRY` dla ujemnego limitu |
| `zapisz(sciezka, o: ref Obraz) -> Wynik` | `ok` (plik zastąpiony, jeśli istniał) | `BLEDNE_PARAMETRY` (złe wymiary, bufor innej długości), `ZA_DUZY`, `BLAD_ZAPISU`, `BRAK_PAMIECI` |
| `sprawdzRozmiar(szer, wys, limit) -> i64` | liczba bajtów bufora | −1 złe wymiary, −2 poza zakresem liczb, −3 ponad limit |
| `nowyObraz(szer, wys, r, g, b, a) -> Wynik` | obraz wypełniony kolorem | `BLEDNE_PARAMETRY`, `ZA_DUZY` |
| `piksel(o, x, y) -> Kolor` | składowe `r, g, b, a` (0..255) | poza obrazem: `(0, 0, 0, 0)` |
| `ustawPiksel(o, x, y, r, g, b, a) -> bool` | `true` po zmianie | `false` poza obrazem lub dla składowej spoza 0..255 |
| `poprawny`, `opisFormatu`, `nazwaRodzaju`, `wersjaBiblioteki` | pomocnicze | - |

`Wynik` ma pola:
* `ok`, `rodzaj`;
* `obraz`;
* `blad` - ścieżka i kopia komunikatu libpng albo opis wrappera;
* `ostrzezenie` - ostrzeżenie libpng przy udanej operacji;
* `formatPliku`.

## Sprawdzenie rozmiaru przed przydziałem

Wywołanie `sprawdzRozmiar(szerokosc, wysokosc, limit)` sprawdza kolejno:
1. Obie liczby muszą być dodatnie.
2. `szerokosc ≤ 2147483647 / 4`, czyli krok wiersza mieści się w `png_int_32`. Ten typ ma argument `row_stride` funkcji `png_image_finish_read` i `png_image_write_to_file`.
3. `wysokosc ≤ (2^63 − 1) / krok`, czyli iloczyn nie przekroczy `i64`. Ten warunek jest sprawdzany dzieleniem, **przed** mnożeniem.
4. `wysokosc ≤ 2147483647`, czyli największa wysokość w PNG.
5. `szerokosc · wysokosc · 4 ≤ limit`. Domyślny limit to 256 MiB, np. obraz 8192 x 8192.

Przy wczytywaniu kroki idą tak:
1. `png_image_begin_read_from_file` czyta tylko nagłówek.
2. Wrapper sprawdza rozmiar.
3. Dopiero po tym wrapper przydziela bufor i wywołuje `png_image_finish_read`.

Dzięki temu poprawny nagłówek 100000 x 100000 (`dane/bomba.png`, 68 bajtów) kończy się błędem `ZA_DUZY` bez próby przydzielenia 40 GB. Przy zapisie wrapper sprawdza zakres oraz to, że długość `piksele` równa się dokładnie `szerokosc · wysokosc · 4`, zanim wywoła bibliotekę.

## Pamięć i `png_image`

Struktura `png_image` jest przydzielana przez `malloc`, zerowana, a pole `version` dostaje wartość `PNG_IMAGE_VERSION` (1), tak jak wymaga `png.h`. Wrapper ustawia `width`, `height`, `format` i `flags` oraz czyta `warning_or_error` i `message`.

Na każdej ścieżce wrapper wywołuje `png_image_free`, a potem `free` dla struktury:
* po sukcesie;
* po błędzie biblioteki;
* gdy sam odrzuca obraz po przeczytaniu nagłówka.

Wywołanie `png_image_free` jest bezpieczne także wtedy, gdy libpng już zwolniła swoje zasoby. Ma znaczenie zwłaszcza w przypadku odrzucenia po nagłówku, bo wtedy libpng trzyma otwarty plik i bufory.

Komunikat z pola `message` (do 64 znaków) jest kopiowany do `String` przed zwolnieniem struktury. Bufor pikseli dla biblioteki jest kopiowany do `List[u8]` i zwalniany, więc użytkownik nigdy nie dostaje wskaźnika do pamięci C.

Sprawdzenie na macOS: `leaks --atExit` na programie testów, który wykonuje między innymi 500 cykli odczytu, trzech rodzajów błędów i zapisu, zgłasza 0 wycieków. Kontrola ujemna: wersja z celowo usuniętym `png_image_free` w ścieżce odrzucenia nagłówka daje 1506 wycieków, więc to sprawdzenie naprawdę wykrywa brak zwolnienia.

## Środowisko i zależności

| Element | Wartość |
| --- | --- |
| Kompilator | `duckc 0.3-alpha (83882805a 2026-11-20)`, `commit-hash: 83882805a` |
| Uruchomienie | natywnie |
| System operacyjny | macOS 27.2, Apple Silicon (arm64) |
| Zależności | libpng 1.6.50 (Homebrew, `/opt/homebrew/lib/libpng16.dylib`, wraz z zlib), Python 3 |

Wersja odniesienia z karty to libpng 1.6.43. Układ `struct png_image` i stałe uproszczonego API są w całej serii 1.6 takie same. Ręczne przesunięcia pól sprawdziłem programem w C (`sizeof` = 104, `offsetof` każdego pola) z nagłówkami `png.h`, `pngconf.h` i `pnglibconf.h` z 1.6.50. Na Linuksie x86_64 (ABI LP64, ten sam układ) projektu nie sprawdzałem.

## Struktura i działanie

| Plik | Odpowiedzialność |
| --- | --- |
| `app/png.dk` | wrapper: deklaracje C, układ `png_image`, typ `Obraz`, sprawdzenie rozmiaru, odczyt, zapis, piksele |
| `app/app.dk` | praktyczne zastosowanie: narzędzie do grafik gry (`info`, `klucz`, `szarosc`, `pomniejsz`) |
| `przyklady/podstawowy.dk` | przykład podstawowy |
| `tests/testy.dk` | testy rozmiaru, obiegu zapis-odczyt, konwersji, błędów i zwalniania |
| `dane/` | pliki testowe i przykładowe grafiki (paleta, szarość z alpha, 16 bitów, przeplot, duszek, krajobraz, uszkodzone, bomba wymiarów) |
| `narzedzia/generuj_dane.py` | generator plików `dane/` w czystym Pythonie (struct + zlib), z opisem oczekiwanych pikseli |

**Deklaracje C** są ręczne, według `png.h`. Użyte funkcje:
* `png_image_begin_read_from_file`, `png_image_finish_read`, `png_image_write_to_file`, `png_image_free`;
* `png_access_version_number` - wersja biblioteki.

Strukturę przekazujemy jako `cptr u8` do bloku 104 bajtów, a pola czytamy pod przesunięciami z `png.h`, opisanymi w komentarzu w `app/png.dk`. Argumenty-wskaźniki, w które podajemy NULL (tło i paleta), są zadeklarowane jako `u64` z wartością 0. W ABI LP64 przekazuje się je tak samo, dlatego adapter C nie jest potrzebny. Wariant DVM nie jest obsługiwany.

**Ograniczenia:**
* brak odczytu i zapisu w pamięci (`png_image_*_memory`);
* brak zapisu palety i 16 bitów;
* brak klasycznego API z `setjmp`;
* metadane (gAMA, tEXt) nie są zwracane;
* limit 256 MiB dotyczy domyślnej funkcji `wczytaj`.

## Sprawdzenie projektu

```bash
python3 run.py --build build --target tests      # 35 sprawdzeń
python3 run.py --build build --target przyklad   # kod 0 = wszystkie oczekiwania przykładu spełnione
```

Testy sprawdzają:
* `sprawdzRozmiar`: krok wiersza, przepełnienie iloczynu, wysokość, limit;
* `nowyObraz` z błędnymi argumentami;
* zapis i ponowny odczyt z porównaniem wszystkich bajtów: kolory, alpha 0, 1, 128, 254 i 255 z zachowanym kolorem, obraz 37x23 z losowymi kanałami, obraz 1x1, zastąpienie pliku;
* konwersje do RGBA8: paleta z tRNS, szarość z alpha, RGB 16-bitowe, przeplot Adam7, RGB bez alpha;
* brakujący plik, plik tekstowy, zepsute dane IDAT, zła suma CRC i ucięty plik - wszystkie z kopią komunikatu libpng;
* nagłówek 100000x100000 i własny limit;
* zapis z błędnym buforem, obrazu 0x0 i do nieistniejącego katalogu;
* 500 cykli udanych i nieudanych operacji.

Scenariusze są w [tests/scenariusze.md](tests/scenariusze.md).

## Autorstwo i materiały

Kod i dokumentacja: Pixel of Software (Marcin Kowalczyk), z pomocą asystenta AI. Szczegóły są w [ZRODLA.md](ZRODLA.md).

Licencja własnego kodu: MIT (plik `LICENSE`). Biblioteka libpng ma licencję PNG Reference Library License version 2, a zlib - licencję zlib. Żadna z nich nie jest dołączona do repozytorium; wrapper łączy się z libpng dynamicznie.
