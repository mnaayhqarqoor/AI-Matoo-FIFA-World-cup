import cv2
import numpy as np
import requests
import folium
from io import BytesIO
from PIL import Image
from ultralytics import YOLO
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import datetime, timedelta
import os

class SingaporeShipDetector:
    def __init__(self):
        # تحميل نموذج YOLOv8 المدرب مسبقاً
        self.model = YOLO('yolov8n.pt')  # أو استخدم yolov8x.pt لدقة أعلى
        
        # إحداثيات مضيق سنغافورة
        self.singapore_strait = {
            'north': 1.45,
            'south': 1.15,
            'east': 104.10,
            'west': 103.60
        }
        
        # إنشاء مجلد للنتائج
        os.makedirs('detected_ships', exist_ok=True)
        os.makedirs('satellite_images', exist_ok=True)
    
    def get_sentinel_images(self, days=60):
        """جلب صور Sentinel-2 المجانية من آخر 60 يوم"""
        # تسجيل حساب مجاني على https://scihub.copernicus.eu/
        api = SentinelAPI(
            'your_username',  # ضع اسم المستخدم الخاص بك
            'your_password',  # ضع كلمة المرور الخاصة بك
            'https://apihub.copernicus.eu/apihub'
        )
        
        # تحديد المنطقة والفترة الزمنية
        footprint = geojson_to_wkt(read_geojson('singapore_strait.geojson'))
        date_start = datetime.now() - timedelta(days=days)
        
        products = api.query(
            footprint,
            date=(date_start, datetime.now()),
            platformname='Sentinel-2',
            cloudcoverpercentage=(0, 20)  # أقل من 20% غيوم
        )
        
        return api.to_geodataframe(products)
    
    def download_satellite_image(self, product_id, api):
        """تحميل صورة القمر الصناعي"""
        try:
            api.download(product_id, directory_path='satellite_images')
            return f"satellite_images/{product_id}.zip"
        except Exception as e:
            print(f"خطأ في التحميل: {e}")
            return None
    
    def detect_ships(self, image_path):
        """كشف السفن في الصورة باستخدام YOLO"""
        # تحميل الصورة
        image = cv2.imread(image_path)
        if image is None:
            print("لا يمكن تحميل الصورة")
            return None, []
        
        # كشف السفن (فئة 'boat' في YOLO = 8)
        results = self.model(image, classes=[8])  # فئة القوارب
        
        ships_detected = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # استخراج إحداثيات المربع
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                
                if confidence > 0.3:  # الحد الأدنى للثقة 30%
                    # رسم مربع أخضر حول السفينة
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    cv2.putText(image, f'Ship {confidence:.2f}', 
                              (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 
                              1, (0, 255, 0), 2)
                    
                    # حفظ صورة السفينة المقصوصة
                    ship_crop = image[max(0, y1):min(image.shape[0], y2), 
                                     max(0, x1):min(image.shape[1], x2)]
                    ship_filename = f"detected_ships/ship_{len(ships_detected)}.jpg"
                    cv2.imwrite(ship_filename, ship_crop)
                    
                    ships_detected.append({
                        'coordinates': [x1, y1, x2, y2],
                        'confidence': confidence,
                        'image_path': ship_filename
                    })
        
        # حفظ الصورة مع المربعات الخضراء
        result_image_path = f"detected_ships/result_{os.path.basename(image_path)}"
        cv2.imwrite(result_image_path, image)
        
        return result_image_path, ships_detected
    
    def process_image_from_url(self, image_url):
        """معالجة صورة من رابط مباشر"""
        try:
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            img_np = np.array(img)
            image_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            # حفظ الصورة مؤقتاً
            temp_path = "satellite_images/temp_image.jpg"
            cv2.imwrite(temp_path, image_bgr)
            
            return self.detect_ships(temp_path)
        except Exception as e:
            print(f"خطأ: {e}")
            return None, []
    
    def create_map(self, ships_detected):
        """إنشاء خريطة تفاعلية للسفن المكتشفة"""
        # مركز مضيق سنغافورة
        m = folium.Map(location=[1.3, 103.85], zoom_start=10)
        
        for i, ship in enumerate(ships_detected):
            # ملاحظة: تحتاج لتحويل الإحداثيات من pixels إلى GPS
            # هذا يتطلب georeferencing data من الصورة الأصلية
            folium.Marker(
                location=[1.3 + (i * 0.01), 103.85 + (i * 0.01)],
                popup=f'سفينة {i+1} - ثقة: {ship["confidence"]:.2f}',
                icon=folium.Icon(color='green')
            ).add_to(m)
        
        m.save('ship_locations_map.html')
        return 'ship_locations_map.html'
