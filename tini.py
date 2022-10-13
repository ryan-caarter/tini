from pyyoutube import Api
import yt_dlp as youtube_dl
import PySimpleGUI as sg
import os
import spotipy
import string
import sys
from spotipy.oauth2 import SpotifyClientCredentials

""" INSTRUCTIONS
1. Open Google Cloud Console: https://console.cloud.google.com/
2. Make a new project, call it whatever
3. Select this new project
4. Search for "YouTube Data API v3" and enable it
5. Search for "Credentials"
6. Create Credentials -> API key
7. Copy the key, replace line 23's "<API key>" with the key
8. Run

There is an upper limit of (30,000?) daily calls you can make on free keys
"""

def get_youtube_api():
    key = "<API key>"
    print(Colors.BLUE + "Getting valid api key.." + Colors.END)
    try:
        api = Api(api_key=key)
        search = api.search_by_keywords(q="", search_type=["video"], count=1, limit=1)
        print(Colors.GREEN + "Youtube API initialised successfully" + Colors.END)
        return api
    except Exception as e:
        print(Colors.FAIL + str(e) + Colors.END)
    return None

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_all_playlists(username):
    all_playlist_track_names = []
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        if playlist['owner']['id'] == username:
            results = sp.user_playlist(username, playlist['id'], fields="tracks,next")
            tracks = results['tracks']
            while tracks['next']:
                tracks = sp.next(tracks)
                all_playlist_track_names += show_tracks(tracks)
    return all_playlist_track_names

def show_tracks(tracks):
    track_names = []
    for i, item in enumerate(tracks['items']):
        track = item['track']
        track_names.append([track['name'], track['artists'][0]['name']])
    return track_names

def get_playlist_uri(playlist_link):
    return playlist_link.split("/")[-1].split("?")[0]

def get_one_playlist(playlist_link):
    tracks = []
    playlist_uri = get_playlist_uri(playlist_link)
    for track in sp.playlist_tracks(playlist_uri)["items"]:
        if track["track"] is not None:
            track_name = track["track"]['name']
            track_artist = track["track"]["artists"][0]["name"]
            result = [track_name, track_artist]
            tracks.append(result)
    return tracks

def download_ytvid_as_mp3(video_url, track, download_location):
    video_info = youtube_dl.YoutubeDL().extract_info(url = video_url,download=False)
    filename = f"{download_location}/{string.capwords(' - '.join(track))}.mp3"
    options={
        'keepvideo':False,
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])
    print(Colors.GREEN + "Download complete... {}".format(filename) + Colors.END)

def download(track_names, download_location, youtube_api, is_search = False):
    for track in track_names:
        search_query = ""
        count_limit = 1
        try:
            search_query = track[0]+' - '+track[1]
        except IndexError:
            print(Colors.FAIL + "Please enter search in the format <song-name>:<artist>" + Colors.END)
            return
        if is_search:
            count_limit = 100
            search_query += " audio"
            print(Colors.BLUE + "Searching Youtube for: " + search_query + Colors.END)
        search = youtube_api.search_by_keywords(q=search_query, search_type=["video"], count = count_limit, limit = count_limit)
        for search_result in search.items:
            try:
                download_ytvid_as_mp3(search_result.id.videoId, track, download_location)
                if is_search:
                    return
            except DownloadError(message, exc_info):
                print(message)
                print(exc_info)

# MAIN
youtube_api = get_youtube_api()
if youtube_api == None:
    sys.exit()

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

layout = [  [sg.Text('Search for a single song in format <song-name>:<artist>:'), sg.InputText(key='search')],
            [sg.Text('OR input a Spotify Playlist URL for one playlist:'), sg.InputText(key='url')],
            [sg.Text('OR a Spotify username for all their playlists:'), sg.InputText(key='username')],
            [sg.Text('Current Folder'), sg.FolderBrowse('Browse Download Location', key='download_location')],
            [sg.Button('Download')],
            [sg.Text('', key='result_label')]]

window = sg.Window('TINI', layout).Finalize()
window.Maximize()

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        sys.exit()
    if event in (None, 'Download'):
        try:
            download_location = values['download_location'] if values['download_location'] != "" else '.'
            if values['url'] != "":
                print(Colors.BLUE + 'Downloading all tracks on that playlist. Please wait..' + Colors.END)
                track_names = get_one_playlist(values['url'])
                download(track_names, download_location, youtube_api)
            elif values['username'] != "":
                print(Colors.BLUE + 'Downloading all playlists by that user. Please wait..' + Colors.END)
                track_names = get_all_playlists(values['username'])
                download(track_names, download_location, youtube_api)
            elif values['search'] != "":
                print(Colors.BLUE + 'Downloading the song based on a search. Please wait..' + Colors.END)
                track_names = [values['search'].split(":")]
                download(track_names, download_location, youtube_api, True)
        except Exception as e:
            print(Colors.FAIL + str(e) + Colors.END)
window.close()
