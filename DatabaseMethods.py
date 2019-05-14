
import sqlite3


class Database(object):
    def AddToDatabase(self,username, IP, location, LastLogin, Port):
        conn = sqlite3.connect('Users.db')#connect to the database

        try:
            conn.execute("CREATE TABLE USERS(ID INTEGER PRIMARY KEY, Username TEXT NOT NULL, PORT INTEGER,IP TEXT NOT NULL, Location INTEGER, LastLogin INTEGER);")
            conn.commit()
        except sqlite3.OperationalError:
            print("Table has already been created")
        theCursor = conn.cursor()
        conn.execute("INSERT INTO Users VALUES (:ID,:Username,:PORT,:IP,:Location,:LastLogin)",{'ID':None,'Username':username,'PORT':Port,'IP':IP,'Location':location,'LastLogin':LastLogin})

        conn.commit()
        conn.close()

    def AddtoConversationDatabse(self,sender,destination,Message,TimeStamp,Encryption):
        conn = sqlite3.connect('Users.db')  # connect to the database

        try:
            conn.execute(
                "CREATE TABLE Messages(ID INTEGER PRIMARY KEY, Sender TEXT NOT NULL, Receiver TEXT NOT NULL,Message TEXT NOT NULL, TimeStamp TEXT NOT NULL, ENCRYPTION INTEGER NOT NULL);")
            conn.commit()
        except sqlite3.OperationalError:
            print("Messages Table has already been created")
        theCursor = conn.cursor()
        conn.execute("INSERT INTO Messages VALUES (:ID,:Sender,:Receiver,:Message,:TimeStamp,:Encryption)",
                     {'ID':None,'Sender': sender, 'Receiver': destination, 'Message': Message, 'TimeStamp': TimeStamp,
                      'Encryption': Encryption})
        conn.commit()
        conn.close()

    def AddtoFileDatabase(self,sender, destination, filename, filetype, Timestamp, Encryption=0):
        conn = sqlite3.connect('Users.db')  # connect to the database

        try:
            conn.execute(
                "CREATE TABLE Files (ID INTEGER PRIMARY KEY, Sender TEXT NOT NULL, Receiver TEXT NOT NULL,FileName TEXT NOT NULL,FileType TEXT NOT NULL, TimeStamp TEXT NOT NULL, ENCRYPTION INTEGER NOT NULL);")
            conn.commit()
        except sqlite3.OperationalError:
            print("Files Table has already been created")
        theCursor = conn.cursor()
        conn.execute("INSERT INTO Files VALUES (:ID,:Sender,:Receiver,:FileName,:FileType,:TimeStamp,:Encryption)",
                     {'ID':None,'Sender': sender, 'Receiver': destination, 'FileName': filename,'FileType':filetype, 'TimeStamp': Timestamp,
                      'Encryption': Encryption})
        conn.commit()
        conn.close()

    def AddtoProfileDatabase(self,user,fullname=None, position=None, description=None, location=None, picture=None,encryption=0,decryptionKey=None):
        conn = sqlite3.connect('Users.db')  # connect to the database
        try:
            conn.execute(
                "CREATE TABLE UserProfile (ID INTEGER PRIMARY KEY,UserName TEXT NOT NULL, FullName TEXT, Position TEXT ,Description TEXT,Location TEXT, Picture TEXT, Encryption INTEGER NOT NULL, DecryptionKey TEXT);")
            conn.commit()
        except sqlite3.OperationalError:
            print("Profile Table has already been created")
        theCursor = conn.cursor()
        conn.execute("INSERT INTO UserProfile VALUES (:ID,:UserName,:FullName,:Position,:Description,:Location,:Picture,:Encryption,:DecryptionKey)",
                     {'ID': None, 'UserProfile': user, 'FullName': fullname, 'Position': position, 'Description': description, 'Location': location,'Picture': picture,"Encryption":encryption,
                      'DecryptionKey': decryptionKey})
        conn.commit()
        conn.close()

    def setup_database(self):
        conn = sqlite3.connect('Users.db')
        c= conn.cursor()
        conn.commit() # connection commit commits current transaction
        conn.close()

    def delete_table(self):
        conn = sqlite3.connect('Users.db')
        conn.execute("DROP TABLE IF EXISTS Users")
        conn.commit()


    def RetrieveData(self):
        conn = sqlite3.connect('Users.db')
        c= conn.cursor()
        UsersList = []
        try:
            #result = conn.execute("SELECT ID, Username, PORT, Location,LastLogin")
            result = conn.execute("SELECT Username FROM Users")
            for row in result:
                #print("ID:" , row[0])
                #print row
                #print("Username:",row[0])
                UsersList.append(row)

                #print (OnlineUsersDictionary)
                #print("PORT:", row[2])
                #print("Location:", row[3])
                #print("LastLogin:",row[4])
                #print(UsersList)
        except sqlite3.OperationalError:
            print("exception catached RetrieveData for online display")
        except:
            print("table is not there")
        print(UsersList)
        return UsersList
    def RetrieveSingleDataIP(self,IP):
        conn=sqlite3.connect('Users.db')
        c = conn.cursor()
        RecipientDictionary = {}
        try:
            result = conn.execute("SELECT * FROM Users WHERE IP = '{}'".format (IP))
            error =0
        except:
            error = 1
        for col in result:
            RecipientDictionary = {"ID":col[0],"Username":col[1],"PORT":col[2],"IP":col[3],"LOCATION":col[4],"LastLogin":col[5]}


        #print (RecipientDictionary)
        conn.commit()
        conn.close()
        return RecipientDictionary

    def RetrieveSingleDataUserName(self,user):
        conn = sqlite3.connect('Users.db')
        c = conn.cursor()
        RecipientDictionary = {}
        try:
            result = conn.execute("SELECT * FROM Users WHERE Username = '{}'".format(user))
            error = 0
        except:
            error = 1
        for col in result:
            RecipientDictionary = {"ID": col[0], "Username": col[1], "PORT": col[2], "IP": col[3], "LOCATION": col[4], "LastLogin": col[5]}

            # print (RecipientDictionary)
        conn.commit()
        conn.close()
        return RecipientDictionary



