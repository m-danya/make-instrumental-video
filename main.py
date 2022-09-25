import argparse
import shutil
import subprocess
from itertools import chain
from pathlib import Path
from PIL import Image
import shutup
import tempfile
import os
from tqdm import tqdm

shutup.please()


def main():
    args = parse_args()
    links = args.links
    cover = args.cover
    mp3s_path = args.mp3_dir

    save_as_mp3 = not cover

    if save_as_mp3:
        print("[WARNING] Cover not provided, so we're going to make mp3s.")

    output_dir_final = Path("output")
    output_dir_final.mkdir(exist_ok=True)
    template_img_path = Path("./template.png")

    with tempfile.TemporaryDirectory() as tempdir_yt, tempfile.TemporaryDirectory() as tempdir_demucs:
        output_dir_yt = Path(tempdir_yt)
        output_dir_demucs = Path(tempdir_demucs)

        # 1. Download yt videos and extract audios from them
        download_audios_from_youtube(links, output_dir_yt)

        if args.let_me_filter_downloaded_videos:
            print(
                f"Downloading is finished, check the {output_dir_yt.resolve()}"
            )
            input("WAITING FOR FILTERING (press enter)")

        # 2. Run demucs and leave instrumental only
        demucsify_and_clean(
            output_dir_yt,
            mp3s_path,
            output_dir_demucs,
            extract_instrumental=not args.vocals,
        )

        # 3. Make mp3s or mp4s
        if save_as_mp3:
            just_move_mp3s(output_dir_final, output_dir_demucs)
        else:
            # 3.1 Make the image for video from cover
            preview_path = make_cover_image(
                cover, output_dir_final, template_img_path
            )

            # 3.2. Make a video
            make_mp4s(output_dir_final, output_dir_demucs, preview_path)


def download_audios_from_youtube(links, output_dir_yt):
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


def demucsify_and_clean(
    output_dir_yt, mp3s_path, output_dir_demucs, extract_instrumental
):
    for audiofile in tqdm(
        list(
            chain(
                output_dir_yt.iterdir(),
                mp3s_path.iterdir() if mp3s_path else [],
            )
        ),
        desc="running demucs",
    ):
        subprocess.run(
            [
                "demucs",
                "--mp3",
                "--two-stems=vocals",
                str(audiofile),
                "-o",
                str(output_dir_demucs),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # leave instrumentals only (or vocals only) and move them
    # to the root directory

    to_remove = "vocals.mp3" if extract_instrumental else "no_vocals.mp3"

    for audiofile in output_dir_demucs.rglob("*.mp3"):
        if audiofile.name == to_remove:
            audiofile.unlink()
        else:
            audiofile.rename(
                output_dir_demucs / (audiofile.parent.name + ".mp3")
            )

    for file_or_dir in output_dir_demucs.iterdir():
        if file_or_dir.is_dir():
            shutil.rmtree(file_or_dir)


def just_move_mp3s(output_dir_final, output_dir_demucs):
    for audiofile in output_dir_demucs.iterdir():
        if audiofile.is_file():
            audiofile.rename(output_dir_final / audiofile.name)


def make_cover_image(cover, cover_output_dir, template_img_path):
    preview = Image.new("RGB", (1280, 720), (255, 255, 255))
    with Image.open(template_img_path) as template_img:
        preview.paste(template_img, (0, 0))
    with Image.open(cover) as cover_img:
        cover_img = cover_img.resize((450, 450))
        preview.paste(cover_img, (int(1280 / 2 - 450 / 2), 60))
    preview_path = cover_output_dir / (cover.stem + "_ready" + cover.suffix)
    preview.save(preview_path)
    preview.close()
    return preview_path


def make_mp4s(output_dir_final, output_dir_demucs, preview_path):
    for audiofile in tqdm(
        list(output_dir_demucs.iterdir()), desc="making mp4s"
    ):
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
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
        # remove the wav
        audiofile.unlink()
    preview_path.unlink()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract instrumental and make video"
    )
    parser.add_argument(
        "links",
        type=str,
        nargs="*",
        help=(
            "links to playlists/videos to extract audio from (the first type"
            " of songs source)"
        ),
    )
    parser.add_argument(
        "--mp3-dir",
        type=Path,
        nargs="?",
        help="directory with mp3s (the second type of songs source)",
        required=False,
    )

    parser.add_argument(
        "--cover",
        type=Path,
        help=(
            "path to a cover image. If not provided, the output is mp3s"
            " instead of mp4s"
        ),
    )
    parser.add_argument(
        "--let-me-filter-downloaded-videos",
        action="store_true",
        help=(
            "pause after downloading videos to allow deleting unwanted videos"
            " (useful for playlists containing a video with a full album)"
        ),
    )
    parser.add_argument(
        "--vocals",
        action="store_true",
        help="extract vocals instead of an instrumental",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
    os.system("cat desc.txt")
