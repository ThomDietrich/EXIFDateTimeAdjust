#!/usr/bin/python
# -*- coding: utf-8 -*-

# exiftool -CreateDate -FileCreateDate -FileModifyDate -DateTimeOriginal -FileName D:\Dropbox\DCIM\Camera\20140101_003335.jpg
# Create Date                     : 2002:12:08 12:00:00                   # total sinnlos, taucht so nirgends auf
# File Creation Date/Time         : 2014:01:10 21:22:23+01:00             # Datei Erstelldatum (durch Sync, Tagging etc meist falsch)
# File Modification Date/Time     : 2014:01:06 07:44:51+01:00             # Datei Änderungsdatum (durch Sync, Tagging etc meist falsch)
# Date/Time Original              : 2014:01:01 00:33:37                   # Das EXIF Date - wenn vorhanden dann der zuverlässigste Zeitstempel
# File Name                       : 20140101_003335.jpg                   # zur Kontrolle heranziehen!

import os
import sys
import shutil
import pyexiv2
import datetime
import win32file
import win32con
from datetime import timedelta, datetime, tzinfo
from colorama import Fore, Back, Style
from colorama import init as coloramainit
coloramainit()

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
		tag = metadata['Exif.Photo.DateTimeOriginal']
		return tag.value 
	except KeyError as e:
		#print "Error (Exif.Photo.DateTimeOriginal) " + str(e)
		return 0


def getDatetimeFileCreated(filepath):
	t = os.path.getctime(filepath)
	t = datetime.fromtimestamp(t)
	t = t.replace(microsecond = 0)
	return t

	
def setDatetimeFileCMA(filepath, timestamp):
	#we need to correct summer saving time
	d = datetime(timestamp.year, 4, 1)   # DST starts last Sunday in March
	dstOn = d - timedelta(days=d.weekday() + 1) 
	d = datetime(timestamp.year, 11, 1) # DST ends last Sunday in October
	dstOff = d - timedelta(days=d.weekday() + 1)
	if (dstOn <=  timestamp.replace(tzinfo=None) < dstOff):
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
		t = datetime.strptime(filename, "%Y-%m-%d_%H.%M.%S")
	except ValueError:
		try:
			# IMG_20140101_003346(.jpg)
			t = datetime.strptime(filename, "IMG_%Y%m%d_%H%M%S")
		except ValueError:
			return 0
	return t


def renameFileDatetime(filepath, timestamp):
	timestampString = timestamp.strftime("%Y-%m-%d_%H.%M.%S")
	path = os.path.dirname(filepath)
	filename = os.path.splitext(os.path.basename(filepath))[0]
	ext = os.path.splitext(os.path.basename(filepath))[1][1:].strip().lower()
	destination = path + os.sep + timestampString + '.' + ext
	if not os.path.exists(destination):
		shutil.move(filepath, path + os.sep + timestampString + '.' + ext)
		return destination
	else:
		print Fore.RED + 'file "' + destination + '" already exists!' + Style.RESET_ALL
		return 0
		
	
if (len(sys.argv) != 2 or not os.path.exists(sys.argv[1])):
	print "parameter missing!"
	print "this script takes one path to a folder with JPGs as command line parameter"
	print ""
	print "https://github.com/ThomDietrich/EXIFDateTimeAdjust"
	sys.exit()
path = os.path.abspath(sys.argv[1].rstrip('\\'))


for file in getJpgFiles(path):
	print Style.BRIGHT + "\n" + "-"*50 + Style.RESET_ALL
	print file
	
	datetimeExif = getDatetimeExif(file)
	datetimeFileCreated = getDatetimeFileCreated(file)
	datetimeFilename = getDatetimeFilename(file)
	print "EXIF:\t\t" + str(datetimeExif)
	print "FileCreate:\t" + str(datetimeFileCreated)
	print "Filename:\t" + str(datetimeFilename)
	
	print "continue?",
	raw_input()
	
	if (datetimeExif and datetimeFilename):
		print "--> elected:\t" + str(datetimeExif)
		#if (datetimeExif == datetimeFilename): #...because we are not in a perfect world
		if ((datetimeFilename - timedelta(seconds=2)) < datetimeExif < (datetimeFilename + timedelta(seconds=2))):
			if (datetimeExif == datetimeFileCreated):
				#print "case 0: EXIF Photo.DateTimeOriginal, filename timestamp and file creation date match"
				print Fore.GREEN + "nothing to do here." + Style.RESET_ALL
			else: 
				print "case 1: EXIF Photo.DateTimeOriginal and filename timestamp match"
				print "correcting file creation date..."
				setDatetimeFileCMA(file, datetimeExif)
		else:
			print "case 2: EXIF Photo.DateTimeOriginal and filename timestamp are different"
			print Fore.RED + "manual correction needed!" + Style.RESET_ALL
	
	elif (datetimeExif and not datetimeFilename):
		print "--> elected:\t" + str(datetimeExif)
		if (datetimeExif == datetimeFileCreated):
			print "case 3: EXIF Photo.DateTimeOriginal and file creation date match"
			print "correcting filename timestamp..."
			renameFileDatetime(file, datetimeExif)
		else:
			print "case 4: EXIF Photo.DateTimeOriginal found"
			print "correcting file creation date..."
			setDatetimeFileCMA(file, datetimeExif)
			print "correcting filename timestamp..."
			renameFileDatetime(file, datetimeExif)
	elif (not datetimeExif and datetimeFilename):
		print "--> elected:\t" + str(datetimeFilename)
		if (datetimeFilename == datetimeFileCreated):
			print "case 5: filename timestamp and file creation date match"
			print "correction EXIF Photo.DateTimeOriginal..."
			print Fore.YELLOW + "--TODO--" + Style.RESET_ALL
		else:
			print "case 6: filename timestamp found"
			print "correction EXIF Photo.DateTimeOriginal..."
			print "correcting file creation date..."
			#setDatetimeFileCMA(file, datetimeExif)
			print Fore.YELLOW + "--TODO--" + Style.RESET_ALL
	
	else:
		print Fore.RED + "no clue... try yourself" + Style.RESET_ALL
		print "(go set the filename, than tickle me again)"




