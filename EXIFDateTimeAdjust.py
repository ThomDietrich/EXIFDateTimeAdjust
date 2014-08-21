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
import getopt
import re
import pyexiv2
import datetime

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
		#print tag.value
		return tag.value 
	except KeyError as e:
		#print "Error (Exif.Photo.DateTimeOriginal) " + str(e)
		return 0
	#try:
	#	tag = metadata['Exif.Image.DateTime']
	#	print tag.value
	#except KeyError as e:
	#	print "Error (Exif.Image.DateTime) " + str(e)
	#print type(tag.value)	
	#print tag.raw_value
	#print tag.value
	#print tag.value.strftime('%A %d %B %Y, %H:%M:%S')

def getDatetimeFile(filepath):
	t = os.path.getctime(filepath)
	t = datetime.datetime.fromtimestamp(t)
	t = t.replace(microsecond = 0)
	return t
	
def getDatetimeFilename(filepath):
	filename = os.path.splitext(os.path.basename(filepath))[0].lower()
	try:
		# 2014-01-01_00.33.46(.jpg)
		t = datetime.datetime.strptime(filename, "%Y-%m-%d_%H.%M.%S")
	except ValueError:
		try:
			# IMG_20140101_003346(.jpg)
			t = datetime.datetime.strptime(filename, "IMG_%Y%m%d_%H%M%S")
		except ValueError:
			return 0
	return t

path = sys.argv[1]
if not os.path.exists(path):
	path = 'D:\\Test' #ersetzen
path = os.path.abspath(path.rstrip('\\'))

print path
for file in getJpgFiles(path):
	print "\n" + "="*50
	print file
	
	datetimeExif = getDatetimeExif(file)
	datetimeFile = getDatetimeFile(file)
	datetimeFilename = getDatetimeFilename(file)
	print "EXIF:\t\t" + str(datetimeExif)
	print "FileCreate:\t" + str(datetimeFile)
	print "Filename:\t" + str(datetimeFilename)
	print ""
	
	if (datetimeExif and datetimeFilename):
		if (datetimeExif == datetimeFilename):
			if (datetimeExif == datetimeFile):
				print "case 0: EXIF Photo.DateTimeOriginal, filename timestamp and file creation date match"
				print "nothing to do here."
			else: 
				print "case 1: EXIF Photo.DateTimeOriginal and filename timestamp match"
				print "correcting file creation date..."
		else:
			print "case 2: EXIF Photo.DateTimeOriginal and filename timestamp are different"
			print "manual correction needed!"
	
	elif (datetimeExif and not datetimeFilename):
		if (datetimeExif == datetimeFile):
			print "case 3: EXIF Photo.DateTimeOriginal and file creation date match"
			print "correcting filename timestamp..."
		else:
			print "case 4: EXIF Photo.DateTimeOriginal found"
			print "correcting filename timestamp..."
			print "correcting file creation date..."
	elif (not datetimeExif and datetimeFilename):
		if (datetimeFilename == datetimeFile):
			print "case 5: filename timestamp and file creation date match"
			print "correction EXIF Photo.DateTimeOriginal..."
		else:
			print "case 6: filename timestamp found"
			print "correction EXIF Photo.DateTimeOriginal..."
			print "correcting file creation date..."
	else:
		print "no clue... try yourself"