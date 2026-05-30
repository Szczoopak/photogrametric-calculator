import argparse
import json
import cv2

# Obsługa wejścia z linii komend
parser = argparse.ArgumentParser(description="Weryfikacja wizualna klikniętych punktów")
parser.add_argument('--img1', required=True, help="Ścieżka do pierwszego zdjęcia (.jpg)")
parser.add_argument('--img2', required=True, help="Ścieżka do drugiego zdjęcia (.jpg)")
parser.add_argument('--uv', required=True, help="Ścieżka do Twojego pliku JSON z punktami")
args = parser.parse_args()

# Wczytywanie danych i filtrowanie
with open(args.uv, 'r') as f:
    data = json.load(f)

img1 = cv2.imread(args.img1)
img2 = cv2.imread(args.img2)

if img1 is None or img2 is None:
    raise ValueError("Nie udało się wczytać jednego lub obu zdjęć! Sprawdź ścieżki do plików.")

point_keys = [k for k in data.keys() if isinstance(data[k], dict)]

if not point_keys:
    raise ValueError("Brak punktów w pliku JSON!")

# Pobieramy pierwszy prawdziwy punkt, by odczytać z niego nazwy zdjęć
first_pt = data[point_keys[0]]
keys = list(first_pt.keys())

if len(keys) < 2:
    raise ValueError("Plik JSON musi zawierać współrzędne dla dokładnie 2 zdjęć.")

key1, key2 = keys[0], keys[1]
print(f"Rysowanie punktów dla zdjęć z kluczami: '{key1}' oraz '{key2}'")

# Rysowanie punktów
for pt_name in point_keys:
    coords = data[pt_name]
    
    # Rysowanie na pierwszym zdjęciu
    if key1 in coords:
        u, v = int(coords[key1][0]), int(coords[key1][1])
        # Zielony okrąg wokół punktu
        cv2.circle(img1, (u, v), radius=40, color=(0, 255, 0), thickness=6)
        # Czerwona kropka w samym centrum
        cv2.circle(img1, (u, v), radius=5, color=(0, 0, 255), thickness=-1)
        # Nazwa punktu
        cv2.putText(img1, pt_name, (u + 35, v - 35), cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0, 0, 255), 6)

    # Rysowanie na drugim zdjęciu
    if key2 in coords:
        u, v = int(coords[key2][0]), int(coords[key2][1])
        # Zielony okrąg wokół punktu
        cv2.circle(img2, (u, v), radius=40, color=(0, 255, 0), thickness=6)
        # Czerwona kropka w samym centrum
        cv2.circle(img2, (u, v), radius=5, color=(0, 0, 255), thickness=-1)
        # Nazwa punktu
        cv2.putText(img2, pt_name, (u + 35, v - 35), cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0, 0, 255), 6)

# Wizualizacja - skalowanie do ekranu
def resize_to_screen(image, target_width=1000):
    scale = target_width / image.shape[1]
    target_height = int(image.shape[0] * scale)
    return cv2.resize(image, (target_width, target_height))

img1_show = resize_to_screen(img1, target_width=1000)
img2_show = resize_to_screen(img2, target_width=1000)

cv2.imshow(f"Weryfikacja: {key1}", img1_show)
cv2.imshow(f"Weryfikacja: {key2}", img2_show)

print("\n[SUKCES] Wygenerowano okna ze zdjęciami.")
print("Naciśnij dowolny klawisz klawiatury będąc w oknie zdjęcia, aby zamknąć program.")
cv2.waitKey(0)
cv2.destroyAllWindows()