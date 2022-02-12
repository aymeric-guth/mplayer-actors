import os
import subprocess


ALLOWED_SHARES = (
    "Audio",
    "Video",
)
ENV = os.getenv("HOME")
ENV_PATH = f"{ENV}/.av-mp/"
MOUNT_POINT = f"{ENV}/.av-mp/mount_point/"
subprocess.run(["mkdir", "-p", MOUNT_POINT])

script_path = "/Desktop/Network/mplayer/"
script_name = "mpv_av_test"
mpv_profile_path = f"{os.getenv('HOME')}/.config/mpv/mpv.conf"
subprocess.run(["cp", f"{ENV}{script_path}{script_name}.js", ENV_PATH])
playlist_file = f"{ENV_PATH}playlist.txt"

PATH = [ MOUNT_POINT ]

ROOT = ( "shared", )
MUSIC_PATH = ( "shared", "Audio" )
VIDEO_PATH = ( "shared", "Video" )
MUSIC_TODO = ( "shared", "Audio", "Music.ToDo", "1st Pass", )

extensions_audio = {".mp3", ".flac", ".m4a", ".ogg", '.wav'}
extensions_video = {".mkv", ".avi", ".mp4", '.wmv'}

extensions_all = extensions_audio | extensions_video
extensions_mpv = extensions_audio | extensions_video
extensions_all_regex = '|'.join(extensions_all)

LOOP_DEFAULT = 1
VOLUME_DEFAULT = 100
LOOP_FLAG_DEFAULT = False

AUDIO_LANG = "eng"
SUBTITLES_LANG = "eng"

# 0 = Main Disp, 1 = Satellite Disp
DEFAULT_DISPLAY = 0
auto_fix_bad_encoding = True

USERNAME = 'yul'
PASSWORD = 'tXALFunQ1q2vY5kOmPBdV8rFTlRg8U9C0zkPNyq38z76F1ZgLs7NAX6ra7GksHeRCfF7Ej3BrBX9TACOg1QMxLdcJhoHas9j5qDorUTit7BTsSnaUrbj650MYOFcZPJxseqrMbv6kHvi0mSp9R0IXq10heEP4lBRxAXxD5nB2t8Wqrjiwicrpy2s29b83mggWysLpL8ub7rQeWzYV7q32RAlRQRfdsKbryJ8lwPMzoxrPrkgNqIp1SXjzHkO7f0l'

volume = VOLUME_DEFAULT
loop = LOOP_DEFAULT
