EXIFDateTimeAdjust
==================

With JPG-files (as with many other files) there are multiple places where a date information is stored:
  - the EXIF metadata "Date/Time Original"
  - the filename (e.g. "IMG_20141231_123559.jpg")
  - the file creation date

The goal is to find the actual capturing date of a photo and to set all other timestamps acordingly.
Different Software and Smartphone Apps use information provided by files in different ways. Ordering is done by name, creation date or metadata info.
While transfering, synchronizing, tagging and processing/editing picture files, the mentioned timestamps are often changed, updated or deleted. 

EXIFDateTimeAdjust is a python script that analyzes all JPG-files in one folder (provided as parameter) and corrects timestamps if necessary.

The script was tested under Windows 7 (x64)

Requirements:
  - [Python2.7](http://python.org/)
  - [pyexiv2](http://tilloy.net/dev/pyexiv2/)
  - [pywin32](http://sourceforge.net/projects/pywin32/files/pywin32/)
  - [colorama](https://pypi.python.org/pypi/colorama)
  
