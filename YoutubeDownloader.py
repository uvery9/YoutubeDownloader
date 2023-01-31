# import importlib
from pytube import YouTube
from pytube import Stream
from pytube import StreamQuery
from pytube.cli import on_progress
from configparser import ConfigParser
import os
import pathlib
import re

DEFAULT_VIDEO_LIMIT_SIZE = 200


def get_config_file() -> str:
    config_file = 'youtube.downloader.config.ini'
    app_dir = pyinstaller_getcwd()
    return os.path.join(app_dir, config_file)


def save_download_path_to_config(download_path: str, config_file: str):
    config = ConfigParser()
    if (os.path.exists(config_file)):
        try:
            with open(config_file) as f:
                config.read_file(f)
            config.set('Settings', 'download_path', download_path)
            with open(config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"! {str(e)}")


def get_download_path_not_none(download_path: str, config_file: str):
    if (not pathlib.Path(download_path).exists()):
        if os.name == "nt":
            download_path = f"{os.getenv('USERPROFILE')}\\Downloads"
        else:  # PORT: For *Nix systems
            download_path = f"{os.getenv('HOME')}/Downloads"
        print(
            f'\n!  WARNING: STRONGLY RECOMMENDED TO SPECIFY YOUR download_path in "{config_file}"\n    Now use "{download_path}"')
        save_download_path_to_config(download_path, config_file)
    print(f"> download_path = {download_path}")
    return download_path


def get_download_path(config_file: str):
    config = ConfigParser()
    if (os.path.exists(config_file)):
        try:
            with open(config_file) as f:
                config.read_file(f)
                return get_download_path_not_none(config['Settings']['download_path'], config_file)
        except:
            return get_download_path_not_none("ERROR_OCCUR", config_file)
    else:
        config.add_section('Settings')
        config['Settings']['download_path'] = "NOT_SET"
        config['Settings']['download_higher_resolution_such_as_1080P'] = "False"
        config['Settings']['youtube_url_history'] = "NOT_SET"
        config['Settings']['max_size_in_MB_of_progressive_video'] = str(
            DEFAULT_VIDEO_LIMIT_SIZE)
        with open(config_file, 'w') as f:
            config.write(f)
    return get_download_path_not_none("NOT_SET", config_file)


def on_complete(stream, file_path):
    print(f"\n> Downloaded to file: \n    {os.path.basename(file_path)}\n")


def get_file_size(stream: Stream) -> str:
    return human_readable_size(stream.filesize)

# def sizeof_fmt(num, suffix="B"):
#     for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
#         if abs(num) < 1024.0:
#             return f"{num:3.1f}{unit}{suffix}"
#         num /= 1024.0
#     return f"{num:.1f}Yi{suffix}"


def human_readable_size(size: int, decimal_places=2) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def get_highest_resolution_progressive_stream(streams: StreamQuery) -> Stream:
    # stream.download() # progressive=True, 视频和文件在同一个文件中, 1080P及以上需要合并视频+音频,下载两个文件
    # stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    # yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first().download()
    stream = streams.get_highest_resolution()
    print(
        f"> Parsing stream info complete, start to save stream to file[size = {get_file_size(stream)}]...")
    return stream


def get_max_size_in_MB_of_progressive_video(config_file: str) -> int:
    config = ConfigParser()
    if (os.path.exists(config_file)):
        try:
            with open(config_file) as f:
                config.read_file(f)
                return int(config['Settings']['max_size_in_MB_of_progressive_video'])
        except:
            return DEFAULT_VIDEO_LIMIT_SIZE
    return DEFAULT_VIDEO_LIMIT_SIZE


def is_need_to_download_1080P_or_more(config_file: str) -> bool:
    config = ConfigParser()
    if (os.path.exists(config_file)):
        try:
            with open(config_file) as f:
                config.read_file(f)
                return config['Settings']['download_higher_resolution_such_as_1080P'] == "True"
        except:
            return False
    return False


def save_youtube_url_to_config(youtube_url: str, config_file: str):
    config = ConfigParser()
    if (os.path.exists(config_file)):
        try:
            with open(config_file) as f:
                config.read_file(f)
            config.set('Settings', 'youtube_url_history', youtube_url)
            with open(config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"! {str(e)}")


def download_video_progressive_top_720P(streams: StreamQuery, download_path: str, file_name_ori: str, url: str):
    try:
        video = get_highest_resolution_progressive_stream(streams)
        video_resolution = str(video.resolution).upper()
        print(f"> Resolution of video: {video_resolution}")
        output_file = f"{file_name_ori}.{video_resolution}-YouTube.mp4"
        if (not isFileExist(download_path, output_file, video)):
            video.download(output_path=download_path,
                           filename=output_file)
            save_to_history(url, os.path.join(download_path, output_file))
            print_ffmpeg_rotated_cmd(download_path, output_file)
        else:
            print(
                f"> Video(with audio) file already downloaded:\n    {output_file}")
    except Exception as e:
        print(f"! {str(e)}")
        save_to_history(url, "download_video_progressive_top_720P failed!")


def isFileExist(folder: str, filename: str, stream: Stream = None) -> bool:
    file_path = os.path.join(folder, filename)
    if (stream == None):
        return os.path.exists(file_path)
    return check_if_file_is_complete(file_path, stream)


def pyinstaller_getcwd():
    import os
    import sys
    # determine if the application is a frozen `.exe` (e.g. pyinstaller --onefile)
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    # or a script file (e.g. `.py` / `.pyw`)
    elif __file__:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path


def IsStringNullOrEmpty(value: str):
    return value is None or len(value) == 0

# 视频文件过大时, 尝试降低分辨率到 1080P


def use_proper_resolution(video: Stream, streams: StreamQuery) -> Stream:
    video_size = video.filesize
    video_size_human_readable = human_readable_size(video_size)
    config_file = get_config_file()
    VIDEO_LIMIT_SIZE = get_max_size_in_MB_of_progressive_video(config_file)
    if (video_size > VIDEO_LIMIT_SIZE * 1024 * 1024):
        print(
            f"> You could configure in {os.path.basename(config_file)}: max_size_in_MB_of_progressive_video = {VIDEO_LIMIT_SIZE} [MB]")
        resolution = str(video.resolution).lower()
        if (resolution != "1080p"):
            tip = f"> Video[{resolution}] is larger than {VIDEO_LIMIT_SIZE} MB[{video_size_human_readable}], the probability of failure is very high, try to download 1080P:"
            resolution_1080p = streams.filter(
                progressive=False, subtype="mp4", resolution="1080p").order_by("resolution").last()
            print(f"> {tip}\n    {resolution_1080p}")
            return resolution_1080p
        else:
            stream_p = streams.filter(
                progressive=False, subtype="mp4").order_by("resolution")
            print(f'. Streams:\n    {stream_p}\n')
            raise ValueError(
                f"Video[{resolution}] is larger than {VIDEO_LIMIT_SIZE} MB[{video_size_human_readable}], the probability of failure is very high")
    else:
        return video


def check_ffmpeg_exist() -> bool:
    import shutil
    return (shutil.which("ffmpeg") is not None)


def get_url_from_clipboard() -> str:
    try:
        import pyperclip
        url_from_clipboard = pyperclip.paste()
        if (not isinstance(url_from_clipboard, str)):
            return None
        url = (url_from_clipboard.splitlines()[0]).strip()
        if ("youtube.com" in url and "/" in url and "=" in url):
            return url
        elif ("youtube.com" in url and "/" in url and "shorts" in url):
            return url
        else:
            return None
    except:
        return None


def save_to_history(url: str, file_path: str):
    try:
        history_filename = "download.history.txt"
        app_dir = pyinstaller_getcwd()
        history_file = os.path.join(app_dir, history_filename)
        str_write_to_file = f"{url} -> \n    {file_path}\n"
        if (os.path.exists(history_file)):
            with open(history_file, 'a') as f:
                f.write(str_write_to_file)
        else:
            with open(history_file, 'w') as f:
                f.write(str_write_to_file)
    except:
        pass


def get_highest_resolution_streams(streams: StreamQuery) -> tuple[Stream, Stream]:
    video = streams.filter(progressive=False, subtype="mp4").order_by(
        "resolution").last()
    video_resolution = str(video.resolution).upper()
    video_resolution_num = re.sub("[^0-9]", "", video_resolution)
    RESOLUTION_LIMIT = 1080
    if (int(video_resolution_num) < RESOLUTION_LIMIT):
        raise AttributeError(
            f". Current {video_resolution} is less than {RESOLUTION_LIMIT}P, do not download video + audio files that need to be combined.")
    audio = streams.get_audio_only()
    return (video, audio)


def print_ffmpeg_rotated_cmd(download_path: str, output_file: str):
    if (check_ffmpeg_exist()):
        # rotation_angle = 90
        rotation_angle = 270
        rotated_file = output_file.replace(".mp4", ".rotated.mp4")
        ffmpeg_cmd = f'ffmpeg -i "{output_file}" -c copy -metadata:s:v:0 rotate={rotation_angle} "{rotated_file}"'
        print(
            f'\n> Run command to rotate video:\n    cd /d "{download_path}" && {ffmpeg_cmd} \n')


def check_if_file_is_complete(file_path: str, stream: Stream) -> bool:
    try:
        if (not os.path.exists(file_path)):
            return False
        file_size = os.path.getsize(file_path)
        filesize = stream.filesize
        print(
            f". File[{file_size} bytes], stream.filesize[{filesize} bytes], stream.filesize_approx[{stream.filesize_approx} bytes]")
        ret = (filesize - file_size) < 1024 * 1024
        if (not ret):
            os.remove(file_path)
        return ret
    except:
        return False


def check_integrity_of_video(download_path: str, video_file: str, callback_to_delete):
    # ffmpeg_cmd = f'ffmpeg -v error -i "Yoga - Gymnastics with Lera.1080P-YouTube.mp4" -f null - >error.log 2>&1'
    # ffmpeg_cmd = f' cd /d "{download_path}" && ffmpeg -v error -i "{video_file}" -f null - '
    # cmd_keep = f'cmd /c "{ffmpeg_cmd}"'
    # os.system(cmd_keep)
    import subprocess
    # run_ret = subprocess.call(
    #     ['ffmpeg', '-v', 'error', '-i', f'{video_file}', '-f', 'null', '-'], cwd=download_path)
    if (isFileExist(download_path, video_file)):
        print(f"> Start checking video file integrity with ffmpeg...")
        run_ret_output = subprocess.check_output(
            ['ffmpeg', '-v', 'error', '-i', f'{video_file}', '-f', 'null', '-'], cwd=download_path, stderr=subprocess.STDOUT, text=True)  # , shell=True
        if (len(run_ret_output) != 0):
            print(
                f"! Video file is incomplete: \n    {video_file}\n! Error detail:\n{run_ret_output}! Error detail^^^")

        else:
            # intput_keys = input(
            #     'Video file is complete, do you want to delete intermediate files? \n  Press Y to DELETE, otherwise CANCEL: ')
            # if (len(intput_keys) > 0):
            #     input_char = intput_keys[0]
            #     if (input_char.lower() == 'y'):
            #         print(f'> Deleting intermediate files...')
            #         callback_to_delete()
            #     else:
            #         print("Your choise is: DO NOTHING.")
            # else:
            #     print("Your choise is: DO NOTHING.")
            print("> Video file is complete, deleting intermediate files...")
            callback_to_delete()
        print(f"> Check video file integrity with ffmpeg ends.")


def main():
    config_file = get_config_file()
    print("*** YoutubeDownloader version 1.0.1 Copyright (c) 2022 Carlo R. All Rights Reserved. ***")
    print("*** Contact us at uvery6@gmail.com ")
    print("> START...")
    print(f"> You could configure software in:\n    {config_file}")
    download_path = get_download_path(config_file)
    # if (youtube_url == None or len(youtube_url) < 8):
    #     print('\n!  ERROR: MUST SPECIFY youtube_url in "config.ini"\n')
    #     return
    url_from_clipboard = get_url_from_clipboard()
    if (url_from_clipboard is not None):
        # youtube_url = input(
        #     f"Paste your video link here [from clipboard = {url_from_clipboard}, press ENTER key to use]: ") or url_from_clipboard
        youtube_url = url_from_clipboard
    else:
        youtube_url = str(input(f"\nPaste your video link here: ")).strip()
    if (IsStringNullOrEmpty(youtube_url) or "/" not in youtube_url):
        print(f'\n!  ERROR: Invalid input: {youtube_url}\n')
        return
    print(f"> Download video from {youtube_url}")
    save_youtube_url_to_config(youtube_url, config_file)
    yt = YouTube(youtube_url, on_progress_callback=on_progress,
                 on_complete_callback=on_complete)  # proxies=my_proxies
    title = yt.title
    author = yt.author
    print(f'> Video title:\n    {title}, \n  Author: {author}\n')
    author_ori = re.sub(r'[\\/*?:"<>|&]', ".", author)
    file_name_ori = f"[{author_ori}]" + re.sub(r'[\\/*?:"<>|&]', "-", title)
    if (file_name_ori.endswith(".")):
        file_name_ori = file_name_ori[0: -1]
    if (file_name_ori != title):
        print(f'. Video format-title:\n    {file_name_ori}')
    print("> The URL is being resolved, please be patient...")
    streams = yt.streams
    # symbols can't be use in filename, '&' can't be use at ffmpeg cmd.
    if (is_need_to_download_1080P_or_more(config_file)):
        try:
            video, audio = get_highest_resolution_streams(streams)
            video = use_proper_resolution(video, streams)
            video_resolution = str(video.resolution).upper()
            print(f"> [Part]Resolution of video: {video_resolution}")
            file_name = f"{file_name_ori}.{video_resolution}"
            youtube_suffix = "-YouTube"
            youtube_part_prefix = f"{youtube_suffix}.Part"
            video_file = f"{file_name}{youtube_part_prefix}.mp4"
            audio_file = f"{file_name}{youtube_part_prefix}.aac"
            output_file = f"{file_name}{youtube_suffix}.mp4"
            if (isFileExist(download_path, output_file)):
                print(
                    f"> Video(with audio) file already exists:\n    {output_file}")
                return

            if (not isFileExist(download_path, video_file, video)):
                print(
                    f"\n> Parsing stream info complete, start to save stream to video(no audio) file [size = {get_file_size(video)}]...")
                video.download(output_path=download_path, filename=video_file)
            else:
                print(f"\n> Video file downloaded: {video_file}")

            if (not isFileExist(download_path, audio_file, audio)):
                print(
                    f"> Parsing stream info complete, start to save stream to audio file[size = {get_file_size(audio)}]...")
                audio.download(output_path=download_path, filename=audio_file)
            else:
                print(f"\n> Audio file downloaded: {audio_file}\n")

            if (check_ffmpeg_exist()):
                ffmpeg_cmd = f' cd /d "{download_path}" && ffmpeg -hide_banner -v warning -stats -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{output_file}"'
                # cmd /c, 不留在cmd命令可能切换的文件夹, /k留在(执行后,工作路径可能改变)
                cmd_keep = f'cmd /c "{ffmpeg_cmd}"'
                print(f"> Start combining video and audio files with ffmpeg...")
                os.system(cmd_keep)
                print(
                    f"\n> Combined video and audio file ends, output file:\n    {output_file}")
                save_to_history(youtube_url, os.path.join(
                    download_path, output_file))
                print_ffmpeg_rotated_cmd(download_path, output_file)

                # print(
                #     f'\n> Run command to delete intermediate files[{youtube_part_prefix}*]:\n    cd /d "{download_path}" && del "{youtube_part_prefix}*" ')
                # check_integrity_of_video(r'E:\HDC\Downloads', "Yoga - Gymnastics with Lera.1080P-YouTube.mp4", lambda: clear_intermediate_files(
                #     "download_path", "video_file", "audio_file"))
                check_integrity_of_video(download_path, output_file, lambda: clear_intermediate_files(
                    download_path, video_file, audio_file))

            else:
                ffmpeg_download_url = "https://ffmpeg.org/download.html"
                print(
                    f"!  ffmpeg.exe not exist, please download ffmpeg and set to PATH, then combine video and audio files by yourself:\n    {ffmpeg_download_url}\n")
            # os.system(f'cmd /c "cd /d {os.getcwd()}"')
            # import pyperclip
            # pyperclip.copy(ffmpeg_cmd)
            # print(
            #     f'> The following command has been copied to the clipboard, please run it in the terminal with ffmpeg\n    {ffmpeg_cmd}')
        except Exception as e:
            print(f"!  {str(e)}")
            save_to_history(youtube_url, "is_need_to_download_1080P_or_more failed!")
            download_video_progressive_top_720P(
                streams, download_path, file_name_ori, youtube_url)

    else:
        download_video_progressive_top_720P(
            streams, download_path, file_name_ori, youtube_url)


def clear_intermediate_files(download_path: str, video_file: str, audio_file: str):
    # print(f"delete {video_file} and {audio_file} from {download_path}...")
    try:
        video = os.path.join(download_path, video_file)
        os.remove(video)
        print("  deleted video(no audio).")

        audio = os.path.join(download_path, audio_file)
        os.remove(audio)
        print("  deleted audio-only.")
    except:
        pass

# TODO: [建议不要] 编译个小的ffmpeg, 原本的ffmpeg 高达120MB
# N_m3u8DL-CLI_v3.0.2_with_ffmpeg_and_SimpleG编译的ffmpeg只有11MB, 但是缺少aac编码, 导致没办法合成视频
# 好处: 集成到发布包里, 能直接下载1080P及以上视频, 坏处: 编译太难
# 目前解决方案: 没检查到ffmpeg, 则关闭1080P下载, 防止用户下载到无声视频?
# 但是下载1080P默认是 False 的,在config.ini 设置为 True 之后才会下载到无声需要合成的视频


# 防止合成失败, 默认保留中间文件, 即 *-YouTube.Part.mp4/aac, 待到用户确认没问题, 自行删除.
# 文件没有下载完整, 会发生问题? 加入大小检测???
if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if ("HTTP Error 429: Too Many Requests" in str(e)):
            print(f"\n!  HTTP Error 429: Too Many Requests to Youtube: You should change your IP address via VPN.\n")
        else:
            # import sys
            # print(sys.exc_info()[0])
            import traceback
            print(f"!  {traceback.format_exc()}")
    finally:
        print("Press Enter to exit...")
        input()
