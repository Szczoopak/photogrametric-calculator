import os
import json
import numpy as np
import cv2

# =============================================================================
# 1. ŚCIEŻKI DO PLIKÓW (Uzupełnij własnymi ścieżkami)
# =============================================================================
path_img1 = r"C:\VSC\Fotka\photogrametric-calculator\data\DJI_20250217091019_0200_V.jpg"
path_img2 = r"C:\VSC\Fotka\photogrametric-calculator\data\DJI_20250217091553_0592_V.jpg" # Przykładowe drugie zdjęcie

path_ori1 = r"C:\VSC\Fotka\photogrametric-calculator\data\DJI_20250217091019_0200_V_orientation.json"
path_ori2 = r"C:\VSC\Fotka\photogrametric-calculator\data\DJI_20250217091553_0592_V_orientation.json" # Dane kamery dla 2. zdjęcia

path_gcp1 = r"C:\VSC\Fotka\photogrametric-calculator\data\DJI_20250217091019_0200_V_gcps.json"
path_gcp2 = r"C:\VSC\Fotka\photogrametric-calculator\data\DJI_20250217091553_0592_V_gcps.json" # Punkty na 2. zdjęciu

# =============================================================================
# 2. FUNKCJA POMOCNICZA: BUDOWANIE MACIERZY K
# =============================================================================
def load_intrinsic_matrix(path_json):
    with open(path_json, 'r') as f:
        data = json.load(f)
    f_pixels = data['intrinsic']['focal_in_pixels']
    w = data['intrinsic']['width']
    h = data['intrinsic']['height']
    offset_x = data['intrinsic']['principal_point_offset'][0]
    offset_y = data['intrinsic']['principal_point_offset'][1]

    cx = (w / 2.0) + offset_x
    cy = (h / 2.0) + offset_y
    fx = fy = f_pixels

    K = np.array([
        [fx,   0.0,   cx],
        [0.0,   fy,   cy],
        [0.0,  0.0,  1.0]
    ], dtype=np.float32)
    return K

# Wczytanie macierzy dla obu stanowisk [cite: 75, 76]
K1 = load_intrinsic_matrix(path_ori1)
K2 = load_intrinsic_matrix(path_ori2)
dist_coeffs = np.zeros((4, 1)) # Zakładamy brak dystorsji (lub małe wartości) [cite: 35, 77]

# =============================================================================
# 3. WCZYTANIE I PAROWANIE PUNKTÓW WIĄŻĄCYCH (2D)
# =============================================================================
with open(path_gcp1, 'r') as f:
    data_gcp1 = json.load(f)
with open(path_gcp2, 'r') as f:
    data_gcp2 = json.load(f)

# Szukamy punktów o takich samych nazwach w obu plikach [cite: 74]
common_keys = [key for key in data_gcp1.keys() if key in data_gcp2]

if len(common_keys) < 5:
    raise Exception(f"Za mało punktów wspólnych! Znaleziono tylko {len(common_keys)}, a do macierzy istotnej wymagane jest min. 5.")

pts1 = np.array([data_gcp1[k] for k in common_keys], dtype=np.float32)
pts2 = np.array([data_gcp2[k] for k in common_keys], dtype=np.float32)

print(f"Pomyślnie sparowano {len(common_keys)} punktów wiążących między zdjęciami.")

# =============================================================================
# 4. WYZNACZANIE GEOMETRII EPIPOLARNEJ (Macierz Istotna E -> R, t)
# =============================================================================
# Wyznaczamy macierz istotną E przy użyciu algorytmu RANSAC [cite: 102]
# Ponieważ zdjęcia robiono tą samą kamerą, używamy K1 jako reprezentatywnej [cite: 103]
E, mask_E = cv2.findEssentialMat(pts1, pts2, cameraMatrix=K1, method=cv2.RANSAC, prob=0.999, threshold=1.0)

# Dekompozycja macierzy E do wzajemnej rotacji R i translacji t [cite: 105, 107]
# Założenie: Lewa kamera (zdjęcie 1) jest w początku układu (0,0,0) i nie jest obrócona[cite: 106].
success, R, t, mask_pose = cv2.recoverPose(E, pts1, pts2, cameraMatrix=K1)

if not success:
    raise Exception("Nie udało się odzyskać orientacji wzajemnej (recoverPose).")

print("\nWzajemna macierz rotacji R (Kamera 2 względem Kamery 1):\n", R)
print("\nWzajemny wektor translacji t (baza stereo - znormalizowana):\n", t)

# =============================================================================
# 5. REKONSTRUKCJA 3D PUNKTÓW (Triangulacja)
# =============================================================================
# Budowa macierzy projekcji P dla obu kamer [cite: 114, 115, 116]
P1 = K1 @ np.hstack((np.eye(3), np.zeros((3, 1))))
P2 = K2 @ np.hstack((R, t))

# Filtrujemy punkty - wybieramy tylko te, które przeszły test geometryczny RANSAC [cite: 117]
valid_idx = (mask_pose.ravel() == 255)
pts1_inliers = pts1[valid_idx]
pts2_inliers = pts2[valid_idx]
names_inliers = [common_keys[i] for i in range(len(common_keys)) if valid_idx[i]]

# Triangulacja punktów w przestrzeni (wynik w postaci współrzędnych jednorodnych) [cite: 118]
pts4D_hom = cv2.triangulatePoints(P1, P2, pts1_inliers.T, pts2_inliers.T)

# Konwersja ze współrzędnych jednorodnych do kartezjańskich (X, Y, Z) [cite: 119, 120]
pts3D_local = pts4D_hom[:3, :] / pts4D_hom[3, :]
pts3D_local = pts3D_local.T # Wynikowy kształt: (N, 3) [cite: 121]

print("\nWyznaczone LOKALNE współrzędne modelowe 3D (w układzie 1. kamery):")
for name, coords in zip(names_inliers, pts3D_local):
    print(f" Punkt {name}: X={coords[0]:.3f}, Y={coords[1]:.3f}, Z={coords[2]:.3f}")

# =============================================================================
# 6. WIZUALIZACJA I SKALOWANIE OKIEN
# =============================================================================
img1 = cv2.imread(path_img1)
img2 = cv2.imread(path_img2)

# Rysowanie punktów inlier na obu obrazach (Duże kółka, żeby były widoczne po zmniejszeniu)
for pt1, pt2 in zip(pts1_inliers, pts2_inliers):
    cv2.circle(img1, (int(pt1[0]), int(pt1[1])), radius=25, color=(0, 255, 0), thickness=-1)
    cv2.circle(img2, (int(pt2[0]), int(pt2[1])), radius=25, color=(0, 255, 255), thickness=-1)

# Funkcja skalująca okno do wyświetlania na ekranie komputera
def resize_to_screen(image, target_width=900):
    scale = target_width / image.shape[1]
    target_height = int(image.shape[0] * scale)
    return cv2.resize(image, (target_width, target_height))

img1_small = resize_to_screen(img1, target_width=800)
img2_small = resize_to_screen(img2, target_width=800)

# Wyświetlenie obrazów w osobnych, dopasowanych oknach
cv2.imshow("Zdjecie 1 - Punkty wiazace (Zielone)", img1_small)
cv2.imshow("Zdjecie 2 - Punkty wiazace (Zolte)", img2_small)

print("\n[INFO] Naciśnij dowolny klawisz w oknie obrazu, aby zamknąć program.")
cv2.waitKey(0)
cv2.destroyAllWindows()