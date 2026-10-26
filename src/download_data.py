"""Download the official UCI archive once; refuse to overwrite existing raw data."""
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip'


def main():
    raw = ROOT / 'data' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / 'bike-sharing-uci.zip'
    if not archive.exists():
        payload = urlopen(URL, timeout=60).read()
        with archive.open('xb') as stream:
            stream.write(payload)
    with ZipFile(archive) as zip_file:
        target = raw / 'uci-bike-sharing'
        target.mkdir(exist_ok=True)
        for name in ['day.csv', 'hour.csv', 'Readme.txt']:
            destination = target / name
            if not destination.exists():
                with destination.open('xb') as stream:
                    stream.write(zip_file.read(name))
    print('Official raw files preserved:', raw)


if __name__ == '__main__':
    main()
