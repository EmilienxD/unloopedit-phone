from asyncio import run
from shazamio import Shazam
import requests

from lib.modules.paths import Path, PathLike
from lib.modules.basics.UList import UList
from lib.modules.display import Logger


class SongAnalyst:
    """Audio analysis tool using Shazam, Chosic, and Sonoteller APIs."""

    logger = Logger('[SongAnalyst]')

    def __init__(self):
        self.schema: dict[str, str | list[str | dict] | dict[str, dict]] = {
            "details": {
                'title': "",
                "related_artists": []
            },
            "analysis": {
                'lyrics': {},
                'music': {}
            }
        }
        self.shazam = Shazam()
        self.headers_chosic = {
            'sec-ch-ua-platform': '"Windows"',
            'Referer': 'https://www.chosic.com/music-genre-finder/',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'app': 'genre_finder',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }
        self.headers_sonoteller = {
            'accept': '*/*',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'content-type': 'application/json',
            'origin': 'https://sonoteller.ai',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        }

    def _url_format(self, string: str) -> str:
        return string.replace(" ", "%20")

    def identify_song(self, audio_path: PathLike) -> dict[str, str | list[str] | dict[str, dict]] | None:
        """Identify song title and subtitle using Shazam."""
        try:
            audio_path = Path(audio_path, 'File', assert_exists=True)
            out = run(self.shazam.recognize(audio_path.fs))
            data = self.schema.copy()
            data['details']['title'] = f"{out['track']['title']} - {out['track']['subtitle']}"
            return data
        except Exception as e:
            self.logger.error(f'Error when identifying song', skippable=True, base_error=e)

    def analize_song_chosic(
            self,
            search: str,
            sanitize: bool = False,
            initial_data: dict | None = None
        ) -> dict[str, str | list[str] | dict[str, dict]] | None:
        """Fetch Chosic track details with optional sanitization."""
        try:
            response = requests.get(
                f'https://www.chosic.com/api/tools/search?q={self._url_format(search)}&type=track&limit=10',
                headers=self.headers_chosic
            )
            track_id = response.json()["tracks"]["items"][0]["id"]
            if not track_id:
                return None

            track_info = requests.get(f'https://www.chosic.com/api/tools/tracks/{track_id}', headers=self.headers_chosic).json()
            youtube_link = self._fetch_youtube_link(track_info["name"], track_info["artists"][0]["name"])

            related_artists = requests.get(
                f'https://www.chosic.com/api/tools/artists/related-artists/{track_info["artists"][0]["id"]}',
                headers=self.headers_chosic
            ).json()["artists"]

            track_info["genres"] = self._extract_genres_from_related_artists(related_artists)

            analysis = requests.get(
                f'https://www.chosic.com/api/tools/audio-features/{track_id}',
                headers=self.headers_chosic
            ).json()

            return self._parse_chosic_data(youtube_link, track_info, related_artists, analysis, sanitize, initial_data)
        except Exception as e:
            self.logger.error(f'Error when fetching song details with chosic api', skippable=True, base_error=e)
    
    def _parse_chosic_data(self,
                youtube_link: str | None = None,
                track_info: dict[str, dict | str] | None = None,
                related_artists: list[dict[str, str]] | None = None,
                analysis: dict[str, float] | None = None,
                sanitize: bool = False,
                initial_data: dict | None = None
            ) -> dict[str, str | list[str] | dict[str, dict]]:
        """Sanitize Chosic data by removing unnecessary fields."""
        if sanitize:
            if track_info:
                track_info = {
                    "name": track_info.get("name", ""),
                    "album": track_info.get("album", {}).get("name", ""),
                    "genres": track_info.get("genres", [])[:10]    # 2 genres * 5 artists
                }
            if related_artists:
                related_artists = [{
                    "name": artist.get("name", ""),
                    "genres": artist.get("genres", [])[:2]
                } for artist in related_artists[:5]]
            if analysis:
                analysis = {
                    key: analysis[key]
                    for key in analysis
                    if key not in {"id", "popularity"}
                }
        data = self.schema.copy() if initial_data is None else initial_data
        if youtube_link:
            data["details"]['link'] = youtube_link
        if track_info:
            data['details'].update(track_info)
        if related_artists:
            data['details']['related_artists'] = related_artists
        if analysis:
            data['analysis']['music'].update(analysis)
        return data

    def _fetch_youtube_link(self, song_name: str, artist_name: str) -> str | None:
        """Retrieve YouTube link based on track and artist name."""
        try:
            youtube_id = requests.get(
                f'https://www.chosic.com/api/tools/get-song-video?song={self._url_format(song_name)}&artist={self._url_format(artist_name)}',
                headers=self.headers_chosic
            ).json()
            return f"https://www.youtube.com/watch?v={youtube_id}" if youtube_id else None
        except Exception as e:
            self.logger.error(f'Error when fetching youtube link with chosic api', skippable=True, base_error=e)

    def _extract_genres_from_related_artists(self, related_artists: list[dict[str, str]]) -> list[str]:
        """Extract unique genres from related artists."""
        return list(UList([genre for artist in related_artists for genre in artist.get("genres", [])]))

    def analyze_song_sonoteller(
            self,
            youtube_link: str,
            sanitize: bool = False,
            initial_data: dict | None = None
        ) -> dict[str, str | list[str] | dict[str, dict]] | None:
        """Fetch Sonoteller audio analysis based on YouTube link with optional sanitization."""
        json_data = {
            'url': youtube_link,
            'user': 'web',
            'token': 'i95evCQoyT8gmwTmXHRewXB7cwXH2X69',
            'fp': '3daoao'
        }
        response = requests.post(
            'https://us-central1-sonochordal-415613.cloudfunctions.net/sonoteller_web_yt_api_multi_function',
            headers=self.headers_sonoteller,
            json=json_data
        ).json()

        if response.get("error"):
            error_msg = response["error"]
            if "quota" in error_msg.lower():
                raise RuntimeError("Quota limit exceeded today; Sonoteller access blocked for the day.")
            else:
                raise ConnectionError(error_msg)
        
        return self._parse_sonoteller_data(response["lyrics"], response["music"], sanitize, initial_data)
    
    def _parse_sonoteller_data(
            self,
            lyrics: dict[str, dict | list] | None,
            music: dict[str, dict] | None,
            sanitize: bool = False,
            initial_data: dict | None = None
        ) -> dict[str, str | list[str] | dict[str, dict]] | None:
        """Sanitize Sonoteller data by removing unnecessary fields."""
        if sanitize:
            if lyrics:
                lyrics = {
                    "explicit": lyrics.get("explicit", ""),
                    "flags": lyrics.get("flags", {}),
                    "keywords": lyrics.get("keywords", []),
                    "language": lyrics.get("language", ""),
                    "moods": dict(next(iter(mood.items())) for mood in lyrics.get("moods", [])),
                    "summary": lyrics.get("summary", ""),
                    "themes": dict(next(iter(theme.items())) for theme in lyrics.get("themes", []))
                }
            if music:
                music = {
                    "bpm": music.get("bpm", ""),
                    "genres": music.get("genres", {}),
                    "instruments": music.get("instruments", []),
                    "key": music.get("key", ""),
                    "moods": music.get("moods", {}),
                    "styles": music.get("styles", {}),
                    "vocal family": music.get("vocal family", "")
                }
        data = self.schema.copy() if initial_data is None else initial_data
        if lyrics:
            data['analysis']['lyrics'].update(lyrics)
        if music:
            data['analysis']['music'].update(music)
        return data

    def analyze(self, audio_path: PathLike, sanitize: bool = False) -> dict[str, str | list[str] | dict[str, dict]]:
        """
        Perform full audio analysis with optional sanitization.

        Parameters:
            sanitize (bool): If True, removes IDs, URLs, dates, and popularity stats from the output.

        Returns:
            dict[str, Union[dict, str]]: A dictionary with sanitized or full song information.
        """
        if not (data := self.identify_song(audio_path)):
            raise ConnectionError("Song identification failed.")
        if not (data := self.analize_song_chosic(data['details']['title'], sanitize, data)):
            raise ConnectionError("Failed to retrieve song data from Chosic.")
        if not (data := self.analyze_song_sonoteller(data['details']['link'], sanitize, data)):
            raise ConnectionError("Failed to retrieve audio analysis data from Sonoteller.")
        return data