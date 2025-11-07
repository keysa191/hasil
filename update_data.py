def scrape_scanangka_api(source_config):
    """
    Fungsi untuk website scanangka.blog yang menggunakan API dengan proteksi session.
    Prosesnya: 1. GET halaman utama untuk dapat cookie. 2. POST ke API menggunakan cookie.
    """
    try:
        # Buat session object untuk mempertahankan cookie
        session = requests.Session()
        
        # Header umum untuk meniru browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # --- Langkah 1: Kunjungi halaman utama untuk mendapatkan session cookie ---
        main_page_url = source_config['url']
        print(f"[{source_config['name']}] Mengunjungi halaman utama untuk mendapatkan session: {main_page_url}")
        response = session.get(main_page_url, timeout=10)
        response.raise_for_status()
        
        # --- Langkah 2: Siapkan dan panggil API ---
        api_url = "https://srv1.scanangka.blog/ajax/getresult"
        pasaran = source_config['api_pasaran']
        
        # Header khusus untuk request API
        api_headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': main_page_url # Header penting, menyatakan asal request
        }
        
        # Data yang akan dikirim ke API
        payload = {
            'pasaran': pasaran
        }
        
        print(f"[{source_config['name']}] Memanggil API untuk pasaran: {pasaran}")
        # Gunakan session.post() agar cookie otomatis terkirim
        api_response = session.post(api_url, data=payload, headers=api_headers, timeout=10)
        api_response.raise_for_status()
        
        data_json = api_response.json()
        
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
