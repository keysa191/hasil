import os
import requests
import yaml
from bs4 import BeautifulSoup
from github import Github
import traceback # Impor traceback untuk melihat detail error

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


def scrape_scanangka_api(source_config):
    """(Fungsi ini tidak diubah, hanya menambah print untuk debugging)"""
    try:
        api_url = "https://srv1.scanangka.blog/ajax/getresult"
        pasaran = source_config['api_pasaran']
        main_page_url = source_config['url']
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        print(f"DEBUG: Mengunjungi halaman utama untuk dapat session: {main_page_url}")
        response = session.get(main_page_url, timeout=10)
        response.raise_for_status()
        
        api_headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': main_page_url
        }
        
        payload = { 'pasaran': pasaran }
        
        print(f"DEBUG: Memanggil API untuk pasaran: {pasaran}")
        api_response = session.post(api_url, data=payload, headers=api_headers, timeout=10)
        api_response.raise_for_status()
        
        data_json = api_response.json()
        
        if not data_json.get('data') or len(data_json['data']) == 0:
            print(f"ERROR: Tidak ada data diterima dari API.")
            return None
            
        first_row_data = data_json['data'][0]
        tanggal = first_row_data[0].strip()
        hari = first_row_data[1].strip()
        result_html = first_row_data[2]
        
        soup = BeautifulSoup(result_html, 'html.parser')
        result_spans = soup.find_all('span', class_='bolaresultmodif')
        
        if not result_spans:
            print(f"ERROR: Tag span result tidak ditemukan di response API.")
            return None
            
        angka_list = [span.text for span in result_spans]
        angka_str = ' '.join(angka_list)

        formatted_output = f"{tanggal} {hari} {angka_str}"
        print(f"SUCCESS: Data berhasil di-scrape dari API: {formatted_output}")
        return formatted_output

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Gagal memanggil API: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Terjadi error tak terduga saat parsing API: {e}")
        traceback.print_exc() # Cetak detail error
        return None


def update_github_file(source_config, new_content):
    """(Fungsi ini tidak diubah, hanya menambah print untuk debugging)"""
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

                if scraper_type == 'scanangka_api':
                    latest_data = scrape_scanangka_api(source)
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
