import os
import requests
import yaml
import json # Diperlukan untuk parsing data dari script
import re # Diperlukan untuk mencari pola data
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


def scrape_embedded_script(source_config):
    """
    Fungsi untuk scraping data yang ada di dalam tag <script>.
    Ini digunakan ketika tidak ada API yang jelas.
    """
    try:
        url = source_config['url']
        search_keyword = source_config.get('search_keyword')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"DEBUG: Mengunduh halaman: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cari semua tag <script>
        scripts = soup.find_all('script')
        target_script_content = None
        
        print(f"DEBUG: Mencari script yang mengandung keyword '{search_keyword}'...")
        for script in scripts:
            if script.string and search_keyword in script.string:
                target_script_content = script.string
                break
        
        if not target_script_content:
            print(f"ERROR: Tidak menemukan script yang mengandung keyword '{search_keyword}'.")
            return None

        # Sekarang kita perlu parsing data dari string JavaScript.
        # Kita asumsikan data dalam format array JSON.
        # Contoh: var data = [["tanggal", "hari", "result_html"], ...];
        
        # Cari pola array 2D di dalam string
        # Pola: [[...],[...],...] yang diikuti oleh ;
        match = re.search(r'(\[\[.*?\]\])', target_script_content, re.DOTALL)
        
        if not match:
            print(f"ERROR: Tidak dapat menemukan pola array data di dalam script.")
            return None
            
        data_string = match.group(1)
        
        # Ubah string menjadi list Python
        # Ganti single quote dengan double quote agar valid JSON
        data_string = data_string.replace("'", '"')
        data_list = json.loads(data_string)
        
        if not data_list or len(data_list) == 0:
            print(f"ERROR: Array data kosong.")
            return None
            
        # Ambil baris pertama (hasil terbaru)
        first_row_data = data_list[0]
        
        tanggal = first_row_data[0].strip()
        hari = first_row_data[1].strip()
        result_html = first_row_data[2]
        
        # Gunakan BeautifulSoup untuk mengekstrak angka dari HTML result
        soup_result = BeautifulSoup(result_html, 'html.parser')
        result_spans = soup_result.find_all('span', class_='bolaresultmodif')
        
        if not result_spans:
            print(f"ERROR: Tag span result tidak ditemukan di data script.")
            return None
            
        angka_list = [span.text for span in result_spans]
        angka_str = ' '.join(angka_list)

        formatted_output = f"{tanggal} {hari} {angka_str}"
        print(f"SUCCESS: Data berhasil di-scrape dari script: {formatted_output}")
        return formatted_output

    except Exception as e:
        print(f"ERROR: Terjadi error tak terduga saat scraping dari script: {e}")
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

                if scraper_type == 'embedded_script':
                    latest_data = scrape_embedded_script(source)
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
