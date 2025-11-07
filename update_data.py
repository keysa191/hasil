import os
import requests
import yaml
from bs4 import BeautifulSoup
from github import Github

# --- KONFIGURASI UTAMA ---
CONFIG_FILE = "config.yml"
GITHUB_REPO = "keysa191/hasil"
GITHUB_TOKEN = os.environ.get("GH_PAT")


def load_config():
    """Memuat konfigurasi dari file YAML."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: File konfigurasi '{CONFIG_FILE}' tidak ditemukan.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing file YAML: {e}")
        return None


def scrape_scanangka_api(source_config):
    """
    Fungsi khusus untuk website scanangka.blog yang menggunakan API.
    Ini adalah metode yang lebih andal.
    """
    try:
        api_url = "https://srv1.scanangka.blog/ajax/getresult"
        pasaran = source_config['api_pasaran']
        
        # Header untuk meniru request dari browser asli
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest' # Header penting untuk request Ajax
        }
        
        # Data yang akan dikirim ke API
        payload = {
            'pasaran': pasaran
        }
        
        # Melakukan request POST ke API
        response = requests.post(api_url, data=payload, headers=headers, timeout=10)
        response.raise_for_status() # Akan error jika status bukan 200 OK
        
        data_json = response.json()
        
        # Pastikan data ada dan tidak kosong
        if not data_json.get('data') or len(data_json['data']) == 0:
            print(f"[{source_config['name']}] Error: Tidak ada data diterima dari API.")
            return None
            
        # Ambil baris pertama (hasil terbaru)
        first_row_data = data_json['data'][0]
        
        # Ekstrak data dari baris
        tanggal = first_row_data[0].strip()
        hari = first_row_data[1].strip()
        result_html = first_row_data[2]
        
        # Gunakan BeautifulSoup untuk mengekstrak angka dari HTML result
        soup = BeautifulSoup(result_html, 'html.parser')
        result_spans = soup.find_all('span', class_='bolaresultmodif')
        
        if not result_spans:
            print(f"[{source_config['name']}] Error: Tag span result tidak ditemukan di response API.")
            return None
            
        angka_list = [span.text for span in result_spans]
        angka_str = ' '.join(angka_list)

        formatted_output = f"{tanggal} {hari} {angka_str}"
        print(f"[{source_config['name']}] Data berhasil di-scrape dari API: {formatted_output}")
        return formatted_output

    except requests.exceptions.RequestException as e:
        print(f"[{source_config['name']}] Error saat memanggil API: {e}")
        return None
    except Exception as e:
        print(f"[{source_config['name']}] Terjadi error tak terduga saat parsing API: {e}")
        return None


def update_github_file(source_config, new_content):
    """Mengupdate file spesifik di repositori GitHub."""
    if not GITHUB_TOKEN:
        print("Error: GH_PAT token tidak diatur. Tidak bisa mengupdate GitHub.")
        return

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = source_config['target_file']
        
        try:
            file = repo.get_contents(file_path)
            repo.update_file(
                path=file_path,
                message=f"Update {source_config['name']}: {new_content}",
                content=new_content,
                sha=file.sha
            )
            print(f"[{source_config['name']}] File '{file_path}' berhasil diupdate.")
        except:
            repo.create_file(
                path=file_path,
                message=f"Create {source_config['name']}: {new_content}",
                content=new_content
            )
            print(f"[{source_config['name']}] File '{file_path}' berhasil dibuat.")

    except Exception as e:
        print(f"[{source_config['name']}] Gagal mengupdate file di GitHub: {e}")


# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    sources = load_config()
    if not sources:
        print("Skrip dihentikan karena tidak ada konfigurasi yang valid.")
    else:
        print(f"Menemukan {len(sources)} sumber data untuk diproses.")
        for source in sources:
            print(f"\n--- Memproses sumber: {source.get('name', 'Tanpa Nama')} ---")
            
            # Pilih scraper berdasarkan tipe yang ada di config
            scraper_type = source.get('scraper_type')
            latest_data = None

            if scraper_type == 'scanangka_api':
                latest_data = scrape_scanangka_api(source)
            # Anda bisa menambahkan elif untuk tipe scraper lain di sini
            # elif scraper_type == 'default':
            #     latest_data = scrape_default(source)
            else:
                print(f"Scraper type '{scraper_type}' tidak dikenal. Lewati.")
                continue

            if latest_data:
                update_github_file(source, latest_data)
        
        print("\n--- Semua proses selesai. ---")
