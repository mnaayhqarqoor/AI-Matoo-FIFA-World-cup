from flask import Flask, render_template, request, jsonify, send_file
from ship_detector import SingaporeShipDetector
import os

app = Flask(__name__)
detector = SingaporeShipDetector()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect_ships():
    if 'image' not in request.files:
        return jsonify({'error': 'لم يتم رفع صورة'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'لم يتم اختيار ملف'})
    
    # حفظ الصورة المرفوعة
    image_path = f'satellite_images/uploaded_{file.filename}'
    file.save(image_path)
    
    # كشف السفن
    result_image, ships = detector.detect_ships(image_path)
    
    if result_image:
        return jsonify({
            'success': True,
            'result_image': result_image,
            'ships_count': len(ships),
            'ships': ships
        })
    
    return jsonify({'error': 'فشل في معالجة الصورة'})

@app.route('/search_last_60_days', methods=['POST'])
def search_recent_images():
    """البحث عن صور من آخر 60 يوم"""
    try:
        # ملاحظة: تحتاج لإعداد Sentinel API credentials
        images = detector.get_sentinel_images(days=60)
        return jsonify({
            'success': True,
            'count': len(images),
            'images': images.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get_image/<path:filename>')
def get_image(filename):
    return send_file(filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
