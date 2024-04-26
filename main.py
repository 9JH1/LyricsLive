import requests
from bs4 import BeautifulSoup
import psutil
import win32gui
import win32process
import flask
from flask_cors import CORS
import re




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
    # Define a regular expression pattern to match words enclosed in square brackets
    pattern = r'\[[^\]]+\]'
    # Use re.sub() to remove words matching the pattern
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text



app = flask.Flask(__name__,template_folder="")
CORS(app)

@app.route("/spotify")
def render_song_info():
    spotify_song = ""
    for process_name, windows in get_window_titles().items():
        if(process_name == "Spotify.exe"):
            spotify_song = [s.strip() for s in windows[0]["title"].split("-")]
    return f"{spotify_song[0]} - {spotify_song[1]}"
@app.route("/")
def render_website():
    return flask.render_template("index.html")

@app.route("/lyrics")
def render_lyrics():
    spotify_song = ""
    for process_name, windows in get_window_titles().items():
        if(process_name == "Spotify.exe"):
            spotify_song = [s.strip() for s in windows[0]["title"].split("-")]
    lyrics = scrape_lyrics_containers(f"https://genius.com/{spotify_song[0].replace(" ","-")}-{spotify_song[1].replace(" ","-").lower().replace(",","")}-lyrics")

    print(f"https://genius.com/{spotify_song[0].replace(" ","-")}-{spotify_song[1].replace(" ","-").lower()}-lyrics")
    return remove_words_in_brackets(str(lyrics)[1:-1])

if __name__ == "__main__": 
    app.run(debug=True)