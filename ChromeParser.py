__author__ = 'marleyjaffe'

import sqlite3 as lite
import argparse
import os
import time
import glob


def ParseCommandLine():
    """
    Name:           ParseCommandLine

    Description:    Process and Validate the command line arguments
                        use Python Standard Library module argparse

    Input:          none

    Actions:
                    Uses the standard library argparse to process the command line
    """
    # Creates the argument parser object names it parser
    parser = argparse.ArgumentParser('Chrome Sync Parser',
                                     description='Pulls and Parses the relevant Chrome Sync Databases')

    # Adds arguments to the parser object
    parser.add_argument('-d', '--database', type=ValidateDatabase,
                        help="Full path to database in question")

    # Verbose CLI argument, enables error printing etc.
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Makes the program print extra information to the screen")

    return parser.parse_args()
    # End ParseCommandLine ================================================


def ValidateDatabase(filePath):
    if os.path.isfile(filePath):		 # Checks to ensure the file exists
        if os.access(filePath, os.R_OK): # Checks to ensure the program has read access
            return filePath
        else:
            raise argparse.ArgumentTypeError("Error: File is not readable")
    else:
        raise argparse.ArgumentTypeError("Error: Path is not valid")


#def OSGlob():

class SyncFile():
    def __init__(self, database):
        self.database = database

        self.connection = lite.connect(self.database)
        self.cursor = self.connection.cursor()

        self.tables = []
        self.SQLiteTables()

        self.UserInfo()

        #for user in self.userAccount:
            #print(self.ConvertTime(user[1]))

        self.cursor.execute("SELECT * FROM `metas`;")
        # Fill the metadata var with the contents of the metas table
        self.metadata = self.cursor.fetchall()

        self.AttachedComputers()
        self.RecoveryEmail()
        self.FirstName()
        self.LastName()
        self.DateOfBirth()


    def SQLiteTables(self):
        """
        Sets a list of the tables in the SQLite database should always be 5
            deleted_metas, metas, models, share_info, share_version
        """
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        self.tables = self.cursor.fetchall()
        # Removes the tuple and returns just the names in the list
        self.tables = [i[0] for i in self.tables]

    def UserInfo(self):
        self.userAccount = []
        self.cursor.execute("SELECT `name`, `db_create_time` FROM `share_info`;")
        # Returns a tuple of email account and creation time in epoch
        self.userAccount = self.cursor.fetchall()

    def ConvertTime(self, timeInEpoch):
        """
        Converts seconds since epoch into readable format (2014-02-24 21:49:54)
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeInEpoch))

    # Sets the ComputerNames list to the values from column 19 in the metadata file
    def AttachedComputers(self):
        self.computerNames = []
        for row in self.metadata:
            # b'\xd2\xb9 is the signature for a computer, remove false positives that don't have enough data
            if str(row[23])[:10] == "b'\\xd2\\xb9" and len(str(row[23])) > 23:
                # Adds a list item to the list with the computer name in [0] and date first signed in to [1]
                # Row 7 needs to be divided by 1000 because the value is stored in milliseconds since epoch
                self.computerNames.append([row[18], row[7]/1000])

    def GetUserInfo(self):
        """
        Returns list of list, each mini list has user email and when Chrome was first signed in
        """
        users = []
        for user in self.userAccount:
            tempList = []
            tempList.append(user[0])
            tempList.append(self.ConvertTime(user[1]))
            users.append(tempList)
        return users

    def GetAttachedComputers(self):
        """
        Retuns list of lists, each mini list has computer string name and date account was added to that account
        """
        computerInfo = []
        for computer in self.computerNames:
            tempList = []
            tempList.append(computer[0])
            tempList.append(self.ConvertTime(computer[1]))
            computerInfo.append(tempList)
        return computerInfo

    def RecoveryEmail(self):
        self.recoveryEmail = []
        for row in self.metadata:
            # b'\x8a\xbf\x0f5 is the signature for a recovery email
            if str(row[23])[:15] == "b'\\x8a\\xbf\\x0f5":
                self.recoveryEmail.append(str(row[18])[36:])

    def GetRecoveryEmail(self):
        return self.recoveryEmail

    def FirstName(self):
        self.firstName = ""
        for row in self.metadata:
            name = str(row[18])[15:24]
            if name == "FirstName":
                self.firstName = str(row[18][25:])

    def GetFirstName(self):
        return self.firstName

    def LastName(self):
        self.lastName = ""
        for row in self.metadata:
            name = str(row[18])[15:23]
            if name == "LastName":
                self.lastName = str(row[18][24:])

    def GetLastName(self):
        return self.lastName

    def GetFullName(self):
        return str(self.firstName+" "+self.lastName)

    def DateOfBirth(self):
        self.DOB = "~~~~~~"
        for row in self.metadata:
            name = str(row[18])[15:23]
            if name == "BirthDay":
                date = str(row[18][24:])
                if len(date) == 1:
                    date = "0"+ date
                self.DOB = date + self.DOB[2:]
            elif name == "BirthYea":
                self.DOB = self.DOB[:2] + str(row[18][25:])

    def GetFullInfo(self):
        return [[self.GetFullName(), self.DOB]]

def DisplayData(data):
    """
    Prints lists that has lists of pairs, second usually being a formatted date, or prints entire passed list
    """
    if isinstance(data, list):
        for item in data:
            if len(item) == 2:
                print(item[0].ljust(35, ":"), item[1].rjust(20, ":"))
            else:
                print(item)
    else:
        print(data)


def main():
    args = ParseCommandLine()
    syncList = []
    if args.database:
        syncList.append(SyncFile(args.database))

    for syncFile in syncList:
        print("Email Account".center(35, "="), "Time added".center(20, "="), "\n")
        DisplayData(syncFile.GetUserInfo())
        print()
        print("Full Name".center(35, "="), "DOB (DDYYYY)".center(20, "="), "\n")
        DisplayData(syncFile.GetFullInfo())
        print()
        print("Computer Name".center(35, "="), "Time added".center(20, "="), "\n")
        DisplayData(syncFile.GetAttachedComputers())
        print()
        print("Recovery Email".center(35, "="), "\n")
        DisplayData(syncFile.GetRecoveryEmail())
        print()





if __name__ == '__main__':
    main()