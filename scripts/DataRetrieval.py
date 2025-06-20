import requests
import json

# SpaceX API'den en son fırlatma verisi
url = "https://api.spacexdata.com/v4/launches/latest"
response = requests.get(url)
data = response.json()

# Gösterilecek bazı alanlar
print("Mission Name:", data["name"])
print("Launch Date:", data["date_utc"])
print("Details:", data["details"])

# Roket ID'si (ek bilgi almak için)
print("Rocket ID:", data["rocket"])

# Önce tüm veri anahtarlarını görelim
print("\nMevcut veri anahtarları:")
for key in data.keys():
    print(f"- {key}")

# Timeline'ı kontrol et ve görüntüle
print("\nTimeline:")
if "timeline" in data and data["timeline"]:
    for key, value in data["timeline"].items():
        print(f"{key} → {value} saniye")
else:
    print("Timeline verisi mevcut değil")

# Payload'ları kontrol et ve görüntüle
print("\nPayloads:")
if "payloads" in data and data["payloads"]:
    for payload in data["payloads"]:
        print(f"Payload ID: {payload}")
else:
    print("Payload verisi mevcut değil")
