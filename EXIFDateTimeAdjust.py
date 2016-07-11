#!/usr/bin/python
# -*- coding: utf-8 -*-

# exiftool -CreateDate -FileCreateDate -FileModifyDate -DateTimeOriginal -FileName D:\Dropbox\DCIM\Camera\20140101_003335.jpg
# Create Date                     : 2002:12:08 12:00:00                   # total sinnlos, taucht so nirgends auf
# File Creation Date/Time         : 2014:01:10 21:22:23+01:00             # Datei Erstelldatum (durch Sync, Tagging etc meist falsch)
# File Modification Date/Time     : 2014:01:06 07:44:51+01:00             # Datei Änderungsdatum (durch Sync, Tagging etc meist falsch)
# Date/Time Original              : 2014:01:01 00:33:37                   # Das EXIF Date - wenn vorhanden dann der zuverlässigste Zeitstempel
# File Name                       : 20140101_003335.jpg                   # zur Kontrolle heranziehen!

# Class-less and UI-less for maximum performance
# no documentation for memory reasons

import os
import sys
import shutil
from datetime import timedelta, datetime

import pyexiv2
import win32file
import win32con
from colorama import Fore, Back, Style
from colorama import init as coloramainit
coloramainit()


if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
    print "parameter missing!"
    print "this script takes one path to a folder with JPGs as command line parameter"
    print ""
    print "https://github.com/ThomDietrich/EXIFDateTimeAdjust"
    sys.exit()
path = os.path.abspath(sys.argv[1].rstrip('\\'))


def getJpgFiles(path):
    files = []
    for entry in os.listdir(path):
        filepath = path + os.sep + entry
        if os.path.isfile(filepath):
            #print entry
            if os.path.splitext(filepath)[1][1:].strip().lower() == "jpg":
                files.append(filepath)
    return files


def getDatetimeExif(filepath):
    metadata = pyexiv2.ImageMetadata(filepath)
    metadata.read()
    #print metadata.exif_keys
    try:
        timestamp = metadata['Exif.Photo.DateTimeOriginal'].value
        # fix 24h bug (2015-01-01 24:01:01)
        if isinstance(timestamp, basestring):
            if timestamp[11:13] == "24":
                timestamp = timestamp[:11] + "00" + timestamp[13:]
            timestamp = datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S")
        return timestamp
    except KeyError:
        #print "Error (Exif.Photo.DateTimeOriginal) " + str(e)
        return 0



def setDatetimeExif(filepath, timestamp):
    metadata = pyexiv2.ImageMetadata(filepath)
    metadata.read()
    key = 'Exif.Photo.DateTimeOriginal'
    metadata[key] = pyexiv2.ExifTag(key, timestamp)
    metadata.write()



def getDatetimeFileCreated(filepath):
    t = os.path.getctime(filepath)
    t = datetime.fromtimestamp(t)
    t = t.replace(microsecond=0)
    return t



def setDatetimeFileCMA(filepath, timestamp):
    #we need to correct summer saving time
    #dirty workaround, does the job...
    datestamp = datetime(timestamp.year, 4, 1)   # DST starts last Sunday in March
    dstOn = datestamp - timedelta(days=datestamp.weekday() + 1)
    datestamp = datetime(timestamp.year, 11, 1) # DST ends last Sunday in October
    dstOff = datestamp - timedelta(days=datestamp.weekday() + 1)
    if dstOn <= timestamp.replace(tzinfo=None) < dstOff:
        #timestamp inside summer saving time
        #print timedelta(hours=1)
        pass
    else:
        #print timedelta(0)
        timestamp = timestamp + timedelta(hours=1)
    handle = win32file.CreateFile(filepath, win32con.GENERIC_WRITE, 0, None, win32con.OPEN_EXISTING, 0, None)
    win32file.SetFileTime(handle, timestamp, timestamp, timestamp)
    handle.close()



def getDatetimeFilename(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0].lower()
    try:
        # 2014-01-01_00.33.46(.jpg)
        t = datetime.strptime(filename[0:19], "%Y-%m-%d_%H.%M.%S")
    except ValueError:
        try:
            # IMG_20140101_003346(.jpg)
            t = datetime.strptime(filename[0:19], "IMG_%Y%m%d_%H%M%S")
        except ValueError:
            return 0
    return t



def getDatetimeFilename1970(filepath):
    filename = os.path.splitext(os.path.basename(filepath))[0].lower()
    try:
        # 1423154214(241.jpg)
        unixts = int(filename[0:13])/1000
        print unixts
        t = datetime.fromtimestamp(unixts)
    except ValueError:
        return 0
    return t


def renameFileDatetime(filepath, timestamp):
    timestampString = timestamp.strftime("%Y-%m-%d_%H.%M.%S")
    path = os.path.dirname(filepath)
    filename = os.path.splitext(os.path.basename(filepath))[0]
    ext = os.path.splitext(os.path.basename(filepath))[1][1:].strip().lower()
    destination = path + os.sep + timestampString + '.' + ext
    if filepath == destination:
        print Fore.YELLOW + 'no rename needed.' + Style.RESET_ALL
        return 0
    if not os.path.exists(destination):
        shutil.move(filepath, destination)
        return destination
    else:
        for i in range(1, 100):
            destination = path + os.sep + timestampString + "_" + str(i).zfill(2) + '.' + ext
            if not os.path.exists(destination):
                shutil.move(filepath, destination)
                print Fore.YELLOW + 'renamed to "' + destination + '"' + Style.RESET_ALL
                return destination
                break
        else:
            print Fore.RED + 'file "' + filepath + '" could not be renamed!' + Style.RESET_ALL
            return 0


for imageFile in reversed(getJpgFiles(path)):
    print Style.BRIGHT + "\n" + "-"*50 + Style.RESET_ALL
    print imageFile

    datetimeExif = getDatetimeExif(imageFile)
    datetimeFileCreated = getDatetimeFileCreated(imageFile)
    datetimeFilename = getDatetimeFilename(imageFile)
    datetimeFilename1970 = getDatetimeFilename1970(imageFile)
    print "EXIF:\t\t" + str(datetimeExif)
    print "FileCreate:\t" + str(datetimeFileCreated)
    print "Filename:\t" + str(datetimeFilename)
    print "Filename1970:\t" + str(datetimeFilename1970)

    if datetimeExif and datetimeFilename:
        print "--> elected:\t" + str(datetimeExif)
        #if datetimeExif == datetimeFilename: #...because we are not in a perfect world
        if (datetimeFilename - timedelta(seconds=300)) < datetimeExif < (datetimeFilename + timedelta(seconds=300)):
            if datetimeExif == datetimeFileCreated:
                #print "case 0: EXIF Photo.DateTimeOriginal, filename timestamp and file creation date match"
                print Fore.GREEN + "nothing to do here." + Style.RESET_ALL
                renameFileDatetime(imageFile, datetimeExif)
                #TODO differentiate between detected and correct timestamp
            else:
                print "case 1: EXIF Photo.DateTimeOriginal and filename timestamp match"
                print Fore.CYAN + "correcting file creation date and filename..." + Style.RESET_ALL
                setDatetimeFileCMA(imageFile, datetimeExif)
                renameFileDatetime(imageFile, datetimeExif)
        else:
            print "case 2: EXIF Photo.DateTimeOriginal and filename timestamp are different"
            print Fore.RED + "manual correction needed!" + Style.RESET_ALL
            print "continue?", raw_input()
    elif datetimeExif and not datetimeFilename:
        print "--> elected:\t" + str(datetimeExif)
        if datetimeExif == datetimeFileCreated:
            print "case 3: EXIF Photo.DateTimeOriginal and file creation date match"
            print Fore.CYAN + "correcting filename timestamp..." + Style.RESET_ALL
            print "continue?", raw_input()
            renameFileDatetime(imageFile, datetimeExif)
        else:
            print "case 4: EXIF Photo.DateTimeOriginal found"
            print Fore.CYAN + "correcting file creation date..." + Style.RESET_ALL
            print Fore.CYAN + "correcting filename timestamp..." + Style.RESET_ALL
            #print "continue?", raw_input()
            setDatetimeFileCMA(imageFile, datetimeExif)
            renameFileDatetime(imageFile, datetimeExif)
    elif not datetimeExif and datetimeFilename:
        print "--> elected:\t" + str(datetimeFilename)
        if datetimeFilename == datetimeFileCreated:
            print "case 5: filename timestamp and file creation date match"
            print Fore.CYAN + "correcting EXIF Photo.DateTimeOriginal..." + Style.RESET_ALL
            print "continue?", raw_input()
            setDatetimeExif(imageFile, datetimeFilename)
        else:
            print "case 6: filename timestamp found"
            print Fore.CYAN + "correcting EXIF Photo.DateTimeOriginal..." + Style.RESET_ALL
            print Fore.CYAN + "correcting file creation date..." + Style.RESET_ALL
            print "continue?", raw_input()
            setDatetimeExif(imageFile, datetimeFilename)
            setDatetimeFileCMA(imageFile, datetimeFilename)
    elif not datetimeExif and not datetimeFilename and datetimeFilename1970:
        print "--> elected:\t" + str(datetimeFilename1970)
        print "case 7"
        print Fore.RED + "only..." + Style.RESET_ALL
        print "continue?", raw_input()
        setDatetimeExif(imageFile, datetimeFilename1970)
        setDatetimeFileCMA(imageFile, datetimeFilename1970)
        renameFileDatetime(imageFile, datetimeFilename1970)
    elif not datetimeExif and not datetimeFilename and datetimeFileCreated:
        print "--> elected:\t" + str(datetimeFileCreated)
        print "case 8: file created timestamp ONLY"
        print Fore.RED + "only..." + Style.RESET_ALL
        print "continue?", raw_input()
        #setDatetimeExif(imageFile, datetimeFileCreated)
        #renameFileDatetime(imageFile, datetimeFileCreated)
    else:
        print Fore.RED + "no clue... try yourself" + Style.RESET_ALL
        print "(go set the filename, than tickle me again)"
        print "continue?", raw_input()
