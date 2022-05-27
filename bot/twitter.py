"""Subclasses the async streaming client"""

import os
import asyncio

import tweepy
from tweepy.asynchronous import AsyncClient, AsyncStreamingClient

import spotify

class TwitterBot(AsyncStreamingClient):
    """Subclass of Tweepy's Async Streaming Client"""

    def __init__(self):
        super().__init__(
            bearer_token=os.getenv('TWEEPYBEARER')
        )

        self.bot = AsyncClient(
            consumer_key=os.getenv('TWEEPYAPITOKEN'),
            consumer_secret=os.getenv('TWEEPYAPISECRET'),
            access_token=os.getenv('TWEEPYACCESS'),
            access_token_secret=os.getenv('TWEEPYACCESSSECRET')
        )

        self.spotify = spotify.SpotifyHandler()

    ### STREAMING CLIENT EVENTS ###

    async def on_response(self, response:tweepy.StreamResponse):
        tweet_author = response.includes['users'][0]['username']
        reply_id = response.data['id']

        # Responds to a tweet if the tweet isn't by itself and the tweet is a response
        if tweet_author != 'playlist_it':
            if 'tweets' in response.includes:
                await self.make_playlist(response)
            else:
                await self.bot.create_tweet(
                    in_reply_to_tweet_id=reply_id,
                    text="Oops! You have to tag me in a reply to another Tweet!"
                )

    ### SELF DEFINED FUNCTIONS ###

    async def make_playlist(self, response:tweepy.StreamResponse) -> str:
        """Makes a playlist based on the response and returns the URL"""
        reference_text = response.includes['tweets'][0]['text']
        reply_id = response.data['id']

        url = await self.spotify.make_playlist_from_string(
            self.session,
            reference_text,
            f"Playlist for {response.includes['users'][0]['username']}"
        )

        if url == None:
            url = "Uh-oh! Something went wrong :("
            print("ERROR")

        await self.bot.create_tweet(
            in_reply_to_tweet_id=reply_id,
            text=url
        )


if __name__ == "__main__":
    async def main():
        bot = TwitterBot()

        await bot.add_rules(tweepy.StreamRule("@playlist_it"))
        print("Now playing!")
        await bot.filter(
            expansions=["referenced_tweets.id","author_id"],
            tweet_fields=["author_id"]
        )
    
    asyncio.run(main())
