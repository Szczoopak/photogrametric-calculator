import os
import json
import random
import argparse
import numpy as np
import cv2
import matplotlib.pyplot as plt

# --- 1. OBSŁUGA WEJŚCIA ---
parser = argparse.ArgumentParser(description="Orientacja zewnetrzna pojedynczego zdjecia - Projekt 1")
parser.add_argument('--image', required=True, help="Sciezka do pliku ze zdjeciem (.jpg)")
parser.add_argument('--gcp_xyz', required=True, help="Sciezka do pliku CSV/TXT ze wspolrzednymi XYZ")
parser.add_argument('--gcp_uv', required=True, help="Sciezka do pliku JSON ze wspolrzednymi UV (pikselowymi)")
parser.add_argument('--intrinsic', required=True, help="Sciezka do pliku JSON z orientacja wewnetrzna")
args = parser.parse_args()

with open(args.intrinsic, 'r') as f:
    data_ori = json.load(f)

intrinsic_data = data_ori.get('intrinsic', data_ori)
f_pixels = intrinsic_data['focal_in_pixels']
w = intrinsic_data['width']
h = intrinsic_data['height']
offset_x = intrinsic_data['principal_point_offset'][0]
offset_y = intrinsic_data['principal_point_offset'][1]

cx = (w / 2.0) + offset_x
cy = (h / 2.0) + offset_y

# Macierz kamery w float32 - zgodnie ze standardem wizyjnym
K = np.array([
    [f_pixels,       0.0,  cx],
    [0.0,       f_pixels,  cy],
    [0.0,            0.0, 1.0]
], dtype=np.float32)

dist_coeffs = np.zeros((4, 1), dtype=np.float32)

# Odczyt punktów pikselowych 2D
with open(args.gcp_uv, 'r') as f:
    data_gcp = json.load(f)

# Odczyt punktów osnowy 3D z pliku geodezyjnego (Odczyt klasyczny X, Y, Z)
coords_3D_dict = {}
with open(args.gcp_xyz, 'r') as f_txt:
    for line in f_txt:
        if line.strip():
            p = line.strip().split(';')
            coords_3D_dict[p[0]] = [float(p[1]), float(p[2]), float(p[3])]

all_keys = list(data_gcp.keys())
if len(all_keys) < 4:
    raise Exception("Za mało punktów w plikach, aby wydzielić 3 punkty kontrolne (check) i punkty osnowy!")

# --- 2. LOSOWANIE PUNKTÓW ---
check_keys = random.sample(all_keys, 3)
control_keys = [k for k in all_keys if k not in check_keys]

print(f"Punkty CONTROL (osnowa): {control_keys}")
print(f"Punkty CHECK (kontrolne): {check_keys}\n")

# --- 3. PRZYGOTOWANIE DANYCH (MĄDRA REDUKCJA DO FLOAT32) ---
# KROK A: Wczytujemy z pliku wielkie liczby globalne jako float64, żeby nie stracić precyzji!
punkty3D_raw_control_64 = np.array([coords_3D_dict[k] for k in control_keys], dtype=np.float64)

# KROK B: Wyznaczamy środek ciężkości w pełnej precyzji float64
centroid_64 = np.mean(punkty3D_raw_control_64, axis=0)

# KROK C: Redukujemy punkty osnowy do środka ciężkości. 
# Wynikiem są małe odległości (np. 15.3m, -5.2m), więc nie ma już ryzyka utraty ułamków!
punkty3D_centric_control_64 = punkty3D_raw_control_64 - centroid_64

# KROK D: Teraz bezpiecznie rzutujemy te małe liczby na float32 dla funkcji OpenCV
punkty3D_centric_control = punkty3D_centric_control_64.astype(np.float32)

# Punkty 2D to małe liczby (piksele), więc od razu mogą być w float32
punkty2D_control = np.array([data_gcp[k] for k in control_keys], dtype=np.float32)


# --- 4. OBLICZENIE PnP ---
success, rvec, tvec = cv2.solvePnP(
    punkty3D_centric_control, 
    punkty2D_control, 
    K, 
    dist_coeffs,
    flags=cv2.SOLVEPNP_SQPNP
)
if not success:
    raise Exception("PnP nie powiodło się dla punktów CONTROL")

# Wyliczenie globalnej pozycji drona na podstawie układu centrycznego (dodajemy pełen centroid_64)
R, _ = cv2.Rodrigues(rvec)
C = -R.T @ tvec + centroid_64.reshape(3, 1)
print("=> Wyliczona pozycja drona (Optical Center) w globalnym XYZ:")
print(f"   X: {C[0,0]:.3f}, Y: {C[1,0]:.3f}, Z: {C[2,0]:.3f}\n")


# --- 5. OBLICZANIE STATYSTYK BŁĘDU REPROJEKCJI ---
def calculate_reprojection_errors(keys, is_control=True):
    # Znów wczytujemy wielkie liczby w float64
    pts3D_raw_64 = np.array([coords_3D_dict[k] for k in keys], dtype=np.float64)
    pts2D_orig = np.array([data_gcp[k] for k in keys], dtype=np.float32)
    
    # Redukujemy do układu centrycznego w float64
    pts3D_centric_64 = pts3D_raw_64 - centroid_64
    
    # Rzutujemy na float32 i wrzucamy do OpenCV
    pts3D_centric = pts3D_centric_64.astype(np.float32)
    
    pts2D_proj, _ = cv2.projectPoints(pts3D_centric, rvec, tvec, K, dist_coeffs)
    pts2D_proj = pts2D_proj.reshape(-1, 2)
    
    # Różnice współrzędnych (wektory błędu)
    dx = pts2D_proj[:, 0] - pts2D_orig[:, 0]
    dy = pts2D_proj[:, 1] - pts2D_orig[:, 1]
    errors = np.sqrt(dx**2 + dy**2)
    
    # Statystyki
    min_err = np.min(errors)
    max_err = np.max(errors)
    rms_err = np.sqrt(np.mean(errors**2))
    
    label = "CONTROL" if is_control else "CHECK"
    print(f"Statystyki bledow reprojekcji dla punktow {label}:")
    print(f"  - Min: {min_err:.2f} px")
    print(f"  - Max: {max_err:.2f} px")
    print(f"  - RMS: {rms_err:.2f} px\n")
    
    return pts2D_orig, dx, dy, errors

# Wyznaczenie błędów dla obu niezależnych grup
orig_cntrl, dx_cntrl, dy_cntrl, err_cntrl = calculate_reprojection_errors(control_keys, is_control=True)
orig_check, dx_check, dy_check, err_check = calculate_reprojection_errors(check_keys, is_control=False)

# --- 6. WIZUALIZACJA ---
img = cv2.imread(args.image)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

fig, ax = plt.subplots(figsize=(12, 8))
ax.imshow(img_rgb) # Wyświetlenie rastra w tle

VECTOR_SCALE = 100000 # Współczynnik powiększenia strzałek na wykresie

# Rysowanie wektorów dla punktów CONTROL (Kolor niebieski)
ax.quiver(orig_cntrl[:, 0], orig_cntrl[:, 1], dx_cntrl, dy_cntrl, 
          angles='xy', scale_units='xy', scale=1/VECTOR_SCALE, color='blue', 
          label='Punkty CONTROL (Osnowa)', width=0.004)

for i, k in enumerate(control_keys):
    ax.text(orig_cntrl[i, 0] + 40, orig_cntrl[i, 1] + 40, f"{err_cntrl[i]:.3f} px", 
            color='blue', fontsize=9, weight='bold')

# Rysowanie wektorów dla punktów CHECK (Kolor czerwony)
ax.quiver(orig_check[:, 0], orig_check[:, 1], dx_check, dy_check, 
          angles='xy', scale_units='xy', scale=1/VECTOR_SCALE, color='red', 
          label='Punkty CHECK (Kontrolne)', width=0.004)

for i, k in enumerate(check_keys):
    ax.text(orig_check[i, 0] + 40, orig_check[i, 1] + 40, f"{err_check[i]:.3f} px", 
            color='red', fontsize=9, weight='bold')

ax.set_title(f"Wizualizacja bledow reprojekcji (Skala wektorow błędu: {VECTOR_SCALE}x)", fontsize=14, weight='bold')
ax.legend(loc='upper right')
plt.axis('off')
plt.tight_layout()
plt.show()