import requests
import base64
import os
from dotenv import load_dotenv
import random
load_dotenv()

def get_access_token():
    client_id = os.getenv("spotify_client_id")
    client_secret = os.getenv("spotify_client_secret")
    

    # Spotify API token URL
    url = 'https://accounts.spotify.com/api/token'

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    data = {
        "grant_type": "client_credentials",
        "client_id":client_id,
        "client_secret":client_secret
    }

    # Request the access token
    response = requests.post(url, headers=headers, data=data)

    # Extract the access token from the response
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        print(f"Access Token: {access_token}")
        return access_token
    else:
        print(f"Failed to get token: {response.status_code}")


def get_artist_id(artist_name, access_token):
    search_url = "https://api.spotify.com/v1/search"
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 1
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['artists']['items']:
            artist_id = data['artists']['items'][0]['id']
            return artist_id
        else:
            print("Artist not found.")
            return None
    else:
        print(f"Failed to search for artist: {response.status_code}, {response.text}")
        return None

def get_all_tracks_from_artist(artist_id, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Get all albums from the artist
    album_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    album_params = {
        "limit": 5,  # Get up to 50 albums
        "include_groups": "album,single"
    }
    response = requests.get(album_url, headers=headers, params=album_params)
    
    if response.status_code != 200:
        return None
    
    albums = response.json()['items']
    
    # Collect all tracks from all albums
    all_tracks = []
    
    for album in albums:
        album_id = album['id']
        track_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
        track_response = requests.get(track_url, headers=headers)
        
        if track_response.status_code == 200:
            tracks = track_response.json()['items']
            all_tracks.extend(tracks)
    
    return all_tracks





def get_artist_top_tracks(artist_id, access_token):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    params = {
        "market": "TW"  # You can set the market to a country code (e.g., "US")
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        tracks = data['tracks']  # List of top tracks
        return tracks if tracks else None
    else:
        print(f"Failed to get top tracks: {response.status_code}, {response.text}")
        return None

def get_random_popular_track(artist_name):
    access_token = get_access_token()
    
    if not access_token:
        return None
    
    artist_id = get_artist_id(artist_name, access_token)
    
    if not artist_id:
        return None
    
    all_tracks = get_all_tracks_from_artist(artist_id, access_token)
    
    if all_tracks:
        random_track = random.choice(all_tracks)
        track_name = random_track['name']
        track_url = random_track['external_urls']['spotify']
        return track_name, track_url
    else:
        print("No popular tracks found for this artist.")
        return None


if __name__ == "__main__":
    access_token = get_access_token()
    query = "Dreamcatcher"  # Song to search
    track_name,track_url = get_random_popular_track(query)
    print(track_name)
    print(track_url)