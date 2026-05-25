import os
import json
import numpy as np
import cv2

# Ścieżki do plików
path_orientacja = r"C:\Programy\Sem_4\Podstawy_fotogrametrii\Projekt1\data\DJI_20250217091553_0592_V_orientation.json"
path_gcp = r"C:\Programy\Sem_4\Podstawy_fotogrametrii\Projekt1\data\DJI_20250217091553_0592_V_gcps.json"
path_gcp_txt = r"C:\Programy\Sem_4\Podstawy_fotogrametrii\Projekt1\data\gcp.txt"

# 1. Wczytanie parametrów wewnętrznych kamery K
with open(path_orientacja, 'r') as f:
    data_ori = json.load(f)

f_pixels = data_ori['intrinsic']['focal_in_pixels']
w = data_ori['intrinsic']['width']
h = data_ori['intrinsic']['height']
offset_x = data_ori['intrinsic']['principal_point_offset'][0]
offset_y = data_ori['intrinsic']['principal_point_offset'][1]

cx = (w / 2.0) + offset_x
cy = (h / 2.0) + offset_y
fx = fy = f_pixels

K = np.array([
    [fx,   0.0,   cx],
    [0.0,   fy,   cy],
    [0.0,  0.0,  1.0]
], dtype=np.float32)

# 2. Wczytanie punktów foto (2D) i osnowy (3D)
with open(path_gcp, 'r') as f:
    data_gcp = json.load(f)

punkty2D = np.array(list(data_gcp.values()), dtype=np.float32)
dist_coeffs = np.zeros((4, 1))

coords_3D_dict = {}
with open(path_gcp_txt, 'r') as f_txt:
    for line in f_txt:
        if line.strip():
            p = line.strip().split(';')
            # Geodezyjne X, Y -> OpenCV X, Y (Wschód, Północ, Wysokość)
            coords_3D_dict[p[0]] = [float(p[1]), float(p[2]), float(p[3])]

punkty3D_raw = np.array([coords_3D_dict[name] for name in data_gcp.keys()], dtype=np.float64)

# 3. Redukcja współrzędnych do lokalnego układu
gcp_origin = punkty3D_raw[0].copy() 
punkty3D_local = (punkty3D_raw - gcp_origin).astype(np.float32)

# 4. Obliczenie orientacji zewnętrznej (PnP)
success, rvec, tvec = cv2.solvePnP(punkty3D_local, punkty2D, K, dist_coeffs) 
if not success: 
    raise Exception("PnP nie powiodło się") 

# 5. Reprojekcja wyliczonych punktów 3D na płaszczyznę obrazu 2D
punkty2D_proj, _ = cv2.projectPoints(punkty3D_local, rvec, tvec, K, dist_coeffs)

points_proj = punkty2D_proj.reshape(-1, 2)  # Wyliczone przez PnP
points_orig = punkty2D.reshape(-1, 2)      # Oryginalne z JSONa

# 6. Wczytanie obrazu i rysowanie punktów
img = cv2.imread(r"C:\Programy\Sem_4\Podstawy_fotogrametrii\Projekt1\data\DJI_20250217091553_0592_V.jpg")

# Rysujemy dwa rodzaje punktów, żeby sprawdzić dokładność wpasowania:
# ZIELONE kółka = Twoje punkty z JSONa
# CZERWONE kropki = Punkty matematycznie wyliczone z orientacji zdjęcia
for pt_orig, pt_proj in zip(points_orig, points_proj):
    # Punkty z JSONa (Zielone, większe kółka)
    cv2.circle(img, (int(pt_orig[0]), int(pt_orig[1])), radius=30, color=(0, 255, 0), thickness=4)
    # Punkty z modelu (Czerwone, mniejsze kropki w środku)
    cv2.circle(img, (int(pt_proj[0]), int(pt_proj[1])), radius=15, color=(0, 0, 255), thickness=-1)

# 7. SKALOWANIE OBRAZU DO WYŚWIETLENIA
Wyznaczona_szerokosc = 1000
skala = Wyznaczona_szerokosc / img.shape[1]
Wyznaczona_wysokosc = int(img.shape[0] * skala)

img_maly = cv2.resize(img, (Wyznaczona_szerokosc, Wyznaczona_wysokosc))

# Wyświetlenie dopasowanego okna
cv2.imshow("Porownanie: Zielone (JSON) vs Czerwone (PnP)", img_maly)
cv2.waitKey(0)
cv2.destroyAllWindows()

