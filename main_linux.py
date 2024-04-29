import requests
from bs4 import BeautifulSoup
import flask
from flask_cors import CORS
import re
import sys
import dbus
import argparse


def get_spotify_song_linux():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--trunclen',
        type=int,
        metavar='trunclen'
    )
    parser.add_argument(
        '-f',
        '--format',
        type=str,
        metavar='custom format',
        dest='custom_format'
    )
    parser.add_argument(
        '-p',
        '--playpause',
        type=str,
        metavar='play-pause indicator',
        dest='play_pause'
    )
    parser.add_argument(
        '--font',
        type=str,
        metavar='the index of the font to use for the main label',
        dest='font'
    )
    parser.add_argument(
        '--playpause-font',
        type=str,
        metavar='the index of the font to use to display the playpause indicator',
        dest='play_pause_font'
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help="if set, don't show any output when the current song is paused",
        dest='quiet',
    )

    args = parser.parse_args()


    def fix_string(string):
        # corrects encoding for the python version used
        if sys.version_info.major == 3:
            return string
        else:
            return string.encode('utf-8')


    def truncate(name, trunclen):
        if len(name) > trunclen:
            name = name[:trunclen]
            name += '...'
            if ('(' in name) and (')' not in name):
                name += ')'
        return name


    # Default parameters
    output = fix_string(u'{play_pause} {artist}: {song}')
    trunclen = 35
    play_pause = fix_string(u'\u25B6,\u23F8') # first character is play, second is paused

    label_with_font = '%{{T{font}}}{label}%{{T-}}'
    font = args.font
    play_pause_font = args.play_pause_font

    quiet = args.quiet

    # parameters can be overwritten by args
    if args.trunclen is not None:
        trunclen = args.trunclen
    if args.custom_format is not None:
        output = args.custom_format
    if args.play_pause is not None:
        play_pause = args.play_pause

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
        status = spotify_properties.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')

        # Handle play/pause label

        play_pause = play_pause.split(',')

        if status == 'Playing':
            play_pause = play_pause[0]
        elif status == 'Paused':
            play_pause = play_pause[1]
        else:
            play_pause = str()

        if play_pause_font:
            play_pause = label_with_font.format(font=play_pause_font, label=play_pause)

        # Handle main label

        artist = fix_string(metadata['xesam:artist'][0]) if metadata['xesam:artist'] else ''
        song = fix_string(metadata['xesam:title']) if metadata['xesam:title'] else ''
        album = fix_string(metadata['xesam:album']) if metadata['xesam:album'] else ''

        if (quiet and status == 'Paused') or (not artist and not song and not album):
            print('')
        else:
            if font:
                artist = label_with_font.format(font=font, label=artist)
                song = label_with_font.format(font=font, label=song)
                album = label_with_font.format(font=font, label=album)

            # Add 4 to trunclen to account for status symbol, spaces, and other padding characters
            return(truncate(output.format(artist=artist, 
                                        song=song, 
                                        play_pause=play_pause, 
                                        album=album), trunclen + 4))

    except Exception as e:
            print(e)


print(get_spotify_song_linux())
exit()



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
    spotify_song = ""
    # define with dbus 
    artist_name = re.sub(r'[^a-zA-Z0-9\s]', '', spotify_song[0]).strip()
    song_title = re.sub(r'[^a-zA-Z0-9\s]', ' ', spotify_song[1]).strip()
    artist_name_url = re.sub(r'\s+', '-', artist_name)
    song_title_url = re.sub(r'\s+', '-', song_title)
    genius_url = f"https://genius.com/{artist_name_url}-{song_title_url.lower()}-lyrics"
    print(genius_url)
    lyrics = scrape_lyrics_containers(genius_url)
    return remove_words_in_brackets(str(lyrics)[1:-1])

if __name__ == "__main__": 
    app.run(debug=True)