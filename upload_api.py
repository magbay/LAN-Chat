import os
from flask import request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from lan_chat import app

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    print('[DEBUG] upload_file called')
    print(f'[DEBUG] request.method: {request.method}')
    print(f'[DEBUG] request.headers: {dict(request.headers)}')
    print(f'[DEBUG] request.files: {request.files}')
    if 'file' not in request.files:
        print('[DEBUG] No file part in request.files:', request.files)
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    print(f'[DEBUG] file.filename: {file.filename}')
    if file.filename == '':
        print('[DEBUG] No selected file')
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print(f'[DEBUG] Saving file as: {filename}')
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        url = f"/uploads/{filename}"
        print(f'[DEBUG] File saved, url: {url}')
        return jsonify({'url': url}), 200
    print('[DEBUG] Invalid file type:', file.filename)
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
