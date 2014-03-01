__author__ = 'marleyjaffe'

import sqlite3 as lite
import argparse
import os
import time
import glob
import platform

# Sets Global variables for verbosity and outFile
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
    # Creates a link to a database outside of the normal system path
    parser.add_argument('-d', '--database', type=ValidateDatabase,
                        help="Full path to database in question")

    # Allows the user to create a starting path for a system extraction.
    # If set the program will go to this path before going into each users folder
    parser.add_argument('-p', '--path', default=False,
                        help="Starting Path to where the database should recursively look for databases")

    # Verbose CLI argument, enables error printing etc.
    parser.add_argument('-v', '--verbose', type=int, default=3,
                        help="Makes the program print extra information to the screen")

    # Allows the output from the program to be saved to a file.
    # If no file is set, the program will print data to the screen.
    parser.add_argument('-f', '--outFile', default=False, help="allows the output to be stored to a file")

    return parser.parse_args()
    # End ParseCommandLine ================================


def ValidateDatabase(filePath):
    """
    Name:           ValidateDatabase

    Description:    Checks the passed database to ensure its readable and a file

    Input:          The path to the file

    Actions:        Checks the file to ensure it is a file and is readable

    """
    if os.path.isfile(filePath):		 # Checks to ensure the file exists
        if os.access(filePath, os.R_OK): # Checks to ensure the program has read access
            return filePath
        else:
            raise argparse.ArgumentTypeError("Error: File is not readable")
    else:
        raise argparse.ArgumentTypeError("Error: Path is not valid")
    # End ValidateDatabase ================================


def GetDatabases(startingPath):
    """
    Name:           GetDatabases

    Description:    Runs through each users directory on a system to pull the SyncData.sqlite3 file
                    Also has the capability to have this search start in a new location
                        This is useful for file exports when keeping folder structure

    Input:          Starting Path, either the starting path or False

    Actions:        Checks the System type and release.
                    Uses Globing to pull each SyncData.sqlite3 file
                    Adds the found database paths to a list and returns the list

    """

    # Creates a blank list
    databaseList = []

    # TODO Allow the examination of a windows export on mac system and vice versa. Done by passing platform as var
    try:
        # Checks if the running system is Windows
        if platform.system() == "Windows":
            # Checks if the system is 7 or XP
            if platform.release() == "7":
                # Checks if there was a starting path provided
                if startingPath:
                    # Sets the databasePath to the the OS specific path with the starting path defined.
                    databasePath = startingPath + "\\Users\\*\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
                else:
                    # Sets the databasePath to the the OS specific path.
                    databasePath = "C:\\Users\\*\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
            elif platform.release() == "XP":
                if startingPath:
                    # Sets the databasePath to the the OS specific path with the starting path defined.
                    databasePath = startingPath + "\\Documents and Settings\\*\\Application Support\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
                else:
                    # Sets the databasePath to the the OS specific path
                    databasePath = "C:\\Documents and Settings\\*\\Application Support\\Google\\Chrome\\User Data\\Default\\Sync Data\\SyncData.sqlite3"
        elif platform.system() == "Darwin":
            if startingPath:
                # Sets the databasePath to the the OS specific path with the starting path defined.
                databasePath = startingPath +"/Users/*/Library/Application Support/Google/Chrome/Default/Sync Data/SyncData.sqlite3"
            else:
                # Sets the databasePath to the the OS specific path
                databasePath = "/Users/*/Library/Application Support/Google/Chrome/Default/Sync Data/SyncData.sqlite3"
        else:
            Report("ERROR: no system detected", 3)
            return databaseList
    except Exception as err:
        Report(str(err),2)

    # Performs the actual glob search using the previously defined databasePath
    for file in glob.glob(databasePath):
        # Adds each found database to the databaseList
        databaseList.append(SyncFile(file))
    # Returns the databaseList
    return databaseList
    # End GetDatabases ====================================


class SyncFile():
    def __init__(self, database):
        """
        Name:           SyncFile

        Description:    Creates objects from passed database

        Input:          Path to the syncFile Database

        Actions:        Creates the object using set functions
                        Uses the sqlite3 library as lite

        """
        # Sets the self.database to the database path
        self.database = database

        # Creates a connection to the database
        self.connection = lite.connect(self.database)
        # Creates a cursor object for the database
        self.cursor = self.connection.cursor()

        # Sets the initial database tables to nothing
        self.tables = []

        # Checks to see if the passed database is locked. If so, will raise the error and stop creating the object.
        # Also sets the tables var
        try:
            # Runs the objects SQLiteTables function
            self.SQLiteTables()
        except lite.OperationalError as err:
            raise err
        # Will initiate the userAccount var
        self.UserInfo()

        # Gets all data from the metas table from the database
        self.cursor.execute("SELECT * FROM `metas`;")
        # Fill the metadata var with the contents of the metas table
        self.metadata = self.cursor.fetchall()

        # Used to set Object variables

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
        # End __init__ ====================================

    def SQLiteTables(self):
        """
        Name:           SQLiteTables

        Description:    Sets a list of the tables in the SQLite database

        Input:          None

        Actions:        Uses the sqlite_master tables to pull all tables names

        Note:           should always be 5 tables
                            deleted_metas, metas, models, share_info, share_version
        """
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        # Will error out if database is locked due to database being open (Chrome open)
        except lite.OperationalError as err:
            raise err
        # Sets the tables to all the records in the cursor
        self.tables = self.cursor.fetchall()
        # Removes the tuple and returns just the names in the list
        self.tables = [i[0] for i in self.tables]
        # End SQLiteTables ================================

    def UserInfo(self):
        """
        Name:           UserInfo

        Description:    Pulls the name and create time from the share_info table

        Input:          None

        Actions:        Pulls the name and db_create_time from the share_info table sets the out put to self.userAccount
        """
        self.userAccount = []
        self.cursor.execute("SELECT `name`, `db_create_time` FROM `share_info`;")
        # Returns a tuple of email account and creation time in epoch
        self.userAccount = self.cursor.fetchall()
        # End UserInfo ====================================

    def ConvertTime(self, timeInEpoch):
        """
        Name:           ConvertTime

        Description:    Converts seconds since epoch into readable format (2014-02-24 21:49:54)

        Input:          Epoch Time in seconds

        Actions:        Uses the time library to format passed epoch time
        """
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeInEpoch))
        # End ConvertTime =================================

    def AttachedComputers(self):
        """
        Name:           AttachedComputers

        Description:    Sets the computer names that the users has logged into

        Input:          None

        Actions:        Runs through each row in the metas table and adds the found computers to a list
                        Sets the ComputerNames list to the values from column 19 in the metadata file
        """
        self.computerNames = []
        for row in self.metadata:
            # b'\xd2\xb9 is the signature for a computer, remove false positives that don't have enough data
            if str(row[23])[:10] == "b'\\xd2\\xb9" and len(str(row[23])) > 23:
                # Adds a list item to the list with the computer name in [0] and date first signed in to [1]
                # Row 7 needs to be divided by 1000 because the value is stored in milliseconds since epoch
                self.computerNames.append([row[18], row[7]/1000])
        # End AttachedComputers ===========================

    def GetUserInfo(self):
        """
        Name:           GetUserInfo

        Description:    Returns list of list, each mini list has user email and when Chrome was first signed in

        Input:          None

        Actions:        Needs UserInfo function to be run prior to get userAccount initialized
                        converts time stored in userAccount's list of tuples into human readable
                        Uses ConvertTime function
                        returns the new list
        """
        users = []
        for user in self.userAccount:
            tempList = []
            tempList.append(user[0])
            tempList.append(self.ConvertTime(user[1]))
            users.append(tempList)
        return users
        # End GetUserInfo =================================

    def GetAttachedComputers(self):
        """
        Name:           GetAttachedComputers

        Description:    Returns list of lists, each mini list has computer string name and date account was added

        Input:          None

        Actions:        Needs AttachedComputers function to be run prior to get computerNames initialized
                        converts time stored in computerNames's list of tuples into human readable
                        Uses ConvertTime function
                        returns the new list
        """
        computerInfo = []
        for computer in self.computerNames:
            tempList = []
            tempList.append(computer[0])
            tempList.append(self.ConvertTime(computer[1]))
            computerInfo.append(tempList)
        return computerInfo
        # End GetAttachedComputers ========================

    def RecoveryEmail(self):
        """
        Name:           RecoveryEmail

        Description:    Sets the recoveryEmail variable

        Input:          None

        Actions:        Adds recovery emails found in the metas table into the recoveryEmail list
        """
        # Sets the var to false to begin with.
        self.recoveryEmail = False
        for row in self.metadata:
            # b'\x8a\xbf\x0f5 is the signature for a recovery email
            if str(row[23])[:15] == "b'\\x8a\\xbf\\x0f5":
                if self.recoveryEmail:
                    # Adds other found email to the list
                    self.recoveryEmail.append(str(row[18])[36:])
                else:
                    # Sets the first found email to the first item in the list
                    self.recoveryEmail = [str(row[18])[36:]]
        # End RecoveryEmail ===============================

    def GetRecoveryEmail(self):
        """
        Name:           GetRecoveryEmail

        Description:    Returns the recoveryEmail var

        Input:          None

        Actions:        Returns the recoveryEmail var
        """
        return self.recoveryEmail
        # End GetRecoveryEmail ============================

    def FirstName(self):
        """
        Name:           FirstName

        Description:    Sets the firstName variable

        Input:          None

        Actions:        Sets the firstName variable to either the found name or False
        """
        self.firstName = False
        for row in self.metadata:
            name = str(row[18])[15:24]
            if name == "FirstName":
                self.firstName = str(row[18][25:])
        # End FirstName ===================================

    def GetFirstName(self):
        """
        Name:           GetFirstName

        Description:    Returns the firstName Var

        Input:          None

        Actions:        Returns the firstName var
        """
        return self.firstName
        # End GetFirstName ================================

    def LastName(self):
        """
        Name:           LastName

        Description:    Sets the lastName variable

        Input:          None

        Actions:        Sets the lastName variable to either the found name or False
        """
        self.lastName = False
        for row in self.metadata:
            name = str(row[18])[15:23]
            if name == "LastName":
                self.lastName = str(row[18][24:])
        # End LastName ====================================

    def GetLastName(self):
        """
        Name:           GetLastName

        Description:    Returns the lastName var

        Input:          None

        Actions:        Returns the lastName var
        """
        return self.lastName
        # End GetLastName =================================

    def GetFullName(self):
        """
        Name:           GetFullName

        Description:    Concatenates the first and last name

        Input:          None

        Actions:        Checks if both the first and last name have content
                            Concatenates the first and last name, adding a space in-between
                        Returns the full name or false
        """
        if self.firstName and self.lastName:
            return str(self.firstName + " " + self.lastName)
        else:
            # If the first or last name do not exits a full name can not be found and return False
            return False
        # End GetFullName =================================

    def DateOfBirth(self):
        """
        Name:           DateOfBirth

        Description:    Sets the Date of Birth variable if data is found else sets it to False

        Input:          None

        Actions:        Sets DOB var to False
                        Checks to see if date can be found, if so sets the var to it
                        Uses dashes to indicate blanks, only used if only day or year not found
                        Current data suggests only day and year are stored, code reflects as such
        """
        # Sets the DOB var to False
        self.DOB = False
        # Loops through each line in the metadata var
        for row in self.metadata:
            # Sets the value of row 18 to name
            name = str(row[18])[15:23]
            # Checks if name is BirthDay
            if name == "BirthDay":
                # Checks if the DOB is false or it has been initialized
                if self.DOB:
                    # Sets the value found to temporary date var
                    date = str(row[18][24:])
                    # Checks to see if the date is a single digit
                    if len(date) == 1:
                        # Adds a 0 before the single digit
                        date = "0"+ date
                    # Adds the day to the beginning of the DOB value
                    self.DOB = date + self.DOB[2:]
                else:
                    # Creates a placeholder of dashes
                    self.DOB = "------"
                    date = str(row[18][24:])
                    if len(date) == 1:
                        date = "0"+ date
                    self.DOB = date + self.DOB[2:]
            elif name == "BirthYea":
                if self.DOB:
                    # Preserves the set day value adds the year to the end
                    self.DOB = self.DOB[:2] + str(row[18][25:])
                else:
                    self.DOB = "------"
                    self.DOB = self.DOB[:2] + str(row[18][25:])
        # End DateOfBirth =================================

    def GetFullInfo(self):
        """
        Name:           GetFullInfo

        Description:    Returns the full name and the DOB. Returns False if either of the values do not exist

        Input:          None

        Actions:        Returns the full name and the DOB in a list.
                        Returns False if either of the values are set to False
        """
        # Returns a list inside a list for printing unification
        if self.GetFullName() and self.DOB:
            return [[self.GetFullName(), self.DOB]]
        else:
            return False
        # End GetFullInfo =================================

    def RecoveryPhoneNumber(self):
        """
        Name:           RecoveryPhoneNumber

        Description:    Sets recoveryPhone var

        Input:          None

        Actions:        Sets recoveryPhone var to False
                        Sets the var to the number if found
        """
        self.recoveryPhone = False
        for row in self.metadata:
            name = str(row[18])[15:28]
            if name == "RecoveryPhone":
                self.recoveryPhone = str(row[18][35:])
        # End RecoveryPhoneNumber =========================

    def GetRecoveryPhone(self):
        """
        Name:           GetRecoveryPhone

        Description:    Returns recoveryPhone Var

        Input:          None

        Actions:        Returns recoveryPhone Var
        """
        return self.recoveryPhone
        # End GetRecoveryPhone

    def Extensions(self):
        """
        Name:           Extensions

        Description:    Returns a list of all extensions found in the metas table

        Input:          None

        Actions:        Sets var to False
                        Adds Extension name to list if extension is found
        """
        self.extension = False
        for row in self.metadata:
            if str(row[23])[:15] == "b'\\xba\\xbf\\x17i":
                if self.extension:
                    self.extension.append(str(row[18]))
                else:
                    self.extension = [str(row[18])]
        # End Extensions ==================================

    def GetExtensions(self):
        """
        Name:           GetExtensions

        Description:    Returns extension var

        Input:          None

        Actions:        Returns extension var
        """
        return self.extension
        # End GetExtensions ===============================

    def Encrypted(self):
        """
        Name:           Encrypted

        Description:    Checks to see if records are encrypted

        Input:          None

        Actions:        Checks to see if metas table values are encrypted
                            This will limit the amount of data obtainable
                        Sets var to False
                        If encryption is found
                            Set encryption var to true
                            Report that the database is encrypted
        """
        self.encrypted = False
        for row in self.metadata:
            if str(row[18]) == "encrypted":
                self.encrypted = True
                # Report using level 1 due to some information being able to be found, just not all
                Report(str("NOTE: The database located at: {0} is encrypted\n".format(self.database)), 1)
                break
        # End Encrypted ===================================

    def HTTPSites(self):
        """
        Name:           HTTPSites

        Description:    Finds all HTTP sites and adds them to a list

        Input:          None

        Actions:        Sets HTTP var to false
                        If http:// is found, add site to list
        """
        self.http = False
        for row in self.metadata:
            # Program was hanging on None values
            if row[18] == None:
                continue
            elif str(row[18][:7]).lower() == "http://":
                if self.http:
                    # TODO when visit time is determined add this in to the append function
                    self.http.append(row[18])
                else:
                    self.http = [row[18]]
        # End HTTPSites ===================================

    def HTTPSSites(self):
        """
        Name:           HTTPSSites

        Description:    Finds all HTTPS sites and adds them to a list

        Input:          None

        Actions:        Sets HTTPS var to false
                        If https:// is found, add site to list
        """
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
        # End HTTPSSites ==================================

    def GetAllSites(self):
        """
        Name:           GetAllSites

        Description:    Returns all http and https sites in one list

        Input:          None

        Actions:        Checks to see if both http and https have data
                        Returns the new list
                        If only one list has data return that one
                        Return False if both lists are False
        """
        if self.http and self.https:
            return self.http + self.https
        elif not self.https and not self.http:
            return False
        elif self.http:
            return self.http
        else:
            return self.https
        # End GetAllSites =================================

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
        Report("Email Account".center(35, "=")+" "+"Time added".center(20, "=")+"\n")
        DisplayData(syncFile.GetUserInfo())
        Report("")
        if syncFile.GetFullInfo():
            Report("Full Name".center(35, "=")+" "+"DOB (DDYYYY)".center(20, "=")+"\n")
            DisplayData(syncFile.GetFullInfo())
            Report("")
        else:
            Report("Full Name".center(35, "=")+" "+"DOB (DDYYYY)".center(20, "=")+"\n", 1)
            Report("No full info available", 1)
            Report("", 1)
        Report("Computer Name".center(35, "=")+" "+"Time added".center(20, "="))
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