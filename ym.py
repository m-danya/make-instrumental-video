import argparse
import urllib.request
from pathlib import Path
import uuid
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def main():
    args = parse_args()

    cmds = []

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    for link in args.link:
        driver.get(link)
        imgs = driver.find_elements(By.CLASS_NAME, "yt-img-shadow")
        img = [
            x for x in imgs if "googleusercontent" in x.get_attribute("src")
        ][0]
        # download the image
        img_path = (
            Path.home() / "Pictures" / "yt-channel" / f"{uuid.uuid4().hex}.jpg"
        )
        urllib.request.urlretrieve(img.get_attribute("src"), img_path)
        cmds.append(f"python main.py {link} --cover {img_path}")
    driver.quit()
    os.system(" && ".join(cmds))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("link", type=str, nargs="+")
    return parser.parse_args()


if __name__ == "__main__":
    main()
