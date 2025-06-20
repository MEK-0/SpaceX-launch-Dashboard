import pandas as pd
import matplotlib.pyplot as plt

# CSV'yi oku
df = pd.read_csv('spacex_launches.csv')

# Tarih sütununu datetime'a çevir
df['date_utc'] = pd.to_datetime(df['date_utc'], errors='coerce')
df = df.dropna(subset=['date_utc'])
df['year'] = df['date_utc'].dt.year

# 1. Yıllara göre fırlatma sayısı
years = df['year'].value_counts().sort_index()
plt.figure(figsize=(10,5))
years.plot(kind='bar')
plt.title('Yıllara Göre SpaceX Fırlatma Sayısı')
plt.xlabel('Yıl')
plt.ylabel('Fırlatma Sayısı')
plt.tight_layout()
plt.savefig('launches_per_year.png')
plt.close()

# 2. Başarılı ve başarısız fırlatma sayısı
success_counts = df['success'].value_counts(dropna=False)
plt.figure(figsize=(6,4))
success_counts.plot(kind='bar', color=['green','red','gray'])
plt.title('Başarılı ve Başarısız Fırlatma Sayısı')
plt.xlabel('Başarı Durumu (True=Başarılı, False=Başarısız, NaN=Bilinmiyor)')
plt.ylabel('Fırlatma Sayısı')
plt.tight_layout()
plt.savefig('success_vs_failure.png')
plt.close()

# 3. Yıllara göre başarı oranı
yearly = df.groupby('year')['success'].mean()
plt.figure(figsize=(10,5))
yearly.plot(marker='o')
plt.title('Yıllara Göre Başarı Oranı')
plt.xlabel('Yıl')
plt.ylabel('Başarı Oranı')
plt.ylim(0,1)
plt.tight_layout()
plt.savefig('success_rate_per_year.png')
plt.close()

print('Grafikler oluşturuldu:')
print('- launches_per_year.png')
print('- success_vs_failure.png')
print('- success_rate_per_year.png') 