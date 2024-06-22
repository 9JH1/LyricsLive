import requests
from bs4 import BeautifulSoup
import psutil
import win32gui
import win32process
import flask
from flask_cors import CORS
import re
from urllib.parse import urljoin
import time 
def get_window_titles():
    window_data = {}
    def enum_windows_callback(hwnd, _):
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            if process_name not in window_data:
                window_data[process_name] = []
            window_title = win32gui.GetWindowText(hwnd)
            if window_title:
                window_data[process_name].append({"title": window_title, "file_path": process.exe()})
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    win32gui.EnumWindows(enum_windows_callback, None)
    return window_data
# this will work cross-platform
def scrape_lyrics_containers(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        lyrics_containers = soup.find_all(attrs={"data-lyrics-container": "true"})
        return lyrics_containers
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)
        return []

def remove_words_in_brackets(text):
    pattern = r'\[[^\]]+\]'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text
app = flask.Flask(__name__,template_folder="")
CORS(app)
genius_url = ""
@app.route("/spotify")
def render_song_info():
    spotify_song = ""
    for process_name, windows in get_window_titles().items():
        if(process_name == "Spotify.exe"):
            spotify_song = [s.strip() for s in windows[0]["title"].split("-", 1)]
    return f"{spotify_song[0]} - {spotify_song[1]}"
@app.route("/")
def render_website():
    return flask.render_template("index.html")
@app.route("/lyrics")
def render_lyrics():
    global genius_url
    spotify_song = ""
    for process_name, windows in get_window_titles().items():
        if process_name == "Spotify.exe":
            spotify_song = [s.strip() for s in windows[0]["title"].split("-", 1)]
            spotify_song[1].replace("-"," ")
            
    spotify_song[1] = spotify_song[1].replace(".","")
    
    spotify_song[1] = spotify_song[1].replace("'","")
    artist_name = re.sub(r'[^a-zA-Z0-9\s]', '', spotify_song[0]).strip()
    song_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', spotify_song[1]).strip()
    artist_name_url = re.sub(r'\s+', '-', artist_name)
    song_title_url = re.sub(r'\s+', '-', song_title)
    genius_url = f"https://genius.com/{artist_name_url}-{song_title_url.lower()}-lyrics"
    print(genius_url)
    lyrics = scrape_lyrics_containers(genius_url)
    return remove_words_in_brackets(str(lyrics)[1:-1])

@app.route("/album_img")
def get_resource_urls():
    response = requests.get(genius_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        resource_urls = set()

        # Find all <img> tags and extract the 'src' attribute
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src')
            if src:
                if str(urljoin(genius_url, src)).endswith(".jpg") or str(urljoin(genius_url, src)).endswith(".png"):
                    return str(urljoin(genius_url, src))
        return None
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)
        return None

if __name__ == "__main__": 
    app.run(debug=True)