from __future__ import unicode_literals
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
from spotipy.oauth2 import SpotifyOAuth
import os
import youtube_dl
import urllib
import urllib.request
import json
from mutagen.id3 import APIC, ID3
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageDraw,ImageFont
import textwrap
import wget
import shutil
from dotenv import dotenv_values


config = dotenv_values(".env")  
playlist_name = 'streudel-mp3'
directory_name = 'streudel-mp3'

# TODO: Allow user to optionally disable spotify config
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
  client_id=config['CLIENT_ID'],
  client_secret=config['CLIENT_SECRET'],
  redirect_uri="https://localhost/spotify",
  scope="playlist-read-collaborative,playlist-modify-public,playlist-modify-private"))

def clear():
    _ = os.system('cls')
    _ = os.system('clear')

def first_use():
    # we could store user prefs in the playlists description?
    playlist = sp.user_playlist_create(sp.current_user()['id'], playlist_name, public=True, collaborative=False, description='')
    print("""
    \n\n
    ===================================================
    Looks like you're using streudel for the first time

    In order for streudel to work properly, you must follow
    these steps:

    1) In the Spotify Desktop client, add the {directory_name} directory 
    to your local files (this directory is in the same directory that streudel.py is)

    2) Enable syncing local files to your mobile devices in 
    Settings > Local Files on your iOS or Android device

    3) Download the playlist on your iOS or Android device
    ===================================================
    """)
    return playlist['href']
   
    

def find_playlist():
    offset = 0
    while 1==1:
        pl = sp.current_user_playlists(50, offset)
        for item in pl['items']:
            if item['name'] == playlist_name :
                return item['href'] 
        if pl['total'] < 50:
            break
        offset += 50
    
    # user has not yet used streudel
    first_use()

def uri_input():
    print('Enter a YouTube uri: ',end="")
    while 1==1:
        uri = str(input())
        # TODO: Validation
        return uri


def id_from_uri(s):
    return s[s.index('=')+1:len(s)]

def gen_cover_art(title):
    try:
        os.remove("art.png")
    except:
        print(end="")

    img = Image.new('RGB', (512, 512), color = '#000000')
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("font.ttf",100)
    lines = textwrap.wrap(title, width=5)
    y_text = 50
    for line in lines:
        width, height = font.getsize(line)
        d.text(((512 - width) / 2, y_text), line, font=font, fill=('#1EB100'))
        y_text += height
    img.save('art.png')

def get_cover_art():
    try:
        os.remove("art.png")
    except:
        print()

    img_uri = "https://img.youtube.com/vi/"+id_from_uri(youtube_uri)+"/maxresdefault.jpg"
    image_filename = wget.download(img_uri,"art.png")

    with Image.open("art.png") as im:
        width, height = im.size 
        left = (width/2)-(height/2)
        right = (width/2)+(height/2)
        im = im.crop((left, 0, right, height))
        im.save("art.png")

def youtube_to_mp3(uri):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'outtmpl':'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([uri])

def get_youtube_video_details(uri):
    params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % id_from_uri(uri)}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    title = ''
    author = ''

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        title = data['title']
        author = data['author_name']

    return title, author

def clear_album_art():
    # remove cover art (shouldn't be any anyways)
    song_file = ID3('song.mp3')
    song_file.delall("APIC")
    song_file.save()

def add_album_art():
    song_file = ID3('song.mp3')
    with open("art.png", 'rb') as albumart:
            song_file.add(APIC(
                encoding=3,
                mime='image/jpeg',
                type=3, desc=u'Cover',
                data=albumart.read()
            ))
    song_file.save()

def add_metadata(title, author):
    song_file = EasyID3('song.mp3')
    song_file['title'] = title
    song_file['artist'] = author
    song_file.save()

def main():
    if not (os.path.isdir('./streudel-mp3')):
        os.mkdir('./streudel-mp3')

    playlist = find_playlist()
    youtube_uri = uri_input()
    title, author = get_youtube_video_details(youtube_uri)

    print('Downloading \''+title+'\' by \''+author+'\'...')
    youtube_to_mp3(youtube_uri)
    print('Downloaded!')

    try:
        print('fetching video thumbnail...')
        get_cover_art()
        print('fetched video thumbnail!')
    except: 
        print('could not fetch video thumbnail...')
        print('generating thumbnail...')
        gen_cover_art(title)
        print('generated video thumbnail!')

    print('clearing album art...')
    clear_album_art()
    print('cleared album art!')

    print('adding new album art...')
    add_album_art()
    print('added new album art!')

    print('adding proper metadata...')
    add_metadata(title, author)
    print('added metadata!')

    shutil.move("./song.mp3","./streudel-mp3/"+title+" - "+author+".mp3")

    print('file downloaded to: '+"./streudel-mp3/"+title+" - "+author+".mp3")
    print('Add to Spotify playlist to ensure syncing!')

main()