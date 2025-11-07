import os
import requests
import yaml # Library untuk membaca file YAML
from bs4 import BeautifulSoup
from github import Github

# --- KONFIGURASI UTAMA ---
# 1. Path ke file konfigurasi
CONFIG_FILE = "config.yml"

# 2. Nama repositori Anda (format: 'pemilik/repo')
GITHUB_REPO = "keysa191/hasil"

# 3. Personal Access Token (PAT). Akan diambil dari secret GitHub Actions.
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


def scrape_default(source_config):
    """
    Fungsi scraping default (seperti yang Anda minta sebelumnya).
    Mencari tabel dengan id 'DataTables_Table_0' dan memformatnya.
    """
    try:
        url = source_config['url']
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Selector spesifik untuk tabel Anda
        table = soup.find('table', {'id': 'DataTables_Table_0'})
        if not table:
            print(f"Error: Tabel dengan id 'DataTables_Table_0' tidak ditemukan di {url}")
            return None

        first_row = table.find('tbody').find('tr')
        if not first_row:
            print(f"Error: Tidak ada baris data di dalam tbody di {url}")
            return None

        cells = first_row.find_all('td')
        if len(cells) < 3:
            print(f"Error: Struktur baris tidak sesuai di {url}")
            return None

        tanggal = cells[0].text.strip()
        hari = cells[1].text.strip()
        
        result_spans = cells[2].find_all('span', class_='bolaresultmodif')
        if not result_spans:
            print(f"Error: Tag span result tidak ditemukan di {url}")
            return None
        
        angka_list = [span.text for span in result_spans]
        angka_str = ' '.join(angka_list)

        formatted_output = f"{tanggal} {hari} {angka_str}"
        print(f"[{source_config['name']}] Data berhasil di-scrape: {formatted_output}")
        return formatted_output

    except requests.exceptions.RequestException as e:
        print(f"[{source_config['name']}] Error saat mengambil URL: {e}")
        return None
    except Exception as e:
        print(f"[{source_config['name']}] Terjadi error tak terduga: {e}")
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
        
        # Cek apakah file ada, jika tidak, buat baru
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
            # Jika file tidak ditemukan (404 error), buat file baru
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
            
            # Di sini Anda bisa menambahkan logika if/elif untuk memilih scraper
            # berdasarkan source['scraper_type']
            if source.get('scraper_type') == 'default':
                latest_data = scrape_default(source)
            else:
                print(f"Scraper type '{source.get('scraper_type')}' tidak dikenal. Lewati.")
                continue

            if latest_data:
                update_github_file(source, latest_data)
        
        print("\n--- Semua proses selesai. ---")
