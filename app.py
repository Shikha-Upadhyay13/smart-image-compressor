from flask import Flask, render_template, request, send_file, url_for
from PIL import Image
import os
import shutil
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
COMPRESSED_FOLDER = 'compressed'
STATIC_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    static_original = None
    static_compressed = None
    done = False
    download_url = None
    error = None

    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        file_ext = filename.lower().split('.')[-1]
        target_size_mb = int(request.form['size'])
        target_size_bytes = target_size_mb * 1024 * 1024

        original_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(original_path)

        compressed_path = os.path.join(COMPRESSED_FOLDER, filename)

        try:
            if file_ext in ['jpg', 'jpeg', 'png', 'webp']:
                compress_image(original_path, compressed_path, target_size_bytes)
            elif file_ext in ['csv', 'txt', 'json']:
                compressed_path = compress_text_file(original_path)
            elif file_ext == 'pdf':
                compressed_path = compress_pdf_file(original_path)
            else:
                compressed_path = zip_file(original_path)

            # Copy for preview (only if image)
            if file_ext in ['jpg', 'jpeg', 'png', 'webp']:
                static_original = f'original_{filename}'
                static_compressed = f'compressed_{filename}'
                shutil.copy(original_path, os.path.join(STATIC_FOLDER, static_original))
                shutil.copy(compressed_path, os.path.join(STATIC_FOLDER, static_compressed))

            download_url = url_for('download_file', filename=os.path.basename(compressed_path))
            done = True

        except Exception as e:
            error = f"❌ Compression failed: {str(e)}"

    return render_template(
        'index.html',
        original=static_original,
        compressed=static_compressed,
        done=done,
        download_url=download_url,
        error=error
    )

def compress_image(input_path, output_path, target_size):
    quality = 95
    while quality >= 10:
        img = Image.open(input_path)
        img.save(output_path, optimize=True, quality=quality)
        if os.path.getsize(output_path) <= target_size:
            break
        quality -= 5

def compress_text_file(input_path):
    zip_path = input_path + '.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(input_path, arcname=os.path.basename(input_path))
    return zip_path

def compress_pdf_file(input_path):
    # Just zipping the PDF for now (real compression would need PyMuPDF or ghostscript)
    return compress_text_file(input_path)

def zip_file(input_path):
    return compress_text_file(input_path)

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(COMPRESSED_FOLDER, filename)
    if not os.path.exists(path):
        path = path + '.zip'
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
