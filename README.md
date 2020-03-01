# Google Drive - Folder downloader

A tools that uses Google Drive APIs V3 to download folders.

## Requirements

- python3
- A credentials.json file with access to the google drive API
- pip

## Install 

1. clone the repository
2. install dependencies `pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

## Usage

On the first launch you will have to authorize the application via a webbrowser. The python libraries will take care of that.

```
usage: download.py [-h] [-f DIRS_FROM [DIRS_FROM ...]] [-d DIR_TO] [-l] [-v]

Google Drive folder and files download

optional arguments:
  -h, --help            show this help message and exit
  -f DIRS_FROM [DIRS_FROM ...], --from DIRS_FROM [DIRS_FROM ...]
                        Google Drive folder tree starting folder to be
                        downloaded or fileId starting with a '+'
  -d DIR_TO, --dest DIR_TO
                        Initial local folder to receive tree and files
  -l, --lista           Just list folder and files to be downloaded. Don´t
                        actually donwnload anything
  -v, --verbose         Writes what it´s doing.
```