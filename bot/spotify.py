"""A handler for Spotify API using AIOHTTP and spotipy's OAuth"""

import re
import string as stringlib
import asyncio
import aiohttp
import urllib.parse
import difflib

import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyHandler():
    """Class with functions that create playlists"""

    def __init__(self):
        self.auth = SpotifyOAuth(scope="user-library-read playlist-modify-public")
        self.access_token:function = lambda : self.auth.get_access_token(as_dict=False)

        sp = spotipy.Spotify(auth_manager=self.auth)
        self.USER_ID = sp.me()['id']

    ### API FUNCTIONS ###

    async def create_playlist(self, aiosession:aiohttp.ClientSession, name:str, description:str) -> dict:
        """Creates a public playlist on the Bot's account and returns the object"""
        async with aiosession.post(
            f"https://api.spotify.com/v1/users/{self.USER_ID}/playlists",
            headers={
                "Authorization": f"Bearer {self.access_token()}"
            },
            json={
                "name": name,
                "description": description,
                "public": True
            }
        ) as resp:
            response_json = await resp.json()
            return response_json

    async def add_songs_to_playlist(self, aiosession:aiohttp.ClientSession, playlist:dict, tracks:list[dict]):
        """Adds the tracks to the playlist. MUST pass a list of tracks."""
        async with aiosession.post(
            f"https://api.spotify.com/v1/playlists/{playlist['id']}/tracks",
            headers={
                "Authorization": f"Bearer {self.access_token()}"
            },
            json={
                "uris": [track['uri'] for track in tracks]
            }
        ) as resp:
            response_json = await resp.json()
            return response_json

    async def search(self, aiosession:aiohttp.ClientSession, query:str, type:str, limit:int=50, offset:int=0) -> dict:
        """Searches spotify and returns the dictionary that results"""
        query = urllib.parse.quote(query)
        url = f"https://api.spotify.com/v1/search?q={query}&type={type}&limit={limit}"
        if offset > 0:
            url += f"&offset={offset}"

        async with aiosession.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token()}"
            }
        ) as resp:
            response_json = await resp.json()
            return response_json

    ### INTERNAL FUNCTIONS ###

    async def add_songs_by_sentence(self, aiosession:aiohttp.ClientSession, sentence:str, playlist:dict):
        """Adds the sentence to the given playlist"""

        # Removes punctuation and capitalization, then splits the words into a list
        words = sentence.lower().translate(str.maketrans('', '', stringlib.punctuation)).split()
        while words:
            found = False

            # Will create a query for each word
            for i in range(len(words)):

                # Adds every word after the first word
                # Then every word but last
                # And so on
                search = ""
                for j in range(len(words) - i):
                    search += words[j]
                    if j < (len(words) - i - 1):
                        search += " "
                
                # Conducts search, adds tracks from each page to the list
                searchtracks = []
                for page in range(5):
                    pageresults = await self.search(aiosession, search, type="track", limit=50, offset=(50 * page))
                    if not pageresults['tracks']['items']:
                        break            
                    for track in pageresults['tracks']['items']:
                        searchtracks.append(track)

                found = False
                search_words = search.split()

                # Checks each track to see if it matches the search string
                for track in searchtracks:
                    title_words = track['name'].lower().split()

                    if title_words == search_words:
                        print(f"{track['name']} by {track['artists'][0]['name']}")
                        await self.add_songs_to_playlist(aiosession, playlist, [track])
                        
                        found = True
                        break
                
                # If it's one word, it attempts to find the closest match
                if not found and len(search_words) == 1:
                    
                    trackdict = {}
                    for track in searchtracks:
                        trackdict[track['name']] = track
                    
                    potentialmatches = difflib.get_close_matches(search_words[0], list(trackdict.keys()))
                    
                    if len(potentialmatches) != 0:
                        track = trackdict[potentialmatches[0]]
                        print(f"{track['name']} by {track['artists'][0]['name']}")
                        await self.add_songs_to_playlist(aiosession, playlist, [track])
                        found = True

                # If it found a result, it removes the words from the list
                if found:
                    for j in range(len(search_words)):
                        words.pop(0)
                    break
            
            # If after everything, it didn't find anything, it removes the word.
            if not found:
                words.pop(0)

    async def make_playlist_from_string(self, aiosession:aiohttp.ClientSession, inputstring:str, name:str) -> str:
        """Makes a playlist from the given string with the given name and returns the URL"""
        
        # Splits the string by sentence to make it easier to work with
        sentences = []
        for sentence in re.split("[.?!(),]", inputstring):
            sentence = sentence.strip()
            if sentence != '':
                sentences.append(sentence)

        # Calls Spotify's API to make a playlist
        try:
            playlist = await self.create_playlist(
                aiosession=aiosession,
                name=name,
                description=f"\"{inputstring}\""
            )
        except:
            print("ERROR CREATING PLAYLIST")
            return None

        # Goes sentence by sentence and adds songs to the playlist based on it
        for sentence in sentences:
            try:
                await self.add_songs_by_sentence(
                    aiosession=aiosession,
                    sentence=sentence,
                    playlist=playlist
                )
            except:
                print("ERROR ADDING SONGS TO PLAYLIST")
                return None

        return playlist['external_urls']['spotify']


if __name__ == "__main__":

    string = input("Enter a sentence to make a playlist out of:\n")
    title = input("Enter a title for the playlist:\n")

    client = SpotifyHandler()
    url = asyncio.run(client.make_playlist_from_string(string, title))
    print(url)
