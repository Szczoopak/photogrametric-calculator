import argparse
import json
import numpy as np
import cv2
import csv

# Obsługa wejścia z linii komend
parser = argparse.ArgumentParser(description="Wcięcie w przód - Projekt 1 (Ocena 4)")
parser.add_argument('--ori1', required=True, help="Sciezka do pliku JSON z orientacja 1. zdjecia")
parser.add_argument('--ori2', required=True, help="Sciezka do pliku JSON z orientacja 2. zdjecia")
parser.add_argument('--uv', required=True, help="Sciezka do pliku JSON ze wspolrzednymi pikselowymi")
parser.add_argument('--out', required=True, help="Sciezka do wynikowego pliku CSV")
args = parser.parse_args()

# Odczyt parametrów wewnętrznych
with open(args.ori1, 'r') as f:
    data_ori1 = json.load(f)
with open(args.ori2, 'r') as f:
    data_ori2 = json.load(f)

# Zakładam, że macierz K jest identyczna dla obu zdjęć (korzystam z ori1)
intr = data_ori1.get('intrinsic', data_ori1)
f_pixels = intr['focal_in_pixels']
cx = (intr['width'] / 2.0) + intr['principal_point_offset'][0]
cy = (intr['height'] / 2.0) + intr['principal_point_offset'][1]

K = np.array([
    [f_pixels,       0.0,  cx],
    [0.0,       f_pixels,  cy],
    [0.0,            0.0, 1.0]
], dtype=np.float32)

# Przygotowanie danych z układem centrycznym
extr1 = data_ori1.get('extrinsic', data_ori1)
extr2 = data_ori2.get('extrinsic', data_ori2)

# Wczytanie globalnej pozycji kamer z pełną precyzją float64
R1_c2w = np.array(extr1['rotation_matrix'], dtype=np.float64).reshape(3, 3)
C1_w = np.array(extr1['translation_vector'], dtype=np.float64).reshape(3, 1)

R2_c2w = np.array(extr2['rotation_matrix'], dtype=np.float64).reshape(3, 3)
C2_w = np.array(extr2['translation_vector'], dtype=np.float64).reshape(3, 1)

# Wyznaczenie środka ciężkości układu
# Jako układ odniesienia wybieram punkt idealnie w połowie między kamerami
centroid_64 = (C1_w + C2_w) / 2.0

# Redukcja środków rzutów do środka ciężkości
C1_local_64 = C1_w - centroid_64
C2_local_64 = C2_w - centroid_64

# Obliczenie wektorów translacji w układzie lokalnym
R1_w2c = R1_c2w.T
t1_local_64 = -R1_w2c @ C1_local_64

R2_w2c = R2_c2w.T
t2_local_64 = -R2_w2c @ C2_local_64

# Rzutowanie małych wartości translacji na float32
Rt1_32 = np.hstack((R1_w2c, t1_local_64)).astype(np.float32)
Rt2_32 = np.hstack((R2_w2c, t2_local_64)).astype(np.float32)

# Ostateczne macierze rzutowania przekazywane do OpenCV
P1 = K @ Rt1_32
P2 = K @ Rt2_32

# Wczytywanie punktów 2D
with open(args.uv, 'r') as f:
    data_uv = json.load(f)

pts1 = []
pts2 = []
pt_names = []

# Pobranie nazw zdjęć z pierwszego punktu w pliku
first_point_data = list(data_uv.values())[0]
image_keys = list(first_point_data.keys())

if len(image_keys) < 2:
    raise ValueError("Błąd: Plik JSON musi zawierać współrzędne dla dokładnie 2 zdjęć.")

key_img1, key_img2 = image_keys[0], image_keys[1]

for pt_id, coords in data_uv.items():
    if key_img1 in coords and key_img2 in coords:
        pts1.append(coords[key_img1])
        pts2.append(coords[key_img2])
        pt_names.append(pt_id)

pts1 = np.array(pts1, dtype=np.float32)
pts2 = np.array(pts2, dtype=np.float32)

print(f"Wczytano {len(pt_names)} par punktów pomierzonych na obu zdjęciach.")

# Wcięcie w przód
pts4D_hom = cv2.triangulatePoints(P1, P2, pts1.T, pts2.T)

# Konwersja na współrzędne kartezjańskie (3D) w układzie lokalnym
pts3D_local = pts4D_hom[:3, :] / pts4D_hom[3, :]
pts3D_local = pts3D_local.T 

# Powrót do pełnej precyzji globalnej (float64) i dodanie centroidu
pts3D_global = pts3D_local.astype(np.float64) + centroid_64.T

# Zapis do pliku CSV
with open(args.out, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    csvwriter.writerow(['Nazwa', 'X', 'Y', 'Z']) 
    
    for name, pt in zip(pt_names, pts3D_global):
        csvwriter.writerow([name, f"{pt[0]:.3f}", f"{pt[1]:.3f}", f"{pt[2]:.3f}"])

print(f"\n[SUKCES] Wyznaczono współrzędne globalne XYZ dla {len(pt_names)} punktów.")
print(f"Wyniki zostały zapisane w pliku: {args.out}")