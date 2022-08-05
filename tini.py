from pyyoutube import Api
import yt_dlp as youtube_dl
import PySimpleGUI as sg
import os
import spotipy
import string
from spotipy.oauth2 import SpotifyClientCredentials

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
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
    print("Download complete... {}".format(filename))

def download(track_names, download_location, is_search = False):
    keys = ["<key1>", "<key2>", "<etc>"]
    api = Api(api_key=keys[0])
    invalid_key = True
    i = 0
    print("getting valid api key..")
    while invalid_key:
        try:
            api = Api(api_key=keys[i])
            search = api.search_by_keywords(q="", search_type=["video"], count=1, limit=1)
            print(bcolors.OKGREEN + keys[i]+ " hasn't hit it's daily call limit yet :)" + bcolors.ENDC)
            invalid_key = False
        except:
            print(bcolors.FAIL +keys[i] + " hit it's daily call limit :(" + bcolors.ENDC)
            i+=1
            if i == len(keys):
                return

    for track in track_names:
        search_query = ""
        count_limit = 1
        try:
            search_query = track[0]+' - '+track[1]
        except IndexError:
            print("Please enter search in the format <song-name>:<artist>")
            return
        if is_search:
            count_limit = 100
            search_query += " audio"
        search = api.search_by_keywords(q=search_query, search_type=["video"], count = count_limit, limit = count_limit)
        for search_result in search.items:
            try:
                download_ytvid_as_mp3(search_result.id.videoId, track, download_location)
                if is_search:
                    return
            except DownloadError(message, exc_info):
                print(message)
                print(exc_info)

# playlist = 'https://open.spotify.com/playlist/4xaSTfDH1oyfqFRmNKEFUf?si=1TAJ8NOwQfiKyq2oafTqXA'
# username = 'ryan.carter.ay'

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

layout = [  [sg.Text('Search for a single song like this, with a colon in the middle <song-name>:<artist>:'), sg.InputText(key='search')],
            [sg.Text('OR input a Spotify Playlist URL for one playlist:'), sg.InputText(key='url')],
            [sg.Text('OR a username for all their playlists:'), sg.InputText(key='username')],
            [sg.Text('Current Folder'), sg.FolderBrowse('Browse Download Location', key='download_location')],
            [sg.Button('Download')],
            [sg.Text('', key='result_label')]]


window = sg.Window('Tini', layout).Finalize()
window.Maximize()

while True:
    event, values = window.read()
    if event in (None, 'Download'):
        download_location = values['download_location'] if values['download_location'] != "" else '.'
        #values['url'] = 'https://open.spotify.com/playlist/4xaSTfDH1oyfqFRmNKEFUf?si=1TAJ8NOwQfiKyq2oafTqXA'
        if values['url'] != "":
            #window['result_label'].update("Downloading all tracks on that playlist. Please wait..")
            print('Downloading all tracks on that playlist. Please wait..')
            track_names = get_one_playlist(values['url'])
            download(track_names, download_location)
            break
        elif values['username'] != "":
            print('Downloading all playlists by that user. Please wait..')
            track_names = get_all_playlists(values['username'])
            download(track_names, download_location)
            break
        elif values['search'] != "":
            print('Downloading the song based on a search. Please wait..')
            track_names = [values['search'].split(":")]
            download(track_names, download_location, True)
            break

window.close()
