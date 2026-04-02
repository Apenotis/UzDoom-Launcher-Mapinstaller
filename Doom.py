# ##############################################################################
# #                                                                            #
# #   ██████╗  ███╗   ███╗ ███████╗                                            #
# #   ██╔══██╗ ████╗ ████║ ██╔════╝                                            #
# #   ██║  ██║ ██╔████╔██║ ███████╗                                            #
# #   ██║  ██║ ██║╚██╔╝██║ ╚════██║                                            #
# #   ██████╔╝ ██║ ╚═╝ ██║ ███████║                                            #
# #   ╚═════╝  ╚═╝     ╚═╝ ╚══════╝                                            #
# #                                                                            #
# #   --- DOOM MANAGEMENT SYSTEM (D.M.S.) ---                                  #
# #                                                                            #
# #   Author:      [Apenotis]                                                  #
# #   Version:     3.0 (April 2026)                                            #
# #   Engine:      UzDoom / GZDoom / Zandronum Support                         #
# #   Description: Fortschrittlicher Manager & Launcher für Retro-Shooter      #
# #   Status:      Linter Verified & Black Formatted                           #
# ##############################################################################

import configparser
import csv
import ctypes
import glob
import json
import math
import msvcrt
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
import traceback
import urllib.request
import zipfile
from datetime import datetime

# ============================================================================
# KONFIGURATION & KONSTANTEN
# ============================================================================

APP_VERSION = "3.0"
UPDATE_URL = "https://raw.githubusercontent.com/Apenotis/UzDoom-Launcher-Mapinstaller/main/Doom.py"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.ini")
CSV_FILE = os.path.join(BASE_DIR, "maps.csv")
IWAD_DIR = os.path.join(BASE_DIR, "iwad")
PWAD_DIR = os.path.join(BASE_DIR, "pwad")
UZ_DIR = os.path.join(BASE_DIR, "UzDoom")
UZ_EXE = os.path.join(UZ_DIR, "uzdoom.exe")

SUPPORTED_ENGINES = ["uzdoom", "gzdoom", "zandronum", "zdoom", "lzdoom"]
DEFAULT_ENGINE = "uzdoom"

# Globale Variablen
CURRENT_ENGINE = DEFAULT_ENGINE
USE_MODS = False
SHOW_STATS = False
DEBUG_MODE = False
TERMINAL_WIDTH = 165

# ============================================================================
# FARBEN (ANSI)
# ============================================================================


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[0m"
    GRAY = "\033[90m"


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================


def clear_screen():
    """Löscht den Bildschirm"""
    os.system("cls" if os.name == "nt" else "clear")


def resize_terminal(cols, lines):
    """Passt die Terminalgröße an (Ignoriert von VS Code und modernem Windows Terminal)"""
    try:
        if os.name == "nt":
            # Für die klassische Windows cmd.exe
            os.system(f"mode con: cols={cols} lines={lines}")

        # ANSI-Escape-Sequenz für Linux/Mac und kompatible Terminals
        sys.stdout.write(f"\x1b[8;{lines};{cols}t")
        sys.stdout.flush()
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        # Falls das Terminal die Änderung blockiert, einfach lautlos weiterlaufen
        pass


def real_len(text):
    """Berechnet die tatsächliche Länge eines Strings ohne ANSI-Codes"""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return len(ansi_escape.sub("", text))


def format_time(total_seconds):
    """Formatiert Sekunden als HH:MM:SS"""
    h = math.floor(total_seconds / 3600)
    m = math.floor((total_seconds % 3600) / 60)
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


# ============================================================================
# SPIELZEIT-TRACKING (alles in config.ini)
# ============================================================================


def get_total_seconds():
    """Liest die Gesamtspielzeit aus der config.ini"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding="utf-8-sig")
            return config.getint("STATS", "total_seconds", fallback=0)
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass
    return 0


def save_total_seconds(seconds):
    """Speichert die Gesamtspielzeit in der config.ini"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding="utf-8-sig")
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass

    if "STATS" not in config:
        config["STATS"] = {}

    config["STATS"]["total_seconds"] = str(seconds)

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8-sig") as f:
            config.write(f)
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        print(
            f"  {Colors.RED}[!] Fehler beim Speichern der Spielzeit: {e}{Colors.WHITE}"
        )


def get_last_played_id_from_csv():
    """Ermittelt die zuletzt gespielte Map-ID aus der CSV"""
    if not os.path.exists(CSV_FILE):
        return ""

    last_id, latest_date = "", None

    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lp_str = row.get("LastPlayed", "").strip()
                if not lp_str or lp_str == "-":
                    continue

                curr_date = None
                try:
                    curr_date = datetime.strptime(lp_str, "%d.%m.%Y %H:%M")
                except ValueError:
                    try:
                        curr_date = datetime.strptime(lp_str, "%d.%m.%Y")
                    except ValueError:
                        print(
                            f"Ungültiges Datumsformat in ID {row.get('ID')}: {lp_str}"
                        )

                # Schritt 3: Wenn wir ein Datum gefunden haben, vergleichen
                if curr_date:
                    if latest_date is None or curr_date > latest_date:
                        latest_date = curr_date
                        last_id = row.get("ID", "")

    except Exception as e:
        print(f"Fehler beim Lesen der CSV: {e}")

    return last_id


def update_csv_playtime(map_id, minutes, last_played="-"):
    """Aktualisiert Spielzeit und das Datum des letzten Spiels in der CSV"""
    if not os.path.exists(CSV_FILE):
        return

    rows = []
    updated = False
    fieldnames = []

    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if str(row["ID"]) == str(map_id):
                    # Playtime sicher addieren
                    try:
                        old_time = int(
                            row.get("Playtime") or 0
                        )  # 'or 0' fängt None/leer ab
                    except Exception:
                        old_time = 0

                    row["Playtime"] = str(old_time + minutes)
                    row["LastPlayed"] = last_played
                    updated = True
                rows.append(row)

        if updated:
            with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    except Exception as e:
        print(f"Fehler bei CSV-Update: {e}")


# ============================================================================
# KONFIGURATION
# ============================================================================


def load_settings():
    global CURRENT_ENGINE, USE_MODS, DEBUG_MODE, SHOW_STATS, TERMINAL_WIDTH

    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding="utf-8-sig")

            # ENGINE
            if "ENGINE" in config:
                CURRENT_ENGINE = config["ENGINE"].get("current", DEFAULT_ENGINE)

            # OPTIONS
            if "OPTIONS" in config:
                SHOW_STATS = config["OPTIONS"].getboolean("showstats", SHOW_STATS)
                USE_MODS = config["OPTIONS"].getboolean("usemods", USE_MODS)
                DEBUG_MODE = config["OPTIONS"].getboolean("debugmode", DEBUG_MODE)
                TERMINAL_WIDTH = config["OPTIONS"].getint(
                    "terminalwidth", TERMINAL_WIDTH
                )
        except Exception as e:
            print(f" Fehler beim Laden der config.ini: {e}")


def save_settings():
    """Speichert alle Einstellungen in die config.ini"""
    config = configparser.ConfigParser()

    # Bestehende Config laden (falls vorhanden)
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding="utf-8-sig")
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass

    # STATS Sektion (erhalten, nicht überschreiben)
    if "STATS" not in config:
        config["STATS"] = {}

    # ENGINE Sektion
    if "ENGINE" not in config:
        config["ENGINE"] = {}
    config["ENGINE"]["current"] = CURRENT_ENGINE

    # OPTIONS Sektion
    if "OPTIONS" not in config:
        config["OPTIONS"] = {}
    config["OPTIONS"]["showstats"] = str(SHOW_STATS)
    config["OPTIONS"]["usemods"] = str(USE_MODS)
    config["OPTIONS"]["debugmode"] = str(DEBUG_MODE)
    config["OPTIONS"]["terminalwidth"] = str(TERMINAL_WIDTH)

    # UPDATE Sektion
    if "UPDATE" not in config:
        config["UPDATE"] = {}
    config["UPDATE"]["next_check"] = ""

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8-sig") as configfile:
            config.write(configfile)
    except Exception as e:
        print(f" Fehler beim Speichern der config.ini: {e}")


# ============================================================================
# ENGINE-MANAGEMENT
# ============================================================================


def get_engine_path():
    """Gibt den Pfad zur aktuellen Engine zurück"""
    exe_name = f"{CURRENT_ENGINE}.exe"
    path_in_folder = os.path.join(CURRENT_ENGINE, exe_name)

    if os.path.exists(path_in_folder):
        return path_in_folder
    if os.path.exists(exe_name):
        return exe_name
    return exe_name


def get_engine_version(engine_path):
    """Ermittelt die Version der Engine (Windows)"""
    if not engine_path or not os.path.exists(engine_path):
        return "N/A"

    try:
        filename = os.path.abspath(engine_path)
        size = ctypes.windll.version.GetFileVersionInfoSizeW(filename, None)
        if size <= 0:
            return "Bereit"

        res = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(filename, None, size, res)

        fixed_info = ctypes.POINTER(ctypes.c_uint16)()
        fixed_size = ctypes.c_uint()

        if ctypes.windll.version.VerQueryValueW(
            res, "\\", ctypes.byref(fixed_info), ctypes.byref(fixed_size)
        ):
            if fixed_size.value:
                major = fixed_info[9]
                minor = fixed_info[8]
                build = fixed_info[11]
                return f"{major}.{minor}.{build}"

        mtime = os.path.getmtime(engine_path)
        return datetime.fromtimestamp(mtime).strftime("%d.%m.%y")
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        return "Aktiv"


def download_uzdoom():
    """Lädt UZDoom von GitHub herunter"""
    print(
        f"\n  {Colors.MAGENTA}>>> Lade UZDoom Engine herunter... Bitte warten. <<<{Colors.WHITE}"
    )
    print(
        f"  {Colors.GRAY}(Suche automatisch nach der neuesten Version...){Colors.WHITE}"
    )

    api_url = "https://api.github.com/repos/UZDoom/UZDoom/releases/latest"
    download_url = ""

    try:
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", "Python-Launcher")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if "windows" in name and name.endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break
    except Exception as e:
        print(
            f"  {Colors.RED}[!] Verbindung zu GitHub fehlgeschlagen: {e}{Colors.WHITE}"
        )
        return

    if not download_url:
        print(
            f"  {Colors.RED}[!] Keine Windows-Version im aktuellen Release gefunden.{Colors.WHITE}"
        )
        return

    print(f"  {Colors.GRAY}(Lade Datei: {download_url.split('/')[-1]}){Colors.WHITE}")

    zip_path = os.path.join(BASE_DIR, "uzdoom_temp.zip")

    try:
        urllib.request.urlretrieve(download_url, zip_path)
        print(
            f"  {Colors.GREEN}[+]{Colors.WHITE} Download abgeschlossen. Entpacke Dateien..."
        )

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(UZ_DIR)

        os.remove(zip_path)
        print(
            f"  {Colors.GREEN}[+]{Colors.WHITE} UZDoom wurde erfolgreich installiert!"
        )
    except Exception as e:
        print(
            f"  {Colors.RED}[!] Fehler beim Herunterladen oder Entpacken: {e}{Colors.WHITE}"
        )


def select_engine():
    """Menü zur Engine-Auswahl"""
    global CURRENT_ENGINE

    while True:
        clear_screen()
        print(f"\n  {Colors.MAGENTA}--- ENGINE-AUSWAHL ---{Colors.WHITE}")
        print(f"  Aktuell: {Colors.CYAN}{CURRENT_ENGINE}{Colors.WHITE}\n")

        found = []
        for i, eng in enumerate(SUPPORTED_ENGINES):
            exe_n = f"{eng}.exe"
            path_check = os.path.join(eng, exe_n)
            is_ready = os.path.exists(path_check) or os.path.exists(exe_n)

            status = (
                f"{Colors.GREEN}[BEREIT]{Colors.WHITE}"
                if is_ready
                else f"{Colors.GRAY}[NICHT GEFUNDEN]{Colors.WHITE}"
            )
            print(f"  {Colors.YELLOW}[{i+1}]{Colors.WHITE} {eng:<12} {status}")
            found.append(eng)

        print(f"\n  {Colors.YELLOW}[0]{Colors.WHITE} Zurück")
        choice = input("\n  Wahl: ").strip()

        if choice == "":
            continue

        if choice == "0" or not choice:
            break

        if choice.isdigit() and 0 < int(choice) <= len(found):
            CURRENT_ENGINE = found[int(choice) - 1]
            save_settings()
            print(
                f"\n  {Colors.GREEN}[+] Engine auf {CURRENT_ENGINE} gewechselt!{Colors.WHITE}"
            )
            time.sleep(1)
            break


# ============================================================================
# LAUNCHER UPDATES
# ============================================================================


def check_uzdoom_update():
    """Prüft auf UZDoom Engine-Updates"""
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/UZDoom/UZDoom/releases/latest"
        )
        req.add_header("User-Agent", "Python-Launcher")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            latest = data.get("tag_name", "")
            return latest != "4.14.3", latest
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        return False, "4.14.3"


def check_launcher_update(auto=False):
    """Prüft auf Launcher-Updates und sichert Script + CSV"""
    if not auto:
        print(f"\n  {Colors.CYAN}[*] Prüfe auf Launcher-Updates...{Colors.WHITE}")

    try:
        req = urllib.request.Request(UPDATE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            remote_code = response.read().decode("utf-8-sig")

        match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', remote_code)
        if match:
            remote_version = match.group(1)

            if remote_version != APP_VERSION:
                if not auto:
                    print(
                        f"\n  {Colors.GREEN}[+] Neues Launcher-Update gefunden! (Version {remote_version}){Colors.WHITE}"
                    )
                    print(
                        f"  {Colors.GRAY}Aktuelle Version: {APP_VERSION}{Colors.WHITE}"
                    )

                choice = (
                    input(
                        f"\n  {Colors.YELLOW}Möchtest du den Launcher aktualisieren? (j/n): {Colors.WHITE}"
                    )
                    .strip()
                    .lower()
                )

                if choice == "j":
                    script_path = os.path.abspath(sys.argv[0])

                    # --- BACKUP-LOGIK (Script & CSV) ---
                    # 1. Script Backup
                    backup_path = f"{script_path}.bak_v{APP_VERSION}"
                    shutil.copy2(script_path, backup_path)

                    # 2. CSV Backup (Falls vorhanden)
                    if os.path.exists(CSV_FILE):
                        csv_backup_path = f"{CSV_FILE}.bak_v{APP_VERSION}"
                        shutil.copy2(CSV_FILE, csv_backup_path)
                        csv_info = " & CSV"
                    else:
                        csv_info = ""

                    print(
                        f"  {Colors.MAGENTA}[*] Backup erstellt: {os.path.basename(backup_path)}{csv_info}{Colors.WHITE}"
                    )

                    # Update schreiben
                    remote_code_fixed = remote_code.replace("\r\n", "\n")
                    with open(script_path, "w", encoding="utf-8-sig") as f:
                        f.write(remote_code_fixed)

                    print(
                        f"  {Colors.GREEN}[+] Update erfolgreich installiert!{Colors.WHITE}"
                    )
                    print(
                        f"  {Colors.YELLOW}[!] Der Launcher wird nun neu gestartet!{Colors.WHITE}"
                    )
                    time.sleep(3)
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    print(f"  {Colors.YELLOW}[!] Update übersprungen.{Colors.WHITE}")
                    time.sleep(1)
            elif not auto:
                print(
                    f"  {Colors.GREEN}[+] Du nutzt bereits die aktuellste Version ({APP_VERSION}).{Colors.WHITE}"
                )
                time.sleep(2)
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        if not auto:
            print(f"  {Colors.RED}[!] Fehler beim Update-Check: {e}{Colors.WHITE}")
            time.sleep(2)


def rollback_launcher():
    """Stellt eine ältere Version des Scripts und der CSV wieder her"""
    script_path = os.path.abspath(sys.argv[0])
    backup_files = sorted(glob.glob(f"{script_path}.bak_v*"), reverse=True)

    if not backup_files:
        print(
            f"\n  {Colors.YELLOW}[!] Keine Backups für einen Rollback gefunden.{Colors.WHITE}"
        )
        input(f"  {Colors.GRAY}Drücke ENTER zum Fortfahren...{Colors.WHITE}")
        return

    print(f"\n  {Colors.CYAN}--- ROLLBACK: VERFÜGBARE BACKUPS ---{Colors.WHITE}")
    for i, backup in enumerate(backup_files):
        print(f"  [{i+1}] {os.path.basename(backup)}")
    print("  [0] Abbrechen")

    choice = input(
        f"\n  {Colors.YELLOW}Wähle ein Backup (0-{len(backup_files)}): {Colors.WHITE}"
    ).strip()

    if choice.isdigit():
        idx = int(choice)
        if idx == 0:
            return
        if 1 <= idx <= len(backup_files):
            selected_script_bak = backup_files[idx - 1]

            # Versions-Suffix extrahieren (z.B. .bak_v1.1)
            version_suffix = selected_script_bak.split(".bak_")[-1]
            selected_csv_bak = f"{CSV_FILE}.bak_{version_suffix}"

            # Aktuellen Zustand als "Broken" sichern (Sicherheitsnetz)
            shutil.copy2(script_path, f"{script_path}.broken")
            if os.path.exists(CSV_FILE):
                shutil.copy2(CSV_FILE, f"{CSV_FILE}.broken")

            # Wiederherstellung Script
            shutil.copy2(selected_script_bak, script_path)

            # Wiederherstellung CSV (falls Backup existiert)
            csv_restored = False
            if os.path.exists(selected_csv_bak):
                shutil.copy2(selected_csv_bak, CSV_FILE)
                csv_restored = True

            msg = f"[+] Rollback auf {version_suffix} erfolgreich!"
            if csv_restored:
                msg += " (Inkl. CSV)"

            print(f"  {Colors.GREEN}{msg}{Colors.WHITE}")
            print(
                f"  {Colors.YELLOW}[!] Launcher wird beendet. Bitte neu starten!{Colors.WHITE}"
            )
            time.sleep(3)
            sys.exit(0)

    print(f"  {Colors.RED}[!] Ungültige Eingabe.{Colors.WHITE}")
    time.sleep(1)


# ============================================================================
# MAP-MANAGEMENT (CSV)
# ============================================================================


def get_next_id(game_type):
    """Ermittelt die nächste freie ID"""

    # 1. FALLBACK: Wenn die CSV fehlt
    if not os.path.exists(CSV_FILE):
        if game_type == "DOOM":
            return "1"
        if game_type == "HERETIC":
            return "H1"
        if game_type == "HEXEN":
            return "X1"
        if game_type == "WOLFENSTEIN":
            return "W"
        if game_type == "TESTMAP":
            return "TEST"
        return "999"

    # 2. VARIABLEN VORBEREITEN
    ids = []
    has_exact_w = False
    has_exact_test = False
    prefix = ""

    if game_type == "HERETIC":
        prefix = "H"
    elif game_type == "HEXEN":
        prefix = "X"
    elif game_type == "WOLFENSTEIN":
        prefix = "W"
    elif game_type == "TESTMAP":
        prefix = "TEST"

    # 3. SCAN DER VORHANDENEN EINTRÄGE
    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                id_val = str(row.get("ID", "")).strip().upper()
                if not id_val:
                    continue

                # Fall: DOOM
                if game_type == "DOOM" and id_val.isdigit():
                    ids.append(int(id_val))

                # Fall: WOLFENSTEIN
                elif game_type == "WOLFENSTEIN":
                    if id_val == "W":
                        has_exact_w = True
                    elif id_val.startswith("W"):
                        num_part = id_val[1:]
                        if num_part.isdigit():
                            ids.append(int(num_part))

                # Fall: TESTMAP
                elif game_type == "TESTMAP":
                    if id_val == "TEST":
                        has_exact_test = True
                    elif id_val.startswith("TEST"):
                        num_part = id_val[4:]
                        if num_part.isdigit():
                            ids.append(int(num_part))

                # Fall: HERETIC/HEXEN
                elif prefix and id_val.startswith(prefix):
                    num_part = id_val[len(prefix) :]  # noqa: E203
                    if num_part.isdigit():
                        ids.append(int(num_part))
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        return "999"

    # 4. DIE NÄCHSTE ID BERECHNEN

    # Speziallogik für Wolfenstein
    if game_type == "WOLFENSTEIN":
        if not has_exact_w:
            return "W"
        next_num = max(ids) + 1 if ids else 2
        return f"W{next_num}"

    # Speziallogik für Testmap
    if game_type == "TESTMAP":
        if not has_exact_test:
            return "TEST"
        next_num = max(ids) + 1 if ids else 2
        return f"TEST{next_num}"

    # Logik für Doom, Heretic, Hexen
    next_num = max(ids) + 1 if ids else 1

    if game_type == "DOOM":
        return str(next_num)
    return f"{prefix}{next_num}"


def toggle_map_clear(map_id):
    """Setzt oder entfernt den [C]-Marker"""
    if not os.path.exists(CSV_FILE):
        return False

    rows = []
    found = False
    search_id = map_id.upper()

    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        if not reader:
            return False

        header = reader[0]
        rows.append(header)

        for row in reader[1:]:
            if not row:
                continue
            if row[0].strip().upper() == search_id:
                found = True
                if " [C]" in row[1]:
                    row[1] = row[1].replace(" [C]", "")
                else:
                    row[1] = row[1] + " [C]"
            rows.append(row)

    if found:
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    return found


def get_completion_stats(all_maps):
    """Zählt alle [C] Marker in der aktuellen Map-Liste"""
    real_maps = [m for m in all_maps if m and m[0] != "EMPTY"]
    total = len(real_maps)
    completed = sum(1 for m in real_maps if "[C]" in str(m[0]))

    percent = (completed / total * 100) if total > 0 else 0
    return completed, total, percent


def toggle_mod_skip(map_id):
    """Schaltet die Mod-Erlaubnis für eine Map"""
    if not os.path.exists(CSV_FILE):
        return False

    rows = []
    found = False
    search_id = map_id.upper()

    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        content = f.read()
        if not content.strip():
            return False
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(content[:2048], delimiters=",;")
        except csv.Error:
            dialect = "excel"

        reader = csv.DictReader(f, dialect=dialect)
        fieldnames = reader.fieldnames

        if "MOD" not in fieldnames:
            fieldnames.append("MOD")

        for row in reader:
            if row.get("ID", "").strip().upper() == search_id:
                found = True
                current = row.get("MOD", "0").strip()
                row["MOD"] = "0" if current == "1" else "1"
            rows.append(row)

    if found:
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, dialect=dialect)
            writer.writeheader()
            writer.writerows(rows)
    return found


def uninstall_map(map_id):
    """Löscht eine Map und ihre Dateien"""
    rows = []
    map_to_delete = None
    header = []

    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if row and row[0].strip().upper() == map_id.upper():
                    map_to_delete = row
                else:
                    rows.append(row)
    except Exception as e:
        print(f"  {Colors.RED}[!] CSV Fehler: {e}{Colors.WHITE}")
        return False

    if not map_to_delete:
        return False

    # Basis-Spiele schützen
    if len(map_to_delete) > 6 and map_to_delete[6].strip().upper() == "IWAD":
        print(
            f"\n  {Colors.RED}[!] Basis-Spiele können nicht gelöscht werden!{Colors.WHITE}"
        )
        time.sleep(2)
        return True

    name = map_to_delete[1].replace(" [C]", "")
    filename = map_to_delete[3]

    print(f"\n  {Colors.RED}WARNUNG: '{name}' wirklich löschen?{Colors.WHITE}")
    confirm = input(f"  {Colors.YELLOW}Tippe 'JA': {Colors.WHITE}").strip()

    if confirm != "JA":
        return True

    # Dateien löschen
    base_name = os.path.splitext(filename)[0]
    dir_path = os.path.join(PWAD_DIR, base_name)
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)

    for root, _, files in os.walk(PWAD_DIR):
        for f in files:
            if f.lower() == filename.lower():
                try:
                    os.remove(os.path.join(root, f))
                except Exception as e:
                    print(f"Fehler aufgetreten: {e}")
                    pass

    # CSV speichern
    try:
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

        repair_map_indices()
        print(f"  {Colors.GREEN}[✔] Gelöscht und IDs neu sortiert!{Colors.WHITE}")
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"  {Colors.RED}[!] Schreibfehler: {e}{Colors.WHITE}")
        return False


def repair_map_indices():
    if not os.path.exists(CSV_FILE):
        return
    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            # Filtert leere Zeilen und Trenner raus
            rows = [r for r in reader if r.get("ID") and "---" not in r.get("Name", "")]
        if not rows:
            return

        # Gruppen erstellen
        iwads, doom_pwads, heretic, hexen, custom_stuff = [], [], [], [], []

        for r in rows:
            kat = str(r.get("Kategorie", "")).upper()
            eid = str(r.get("ID", "")).upper()

            # Kategorien filtern
            if kat == "IWAD":
                iwads.append(r)
            elif eid.startswith("H") and not eid.startswith("HX"):
                heretic.append(r)
            elif eid.startswith("X") or eid.startswith("HX"):
                hexen.append(r)
            elif (
                kat in ["WOLFENSTEIN", "TESTMAP", "CUSTOM"]
                or eid.startswith("W")
                or eid.startswith("T")
            ):
                custom_stuff.append(r)
            else:
                doom_pwads.append(r)

        def get_num(r):
            m = re.search(r"\d+", str(r.get("ID", "0")))
            return int(m.group()) if m else 0

        # --- AUTO-REPAIR BEREICH ---
        iwads.sort(key=get_num)
        for i, r in enumerate(iwads, 1):
            r["ID"] = str(i)

        doom_pwads.sort(key=get_num)
        for i, r in enumerate(doom_pwads, len(iwads) + 1):
            r["ID"] = str(i)

        heretic.sort(key=get_num)
        for i, r in enumerate(heretic, 1):
            r["ID"] = f"H{i}"

        hexen.sort(key=get_num)
        for i, r in enumerate(hexen, 1):
            r["ID"] = f"X{i}"

        custom_stuff.sort(key=lambda x: x.get("Kategorie", ""))

        # Datei schreiben
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=reader[0].keys())
            writer.writeheader()
            writer.writerows(iwads + doom_pwads + heretic + hexen + custom_stuff)

    except Exception as e:
        print(f" Fehler bei ID-Reparatur: {e}")


# ============================================================================
# MAPS LADEN & ANZEIGEN
# ============================================================================


def load_maps():
    import re

    blocks = {1: [], 2: [], 3: []}

    if not os.path.exists(CSV_FILE):
        return blocks

    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        content = f.read()
        if not content.strip():
            return blocks
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(content[:2048], delimiters=",;")
        except csv.Error:
            dialect = "excel"

        reader = csv.DictReader(f, dialect=dialect)

        for row in reader:

            def safe_get(keys, default=""):
                if isinstance(keys, str):
                    keys = [keys]
                for k in keys:
                    val = row.get(k)
                    if val is not None:
                        return str(val).strip()
                return default

            entry_id = safe_get("ID")
            name = safe_get("Name", "Unbekannt")
            core = safe_get(["Core", "IWAD"])
            ordner = safe_get(["Ordner_oder_Datei", "Ordner", "PWAD"])
            mods = safe_get(["ModsErlaubt", "MOD"], "1")
            if not mods:
                mods = "1"
            extra = safe_get(["Extra", "ARGS"])
            cat = safe_get("Kategorie").upper()

            if not cat:
                if "heretic" in core.lower() or "hexen" in core.lower():
                    cat = "EXTRA"
                elif "doom2" in core.lower() and ordner:
                    cat = "PWAD"
                else:
                    cat = "IWAD"

            try:
                play_val = row.get("Playtime", "0")
                playtime_min = (
                    int(play_val) if play_val and str(play_val).isdigit() else 0
                )
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

            mod_icon = "[M] " if mods == "1" else ""
            base_str = f"{entry_id} - {name} {mod_icon}"

            if playtime_str:
                display_text = (
                    f"{base_str}__L__ {Colors.GRAY}{playtime_str}{Colors.WHITE}"
                )
            else:
                display_text = f"{base_str}__L__"

            remaining = []
            if ordner:
                remaining.append(ordner)
            remaining.append(mods)
            if extra:
                remaining.extend(extra.split())

            item_tuple = (display_text, entry_id, core, name, remaining, 0)

            if cat == "IWAD":
                blocks[1].append((*item_tuple[:5], 1))
            elif cat == "PWAD":
                blocks[2].append((*item_tuple[:5], 2))
            elif cat in ["EXTRA", "HERETIC", "HEXEN"]:
                blocks[3].append((*item_tuple[:5], 3))

        def natural_sort_key(item):
            eid = str(item[1]).upper()
            priorities = {
                "H": 1,
                "X": 2,
                "W": 3,
                "T": 4,
            }

            prefix_match = re.match(r"([A-Z]+)", eid)
            prefix = prefix_match.group(1) if prefix_match else ""

            first_char = prefix[0] if prefix else ""
            weight = priorities.get(first_char, 99)

            num_match = re.search(r"(\d+)", eid)
            num = int(num_match.group(1)) if num_match else 0
            return (weight, num)

        if blocks[3]:
            blocks[3].sort(key=natural_sort_key)

            formatted_col4 = []
            last_prefix = None

            for item in blocks[3]:
                current_id = str(item[1]).upper()
                prefix_match = re.match(r"([A-Z]+)", current_id)
                current_prefix = prefix_match.group(1) if prefix_match else ""

                if last_prefix is not None and current_prefix != last_prefix:
                    formatted_col4.append(("EMPTY", "EMPTY", "", "", [], 3))

                formatted_col4.append(item)
                last_prefix = current_prefix

            blocks[3] = formatted_col4

    return blocks


# ============================================================================
# INSTALLER
# ============================================================================


def run_installer():
    """Installiert Maps aus dem Install-Ordner"""
    INSTALL_DIR = os.path.join(BASE_DIR, "Install")

    # 1. Erkennungs-Matrix für Original-Dateien
    OFFICIAL_MAPPING = {
        "doom.wad": {
            "Name": "Ultimate Doom",
            "IWAD": "doom.wad",
            "Ordner": "",
            "Kat": "IWAD",
        },
        "doom2.wad": {
            "Name": "Doom II: Hell on Earth",
            "IWAD": "doom2.wad",
            "Ordner": "",
            "Kat": "IWAD",
        },
        "tnt.wad": {
            "Name": "Final Doom: TNT:Evilution",
            "IWAD": "tnt.wad",
            "Ordner": "",
            "Kat": "IWAD",
        },
        "plutonia.wad": {
            "Name": "Final Doom: The Plutonia Experiment",
            "IWAD": "plutonia.wad",
            "Ordner": "",
            "Kat": "IWAD",
        },
        "sigil.wad": {
            "Name": "Sigil",
            "IWAD": "doom.wad",
            "Ordner": "sigil.wad",
            "Kat": "IWAD",
        },
        "sigil2.wad": {
            "Name": "Sigil 2",
            "IWAD": "doom.wad",
            "Ordner": "sigil2.wad",
            "Kat": "IWAD",
        },
        "masterlevels.wad": {
            "Name": "Doom II: Masterlevels",
            "IWAD": "doom2.wad",
            "Ordner": "masterlevels.wad",
            "Kat": "IWAD",
        },
        "nerve.wad": {
            "Name": "Doom II: No Rest for the Living",
            "IWAD": "doom2.wad",
            "Ordner": "nerve.wad",
            "Kat": "IWAD",
        },
        "id1.wad": {
            "Name": "Doom II: Legacy of Rust",
            "IWAD": "doom2.wad",
            "Ordner": "id1.wad",
            "Kat": "IWAD",
        },
    }

    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)
        print(
            f"\n  {Colors.YELLOW}[!] Ordner 'Install' wurde erstellt. WADs dort ablegen.{Colors.WHITE}"
        )
        time.sleep(3)
        return

    items = os.listdir(INSTALL_DIR)
    if not items:
        print(
            f"\n  {Colors.YELLOW}Keine Dateien im Install-Ordner gefunden.{Colors.WHITE}"
        )
        time.sleep(2)
        return

    print(f"\n {Colors.CYAN}--- INSTALLATION LÄUFT ---{Colors.WHITE}")
    installed_count = 0

    # ERSTER DURCHGANG: Dateien entpacken oder Originale erkennen
    for item in items:
        item_path = os.path.join(INSTALL_DIR, item)
        if not os.path.isfile(item_path):
            continue

        fname_lower = item.lower()

        # --- CHECK: Ist es ein Original-Spiel? ---
        if fname_lower in OFFICIAL_MAPPING:
            data = OFFICIAL_MAPPING[fname_lower]
            print(
                f"  {Colors.CYAN}[*]{Colors.WHITE} Original-Spiel erkannt: {Colors.GREEN}{data['Name']}{Colors.WHITE}"
            )

            # Ziel: Direkt in den Iwad  Ordner
            target_path = os.path.join(BASE_DIR, "iwad", item)

            if not os.path.exists(target_path):
                shutil.move(item_path, target_path)

                # In die CSV eintragen
                with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as csvfile:
                    fieldnames = [
                        "ID",
                        "Name",
                        "IWAD",
                        "Ordner",
                        "MOD",
                        "ARGS",
                        "Kategorie",
                        "Playtime",
                        "LastPlayed",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if os.path.getsize(CSV_FILE) == 0:
                        writer.writeheader()
                    writer.writerow(
                        {
                            "ID": "TEMP",
                            "Name": data["Name"],
                            "IWAD": data["IWAD"],
                            "Ordner": data["Ordner"],
                            "MOD": "0",
                            "ARGS": "",
                            "Kategorie": data["Kat"],
                            "Playtime": "0",
                            "LastPlayed": "-",
                        }
                    )
                installed_count += 1
                continue
            else:
                print(
                    f"  {Colors.RED}[!] {item} existiert bereits im Hauptverzeichnis.{Colors.WHITE}"
                )
                os.remove(item_path)
                continue

        # --- NORMALER MOD-INSTALLER ---
        ext = item.rsplit(".", 1)[-1].lower() if "." in item else ""
        folder_name = item.rsplit(".", 1)[0]
        tmp_f = os.path.join(INSTALL_DIR, folder_name)

        if ext == "zip":
            print(f"  {Colors.MAGENTA}[*]{Colors.WHITE} Entpacke ZIP: {item}...")
            os.makedirs(tmp_f, exist_ok=True)
            try:
                with zipfile.ZipFile(item_path, "r") as z:
                    z.extractall(tmp_f)
                os.remove(item_path)
            except Exception as e:
                print(f"  {Colors.RED}[!] ZIP-Fehler: {e}{Colors.WHITE}")

        elif ext == "7z":
            print(f"  {Colors.MAGENTA}[*]{Colors.WHITE} Entpacke 7Z: {item}...")
            os.makedirs(tmp_f, exist_ok=True)
            try:
                import py7zr

                with py7zr.SevenZipFile(item_path, mode="r") as z:
                    z.extractall(path=tmp_f)
                os.remove(item_path)
            except ImportError:
                print(
                    f"  {Colors.YELLOW}[!] py7zr fehlt. Installiere über pip...{Colors.WHITE}"
                )
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "py7zr", "--quiet"]
                )
            except Exception as e:
                print(f"  {Colors.RED}[!] 7Z-Fehler: {e}{Colors.WHITE}")

        elif ext in ["wad", "pk3", "pk7"]:
            print(f"  {Colors.MAGENTA}[*]{Colors.WHITE} Verpacke Mod-Datei: {item}...")
            os.makedirs(tmp_f, exist_ok=True)
            shutil.move(item_path, os.path.join(tmp_f, item))

    # ZWEITER DURCHGANG: Ordner verarbeiten und in die CSV einpflegen
    folders = [
        d
        for d in os.listdir(INSTALL_DIR)
        if os.path.isdir(os.path.join(INSTALL_DIR, d))
    ]

    for folder in folders:
        full_path = os.path.join(INSTALL_DIR, folder)

        # Unterordner-Korrektur
        game_files = [
            f
            for f in os.listdir(full_path)
            if f.lower().endswith((".wad", ".pk3", ".pk7"))
        ]
        if not game_files:
            for item in os.listdir(full_path):
                sub_path = os.path.join(full_path, item)
                if os.path.isdir(sub_path):
                    for sub_item in os.listdir(sub_path):
                        shutil.move(os.path.join(sub_path, sub_item), full_path)
                    os.rmdir(sub_path)
                    break

        # Basis-Spiel TXT-Scan
        m_name = folder.replace("_", " ")
        m_core = "doom2.wad"
        kat = "PWAD"
        game_type = "DOOM"

        txt_files = [f for f in os.listdir(full_path) if f.lower().endswith(".txt")]
        if txt_files:
            try:
                with open(
                    os.path.join(full_path, txt_files[0]),
                    "r",
                    encoding="utf-8-sig",
                    errors="ignore",
                ) as txt:
                    content = txt.read().lower()
                    if "heretic" in content:
                        m_core, kat, game_type = "heretic.wad", "EXTRA", "HERETIC"
                    elif "hexen" in content:
                        m_core, kat, game_type = "hexen.wad", "EXTRA", "HEXEN"
                    elif "plutonia" in content:
                        m_core = "plutonia.wad"
                    elif "tnt" in content:
                        m_core = "tnt.wad"
                    elif "doom.wad" in content:
                        m_core = "doom.wad"
            except Exception as e:
                print(f"Fehler aufgetreten: {e}")
                pass

        # In PWADS Ordner verschieben
        target_name = folder.replace(" ", "_")
        target_path = os.path.join(PWAD_DIR, target_name)

        if not os.path.exists(target_path):
            shutil.move(full_path, target_path)
            new_id = get_next_id(game_type)

            with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=[
                        "ID",
                        "Name",
                        "IWAD",
                        "Ordner",
                        "MOD",
                        "ARGS",
                        "Kategorie",
                        "Playtime",
                        "LastPlayed",
                    ],
                )
                writer.writerow(
                    {
                        "ID": new_id,
                        "Name": m_name,
                        "IWAD": m_core,
                        "Ordner": target_name,
                        "MOD": "0",
                        "ARGS": "",
                        "Kategorie": kat,
                        "Playtime": "0",
                        "LastPlayed": "-",
                    }
                )
            print(
                f"  {Colors.GREEN}[+]{Colors.WHITE} Mod installiert: {Colors.YELLOW}{m_name}{Colors.WHITE}"
            )
            installed_count += 1
        else:
            shutil.rmtree(full_path)

    if installed_count > 0:
        repair_map_indices()
        print(
            f"\n  {Colors.GREEN}Installation von {installed_count} Element(en) erfolgreich!{Colors.WHITE}"
        )
    time.sleep(2)


# ============================================================================
# DOOMWORLD API
# ============================================================================


def get_installed_pwads():
    """Listet alle installierten WADs auf"""
    installed = []

    if os.path.exists(PWAD_DIR):
        for root, _, files in os.walk(PWAD_DIR):
            for f in files:
                if f.lower().endswith((".wad", ".pk3", ".zip", ".pk7")):
                    installed.append(f.lower())

    if os.path.exists(IWAD_DIR):
        for root, _, files in os.walk(IWAD_DIR):
            for f in files:
                if f.lower().endswith((".wad", ".pk3")):
                    installed.append(f.lower())

    return installed


def fetch_folder_files(folder_name):
    """Holt Dateien aus einem idgames-Ordner"""
    url = f"https://www.doomworld.com/idgames/api/api.php?action=getcontents&name={folder_name}&out=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8-sig"))
            content = data.get("content", {})
            if not content:
                return [], []

            f = content.get("file", [])
            if f is None:
                f = []
            if isinstance(f, dict):
                f = [f]

            d = content.get("dir", [])
            if d is None:
                d = []
            if isinstance(d, dict):
                d = [d]

            return f, d
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        return [], []


def download_idgames(file_data):
    """Lädt eine Map von idgames herunter und installiert sie"""
    TEMP_DIR = "install"
    FINAL_DIR = "pwad"

    for d in [TEMP_DIR, FINAL_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)

    filename = file_data.get("filename")
    folder_name = os.path.splitext(filename)[0]
    title = (file_data.get("title") or filename).replace(",", " ")

    temp_extract_path = os.path.join(TEMP_DIR, folder_name)
    final_mod_path = os.path.join(FINAL_DIR, folder_name)

    if os.path.exists(final_mod_path):
        print(
            f"\n  {Colors.YELLOW}[Info]{Colors.WHITE} '{folder_name}' existiert bereits im {FINAL_DIR}-Ordner."
        )
        if input("  Überschreiben? (j/N): ").lower() != "j":
            return

    is_already_in_csv = False
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            if folder_name.lower() in f.read().lower():
                is_already_in_csv = True

    api_dir = file_data.get("dir", "").lower()
    if "heretic" in api_dir:
        game_type, core_wad, category = "HERETIC", "heretic.wad", "EXTRA"
    elif "hexen" in api_dir:
        game_type, core_wad, category = "HEXEN", "hexen.wad", "EXTRA"
    else:
        game_type, core_wad, category = (
            "DOOM",
            ("doom2.wad" if "doom2" in api_dir else "doom.wad"),
            "PWAD",
        )

    try:
        zip_temp_path = os.path.join(TEMP_DIR, filename)
        print(f"\n  {Colors.CYAN}Lade herunter:{Colors.WHITE} {title}...")
        req = urllib.request.Request(
            f"https://youfailit.net/pub/idgames/{file_data.get('dir')}{filename}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req) as response, open(
            zip_temp_path, "wb"
        ) as out_file:
            out_file.write(response.read())

        print(f"  {Colors.YELLOW}Entpacke...{Colors.WHITE}")
        with zipfile.ZipFile(zip_temp_path, "r") as zip_ref:
            zip_ref.extractall(temp_extract_path)

        os.remove(zip_temp_path)

        if os.path.exists(temp_extract_path):
            contents = os.listdir(temp_extract_path)
            if len(contents) == 1:
                single_item_path = os.path.join(temp_extract_path, contents[0])
                if os.path.isdir(single_item_path):
                    for item in os.listdir(single_item_path):
                        src = os.path.join(single_item_path, item)
                        dst = os.path.join(temp_extract_path, item)
                        shutil.move(src, dst)
                    os.rmdir(single_item_path)
                    print(
                        f"  {Colors.MAGENTA}[Info] Verschachtelten Unterordner '{contents[0]}' aufgelöst.{Colors.WHITE}"
                    )

        print(f"  {Colors.GREEN}Verschiebe nach:{Colors.WHITE} {final_mod_path}")
        if os.path.exists(final_mod_path):
            shutil.rmtree(final_mod_path)
        shutil.move(temp_extract_path, final_mod_path)

        if not is_already_in_csv:
            new_id = get_next_id(game_type)
            with open(CSV_FILE, "a+", newline="", encoding="utf-8-sig") as f:
                f.seek(0)
                delim = ";" if ";" in f.readline() else ","
                f.seek(0, os.SEEK_END)
                if f.tell() > 0:
                    f.seek(f.tell() - 1)
                    if f.read(1) != "\n":
                        f.write("\n")
                writer = csv.writer(f, delimiter=delim)
                writer.writerow(
                    [new_id, title, core_wad, folder_name, "0", "", category, "0", "-"]
                )

            repair_map_indices()
            print(f"  {Colors.GREEN}[OK]{Colors.WHITE} Registriert als ID: {new_id}")

        input("\n  Installation fertig & install-Ordner bereinigt. ENTER...")

    except Exception as e:
        print(
            f"\n  {Colors.RED}[!] Fehler beim Download/Entpacken:{Colors.WHITE} {str(e)}"
        )
        try:
            if "zip_temp_path" in locals() and os.path.exists(zip_temp_path):
                os.remove(zip_temp_path)
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass
        try:
            if "temp_extract_path" in locals() and os.path.exists(temp_extract_path):
                shutil.rmtree(temp_extract_path)
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass
        input(
            f"\n  {Colors.YELLOW}Drücke ENTER, um ins Menü zurückzukehren...{Colors.WHITE}"
        )


def search_doomworld():
    """Durchsucht Doomworld nach Maps"""
    clear_screen()
    print(f"\n  {Colors.MAGENTA}--- DOOMWORLD (idgames) SUCHE ---{Colors.WHITE}")
    print(f"  [{Colors.YELLOW}1{Colors.WHITE}] Manuelle Suche (Stichwort)")
    print(f"  [{Colors.YELLOW}2{Colors.WHITE}] Doom Megawads (Top Rated)")
    print(f"  [{Colors.YELLOW}3{Colors.WHITE}] Doom 2 Megawads (Top Rated)")
    print(f"  [{Colors.YELLOW}4{Colors.WHITE}] Heretic Wads (Top Rated)")
    print(f"  [{Colors.YELLOW}5{Colors.WHITE}] Hexen Wads (Top Rated)")

    choice = input("\n  Option wählen (ENTER zum Abbruch): ").strip()
    if not choice:
        return

    all_results = []

    if choice == "1":
        query = input("  Suchbegriff: ").strip()
        if not query:
            return
        url = f"https://www.doomworld.com/idgames/api/api.php?action=search&query={urllib.parse.quote(query)}&type=title&sort=rating&dir=desc&out=json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8-sig"))
                res = data.get("content", {}).get("file", [])
                if res is None:
                    res = []
                all_results = [res] if isinstance(res, dict) else res
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass

    elif choice in ["2", "3", "4", "5"]:
        if choice == "2":
            main_folders = ["levels/doom/megawads/"]
        elif choice == "3":
            main_folders = ["levels/doom2/megawads/", "levels/doom2/Ports/megawads/"]
        elif choice == "4":
            main_folders = ["levels/heretic/", "levels/heretic/Ports/"]
        elif choice == "5":
            main_folders = ["levels/hexen/", "levels/hexen/Ports/"]

        print(
            f"  {Colors.GRAY}Synchronisiere mit Doomworld... bitte warten...{Colors.WHITE}"
        )
        for folder in main_folders:
            files, subdirs = fetch_folder_files(folder)
            if files:
                all_results.extend(files)
            if subdirs:
                for sd in subdirs:
                    if sd and "name" in sd:
                        folder_name = sd["name"].lower()
                        if any(
                            x in folder_name
                            for x in ["deathmatch", "music", "skins", "sounds"]
                        ):
                            continue

                        sys.stdout.write(f"\r  Scanne: {sd['name'][-25:]}   ")
                        sys.stdout.flush()
                        s_files, _ = fetch_folder_files(sd["name"])
                        if s_files:
                            all_results.extend(s_files)

        print("\r" + " " * 60 + "\r", end="")

    if not all_results:
        print(f"  {Colors.RED}[!] Keine Karten gefunden.{Colors.WHITE}")
        input("  ENTER...")
        return

    all_results.sort(key=lambda x: float(x.get("rating", 0) or 0), reverse=True)

    page_size = 50
    current_start = 0
    installed_files = get_installed_pwads()

    while True:
        clear_screen()
        total = len(all_results)
        current_end = min(current_start + page_size, total)

        print(
            f"\n  {Colors.MAGENTA}--- DOOMWORLD ERGEBNISSE ({current_start + 1} bis {current_end} von {total}) ---{Colors.WHITE}"
        )
        print(
            f"  {Colors.MAGENTA}┌─────┬────────────────────────────────────────────────────────┬────────────┬──────────────────────────────────┐{Colors.WHITE}"
        )
        print(
            f"  {Colors.MAGENTA}│{Colors.WHITE} {'#':<3} {Colors.MAGENTA}│{Colors.WHITE} {'Titel':<54} {Colors.MAGENTA}│{Colors.WHITE} {'Größe':<10} {Colors.MAGENTA}│{Colors.WHITE} {'Rating':<16}{'Status':>16} {Colors.MAGENTA}│{Colors.WHITE}"
        )
        print(
            f"  {Colors.MAGENTA}├─────┼────────────────────────────────────────────────────────┼────────────┼──────────────────────────────────┤{Colors.WHITE}"
        )

        for i in range(current_start, current_end):
            res = all_results[i]
            title = res.get("title") or res.get("filename") or "Unbekannt"
            title = str(title)
            if len(title) > 54:
                title = title[:51] + "..."
            else:
                title = title[:54]

            raw_filename = str(res.get("filename", "")).lower()
            filename = raw_filename.split("/")[-1]
            base_name = os.path.splitext(filename)[0]

            try:
                size_bytes = int(res.get("size", 0))
                size_mb = f"{size_bytes / (1024*1024):.1f} MB"
            except Exception as e:
                print(f"Fehler aufgetreten: {e}")
                size_mb = "?? MB"

            try:
                r_val = float(res.get("rating", 0) or 0)
            except Exception as e:
                print(f"Fehler aufgetreten: {e}")
                r_val = 0.0

            stars = "★" * int(r_val)
            if r_val % 1 >= 0.5:
                stars += "½"

            is_installed = False
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
                    if base_name in f.read().lower():
                        is_installed = True

            if not is_installed:
                if filename in installed_files or any(
                    base_name in f for f in installed_files
                ):
                    is_installed = True
                elif os.path.exists(os.path.join(PWAD_DIR, base_name)):
                    is_installed = True

            if is_installed:
                row_col = Colors.GREEN
                print(
                    f"  {Colors.MAGENTA}│ {row_col}{i+1:<3}{Colors.MAGENTA} │ {row_col}{title:<54}{Colors.MAGENTA} │ {row_col}{size_mb:<10}{Colors.MAGENTA} │ {row_col}{stars:<16}{'[INSTALLIERT]':>16}{Colors.MAGENTA} │{Colors.WHITE}"
                )
            else:
                print(
                    f"  {Colors.MAGENTA}│ {Colors.YELLOW}{i+1:<3}{Colors.MAGENTA} │ {Colors.WHITE}{title:<54}{Colors.MAGENTA} │ {Colors.CYAN}{size_mb:<10}{Colors.MAGENTA} │ {Colors.YELLOW}{stars:<16}{'':>16}{Colors.MAGENTA} │{Colors.WHITE}"
                )

        print(
            f"  {Colors.MAGENTA}└─────┴────────────────────────────────────────────────────────┴────────────┴──────────────────────────────────┘{Colors.WHITE}"
        )

        print(f"\n  {Colors.MAGENTA}Navigation:{Colors.WHITE}")
        nav_options = []
        if current_end < total:
            nav_options.append(f"[{Colors.YELLOW}N{Colors.WHITE}] Nächste Seite")
        if current_start > 0:
            nav_options.append(f"[{Colors.YELLOW}B{Colors.WHITE}] Vorherige Seite")

        if nav_options:
            print("  " + "  ".join(nav_options))

        sel = (
            input(
                f"\n  Nummer wählen, {Colors.YELLOW}N{Colors.WHITE}/{Colors.YELLOW}B{Colors.WHITE} blättern oder ENTER für Abbruch: "
            )
            .strip()
            .lower()
        )

        if not sel:
            break
        elif sel == "n" and current_end < total:
            current_start += page_size
        elif sel == "b" and current_start > 0:
            current_start -= page_size
        elif sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < total:
                download_idgames(all_results[idx])
                break
            else:
                print(f"  {Colors.RED}[!] Ungültige Nummer.{Colors.WHITE}")
                time.sleep(1)


# ============================================================================
# INITIAL SETUP
# ============================================================================


def initial_setup():
    """Führt die Ersteinrichtung durch"""
    setup_activity = False
    clear_screen()

    # 1. Benötigte Ordnerstruktur
    required_dirs = [
        "iwad",
        "pwad",
        "mods",
        os.path.join("mods", "doom"),
        os.path.join("mods", "heretic"),
        os.path.join("mods", "hexen"),
        "UzDoom",
        "Install",
    ]

    print(f"\n {Colors.CYAN}--- ERSTEINRICHTUNG / SYSTEMPRÜFUNG ---{Colors.WHITE}\n")

    for d in required_dirs:
        path = os.path.join(BASE_DIR, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(
                f"  {Colors.GREEN}[+]{Colors.WHITE} Ordner erstellt: {Colors.YELLOW}{d}{Colors.WHITE}"
            )
            setup_activity = True

    # 2. maps.csv nur mit Header erstellen
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
            f.write("ID,Name,IWAD,Ordner,MOD,ARGS,Kategorie,Playtime,LastPlayed\n")
        print(
            f"  {Colors.GREEN}[+]{Colors.WHITE} Datenbank-Struktur erstellt: {Colors.YELLOW}maps.csv{Colors.WHITE}"
        )
        setup_activity = True

    # 3. Engine-Prüfung
    if not os.path.exists(UZ_EXE):
        print(f"  {Colors.RED}[!] WICHTIG: UzDoom Engine fehlt!{Colors.WHITE}")
        dl_choice = (
            input("      Soll UZDoom jetzt automatisch heruntergeladen werden? (j/n): ")
            .strip()
            .lower()
        )
        if dl_choice == "j":
            download_uzdoom()
        setup_activity = True

    # 4. Installations-Hinweis
    has_maps = False
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            has_maps = len(f.readlines()) > 1

    if not has_maps:
        print(f"\n  {Colors.MAGENTA}WILLKOMMEN BEIM LAUNCHER!{Colors.WHITE}")
        print(f"  {Colors.GRAY}So startest du:{Colors.WHITE}")
        print(
            f"  1. Kopiere deine {Colors.CYAN}doom2.wad{Colors.WHITE}, {Colors.CYAN}doom.wad{Colors.WHITE} etc. in den Ordner '{Colors.YELLOW}Install{Colors.WHITE}'."
        )
        print(
            f"  2. Starte den Launcher und drücke {Colors.YELLOW}[C]{Colors.WHITE} (Map-Installer)."
        )
        print("  3. Der Installer sortiert alles automatisch in die richtigen Ordner.")
        setup_activity = True

    # 5. Konfigurationsdatei
    if not os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config["STATS"] = {"total_seconds": "0"}
        config["ENGINE"] = {"current": DEFAULT_ENGINE}
        config["OPTIONS"] = {
            "showstats": "False",
            "usemods": "False",
            "debugmode": "False",
            "terminalwidth": "165",
        }
        config["UPDATE"] = {"last_check": "", "next_check": ""}
        with open(CONFIG_FILE, "w", encoding="utf-8-sig") as f:
            config.write(f)
        setup_activity = True

    if setup_activity:
        print(f"\n {Colors.CYAN}---------------------------------------{Colors.WHITE}")
        input(
            f" {Colors.WHITE}Einrichtung bereit. Drücke {Colors.GREEN}ENTER{Colors.WHITE} zum Starten... "
        )


# ============================================================================
# STATS & ANALYSE
# ============================================================================


def analyze_session(log_file, map_id, mapname, session_seconds):
    """Analysiert die Logdatei und zeigt Statistiken an"""
    stats = {"health": 0, "armor": 0, "ammo": 0, "key": 0, "powerup": 0}
    weapons_found = set()
    VALID_START = [
        "picked up",
        "you got",
        "a chainsaw",
        "berserk",
        "megasphere",
        "supercharge",
        "stimpack",
        "medikit",
    ]

    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8-sig", errors="ignore") as f:
            for line in f:
                ln = line.lower().strip()
                if not any(ln.startswith(x) for x in VALID_START):
                    continue

                # Waffen
                if "bfg9000" in ln:
                    weapons_found.add("BFG9000")
                elif "plasma" in ln:
                    weapons_found.add("Plasma Gun")
                elif "rocket" in ln:
                    weapons_found.add("Rocket Launcher")
                elif "super shotgun" in ln or "ssg" in ln:
                    weapons_found.add("Super Shotgun")
                elif "shotgun" in ln:
                    weapons_found.add("Shotgun")
                elif "chaingun" in ln:
                    weapons_found.add("Chaingun")
                elif "chainsaw" in ln:
                    weapons_found.add("Chainsaw")

                # Items
                if any(
                    x in ln
                    for x in [
                        "health bonus",
                        "stimpack",
                        "medikit",
                        "supercharge",
                        "berserk",
                    ]
                ):
                    stats["health"] += 1
                if any(x in ln for x in ["armor bonus", "armor", "megasphere"]):
                    stats["armor"] += 1
                if any(
                    x in ln for x in ["clip", "shells", "ammo", "box of", "backpack"]
                ):
                    stats["ammo"] += 1
                if any(x in ln for x in ["key", "card", "skull"]):
                    stats["key"] += 1
                if any(
                    x in ln
                    for x in [
                        "suit",
                        "visor",
                        "invulnerability",
                        "invisibility",
                        "computer area map",
                    ]
                ):
                    stats["powerup"] += 1

    clear_screen()
    width = 60
    m, s = divmod(session_seconds, 60)

    print(f"\n {Colors.GRAY}{'=' * width}")
    print(f" {Colors.CYAN}  S E S S I O N   Z U S A M M E N F A S S U N G")
    print(f" {Colors.GRAY}{'=' * width}{Colors.WHITE}")

    print(f"  Projekt:  {Colors.YELLOW}{map_id} - {mapname}{Colors.WHITE}")
    print(f"  Dauer:    {Colors.YELLOW}{m} Min. {s} Sek.{Colors.WHITE}")
    print(f" {Colors.GRAY}{'-' * width}{Colors.WHITE}")

    print(f"  {Colors.CYAN}GEGENSTÄNDE:{Colors.WHITE}\n")
    print(
        f"  Heilung:    {Colors.GREEN}{str(stats['health']).rjust(3)}{Colors.WHITE}      Rüstung:    {Colors.CYAN}{str(stats['armor']).rjust(3)}{Colors.WHITE}"
    )
    print(
        f"  Munition:   {Colors.YELLOW}{str(stats['ammo']).rjust(3)}{Colors.WHITE}      Schlüssel:  {Colors.BLUE}{str(stats['key']).rjust(3)}{Colors.WHITE}"
    )
    print(
        f"  Spezial:    {Colors.MAGENTA}{str(stats['powerup']).rjust(3)}{Colors.WHITE}"
    )

    print(f"\n {Colors.GRAY}{'-' * width}{Colors.WHITE}")

    w_text = ", ".join(sorted(list(weapons_found))) if weapons_found else "Keine"
    w_color = Colors.MAGENTA if weapons_found else Colors.GRAY

    wrapper = textwrap.TextWrapper(width=width - 12)
    w_lines = wrapper.wrap(w_text)

    for i, line in enumerate(w_lines):
        if i == 0:
            print(f"  {Colors.CYAN}WAFFEN:{Colors.WHITE}    {w_color}{line}")
        else:
            print(f"            {w_color}{line}")

    print(f" {Colors.GRAY}{'=' * width}{Colors.WHITE}")
    print(
        f"\n    {Colors.YELLOW}Drücke ENTER, um zum Menü zurückzukehren...{Colors.WHITE}"
    )
    input()


# ============================================================================
# GAME START
# ============================================================================


def launch_game(map_data):

    resize_terminal(TERMINAL_WIDTH, 60)
    clear_screen()

    # Struktur:
    _, map_id, core, mapname, remaining, _ = map_data
    core = core.replace(" ", "").strip()
    display_core = core

    VALID_EXTS = (
        ".wad",
        ".pk3",
        ".pk7",
        ".zip",
        ".deh",
        ".bex",
        ".ipk3",
        ".pke",
        ".kpf",
    )

    # Ordner für Mods bestimmen
    sub_folder = "doom"
    if core.lower() == "heretic.wad":
        sub_folder = "heretic"
    elif core.lower() == "hexen.wad":
        sub_folder = "hexen"

    file_params = []
    extra_params = []
    mod_flag = False
    auto_mod = None

    # --- 1. PARAMETER PARSEN  ---
    i = 0
    while i < len(remaining):
        item = str(remaining[i]).strip()
        if not item:
            i += 1
            continue

        if item == "1":
            mod_flag = True
            i += 1
        elif item == "0":
            mod_flag = False
            i += 1
        elif item.startswith("-") or item.startswith("+"):
            extra_params.append(item)
            i += 1
            while i < len(remaining):
                next_val = str(remaining[i]).strip()
                if next_val and not (
                    next_val.startswith("-") or next_val.startswith("+")
                ):
                    if item.lower() == "-config":
                        extra_params.append(os.path.join(BASE_DIR, next_val))
                    else:
                        extra_params.append(next_val)
                    i += 1
                else:
                    break
        else:
            # Suche nach Map-Dateien oder Ordnern
            target_path = None
            potential_paths = [
                os.path.join(PWAD_DIR, item),
                os.path.join(IWAD_DIR, item),
                os.path.join(PWAD_DIR, item + ".wad"),
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    target_path = p
                    break

            if target_path:
                if os.path.isdir(target_path):
                    for f in os.listdir(target_path):
                        if f.lower().endswith(VALID_EXTS):
                            file_params.extend(["-file", os.path.join(target_path, f)])
                else:
                    file_params.extend(["-file", target_path])
            else:
                # Prüfen auf Auto-Mods
                is_system = item.lower() in ["doom", "heretic", "hexen"]
                if not is_system:
                    if os.path.isdir(os.path.join(BASE_DIR, "mods", sub_folder, item)):
                        auto_mod = os.path.join(sub_folder, item)
                    elif os.path.isdir(os.path.join(BASE_DIR, "mods", item)):
                        auto_mod = item
            i += 1

    # --- 2. MOD-AUSWAHL ---
    mod_name = "Vanilla"
    mod_params = []

    if auto_mod:
        mod_name = f"{os.path.basename(auto_mod)} (Auto)"
        mod_path = os.path.join(BASE_DIR, "mods", auto_mod)
        for f in os.listdir(mod_path):
            if f.lower().endswith(VALID_EXTS):
                mod_params.extend(["-file", os.path.join(mod_path, f)])

    elif not mod_flag and USE_MODS:
        mod_dir = os.path.join(BASE_DIR, "mods", sub_folder)
        if os.path.exists(mod_dir):
            available_mods = [
                d
                for d in os.listdir(mod_dir)
                if os.path.isdir(os.path.join(mod_dir, d))
            ]
            if available_mods:
                while True:
                    resize_terminal(TERMINAL_WIDTH, 60)
                    clear_screen()
                    print(f"\n {Colors.CYAN}MOD-AUSWAHL:{Colors.WHITE}\n {'-'*47}")
                    print(
                        f" KARTE : {Colors.GREEN}{mapname}{Colors.WHITE}\n {'-'*47}\n"
                    )
                    for idx, m in enumerate(available_mods, 1):
                        print(f"        {Colors.CYAN}{idx}.{Colors.WHITE} {m}")
                    print(
                        f"\n        {Colors.CYAN}0.{Colors.WHITE} Keine Mod (Vanilla)\n"
                    )

                    m_choice = input(
                        f"        {Colors.YELLOW}DEINE WAHL: {Colors.WHITE}"
                    ).strip()
                    if not m_choice or m_choice == "0":
                        break

                    try:
                        choices = m_choice.split()
                        selected_mods = [
                            available_mods[int(c) - 1]
                            for c in choices
                            if 1 <= int(c) <= len(available_mods)
                        ]
                        if selected_mods:
                            mod_name = ", ".join(selected_mods)
                            for sm in selected_mods:
                                mp = os.path.join(mod_dir, sm)
                                for f in os.listdir(mp):
                                    if f.lower().endswith(VALID_EXTS):
                                        mod_params.extend(
                                            ["-file", os.path.join(mp, f)]
                                        )
                            break
                    except Exception as e:
                        print(f"Fehler aufgetreten: {e}")
                        print(
                            f"            {Colors.RED}Ungültige Auswahl!{Colors.WHITE}"
                        )
                        time.sleep(1)

    # --- 3. STARTVORBEREITUNG & DEBUG ---
    engine_exe = get_engine_path()
    if not os.path.exists(engine_exe):
        print(
            f"\n {Colors.RED}Fehler: Engine nicht gefunden: {engine_exe}{Colors.WHITE}"
        )
        time.sleep(4)
        return

    cmd = (
        [engine_exe, "+logfile", "logfile.txt", "-iwad", os.path.join(IWAD_DIR, core)]
        + file_params
        + mod_params
        + extra_params
    )

    clear_screen()
    print(f"\n {Colors.GREEN}S T A R T E   E N G I N E{Colors.WHITE}\n {'-'*28}")
    print(f" KARTE : {Colors.CYAN}{mapname}{Colors.WHITE}")
    print(f" IWAD  : {Colors.CYAN}{display_core}{Colors.WHITE}")
    print(f" MOD   : {Colors.CYAN}{mod_name}{Colors.WHITE}\n {'-'*28}")

    if DEBUG_MODE:
        print(f"\n {Colors.MAGENTA}=== DEBUG: BEFEHL ==={Colors.WHITE}")
        print(f" {Colors.CYAN}{' '.join(cmd)}{Colors.WHITE}\n")

        # Abbruch-Abfrage
        ans = input(
            f" {Colors.YELLOW}ENTER zum Starten, '0' zum Abbruch: {Colors.WHITE}"
        ).strip()
        if ans == "0":
            print(f"\n {Colors.RED}[!] Start abgebrochen.{Colors.WHITE}")
            time.sleep(1)
            return

    # --- 4. START ---
    start_time = datetime.now()
    try:
        try:

            while msvcrt.kbhit():
                msvcrt.getch()
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass

        subprocess.run(cmd)
    except Exception as e:
        print(f"\n {Colors.RED}Fehler beim Starten: {e}{Colors.WHITE}")
        time.sleep(4)
        return

    end_time = datetime.now()

    # --- 5. STATS SPEICHERN ---
    delta_seconds = int((end_time - start_time).total_seconds())
    save_total_seconds(get_total_seconds() + delta_seconds)

    today_str = datetime.now().strftime("%d.%m.%Y")
    update_csv_playtime(map_id, delta_seconds // 60, last_played=today_str)

    if SHOW_STATS:
        analyze_session(
            os.path.join(BASE_DIR, "logfile.txt"), map_id, mapname, delta_seconds
        )

    print(
        f"\n{Colors.MAGENTA}[SYSTEM]{Colors.WHITE} Spiel beendet. Kehre zum Menü zurück..."
    )
    time.sleep(0.3)
    try:
        while msvcrt.kbhit():
            msvcrt.getch()
    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        pass


# ============================================================================
# MAIN MENU
# ============================================================================


def format_entry_clean(item, width, l_id, name_color, is_col4=False):
    if not item or item[0] == "EMPTY":
        return " " * width
    raw_name, d_id = item[0], str(item[1]).upper()

    d_id_padded = d_id

    # --- FARBEN ---
    if is_col4:
        id_color = Colors.YELLOW
        if d_id.startswith("H") and not d_id.startswith("HX"):
            final_name_color = Colors.YELLOW  # Heretic = Gelb
        elif d_id.startswith("X") or d_id.startswith("HX"):
            final_name_color = Colors.YELLOW  # Hexen = Gelb
        elif d_id.startswith("W"):
            final_name_color = Colors.CYAN  # Wolfenstein = Cyan
        elif d_id.startswith("T"):
            final_name_color = Colors.WHITE  # Testmap = Weiß
        else:
            final_name_color = Colors.WHITE
    else:
        id_color = Colors.CYAN
        final_name_color = name_color

    clean_name = raw_name
    if " - " in raw_name[:10]:
        clean_name = raw_name.split(" - ", 1)[-1]
    clean_name = clean_name.replace("__L__", "").replace("[L]", "").strip()

    styled_text = clean_name.replace(
        "[C]", f"{Colors.CYAN}[C]{final_name_color}"
    ).replace("[M]", f"{Colors.RED}[M]{final_name_color}")

    p_char = "→" if (l_id and str(l_id) == d_id) else " "
    visible = f"{p_char}[{d_id_padded}] {clean_name}"

    pad = width - real_len(visible)

    return f"{Colors.CYAN}{p_char}{Colors.GRAY}[{id_color}{d_id_padded}{Colors.GRAY}]{final_name_color} {styled_text}{Colors.WHITE}{' ' * max(0, pad)}"


def main():
    """Hauptmenü des Launchers - Die vollständige Schaltzentrale"""
    global TERMINAL_WIDTH, USE_MODS, SHOW_STATS, DEBUG_MODE

    # 1. Start-Vorbereitungen
    initial_setup()
    load_settings()
    repair_map_indices()
    last_error = ""

    while True:
        # 2. DATEN LADEN UND SPALTEN-LOGIK
        blocks = load_maps()
        col1, pwads, col4_raw = blocks[1], blocks[2], blocks[3]

        # PWAD-Liste für die zweispaltige Anzeige in der Mitte aufteilen
        col2, col3 = [], []
        half = math.ceil(len(pwads) / 2)
        for i in range(half):
            col2.append(pwads[i])
            col3.append(pwads[i + half] if i + half < len(pwads) else None)

        # Hilfsfunktion zur Ermittlung der längsten Zeile pro Spalte
        def get_max_len(col):
            max_l = 0
            for item in col:
                if item and item[0] != "EMPTY":
                    item_len = real_len(item[0].replace("__L__", "").replace("[L]", ""))
                    if item_len > max_l:
                        max_l = item_len
            return max_l

        # 3. DYNAMISCHE BREITENBERECHNUNG
        w1 = max(30, get_max_len(col1) + 8)
        w2 = max(30, get_max_len(col2) + 8)
        w3 = max(30, get_max_len(col3) + 8)
        w4 = max(45, get_max_len(col4_raw) + 8)

        calculated_width = w1 + w2 + w3 + w4 + 15
        TERMINAL_WIDTH = max(165, calculated_width)

        resize_terminal(TERMINAL_WIDTH, 60)
        term_width = os.get_terminal_size().columns - 2
        clear_screen()

        # 4. SYSTEM-INFOS & UPDATES
        check_launcher_update(auto=True)
        display_time = format_time(get_total_seconds())
        last_id = get_last_played_id_from_csv()
        engine_version = get_engine_version(get_engine_path())
        uzdoom_update, _ = check_uzdoom_update()
        upd = (
            f" {Colors.MAGENTA}[U]{Colors.WHITE}"
            if (uzdoom_update and CURRENT_ENGINE == "uzdoom")
            else ""
        )

        # 5. HEADER ZEICHNEN
        def format_head(text, width):
            return text + (" " * max(0, width - real_len(text)))

        h1_t = f"{Colors.CYAN}IWADS{Colors.WHITE}"
        h2_t, h3_t = (
            f"{Colors.CYAN}PWADS{Colors.WHITE}",
            f"{Colors.CYAN}PWADS{Colors.WHITE}",
        )
        h4_t = f"{Colors.CYAN}HERETIC / HEXEN / WOLFENSTEIN / TEST{Colors.WHITE}"

        header_content = (
            f" {format_head(h1_t, w1)} {Colors.GRAY}│{Colors.WHITE} "
            f"{format_head(h2_t, w2)} {Colors.GRAY}│{Colors.WHITE} "
            f"{format_head(h3_t, w3)} {Colors.GRAY}│{Colors.WHITE} "
            f"{h4_t}"
        )

        i_width = term_width - 2
        print(f"\n {Colors.GRAY}╭{'─' * i_width}╮")
        print(
            f" {Colors.GRAY}│{Colors.WHITE}{header_content}{' ' * max(0, i_width - real_len(header_content))}{Colors.GRAY}│"
        )
        print(f" {Colors.GRAY}╰{'─' * i_width}╯{Colors.WHITE}")

        # 6. ZEICHNEN DER SPALTEN
        max_idx = max(25, len(col1), len(col2), len(col3), len(col4_raw))
        for i in range(max_idx):
            d1, d2, d3, d4 = (
                col1[i] if i < len(col1) else None,
                col2[i] if i < len(col2) else None,
                col3[i] if i < len(col3) else None,
                col4_raw[i] if i < len(col4_raw) else None,
            )

            r1 = format_entry_clean(d1, w1, last_id, Colors.RED)
            r2 = format_entry_clean(d2, w2, last_id, Colors.GREEN)
            r3 = format_entry_clean(d3, w3, last_id, Colors.GREEN)
            r4 = format_entry_clean(d4, w4, last_id, Colors.WHITE, is_col4=True)

            print(
                f"   {r1} {Colors.GRAY}│{Colors.WHITE} {r2} {Colors.GRAY}│{Colors.WHITE} {r3} {Colors.GRAY}│{Colors.WHITE} {r4}"
            )

        # 7. STATISTIKEN & FUSSZEILE
        mod_count = 0
        for s in ["doom", "heretic", "hexen"]:
            p = os.path.join(BASE_DIR, "mods", s)
            if os.path.isdir(p):
                mod_count += len(
                    [d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))]
                )

        total_m = (
            len(col1) + len(pwads) + len([x for x in col4_raw if x and x[0] != "EMPTY"])
        )
        all_entries = col1 + pwads + [x for x in col4_raw if x and x[0] != "EMPTY"]
        done_count = sum(1 for m in all_entries if m and "[C]" in str(m[0]))
        done_percent = (done_count / total_m * 100) if total_m > 0 else 0

        m_on = (
            f"{Colors.GREEN}ON{Colors.WHITE}"
            if USE_MODS
            else f"{Colors.RED}OFF{Colors.WHITE}"
        )
        s_on = (
            f"{Colors.GREEN}ON{Colors.WHITE}"
            if SHOW_STATS
            else f"{Colors.RED}OFF{Colors.WHITE}"
        )
        d_on = (
            f"{Colors.GREEN}ON{Colors.WHITE}"
            if DEBUG_MODE
            else f"{Colors.RED}OFF{Colors.WHITE}"
        )

        p_maps = f"{Colors.CYAN}KARTEN:{Colors.WHITE} {total_m} {Colors.GRAY}| {Colors.RED}IWAD{Colors.WHITE} {len(col1)} {Colors.GRAY}│{Colors.WHITE} {Colors.GREEN}PWAD{Colors.WHITE} {len(pwads)} {Colors.GRAY}│{Colors.WHITE} {Colors.CYAN}Extras{Colors.WHITE} {len([x for x in col4_raw if x and x[0] != 'EMPTY'])}"
        p_done = f"{Colors.CYAN}DONE:{Colors.WHITE} {done_count} {Colors.GRAY}({Colors.GREEN}{done_percent:.1f}%{Colors.WHITE}{Colors.GRAY}){Colors.WHITE}"
        p_time = f"{Colors.CYAN}ZEIT:{Colors.WHITE} {display_time}"
        p_eng = f"{Colors.CYAN}ENGINE:{Colors.WHITE} {Colors.BLUE}{CURRENT_ENGINE}{Colors.WHITE} {engine_version}{upd} {Colors.GRAY}│{Colors.WHITE} {Colors.CYAN}MODS:{Colors.WHITE} {mod_count}"
        p_mods = f"{Colors.YELLOW}[/M]{Colors.WHITE} Mod {m_on} {Colors.YELLOW}[/S]{Colors.WHITE} Stats {s_on} {Colors.YELLOW}[/D]{Colors.WHITE} Debug {d_on}"

        foot_core = f"{p_maps}  {Colors.GRAY}│{Colors.WHITE}  {p_done}  {Colors.GRAY}│{Colors.WHITE}  {p_time}  {Colors.GRAY}│{Colors.WHITE}  {p_eng}  {Colors.GRAY}│{Colors.WHITE}  {p_mods}"
        f_width = term_width - 4
        f_line = (
            (" " * (max(0, f_width - real_len(foot_core)) // 2))
            + foot_core
            + (
                " "
                * (
                    max(0, f_width - real_len(foot_core))
                    - (max(0, f_width - real_len(foot_core)) // 2)
                )
            )
        )

        print(
            f" {Colors.GRAY}╭{'─' * f_width}╮\n {Colors.GRAY}│{Colors.WHITE}{f_line}{Colors.GRAY}│\n {Colors.GRAY}╰{'─' * f_width}╯{Colors.WHITE}"
        )

        # 8. BEFEHLSLISTE
        cmds = [
            f"{Colors.YELLOW}[0]{Colors.WHITE} Beenden",
            f"{Colors.YELLOW}[?]{Colors.WHITE} Zufall",
            f"{Colors.YELLOW}[R]{Colors.WHITE} Reset",
            f"{Colors.YELLOW}[C]{Colors.WHITE} Installer",
            f"{Colors.YELLOW}[D]{Colors.WHITE} DoomWorld",
            f"{Colors.YELLOW}[ID]c{Colors.WHITE} Clear",
            f"{Colors.YELLOW}[ID]m{Colors.WHITE} Skip",
            f"{Colors.YELLOW}[ID]x{Colors.WHITE} Delete",
            f"{Colors.YELLOW}[E]{Colors.WHITE} Engine",
        ]
        print(
            " " * max(0, (term_width - real_len("   ".join(cmds))) // 2)
            + "   ".join(cmds)
            + "\n"
        )

        if last_error:
            print(
                f"     {Colors.RED}Fehler: '{Colors.YELLOW}{last_error}{Colors.RED}' ungültig.{Colors.WHITE}"
            )
            last_error = ""
        else:
            print()

        # 9. EINGABE & PUFFER-SCHUTZ
        try:

            while msvcrt.kbhit():
                msvcrt.getch()
        except Exception as e:
            print(f"Fehler aufgetreten: {e}")
            pass

        choice = (
            input(
                f"     {Colors.YELLOW}ID ODER ENTER für ({Colors.MAGENTA}{last_id}{Colors.YELLOW}): {Colors.WHITE}"
            )
            .strip()
            .lower()
        )

        # 10. LOGIK-VERARBEITUNG
        if choice == "0":
            sys.exit(0)
        if choice == "e":
            select_engine()
            save_settings()
            continue
        if choice == "c":
            run_installer()
            continue
        if choice == "d":
            search_doomworld()
            continue
        if choice == "r":
            subprocess.Popen(
                [sys.executable, os.path.join(BASE_DIR, "doom.py")],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            sys.exit(0)

        if choice == "/u":
            check_launcher_update(auto=False)
            continue
        if choice == "/m":
            USE_MODS = not USE_MODS
            save_settings()
            continue
        if choice == "/s":
            SHOW_STATS = not SHOW_STATS
            save_settings()
            continue
        if choice == "/d":
            DEBUG_MODE = not DEBUG_MODE
            save_settings()
            continue

        # Zufall
        if choice == "?":
            all_m = [i for b in blocks.values() for i in b if i and i[0] != "EMPTY"]
            if all_m:
                s = random.choice(all_m)
                print(
                    f"\n    {Colors.MAGENTA}Zufall: {Colors.CYAN}{s[1]}{Colors.WHITE}"
                )
                time.sleep(2)
                launch_game(s)
            continue

        # Letzte ID bei leerem Enter
        if choice == "":
            if last_id:
                choice = str(last_id)
            else:
                continue

        # Suffix-Kommandos (x, c, m)
        if len(choice) > 1 and choice[-1] in "xcm":
            tid = choice[:-1].upper()
            if choice.endswith("x"):
                uninstall_map(tid)
            elif choice.endswith("c"):
                toggle_map_clear(tid)
            elif choice.endswith("m"):
                toggle_mod_skip(tid)
            continue

        # Reguläre Suche nach Map-ID
        selected_map = None
        for b in blocks.values():
            for it in b:
                if it and it[1].lower() == choice:
                    selected_map = it
                    break
            if selected_map:
                break

        if selected_map:
            launch_game(selected_map)
        else:
            last_error = choice


# ============================================================================
# START
# ============================================================================

if __name__ == "__main__":
    # Terminal vorbereiten
    resize_terminal(110, 35)
    os.system("")  # Aktiviert ANSI-Farben unter Windows
    load_settings()

    try:
        main()

    except KeyboardInterrupt:
        # Normales Beenden durch STRG+C
        print(
            f"\n\n  {Colors.YELLOW}Launcher wurde durch Benutzer beendet.{Colors.WHITE}"
        )
        sys.exit(0)

    except Exception as e:
        print(f"Fehler aufgetreten: {e}")
        clear_screen()
        print(f"{Colors.RED}" + "=" * 60)
        print("KRITISCHER SYSTEMFEHLER")
        print("=" * 60 + f"{Colors.WHITE}\n")

        traceback.print_exc()

        print(f"\n{Colors.RED}" + "=" * 60 + f"{Colors.WHITE}")
        print(f"\n{Colors.YELLOW}[!] Der Launcher ist abgestürzt.{Colors.WHITE}")
        print("Dies passiert oft nach einem fehlerhaften Update oder bei CSV-Fehlern.")

        print(
            f"\n{Colors.CYAN}Möchtest du ein Backup wiederherstellen (Rollback)? (j/n){Colors.WHITE}"
        )

        rettung = input(f" {Colors.GRAY}> {Colors.WHITE}").strip().lower()

        if rettung == "j":
            rollback_launcher()
        else:
            print(
                f"\n{Colors.GRAY}Der Launcher wird ohne Änderungen beendet.{Colors.WHITE}"
            )
            input("Drücke ENTER zum Schließen...")
            sys.exit(1)
