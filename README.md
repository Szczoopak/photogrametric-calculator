# 📸 Podstawy Fotogrametrii – Projekt 1

Repozytorium zawiera zestaw skryptów w języku Python zrealizowanych w ramach uniwersyteckiego projektu z fotogrametrii. Celem projektu jest implementacja i automatyzacja podstawowych algorytmów fotogrametrycznych: **wyznaczania orientacji zewnętrznej (wcięcie wstecz)**, **wcięcia w przód (triangulacji)** oraz **orientacji wzajemnej stereogramu**.

---

## 📁 Struktura repozytorium

```text
├── data/
│   ├── data_aula/                  # Dane do orientacji wzajemnej (wnętrze Gmachu Głównego)
│   │   └── moje_punkty_aula.json   # Moje punkty do weryfikacji poprawności obliczeń w ocena5.py
│   └── data_dron/                  # Dane z pułapu lotniczego (zdjęcia, orientacja, GCP)
│       └── moje_punkty_dron.json   # Samodzielnie przygotowany plik ze współrzędnymi pikselowymi
├── results/                        # Folder na pliki wynikowe
│   ├── DSC08444.json               # Wynikowy plik orientacji zdjęcia 1 (wygenerowany przez ocena5.py)
│   ├── DSC08447.json               # Wynikowy plik orientacji zdjęcia 2 (wygenerowany przez ocena5.py)
│   ├── moje_punkty_ocena4.csv      # Obliczone współrzędne 3D dla danych z drona
│   └── moje_punkty_ocena5.csv      # Obliczone współrzędne 3D dla danych z auli
├── ocena3.py                       # Wcięcie wstecz (Orientacja zewnętrzna)
├── ocena4.py                       # Wcięcie w przód (Triangulacja przestrzenna)
├── ocena5.py                       # Orientacja wzajemna (Stereogram)
├── sprawdz_punkty.py               # Narzędzie pomocnicze do weryfikacji punktów
├── requirements.txt                # Lista wymaganych bibliotek
└── README.md                       # Dokumentacja projektu
```

## 📜 Opis skryptów

- **ocena3.py** – Wyznacza orientację zewnętrzną pojedynczego zdjęcia (wcięcie wstecz) przy użyciu `cv2.solvePnP`. Losowo dzieli punkty na osnowę i kontrolne oraz generuje wykres błędów reprojekcji.
- **ocena4.py** – Wyznacza współrzędne 3D $(X, Y, Z)$ za pomocą wcięcia w przód (triangulacji przestrzennej). Pobiera dane orientacji dwóch zdjęć i plik z pomierzonymi pikselami, po czym eksportuje wynik do pliku CSV.
- **ocena5.py** – Wyznacza orientację wzajemną pary zdjęć (stereogramu). Na podstawie dopasowanych punktów wiążących oblicza macierz istotną (Essential Matrix) i skaluje stereogram do rzeczywistych wymiarów, generując pliki orientacji aparatów.
- **sprawdz_punkty.py** – Narzędzie wizualne, które nakłada celowniki na zdjęcia w oparciu o plik JSON. Pozwala szybko zweryfikować, czy punkty na obu zdjęciach zostały pomierzone poprawnie i bez pomyłek.

## 🛠️ Instalacja i uruchomienie

### Wymagania systemowe

- Python 3.12 (zalecana wersja, na której testowano skrypty)

### Klonowanie repozytorium

```bash
git clone https://github.com/Szczoopak/photogrametric-calculator.git
cd photogrametric-calculator
```

### Instalacja zależności

```bash
pip install -r requirements.txt
```

## ⚙️ Słownik parametrów uruchamiania (CLI)

Każdy ze skryptów obsługuje zestaw parametrów przekazywanych z poziomu konsoli. Poniżej znajduje się zestawienie flag używanych w projekcie:

| Parametr      | Typ     | Opis                                                                                   |
|---------------|---------|----------------------------------------------------------------------------------------|
| `--image`     | Ścieżka | Plik obrazu wejściowego (np. .jpg), dla którego liczymy orientację.                    |
| `--gcp_xyz`   | Ścieżka | Plik tekstowy (.txt) zawierający współrzędne terenowe $(X, Y, Z)$ punktów osnowy (GCP). |
| `--gcp_uv`    | Ścieżka | Plik .json zawierający współrzędne pikselowe $(u, v)$ punktów osnowy na danym zdjęciu. |
| `--intrinsic` | Ścieżka | Plik .json z parametrami orientacji wewnętrznej / kalibracji kamery.                   |
| `--uv`        | Ścieżka | Plik .json ze współrzędnymi pikselowymi mierzonych punktów lub punktów wiążących.      |
| `--ori1` /<br>`--ori2` | Ścieżka | Pliki .json z danymi orientacji (zewnętrznej i wewnętrznej) odpowiednio dla pierwszego i drugiego zdjęcia. |
| `--out`       | Ścieżka | Lokalizacja docelowa oraz nazwa wyjściowego pliku .csv z wynikami obliczeń 3D.         |
| `--img1` /<br>`--img2` | Ścieżka | Ścieżki do pierwszego i drugiego zdjęcia używane przy wizualnej weryfikacji punktów.   |

💡 **Wskazówka:** Każdy ze skryptów posiada wbudowany system pomocy. Jeśli chcesz szybko sprawdzić wymagane parametry lub upewnić się, jakie flagi są dostępne, możesz uruchomić dowolny plik z flagą `-h` lub `--help`:
```bash
python ocena3.py --help
```

## 💻 Polecenia uruchomienia (dane testowe)

### 1. Orientacja zewnętrzna (ocena3.py)

```bash
python ocena3.py --image "data/data_dron/DJI_20250217091019_0200_V.jpg" --gcp_xyz "data/data_dron/gcp.txt" --gcp_uv "data/data_dron/DJI_20250217091019_0200_V_gcps.json" --intrinsic "data/data_dron/DJI_20250217091019_0200_V_orientation.json"
```

### 2. Orientacja wzajemna (ocena5.py)

Uruchomienie tego skryptu generuje w katalogu `results/` pliki orientacji `DSC08444.json` oraz `DSC08447.json`, niezbędne do kolejnego etapu.

```bash
python ocena5.py --intrinsic "data/data_aula/intrinsic_orientation.json" --uv "data/data_aula/tie_points.json"
```

### 3. Triangulacja przestrzenna (ocena4.py)

#### Dla danych z drona:

```bash
python ocena4.py --ori1 "data/data_dron/DJI_20250217091019_0200_V_orientation.json" --ori2 "data/data_dron/DJI_20250217091553_0592_V_orientation.json" --uv "data/data_dron/moje_punkty_dron.json" --out "results/moje_punkty_ocena4.csv"
```

#### Dla danych z auli (wykorzystuje pliki wygenerowane w kroku 2):

```bash
python ocena4.py --ori1 "results/DSC08444.json" --ori2 "results/DSC08447.json" --uv "data/data_aula/moje_punkty_aula.json" --out "results/moje_punkty_ocena5.csv"
```

### 4. Weryfikacja wizualna (sprawdz_punkty.py)

```bash
python sprawdz_punkty.py --img1 "data/data_aula/DSC08444.jpg" --img2 "data/data_aula/DSC08447.jpg" --uv "data/data_aula/moje_punkty_aula.json"
```

## ✔️ Weryfikacja

Poprawność algorytmów została potwierdzona w programie CloudCompare oraz poprzez metryczną kontrolę wymiarów obiektów (zegar) w auli Gmachu Głównego.
