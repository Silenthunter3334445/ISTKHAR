import os
import re
from typing import Union

import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython import VideosSearch, Playlist


API_URL = os.environ.get(
    "SHRUTI_API_URL",
    "https://api01.shrutibots.site",
)

API_KEY = os.environ.get(
    "SHRUTI_API_KEY",
    "ShrutiBots7EhoL3cMjnYD3VEhQDIA",
)

DOWNLOAD_DIR = "downloads"


def time_to_seconds(value):
    """Convert HH:MM:SS / MM:SS to seconds safely."""
    if not value:
        return 0

    try:
        parts = str(value).strip().split(":")
        seconds = 0

        for part in parts:
            seconds = seconds * 60 + int(part)

        return seconds
    except (ValueError, TypeError):
        return 0


def clean_youtube_url(link: str) -> str:
    """Remove unnecessary YouTube URL parameters."""
    if not link:
        return ""

    link = str(link).strip()

    if "youtube.com/watch" in link and "v=" in link:
        video_id = link.split("v=", 1)[1].split("&", 1)[0]
        return f"https://www.youtube.com/watch?v={video_id}"

    if "youtu.be/" in link:
        video_id = link.split("youtu.be/", 1)[1].split("?", 1)[0]
        return f"https://www.youtube.com/watch?v={video_id}"

    return link.split("&", 1)[0]


def get_video_id(link: str):
    """Extract YouTube video ID."""
    if not link:
        return None

    link = str(link).strip()

    if "v=" in link:
        return link.split("v=", 1)[1].split("&", 1)[0]

    if "youtu.be/" in link:
        return link.split("youtu.be/", 1)[1].split("?", 1)[0]

    return link


async def download_song(link: str) -> Union[str, None]:
    video_id = get_video_id(link)

    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.mp3",
    )

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        timeout = aiohttp.ClientTimeout(total=300)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{API_URL}/download",
                params={
                    "url": video_id,
                    "type": "audio",
                    "api_key": API_KEY,
                },
            ) as response:

                if response.status != 200:
                    print(
                        f"Audio API returned HTTP {response.status}"
                    )
                    return None

                with open(file_path, "wb") as file:
                    async for chunk in response.content.iter_chunked(
                        131072
                    ):
                        file.write(chunk)

        if (
            os.path.exists(file_path)
            and os.path.getsize(file_path) > 0
        ):
            return file_path

        return None

    except Exception as error:
        print(f"Audio download error: {error}")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        return None


async def download_video(link: str) -> Union[str, None]:
    video_id = get_video_id(link)

    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"{video_id}.mp4",
    )

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        timeout = aiohttp.ClientTimeout(total=600)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"{API_URL}/download",
                params={
                    "url": video_id,
                    "type": "video",
                    "api_key": API_KEY,
                },
            ) as response:

                if response.status != 200:
                    print(
                        f"Video API returned HTTP {response.status}"
                    )
                    return None

                with open(file_path, "wb") as file:
                    async for chunk in response.content.iter_chunked(
                        131072
                    ):
                        file.write(chunk)

        if (
            os.path.exists(file_path)
            and os.path.getsize(file_path) > 0
        ):
            return file_path

        return None

    except Exception as error:
        print(f"Video download error: {error}")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        return None


class YouTubeAPI:

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        )

    async def exists(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + str(link)

        if not link:
            return False

        return bool(re.search(self.regex, link))

    async def url(
        self,
        message_1: Message,
    ) -> Union[str, None]:

        messages = [message_1]

        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:

            if message.entities:
                for entity in message.entities:

                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption

                        if not text:
                            continue

                        return text[
                            entity.offset:
                            entity.offset + entity.length
                        ]

                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url

            if message.caption_entities:
                for entity in message.caption_entities:

                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url

                    if entity.type == MessageEntityType.URL:
                        text = message.caption

                        if not text:
                            continue

                        return text[
                            entity.offset:
                            entity.offset + entity.length
                        ]

        return None

    async def _search(self, query: str, limit=1):
        """Safe YouTube search."""

        if not query:
            return []

        query = str(query).strip()

        if not query:
            return []

        try:
            search = VideosSearch(
                query,
                limit=limit,
            )

            data = await search.next()

            if not data:
                return []

            return data.get("result") or []

        except Exception as error:
            print(f"YouTube search error: {error}")
            return []

    async def details(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + str(link)

        link = clean_youtube_url(link)

        results = await self._search(link, 1)

        if not results:
            return (
                None,
                None,
                0,
                None,
                None,
            )

        result = results[0]

        title = result.get("title", "Unknown")
        duration_min = result.get("duration")
        thumbnail = None
        vidid = result.get("id")

        thumbnails = result.get("thumbnails") or []

        if thumbnails:
            thumbnail = thumbnails[0].get("url")

            if thumbnail:
                thumbnail = thumbnail.split("?")[0]

        duration_sec = time_to_seconds(duration_min)

        return (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        )

    async def title(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        details = await self.details(link, videoid)

        return details[0]

    async def duration(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        details = await self.details(link, videoid)

        return details[1]

    async def thumbnail(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        details = await self.details(link, videoid)

        return details[3]

    async def video(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + str(link)

        try:
            downloaded_file = await download_video(link)

            if downloaded_file:
                return 1, downloaded_file

            return 0, "Video download failed."

        except Exception as error:
            print(f"Video error: {error}")

            return 0, f"Video download error: {error}"

    async def playlist(
        self,
        link,
        limit,
        user_id,
        videoid: Union[bool, str] = None,
    ):

        if videoid:
            link = self.listbase + str(link)

        if not link:
            return []

        try:
            playlist = await Playlist.get(link)

            videos = playlist.get("videos") or []

            ids = []

            for data in videos[:limit]:

                if not data:
                    continue

                video_id = data.get("id")

                if video_id:
                    ids.append(video_id)

            return ids

        except Exception as error:
            print(f"Playlist error: {error}")
            return []

    async def track(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + str(link)

        link = clean_youtube_url(link)

        results = await self._search(link, 1)

        if not results:
            return None, None

        result = results[0]

        title = result.get("title", "Unknown")
        duration_min = result.get("duration")
        vidid = result.get("id")
        yturl = result.get("link")

        thumbnails = result.get("thumbnails") or []

        thumbnail = None

        if thumbnails:
            thumbnail = thumbnails[0].get("url")

            if thumbnail:
                thumbnail = thumbnail.split("?")[0]

        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }

        return track_details, vidid

    async def formats(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + str(link)

        link = clean_youtube_url(link)

        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:

                data = ydl.extract_info(
                    link,
                    download=False,
                )

                formats_available = []

                for fmt in data.get("formats", []):

                    try:
                        if "dash" in str(
                            fmt.get("format", "")
                        ).lower():
                            continue

                        formats_available.append(
                            {
                                "format": fmt.get("format"),
                                "filesize": fmt.get("filesize"),
                                "format_id": fmt.get("format_id"),
                                "ext": fmt.get("ext"),
                                "format_note": fmt.get("format_note"),
                                "yturl": link,
                            }
                        )

                    except Exception:
                        continue

                return formats_available, link

        except Exception as error:
            print(f"Formats error: {error}")
            return [], link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + str(link)

        link = clean_youtube_url(link)

        results = await self._search(link, 10)

        if not results:
            return (
                None,
                None,
                None,
                None,
            )

        try:
            result = results[query_type]
        except IndexError:
            result = results[0]

        title = result.get("title")
        duration_min = result.get("duration")
        vidid = result.get("id")

        thumbnails = result.get("thumbnails") or []

        thumbnail = None

        if thumbnails:
            thumbnail = thumbnails[0].get("url")

            if thumbnail:
                thumbnail = thumbnail.split("?")[0]

        return (
            title,
            duration_min,
            thumbnail,
            vidid,
        )

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + str(link)

        try:

            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)

            if downloaded_file:
                return downloaded_file, True

            return None, False

        except Exception as error:
            print(f"Download error: {error}")
            return None, False


YouTube = YouTubeAPI()
