import os
import requests
from bs4 import BeautifulSoup
from github import Github

# --- KONFIGURASI ---
# 1. URL halaman web yang ingin Anda scrap. ANDA HARUS MENGISI INI.
URL_TO_SCRAPE = "https://srv1.scanangka.blog/keluaranharian?pasaran=sydney" 

# 2. Nama repositori Anda (format: 'pemilik/repo')
GITHUB_REPO = "keysa191/hasil"

# 3. Path file yang akan diupdate di repositori
GITHUB_FILE_PATH = "datasdp"

# 4. Personal Access Token (PAT) Anda. Akan diambil dari secret GitHub Actions.
#    JANGAN Hardcode token di sini!
GITHUB_TOKEN = os.environ.get("GH_PAT")


def scrape_latest_result():
    """
    Fungsi untuk melakukan scraping data terbaru dari URL yang ditentukan.
    Mengembalikan string dengan format "tanggal hari x x x x" atau None jika gagal.
    """
    try:
        # Mengambil konten halaman
        response = requests.get(URL_TO_SCRAPE, timeout=10)
        response.raise_for_status()  # Memastikan request berhasil

        # Parsing HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Menemukan tabel berdasarkan ID
        table = soup.find('table', {'id': 'DataTables_Table_0'})
        if not table:
            print("Error: Tabel dengan id 'DataTables_Table_0' tidak ditemukan.")
            return None

        # Mengambil baris pertama di dalam tbody (hasil terbaru)
        first_row = table.find('tbody').find('tr')
        if not first_row:
            print("Error: Tidak ada baris data (tr) di dalam tbody.")
            return None

        # Mengambil sel-sel (td) dari baris tersebut
        cells = first_row.find_all('td')
        if len(cells) < 3:
            print("Error: Struktur baris tidak sesuai, kurang dari 3 kolom.")
            return None

        # 1. Ekstrak Tanggal
        tanggal = cells[0].text.strip()

        # 2. Ekstrak Hari
        hari = cells[1].text.strip()

        # 3. Ekstrak Angka Result
        result_spans = cells[2].find_all('span', class_='bolaresultmodif')
        if not result_spans:
            print("Error: Tag span dengan class 'bolaresultmodif' tidak ditemukan.")
            return None
        
        angka_list = [span.text for span in result_spans]
        angka_str = ' '.join(angka_list)

        # Format output sesuai permintaan
        formatted_output = f"{tanggal} {hari} {angka_str}"
        print(f"Data berhasil di-scrape: {formatted_output}")
        return formatted_output

    except requests.exceptions.RequestException as e:
        print(f"Error saat mengambil URL: {e}")
        return None
    except Exception as e:
        print(f"Terjadi error tak terduga saat scraping: {e}")
        return None


def update_github_file(new_content):
    """
    Fungsi untuk mengupdate file di repositori GitHub menggunakan GitHub API.
    """
    if not GITHUB_TOKEN:
        print("Error: GH_PAT token tidak diatur. Tidak bisa mengupdate GitHub.")
        return

    try:
        # Inisialisasi koneksi ke GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        # Dapatkan file yang akan diupdate
        file = repo.get_contents(GITHUB_FILE_PATH)
        
        # Update file dengan konten baru
        # Pesan commit akan otomatis menggunakan tanggal yang di-scrape
        commit_message = f"Update data hasil: {new_content}"
        repo.update_file(
            path=GITHUB_FILE_PATH,
            message=commit_message,
            content=new_content,
            sha=file.sha
        )
        print(f"File '{GITHUB_FILE_PATH}' di repositori '{GITHUB_REPO}' berhasil diupdate.")
        print(f"Link commit: https://github.com/{GITHUB_REPO}/commits/main")

    except Exception as e:
        print(f"Gagal mengupdate file di GitHub: {e}")


# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    if URL_TO_SCRAPE == "URL_HALAMAN_WEB_ANDA_DISINI":
        print("Error: Silakan ganti 'URL_HALAMAN_WEB_ANDA_DISINI' dengan URL yang benar di dalam skrip.")
    else:
        latest_data = scrape_latest_result()
        if latest_data:
            update_github_file(latest_data)
