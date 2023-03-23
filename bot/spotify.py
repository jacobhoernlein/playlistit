from difflib import get_close_matches
from string import punctuation

import spotipy


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def simplify_string(s: str) -> str:
    """Removes punctuation and capitalization from given string."""

    return s.lower().translate(str.maketrans('', '', punctuation))

def get_best_match(sp: spotipy.Spotify, words: list[str]) -> tuple[dict | None, list[str]]:
    """Uses the Spotify class to find a song that best applies to the
    list of words passed. Returns the track dict, and the new words
    list.
    """
 
    working_words = words[0:5]
    while working_words:

        # Join the current list of words into a sentence.
        query = ' '.join(working_words)

        # Get a list of tracks based on the query.
        tracks = sp.search(query, limit=50, type='track')['tracks']['items']

        # Look for an exact match. If one is found,
        # edit original words list and return the id.
        for track in tracks:
            name = simplify_string(track['name'])
            if name == query:
                return track, words[len(working_words):]

        # If an exact match isn't found, and only one word is left,
        # look for best match.
        if len(working_words) == 1:
            name_to_track = {
                track['name']: track
                for track in tracks
            }

            matches = get_close_matches(working_words[0], list(name_to_track))
            if matches:
                return name_to_track[matches[0]], words[1:]
            else:
                return None, words[1:]

        # If match isn't found, remove last word and try again.
        working_words.pop()

    return None, words[1:]

def get_song_ids(sp: spotipy.Spotify, description: str) -> list[int | None]:
    """Gets a list of Spotify Track IDs that spell out the passed
    description.
    """

    words = simplify_string(description).split()
    track_ids = []

    while words:
        track, words = get_best_match(sp, words)
        if track is not None:
            print(f" - {track['name']} by {track['artists'][0]['name']}")
            track_ids.append(track['id'])

    return track_ids


if __name__ == '__main__':

    scope = 'user-library-read playlist-modify-public'
    
    try:
        auth = spotipy.oauth2.SpotifyOAuth(scope=scope)
    except spotipy.oauth2.SpotifyOauthError:
        print("Authorization failed. Make sure SPOTIFY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI environment variables are set. See https://www.youtube.com/watch?v=3RGm4jALukM for more info.")
        exit(1)
    
    sp = spotipy.Spotify(auth_manager=auth)
    user_id = sp.me()['id']

    name = input("Enter a title for the playlist:\n")
    description = input("Enter a sentence to make a playlist out of:\n")

    playlist = sp.user_playlist_create(user_id, name, description=description)
    tracks = get_song_ids(sp, description)
    sp.playlist_add_items(playlist['id'], tracks)
    print(f"Here's your playlist:\n{playlist['external_urls']['spotify']}")
