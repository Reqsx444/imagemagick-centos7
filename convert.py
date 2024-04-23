#pip install Pillow - żeby zainstalować moduł PIL
# Importowanie wymaganych bibliotek
import os
import time
import argparse
import subprocess
import importlib.util
from PIL import Image
from pathlib import Path
from datetime import datetime

# Przygotowanie katalogu z logami
Path('/var/log/conversion_log_pass').touch()
Path('/var/log/conversion_log_unchanged').touch()
logs_pass = '/var/log/conversion_log_pass'
logs_unchanged = '/var/log/conversion_log_unchanged'

# Zmienne do obsługi weryfikacji i instalacji paczki
package = 'ImageMagick'
install_package = 'yum install -y ImageMagick ImageMagick-devel'

# Weryfikacja, czy paczka jest zainstalowana
spec = importlib.util.find_spec(package)
if spec is None:
    os.system(install_package)
else:
    pass

# Obsługa flag
parser = argparse.ArgumentParser()
parser.add_argument("-q", "--quality", help="Target image quality", type=int)
parser.add_argument("-y", "--year", help="Max file year", type=int)
parser.add_argument("-r", "--min_resolution_input", help="Target resolution")
parser.add_argument("-c", "--replace", help="Override file (1=Yes 0=No)", default = 1, type=int)
parser.add_argument("-s", "--suffix", help="Add suffix to converted image")
parser.add_argument("-p", "--path", help="Path to dir")

args = parser.parse_args()

quality = args.quality
year = args.year
min_resolution_input = args.min_resolution_input
replace = args.replace
suffix = args.suffix
path = args.path

# Zapytania do klienta, jeśli flagi nie zostały podane
if quality and year and path and min_resolution_input:
    min_resolution = tuple(map(int, min_resolution_input.split('x')))
else:
    quality = int(input('Docelowa jakość: '))
    year = int(input('Do którego roku?: '))
    min_resolution_input = input("Docelowa rozdzielczość (np. 1920x1080): ")
    min_resolution = tuple(map(int, min_resolution_input.split('x')))
    replace = int(input('Czy zamienić plik źródłowy plikiem docelowym? (Nie = 0 | Tak = 1): '))
    if replace == 0 :
        suffix = str(input('Jaki suffix nadać dla nowych plików: '))
    else:
        pass
    path = str(input('Ścieżka do katalogu, w którym mają być podjęte działania: '))

timestamp = time.time()
current_date = time.ctime(timestamp)

# Konfiguracja datay do wyszukiwania zdjęć
os.system(f'touch -t {year}01010000 /tmp/{year}-Jan-01-0000')

# Lista zdjęć
matched_files_command = f'find {path} -type f \( -iname "*.jpeg" -o -iname "*.jpg" \) ! -newer /tmp/{year}-Jan-01-0000 -print'
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
            os.system(f'echo "{current_date}: {file_path} jest uszkodzony." >> {logs_unchanged}')
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
        if width >= min_resolution[0] and height >= min_resolution[1]:
            os.system(f'convert -resize {min_resolution_input} -quality {quality}% {file_path} {file_path}')
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} i nadpisano plik." >> {logs_pass}')
        else:
            os.system(f'echo "{current_date}: Nie dokonano konwersji {file_path} - plik nie spełnia wymagań." >> {logs_unchanged}')

    def conversion_with_suffix(width, height, min_resolution, min_resolution_input, quality, file_path, suffix):
        if width >= min_resolution[0] and height >= min_resolution[1]:
            os.system(f'convert -resize {min_resolution_input} -quality {quality}% {file_path} {file_path}{suffix}')
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} do {file_path}{suffix}" >> {logs_pass}')
        else:
            os.system(f'echo "{current_date}: Nie dokonano konwersji {file_path} - plik nie spełnia wymagań." >> {logs_unchanged}')

    if replace == 1:
        conversion_with_replace(width, height, min_resolution, min_resolution_input, quality, file_path)
    else:
        conversion_with_suffix(width, height, min_resolution, min_resolution_input, quality, file_path, suffix)

os.system(f'rm -rf /tmp/{year}-Jan-01-0000')
