from flask import Flask, render_template, request, send_file, jsonify
from yt_dlp import YoutubeDL
import os
import time

app = Flask(__name__)

# Gunakan /tmp agar aman di serverless/container
DOWNLOAD_FOLDER = '/tmp'
COOKIE_PATH = "/tmp/cookies.txt"

def get_ydl_opts(download=True):
    # Ambil isi cookies dari Environment Variable Koyeb
    cookie_content = os.environ.get('YOUTUBE_COOKIES')
    
    if cookie_content:
        with open(COOKIE_PATH, 'w', encoding='utf-8') as f:
            f.write(cookie_content.replace('\\n', '\n').strip())
        print(f"DEBUG: Cookies written to {COOKIE_PATH}")
    
    opts = {
        'format': 'best',

        'cookiefile': COOKIE_PATH,

        'restrictfilenames': True,

        'http_headers': {
            'User-Agent': 'com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_2 like Mac OS X)'
        },

        'extractor_args': {
            'youtube': {
                'player_client': ['ios']
            }
        },

        'sleep_interval_requests': 1,

        'extractor_retries': 5,

        'quiet': True,
        'no_warnings': True,
    }

    if download:
        opts.update({
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    return opts

def cleanup_downloads():
    """Menghapus file jika lebih dari 3 file di /tmp"""
    files = [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith('.mp3')]
    if len(files) >= 3:
        files.sort(key=os.path.getmtime)
        while len(files) >= 3:
            os.remove(files.pop(0))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            youtube_url = request.form['url'].strip()
            # WAJIB gunakan opts dengan cookies agar tidak kena blokir saat ambil info
            opts = get_ydl_opts(download=False)
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                video_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': info.get('duration', 0),
                    'url': youtube_url
                }
            return render_template('index.html', video_info=video_info)
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    try:
        cleanup_downloads()
        url = request.form['url']
        opts = get_ydl_opts(download=True)
        
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Dapatkan nama file asli yang sudah diproses
            final_filename = ydl.prepare_filename(info)
            final_filename = os.path.splitext(final_filename)[0] + '.mp3'
            basename = os.path.basename(final_filename)
            
        return jsonify({'success': True, 'filename': basename})
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File tidak ditemukan.", 404

if __name__ == '__main__':
    # Lokal test
    app.run(debug=True, port=8080)