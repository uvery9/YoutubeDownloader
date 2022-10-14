## Download youtube video files using pytube
usage: 
  1. configure youtube_url AND download_path in config.ini (if not exist, run YoutubeDownloader.exe to generate), 
  2. Run YoutubeDownloader.exe
  * default highest resolution = 720P, which include video + voice 



The reasons are as follows: https://pytube.io/en/latest/user/streams.html
In the context of pytube, the implications are for the highest quality streams; you now need to 
download both the audio and video tracks and then post-process them with software like FFmpeg to merge them.

The legacy streams that contain the audio and video in a single file (referred to as “progressive download”) are still available, 
but only for resolutions 720P and below.