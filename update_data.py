def scrape_static_table(source_config):
    """
    Fungsi untuk scraping data dari tabel HTML statis.
    Ini adalah pendekatan yang paling andal jika data sudah ada di HTML.
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
        
        # --- PERUBAHAN DI SINI ---
        # Cari tabel berdasarkan class, bukan ID
        table = soup.find('table', class_='liveresult')
        
        if not table:
            print(f"ERROR: Tabel dengan class 'liveresult' tidak ditemukan.")
            return None

        # Ambil baris pertama di dalam tbody (hasil terbaru)
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

        # Ekstrak data
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
