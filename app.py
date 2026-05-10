from flask import Flask, render_template, request, send_file, jsonify
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)

# Gunakan /tmp jika di Vercel, jika lokal gunakan folder 'downloads'
DOWNLOAD_FOLDER = '/tmp' if os.environ.get('VERCEL') else 'downloads'
# Letakkan di bagian atas setelah app = Flask(__name__)
COOKIE_PATH = "/tmp/cookies.txt"

def prepare_cookies():
    raw_cookies = os.environ.get('YOUTUBE_COOKIES')
    if raw_cookies:
        try:
            with open(COOKIE_PATH, 'w') as f:
                f.write(raw_cookies)
            print(f"DEBUG: Cookies successfully written to {COOKIE_PATH}")
        except Exception as e:
            print(f"DEBUG: Failed to write cookies: {e}")
    else:
        print("DEBUG: No YOUTUBE_COOKIES found in environment variables")

def cleanup_downloads():
    """Menghapus file lama jika lebih dari 3 file"""
    files = [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith('.mp3')]
    # Urutkan berdasarkan waktu modifikasi (paling lama di awal)
    files.sort(key=os.path.getmtime)
    
    while len(files) >= 3:
        os.remove(files.pop(0))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            youtube_url = request.form['url'].strip()
            with YoutubeDL() as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                video_info = {
                    'title': info['title'],
                    'thumbnail': info['thumbnail'],
                    'duration': info['duration'],
                    'url': youtube_url
                }
            return render_template('index.html', video_info=video_info)
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    try:
        # Jalankan pembersihan sebelum download baru
        cleanup_downloads()
        
        youtube_url = request.form['url']
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'restrictfilenames': True, 
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'cookiefile': COOKIE_PATH,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
                'quiet': True,
                'no_warnings': True,
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            # Dapatkan nama file asli yang sudah dibersihkan oleh yt-dlp
            final_filename = ydl.prepare_filename(info)
            # Ubah ekstensi ke mp3 karena postprocessor mengubahnya
            final_filename = os.path.splitext(final_filename)[0] + '.mp3'
            basename = os.path.basename(final_filename)
            
        return jsonify({'success': True, 'filename': basename})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    # Pastikan file diambil dari folder yang benar
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File tidak ditemukan atau sudah dihapus otomatis.", 404

if __name__ == '__main__':
    app.run(debug=True)