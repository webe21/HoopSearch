from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Inisialisasi Service untuk WebDriver dengan path yang benar
driver = webdriver.Chrome()

# URL dasar untuk scraping
base_url = 'https://iblindonesia.com/profile/player?season=39576&disp=all&team=all&position=all&per_page='

# Daftar untuk menyimpan nama pemain
player_names = []

# Loop untuk beberapa halaman
for page in range(1, 18):  # Ganti 4 dengan jumlah halaman yang ingin di-scrape
    url = base_url + str(page)
    print(f'Mengakses halaman: {url}')
    
    # Mengakses halaman
    driver.get(url)
    time.sleep(3)  # Tunggu beberapa detik agar halaman dimuat sepenuhnya
    
    # Mencari elemen nama pemain
    player_items = driver.find_elements(By.CLASS_NAME, 'player-item')
    
    # Mengecek apakah elemen ditemukan
    if not player_items:
        print(f'Tidak ada elemen yang ditemukan di halaman {page}')
    else:
        for player_item in player_items:
            player_name = player_item.find_element(By.TAG_NAME, 'span').text
            print(f'Nama pemain ditemukan: {player_name}')
            player_names.append(player_name)

# Menutup browser
driver.quit()

# Mengecek apakah daftar nama pemain kosong
if not player_names:
    print('Tidak ada nama pemain yang ditemukan')
else:
    # Mengonversi data ke format DataFrame
    data = pd.DataFrame({'Nama Pemain': player_names})

    # Mengekspor data ke file Excel
    data.to_excel('data_pemain_dengan_selenium.xlsx', index=False)
    print('Data berhasil diekspor ke data_pemain_dengan_selenium.xlsx')
