import json
import requests
import os
from urllib.parse import urlparse

# Images klasörünü oluştur
assets_folder = '../assets'
if not os.path.exists(assets_folder):
    os.makedirs(assets_folder)

# Roket bilgilerini oku
with open('../data/rockets_info.json', 'r', encoding='utf-8') as f:
    rockets_info = json.load(f)

print("🚀 Roket görselleri indiriliyor...")

for rocket in rockets_info:
    rocket_name = rocket['name']
    images = rocket['flickr_images']
    
    print(f"\n📸 {rocket_name} için {len(images)} görsel indiriliyor...")
    
    # Her roket için klasör oluştur
    rocket_folder = f"../assets/images/{rocket_name.replace(' ', '_')}"
    if not os.path.exists(rocket_folder):
        os.makedirs(rocket_folder)
    
    # Görselleri indir
    for i, image_url in enumerate(images):
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                # Dosya uzantısını belirle
                parsed_url = urlparse(image_url)
                file_extension = os.path.splitext(parsed_url.path)[1]
                if not file_extension:
                    file_extension = '.jpg'  # Varsayılan
                
                # Dosya adını oluştur
                filename = f"{rocket_folder}/image_{i+1}{file_extension}"
                
                # Görseli kaydet
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"  ✅ {filename} indirildi")
            else:
                print(f"  ❌ {image_url} indirilemedi (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"  ❌ {image_url} indirilirken hata: {e}")

print("\n🎉 Tüm görseller indirildi!")
print("📁 Görseller 'images' klasöründe saklanıyor.") 