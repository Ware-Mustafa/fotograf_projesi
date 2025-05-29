import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import time
from threading import Thread
import shutil
from datetime import datetime
import sys

class UltimateFaceMatcher:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Yüz Tanıma Sistemi")
        self.root.geometry("1200x800")
        
        # Yüz tanıma modelini yükle
        self.face_cascade = self.load_cascade()
        if self.face_cascade is None:
            messagebox.showerror("Kritik Hata", "Yüz tanıma modeli yüklenemedi!\nLütfen 'haarcascade_frontalface_default.xml' dosyasını scriptin yanına kopyalayın.")
            self.root.destroy()
            return
        
        # Değişkenler
        self.folder_path = ""
        self.output_folder = ""
        self.camera_on = False
        self.cap = None
        self.target_face = None
        self.known_faces = []
        self.face_labels = []
        self.scanning = False
        self.match_threshold = 0.85
        
        # Türkçe karakter desteği için
        self.fix_unicode_paths()
        
        # GUI
        self.create_widgets()
    
    def fix_unicode_paths(self):
        """Windows'ta Unicode path sorunlarını çözer"""
        if os.name == 'nt':
            try:
                from ctypes import windll
                windll.kernel32.SetDllDirectoryW(None)
            except:
                pass
    
    def load_cascade(self):
        """Yüz tanıma modelini yükler (3 farklı yöntem dener)"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml'),
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
            'haarcascade_frontalface_default.xml'
        ]
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    cascade = cv2.CascadeClassifier(path)
                    if not cascade.empty():
                        print(f"Model başarıyla yüklendi: {path}")
                        return cascade
            except Exception as e:
                print(f"Yükleme hatası {path}: {str(e)}")
                continue
        
        return None
    
    def create_widgets(self):
        """Arayüzü oluşturur"""
        # Kontrol paneli
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(control_frame, text="Kaynak Klasör Seç", command=self.select_source_folder,
                font=("Helvetica", 12), bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Çıktı Klasörü Seç", command=self.select_output_folder,
                font=("Helvetica", 12), bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=5)
        
        self.btn_camera = tk.Button(control_frame, text="Kamerayı Aç", command=self.toggle_camera,
                                 font=("Helvetica", 12), bg="#2196F3", fg="white")
        self.btn_camera.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Yüz Tara ve Eşleştir", command=self.scan_and_match,
                font=("Helvetica", 12), bg="#FF5722", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Görüntü alanı
        self.camera_label = tk.Label(self.root, bg="black")
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sonuçlar
        result_frame = tk.Frame(self.root)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.result_label = tk.Label(result_frame, text="", font=("Helvetica", 12), 
                                   justify=tk.LEFT, wraplength=1100)
        self.result_label.pack(fill=tk.BOTH, expand=True)
        
        # İlerleme çubuğu
        self.progress = tk.DoubleVar()
        self.progress_bar = tk.Scale(self.root, variable=self.progress, from_=0, to=100,
                                   orient=tk.HORIZONTAL, length=600, showvalue=False, state=tk.DISABLED)
        self.progress_bar.pack(pady=10)
    
    def safe_path_join(self, *args):
        """Türkçe karakter ve Unicode sorunlarını çözen güvenli path birleştirme"""
        try:
            path = os.path.join(*args)
            if os.name == 'nt':
                path = os.path.normpath(path)
            return path
        except Exception as e:
            print(f"Path birleştirme hatası: {e}")
            return None
    
    def safe_imread(self, path):
        """Türkçe karakter destekli resim okuma"""
        try:
            # Önce standart yöntemi dene
            img = cv2.imread(path)
            if img is not None:
                return img
            
            # Unicode path için alternatif yöntem
            stream = open(path, "rb")
            bytes = bytearray(stream.read())
            numpyarray = np.asarray(bytes, dtype=np.uint8)
            img = cv2.imdecode(numpyarray, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"Resim okuma hatası {path}: {str(e)}")
            return None
    
    def select_source_folder(self):
        """Kaynak klasör seçimi"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.load_known_faces()
            messagebox.showinfo("Bilgi", f"Kaynak klasör seçildi!\n{len(self.known_faces)} yüz yüklendi.")
    
    def select_output_folder(self):
        """Çıktı klasörü seçimi"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            messagebox.showinfo("Bilgi", f"Çıktı klasörü seçildi!\nEşleşen fotoğraflar buraya kaydedilecek.")
    
    def load_known_faces(self):
        """Kaynak klasördeki yüzleri yükler"""
        self.known_faces = []
        self.face_labels = []
        
        if not os.path.exists(self.folder_path):
            messagebox.showerror("Hata", "Klasör bulunamadı!")
            return
            
        for filename in os.listdir(self.folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img_path = self.safe_path_join(self.folder_path, filename)
                    if img_path is None:
                        continue
                        
                    img = self.safe_imread(img_path)
                    if img is None:
                        continue
                        
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, 
                                                              minNeighbors=5, minSize=(100, 100))
                    
                    for (x, y, w, h) in faces:
                        face = gray[y:y+h, x:x+w]
                        face = cv2.resize(face, (200, 200))
                        self.known_faces.append(face)
                        self.face_labels.append(filename)
                        
                except Exception as e:
                    print(f"{filename} işlenirken hata: {str(e)}")
                    continue
    
    def toggle_camera(self):
        """Kamerayı açar/kapatır"""
        if not self.camera_on:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Hata", "Kamera açılamadı!")
                return
            
            self.camera_on = True
            self.btn_camera.config(text="Kamerayı Kapat", bg="#F44336")
            self.show_camera()
        else:
            self.camera_on = False
            if self.cap:
                self.cap.release()
            self.btn_camera.config(text="Kamerayı Aç", bg="#2196F3")
            self.camera_label.config(image=None)
    
    def show_camera(self):
        """Kamera görüntüsünü gösterir"""
        if self.camera_on and self.cap:
            ret, frame = self.cap.read()
            if ret:
                if self.scanning:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, 
                                                             minNeighbors=5, minSize=(100, 100))
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                        center = (x + w//2, y + h//2)
                        cv2.circle(frame, center, 5, (0, 0, 255), -1)
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
                self.root.after(10, self.show_camera)
    
    def scan_and_match(self):
        """Yüz tarama ve eşleştirme işlemini başlatır"""
        if not self.camera_on:
            messagebox.showerror("Hata", "Önce kamerayı açın!")
            return
            
        if not self.folder_path:
            messagebox.showerror("Hata", "Önce kaynak klasör seçin!")
            return
            
        if not self.output_folder:
            messagebox.showerror("Hata", "Önce çıktı klasörü seçin!")
            return
            
        ret, frame = self.cap.read()
        if ret:
            self.scanning = True
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, 
                                                     minNeighbors=5, minSize=(100, 100))
            
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                self.target_face = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                
                # Yakalanan yüzü geçici olarak kaydet
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                face_img = frame[y:y+h, x:x+w]
                temp_path = f"temp_face_{timestamp}.jpg"
                cv2.imwrite(temp_path, face_img)
                
                self.result_label.config(text="Yüz tespit edildi. Eşleşme aranıyor...")
                Thread(target=self.find_and_save_matches, args=(timestamp,), daemon=True).start()
            else:
                messagebox.showerror("Hata", "Yüz algılanamadı! Daha iyi bir poz verin.")
                self.scanning = False
    
    def find_and_save_matches(self, timestamp):
        """Eşleşmeleri bulur ve kaydeder"""
        self.progress_bar.config(state=tk.NORMAL)
        matches = []
        start_time = time.time()
        temp_path = f"temp_face_{timestamp}.jpg"
        
        for i, face in enumerate(self.known_faces):
            try:
                self.progress.set((i+1)/len(self.known_faces)*100)
                self.root.update()
                
                # Histogram karşılaştırması
                hist1 = cv2.calcHist([self.target_face], [0], None, [256], [0, 256])
                hist2 = cv2.calcHist([face], [0], None, [256], [0, 256])
                similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                
                if similarity > self.match_threshold:
                    matches.append(self.face_labels[i])
                    
                    # Eşleşen resmi çıktı klasörüne kopyala
                    src_path = self.safe_path_join(self.folder_path, self.face_labels[i])
                    dst_filename = f"match_{timestamp}_{self.face_labels[i]}"
                    dst_path = self.safe_path_join(self.output_folder, dst_filename)
                    
                    if src_path and dst_path:
                        try:
                            shutil.copy2(src_path, dst_path)
                        except Exception as e:
                            print(f"Kopyalama hatası: {str(e)}")
                    
            except Exception as e:
                print(f"Eşleştirme hatası: {str(e)}")
                continue
        
        elapsed_time = time.time() - start_time
        self.scanning = False
        self.progress.set(0)
        self.progress_bar.config(state=tk.DISABLED)
        
        # Yakalanan yüzü kaydet
        if matches and self.output_folder:
            dst_filename = f"captured_face_{timestamp}.jpg"
            dst_path = self.safe_path_join(self.output_folder, dst_filename)
            if dst_path:
                try:
                    shutil.move(temp_path, dst_path)
                except Exception as e:
                    print(f"Kaydetme hatası: {str(e)}")
        
        # Sonuçları göster
        if matches:
            result_text = f"✅ {len(matches)} EŞLEŞME BULUNDU ({elapsed_time:.2f}s)\n\n"
            result_text += "\n".join(matches[:10])  # İlk 10 sonucu göster
            if len(matches) > 10:
                result_text += f"\n\n...ve {len(matches)-10} adet daha"
            
            result_text += f"\n\nEşleşen fotoğraflar '{self.output_folder}' klasörüne kaydedildi."
            self.result_label.config(text=result_text)
        else:
            self.result_label.config(text=f"❌ EŞLEŞME BULUNAMADI ({elapsed_time:.2f}s)\n\nDaha iyi sonuçlar için:\n- Işığın yüzünüzü iyi aydınlattığından emin olun\n- Doğrudan kameraya bakın\n- Başka bir açı deneyin")
        
        # Geçici dosyayı sil
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

if __name__ == "__main__":
    # Unicode desteği için
    if os.name == 'nt':
        from ctypes import windll
        windll.kernel32.SetConsoleOutputCP(65001)
    
    root = tk.Tk()
    try:
        app = UltimateFaceMatcher(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılamadı: {str(e)}")
        print(f"Kritik hata: {str(e)}")