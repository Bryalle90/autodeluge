# README

* version: 2.0
* date: Jan 10, 2016

## Program Requirements
### Required
* [Python 2.7.9](https://www.python.org/downloads/)
	* This script is written and tested in Python 2.7.9 and Windows 7/8/10
* [deluge-client](https://pypi.python.org/pypi/deluge-client/1.0.2)
* [requests library](https://pypi.python.org/pypi/requests/2.9.1)
* [deluge 1.3.12](http://dev.deluge-torrent.org/wiki/Download)
* [FileBot](http://www.filebot.net/#download)
* [Java Runtime Environment](https://java.com/en/download/manual.jsp)
### Optional
* [Pushbullet](https://www.pushbullet.com/)
	* pushbullet is a free application that allows you to send notifications, lists, files, etc. 
	across multiple devices including iOS, android, windows(desktop), chrome, firefox
*[Auto Remove Plus](http://forum.deluge-torrent.org/viewtopic.php?f=9&t=47243)
	* deluge plugin used to automatically stop and remove torrents once goals have been met

## How do I get set up?

### Set up Deluge
#### How to set up Deluge for the script
* Go to `preferences>interface`
	* Disable `Classic Mode`
* Go to `%appdata%\deluge\`
	* Open auth with a text editor
	* Create a new login or use localclient
#### Plugins
* AutoRemovePlus (optional)
	* Make sure to allow enough time for the script to work before removing a torrent
* Execute
	* Event>Torrent Complete>Command
		* Enter full path of autoDeluge2.exe
	* Event>Torrent Removed>Command
		* Enter full path of cleanup.exe
* Label
	* For each label created, make sure there is a label file in the labels folder

### Set up autoDeluge
* edit included config.cfg file

General
------------: | :------------
path          | Location for files to be extracted/copied to before processing by FileBot
overwrite     | (True/False) overwrite files that are already present in final directory

Client
------------: | :------------
host          | Typically 127.0.0.1
port          | `Preferences>Daemon>Daemon port`
username      | Found in %appdata%\deluge\auth
password      | Found in %appdata%\deluge\auth

FileBot
------------: | :------------
path          | Path of FileBot root folder

Notifications
------------: | :------------
pushbullet    | (True/False) Use PushBullet for notifications
email         | (True/False) Use email notifications

Display
------------: | :------------
filesize      | Display filesize as GB, MB, KB, B
speed         | Display avg speed as GB, MB, KB, Gb, Mb, Kb

Email
------------: | :------------
enable        | (True/False) Use email notifications
SMTPServer    | Email server (gmail is default)
SMTPPort      | Email port (gmail is default)
username      | Your email username (example@gmail.com)
password      | Your email password
emailTo       | What addresses to email notification to, separated by | (pipe character)

PushBullet
------------: | :------------
enable        | (True/False) Use PushBullet for notifications
token         | Your [access token](https://www.pushbullet.com/account) from Pushbullet
devices       | Can either be a list of specific device names, separated by | (pipe character), or leave blank for all devices

Extensions
------------: | :------------
video         | You can either leave it as-is or modify the list, separating each extension by | (pipe character)
subtitle      | You can either leave it as-is or modify the list, separating each extension by | (pipe character)
readme        | You can either leave it as-is or modify the list, separating each extension by | (pipe character)
archive       | You can either leave it as-is or modify the list, separating each extension by | (pipe character)
ignore        | Any file with any of the words in this list will be ignored, even with a desired extension, separated by  | (pipe character)

* set up labels in the labels folder (the script will ignore any torrent without a label and accompanying config file)

Type
------------: | :------------
video         | (True/False) For this label, do you want to keep files of this type?
subtitle      | (True/False) For this label, do you want to keep files of this type?
readme        | (True/False) For this label, do you want to keep files of this type?

Filebot
------------: | :------------
database      | TV: `TVRage, AniDB, TheTVDB` Movies: `OpenSubtitles, IMDb, TheMovieDB`
query         | Force a specific search string, leave blank to derive from file name
format        | How you want your file names to be [formatted](http://www.filebot.net/naming.html)
language      | The [2-letter language code](http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) for episode/movie titles 
path          | The final path for your file(s)