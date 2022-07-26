import argparse
import subprocess
from pathlib import Path
from PIL import Image
import shutup
import tempfile

shutup.please()


def main():
    args = parse_args()
    links = args.links
    cover = args.cover
    output_dir_final = Path("output")
    output_dir_final.mkdir(exist_ok=True)
    template_img_path = Path("./template.png")

    preview = Image.new("RGB", (1280, 720), (255, 255, 255))
    with Image.open(template_img_path) as template_img:
        preview.paste(template_img, (0, 0))
    with Image.open(cover) as cover_img:
        cover_img = cover_img.resize((450, 450))
        preview.paste(cover_img, (int(1280 / 2 - 450 / 2), 60))
    preview_path = output_dir_final / (cover.stem + "_ready" + cover.suffix)
    preview.save(preview_path)
    preview.close()

    with tempfile.TemporaryDirectory() as tempdir_yt, tempfile.TemporaryDirectory() as tempdir_spleeter:
        output_dir_yt = Path(tempdir_yt)
        output_dir_spleeter = Path(tempdir_spleeter)
        for link in links:
            subprocess.run(
                [
                    "yt-dlp",
                    "--rm-cache-dir",
                    "--extract-audio",
                    "--yes-playlist",
                    str(link),
                    "-o",
                    f"{output_dir_yt}/%(title)s.%(ext)s",
                ]
            )

        from spleeter.separator import Separator

        separator = Separator("spleeter:2stems")
        for audiofile in output_dir_yt.iterdir():
            separator.separate_to_file(
                str(audiofile),
                str(output_dir_spleeter),
                filename_format="{filename}_{instrument}.{codec}",
            )
            # remove original files
            audiofile.unlink()

        # leave instrumentals only
        for audiofile in output_dir_spleeter.iterdir():
            if audiofile.stem.endswith("_vocals"):
                audiofile.unlink()
            if audiofile.stem.endswith("_accompaniment"):
                audiofile.rename(
                    audiofile.parent
                    / audiofile.name.replace("_accompaniment", "")
                )

        for audiofile in output_dir_spleeter.iterdir():
            subprocess.run(
                [
                    "ffmpeg",
                    "-loop",
                    "1",
                    "-y",
                    "-i",
                    preview_path,
                    "-i",
                    audiofile,
                    "-shortest",
                    output_dir_final / f"{audiofile.stem}.mp4",
                ]
            )
            audiofile.unlink()
        preview_path.unlink()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract instrumental and make video"
    )
    parser.add_argument(
        "links",
        type=str,
        nargs="+",
        help="Link to playlists/videos to extract audio from",
    )
    parser.add_argument("cover", type=Path, help="Path to a cover image")
    return parser.parse_args()


if __name__ == "__main__":
    main()
