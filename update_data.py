# --- TES: Jika baris ini muncul di log, berarti file berhasil dibaca ---
print("--- SCRIPT LOADING ---")

import os
import requests
import yaml
from bs4 import BeautifulSoup
from github import Github
import traceback

# --- KONFIGURASI UTAMA ---
CONFIG_FILE = "config.yml"
GITHUB_REPO = "keysa191/hasil"
GITHUB_TOKEN = os.environ.get("GH_PAT")


def load_config():
    """Memuat konfigurasi dari file YAML."""
    print("DEBUG: Mencoba memuat file konfigurasi...")
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        print("DEBUG: File konfigurasi berhasil dimuat dan di-parse.")
        return config
    except FileNotFoundError:
        print(f"ERROR: File konfigurasi '{CONFIG_FILE}' tidak ditemukan.")
        return None
    except yaml.YAMLError as e:
        print(f"ERROR: Gagal parsing file YAML. Periksa indentasi dan sintaks. Detail error: {e}")
        return None


def scrape_static_table(source_config):
    """
    Fungsi untuk scraping data dari tabel HTML statis.
    """
    try:
        url = source_config['url']
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        
        print(f"DEBUG: Mengunduh halaman: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cari tabel berdasarkan class
        table = soup.find('table', class_='liveresult')
        
        if not table:
            print(f"ERROR: Tabel dengan class 'liveresult' tidak ditemukan.")
            return None

        tbody = table.find('tbody')
        if not tbody:
            print("ERROR: Tabel ditemukan, tetapi tidak memiliki tag <tbody>.")
            return None
            
        first_row = tbody.find('tr')
        if not first_row:
            print("ERROR: Tabel ditemukan, tetapi tidak ada baris data (<tr>) di dalam <tbody>.")
            return None

        cells = first_row.find_all('td')
        if len(cells) < 3:
            print(f"ERROR: Struktur baris tidak sesuai, hanya menemukan {len(cells)} kolom.")
            return None

        tanggal = cells[0].text.strip()
        hari = cells[1].text.strip()
        
        result_spans = cells[2].find_all('span', class_='bolaresultmodif')
        if not result_spans:
            print("ERROR: Tag span dengan class 'bolaresultmodif' tidak ditemukan di kolom result.")
            return None
        
        angka_list = [span.text for span in result_spans]
        angka_str = ' '.join(angka_list)

        formatted_output = f"{tanggal} {hari} {angka_str}"
        print(f"SUCCESS: Data berhasil di-scrape dari tabel: {formatted_output}")
        return formatted_output

    except Exception as e:
        print(f"ERROR: Terjadi error tak terduga saat scraping: {e}")
        traceback.print_exc()
        return None


def update_github_file(source_config, new_content):
    """Mengupdate file spesifik di repositori GitHub."""
    if not GITHUB_TOKEN:
        print("ERROR: GH_PAT token tidak diatur.")
        return

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = source_config['target_file']
        
        print(f"DEBUG: Mencoba mengupdate file '{file_path}' di GitHub...")
        try:
            file = repo.get_contents(file_path)
            repo.update_file(
                path=file_path,
                message=f"Update {source_config['name']}: {new_content}",
                content=new_content,
                sha=file.sha
            )
            print(f"SUCCESS: File '{file_path}' berhasil diupdate.")
        except:
            repo.create_file(
                path=file_path,
                message=f"Create {source_config['name']}: {new_content}",
                content=new_content
            )
            print(f"SUCCESS: File '{file_path}' berhasil dibuat.")

    except Exception as e:
        print(f"ERROR: Gagal mengupdate file di GitHub: {e}")
        traceback.print_exc()


# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    print("--- DEBUG: Script dimulai ---")
    try:
        sources = load_config()
        if not sources:
            print("DEBUG: Skrip dihentikan karena load_config() mengembalikan None.")
        else:
            print(f"DEBUG: Konfigurasi valid. Menemukan {len(sources)} sumber data.")
            for source in sources:
                print(f"\n--- Memproses sumber: {source.get('name', 'Tanpa Nama')} ---")
                
                scraper_type = source.get('scraper_type')
                latest_data = None

                if scraper_type == 'static_table':
                    latest_data = scrape_static_table(source)
                else:
                    print(f"WARNING: Scraper type '{scraper_type}' tidak dikenal. Lewati.")
                    continue

                if latest_data:
                    update_github_file(source, latest_data)
                else:
                    print(f"INFO: Tidak ada data yang berhasil di-scrape untuk sumber ini.")
            
            print("\n--- DEBUG: Semua proses selesai. ---")
    except Exception as e:
        print(f"\nCRITICAL ERROR: Terjadi error tak terduga di level utama skrip!")
        print(f"Error: {e}")
        traceback.print_exc()
