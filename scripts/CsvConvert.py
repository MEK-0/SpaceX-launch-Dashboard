import requests
import csv
import json
from datetime import datetime

# SpaceX resmi API'si
url = "https://api.spacexdata.com/v4/launches"

try:
    print("SpaceX API'den veri alınıyor...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # CSV için veri 
        rows = []
        for launch in data:
            
            row = {
                "id": launch.get("id", ""),
                "name": launch.get("name", ""),
                "flight_number": launch.get("flight_number", ""),
                "date_utc": launch.get("date_utc", ""),
                "date_local": launch.get("date_local", ""),
                "success": launch.get("success", ""),
                "details": launch.get("details", ""),
                "rocket": launch.get("rocket", ""),
                "launchpad": launch.get("launchpad", ""),
                "upcoming": launch.get("upcoming", ""),
                "tbd": launch.get("tbd", ""),
                "net": launch.get("net", ""),
                "window": launch.get("window", ""),
                "static_fire_date_utc": launch.get("static_fire_date_utc", ""),
                "auto_update": launch.get("auto_update", ""),
                "launch_library_id": launch.get("launch_library_id", ""),
                "date_precision": launch.get("date_precision", ""),
                "date_unix": launch.get("date_unix", "")
            }
            rows.append(row)
        

        if rows:
            with open("../data/spacex_launches.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"spacex_launches.csv oluşturuldu: {len(rows)} fırlatma kaydedildi.")
            print(f"İlk fırlatma: {rows[0]['name']}")
            print(f"Son fırlatma: {rows[-1]['name']}")
        else:
            print("Hiç fırlatma verisi bulunamadı.")
            
    else:
        print(f"API hatası: {response.status_code}")
        print(f"Hata mesajı: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Bağlantı hatası: {e}")
except json.JSONDecodeError as e:
    print(f"JSON çözümleme hatası: {e}")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
