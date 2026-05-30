import os
import argparse
import json
import numpy as np
import cv2

# Obsługa wejścia z linii komend
parser = argparse.ArgumentParser(description="Orientacja wzajemna pary zdjec")
parser.add_argument('--intrinsic', required=True, help="Sciezka do pliku JSON z orientacja wewnetrzna")
parser.add_argument('--uv', required=True, help="Sciezka do pliku JSON z punktami wiazacymi (tie_points)")
args = parser.parse_args()

# Odczyt danych wejściowych
with open(args.intrinsic, 'r') as f:
    data_ori = json.load(f)

intr = data_ori.get('intrinsic', data_ori)
f_pixels = intr['focal_in_pixels']
cx = (intr['width'] / 2.0) + intr['principal_point_offset'][0]
cy = (intr['height'] / 2.0) + intr['principal_point_offset'][1]

K = np.array([
    [f_pixels,       0.0,  cx],
    [0.0,       f_pixels,  cy],
    [0.0,            0.0, 1.0]
], dtype=np.float32)

with open(args.uv, 'r') as f:
    data_uv = json.load(f)

# Pobranie znanej odległości między punktami 0 i 1
target_distance = data_uv.get("DISTANCE_0_1", 1.0)

point_keys = [k for k in data_uv.keys() if isinstance(data_uv[k], dict)]
if len(point_keys) < 5:
    raise ValueError("Za mało punktów wiążących! Minimum to 5.")

first_pt = data_uv[point_keys[0]]
image_keys = list(first_pt.keys())
key_img1, key_img2 = image_keys[0], image_keys[1]

pts1 = []
pts2 = []

for k in point_keys:
    if key_img1 in data_uv[k] and key_img2 in data_uv[k]:
        pts1.append(data_uv[k][key_img1])
        pts2.append(data_uv[k][key_img2])

# Punkty pikselowe to małe liczby, od razu rzutowane na float32 dla OpenCV
pts1 = np.array(pts1, dtype=np.float32)
pts2 = np.array(pts2, dtype=np.float32)

# Macierz istotna E 
E, mask_E = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
if E is None or E.shape != (3, 3):
    raise Exception("Nie udało się wyznaczyć poprawnej macierzy istotnej E.")

# Rotacja i wektor kierunkowy translacji (Znormalizowany t)
points, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, K, mask=mask_E)

# Skalowanie (Na podstawie odległości 3D między pkt 0 a 1)
if "0" in data_uv and "1" in data_uv:
    # Pobieramy punkty bazowe z JSON
    pt0_1 = data_uv["0"][key_img1]
    pt0_2 = data_uv["0"][key_img2]
    pt1_1 = data_uv["1"][key_img1]
    pt1_2 = data_uv["1"][key_img2]

    # Przygotowanie do triangulacji
    pts1_scale = np.array([pt0_1, pt1_1], dtype=np.float32).T
    pts2_scale = np.array([pt0_2, pt1_2], dtype=np.float32).T

    # Wirtualne macierze projekcji dla bazy = 1 
    Rt1_32 = np.hstack((np.eye(3), np.zeros((3, 1)))).astype(np.float32)
    Rt2_32 = np.hstack((R, t)).astype(np.float32)
    
    P1_unscaled = K @ Rt1_32
    P2_unscaled = K @ Rt2_32

    # Wcięcie w przód dla punktów 0 i 1
    pts4D = cv2.triangulatePoints(P1_unscaled, P2_unscaled, pts1_scale, pts2_scale)
    
    # Przejście na float64 dla bezstratnego obliczenia odległości
    pts4D_64 = pts4D.astype(np.float64)
    pts3D = pts4D_64[:3, :] / pts4D_64[3, :]

    # Dystans Euklidesowy między wirtualnym punktem 0 i 1
    model_distance = np.linalg.norm(pts3D[:, 0] - pts3D[:, 1])

    # Wyliczenie współczynnika skali
    true_scale_factor = target_distance / model_distance
    print(f"Rzeczywista docelowa odleglosc 0-1: {target_distance:.3f} m")
    print(f"Wirtualna odleglosc 0-1 (bez skali): {model_distance:.3f} jedn.")
    print(f"Aplikowany mnoznik (Wspolczynnik Skali): {true_scale_factor:.3f}")

    # Skalowanie ostatecznego wektora przesunięcia drona
    t = t * true_scale_factor
else:
    print("Ostrzeżenie: Brak punktów '0' i '1' w pliku! Przyjęto brak skalowania bazy (Skala = 1.0).")

# Zapis do oddzielnych plików JSON dla obu zdjęć (żeby można było sprawdzić poprawność w programie ocena4.py)
ori_img1 = {
    "intrinsic": intr,
    "extrinsic": {
        "rotation_matrix": np.eye(3).tolist(),
        "translation_vector": [0.0, 0.0, 0.0]
    }
}

ori_img2 = {
    "intrinsic": intr,
    "extrinsic": {
        "rotation_matrix": R.tolist(),
        "translation_vector": t.flatten().tolist()
    }
}

# Definiowanie ścieżki do folderu wynikowego i upewnienie się, że on istnieje
output_dir = "results"
os.makedirs(output_dir, exist_ok=True)

# Zapis do oddzielnych plików JSON automatycznie w folderze results
nazwa_pliku1 = os.path.join(output_dir, f"{key_img1}.json")
nazwa_pliku2 = os.path.join(output_dir, f"{key_img2}.json")

with open(nazwa_pliku1, 'w', encoding='utf-8') as f1:
    json.dump(ori_img1, f1, indent=4)

with open(nazwa_pliku2, 'w', encoding='utf-8') as f2:
    json.dump(ori_img2, f2, indent=4)

print("\n[SUKCES] Zakończono generowanie orientacji!")
print(f"Utworzono pliki z orientacją w folderze '{output_dir}': '{key_img1}.json' oraz '{key_img2}.json'.")