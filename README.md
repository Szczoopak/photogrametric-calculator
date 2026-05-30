# Podstawy Fotogrametrii – Projekt 1

Repozytorium zawiera zestaw skryptów w języku Python zrealizowanych w ramach uniwersyteckiego projektu z fotogrametrii. Celem projektu jest implementacja i automatyzacja podstawowych algorytmów fotogrametrycznych: wyznaczania orientacji zewnętrznej (wcięcie wstecz), wcięcia w przód (triangulacji) oraz orientacji wzajemnej stereogramu.

## 📁 Struktura repozytorium

```text
├── data/
│   ├── data_aula/                  # Dane do orientacji wzajemnej (wnętrze Gmachu Głównego)
│   │   └── moje_punkty_aula.json   # Moje punkty, na których sprawdziłem czy obliczenia z ocena5.py są poprawne
│   └── data_dron/                  # Dane z pułapu lotniczego (zdjęcia, orientacja, GCP)
│       └── moje_punkty_dron.json   # Samodzielnie przygotowany plik ze współrzędnymi pikselowymi
├── results/                        # Folder na pliki wynikowe
├── ocena3.py                       # Wcięcie wstecz (Orientacja zewnętrzna)
├── ocena4.py                       # Wcięcie w przód (Triangulacja przestrzenna)
├── ocena5.py                       # Orientacja wzajemna (Stereogram)
├── sprawdz_punkty.py               # Narzędzie pomocnicze do weryfikacji punktów
├── requirements.txt                # Lista wymaganych bibliotek
└── README.md                       # Dokumentacja projektu
```

## 📜 Opis skryptów

- **ocena3.py** – Wyznacza orientację zewnętrzną pojedynczego zdjęcia (wcięcie wstecz) przy użyciu `cv2.solvePnP`. Losowo dzieli punkty na osnowę i kontrolne oraz generuje wykres błędów reprojekcji.
- **ocena4.py** – Wyznacza współrzędne 3D (X, Y, Z) za pomocą wcięcia w przód (triangulacji). Pobiera dane orientacji dwóch zdjęć i plik z pomierzonymi pikselami, eksportując wynik do CSV.
- **ocena5.py** – Wyznacza orientację wzajemną pary zdjęć. Na podstawie dopasowanych punktów wiążących oblicza macierz istotną i skaluje stereogram do rzeczywistych wymiarów.
- **sprawdz_punkty.py** – Narzędzie wizualne, które nakłada celowniki na zdjęcia w oparciu o plik JSON. Pozwala szybko zweryfikować, czy punkty na obu zdjęciach zostały pomierzone poprawnie.

## 🛠️ Instalacja i uruchomienie

### Klonowanie repozytorium

```bash
git clone https://github.com/Szczoopak/photogrametric-calculator.git
cd photogrametric-calculator
```

### Instalacja zależności

```bash
pip install -r requirements.txt
```

## 💻 Polecenia uruchomienia (dane testowe)

### 1. Orientacja zewnętrzna (Ocena 3)

```bash
python ocena3.py \
  --image "data/data_dron/DJI_20250217091019_0200_V.jpg" \
  --gcp_xyz "data/data_dron/gcp.txt" \
  --gcp_uv "data/data_dron/DJI_20250217091019_0200_V_gcps.json" \
  --intrinsic "data/data_dron/DJI_20250217091019_0200_V_orientation.json"
```

### 2. Orientacja wzajemna (Ocena 5)

```bash
python ocena5.py \
  --intrinsic "data/data_aula/intrinsic_orientation.json" \
  --uv "data/data_aula/tie_points.json"
```

### 3. Triangulacja przestrzenna (Ocena 4)

#### Dla danych z drona

```bash
python ocena4.py \
  --ori1 "data/data_dron/DJI_20250217091019_0200_V_orientation.json" \
  --ori2 "data/data_dron/DJI_20250217091553_0592_V_orientation.json" \
  --uv "data/data_dron/moje_punkty_dron.json" \
  --out "results/moje_punkty_ocena4.csv"
```

#### Dla danych z auli

```bash
python ocena4.py \
  --ori1 "results/DSC08444.json" \
  --ori2 "results/DSC08447.json" \
  --uv "data/data_aula/moje_punkty_aula.json" \
  --out "results/moje_punkty_ocena5.csv"
```

### 4. Weryfikacja wizualna

```bash
python sprawdz_punkty.py \
  --img1 "data/data_aula/DSC08444.jpg" \
  --img2 "data/data_aula/DSC08447.jpg" \
  --uv "data/data_aula/moje_punkty_aula.json"
```

## ✔️ Weryfikacja

Poprawność algorytmów została potwierdzona w programie CloudCompare oraz poprzez metryczną kontrolę wymiarów obiektów (zegar) w auli Gmachu Głównego.