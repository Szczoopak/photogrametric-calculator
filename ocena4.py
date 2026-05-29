import argparse
import json
import numpy as np
import cv2
import csv

# =============================================================================
# 1. PARSER LINII KOMEND (Wymaganie instrukcji)
# =============================================================================
parser = argparse.ArgumentParser(description="Wcięcie w przód - Projekt 1 (Ocena 4)")
parser.add_argument('--ori1', required=True, help="Ścieżka do pliku JSON z orientacją 1. zdjęcia")
parser.add_argument('--ori2', required=True, help="Ścieżka do pliku JSON z orientacją 2. zdjęcia")
parser.add_argument('--uv', required=True, help="Ścieżka do pliku JSON ze współrzędnymi pikselowymi (np. tie_points.json)")
parser.add_argument('--out', required=True, help="Ścieżka do wynikowego pliku CSV")
args = parser.parse_args()

# =============================================================================
# 2. FUNKCJA BUDUJĄCA MACIERZ RZUTOWANIA P (P = K * [R | t])
# =============================================================================
def get_projection_matrix(path_json):
    """Zwraca macierz rzutowania P w globalnym układzie współrzędnych (float64)."""
    with open(path_json, 'r') as f:
        data = json.load(f)
    
    # 1. Macierz kalibracyjna K (Wewnętrzna)
    intr = data.get('intrinsic', data)
    f_pixels = intr['focal_in_pixels']
    cx = (intr['width'] / 2.0) + intr['principal_point_offset'][0]
    cy = (intr['height'] / 2.0) + intr['principal_point_offset'][1]
    
    K = np.array([
        [f_pixels, 0.0, cx],
        [0.0, f_pixels, cy],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    # 2. Orientacja zewnętrzna (Rotacja i Środek Rzutów)
    extr = data.get('extrinsic', data)
    R_c2w = np.array(extr['rotation_matrix'], dtype=np.float64).reshape(3, 3) # Camera to World
    C_w = np.array(extr['translation_vector'], dtype=np.float64).reshape(3, 1) # Camera Center (Global XYZ)

    # Aby zrzutować punkty na płaszczyznę, potrzebujemy macierzy z World to Camera
    R_w2c = R_c2w.T
    t_w2c = -R_w2c @ C_w

    # 3. Złożenie macierzy rzutowania P (Kształt: 3x4)
    Rt = np.hstack((R_w2c, t_w2c))
    P = K @ Rt
    
    return P

# Wyznaczenie absolutnych macierzy rzutowania w przestrzeni globalnej
P1 = get_projection_matrix(args.ori1)
P2 = get_projection_matrix(args.ori2)

# =============================================================================
# 3. WCZYTANIE PUNKTÓW Z PLIKU JSON
# =============================================================================
with open(args.uv, 'r') as f:
    data_uv = json.load(f)

pts1 = []
pts2 = []
pt_names = []

# Dynamiczne pobranie kluczy (nazw zdjęć) z pierwszego punktu w pliku
first_point_data = list(data_uv.values())[0]
image_keys = list(first_point_data.keys())

if len(image_keys) < 2:
    raise ValueError("Błąd: Plik JSON musi zawierać współrzędne dla dokładnie 2 zdjęć.")

key_img1, key_img2 = image_keys[0], image_keys[1]

# Ekstrakcja współrzędnych
for pt_id, coords in data_uv.items():
    if key_img1 in coords and key_img2 in coords:
        pts1.append(coords[key_img1])
        pts2.append(coords[key_img2])
        pt_names.append(pt_id)

pts1 = np.array(pts1, dtype=np.float64)
pts2 = np.array(pts2, dtype=np.float64)

print(f"Wczytano {len(pt_names)} par punktów pomierzonych na obu zdjęciach.")

# =============================================================================
# 4. WCIĘCIE W PRZÓD (Triangulacja)
# =============================================================================
# Funkcja triangulatePoints wymaga punktów w kształcie (2, N)
pts4D_hom = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)

# Konwersja ze współrzędnych jednorodnych (4D) na kartezjańskie (3D)
pts3D_global = pts4D_hom[:3, :] / pts4D_hom[3, :]
pts3D_global = pts3D_global.T # Zmiana kształtu z powrotem na (N, 3)

# =============================================================================
# 5. ZAPIS DO PLIKU CSV
# =============================================================================
with open(args.out, 'w', newline='') as csvfile:
    # W polskiej geodezji często używa się średnika jako separatora
    csvwriter = csv.writer(csvfile, delimiter=';')
    # Nagłówek ułatwi pracę w CloudCompare
    csvwriter.writerow(['Nazwa', 'X', 'Y', 'Z']) 
    
    for name, pt in zip(pt_names, pts3D_global):
        csvwriter.writerow([name, f"{pt[0]:.3f}", f"{pt[1]:.3f}", f"{pt[2]:.3f}"])

print(f"\n[SUKCES] Wyznaczono współrzędne globalne XYZ dla {len(pt_names)} punktów.")
print(f"Wyniki zostały zapisane w pliku: {args.out}")