import requests
from bs4 import BeautifulSoup
import psutil
import flask
from flask_cors import CORS
import re
from urllib.parse import urljoin
import sys
import time 
import platform
import argparse
print("VERSION 7")
if platform.system() == "Windows":
    import win32gui
    import win32process
elif platform.system() =="Linux": 
    import dbus

app = flask.Flask(__name__,template_folder="")
CORS(app)

@app.route("/packet")
def return_list_packet():
    packet = {}
    spotify_song = ""
    if platform.system() == "Windows":
            def get_title_windows():
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
            for process_name, windows in get_title_windows().items():
                if process_name == "Spotify.exe":
                    spotify_song = windows[0]['title']
    elif platform.system() == "Linux":
        def get_spot_linux():
            def fix_string(string):
                # corrects encoding for the python version used
                if sys.version_info.major == 3:
                    return string
                else:
                    return string.encode('utf-8')


            # Default parameters
            
            try:
                session_bus = dbus.SessionBus()
                spotify_bus = session_bus.get_object(
                    'org.mpris.MediaPlayer2.spotify',
                    '/org/mpris/MediaPlayer2'
                )

                spotify_properties = dbus.Interface(
                    spotify_bus,
                    'org.freedesktop.DBus.Properties'
                )

                metadata = spotify_properties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                artist = fix_string(metadata['xesam:artist'][0]) if metadata['xesam:artist'] else ''
                song = fix_string(metadata['xesam:title']) if metadata['xesam:title'] else ''
                output = fix_string(f'{artist} - {song}')
                return output

            except Exception as e:
                    print(e)
        spotify_song = get_spot_linux()

    spotify_song = spotify_song.replace(".","")
    spotify_song = spotify_song.replace("'","")
    spotify_song = spotify_song.replace("&","and")
    spotify_song = spotify_song.split("-",1)
    if str(spotify_song[1]).replace("-","") != spotify_song[1]:
        spotify_song_tmp = spotify_song[1].split("-")
        print(str(spotify_song_tmp[1].lower()).replace("remaster",""))
        if str(spotify_song_tmp[1].lower()).replace("remaster","") != spotify_song_tmp[1].lower():
           spotify_song[1] = spotify_song_tmp[0]

    artist_name = re.sub(r'[^a-zA-Z0-9\s]', '', spotify_song[0]).strip()
    song_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', spotify_song[1]).strip()
    artist_name_url = re.sub(r'\s+', '-', artist_name)
    song_title_url = re.sub(r'\s+', '-', song_title)

    packet["endpoint"] = f"https://genius.com/{artist_name_url}-{song_title_url.lower()}-lyrics"
    packet["song"] = spotify_song[1]
    packet["artist"] = artist_name
    
    response = requests.get(packet["endpoint"])

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        packet["lyrics"] = str(soup.find_all(attrs={"data-lyrics-container": "true"}))
        packet["lyrics"] = packet["lyrics"].replace("е","e")
        packet["lyrics"] = packet["lyrics"][1:-1]
        packet["lyrics"] = re.sub(r'\s+', ' ', re.sub(r'\[.*?\]', '',packet["lyrics"] )).strip()

        for img_tag in soup.find_all('img'):
                src = img_tag.get('src')
                if src:
                    if str(urljoin(packet["endpoint"], src)).endswith(".jpg") or str(urljoin(packet["endpoint"], src)).endswith(".png"):
                        packet["album_cover"] = str(urljoin(packet["endpoint"], src))
        packet["album"] = str(
            BeautifulSoup(
                str(
                    BeautifulSoup(
                        str(soup.find_all(attrs={"class":"HeaderArtistAndTracklistdesktop__Tracklist-sc-4vdeb8-2 glZsJC"})),"html.parser"
                    ).find_all(attrs={"class":"StyledLink-sc-3ea0mt-0"})
                ),"html.parser"
            ).text
        )[1:-1]
    else:
        print(f"Failed to retrieve {packet['endpoint']} Status code:{response.status_code}")
        packet["lyrics"] = "Can't Load Lyrics :( is Artist: "+f'"{packet["artist"]}"'+" on Genius.com?"
        packet["album"] = "Can't Load Album :("
    
    # do the same for the artist pfp
    response = requests.get(f"https://genius.com/artists/{artist_name_url}");
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            packet["artist_cover"] = f"https{(str((str(str(soup.find_all(class_="user_avatar")).split("url")[1]).split("https"))[1]).split("');"))[0]}"
        except: 
            print("Something Went wrong in the artist_cover portion ( line 132 )")
    return flask.jsonify(packet)



if __name__ == "__main__":

    app.run(debug=True)
