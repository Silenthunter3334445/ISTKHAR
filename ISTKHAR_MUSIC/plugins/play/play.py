import random
import string

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from ISTKHAR_MUSIC import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from ISTKHAR_MUSIC.core.call import noor
from ISTKHAR_MUSIC.utils import seconds_to_min, time_to_seconds
from ISTKHAR_MUSIC.utils.channelplay import get_channeplayCB
from ISTKHAR_MUSIC.utils.decorators.language import languageCB
from ISTKHAR_MUSIC.utils.decorators.play import PlayWrapper
from ISTKHAR_MUSIC.utils.formatters import formats
from ISTKHAR_MUSIC.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from ISTKHAR_MUSIC.utils.logger import play_logs
from ISTKHAR_MUSIC.utils.stream.stream import stream
from config import BANNED_USERS, lyrical


def youtube_error_message(_):
    try:
        return _["play_3"]
    except Exception:
        return "❌ Unable to find the requested song. Please try another query."


@app.on_message(
    filters.command(
        [
            "play",
            "vplay",
            "cplay",
            "cvplay",
            "playforce",
            "vplayforce",
            "cplayforce",
            "cvplayforce",
        ]
    )
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )

    plist_id = None
    slider = False
    plist_type = None
    spotify = None
    details = None
    track_id = None
    img = None
    cap = None
    streamtype = None
    query = None

    user_id = message.from_user.id
    user_name = message.from_user.first_name

    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )

    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )

    # ============================================================
    # TELEGRAM AUDIO
    # ============================================================

    if audio_telegram:
        if audio_telegram.file_size > 104857600:
            return await mystic.edit_text(_["play_5"])

        duration = audio_telegram.duration or 0

        if duration > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(
                    config.DURATION_LIMIT_MIN,
                    app.mention,
                )
            )

        file_path = await Telegram.get_filepath(audio=audio_telegram)

        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(
                audio_telegram,
                audio=True,
            )
            dur = await Telegram.get_duration(
                audio_telegram,
                file_path,
            )

            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        return

    # ============================================================
    # TELEGRAM VIDEO
    # ============================================================

    elif video_telegram:
        if message.reply_to_message.document:
            try:
                file_name = video_telegram.file_name or ""
                ext = file_name.split(".")[-1]

                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(" | ".join(formats))
                    )
            except Exception:
                return await mystic.edit_text(
                    _["play_7"].format(" | ".join(formats))
                )

        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await mystic.edit_text(_["play_8"])

        file_path = await Telegram.get_filepath(video=video_telegram)

        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(
                video_telegram,
                file_path,
            )

            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        return

    # ============================================================
    # URL
    # ============================================================

    elif url:

        # ========================================================
        # YOUTUBE
        # ========================================================

        if await YouTube.exists(url):

            if "playlist" in url.lower():
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )

                    if not details:
                        return await mystic.edit_text(
                            youtube_error_message(_)
                        )

                except Exception as e:
                    print(f"YouTube playlist error: {e}")
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                streamtype = "playlist"
                plist_type = "yt"

                try:
                    if "list=" in url:
                        plist_id = url.split("list=", 1)[1].split("&", 1)[0]
                    else:
                        plist_id = None
                except Exception:
                    plist_id = None

                if not plist_id:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]

            else:
                try:
                    details, track_id = await YouTube.track(url)
                except Exception as e:
                    print(f"YouTube track error: {e}")
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                # IMPORTANT:
                # YouTube.track() can return (None, None)
                if not details or not track_id:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                streamtype = "youtube"

                img = details.get("thumb")

                if not img:
                    img = config.YOUTUBE_IMG_URL if hasattr(
                        config,
                        "YOUTUBE_IMG_URL",
                    ) else config.PLAYLIST_IMG_URL

                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min") or "Live",
                )

        # ========================================================
        # SPOTIFY
        # ========================================================

        elif await Spotify.valid(url):
            spotify = True

            if (
                not config.SPOTIFY_CLIENT_ID
                and not config.SPOTIFY_CLIENT_SECRET
            ):
                return await mystic.edit_text(
                    "» sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n\n"
                    "ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )

            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)

                    if not details:
                        return await mystic.edit_text(
                            youtube_error_message(_)
                        )

                except Exception as e:
                    print(f"Spotify track error: {e}")
                    return await mystic.edit_text(_["play_3"])

                streamtype = "youtube"
                img = details.get("thumb")
                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min") or "Unknown",
                )

            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)

                    if not details or not plist_id:
                        return await mystic.edit_text(_["play_3"])

                except Exception as e:
                    print(f"Spotify playlist error: {e}")
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_11"].format(
                    app.mention,
                    message.from_user.mention,
                )

            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)

                    if not details or not plist_id:
                        return await mystic.edit_text(_["play_3"])

                except Exception as e:
                    print(f"Spotify album error: {e}")
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_11"].format(
                    app.mention,
                    message.from_user.mention,
                )

            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)

                    if not details or not plist_id:
                        return await mystic.edit_text(_["play_3"])

                except Exception as e:
                    print(f"Spotify artist error: {e}")
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_11"].format(
                    message.from_user.first_name
                )

            else:
                return await mystic.edit_text(_["play_15"])

        # ========================================================
        # APPLE MUSIC
        # ========================================================

        elif await Apple.valid(url):

            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)

                    if not details:
                        return await mystic.edit_text(_["play_3"])

                except Exception as e:
                    print(f"Apple track error: {e}")
                    return await mystic.edit_text(_["play_3"])

                streamtype = "youtube"
                img = details.get("thumb")
                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min") or "Unknown",
                )

            elif "playlist" in url:
                spotify = True

                try:
                    details, plist_id = await Apple.playlist(url)

                    if not details or not plist_id:
                        return await mystic.edit_text(_["play_3"])

                except Exception as e:
                    print(f"Apple playlist error: {e}")
                    return await mystic.edit_text(_["play_3"])

                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_12"].format(
                    app.mention,
                    message.from_user.mention,
                )
                img = url

            else:
                return await mystic.edit_text(_["play_3"])

        # ========================================================
        # RESSO
        # ========================================================

        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)

                if not details:
                    return await mystic.edit_text(_["play_3"])

            except Exception as e:
                print(f"Resso error: {e}")
                return await mystic.edit_text(_["play_3"])

            streamtype = "youtube"
            img = details.get("thumb")
            cap = _["play_10"].format(
                details.get("title", "Unknown"),
                details.get("duration_min") or "Unknown",
            )

        # ========================================================
        # SOUNDCLOUD
        # ========================================================

        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)

                if not details:
                    return await mystic.edit_text(_["play_3"])

            except Exception as e:
                print(f"SoundCloud error: {e}")
                return await mystic.edit_text(_["play_3"])

            duration_sec = details.get("duration_sec", 0) or 0

            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        app.mention,
                    )
                )

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await mystic.delete()

        # ========================================================
        # DIRECT / M3U8 / INDEX URL
        # ========================================================

        else:
            try:
                await noor.stream_call(url)

            except NoActiveGroupCall:
                await mystic.edit_text(_["black_9"])

                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=_["play_17"],
                )

            except Exception as e:
                return await mystic.edit_text(
                    _["general_2"].format(type(e).__name__)
                )

            await mystic.edit_text(_["str_2"])

            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )

            except Exception as e:
                ex_type = type(e).__name__
                err = (
                    e
                    if ex_type == "AssistantErr"
                    else _["general_2"].format(ex_type)
                )
                return await mystic.edit_text(err)

            return await play_logs(
                message,
                streamtype="M3u8 or Index Link",
            )

    # ============================================================
    # SEARCH QUERY
    # ============================================================

    else:
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)

            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )

        slider = True

        try:
            query = message.text.split(None, 1)[1]
        except Exception:
            return await mystic.edit_text(
                youtube_error_message(_)
            )

        if "-v" in query:
            query = query.replace("-v", "").strip()

        if not query:
            return await mystic.edit_text(
                youtube_error_message(_)
            )

        try:
            details, track_id = await YouTube.track(query)

        except Exception as e:
            print(f"YouTube search error: {e}")
            return await mystic.edit_text(
                youtube_error_message(_)
            )

        # IMPORTANT FIX
        if not details or not track_id:
            return await mystic.edit_text(
                youtube_error_message(_)
            )

        streamtype = "youtube"

    # ============================================================
    # DIRECT PLAY
    # ============================================================

    if str(playmode) == "Direct":

        if not plist_type:

            # IMPORTANT FIX
            if not details or not isinstance(details, dict):
                return await mystic.edit_text(
                    youtube_error_message(_)
                )

            duration_min = details.get("duration_min")

            if duration_min:
                duration_sec = time_to_seconds(duration_min)

                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(
                            config.DURATION_LIMIT_MIN,
                            app.mention,
                        )
                    )

            else:
                if not track_id:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )

        except Exception as e:
            ex_type = type(e).__name__

            err = (
                e
                if ex_type == "AssistantErr"
                else _["general_2"].format(ex_type)
            )

            return await mystic.edit_text(err)

        await mystic.delete()

        return await play_logs(
            message,
            streamtype=streamtype,
        )

    # ============================================================
    # NON DIRECT MODE
    # ============================================================

    else:

        if plist_type:

            if not plist_id:
                return await mystic.edit_text(
                    youtube_error_message(_)
                )

            ran_hash = "".join(
                random.choices(
                    string.ascii_uppercase + string.digits,
                    k=10,
                )
            )

            lyrical[ran_hash] = plist_id

            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )

            await mystic.delete()

            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(buttons),
            )

            return await play_logs(
                message,
                streamtype=f"Playlist : {plist_type}",
            )

        # ========================================================
        # YOUTUBE SEARCH SLIDER
        # ========================================================

        else:

            if not details or not isinstance(details, dict):
                return await mystic.edit_text(
                    youtube_error_message(_)
                )

            if slider:

                if not track_id:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                thumbnail = details.get("thumb")

                if not thumbnail:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                title = details.get(
                    "title",
                    "Unknown",
                )

                duration = details.get(
                    "duration_min"
                ) or "Live"

                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                await mystic.delete()

                await message.reply_photo(
                    photo=thumbnail,
                    caption=_["play_10"].format(
                        title.title(),
                        duration,
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

                return await play_logs(
                    message,
                    streamtype="Searched on Youtube",
                )

            else:

                if not track_id:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                if not img:
                    img = details.get("thumb")

                if not img:
                    return await mystic.edit_text(
                        youtube_error_message(_)
                    )

                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )

                await mystic.delete()

                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

                return await play_logs(
                    message,
                    streamtype="URL Searched Inline",
                )


# ================================================================
# MUSIC STREAM CALLBACK
# ================================================================

@app.on_callback_query(
    filters.regex("MusicStream") & ~BANNED_USERS
)
@languageCB
async def play_music(client, CallbackQuery, _):

    try:
        callback_data = CallbackQuery.data.strip()
        callback_request = callback_data.split(None, 1)[1]

        vidid, user_id, mode, cplay, fplay = callback_request.split(
            "|"
        )

    except Exception:
        return

    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(
                _["playcb_1"],
                show_alert=True,
            )
        except Exception:
            return

    try:
        chat_id, channel = await get_channeplayCB(
            _,
            cplay,
            CallbackQuery,
        )
    except Exception:
        return

    user_name = CallbackQuery.from_user.first_name

    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except Exception:
        pass

    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel)
        if channel
        else _["play_1"]
    )

    try:
        details, track_id = await YouTube.track(
            vidid,
            True,
        )

    except Exception as e:
        print(f"YouTube callback error: {e}")

        return await mystic.edit_text(
            youtube_error_message(_)
        )

    # IMPORTANT FIX
    if not details or not track_id:
        return await mystic.edit_text(
            youtube_error_message(_)
        )

    duration_min = details.get("duration_min")

    if duration_min:
        duration_sec = time_to_seconds(duration_min)

        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(
                    config.DURATION_LIMIT_MIN,
                    app.mention,
                )
            )

    else:
        buttons = livestream_markup(
            _,
            track_id,
            CallbackQuery.from_user.id,
            mode,
            "c" if cplay == "c" else "g",
            "f" if fplay else "d",
        )

        return await mystic.edit_text(
            _["play_13"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None

    try:
        await stream(
            _,
            mystic,
            CallbackQuery.from_user.id,
            details,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="youtube",
            forceplay=ffplay,
        )

    except Exception as e:
        ex_type = type(e).__name__

        err = (
            e
            if ex_type == "AssistantErr"
            else _["general_2"].format(ex_type)
        )

        return await mystic.edit_text(err)

    return await mystic.delete()


# ================================================================
# ANONYMOUS ADMIN
# ================================================================

@app.on_callback_query(
    filters.regex("AnonymousAdmin") & ~BANNED_USERS
)
async def piyush_check(client, CallbackQuery):

    try:
        await CallbackQuery.answer(
            "» ʀᴇᴠᴇʀᴛ ʙᴀᴄᴋ ᴛᴏ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ :\n\n"
            "ᴏᴘᴇɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs.\n"
            "-> ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs\n"
            "-> ᴄʟɪᴄᴋ ᴏɴ ʏᴏᴜʀ ɴᴀᴍᴇ\n"
            "-> ᴜɴᴄʜᴇᴄᴋ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs.",
            show_alert=True,
        )
    except Exception:
        pass


# ================================================================
# PLAYLIST CALLBACK
# ================================================================

@app.on_callback_query(
    filters.regex("noorPlaylists") & ~BANNED_USERS
)
@languageCB
async def play_playlists_command(client, CallbackQuery, _):

    try:
        callback_data = CallbackQuery.data.strip()
        callback_request = callback_data.split(None, 1)[1]

        (
            videoid,
            user_id,
            ptype,
            mode,
            cplay,
            fplay,
        ) = callback_request.split("|")

    except Exception:
        return

    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(
                _["playcb_1"],
                show_alert=True,
            )
        except Exception:
            return

    try:
        chat_id, channel = await get_channeplayCB(
            _,
            cplay,
            CallbackQuery,
        )
    except Exception:
        return

    user_name = CallbackQuery.from_user.first_name

    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except Exception:
        pass

    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel)
        if channel
        else _["play_1"]
    )

    videoid = lyrical.get(videoid)

    if not videoid:
        return await mystic.edit_text(
            youtube_error_message(_)
        )

    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    spotify = True
    result = None

    # ============================================================
    # YOUTUBE PLAYLIST
    # ============================================================

    if ptype == "yt":
        spotify = False

        try:
            result = await YouTube.playlist(
                videoid,
                config.PLAYLIST_FETCH_LIMIT,
                CallbackQuery.from_user.id,
                True,
            )

            if not result:
                return await mystic.edit_text(
                    youtube_error_message(_)
                )

        except Exception as e:
            print(f"Playlist callback error: {e}")
            return await mystic.edit_text(_["play_3"])

    # ============================================================
    # SPOTIFY PLAYLIST
    # ============================================================

    elif ptype == "spplay":
        try:
            result, spotify_id = await Spotify.playlist(
                videoid
            )

            if not result:
                return await mystic.edit_text(_["play_3"])

        except Exception as e:
            print(f"Spotify playlist callback error: {e}")
            return await mystic.edit_text(_["play_3"])

    # ============================================================
    # SPOTIFY ALBUM
    # ============================================================

    elif ptype == "spalbum":
        try:
            result, spotify_id = await Spotify.album(
                videoid
            )

            if not result:
                return await mystic.edit_text(_["play_3"])

        except Exception as e:
            print(f"Spotify album callback error: {e}")
            return await mystic.edit_text(_["play_3"])

    # ============================================================
    # SPOTIFY ARTIST
    # ============================================================

    elif ptype == "spartist":
        try:
            result, spotify_id = await Spotify.artist(
                videoid
            )

            if not result:
                return await mystic.edit_text(_["play_3"])

        except Exception as e:
            print(f"Spotify artist callback error: {e}")
            return await mystic.edit_text(_["play_3"])

    # ============================================================
    # APPLE PLAYLIST
    # ============================================================

    elif ptype == "apple":
        try:
            result, apple_id = await Apple.playlist(
                videoid,
                True,
            )

            if not result:
                return await mystic.edit_text(_["play_3"])

        except Exception as e:
            print(f"Apple playlist callback error: {e}")
            return await mystic.edit_text(_["play_3"])

    else:
        return await mystic.edit_text(_["play_3"])

    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="playlist",
            spotify=spotify,
            forceplay=ffplay,
        )

    except Exception as e:
        ex_type = type(e).__name__

        err = (
            e
            if ex_type == "AssistantErr"
            else _["general_2"].format(ex_type)
        )

        return await mystic.edit_text(err)

    return await mystic.delete()


# ================================================================
# SLIDER CALLBACK
# ================================================================

@app.on_callback_query(
    filters.regex("slider") & ~BANNED_USERS
)
@languageCB
async def slider_queries(client, CallbackQuery, _):

    try:
        callback_data = CallbackQuery.data.strip()
        callback_request = callback_data.split(None, 1)[1]

        (
            what,
            rtype,
            query,
            user_id,
            cplay,
            fplay,
        ) = callback_request.split("|")

    except Exception:
        return

    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(
                _["playcb_1"],
                show_alert=True,
            )
        except Exception:
            return

    try:
        rtype = int(rtype)
    except Exception:
        rtype = 0

    what = str(what)

    # ============================================================
    # NEXT
    # ============================================================

    if what == "F":

        if rtype == 9:
            query_type = 0
        else:
            query_type = rtype + 1

        try:
            await CallbackQuery.answer(
                _["playcb_2"]
            )
        except Exception:
            pass

        try:
            (
                title,
                duration_min,
                thumbnail,
                vidid,
            ) = await YouTube.slider(
                query,
                query_type,
            )

        except Exception as e:
            print(f"Slider forward error: {e}")
            return await CallbackQuery.answer(
                "❌ Unable to load result.",
                show_alert=True,
            )

        if not title or not vidid:
            return await CallbackQuery.answer(
                "❌ No result found.",
                show_alert=True,
            )

        if not thumbnail:
            return await CallbackQuery.answer(
                "❌ Thumbnail unavailable.",
                show_alert=True,
            )

        buttons = slider_markup(
            _,
            vidid,
            user_id,
            query,
            query_type,
            cplay,
            fplay,
        )

        med = InputMediaPhoto(
            media=thumbnail,
            caption=_["play_10"].format(
                title.title(),
                duration_min or "Live",
            ),
        )

        return await CallbackQuery.edit_message_media(
            media=med,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    # ============================================================
    # PREVIOUS
    # ============================================================

    if what == "B":

        if rtype == 0:
            query_type = 9
        else:
            query_type = rtype - 1

        try:
            await CallbackQuery.answer(
                _["playcb_2"]
            )
        except Exception:
            pass

        try:
            (
                title,
                duration_min,
                thumbnail,
                vidid,
            ) = await YouTube.slider(
                query,
                query_type,
            )

        except Exception as e:
            print(f"Slider backward error: {e}")
            return await CallbackQuery.answer(
                "❌ Unable to load result.",
                show_alert=True,
            )

        if not title or not vidid:
            return await CallbackQuery.answer(
                "❌ No result found.",
                show_alert=True,
            )

        if not thumbnail:
            return await CallbackQuery.answer(
                "❌ Thumbnail unavailable.",
                show_alert=True,
            )

        buttons = slider_markup(
            _,
            vidid,
            user_id,
            query,
            query_type,
            cplay,
            fplay,
        )

        med = InputMediaPhoto(
            media=thumbnail,
            caption=_["play_10"].format(
                title.title(),
                duration_min or "Live",
            ),
        )

        return await CallbackQuery.edit_message_media(
            media=med,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
