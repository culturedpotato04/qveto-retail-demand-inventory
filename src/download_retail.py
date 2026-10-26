"""Fetch the public UCI retail workbook while preserving existing raw files."""
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
URL='https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip'


def main():
    raw=ROOT/'data/raw/retail'
    raw.mkdir(parents=True,exist_ok=True)
    archive=raw/'online-retail.zip'
    if not archive.exists():
        with urlopen(URL,timeout=90) as response,archive.open('xb') as output:
            while chunk:=response.read(1024*1024): output.write(chunk)
    target=raw/'original/Online Retail.xlsx'
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        with ZipFile(archive) as z,target.open('xb') as output:
            output.write(z.read('Online Retail.xlsx'))
    print('Original retail workbook ready:',target)


if __name__=='__main__': main()
