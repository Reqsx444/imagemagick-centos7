#pip install Pillow - żeby zainstalować moduł PIL
from datetime import datetime
import os
import importlib.util
import subprocess
from pathlib import Path
from PIL import Image

# Przygotowanie katalogu z logami
Path('/var/log/conversion_log_pass').touch()
Path('/var/log/conversion_log_unchanged').touch()
logs_pass = '/var/log/conversion_log_pass'
logs_unchanged = '/var/log/conversion_log_unchanged'

# Zmienne do obsługi weryfikacji i instalacji paczki
package = 'ImageMagick'
install_package = 'yum install -y ImageMagick ImageMagick-devel'

# Zapytania do klienta
quality = int(input('Docelowa jakość: '))
user_date = str(input('Data najstarszego możliwego pliku (YYYY-MM-DD): '))
min_resolution_input = input("Minimalna rozdzielczość (np. 1920x1080): ")
min_resolution = tuple(map(int, min_resolution_input.split('x')))
replace = int(input('Czy zamienić plik źródłowy plikiem docelowym? (Nie = 0 | Tak = 1): '))
if replace == 0 :
    suffix = str(input('Jaki suffix nadać dla nowych plików: '))
else:
    pass
path = str(input('Ścieżka do katalogu, w którym mają być podjęte działania: '))

# Weryfikacja, czy paczka jest zainstalowana
spec = importlib.util.find_spec(package)
if spec is None:
    os.system(install_package)
else:
    pass

# Konfiguracja datay do wyszukiwania zdjęć
def days_since(date_str):
    given_date = datetime.strptime(date_str, '%Y-%m-%d')
    today = datetime.today()
    delta = today - given_date
    return delta.days

days = days_since(user_date)

# Wyszukiwanie zdjęć
matched_files_command = f'find {path} -type f \( -iname "*.jpeg" -o -iname "*.jpg" \) -mtime +{days} -print'
matched_files = subprocess.check_output(matched_files_command, shell=True)

matched_files = matched_files.decode().splitlines()

# Uruchomienie polecenia convert dla każdego elemantu
for file_path in matched_files:

def jpg_checker(file_path):
    try:
        img = Image.open(file_path)
        img.verify()
        return True
    except (IOError, SyntaxError):
        return False

if jpg_checker(file_path):
    pass
else:
    matched_files.remove(file_path)

for file_path in matched_files:
    identify_command = f'identify -format "%wx%h" "{file_path}"'
    resolution = subprocess.check_output(identify_command, shell=True).decode().strip()
    width, height = map(int, resolution.split('x'))
    def conversion_with_replace(width, height, min_resolution, min_resolution_input, quality, file_path):
        if width > min_resolution[0] and height > min_resolution[1]:
            os.system(f'convert -resize {min_resolution_input} -quality {quality}% {file_path} {file_path}')
            os.system(f'echo "Dokonano konwersji {file_path} i nadpisano plik." >> {logs_pass}')
        else:
            os.system(f'echo "Nie dokonano konwersji {file_path} - plik nie spełnia wymagań." >> {logs_unchanged}')

    def conversion_with_suffix(width, height, min_resolution, min_resolution_input, quality, file_path, suffix):
        if width > min_resolution[0] and height > min_resolution[1]:
            os.system(f'convert -resize {min_resolution_input} -quality {quality}% {file_path} {file_path}{suffix}')
            os.system(f'echo "Dokonano konwersji {file_path} do {file_path}{suffix}" >> {logs_pass}')
        else:
            os.system(f'echo "Nie dokonano konwersji {file_path} - plik nie spełnia wymagań." >> {logs_unchanged}')

    if replace == 1:
        conversion_with_replace(width, height, min_resolution, min_resolution_input, quality, file_path)
    else:
        conversion_with_suffix(width, height, min_resolution, min_resolution_input, quality, file_path, suffix)