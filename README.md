# make-instrumental-video

![img](docs/diagram.png)

Given a list of links to some YouTube videos and a cover image, the script does the following things:
1. Generates an image for making static video using `template.png` and given cover image 

for every video (in every playlist) it does this:

2. Downloads the video and extracts audio from it using [yt-dlp](https://github.com/yt-dlp/yt-dlp)
3. Runs [spleeter](https://github.com/deezer/spleeter) on this audio, getting an instrumental wav
4. Runs [ffmpeg](https://github.com/FFmpeg/FFmpeg) to create static video from the instrumental wav (see 3) and the image (see 1)

### Prerequisites

1. python3.9
2. python3.9-venv
3. python3.9-dev (possibly)
4. ffmpeg

### Usage

```bash
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt 
python3 main.py <links> <path_to_cover_image>
```