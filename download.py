#!/usr/bin/python
import os
from datetime import date
from queue import Queue

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

#########################################################################
# Made for Python 3.5 and Google Drive API v3.
# Usage: to replicate a Gogle Drive folder structure with all files, in your computer
# python dl_gdrive_folder.py <Google drive folder source> <local computer folder destination>
# Example:
# Folder Structure at Google Drive:
# F1
#	File0
#	F11
#		File1
#	F12
#		F211
#			FileA
#			FileB
# To download everything from folder F211 to a local folder TST
# python dl_gdrive_folder.py F211 TST
# It doesn´t work if you have more than one folder with the same name
#########################################################################
# Updated by Willena (https://github.com/Willena/)
#
# Build from the works of :
# Atila Xavier - https://github.com/atilaxavier/Google-Drive-Download
# and
# Mark Culhane - google_drive_backup.py
# https://github.com/markz0r/tools/blob/master/backup_scripts/google_drive_backup.py
# and
# HatsuneMiku - recursive navigation over folders
# http://stackoverflow.com/questions/22092402/python-google-drive-api-list-the-entire-drive-file-tree
# https://github.com/HatsuneMiku/googleDriveAccess
#
# Know Issues:
#		- wasn´t downloading files if verbose was not used - fixed on 19/01/2017
#		- don´t work with Google "Forms" - fixed (simply skip those files)
#		- downloads trashed files - fixed (don´t even consider them)
#########################################################################

#########################################################################
# Pre-requisites - Authorize API usage on google drive, and download/install google drive pyhton api.
# Follow instructions on : https://developers.google.com/drive/v3/web/quickstart/python
# To install python client on windows:
# pip install --upgrade google-api-python-client
# Authorize API https://developers.google.com/drive/v3/web/quickstart/python#step_1_turn_on_the_api_name
# Download the client_secret.json to same dir as this script
#########################################################################
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
APPLICATION_NAME = 'Drive File API - Python'
FOLDER_TYPE = 'application/vnd.google-apps.folder'
to_dir = str(date.today()) + "_drive_backup"
global num_files
global num_skiped

toRetry = []

try:
    import argparse

    parser = argparse.ArgumentParser(description="Google Drive folder and files download")
    parser.add_argument("-f", "--from", dest='dirs_from', nargs='+',
                        help="Google Drive folder tree starting folder to be downloaded or fileId starting with a '+' ")
    parser.add_argument("-d", '--dest', dest='dir_to', type=str, help="Initial local folder to receive tree and files")
    parser.add_argument("-l", "--lista",
                        help="Just list folder and files to be downloaded. Don´t actually donwnload anything",
                        action="store_true")
    parser.add_argument("-v", "--verbose", help="Writes what it´s doing.", action="store_true")
    args = parser.parse_args()
    from_dirs = args.dirs_from
    to_dir = args.dir_to
except ImportError:
    print("argparse Error!")
    args = None


def prepDest(folder, spaces):
    if not os.path.exists(folder):
        if args.lista:
            print("{} Will create folder: {}".format(spaces, folder))
        else:
            if args.verbose:
                print("{} Creating folder: {}".format(spaces, folder))
            os.makedirs(folder)
            return True
    else:
        # print("{} Folder {} already exists".format(spaces, folder))
        return True
    return False


def downloadFile(service, spaces, file_name, file_id, mimeType, dest_folder):
    # Function that performs the download of each file to the specified local folder
    global num_skiped
    valid = True
    if (args.lista):
        print("{} downloading file: {}, to folder {} \n".format(spaces, file_name, dest_folder))
    else:
        if args.verbose:
            print("{} downloading file: {}, to folder {} \n".format(spaces, file_name, dest_folder))
        request = service.files().get_media(fileId=file_id)
        if "application/vnd.google-apps" in mimeType:
            if args.verbose:
                print("Google apps media types will be exported accordingly")
            if "form" in mimeType:
                print("Google app Form: {} - cannot be downloaded. Skiping...".format(file_name))
                valid = False
                num_skiped += 1
            elif "document" in mimeType:
                request = service.files().export_media(fileId=file_id,
                                                       mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                file_name = file_name + ".docx"
            elif "spreadsheet" in mimeType:
                request = service.files().export_media(fileId=file_id,
                                                       mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                file_name = file_name + ".xlsx"
            elif "presentation" in mimeType:
                request = service.files().export_media(fileId=file_id,
                                                       mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
                file_name = file_name + ".pptx"
            else:
                request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
                file_name = file_name + ".pdf"
        if valid:
            print("{}Downloading -- {}".format(spaces, file_name))
            filepath = os.path.join(dest_folder, file_name)

            # Make sure the path exist before writing
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as wer:
                done = False
                downloader = MediaIoBaseDownload(wer, request)
                if args.verbose:
                    print("Writing file {} to folder {}.\n".format(file_name, dest_folder))

                while done is False:
                    status, done = downloader.next_chunk()
                    if status is not None and (status.total_size is not None and status.resumable_progress is not None):
                        print("\rDownload %s (%s/%s): %d%%." % (file_name, sizeof_fmt(status.total_size), sizeof_fmt(status.resumable_progress), int(status.progress() * 100)), end='')
                print("Download OK")
                global num_files
                num_files += 1


def getFolderId(service, folderName: str):
    query = "name contains '%s' and mimeType = '%s'" % (folderName, FOLDER_TYPE)

    fid = None

    if folderName.startswith('+'):
        return (folderName[1:])

    if args.verbose:
        print("Checking source folder existence: {}".format(folderName))

    result = service.files().list(q=query,
                                  pageSize=10, pageToken='',
                                  fields="nextPageToken,files(parents,id,name,mimeType)").execute()
    if args.verbose:
        print("Result: {}".format(result))
    if len(result['files']) == 0:
        print("Folder NOT found")
    else:
        folder = result.get('files')[0]
        fid = folder['id']
        if args.verbose:
            print("Found {} folders with this name".format(len(result.get('files'))))
            print("Found folder! Id: {}".format(fid))
            print("Name: {}".format(folder['name']))
            for p in folder['parents']:
                print("Parent : {}".format(p))
    return (fid)


def getlist(ds, q, **kwargs):
    result = None
    npt = ''
    while not npt is None:
        if npt != '': kwargs['pageToken'] = npt
        entries = ds.files().list(q=q, **kwargs).execute()
        if result is None:
            result = entries
        else:
            result['files'] += entries['files']
        npt = entries.get('nextPageToken')
    return result


def getFolderFiles(service, folderId, folderName, dest_folder, depth):
    global toRetry
    # recursive function that walks down the folder tree creating the local folders and downloading the files
    spaces = ' ' * depth
    d_folder = dest_folder + os.path.sep + folderName
    prepDest(d_folder, spaces)
    if (args.lista or args.verbose):
        #		print('%s+%s\n%s	 %s\n' % (spaces, folderId, spaces, folderName))
        print("{}+{}\n{}     {}\n".format(spaces, folderId, spaces, folderName))
    else:
        print("Source Folder: {}\n".format(folderName))

    # searching only for folders
    query = "'%s' in parents and mimeType='%s' and trashed = false" % (folderId, FOLDER_TYPE)
    entries = getlist(service, query, **{'pageSize': 1000})
    for folder in entries['files']:
        getFolderFiles(service, folder['id'], folder['name'], d_folder, depth + 1)

    # searching only for files (notice que query is mimTye != FOLDER_TYPE
    query = "'%s' in parents and mimeType!='%s' and trashed = false" % (folderId, FOLDER_TYPE)
    entries = getlist(service, query, **{'pageSize': 1000})
    for f in entries['files']:
        if (args.lista or args.verbose):
            #			print('%s -ID: %s NAME: %s TYPE: %s' % (spaces, f['id'], f['name'], f['mimeType']))
            print("{} -ID: {} NAME: {} TYPE: {}".format(spaces, f['id'], f['name'], f['mimeType']))
        try:
            downloadFile(service, spaces, f['name'], f['id'], f['mimeType'], d_folder)
        except HttpError as e:
            toRetry.append((f['name'], f['id'], f['mimeType'], d_folder))
            print(
                "{} -ID: {} NAME: {} TYPE: {} -- FAILED ({}) -- Stored for later try".format(spaces, f['id'], f['name'],
                                                                                             f['mimeType'], e))

    print("{} files downloaded so far\n".format(num_files))


def main(basedir):
    global from_dirs
    global num_files
    num_files = 0
    global num_skiped
    num_skiped = 0

    print("Connecting with Google Drive")

    try:
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=1337)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        service = build('drive', 'v3', credentials=creds)

    except Exception as e:
        print("Error connecting to Google Drive")
        print(e)
    else:

        print("Connected. Now let´s read the files")
        print("Starting download of {}".format(from_dirs))
        for from_dir in from_dirs:
            print("Downloading folder and files from: {} -> to: {}".format(from_dir, to_dir))

            if args.lista:
                print("just listing folder and files from source")
                prepDest(to_dir, "")

                folderId = getFolderId(service, from_dir)

                if isId(from_dir):
                    from_dir = getNameFromId(service, from_dir[1:])

                if not folderId is None:
                    getFolderFiles(service, folderId, from_dir, to_dir, 0)

                else:
                    print("Aborting. Source folder {} not found".format(from_dir))

            elif prepDest(to_dir, ""):
                print("Downloading files")
                folderId = getFolderId(service, from_dir)
                if isId(from_dir):
                    from_dir = getNameFromId(service, from_dir[1:])
                if not folderId is None:
                    getFolderFiles(service, folderId, from_dir, to_dir, 0)
                    print("{} total files downloaded.\n".format(num_files))
                    if num_skiped > 0:
                        print("{} total skiped files, not downloaded.".format(num_skiped))

                    print("Retrying - Files marked as Errored")
                    for item in toRetry:
                        print("{} -ID: {} NAME: {} TYPE: {} PATH: {}".format("", item[0], item[1], item[2], item[3]))
                        try:
                            downloadFile(service, "", item[0], item[1], item[2], item[3])
                        except Exception:
                            print(
                                "STILL FAILLING ! {} -ID: {} NAME: {} TYPE: {} PATH: {} -- Not Retrying -- Skiped".format(
                                    "", item[0], item[1], item[2], item[3]))

                else:
                    print("Aborting. Source folder {} not found".format(from_dir))
            else:
                print("Destination folder : {} - already exists".format(to_dir))


def getNameFromId(service, fileId):
    return service.files().get(fileId=fileId).execute()['name']


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def isId(id: str):
    return id.startswith('+')


if __name__ == '__main__':
    main(os.path.dirname(__file__))
