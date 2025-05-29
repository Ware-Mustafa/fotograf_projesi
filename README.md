# 🧠 Python OpenCV Yüz Tanıma Sistemi

Bu proje, Python dili ve OpenCV kütüphanesi kullanılarak geliştirilmiş basit ama hızlı bir **yüz tanıma ve eşleştirme sistemidir**.

## 🚀 Proje Özellikleri

- 📁 Kullanıcıdan iki klasör seçmesi istenir:
  - **Arama klasörü**: İçerisinde referans fotoğraflar bulunur.
  - **Çıktı klasörü**: Eşleşen fotoğrafların kopyaları buraya kaydedilir.
- 🔍 `cv2.CascadeClassifier` kullanılarak yüz tespiti yapılır.
- 🤝 `cv2.matchTemplate` ile yüzler arasında eşleşme aranır.
- ⚡ Hızlı ve verimli çalışır, yüz tarama işlemleri milisaniyeler içinde tamamlanır.
- 🧰 Tamamen açık kaynak, basit mantıkla herkesin kullanabileceği şekilde geliştirilmiştir.

## 🧪 Kullanılan Teknolojiler

- Python 3.x
- OpenCV (cv2)
- Haar Cascade Classifier
- 
## 🖼️ Fotoğraflar

| Arama Fotoğrafı | Eşleşen Sonuç |
|-----------------|----------------|
| <img src="https://github.com/user-attachments/assets/1249bf34-4884-472d-b05c-b6ee5fe3c675" width="300"/> | <img src="https://github.com/user-attachments/assets/d2426101-b073-43ee-9660-bbd66737031b" width="300"/> |


## ⚙️ Kurulum


```bash
pip install opencv-python
pip install opencv-python-headless
