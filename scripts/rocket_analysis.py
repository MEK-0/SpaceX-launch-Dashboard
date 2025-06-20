import pandas as pd
import requests
import json

# CSV'yi oku
df = pd.read_csv('../data/spacex_launches.csv')

# Kullanılan roket ID'lerini bul
rocket_ids = df['rocket'].unique()
print(f"Toplam {len(rocket_ids)} farklı roket ID'si bulundu:")

# Her roket ID'si için detaylı bilgi al
rockets_info = []

for rocket_id in rocket_ids:
    if pd.isna(rocket_id) or rocket_id == "":
        continue
        
    try:
        # SpaceX API'den roket bilgilerini al
        url = f"https://api.spacexdata.com/v4/rockets/{rocket_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            rocket_data = response.json()
            
            rocket_info = {
                'id': rocket_id,
                'name': rocket_data.get('name', 'Bilinmiyor'),
                'type': rocket_data.get('type', 'Bilinmiyor'),
                'active': rocket_data.get('active', False),
                'stages': rocket_data.get('stages', 0),
                'boosters': rocket_data.get('boosters', 0),
                'cost_per_launch': rocket_data.get('cost_per_launch', 0),
                'success_rate_pct': rocket_data.get('success_rate_pct', 0),
                'first_flight': rocket_data.get('first_flight', 'Bilinmiyor'),
                'country': rocket_data.get('country', 'Bilinmiyor'),
                'company': rocket_data.get('company', 'Bilinmiyor'),
                'description': rocket_data.get('description', 'Açıklama yok'),
                'wikipedia': rocket_data.get('wikipedia', ''),
                'flickr_images': rocket_data.get('flickr_images', [])
            }
            
            rockets_info.append(rocket_info)
            print(f"✅ {rocket_info['name']} - {rocket_info['type']}")
            
        else:
            print(f"❌ {rocket_id} için veri alınamadı")
            
    except Exception as e:
        print(f"❌ {rocket_id} için hata: {e}")

# Sonuçları JSON dosyasına kaydet
with open('../data/rockets_info.json', 'w', encoding='utf-8') as f:
    json.dump(rockets_info, f, ensure_ascii=False, indent=2)

print(f"\n{len(rockets_info)} roket bilgisi rockets_info.json dosyasına kaydedildi.")

# Özet bilgiler
print("\n=== ROKET ÖZETİ ===")
for rocket in rockets_info:
    print(f"🚀 {rocket['name']}")
    print(f"   Tür: {rocket['type']}")
    print(f"   Aktif: {'Evet' if rocket['active'] else 'Hayır'}")
    print(f"   Başarı Oranı: %{rocket['success_rate_pct']}")
    print(f"   İlk Uçuş: {rocket['first_flight']}")
    print(f"   Resim Sayısı: {len(rocket['flickr_images'])}")
    print() 