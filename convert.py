# Importowanie wymaganych bibliotek
import os
import time
import shlex
import imghdr
import argparse
import subprocess
import importlib.util
from PIL import Image # type: ignore
from pathlib import Path
from datetime import datetime

# Wyczyszczenie logów sprawdzających z poprzedniego run'a
os.system(f'rm -rf /var/log/conversion/logs_date_verification')
os.system(f'rm -rf /var/log/conversion/logs_accuracy_verification')
os.system(f'rm -rf /var/log/conversion/logs_resolution_verification')

# Przygotowanie katalogów z logami
if not os.path.exists('/var/log/conversion'):
    os.makedirs('/var/log/conversion')
Path('/var/log/conversion/logs_pass').touch()
Path('/var/log/conversion/logs_unchanged').touch()
Path('/var/log/conversion/logs_date_verification').touch()
Path('/var/log/conversion/logs_accuracy_verification').touch()
Path('/var/log/conversion/logs_resolution_verification').touch()
logs_pass = '/var/log/conversion/logs_pass'
logs_unchanged = '/var/log/conversion/logs_unchanged'
logs_date = '/var/log/conversion/logs_date_verification'
logs_acc = '/var/log/conversion/logs_accuracy_verification'
logs_res = '/var/log/conversion/logs_resolution_verification'

# Zmienne do obsługi weryfikacji i instalacji paczki
package = 'ImageMagick'
install_package = 'yum install -y ImageMagick ImageMagick-devel >/dev/null 2>&1'

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
parser.add_argument("-d", "--dryrun", help="Run in test mode (1=Yes 0=No)", default = 0, type=int)

args = parser.parse_args()

quality = args.quality
year = args.year
min_resolution_input = args.min_resolution_input
replace = args.replace
suffix = args.suffix
path = args.path
dryrun= args.dryrun

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

# Konfiguracja daty do wyszukiwania zdjęć
os.system(f'touch -t {year}01010000 /tmp/{year}-Jan-01-0000')

 # Lista zdjęć
matched_files_command = f'find {path} -type f \( -iname "*.jpeg" -o -iname "*.jpg" -o -iname "*.png" \) ! -newer /tmp/{year}-Jan-01-0000 -print'
matched_files = subprocess.check_output(matched_files_command, shell=True)

# Import listy zakwalifikowanych po dacie i nazwie plików do loga
os.system(f'{matched_files_command} >> {logs_date}')

# Sortowanie listy
matched_files = matched_files.decode().splitlines()

# Uruchomienie polecenia convert dla każdego elemantu
def image_validator(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (IOError, SyntaxError):
        os.system(f'echo "{current_date}: {file_path} jest uszkodzony." >> {logs_unchanged}')
        return False

def image_type_checker(file_path):
    image_type = imghdr.what(file_path)
    if image_type in ["jpeg", "png"]:
        return True
    else:
        os.system(f'echo "{current_date}: {file_path} jest uszkodzony." >> {logs_unchanged}')
        return False

matched_files_copy = matched_files.copy()

for file_path in matched_files:
    if image_type_checker(file_path):
        if image_validator(file_path):
            os.system(f'echo "{file_path} OK." >> {logs_acc}')
        else:
            os.system(f'echo "{file_path} USZKODZONY." >> {logs_acc}')
            matched_files.remove(file_path)
    else:
        os.system(f'echo "{file_path} NIEOBRAZKOWY" >> {logs_acc}')
        matched_files.remove(file_path)

modification_time = 0

for file_path in matched_files:
    try:
        identify_command = f'identify -format "%wx%h" {shlex.quote(file_path)}'
        resolution = subprocess.check_output(identify_command, shell=True).decode().strip()
        width, height = map(int, resolution.split('x'))
    except subprocess.CalledProcessError as e:
        print(f'Error processing file: {file_path}. Skipping...')
        continue
    def conversion_with_replace(width, height, min_resolution, min_resolution_input, quality, file_path, modification_time):
        if width >= min_resolution[0] and height >= min_resolution[1]:
            modification_time = os.path.getmtime(file_path)
            subprocess.run(['convert', '-resize', f'{min_resolution_input}>', '-quality', f'{quality}%', file_path, file_path])
            os.utime(file_path, (modification_time, modification_time))
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} i nadpisano plik." >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana rozmiaru i jakości" >> {logs_res}')
        elif width < min_resolution[0] or height < min_resolution[1]:
            modification_time = os.path.getmtime(file_path)
            subprocess.run(['convert', '-quality', f'{quality}%', file_path, file_path])
            os.utime(file_path, (modification_time, modification_time))
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} i nadpisano plik (bez zmiany rozmiarów)." >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana jakości" >> {logs_res}')
        else:
            os.system(f'echo "{current_date}: Nie dokonano konwersji {file_path} - plik nie spełnia wymagań rozmiarowych." >> {logs_unchanged}')
            os.system(f'echo "{file_path} Brak zmian" >> {logs_res}')

    def conversion_with_suffix(width, height, min_resolution, min_resolution_input, quality, file_path, suffix):
        if width >= min_resolution[0] and height >= min_resolution[1]:
            subprocess.run(['convert', '-resize', f'{min_resolution_input}>', '-quality', f'{quality}%', file_path, f'{file_path}{suffix}'])
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} do {file_path}{suffix}" >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana rozmiaru i jakości" >> {logs_res}')
        elif width < min_resolution[0] or height < min_resolution[1]:
            subprocess.run(['convert', '-quality', f'{quality}%', file_path, f'{file_path}{suffix}'])
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} do {file_path}{suffix} (bez zmiany rozmiarów)" >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana jakości" >> {logs_res}')
        else:
            os.system(f'echo "{current_date}: Nie dokonano konwersji {file_path} - plik nie spełnia wymagań rozmiarowych." >> {logs_unchanged}')
            os.system(f'echo "{file_path} Brak zmian" >> {logs_res}')

    def conversion_with_replace_dry_run(width, height, min_resolution, min_resolution_input, quality, file_path, modification_time):
        if width >= min_resolution[0] and height >= min_resolution[1]:
            modification_time = os.path.getmtime(file_path)
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} i nadpisano plik." >> {logs_pass}')
            os.utime(file_path, (modification_time, modification_time))
            os.system(f'echo "{file_path} Zmiana rozmiaru i jakości" >> {logs_res}')
        elif width < min_resolution[0] or height < min_resolution[1]:
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} i nadpisano plik (bez zmiany rozmiarów)." >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana jakości" >> {logs_res}')
        else:
            os.system(f'echo "{current_date}: Nie dokonano konwersji {file_path} - plik nie spełnia wymagań rozmiarowych." >> {logs_unchanged}')
            os.system(f'echo "{file_path} Brak zmian" >> {logs_res}')

    def conversion_with_suffix_dry_run(width, height, min_resolution, min_resolution_input, quality, file_path, suffix):
        if width >= min_resolution[0] and height >= min_resolution[1]:
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} do {file_path}{suffix}" >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana rozmiaru i jakości" >> {logs_res}')
        elif width < min_resolution[0] or height < min_resolution[1]:
            os.system(f'echo "{current_date}: Dokonano konwersji {file_path} do {file_path}{suffix} (bez zmiany rozmiarów)" >> {logs_pass}')
            os.system(f'echo "{file_path} Zmiana jakości" >> {logs_res}')
        else:
            os.system(f'echo "{current_date}: Nie dokonano konwersji {file_path} - plik nie spełnia wymagań rozmiarowych." >> {logs_unchanged}')
            os.system(f'echo "{file_path} Brak zmian" >> {logs_res}')

    if replace == 1 and dryrun == 0:
        conversion_with_replace(width, height, min_resolution, min_resolution_input, quality, file_path, modification_time)
    elif replace == 0 and dryrun == 0:
        conversion_with_suffix(width, height, min_resolution, min_resolution_input, quality, file_path, suffix)
    elif replace == 1 and dryrun == 1:
        conversion_with_replace_dry_run(width, height, min_resolution, min_resolution_input, quality, file_path, modification_time)
    elif replace == 0 and dryrun == 1:
        conversion_with_suffix_dry_run(width, height, min_resolution, min_resolution_input, quality, file_path, suffix)
    else:
        print('Niepoprawny argument dla --replace')

os.system(f'rm -rf /tmp/{year}-Jan-01-0000')
