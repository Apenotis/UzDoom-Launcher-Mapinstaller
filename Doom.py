import os, sys, subprocess, time, math, urllib.request, json, csv, re, random, zipfile, shutil, configparser
from datetime import datetime
from pathlib import Path

def download_uzdoom():
    print(f"\n  {Colors.MAGENTA}>>> Lade UZDoom Engine herunter... Bitte warten. <<<{Colors.WHITE}")
    print(f"  {Colors.GRAY}(Suche automatisch nach der neuesten Version...){Colors.WHITE}")
    
    # 1. Neueste Version über die GitHub API abfragen
    api_url = "https://api.github.com/repos/UZDoom/UZDoom/releases/latest"
    download_url = ""
    
    try:
        req = urllib.request.Request(api_url)
        req.add_header('User-Agent', 'Python-Launcher')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            # 2. In den hochgeladenen Dateien nach der Windows-ZIP suchen
            for asset in data.get('assets', []):
                name = asset.get('name', '').lower()
                if 'windows' in name and name.endswith('.zip'):
                    download_url = asset.get('browser_download_url')
                    break
                    
    except Exception as e:
        print(f"  {Colors.RED}[!] Verbindung zu GitHub fehlgeschlagen: {e}{Colors.WHITE}")
        return

    if not download_url:
        print(f"  {Colors.RED}[!] Keine Windows-Version im aktuellen Release gefunden.{Colors.WHITE}")
        return
        
    print(f"  {Colors.GRAY}(Lade Datei: {download_url.split('/')[-1]}){Colors.WHITE}")
    
    zip_path = os.path.join(BASE_DIR, "uzdoom_temp.zip")
    uz_dir = os.path.join(BASE_DIR, "UzDoom")
    
    # 3. Datei herunterladen und entpacken
    try:
        urllib.request.urlretrieve(download_url, zip_path)
        print(f"  {Colors.GREEN}[+]{Colors.WHITE} Download abgeschlossen. Entpacke Dateien...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(uz_dir)
            
        os.remove(zip_path) # Räumt die ZIP-Datei danach auf
        print(f"  {Colors.GREEN}[+]{Colors.WHITE} UZDoom wurde erfolgreich installiert!")
        
    except Exception as e:
        print(f"  {Colors.RED}[!] Fehler beim Herunterladen oder Entpacken: {e}{Colors.WHITE}")

def real_len(text):
    """Gibt die sichtbare Länge eines Strings ohne ANSI-Farbcodes zurück."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', text))

def resize_terminal(cols, lines):
    if os.name == 'nt':
        os.system(f'mode con: cols={cols} lines={lines}')
    sys.stdout.write(f"\x1b[8;{lines};{cols}t")
    sys.stdout.flush()

os.system('') 

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[0m'
    GRAY = '\033[90m'

SHOW_STATS = False
USE_MODS = False
DEBUG_MODE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "maps.csv")
IWAD_DIR = os.path.join(BASE_DIR, "iwad")
PWAD_DIR = os.path.join(BASE_DIR, "pwad")
UZ = os.path.join(BASE_DIR, "UzDoom", "uzdoom.exe")
CUR_VERSION = "4.14.3"
TIME_FILE = os.path.join(BASE_DIR, "total_time.txt")
terminal_width = 200
DEFAULT_ENGINE = "uzdoom"
CURRENT_ENGINE = DEFAULT_ENGINE
#ENGINES_DIR = "engines"
CONFIG_FILE = "config.ini"

# Liste der unterstützten Engines (Namen der EXEs ohne .exe)
SUPPORTED_ENGINES = ["uzdoom", "gzdoom", "zandronum", "zdoom", "lzdoom"]

def toggle_map_clear(map_id):
    if not os.path.exists(CSV_FILE): return False
    rows = []
    found = False
    search_id = map_id.upper()
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        # FEHLER BEHOBEN: Wir nutzen jetzt das Standard-Trennzeichen (Komma)
        reader = list(csv.reader(f))
        if not reader: return False
        
        header = reader[0]
        rows.append(header)
        
        for row in reader[1:]:
            if not row: continue
            
            # Die ID (Spalte 0) auslesen und Leerzeichen entfernen
            if row[0].strip().upper() == search_id:
                found = True
                # Toggle: Wenn [C] da ist, entfernen. Wenn nicht, hinzufügen.
                if " [C]" in row[2]:
                    row[2] = row[2].replace(" [C]", "")
                else:
                    row[2] = row[2] + " [C]"
            rows.append(row)
    
    if found:
        with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
            # FEHLER BEHOBEN: Auch hier das Semikolon entfernt!
            writer = csv.writer(f)
            writer.writerows(rows)
    return found

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_total_seconds():
    if not os.path.exists(TIME_FILE):
        return 0
    with open(TIME_FILE, 'r') as f:
        content = f.read().strip()
        return int(content) if content.isdigit() else 0

def save_total_seconds(seconds):
    with open(TIME_FILE, 'w') as f:
        f.write(str(seconds))

def format_time(total_seconds):
    h = math.floor(total_seconds / 3600)
    m = math.floor((total_seconds % 3600) / 60)
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def check_update():
    try:
        req = urllib.request.Request('https://api.github.com/repos/UZDoom/UZDoom/releases/latest')
        req.add_header('User-Agent', 'Python-Launcher')
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            latest = data.get('tag_name', CUR_VERSION)
            return latest != CUR_VERSION, latest
    except Exception:
        return False, CUR_VERSION

def get_last_played():
    last_file = os.path.join(BASE_DIR, "last_played.txt")
    if os.path.exists(last_file):
        with open(last_file, 'r') as f:
            return f.read().strip()
    return ""

def update_csv_playtime(target_id, add_minutes):
    """Aktualisiert die Spielzeit einer bestimmten ID in der maps.csv"""
    if not os.path.exists(CSV_FILE) or add_minutes <= 0: 
        return
        
    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if 'Playtime' not in fieldnames:
            return # Sicherheitsabbruch, falls die Spalte fehlt
            
        for row in reader:
            if row.get('ID', '').strip() == target_id:
                current_time = int(row.get('Playtime', '0'))
                row['Playtime'] = str(current_time + add_minutes)
                row['LastPlayed'] = datetime.now().strftime("%d.%m.%Y") # Update auch das Datum!
            rows.append(row)
            
    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def get_next_id(game_type):
    """
    Findet die nächste freie ID basierend auf dem Spieltyp.
    game_type: 'DOOM', 'HERETIC' oder 'HEXEN'
    """
    if not os.path.exists(CSV_FILE):
        return "1" if game_type == 'DOOM' else (f"H1" if game_type == 'HERETIC' else "HX1")
    
    prefix = ""
    if game_type == 'HERETIC': prefix = "H"
    elif game_type == 'HEXEN': prefix = "HX"
    
    ids = []
    # 'utf-8-sig' filtert unsichtbare Sonderzeichen am Dateianfang (BOM)
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        if not lines: return "1" if game_type == 'DOOM' else f"{prefix}1"
        
        # Dynamische Prüfung auf Komma oder Semikolon
        delim = ';' if ';' in lines[0] else ','
        reader = csv.DictReader(lines, delimiter=delim)
        
        for row in reader:
            if not reader.fieldnames: continue
            # Wir nehmen immer die erste Spalte (ID)
            id_val = str(row.get(reader.fieldnames[0], '')).strip().upper()
            
            if game_type == 'DOOM':
                # Suche nach reinen Zahlen (deine Bestands-IDs)
                if id_val.isdigit():
                    ids.append(int(id_val))
            else:
                # Suche nach Präfix (H oder HX)
                if id_val.startswith(prefix):
                    num_part = id_val[len(prefix):]
                    if num_part.isdigit():
                        ids.append(int(num_part))
    
    next_num = max(ids) + 1 if ids else 1
    return f"{next_num}" if game_type == 'DOOM' else f"{prefix}{next_num}"

def run_installer():
    INSTALL_DIR = os.path.join(BASE_DIR, "Install")
    # Hier nutzen wir die globale Variable CSV_FILE, die du oben definiert hast
    target_csv = CSV_FILE 

    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
        print(f"\n  {Colors.YELLOW}[!] Der Ordner 'Install' wurde erstellt.{Colors.WHITE}")
        print(f"  {Colors.YELLOW}Lege dort deine WADs/ZIPs ab und drücke danach wieder [I].{Colors.WHITE}")
        time.sleep(3)
        return

    items = os.listdir(INSTALL_DIR)
    if not items:
        print(f"\n  {Colors.YELLOW}Keine neuen Dateien im Install-Ordner gefunden.{Colors.WHITE}")
        time.sleep(2)
        return

    print(f"\n {Colors.CYAN}--- INSTALLATION LÄUFT ---{Colors.WHITE}")
    installed_count = 0

    # Phase 1: Entpacken und Sortieren
    for item in items:
        item_path = os.path.join(INSTALL_DIR, item)
        if os.path.isfile(item_path):
            ext = item.lower().rsplit('.', 1)[-1] if '.' in item else ""
            folder_name = item.rsplit('.', 1)[0]
            tmp_f = os.path.join(INSTALL_DIR, folder_name)

            if ext == 'zip':
                print(f"  {Colors.MAGENTA}[*]{Colors.WHITE} Entpacke ZIP: {item}...")
                os.makedirs(tmp_f, exist_ok=True)
                try:
                    with zipfile.ZipFile(item_path, 'r') as z: 
                        z.extractall(tmp_f)
                    os.remove(item_path)
                except Exception as e: 
                    print(f"  {Colors.RED}[!] Fehler: {e}{Colors.WHITE}")
            
            elif ext in ['wad', 'pk3', 'pk7']:
                print(f"  {Colors.MAGENTA}[*]{Colors.WHITE} Verpacke Datei: {item}...")
                os.makedirs(tmp_f, exist_ok=True)
                shutil.move(item_path, os.path.join(tmp_f, item))

    # Phase 2: In PWAD Ordner verschieben und CSV-Eintrag erstellen
    folders = [d for d in os.listdir(INSTALL_DIR) if os.path.isdir(os.path.join(INSTALL_DIR, d))]
    for folder in folders:
        full_path = os.path.join(INSTALL_DIR, folder)
        m_name = folder.replace("_", " ")
        m_core = "doom2.wad"
        
        # Basis-Spiel ermitteln
        txt_files = [f for f in os.listdir(full_path) if f.lower().endswith(".txt")]
        if txt_files:
            try:
                with open(os.path.join(full_path, txt_files[0]), 'r', encoding='utf-8', errors='ignore') as txt:
                    content = txt.read().lower()
                    if "heretic" in content: m_core = "heretic.wad"
                    elif "hexen" in content: m_core = "hexen.wad"
                    elif "plutonia" in content: m_core = "plutonia.wad"
                    elif "tnt" in content: m_core = "tnt.wad"
                    elif "doom.wad" in content: m_core = "doom.wad"
            except: pass

        kat, pref = ("EXTRA", "H") if "heretic" in m_core else (("EXTRA", "HX") if "hexen" in m_core else ("PWAD", "D"))

        target_name = folder.replace(" ", "_")
        target_path = os.path.join(PWAD_DIR, target_name)

        if not os.path.exists(target_path):
            shutil.move(full_path, target_path)
            
            # 1. Spieltyp für die ID-Vergabe bestimmen
            if "heretic.wad" in m_core.lower():
                game_type = 'HERETIC'
                kat = "EXTRA"
            elif "hexen.wad" in m_core.lower():
                game_type = 'HEXEN'
                kat = "EXTRA"
            else:
                game_type = 'DOOM'
                kat = "PWAD"

            # 2. Neue ID generieren
            new_id = get_next_id(game_type)
            
            # 3. FIX: Sicherstellen, dass die CSV-Datei mit einer neuen Zeile endet
            if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
                with open(CSV_FILE, 'rb+') as f:
                    f.seek(-1, os.SEEK_END)
                    if f.read(1) != b'\n':
                        f.write(b'\n')
            
            # 4. In die CSV schreiben
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID", "Name", "IWAD", "Ordner", "MOD", "ARGS", "Kategorie", "Playtime", "LastPlayed"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Falls Datei leer ist, Header schreiben
                if os.path.getsize(CSV_FILE) == 0:
                    writer.writeheader()
                    
                writer.writerow({
                    "ID": new_id,
                    "Name": m_name,
                    "IWAD": m_core,
                    "Ordner": target_name,
                    "MOD": "0",
                    "ARGS": "",
                    "Kategorie": kat,
                    "Playtime": "0",
                    "LastPlayed": "-"
                })

            print(f"  {Colors.GREEN}[+]{Colors.WHITE} Installiert: {Colors.YELLOW}{m_name}{Colors.WHITE} (ID: {new_id})")
            installed_count += 1
        else:
            print(f"  {Colors.RED}[!] Übersprungen: {folder} existiert bereits.{Colors.WHITE}")
            shutil.rmtree(full_path)

    if installed_count > 0:
        print(f"\n  {Colors.GREEN}Installation erfolgreich abgeschlossen!{Colors.WHITE}")
    time.sleep(2)

def load_maps():
    blocks = {1: [], 2: [], 3: []} 
    
    if not os.path.exists(CSV_FILE):
        return blocks
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content.strip(): 
            return blocks
        f.seek(0)
        
        try:
            dialect = csv.Sniffer().sniff(content[:2048], delimiters=',;')
        except csv.Error:
            dialect = 'excel'
            
        reader = csv.DictReader(f, dialect=dialect)
        
        for row in reader:
            # --- SICHERER DATEN-ABRUF (Verhindert den Absturz) ---
            def safe_get(keys, default=""):
                if isinstance(keys, str): keys = [keys]
                for k in keys:
                    val = row.get(k)
                    if val is not None:
                        return str(val).strip()
                return default

            # Wir nutzen safe_get für alle Felder
            entry_id = safe_get('ID')
            name     = safe_get('Name', 'Unbekannt')
            core     = safe_get(['Core', 'IWAD'])
            ordner   = safe_get(['Ordner_oder_Datei', 'Ordner', 'PWAD'])
            mods     = safe_get(['ModsErlaubt', 'MOD'], '0')
            if not mods: mods = "0"
            extra    = safe_get(['Extra', 'ARGS'])
            cat      = safe_get('Kategorie').upper()
            
            # --- Deine Kategorisierungs-Logik ---
            if not cat:
                if "heretic" in core.lower() or "hexen" in core.lower():
                    cat = "EXTRA"
                elif "doom2" in core.lower() and ordner:
                    cat = "PWAD"
                else:
                    cat = "IWAD"
            
            # --- Playtime auslesen und formatieren ---
            try:
                play_val = row.get('Playtime', '0')
                playtime_min = int(play_val) if play_val and str(play_val).isdigit() else 0
            except (ValueError, TypeError):
                playtime_min = 0

            playtime_str = ""
            if playtime_min > 0:
                if playtime_min >= 60:
                    h = playtime_min // 60
                    m = playtime_min % 60
                    playtime_str = f"[{h}h {m}m]"
                else:
                    playtime_str = f"[{playtime_min}m]"

            base_str = f"{entry_id} - {name}"
            
            if playtime_str:
                display_text = f"{base_str} {Colors.GRAY}{playtime_str}{Colors.WHITE}"
            else:
                display_text = base_str
            
            remaining = []
            if ordner: remaining.append(ordner)
            remaining.append(mods)
            if extra: remaining.extend(extra.split())
            
            # Zuordnung zu den Blocks (Tupel-Struktur beibehalten)
            if cat == 'IWAD':
                blocks[1].append((display_text, entry_id, core, name, remaining, 1))
            elif cat == 'PWAD':
                blocks[2].append((display_text, entry_id, core, name, remaining, 2))
            elif cat in ['EXTRA', 'HERETIC', 'HEXEN']:
                blocks[3].append((display_text, entry_id, core, name, remaining, 3))

        # --- Deine Präfix-Optimierung für Block 3 ---
        formatted_col4 = []
        last_prefix = None
        
        for item in blocks[3]:
            current_id = item[1]
            # HX1 -> HX
            current_prefix = str(current_id).rstrip("0123456789").upper()
            
            if last_prefix and current_prefix != last_prefix:
                formatted_col4.append(("EMPTY", "EMPTY", "", "", [], 3))
                
            formatted_col4.append(item)
            last_prefix = current_prefix
            
        blocks[3] = formatted_col4
                
    return blocks

def initial_setup():
    setup_activity = False
    
    # Kurz das Terminal leeren für eine saubere Setup-Ansicht
    clear_screen()
    
    # 1. Ordner prüfen und bei Bedarf erstellen
    required_dirs = [
        "iwad", "pwad", "mods", 
        os.path.join("mods", "doom"), 
        os.path.join("mods", "heretic"), 
        os.path.join("mods", "hexen"), 
        "UzDoom"
    ]
    
    print(f"\n {Colors.CYAN}--- ERSTEINRICHTUNG / SYSTEMPRÜFUNG ---{Colors.WHITE}\n")
    
    for d in required_dirs:
        path = os.path.join(BASE_DIR, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"  {Colors.GREEN}[+]{Colors.WHITE} Ordner erstellt: {Colors.YELLOW}{d}{Colors.WHITE}")
            setup_activity = True

    # 2. CSV-Datei prüfen und bei Bedarf mit Standardwerten erstellen
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
            # NEU: Der Header enthält jetzt Playtime und LastPlayed
            f.write("ID,Name,IWAD,Ordner,MOD,ARGS,Kategorie,Playtime,LastPlayed\n")
            # NEU: Die Standard-Einträge haben jetzt eine 0 für Playtime und ein "-" für LastPlayed
            f.write("1,Ultimate Doom,doom.wad,0,0,,IWAD,0,-\n")
            f.write("2,Doom II: Hell on Earth,doom2.wad,0,0,,IWAD,0,-\n")
        print(f"  {Colors.GREEN}[+]{Colors.WHITE} Standard-Datenbank erstellt: {Colors.YELLOW}maps.csv{Colors.WHITE}")
        setup_activity = True

    # 3. Engine (uzdoom.exe) prüfen
    if not os.path.exists(UZ):
        print(f"  {Colors.RED}[!] WICHTIG: UzDoom Engine fehlt!{Colors.WHITE}")
        dl_choice = input(f"      Möchtest du UZDoom jetzt automatisch herunterladen? (j/n): ").strip().lower()
        if dl_choice == 'j':
            download_uzdoom()
        else:
            print(f"      Bitte entpacke die {Colors.CYAN}uzdoom.exe{Colors.WHITE} manuell in den Ordner '{Colors.YELLOW}UzDoom{Colors.WHITE}'.")
        setup_activity = True

    # 4. IWADs (Basisspiele) prüfen
    iwad_path = os.path.join(BASE_DIR, "iwad")
    iwads_found = [f for f in os.listdir(iwad_path) if f.lower().endswith(('.wad', '.pk3'))] if os.path.exists(iwad_path) else []
    
    if not iwads_found:
        print(f"  {Colors.RED}[!] WICHTIG: Keine Hauptspiele (IWADs) gefunden!{Colors.WHITE}")
        print(f"      Bitte kopiere z.B. {Colors.CYAN}doom.wad{Colors.WHITE} oder {Colors.CYAN}doom2.wad{Colors.WHITE} in den Ordner '{Colors.YELLOW}iwad{Colors.WHITE}'.")
        setup_activity = True

# 5. Spielzeit-Tracker (total_time.txt) prüfen
    time_file = os.path.join(BASE_DIR, "total_time.txt")
    if not os.path.exists(time_file):
        with open(time_file, 'w', encoding='utf-8') as f:
            f.write("0")
        print(f"  {Colors.GREEN}[+]{Colors.WHITE} Spielzeit-Tracker erstellt: {Colors.YELLOW}total_time.txt{Colors.WHITE}")
        setup_activity = True

    # Wenn etwas neu erstellt oder eine Warnung ausgegeben wurde, warten wir kurz auf den Nutzer
    if setup_activity:
        print(f"\n {Colors.CYAN}---------------------------------------{Colors.WHITE}")
        print(f" {Colors.YELLOW}Einrichtung abgeschlossen oder Hinweise gefunden.{Colors.WHITE}")
        input(f" {Colors.WHITE}Drücke {Colors.GREEN}ENTER{Colors.WHITE}, um den Launcher zu starten... ")

def fetch_doom_api(url, raw=False):
    """ Hilfsfunktion: Holt Daten und stellt sicher, dass immer eine Liste oder ein Dict zurückkommt """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            if raw: 
                return data if data is not None else {}
            
            content = data.get('content') if data else {}
            if content is None: content = {}
            
            files = content.get('file', [])
            if files is None: files = []
            if isinstance(files, dict): files = [files]
            return files
    except Exception:
        return [] if not raw else {}

def fetch_folder_files(folder_name):
    """ Hilfsfunktion: Holt alle Dateien aus einem Ordner über die API """
    url = f"https://www.doomworld.com/idgames/api/api.php?action=getcontents&name={folder_name}&out=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            content = data.get('content', {})
            # Wir sammeln Dateien (file) und Unterordner (dir)
            files = content.get('file', [])
            if isinstance(files, dict): files = [files]
            
            subdirs = content.get('dir', [])
            if isinstance(subdirs, dict): subdirs = [subdirs]
            
            return files, subdirs
    except:
        return [], []

def fetch_folder_files(folder_name):
    """ Holt Dateien und Unterordner. Garantiert immer zwei Listen als Rückgabe. """
    url = f"https://www.doomworld.com/idgames/api/api.php?action=getcontents&name={folder_name}&out=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            content = data.get('content', {})
            if not content: return [], []
            
            # Files extrahieren & absichern
            f = content.get('file', [])
            if f is None: f = []
            if isinstance(f, dict): f = [f]
            
            # Dirs extrahieren & absichern
            d = content.get('dir', [])
            if d is None: d = []
            if isinstance(d, dict): d = [d]
            
            return f, d
    except:
        return [], []

def get_engine_path():
    """ Sucht die .exe im Engine-Ordner im Root-Verzeichnis (z.B. uzdoom/uzdoom.exe) """
    exe_name = f"{CURRENT_ENGINE}.exe"
    
    # Pfad-Struktur: ./uzdoom/uzdoom.exe
    path_in_folder = os.path.join(CURRENT_ENGINE, exe_name)
    
    if os.path.exists(path_in_folder):
        return path_in_folder
    
    # Fallback: Falls die exe doch direkt im Root ohne Ordner liegt
    if os.path.exists(exe_name):
        return exe_name
        
    return exe_name # Fallback auf System-Umgebung

def select_engine():
    """ Menü zur Engine-Wahl """
    global CURRENT_ENGINE
    while True:
        clear_screen()
        print(f"\n  {Colors.MAGENTA}--- ENGINE-AUSWAHL ---{Colors.WHITE}")
        print(f"  Aktuell: {Colors.CYAN}{CURRENT_ENGINE}{Colors.WHITE}\n")
        
        found = []
        for i, eng in enumerate(SUPPORTED_ENGINES):
            exe_n = f"{eng}.exe"
            # Wir prüfen: ./name/name.exe ODER direkt im Root
            path_check = os.path.join(eng, exe_n)
            is_ready = os.path.exists(path_check) or os.path.exists(exe_n)
            
            status = f"{Colors.GREEN}[BEREIT]{Colors.WHITE}" if is_ready else f"{Colors.GRAY}[NICHT GEFUNDEN]{Colors.WHITE}"
            print(f"  {Colors.YELLOW}[{i+1}]{Colors.WHITE} {eng:<12} {status}")
            found.append(eng)

        print(f"\n  {Colors.YELLOW}[0]{Colors.WHITE} Zurück")
        choice = input(f"\n  Wahl: ").strip()
        
        if choice == '0' or not choice: break
        if choice.isdigit() and 0 < int(choice) <= len(found):
            CURRENT_ENGINE = found[int(choice)-1]
            save_settings()
            break

def search_doomworld():
    print(f"\n  {Colors.MAGENTA}--- DOOMWORLD ONLINE-ARCHIV ---{Colors.WHITE}")
    print(f"  {Colors.YELLOW}[1]{Colors.WHITE} Manuelle Suche (Name/Titel)")
    print(f"  {Colors.YELLOW}[2]{Colors.WHITE} Top Megawads: {Colors.CYAN}Doom 1{Colors.WHITE}")
    print(f"  {Colors.YELLOW}[3]{Colors.WHITE} Top Megawads: {Colors.CYAN}Doom 2{Colors.WHITE}")
    
    choice = input(f"\n  Option wählen (ENTER zum Abbruch): ").strip()
    if not choice: return

    all_results = []
    
    # --- DATENBESCHAFFUNG ---
    if choice == '1':
        query = input(f"  Suchbegriff: ").strip()
        if not query: return
        url = f"https://www.doomworld.com/idgames/api/api.php?action=search&query={urllib.parse.quote(query)}&type=title&sort=rating&dir=desc&out=json"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                res = data.get('content', {}).get('file', [])
                if res is None: res = []
                all_results = [res] if isinstance(res, dict) else res
        except: pass

    elif choice in ['2', '3']:
        main_folders = ["levels/doom/megawads/"] if choice == '2' else ["levels/doom2/megawads/", "levels/doom2/Ports/megawads/"]
        
        print(f"  {Colors.GRAY}Synchronisiere mit Doomworld... bitte warten...{Colors.WHITE}")
        for folder in main_folders:
            # 1. Dateien im Hauptordner
            files, subdirs = fetch_folder_files(folder)
            if files: all_results.extend(files)
            
            # 2. Unterordner scannen (A-Z)
            if subdirs:
                for sd in subdirs:
                    if sd and 'name' in sd:
                        sys.stdout.write(f"\r  Scanne: {sd['name'][-20:]}   ")
                        sys.stdout.flush()
                        s_files, _ = fetch_folder_files(sd['name'])
                        if s_files: all_results.extend(s_files)
        print("\r" + " " * 60 + "\r", end="")

    if not all_results:
        print(f"  {Colors.RED}[!] Keine Karten gefunden.{Colors.WHITE}")
        input("  ENTER..."); return

    # --- SORTIERUNG & NAVIGATION (PAGINATION) ---
    all_results.sort(key=lambda x: float(x.get('rating', 0) or 0), reverse=True)

    page_size = 50  # Karten pro Seite
    current_start = 0

    while True:
        clear_screen()
        total = len(all_results)
        current_end = min(current_start + page_size, total)
        
        print(f"\n  {Colors.MAGENTA}--- DOOMWORLD ERGEBNISSE ({current_start + 1} bis {current_end} von {total}) ---{Colors.WHITE}")
        print(f"  {'#':<4} {'Titel':<40} {'Größe':<10} {'Rating'}")
        print(f"  {'-' * 72}")

        # Aktuellen Block anzeigen
        for i in range(current_start, current_end):
            res = all_results[i]
            title = res.get('title') or res.get('filename') or 'Unbekannt'
            title = str(title)[:39]
            
            try:
                size_bytes = int(res.get('size', 0))
                size_mb = f"{size_bytes / (1024*1024):.1f} MB"
            except: size_mb = "?? MB"
                
            try:
                r_val = float(res.get('rating', 0) or 0)
            except: r_val = 0.0
            
            stars = "★" * int(r_val)
            if r_val % 1 >= 0.5: stars += "½"
            
            print(f"  {Colors.YELLOW}[{i+1:<3}]{Colors.WHITE} {title:<40} {Colors.CYAN}{size_mb:<10}{Colors.WHITE} {Colors.GREEN}{stars:<10}{Colors.WHITE}")

        # Navigationstipps
        print(f"\n  {Colors.MAGENTA}Navigation:{Colors.WHITE}")
        nav_options = []
        if current_end < total:
            nav_options.append(f"[{Colors.YELLOW}N{Colors.WHITE}] Nächste Seite")
        if current_start > 0:
            nav_options.append(f"[{Colors.YELLOW}B{Colors.WHITE}] Vorherige Seite")
        
        if nav_options:
            print("  " + "  ".join(nav_options))
        
        sel = input(f"\n  Nummer wählen, {Colors.YELLOW}N{Colors.WHITE}/{Colors.YELLOW}B{Colors.WHITE} blättern oder ENTER für Abbruch: ").strip().lower()

        if not sel: 
            break
        elif sel == 'n' and current_end < total:
            current_start += page_size
        elif sel == 'b' and current_start > 0:
            current_start -= page_size
        elif sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < total:
                download_idgames(all_results[idx])
                break # Nach Download zurück zum Hauptmenü
            else:
                print(f"  {Colors.RED}[!] Ungültige Nummer.{Colors.WHITE}")
                time.sleep(1)

def download_idgames(file_data):
    TEMP_DIR = "install"  # Nur noch als Zwischenspeicher
    FINAL_DIR = "pwad"    # Das eigentliche Ziel für deine Mods
    
    # Sicherstellen, dass beide Ordner existieren
    for d in [TEMP_DIR, FINAL_DIR]:
        if not os.path.exists(d): os.makedirs(d)

    # 1. Daten vorbereiten
    filename = file_data.get('filename')
    folder_name = os.path.splitext(filename)[0]
    title = (file_data.get('title') or filename).replace(',', ' ')
    
    temp_extract_path = os.path.join(TEMP_DIR, folder_name)
    final_mod_path = os.path.join(FINAL_DIR, folder_name)

    # --- DUBLETTEN-PRÜFUNG im Zielordner ---
    if os.path.exists(final_mod_path):
        print(f"\n  {Colors.YELLOW}[Info]{Colors.WHITE} '{folder_name}' existiert bereits im {FINAL_DIR}-Ordner.")
        if input(f"  Überschreiben? (j/N): ").lower() != 'j': return

    # --- CSV-PRÜFUNG ---
    is_already_in_csv = False
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            if folder_name.lower() in f.read().lower():
                is_already_in_csv = True

    # Spieltyp bestimmen
    api_dir = file_data.get('dir', '').lower()
    if "heretic" in api_dir:
        game_type, core_wad, category = 'HERETIC', "heretic.wad", "EXTRA"
    elif "hexen" in api_dir:
        game_type, core_wad, category = 'HEXEN', "hexen.wad", "EXTRA"
    else:
        game_type, core_wad, category = 'DOOM', ("doom2.wad" if "doom2" in api_dir else "doom.wad"), "PWAD"

    try:
        # 2. Download in den TEMP-Ordner
        zip_temp_path = os.path.join(TEMP_DIR, filename)
        print(f"\n  {Colors.CYAN}Lade herunter:{Colors.WHITE} {title}...")
        req = urllib.request.Request(f"https://youfailit.net/pub/idgames/{file_data.get('dir')}{filename}", 
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(zip_temp_path, 'wb') as out_file:
            out_file.write(response.read())

        # 3. Entpacken im TEMP-Ordner
        print(f"  {Colors.YELLOW}Entpacke...{Colors.WHITE}")
        with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_path)
        
        # ZIP sofort löschen
        os.remove(zip_temp_path)

        # 4. VERSCHIEBEN in den PWAD-Ordner (Wichtig!)
        print(f"  {Colors.GREEN}Verschiebe nach:{Colors.WHITE} {final_mod_path}")
        if os.path.exists(final_mod_path):
            shutil.rmtree(final_mod_path) # Alten Ordner löschen falls vorhanden
        shutil.move(temp_extract_path, final_mod_path)

        # 5. CSV-Eintrag schreiben
        if not is_already_in_csv:
            new_id = get_next_id(game_type)
            # Format: ID, Name, Core, Ordner, Mods, Extra, Kategorie, Playtime, Status
            csv_row = [str(new_id), title, core_wad, folder_name, "0", "", category, "0", "-"]
            
            with open(CSV_FILE, 'a+', newline='', encoding='utf-8-sig') as f:
                f.seek(0)
                delim = ';' if ';' in f.readline() else ','
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) != '\n': f.write('\n')
                csv.writer(f, delimiter=delim).writerow(csv_row)
            
            print(f"  {Colors.GREEN}[OK]{Colors.WHITE} Registriert als ID: {new_id}")

        input("\n  Installation fertig & install-Ordner bereinigt. ENTER...")

    except Exception as e:
        print(f"\n  {Colors.RED}[!] Fehler:{Colors.WHITE} {str(e)}")
        # Aufräumen falls was schief ging
        if os.path.exists(temp_extract_path): shutil.rmtree(temp_extract_path)
        input("  Drücke ENTER...")

    except Exception as e:
        print(f"\n  {Colors.RED}[!] Fehler:{Colors.WHITE} {str(e)}")
        if os.path.exists(zip_path): os.remove(zip_path)
        input("  Drücke ENTER...")

SETTINGS_FILE = "settings.json"

def load_settings():
    global CURRENT_ENGINE, USE_MODS, DEBUG_MODE, SHOW_STATS
    config = configparser.ConfigParser()
    
    # 1. Zuerst Defaults setzen, falls die Datei fehlt
    # (Diese Variablen müssen oben im Skript existieren!)
    
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            if 'DEFAULT' in config:
                # getboolean wandelt "True"/"False" Text in echtes True/False um
                SHOW_STATS = config['DEFAULT'].getboolean('showstats', SHOW_STATS)
                USE_MODS = config['DEFAULT'].getboolean('usemods', USE_MODS)
                DEBUG_MODE = config['DEFAULT'].getboolean('debugmode', DEBUG_MODE)
                CURRENT_ENGINE = config['DEFAULT'].get('currentengine', CURRENT_ENGINE)
        except Exception as e:
            print(f" Fehler beim Laden der config.ini: {e}")

def save_settings():
    global CURRENT_ENGINE, USE_MODS, DEBUG_MODE, SHOW_STATS
    try:
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'showstats': str(SHOW_STATS),
            'usemods': str(USE_MODS),
            'debugmode': str(DEBUG_MODE),
            'currentengine': str(CURRENT_ENGINE),
            'terminalwidth': '200'
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except Exception as e:
        print(f" Fehler beim Speichern der config.ini: {e}")

def main():
    global SHOW_STATS, USE_MODS, DEBUG_MODE, terminal_width, CURRENT_ENGINE

    initial_setup()

    update_available, latest_version = check_update()
    last_error = ""

    while True:
        blocks = load_maps()
        
        # --- Dynamische Spaltenbreite berechnen ---
        dynamic_col_width = 35 
        for block in blocks.values():
            for item in block:
                if item[0] != "EMPTY":
                    # Nutzt unsere real_len Funktion, um die echte Länge zu messen
                    length = real_len(item[0]) 
                    if length > dynamic_col_width:
                        dynamic_col_width = length
                        
        # Wir fügen 4 Leerzeichen als Puffer hinzu, damit es nicht gequetscht aussieht
        dynamic_col_width += 4 
        
        # Die Terminal-Breite berechnet sich nun aus: (4 Spalten * Spaltenbreite) + etwas Rand
        terminal_width = (dynamic_col_width * 4) + 15
        
        resize_terminal(terminal_width, 60)
        term_width = os.get_terminal_size().columns - 2
        clear_screen()
        os.system(f"title UZDoom Launcher - Python Edition")
        
        total_seconds = get_total_seconds()
        display_time = format_time(total_seconds)
        last_id = get_last_played()
        last_name = ""
        
        col1 = blocks[1]
        pwads = blocks[2]
        col4_raw = blocks[3]
        
        col2, col3 = [], []
        half = math.ceil(len(pwads) / 2)

        for i in range(half):
            col2.append(pwads[i])
            if i + half < len(pwads):
                col3.append(pwads[i + half])
            else:
                col3.append(None)
                
        for block in blocks.values():
            for item in block:
                if item and item[0] != "EMPTY" and item[1] == last_id:
                    last_name = item[3]

        # Header
        print(f"\n {Colors.CYAN}{'='*term_width}")
        print(f"      I W A D S                                   | P W A D S                                     | P W A D S                                            | H E R E T I C / H E X E N / W O L F")
        print(f" {'='*term_width}{Colors.WHITE}")

        max_idx = max(25, len(col1), len(col2), len(col3), len(col4_raw))
        
        # Mod-Zählung
        mod_count = 0
        for s in ["doom", "heretic", "hexen", "wolfenstein"]:
            p = os.path.join(BASE_DIR, "mods", s)
            if os.path.isdir(p):
                mod_count += len([d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))])

        # Zeilen ausgeben
        for i in range(max_idx):
            c1 = col1[i][0] if i < len(col1) else ""
            c2 = col2[i][0] if i < len(col2) and col2[i] else ""
            c3 = col3[i][0] if i < len(col3) and col3[i] else ""
            c4_data = col4_raw[i] if i < len(col4_raw) else None
            
            c4 = c4_data[0] if c4_data and c4_data[0] != "EMPTY" else ""
            b4 = c4_data[-1] if c4_data else 3
            
            # Padding und "Last Played" Marker
            def format_col(text, width, color, is_last):
                if not text: return " " * width
                
                # Basis-Text ohne unsichtbare Längen
                base_text = f"{text}{' [L]' if is_last else ''}"
                
                # Füllzeichen berechnen basierend auf der ECHTEN Länge
                padding_needed = width - real_len(base_text)
                if padding_needed < 0: padding_needed = 0
                
                padded = base_text + (" " * padding_needed)
                
                # JETZT ERST die Farben hinzufügen
                if is_last:
                    padded = padded.replace("[L]", f"{Colors.MAGENTA}[L]{color}")
                if " [C]" in padded:
                    padded = padded.replace(" [C]", f" {Colors.GREEN}[C]{color}")
                    
                return padded

            f1 = format_col(c1, dynamic_col_width, Colors.RED, c1.startswith(last_id + " -") if last_id else False)
            f2 = format_col(c2, dynamic_col_width, Colors.GREEN, c2.startswith(last_id + " -") if last_id else False)
            f3 = format_col(c3, dynamic_col_width, Colors.GREEN, c3.startswith(last_id + " -") if last_id else False)
            
            # Farbe für Col4
            c4_color = Colors.GREEN
            if b4 == 3: c4_color = Colors.YELLOW
            elif b4 == 4: c4_color = Colors.CYAN
            elif b4 == 5: c4_color = Colors.WHITE
            
            f4 = format_col(c4, dynamic_col_width, c4_color, c4.startswith(last_id + " -") if last_id else False)
            display4 = f"{c4_color}{f4}{Colors.WHITE}" if c4 else ""

            print(f"    {Colors.RED}{f1}{Colors.WHITE} {Colors.GRAY}|{Colors.WHITE} {Colors.GREEN}{f2}{Colors.WHITE} {Colors.GRAY}|{Colors.WHITE} {Colors.GREEN}{f3}{Colors.WHITE} {Colors.GRAY}| {display4}")

        total_maps = len(col1) + len(pwads) + len([x for x in col4_raw if x[0] != "EMPTY"])
        upd_marker = f" {Colors.RED}[U] Update verfügbar{Colors.WHITE}" if update_available else ""

        print(f"\n {Colors.CYAN}{'='*term_width}{Colors.WHITE}")
        
        # Schalter-Status vorbereiten
        m_on = f"{Colors.GREEN}ON{Colors.WHITE}" if USE_MODS else f"{Colors.RED}OFF{Colors.WHITE}"
        s_on = f"{Colors.GREEN}ON{Colors.WHITE}" if SHOW_STATS else f"{Colors.RED}OFF{Colors.WHITE}"
        d_on = f"{Colors.GREEN}ON{Colors.WHITE}" if DEBUG_MODE else f"{Colors.RED}OFF{Colors.WHITE}"

        # Linker Teil: Statistiken & Engine (Fest verankert)
        len_extra = len([x for x in col4_raw if x[0] != 'EMPTY'])
        st_left = (f"    KARTEN: {Colors.GREEN}Gesamt: {total_maps}{Colors.WHITE} | "
                   f"{Colors.RED}IWAD: {len(col1)}{Colors.WHITE} | "
                   f"{Colors.GREEN}PWAD: {len(pwads)}{Colors.WHITE} | "
                   f"{Colors.CYAN}Heretic / Hexen: {len_extra}{Colors.WHITE}  "
                   f"{Colors.GRAY}│{Colors.WHITE}  {Colors.YELLOW}ZEIT: {display_time}{Colors.WHITE}  "
                   f"{Colors.GRAY}│{Colors.WHITE}  MODS: {Colors.YELLOW}{mod_count}{Colors.WHITE}  "
                   f"{Colors.GRAY}│{Colors.WHITE}  {Colors.BLUE}UZDoom {CUR_VERSION}{upd_marker}{Colors.WHITE}")
        
        # Rechter Teil: Deine neuen langen Beschreibungen
        # Dieser Teil "wächst" jetzt nach links
        st_right = (f" {Colors.YELLOW}[/M] Mod-Menu {m_on}  "
                    f"[/S] Statistiken {s_on}  "
                    f"[/D] DebugMenu {d_on}{Colors.WHITE}    ")

        # --- PRÄZISE BERECHNUNG DER RECHTSBÜNDIGKEIT ---
        # Wir messen die tatsächliche Breite der Buchstaben ohne die unsichtbaren Farbcodes
        raw_l = f"    KARTEN: Gesamt: {total_maps} | IWAD: {len(col1)} | PWAD: {len(pwads)} | Heretic / Hexen: {len_extra}  │  ZEIT: {display_time}  │  MODS: {mod_count}  │  UZDoom {CUR_VERSION}{' [U]' if update_available else ''}"
        raw_r = f" [/M] Mod-Menu {'ON' if USE_MODS else 'OFF'}  [/S] Statistiken {'ON' if SHOW_STATS else 'OFF'}  [/D] DebugMenu {'ON' if DEBUG_MODE else 'OFF'}    "
        
        # Das Padding ist der restliche Platz. Wenn es eng wird, schrumpft dieser Wert auf 1.
        pad_stat = term_width - len(raw_l) - len(raw_r)
        
        # Falls das Fenster ZU schmal ist, kürzen wir die linke Seite leicht ab (Notlösung)
        if pad_stat < 1: 
            pad_stat = 1
        
        # Ausgabe: Linksbündiger Teil + dynamischer Leerraum + Rechtsbündiger Teil
        print(f"{st_left}{' ' * pad_stat}{st_right}")
        print(f" {Colors.CYAN}{'='*term_width}{Colors.WHITE}")
        print()

        # --- BEFEHLSZEILE (Ganz unten) ---
        if last_id:
            cmd_line = f"    {Colors.YELLOW}[0] Beenden  [?] Zufall  [R] Reset  [I] Installer  [S] Suche{Colors.WHITE}    {Colors.CYAN}[E] Engine: {CURRENT_ENGINE}{Colors.WHITE}" + (f"    {Colors.YELLOW}Zuletzt gespielt: {Colors.CYAN}{last_id} - {last_name} {Colors.YELLOW}[L]{Colors.WHITE}" if last_id else "")
        
        print(cmd_line)
        print()
        
        if last_error:
            print(f"    {Colors.RED}Fehler: ID '{Colors.YELLOW}{last_error}{Colors.RED}' ist ungültig.{Colors.WHITE}")
            last_error = ""
        else:
            print()

        choice = input(f"    {Colors.YELLOW}Gib die {Colors.YELLOW}ID{Colors.CYAN} {Colors.YELLOW}ein ODER ENTER für letzte Karte - {Colors.MAGENTA}{last_id}{Colors.YELLOW}): {Colors.WHITE}").strip().lower()

        if choice == 'e':
            select_engine()
            save_settings()
            continue
        if choice == '0':
            sys.exit(0)

        # --- DIESER BLOCK MUSS VOR ALLEM ANDEREN KOMMEN ---
        if choice.endswith('c') and len(choice) > 1:
            target_id = choice[:-1].upper()
            if toggle_map_clear(target_id):
                # Die while-Schleife startet von vorne und lädt alles automatisch neu!
                continue
            else:
                last_error = f"ID '{target_id}' nicht gefunden!"
                continue

        if choice == '/m':
            USE_MODS = not USE_MODS
            save_settings()
            continue
        if choice == '/s':
            SHOW_STATS = not SHOW_STATS
            save_settings()
            continue
        if choice == '/d':
            DEBUG_MODE = not DEBUG_MODE
            save_settings()
            continue
            
        if choice == 'r':
            print(f"    {Colors.YELLOW}Script wird neu gestartet...{Colors.WHITE}")
            subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "doom.py")], creationflags=subprocess.CREATE_NEW_CONSOLE)
            sys.exit(0)
            # --- ZUFALLSKARTE ---
        if choice == '?':
            all_valid_maps = []
            for block in blocks.values():
                for item in block:
                    if item and item[0] != "EMPTY":
                        all_valid_maps.append(item)
            
            if all_valid_maps:
                selected_map = random.choice(all_valid_maps)
                print(f"\n    {Colors.MAGENTA}Zufallsauswahl: {Colors.CYAN}{selected_map[1]} - {selected_map[3]}{Colors.WHITE}")
                time.sleep(2)
                launch_game(selected_map)
            else:
                last_error = "Keine Karten für Zufallsauswahl gefunden!"
            continue
        if choice == 'i':
            run_installer()
            continue
        if choice == 'e':
            select_engine()
        if choice == 's':
            search_doomworld()
            continue
        if choice == '0': sys.exit(0)    
        if choice == 'l' and last_id:
            choice = last_id
        if choice == 'u' and update_available:
            os.system('start "" "https://github.com/m886/UzDoom/releases/latest"')
            continue

        selected_map = None
        for block in blocks.values():
            for item in block:
                if item and item[0] != "EMPTY" and item[1].lower() == choice:
                    selected_map = item
                    break
            if selected_map: break
            
        if not selected_map:
            last_error = choice
            continue

        launch_game(selected_map)

def launch_game(map_data):

    resize_terminal(terminal_width, 60) 
    clear_screen()
    
    map_id = map_data[0]
    mapname = map_data[2]
    core = map_data[3]
    pwad_folder = map_data[4]

    _, map_id, core, mapname, remaining, _ = map_data
    core = core.replace(" ", "")
    display_core = core
    
    sub_folder = "doom"
    if core.lower() == "heretic.wad": sub_folder = "heretic"
    elif core.lower() == "hexen.wad": sub_folder = "hexen"

    file_params = []
    extra_params = []
    mod_flag = False
    auto_mod = None
    
    i = 0
    while i < len(remaining):
        item = remaining[i].strip()
        if not item:
            i += 1
            continue
            
        if item == "1": mod_flag = True
        elif item == "0": mod_flag = False
        elif item.startswith("-") or item.startswith("+"):
            extra_params.append(item)
            if item.lower() in ["-config", "-warp", "-skill", "+map"] and i + 1 < len(remaining):
                if item.lower() == "-config":
                    extra_params.append(os.path.join(BASE_DIR, remaining[i+1].strip()))
                else:
                    extra_params.append(remaining[i+1].strip())
                i += 1
        else:
            target_path = None
            if os.path.exists(os.path.join(PWAD_DIR, item)): target_path = os.path.join(PWAD_DIR, item)
            elif os.path.exists(os.path.join(IWAD_DIR, item)): target_path = os.path.join(IWAD_DIR, item)
            elif os.path.exists(os.path.join(PWAD_DIR, item + ".wad")): target_path = os.path.join(PWAD_DIR, item + ".wad")
            
            if target_path:
                if os.path.isdir(target_path):
                    valid_exts = (".wad", ".pk3", ".pk7", ".zip")
                    for f in os.listdir(target_path):
                        # FIX: lower() hinzugefügt und Tuple statt verschachtelter Schleife
                        if f.lower().endswith(valid_exts):  
                            file_params.extend(["-file", os.path.join(target_path, f)])
                else:
                    file_params.extend(["-file", target_path])
            else:
                is_system = item.lower() in ["doom", "heretic", "hexen"]
                if not is_system:
                    if os.path.isdir(os.path.join(BASE_DIR, "mods", sub_folder, item)):
                        auto_mod = os.path.join(sub_folder, item)
                    elif os.path.isdir(os.path.join(BASE_DIR, "mods", item)):
                        auto_mod = item
        i += 1

    mod_name = "Vanilla"
    mod_params = []
    
    if auto_mod:
        mod_name = f"{os.path.basename(auto_mod)} (Auto)"
        mod_path = os.path.join(BASE_DIR, "mods", auto_mod)
        valid_exts = (".pk3", ".wad", ".zip")
        for f in os.listdir(mod_path):
            if f.lower().endswith(valid_exts): # FIX: lower()
                mod_params.extend(["-file", os.path.join(mod_path, f)])
    elif not mod_flag and USE_MODS:
        mod_dir = os.path.join(BASE_DIR, "mods", sub_folder)
        if os.path.exists(mod_dir):
            available_mods = [d for d in os.listdir(mod_dir) if os.path.isdir(os.path.join(mod_dir, d))]
            if available_mods:
                while True:
                    resize_terminal(terminal_width, 60)
                    clear_screen()
                    print(f"\n {Colors.CYAN}MOD-AUSWAHL (Mehrfachwahl möglich, z.B. 1 2 5):{Colors.WHITE}")
                    print(f" {'-'*47}")
                    print(f" SPIEL : {Colors.GREEN}{display_core}{Colors.WHITE}")
                    print(f" KARTE : {Colors.GREEN}{mapname}{Colors.WHITE}")
                    print(f" {'-'*47}\n")
                    
                    for idx, m in enumerate(available_mods, 1):
                        print(f"       {Colors.CYAN}{idx}.{Colors.WHITE} {m}")
                    print(f"\n       {Colors.CYAN}0.{Colors.WHITE} Keine Mod (Vanilla)")
                    print(f"{'-'*48}\n")
                    
                    m_choice = input(f"       {Colors.YELLOW}DEINE WAHL: {Colors.WHITE}").strip()
                    
                    if not m_choice or m_choice == "0":
                        break
                        
                    choices = m_choice.split()
                    valid = True
                    selected_mods = []
                    for c in choices:
                        if c.isdigit() and 1 <= int(c) <= len(available_mods):
                            selected_mods.append(available_mods[int(c)-1])
                        else:
                            valid = False
                    
                    if valid:
                        mod_name = ", ".join(selected_mods)
                        for sm in selected_mods:
                            mp = os.path.join(mod_dir, sm)
                            valid_exts = (".pk3", ".wad", ".zip")
                            for f in os.listdir(mp):
                                if f.lower().endswith(valid_exts): # FIX: lower()
                                    mod_params.extend(["-file", os.path.join(mp, f)])
                        break
                    else:
                        print(f"          {Colors.RED}Ungültige Auswahl!{Colors.WHITE}")
                        time.sleep(1.5)
    elif mod_flag:
        mod_name = "Vanilla (Deaktiviert)"

    clear_screen()
    resize_terminal(terminal_width, 60)
    print(f"\n {Colors.GREEN}S T A R T E   E N G I N E{Colors.WHITE}")
    print(f" {'-'*28}")
    print(f" KARTE : {Colors.CYAN}{mapname}{Colors.WHITE}")
    print(f" IWAD  : {Colors.CYAN}{display_core}{Colors.WHITE}")
    print(f" MOD   : {Colors.CYAN}{mod_name}{Colors.WHITE}")
    print(f" {'-'*28}\n")
    print(f" {Colors.YELLOW}Spiel läuft... Bitte warten.{Colors.WHITE}")

    with open(os.path.join(BASE_DIR, "last_played.txt"), 'w') as f:
        f.write(map_id)

    log_file = os.path.join(BASE_DIR, "logfile.txt")
    start_time = datetime.now()
    
 # --- NEU: Dynamische Engine-Wahl (Diese Zeile muss eingerückt sein!) ---
    engine_exe = get_engine_path() 

    # Befehl zusammenbauen
    cmd = [engine_exe, "+logfile", "logfile.txt", "-iwad", os.path.join(IWAD_DIR, core)] + file_params + mod_params + extra_params

    # --- DEBUG SCHALTER ---
    if DEBUG_MODE:
        print(f"\n          {Colors.MAGENTA}=== DEBUG: VOLLSTÄNDIGER BEFEHL ==={Colors.WHITE}")
        debug_str = " ".join(cmd)
        print(f"          {Colors.CYAN}{debug_str}{Colors.WHITE}")
        print(f"          {Colors.MAGENTA}==================================={Colors.WHITE}\n")
        debug_choice = input(f" {Colors.YELLOW}Drücke ENTER zum Starten oder tippe '0' zum Abbrechen: {Colors.WHITE}").strip()
        if debug_choice == '0':
            print(f"          {Colors.RED}Start vom Benutzer abgebrochen.{Colors.WHITE}")
            time.sleep(1.5)
            return

    # Sicherheitsprüfung
    if not os.path.exists(engine_exe):
        print(f"\n {Colors.RED}Fehler: Engine '{CURRENT_ENGINE}' nicht gefunden unter:{Colors.WHITE}")
        print(f" {Colors.YELLOW}{engine_exe}{Colors.WHITE}")
        print(f"\n {Colors.GRAY}Stelle sicher, dass die .exe im Ordner 'engines' liegt.{Colors.WHITE}")
        time.sleep(4)
        return 

    # Das Spiel starten
    subprocess.run(cmd)

    # Zeitmessung und Statistik (Muss exakt unter subprocess stehen!)
    end_time = datetime.now()
    session_seconds = int((end_time - start_time).total_seconds())
    
    total_time_seconds = get_total_seconds() + session_seconds
    save_total_seconds(total_time_seconds)

    m, s = divmod(session_seconds, 60)
    
    if m > 0:
        update_csv_playtime(map_id, m)
        
    if SHOW_STATS:
        analyze_session(log_file, map_id, mapname, session_seconds)

def analyze_session(log_file, map_id, mapname, session_seconds):
    print(f"\n{Colors.GREEN}    Spiel beendet. Analysiere Sitzung... {Colors.WHITE}")
    stats = {'health': 0, 'armor': 0, 'ammo': 0, 'key': 0, 'powerup': 0}
    weapons_found = set()
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_lower = line.lower()
                
                # --- HEILUNG & RÜSTUNG ---
                if any(x in line_lower for x in ["heilung", "health", "bonus", "stimpack", "medikit", "mega", "supercharge", "berserk"]): stats['health'] += 1
                if any(x in line_lower for x in ["panzer", "armor", "mega"]): stats['armor'] += 1
                
                # --- MUNITION ---
                if any(x in line_lower for x in ["patronen", "magazin", "rakete", "zelle", "kiste", "clip", "shell", "rocket", "cell", "ammo", "box", "rucksack", "backpack"]): stats['ammo'] += 1
                
                # --- SCHLÜSSEL ---
                if any(x in line_lower for x in ["schlüssel", "karte", "keycard", "key", "skull"]): stats['key'] += 1
                
                # --- SPEZIAL ---
                if any(x in line_lower for x in ["suit", "visor", "shielding", "invulnerability", "unverwundbarkeit", "invisibility", "unsichtbarkeit", "computer", "strahlenschutz", "infrarot"]): stats['powerup'] += 1
                
                # --- WAFFEN ---
                for w in ["pistole", "pistol", "schrotflinte", "shotgun", "gewehr", "chaingun", "maschinengewehr", "kettensäge", "chainsaw", "saw", "raketenwerfer", "launcher", "plasma", "bfg", "mg-42", "railgun"]:
                    # Wenn das Wort im Text vorkommt, speichere es mit großem Anfangsbuchstaben
                    if w in line_lower: 
                        weapons_found.add(w.capitalize())

    clear_screen()
    resize_terminal(terminal_width, 60)
    print(f"{Colors.MAGENTA}========================================================{Colors.WHITE}")
    print(f"    S E S S I O N   Z U S A M M E N F A S S U N G")
    print(f"{Colors.MAGENTA}========================================================{Colors.WHITE}\n")
    print(f"    Projekt: {map_id} - {Colors.YELLOW}{mapname}{Colors.WHITE}")
    
    m, s = divmod(session_seconds, 60)
    print(f"    Dauer:   {Colors.YELLOW}{m} Min. {s} Sek.{Colors.WHITE}\n")
    
        
    print(f"    Gegenstände:")
    print(f"    - Heilung:  {Colors.GREEN}{stats['health']}{Colors.WHITE} | Rüstung: {Colors.CYAN}{stats['armor']}{Colors.WHITE}")
    print(f"    - Munition: {Colors.YELLOW}{stats['ammo']}{Colors.WHITE} | Schlüssel: {Colors.BLUE}{stats['key']}{Colors.WHITE}")
    print(f"    - Spezial:  {Colors.MAGENTA}{stats['powerup']}{Colors.WHITE}")
    if weapons_found: 
        print(f"\n    Waffen:     {Colors.MAGENTA}{', '.join(weapons_found)}{Colors.WHITE}")
    print(f"\n{Colors.MAGENTA}========================================================{Colors.WHITE}")
    
    print(f"\n    {Colors.YELLOW}Drücke eine beliebige Taste, um zum Menü zurückzukehren...{Colors.WHITE}")
    if os.name == 'nt':
        os.system('pause >nul')
    else:
        input()

if __name__ == "__main__":
    load_settings()
    try:
        main()
    except Exception as e:
        # Falls das Programm abstürzt, wird der Fehler hier ausgegeben
        print("\n" + "="*50)
        print(f"ABSTURZ-BERICHT:")
        print("="*50)
        import traceback
        traceback.print_exc() # Zeigt genau, in welcher Zeile es knallt
        print("="*50)
        input("\nDrücke ENTER, um dieses Fenster zu schließen...")