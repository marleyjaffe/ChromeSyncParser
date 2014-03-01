__author__ = 'marleyjaffe'

import sqlite3 as lite
import argparse
import os
import time
import glob
import platform

verbosity = 3
outFile = False

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

    parser.add_argument('-p', '--path', default = False,
                        help="Starting Path to where the database should recursively look for databases")

    # Verbose CLI argument, enables error printing etc.
    parser.add_argument('-v', '--verbose', type=int, default=3,
                        help="Makes the program print extra information to the screen")

    parser.add_argument('-f', '--outFile', default=False, help="allows the output to be stored to a file")

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


def GetDatabases(startingPath):
    databaseList = []

    # TODO Allow the examination of a windows export on mac system and vice versa. Done by passing platform as var
    try:
        if platform.system() == "Windows":
            if platform.release() == "7":
                if startingPath:
                    databasePath = startingPath + "\\Users\\*\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
                else:
                    databasePath = "C:\\Users\\*\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
        elif platform.system() == "Windows":
            if platform.release() == "XP":
                if startingPath:
                    databasePath = startingPath + "\\Documents and Settings\\*\\Application Support\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
                else:
                    databasePath = "C:\\Documents and Settings\\*\\Application Support\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
        elif platform.system() == "Darwin":
            if startingPath:
                databasePath = startingPath +"/Users/*/Library/Application Support/Google/Chrome/Default/Sync Data/SyncData.sqlite3"
            else:
                databasePath = "/Users/*/Library/Application Support/Google/Chrome/Default/Sync Data/SyncData.sqlite3"
        else:
            Report("ERROR: no system detected", 2)
            return databaseList
    except Exception as err:
        Report(str(err),2)

    for file in glob.glob(databasePath):
        databaseList.append(SyncFile(file))
    return databaseList


class SyncFile():
    def __init__(self, database):
        self.database = database

        self.connection = lite.connect(self.database)
        self.cursor = self.connection.cursor()

        self.tables = []
        # Checks to see if the passed database is locked. If so, will raise the error and stop creating the object.
        try:
            self.SQLiteTables()
        except lite.OperationalError as err:
            raise err
        self.UserInfo()

        #for user in self.userAccount:
            #print(self.ConvertTime(user[1]))

        self.cursor.execute("SELECT * FROM `metas`;")
        # Fill the metadata var with the contents of the metas table
        self.metadata = self.cursor.fetchall()

        self.Encrypted()
        self.AttachedComputers()
        self.RecoveryEmail()
        self.FirstName()
        self.LastName()
        self.DateOfBirth()
        self.RecoveryPhoneNumber()
        self.Extensions()
        self.HTTPSites()
        self.HTTPSSites()


    def SQLiteTables(self):
        """
        Sets a list of the tables in the SQLite database should always be 5
            deleted_metas, metas, models, share_info, share_version
        """
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        except lite.OperationalError as err:
            raise err
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
        self.recoveryEmail = False
        for row in self.metadata:
            # b'\x8a\xbf\x0f5 is the signature for a recovery email
            if str(row[23])[:15] == "b'\\x8a\\xbf\\x0f5":
                if self.recoveryEmail:
                    self.recoveryEmail.append(str(row[18])[36:])
                else:
                    self.recoveryEmail = [str(row[18])[36:]]

    def GetRecoveryEmail(self):
        return self.recoveryEmail

    def FirstName(self):
        self.firstName = False
        for row in self.metadata:
            name = str(row[18])[15:24]
            if name == "FirstName":
                self.firstName = str(row[18][25:])

    def GetFirstName(self):
        return self.firstName

    def LastName(self):
        self.lastName = False
        for row in self.metadata:
            name = str(row[18])[15:23]
            if name == "LastName":
                self.lastName = str(row[18][24:])

    def GetLastName(self):
        return self.lastName

    def GetFullName(self):
        if self.firstName and self.lastName:
            return str(self.firstName + " " + self.lastName)
        else:
            return False

    def DateOfBirth(self):
        self.DOB = False
        for row in self.metadata:
            name = str(row[18])[15:23]
            if name == "BirthDay":
                if self.DOB:
                    date = str(row[18][24:])
                    if len(date) == 1:
                        date = "0"+ date
                    self.DOB = date + self.DOB[2:]
                else:
                    self.DOB = "------"
                    date = str(row[18][24:])
                    if len(date) == 1:
                        date = "0"+ date
                    self.DOB = date + self.DOB[2:]
            elif name == "BirthYea":
                if self.DOB:
                    self.DOB = self.DOB[:2] + str(row[18][25:])
                else:
                    self.DOB = "------"
                    self.DOB = self.DOB[:2] + str(row[18][25:])

    def GetFullInfo(self):
        # Returns a list inside a list for printing unification
        if self.GetFullName() and self.DOB:
            return [[self.GetFullName(), self.DOB]]
        else:
            return False

    def RecoveryPhoneNumber(self):
        self.recoveryPhone = False
        for row in self.metadata:
            name = str(row[18])[15:28]
            if name == "RecoveryPhone":
                self.recoveryPhone = str(row[18][35:])

    def GetRecoveryPhone(self):
        return self.recoveryPhone

    def Extensions(self):
        self.extension = False
        for row in self.metadata:
            if str(row[23])[:15] == "b'\\xba\\xbf\\x17i":
                if self.extension:
                    self.extension.append(str(row[18]))
                else:
                    self.extension = [str(row[18])]

    def GetExtensions(self):
            return self.extension

    def Encrypted(self):
        self.encrypted = False
        for row in self.metadata:
            if str(row[18]) == "encrypted":
                self.encrypted = True
                Report(str("NOTE: The database located at: {0} is encrypted\n".format(self.database)), 1)
                break
    def HTTPSites(self):
        self.http = False
        for row in self.metadata:
            if row[18] == None:
                continue
            elif str(row[18][:7]).lower() == "http://":
                if self.http:
                    # TODO when visit time is determined add this in to the append function
                    self.http.append(row[18])
                else:
                    self.http = [row[18]]

    def HTTPSSites(self):
        self.https = False
        for row in self.metadata:
            if row[18] == None:
                continue
            elif str(row[18][:8]).lower() == "https://":
                if self.https:
                    # TODO when visit time is determined add this in to the append function
                    self.https.append(row[18])
                else:
                    self.https = [row[18]]
    def GetAllSites(self):
        if self.http and self.https:
            return self.http + self.https
        elif not self.https and not self.http:
            return False
        elif self.http:
            return self.http
        else:
            return self.https

def DisplayData(data):
    """
    Prints lists that has lists of pairs, second usually being a formatted date, or prints entire passed list
    """
    if isinstance(data, list):
        for item in data:
            if len(item) == 2:
                Report(str(item[0].ljust(35, ":") + " " + item[1].rjust(20, ":")))
            else:
                Report(str(item))
    else:
        Report(str(data))


def Report(msg, level=False):
    """
    Prints the msg based on the verbosity level. if no verbosity level passed, it will print the message.
    Higher levels are more important. A 1 verbosity will print everything, a 2 will print level 2&3, a 3 will print 3
    """

    if not level:
        if not outFile:
            print(msg)
        else:
            outFile.write(msg+'\n')
    elif level >= verbosity:
        if not outFile:
            print(msg)
        else:
            outFile.write(msg+'\n')


def CheckFile(filePath):
    if not filePath:
        return filePath
    elif os.path.exists(filePath):
        f = open(filePath, "w")
        Report("File {0} already exists, writing over it\n".format(filePath), 1)
        return f
    else:
        f = open(filePath, "w")
        Report("File {0} does not exist, creating it\n".format(filePath), 1)
        return f


def main():
    global verbosity
    global outFile

    args = ParseCommandLine()
    syncList = []
    verbosity = args.verbose
    outFile = CheckFile(args.outFile)

    if args.database:
        try:
            syncList.append(SyncFile(args.database))
        except Exception as err:
            Report(err, 3)
    else:
        try:
            syncList = GetDatabases(args.path)
        except Exception as err:
            Report(err, 3)

    for syncFile in syncList:
        Report("\nDatabase: {0}\n".format(syncFile.database).center(56))
        Report("Email Account".center(35, "=") +" "+ "Time added".center(20, "=")+"\n")
        DisplayData(syncFile.GetUserInfo())
        Report("")
        if syncFile.GetFullInfo():
            Report("Full Name".center(35, "=") + " "+"DOB (DDYYYY)".center(20, "=")+"\n")
            DisplayData(syncFile.GetFullInfo())
            Report("")
        else:
            Report("Full Name".center(35, "=") + " "+"DOB (DDYYYY)".center(20, "=")+"\n", 1)
            Report("No full info available", 1)
            Report("", 1)
        Report("Computer Name".center(35, "=")+" "+ "Time added".center(20, "="))
        Report("{0} Computer(s) were synced".format(len(syncFile.GetAttachedComputers())).center(35, "_"), 1)
        Report("")
        DisplayData(syncFile.GetAttachedComputers())
        Report("")
        if syncFile.GetRecoveryEmail():
            Report("Recovery Email".center(35, "=")+"\n")
            DisplayData(syncFile.GetRecoveryEmail())
            Report("")
        else:
            Report("Recovery Email".center(35, "=")+"\n", 1)
            Report("No Recovery email found", 1)
            Report("", 1)
        if syncFile.GetRecoveryPhone():
            Report("Recovery Phone".center(35, "=")+"\n")
            DisplayData(syncFile.GetRecoveryPhone())
            Report("")
        else:
            Report("Recovery Phone".center(35, "=")+"\n", 1)
            Report("No Recovery phone found", 1)
            Report("", 1)
        if syncFile.GetExtensions():
            Report("Extensions(s)".center(35, "="))
            Report("{0} Extensions were Found".format(len(syncFile.GetExtensions())).center(35, "_"), 1)
            Report("")
            DisplayData(syncFile.GetExtensions())
            Report("")
        else:
            Report("Extensions(s)".center(35, "=")+"\n", 1)
            Report("No Extensions found", 1)
            Report("", 1)
        if syncFile.GetAllSites():
            Report("All Sites".center(35, "="))
            Report("{0} Sites found".format(len(syncFile.GetAllSites())).center(35, "_"), 1)
            Report("")
            DisplayData(syncFile.GetAllSites())
            Report("")
        else:
            Report("All Sites".center(35, "=")+"\n", 1)
            Report("No sites were found", 1)
            Report("", 1)

        if outFile:
            outFile.close()
            outFile = False
            Report("The out file has been closed.\n", 1)
        Report("The Program has finished. Exiting now\n", 3)


if __name__ == '__main__':
    main()