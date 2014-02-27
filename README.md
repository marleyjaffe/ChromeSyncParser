ChromeSyncParser
================
This program will help forensic examiners analyze the contents of the SyncData.sqlite3.
This database is created when an account is synced with the Google Chrome Browser.


Warning
---------------

SQLite is not a forensic format. While the intention of this program is not to change or modify any data,
please take the appropriate steps when analyzing evidence.

Most of the evidence will not be found if the personal sync passphrase was enabled over the Google Credentials.

DataLocation
---------------

SyncData.sqlite3 files can be located at in the following locations:

Win Vista or Later:
    C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data\Default\databases

Windows XP:
    C:\Documents and Settings\%USERNAME%\Application Support\Google\Chrome\Default\databases

Mac OS X:
    ~/Library/Application Support/Google/Chrome/Default/Sync Data/

Linux:
    ~/.config/google-chrome/Default/databases

Note:
    If Chrome browser is open, the sync database may be open and can cause the program to error
