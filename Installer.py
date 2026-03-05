import os
import shutil
import csv
import re
import zipfile
import subprocess

# --- EINSTELLUNGEN & PFADE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.join(BASE_DIR, "Install")
PWAD_DIR = os.path.join(BASE_DIR, "pwad")
CSV_FILE = os.path.join(BASE_DIR, "maps.csv")

# --- FARBEN ---
os.system('') 
class Colors:
    RED, GREEN, YELLOW, CYAN, MAGENTA, WHITE = '\033[91m', '\033[92m', '\033[93m', '\033[96m', '\033[95m', '\033[0m'

def get_next_id(prefix):
    """Findet die nächste freie ID anhand des Präfixes (z.B. 'H', 'HX', 'D')"""
    if not os.path.exists(CSV_FILE): 
        return f"{prefix}1"
    
    ids = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        # Wir nutzen DictReader, um robuster zu sein
        reader = csv.DictReader(f)
        for row in reader:
            entry_id = row.get('ID', '').strip().upper()
            if entry_id.startswith(prefix):
                # Extrahiere nur die Zahl nach dem Präfix
                num_part = entry_id[len(prefix):]
                if num_part.isdigit():
                    ids.append(int(num_part))
                    
    return f"{prefix}{max(ids) + 1}" if ids else f"{prefix}1"

def extract_archive(filepath, target_dir):
    """Entpackt ZIP, RAR und 7Z Dateien"""
    ext = filepath.lower().rsplit('.', 1)[-1]
    
    if ext == 'zip':
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            return True
        except Exception as e:
            print(f"   {Colors.RED}Fehler beim Entpacken der ZIP: {e}{Colors.WHITE}")
            return False
            
    elif ext in ['rar', '7z']:
        try:
            subprocess.run(["7z", "x", filepath, f"-o{target_dir}", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except FileNotFoundError:
            print(f"   {Colors.RED}Achtung: '7z' Befehl nicht gefunden!{Colors.WHITE}")
            print(f"   {Colors.YELLOW}Um .rar und .7z zu entpacken, muss 7-Zip in den Windows-Umgebungsvariablen eingetragen sein.{Colors.WHITE}")
            return False
        except subprocess.CalledProcessError:
            print(f"   {Colors.RED}Fehler beim Entpacken des Archivs mit 7-Zip!{Colors.WHITE}")
            return False
    return False

def prepare_install_directory():
    """Scannt nach Archiven und losen WADs und bereitet sie in Ordnern vor"""
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
        return False

    items = os.listdir(INSTALL_DIR)
    if not items:
        return False

    for item in items:
        item_path = os.path.join(INSTALL_DIR, item)
        
        if os.path.isfile(item_path):
            ext = item.lower().rsplit('.', 1)[-1] if '.' in item else ""
            folder_name = item.rsplit('.', 1)[0]
            target_folder = os.path.join(INSTALL_DIR, folder_name)
            
            # ARCHIVE ENTPACKEN
            if ext in ['zip', 'rar', '7z']:
                print(f" {Colors.MAGENTA}Entpacke Archiv:{Colors.WHITE} {item}...")
                os.makedirs(target_folder, exist_ok=True)
                
                if extract_archive(item_path, target_folder):
                    os.remove(item_path) # Löscht das Archiv nach erfolgreichem Entpacken
                    
                    # FIX FÜR UNNÖTIGE UNTERORDNER (Behältst du bei, sehr gut!)
                    contents = os.listdir(target_folder)
                    if len(contents) == 1:
                        nested_dir = os.path.join(target_folder, contents[0])
                        if os.path.isdir(nested_dir):
                            for f in os.listdir(nested_dir):
                                shutil.move(os.path.join(nested_dir, f), target_folder)
                            os.rmdir(nested_dir)
                else:
                    if not os.listdir(target_folder):
                        os.rmdir(target_folder)
            
            # LOSE KARTEN VERPACKEN
            elif ext in ['wad', 'pk3', 'pk7']:
                print(f" {Colors.MAGENTA}Verpacke lose Datei:{Colors.WHITE} {item}...")
                os.makedirs(target_folder, exist_ok=True)
                shutil.move(item_path, os.path.join(target_folder, item))

    return True

def install_process():
    print(f"\n {Colors.CYAN}=== UZDOOM MAP-INSTALLER ==={Colors.WHITE}\n")
    
    # Stelle sicher, dass der PWAD Ordner existiert
    if not os.path.exists(PWAD_DIR):
        os.makedirs(PWAD_DIR)

    prepare_install_directory()
    
    folders = [d for d in os.listdir(INSTALL_DIR) if os.path.isdir(os.path.join(INSTALL_DIR, d))]
    
    if not folders:
        print(f" {Colors.YELLOW}Keine neuen Karten im '{INSTALL_DIR}' Verzeichnis gefunden.{Colors.WHITE}")
        print(f" {Colors.GRAY}Tipp: Lege ZIP, RAR, 7Z oder .WAD Dateien in den Ordner '{INSTALL_DIR}'.{Colors.WHITE}")
        return

    installed_count = 0

    for folder in folders:
        full_path = os.path.join(INSTALL_DIR, folder)
        print(f" {Colors.CYAN}Prüfe Ordner:{Colors.WHITE} {folder}")
        
        m_name = folder.replace("_", " ") 
        m_core = "doom2.wad" # Standard-Fallback
        
        # Lese Textdateien für Infos
        txt_files = [f for f in os.listdir(full_path) if f.lower().endswith(".txt")]
        if txt_files:
            with open(os.path.join(full_path, txt_files[0]), 'r', encoding='utf-8', errors='ignore') as txt:
                content = txt.read()
                
                # Suche nach dem Titel
                match = re.search(r"title\s*:\s*(.*)", content, re.IGNORECASE)
                if match: 
                    m_name = match.group(1).strip()
                
                # Schlauere Erkennung der benötigten IWAD
                content_lower = content.lower()
                if "heretic" in content_lower: m_core = "heretic.wad"
                elif "hexen" in content_lower: m_core = "hexen.wad"
                elif "plutonia" in content_lower: m_core = "plutonia.wad"
                elif "tnt" in content_lower: m_core = "tnt.wad"
                elif "doom.wad" in content_lower or "ultimate doom" in content_lower: m_core = "doom.wad"

        # Kategorie und Präfix festlegen
        if "heretic" in m_core:
            kategorie = "EXTRA"
            prefix = "H"
        elif "hexen" in m_core:
            kategorie = "EXTRA"
            prefix = "HX"
        else:
            kategorie = "PWAD"
            prefix = "D" # Standard-Doom erhält das D-Präfix

        target_name = folder.replace(" ", "_")
        target_path = os.path.join(PWAD_DIR, target_name)
        
        if os.path.exists(target_path):
            print(f"   {Colors.RED}-> Fehler: Eine Modifikation mit dem Ordnernamen '{target_name}' existiert bereits!{Colors.WHITE}")
            continue

        # Verschiebe Ordner in den PWAD-Ordner
        shutil.move(full_path, target_path)
        
        # ID generieren und in die CSV eintragen
        new_id = get_next_id(prefix)
        write_header = not os.path.exists(CSV_FILE)
        
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            # NEU: Playtime und LastPlayed hinzugefügt
            fieldnames = ["ID", "Name", "IWAD", "Ordner", "MOD", "ARGS", "Kategorie", "Playtime", "LastPlayed"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if write_header:
                writer.writeheader()
                
            writer.writerow({
                "ID": new_id,
                "Name": m_name,
                "IWAD": m_core,
                "Ordner": target_name,
                "MOD": "0",
                "ARGS": "",
                "Kategorie": kategorie,
                "Playtime": "0",     # Startwert für Spielzeit
                "LastPlayed": "-"    # Startwert für Zuletzt gespielt
            })
            
        print(f"   {Colors.GREEN}-> Erfolgreich installiert als ID {Colors.YELLOW}{new_id}{Colors.GREEN} (Basis: {m_core}){Colors.WHITE}")
        installed_count += 1

    if installed_count > 0:
        print(f"\n {Colors.CYAN}Installation erfolgreich abgeschlossen! ({installed_count} Karten hinzugefügt){Colors.WHITE}")

if __name__ == "__main__":
    install_process()
    input(f"\n {Colors.YELLOW}Drücke ENTER zum Beenden...{Colors.WHITE}")