#!/usr/bin/python
""" Compsys 302 Python Assignment

    COMPSYS302 - Software Design
    Author: Arjun Kumar (akmu999@aucklanduni.ac.nz)
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)

# The address we listen for connections on
listen_ip = "0.0.0.0"
listen_port = 10001

#Imported Modules
import mimetypes
import base64
import os
import sqlite3
import cherrypy
import hashlib
import urllib2
import threading
import json
import time
from DatabaseMethods import Database
from jinja2 import Environment,FileSystemLoader

#The setup for jinja2. A Templates folder is used to store the html files
env = Environment(loader=FileSystemLoader('Templates'))
instance = Database()

#Main Class
class MainApp(object):

    #CherryPy Configuration
    _cp_config = {'tools.encode.on': True,
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on' : 'True',
                  #path to '/' using the os module
                  '/': {
                      'tools.sessions.on': True,
                      'tools.staticdir.root': os.path.abspath(os.getcwd())
                  },
                  # path to '/static' using the os module
                  '/static': {
                      'tools.staticdir.on': True,
                      'tools.staticdir.dir': './public'
                  }
                  }


    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "I don't know where you're trying to go, so have a 404 Error."
        cherrypy.response.status = 404
        return Page

    #Index Page, This is the login page
    @cherrypy.expose
    def index(self):
        Template = env.get_template('Index.html')
        return Template.render()       #this return statement returns back a rendered template. No variables are part of
                                    #render for this code



    # LOGGING IN AND OUT
    @cherrypy.expose
    def signin(self, username=None, password=None,location=None):
        if((username==None)or (password==None) or (location==None)):
            raise cherrypy.HTTPRedirect('/index')
        else:
            """Check their name and password and send them either to the main page, or back to the main login screen."""
            from socket import gethostname, gethostbyname
            ip=gethostbyname(gethostname())     #creating a copy of the user credentials and passing them to the other functions
            usernameCredential= username        #such as report to api and updating the database
            passwordCredential = password
            locationC = location
            ipC =ip
            salt = "COMPSYS302-2017"
            password = password+salt
            password_bytes = password.encode('utf-8')  #encode the password to utf-8 format bytes
            hashedpassword = hashlib.sha256(password_bytes).hexdigest() #hash the password which is in bytes and then get a string of hex type
            #report to Login Server url link
            ReportToAPI = urllib2.Request(('http://cs302.pythonanywhere.com/report?username={}&password={}&location={}&ip={}&port=10001&enc=0'.format(usernameCredential,hashedpassword,locationC,ipC)))
            reportRequest = urllib2.urlopen(('http://cs302.pythonanywhere.com/report?username={}&password={}&location={}&ip={}&port=10001&enc=0'.format(usernameCredential,hashedpassword,locationC,ipC)))
            logindata = reportRequest.read() #read the data returned from the login servr
            logindata = logindata.decode("utf-8")   #read the login data
            error = self.authoriseUserLogin(logindata,usernameCredential) #call the authenitcate function to check the login credentials
            print(logindata) #print statement used for testing purposes, print statements at other places in the code were also used and may still be there
            if (error == 0):
                    threading.Timer(30, self.ThreadLogin, args=(usernameCredential, hashedpassword, locationC)).start() # start a 30 second thread for report to login server api
                    threading.Timer(30, self.UpdateOnlineUserDatabase, args=(usernameCredential, hashedpassword, locationC)).start() # start a thread to update the database
                    raise cherrypy.HTTPRedirect('/HomePage') #go to the homepage function
            else:
                raise cherrypy.HTTPRedirect('/login') #stay at the login function


    @cherrypy.expose
    def ThreadLogin(self,user,password,location):
        #login thread, gets the current users ip and then uses it with the parameters received to form the url link to report to the reportAPI
        from socket import gethostname, gethostbyname
        ip = gethostbyname(gethostname())
        ReportToAPI = urllib2.Request(('http://cs302.pythonanywhere.com/repor.t?username={}&password={}&location={}&ip={}&port=10001&enc=0'.format(user,password,location,ip)))
        reportRequest = urllib2.urlopen(('http://cs302.pythonanywhere.com/report?username={}&password={}&location={}&ip={}&port=10001&enc=0'.format(user,password,location,ip)))

    #this function is used to update the table of the online users. This function is called every 30 seconds and the getList is called from the login server.
    def UpdateOnlineUserDatabase(self,user,password,location):
        instance.delete_table()
        instance.RetrieveData()
        onlineUsersData = urllib2.urlopen('http://cs302.pythonanywhere.com/getList?username={}&password={}&enc=0&json=1'.format(user,password))
        data = onlineUsersData.read()
        data = data.decode("utf=8")
        book = json.loads(data)
        for username in book:

            instance.AddToDatabase(book[username]['username'], book[username]['ip'], book[username]['location'],
                               book[username]['lastLogin'], book[username]['port'])

        instance.RetrieveData()

    #Online Messages Function helps in displaying the messages on to the html page.
    @cherrypy.expose
    def onlineMessages(self,username):
        List = {}
        List = self.FindMessages(username) #username regarding the messages
        import ast
        List = ast.literal_eval(json.dumps(List)) #clear the list of the prefix u
        print(List)
        print(len(List))    #get the length of the list made up of dictionary
        messageList = []    #message list to store the messages
        for index in range(len(List)):  # for loop to iterate through the list of the messages and then get the keys
                                        # for every index. Then put them together into a string and append them.
            Message = List[index]['Message']
            Sender = List[index]['Sender']
            Receiver = List[index]['Receiver']
            TimeStamp = List[index]['TimeStamp']
            MessageTime = time.strftime("%d-%m-%Y %I:%M %p", time.localtime(float((TimeStamp)))) #time format
            data = str(MessageTime)+ ' ' + str(Sender) +' ' + 'to' + ' '+ str(Receiver) + ' ' +' '+ ' '+ ' ' + (Message)
            messageList.append(data) #string message added to the message list
        print(messageList) #print command used for testing

        newList = []
        for index in range(len(messageList)):   #this for loop is to add the <li> list html tags and remove any punctuation
            a = str(messageList[index])
            a = a.replace("'","") #remove apostrophes
            data = str('<li>'+a+'</li>')
            newList.append(data)

        newList = str(newList)
        newList = newList.replace("'","")  #remove every bracket and comma from the list
        newList = newList.replace(",", "")
        newList = newList.replace("[","")
        newList = newList.replace("]","")


        print(newList)      #prin the list
        Template = env.get_template('MessageList.html')
        return Template.render(List = newList) #render the MessageList page with then newList


#The Homepage function used to display data related to homepage. Current users data is used and then the list of
#online users is recieved. These variables are added to the render function and the Homepage is produced.
    @cherrypy.expose
    def HomePage(self):
        if (cherrypy.session.get('username')):

            input_data = self.RetrieveData()
            import ast
            input_data = ast.literal_eval(json.dumps(input_data))
            input_data = str(input_data)
            input_data = input_data.replace("[", " ")
            input_data = input_data.replace("]", " ")
            input_data = input_data.replace("'", " ")
            #f = open("HomePage.html",'r')
            UserName = '{}'.format(cherrypy.session.get('username'))
            Template = env.get_template('HomePage.html')
            return Template.render(Home='Recon', User = UserName, List = input_data)
        else:
            return "USER FLAGGED: UNAUTHORISED ACCESS PLEASE CONTACT SYSTEM ADMINISTRATOR" #The error message returned

    #The get Status API
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getStatus(self):

        #status = LookUpUserStatus(profile_username)
        import ast
        #print(status)
        #status = ast.literal_eval(json.dumps(status))
        #return str(status)


    #The css function is used to by the /css/ in the html page. The function reads the css and returns it.
    @cherrypy.expose
    def css(self,fname):
        f = open(fname,"r")
        data = f.read()
        f.close()
        return data

    #The signout function closes the cherrypy session
    @cherrypy.expose
    def signout(self):
        if (cherrypy.session.get('username')): #if the current cherrypy session
         """Logs the current user out, expires their session"""
        username = cherrypy.session.get('username')
        if (username == None):
            pass
        else:
            cherrypy.lib.sessions.expire()  #log out of the session. expire session and then clear session. Then go back
            cherrypy.session.clear()        #to the INDEX page
        raise cherrypy.HTTPRedirect('/')

    #This function checks the data recieved from the login server and then compares it with the stored string to authenticate
    #the user
    def authoriseUserLogin(self, logindata,username):
        cherrypy.session['username'] = username
        if (logindata == "0, User and IP logged"):
            return 0
        else:
            return 1
     #---------------------------------------------------------------------------MESSAGING START-----------------------------------------------------------------------#
   #The sendMessage API takes in the arguments of sender, time stamp, message and destination
    @cherrypy.expose
    def sendMessage(self,sender=None,stamp=None,Message=None,destination=None):
        if (cherrypy.session.get('username')):
            from socket import gethostname, gethostbyname #get the current users ip
            ip = gethostbyname(gethostname())

            user = ('{}'.format(destination)) #format to lookup the receiver details
            UserDetails = self.RetrieveSingleDataIP(ip) #retrieveSingleSataIp is used to get the details of the user
            RecepientDetails = self.RetrieveSingleDataUserName(user) #user variable is used to get the details of the receiver, not the above statement
            UserSendingMessage = cherrypy.session.get('username')
            timestamp = time.time()
            if (len(RecepientDetails)==0):#if the result is 0 then the user is most likely offline or the enterd username is wrong
                error_code = "USER NOT ONLINE OR WRONG USERNAME"
                error_code = json.dumps(error_code) #return a json errror code

                Template = env.get_template('MessagePage.html')
                return Template.render(Error=error_code)
            else:
                stamp=time.time() #the timestamp
                self.AddtoConversationDatabse(UserSendingMessage, destination, Message, stamp, 0) #if the size of details of sender recieved is not 0 then add the information to
                                                                                                    #message table
                output_dict = {"sender":UserSendingMessage,"destination":RecepientDetails['Username'],"message":Message,"stamp":timestamp} #dictionary containing message and other details
                data = json.dumps(output_dict) #output the dictionary into json
                import ast
                RecepientDetails=ast.literal_eval(json.dumps(RecepientDetails))#
                print (RecepientDetails)
                IP = RecepientDetails['IP'] #get the IP
                PORT = RecepientDetails['PORT']#get the Port
                print(IP)
                print(PORT) #print command to test if the port was right and if the function worked properly
                req = urllib2.Request(('http://{}:{}/receiveMessage'.format(IP,PORT)),data,{'Content-Type':'application/json'}) #open the formed url link and pass the json object
                response = urllib2.urlopen(req)
                raise cherrypy.HTTPRedirect('/MessagePage') #go to the Message function now

    #receive message function user get the JSON object and then extract the information
    #based on the differnt keys. After that add the information to the message table and return 0 for success
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):
        input_data = cherrypy.request.json
        import ast
        input_data = ast.literal_eval(json.dumps(input_data))
        sender = input_data['sender']
        destination = input_data['destination']
        message = input_data['message']
        stamp = input_data['stamp']
        self.AddtoConversationDatabse(sender,destination,message,stamp,0) #add to message table using the function
        print(input_data)
        return '0'

    #get the list of online users
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getOnlineUsersList(self):
        onlineUsersData = urllib2.urlopen('http://cs302.pythonanywhere.com/getList?username={}&password={}&enc=0&json=1'.format(user,password)) #open the url link and then add to it
        data = onlineUsersData.read() #read the data from the url link
        data = data.decode("utf=8") #decode the bytes into string
        book = json.loads(data) #get the dictionary out of json by using json.loads
        input_data = cherrypy.request.json #get the input from cherrypy
        import ast
        input_data = ast.literal_eval(json.dumps(input_data)) #return u prefix
        return input_data #return the input_data

    #function to send file
    @cherrypy.expose
    def sendFile(self,sender=None,destination=None,file=None,filename=None,content_type=None,stamp=None):
        if (cherrypy.session.get('username')):
            from socket import gethostname, gethostbyname
            ip = gethostbyname(gethostname())
            user = ('{}'.format(destination))
            RecepientDetails = self.RetrieveSingleDataUserName(user) #details of the receiever of the file
            UserSendingMessage = cherrypy.session.get('username') #person sending the messsage
            timestamp = time.time() #time stamp

            import ast
            filename = ast.literal_eval(json.dumps(filename))

            filetype = mimetypes.guess_type(filename) #file type using the mimetypes function
            filetype = str(filetype) # filetype output to string
            filetype = filetype.replace("'application/","") #remove some of the unnecessary stuff from the filetype output
            filetype = filetype.replace("', None", "")
            filetype = filetype.replace("(", "")
            filetype = filetype.replace(")", "")
            print (filetype) #print command to check the file type

            if (len(RecepientDetails)==0):
                error_code = "User not online or wrong username or wrong filetype" #error code returned if the size of the query from the database is zero
                error_code = json.dumps(error_code)

                Template = env.get_template('FilePage.html')
                return Template.render(Error = error_code)
            else:
                #size = 0
                #while (size < 349525)
                #Openedfile = file.open().read(8192)
                #size += len(openedfile)
                OpenedFile = open(filename,'rb').read()#open the file
                OpenedFile = base64.b64encode(OpenedFile) #encode the data into base64
                #output dictionary conatining all the arguments to send the json string
                output_dict = {"sender":UserSendingMessage,"destination":RecepientDetails['Username'],"file":OpenedFile,"filename":filename,"content_type":filetype,"stamp":timestamp}
                #put the dictionary into JSON format
                data = json.dumps(output_dict)
                import ast
                RecepientDetails=ast.literal_eval(json.dumps(RecepientDetails))
                print (RecepientDetails)
                IP = RecepientDetails['IP']                 #ip for the person receiving the function
                PORT = RecepientDetails['PORT']             #receiver's port, used to form the url link
                print(IP)
                print(PORT)
                req = urllib2.Request(('http://{}:{}/receiveFile'.format(IP,PORT)),data,{'Content-Type':'application/json'}) #the url link used to open the url link and send the data
                response = urllib2.urlopen(req)#open url
                raise cherrypy.HTTPRedirect('/FilePage') #go to FilePage


    @cherrypy.expose
    def getMessages(self,username):
        input_data = self.FindMessages(username)
        import ast
        print(input_data)
        input_data = ast.literal_eval(json.dumps(input_data))
        input_data = str(input_data)
        input_data = input_data.replace("[", " ")
        input_data = input_data.replace("]", " ")
        input_data = input_data.replace("'", " ")
        f = open("MessagePage.html", 'r')
        UserName = '{}'.format(cherrypy.session.get('username'))
        data = f.read().format(Messages=input_data)
        f.close()
        return data

    #This function is used to set the profile. The parameters from the html forum are passed to the function. Current user
    #name is extraced using the cherrypy username and then the arguments are passed to the add to the profile function to
    #update the profile if already exists or create it if it is not there.
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def setProfile(self,fullname=None,position=None,description=None,location=None,picture=None,encryption=None,decryptionKey=None):
        if(cherrypy.session.get('username')):
            userName = cherrypy.session.get('username')
            self.AddtoProfileDatabase(userName,fullname,position,description,location,picture,encryption,decryptionKey)


    #the get profile API is used by other users to get profile of the current user logged into the account.
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getProfile(self):
        try:
            request = cherrypy.request.json
            import ast
            request = ast.literal_eval(json.dumps(request))
            profile_username = request["profile_username"]
            sender           = request["sender"]
            print("{} called get profile".format(sender))
            from socket import gethostname, gethostbyname
            ip = gethostbyname(gethostname()) #current user ip

            UserDetails = self.RetrieveUserProfile('{}'.format(profile_username))#the user details are extracted usring theretriveUserProfile function
            fullname = UserDetails["FullName"]
            position = UserDetails["Position"]
            description = UserDetails['Description']
            location = UserDetails["Location"]
            picture = UserDetails["Picture"]
            encryption = UserDetails["Encryption"]
            decryptionKey = UserDetails['DecryptionKey']
            output_dict = {"fullname": fullname, "position": position,
                           "description": description, "location": location,"picture":picture,"encryption":encryption,"decryptionKey":decryptionKey}
            data = json.dumps((output_dict)) #dicionary is converted to the json format
            print(data) #print command used to test the data
            return data #the return command is used to return the data
        except:
            return 'error'

    #getPeoplesProfile function is used to extract data for the username if they are online. The data is then passed to the
    #webpage for rendering.
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def getPeoplesProfile(self,username):
        try:
            CurrentUser = cherrypy.session.get('username')
            data = {"sender": CurrentUser, "profile_username":username}
            data = json.dumps(data)
            UserToBeFound = self.RetrieveSingleDataUserName(username)
            import ast
            print (UserToBeFound)
            IP = UserToBeFound['IP']
            PORT = UserToBeFound['PORT']
            req = urllib2.Request(('http://{}:{}/getProfile'.format(IP, PORT)), data,
                                       {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req)
            input_from_calledAPI = response.read()
            print(input_from_calledAPI)
            import ast
            input_from_calledAPI = (json.loads(input_from_calledAPI))
            fullname = input_from_calledAPI['fullname']
            position = input_from_calledAPI['position']
            description = input_from_calledAPI['description']
            location = input_from_calledAPI['location']
            picture = input_from_calledAPI['picture'] #everything is extracted using keys and put into variables
            if ('encryption' in input_from_calledAPI):  #if statements used to check if someone has encryption or not
                encryption = input_from_calledAPI['encryption']
            else:
                encryption = 0 #if no encryption key is given then make the value 0
            if('decryptionKey' in input_from_calledAPI):
                decryptionKey = input_from_calledAPI['decryptionKey']
            else:
                decryptionKey = 0;
            print('Add to Profile Database')
            self.AddtoProfileDatabase(username,fullname, position, description, location, picture, encryption, decryptionKey)
            self.DisplayProfile(fullname, position, description, location, picture)
            Template = env.get_template('ProfilePage.html') #render the profile page with the variable values
            return Template.render(Picture = picture, FullName=fullname, Position=position, Description=description, Location=location)
        except:
            Template = env.get_template('ProfilePage.html')  # render the profile page with the variable values
            return Template.render(Error = "User Not Online OR Wrong UserName")


    @cherrypy.expose
    def DisplayProfile(self,fullname, position, description, location, picture):
        return '0'
        #OnlineUsersList = self.RetrieveData()
        # for x in range(0, len(OnlineUsersList)):
        #     import ast
        #     input_data = ast.literal_eval(json.dumps(OnlineUsersList[x]))
        #     print (input_data)
        #     input_data = str(input_data)
        #     input_data = input_data.replace("[", " ")
        #     input_data = input_data.replace("]", " ")
        #     input_data = input_data.replace("'", " ")
        #     input_data = input_data.replace(",", " ")
        #     print (input_data)
        #
        #     input_data = input_data.replace(" ","")
        #     data = {"profile_username":input_data,"sender":sender}
        #     data = json.dumps(data)
        #     input_data = input_data.replace(" ","")
        #     UserToBeFound = self.RetrieveSingleDataUserName(input_data)
        #     UserToBeFound = ast.literal_eval(json.dumps(UserToBeFound))
        #     print (UserToBeFound)
        #     IP = UserToBeFound['IP']
        #     PORT = UserToBeFound['PORT']
        #     print(IP)
        #     print(PORT)
        #     print(data)
        #     req = urllib2.Request(('http://{}:{}/getProfile'.format(IP, PORT)), data,
        #                           {'Content-Type': 'application/json'})
        #     response = urllib2.urlopen(req)
        #     self.outputFromApiGetProfiles()


    @cherrypy.expose
    @cherrypy.tools.json_in()
    def outputFromApiGetProfiles(self):
        try:
            input_from_calledAPI = cherrypy.request.json
            import ast
            input_from_calledAPI = ast.literal_eval(json.loads(input_from_calledAPI))
            fullname = input_from_calledAPI['sender']
            position = input_from_calledAPI['position']
            description = input_from_calledAPI['description']
            location = input_from_calledAPI['location']
            picture = input_from_calledAPI['picture']
            encryption = input_from_calledAPI['encryption']
            decryptionKey = input_from_calledAPI['decryptionKey']
            print('Add to Profile Database')
            self.AddtoProfileDatabase(fullname, position, description, location, picture, encryption, decryptionKey)
        except:
            return '0'

    #acknoweldge api is not complete
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def acknowledge(self):
        return '0'



    #recieve file api is used to receive file from a client. The json is changed to the dictionary and then the values
    #are extracted using the keys. The data stored in filename is written to a file with file name and then the newly created opened
    #file is closed. The file is saved locally on the the machine
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):
        input_data = cherrypy.request.json
        import ast
        input_data = ast.literal_eval(json.dumps(input_data))
        sender = input_data['sender']
        destination = input_data['destination']
        receivedfile = base64.b64decode(input_data['file']) #the decode bade64 command is used to decode the data back to the original form
        filename = input_data['filename']
        filetype = input_data['content_type']
        print(filetype)
        Timestamp = input_data['stamp']
        OpenedFile = open(filename, 'wb')
        OpenedFile.write(receivedfile)
        OpenedFile.close()
        instance.AddtoFileDatabase(sender, destination, filename,filetype, Timestamp, 0)
        print(input_data)
        return '0'

    #This is the message Page function, it returns a rendered MessagePage
    @cherrypy.expose
    def MessagePage(self):
        Template = env.get_template('MessagePage.html')
        return Template.render()

    # This is the FilePage function, it returns a rendered MessagePage
    @cherrypy.expose
    def FilePage(self):
        Template = env.get_template('FilePage.html')
        return Template.render()

    # This is the ProfilePage function, it returns a rendered MessagePage
    @cherrypy.expose
    def ProfilePage(self):
        Template = env.get_template('ProfilePage.html')
        return Template.render()
        #---------------------------------------------------------------------------MESSAGING END-------------------------------------------------------------------------#

        #---------------------------------------------------------------------------DATABASE FUNCTIONS----------------------------------------------------------------------#
    #The database functions run sqlite queries to access data from the tables

    #The LookUpUserStatus function is used to check the user information
    def LookUpUserStatus(self,profile_username):
        conn = sqlite3.connect('Users.db')
        c = conn.cursor()
        RecipientDictionary = {}
        try:
            result = conn.execute("SELECT * FROM Users WHERE Username = '{}'".format(profile_username))
            error = 0
        except:
            error = 1
        for col in result:
            RecipientDictionary = {"ID": col[0], "Username": col[1], "PORT": col[2], "IP": col[3], "LOCATION": col[4],
                                   "LastLogin": col[5]}
            # print (RecipientDictionary)
        conn.commit()
        conn.close()
        return RecipientDictionary


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

    def AddtoProfileDatabase(self,user,fullname=None, position=None, description=None, location=None, picture=None,encryption=None,decryptionKey=None):
        conn = sqlite3.connect('Users.db')  # connect to the database
        if(encryption == None):
            encryption = 0;
        try:
            conn.execute("CREATE TABLE UserProfiles (ID INTEGER PRIMARY KEY,UserName TEXT NOT NULL, FullName TEXT, Position TEXT ,Description TEXT,Location TEXT, Picture TEXT, Encryption INTEGER NOT NULL, DecryptionKey TEXT);")
            conn.commit()
        except sqlite3.OperationalError:
            check = self.CheckIfRowExists(user)
            if(check):
                conn.execute("""UPDATE UserProfiles  SET UserName = ?, FullName = ?, Position = ?, Description = ?, Location =?, Picture = ?, Encryption= ?, DecryptionKey=? WHERE UserName = ?""",(user,user,fullname,position,description,location,picture,encryption,decryptionKey))
                print("Profile UPDATED")
                conn.commit()
                conn.close()
            else:
                conn.execute("INSERT INTO UserProfiles VALUES (:ID,:UserName,:FullName,:Position,:Description,:Location,:Picture,:Encryption,:DecryptionKey)",
                            {'ID': None, 'UserName': user, 'FullName': fullname, 'Position': position,'Description': description,'Location':location,'Picture': picture,'Encryption': encryption,'DecryptionKey': decryptionKey})
                conn.commit()
                conn.close()
    def CheckIfRowExists(self,user):

        conn = sqlite3.connect('Users.db')
        cursor = conn.execute("SELECT rowid FROM  UserProfiles WHERE UserName = '{}'".format(user))
        data = cursor.fetchall()
        if (len(data)== 0):
            return 0
        else:
            return 1
        # if(check):
        #     "(UPDATE VALUES (:ID,:UserName,:FullName,:Position,:Description,:Location,:Picture,:Encryption,:DecryptionKey)",{})
        # else:
        #     "(INSERT INTO VALUES,{'user':user'ID': None, 'UserName': user, 'FullName': fullname, 'Position': position, 'Description': description, 'Location': location,'Picture': picture,"Encryption":encryption,'DecryptionKey': decryptionKey})
        conn.close()

    def FindMessages(self,UserName):
        conn = sqlite3.connect('Users.db')
        c= conn.cursor()
        MessagesList = []
        CurrentUser = cherrypy.session.get('username')
        print(CurrentUser)
        try:
            #result = conn.execute("SELECT Sender,Receiver,Message FROM Messages WHERE Sender = CurrentUser OR Receiver = {}".format(UserName))
            result = conn.execute("SELECT ID, Sender, Receiver, Message,TimeStamp FROM Messages WHERE (Sender = '{}' AND Receiver ='{}') OR (Sender = '{}' AND Receiver = '{}')".format(CurrentUser,UserName,UserName,CurrentUser))
            for row in result:
                info = {
                    "ID": row[0],
                    "Sender" : row[1],
                    "Receiver" :row[2],
                    "Message" : row[3],
                    "TimeStamp": row[4],
                }
                MessagesList.append(info)
                #print(MessagesList)
        except sqlite3.OperationalError:
            print("exception catached RetrieveData for online Messages display")
        except:
            print("table is not there")
        #print(MessagesList)
        return MessagesList


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
        #print(UsersList)
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
        for row in result:
            RecipientDictionary = {"ID": row[0], "Username": row[1], "PORT": row[2], "IP": row[3], "LOCATION": row[4], "LastLogin": row[5]}

            # print (RecipientDictionary)
        conn.commit()
        conn.close()
        return RecipientDictionary
            #----------------------------------------------------------------------------DATABASE FUNCTIONS END------------------------------------------------------------------#
            #----------------------------------------------------------------------------APIs WRITTEN FROM SCRATCH--------------------------------------------------------------#


    def RetrieveUserProfile(self,profile_username):
        conn = sqlite3.connect('Users.db')
        c = conn.cursor()
        RecipientDictionary = {}
        try:
            result = conn.execute("SELECT * FROM UserProfiles WHERE UserName = '{}'".format(profile_username))
            error = 0
        except:
            error = 1
        for col in result:
            RecipientDictionary = {"ID": col[0], "UserName": col[1], "FullName": col[2], "Position": col[3], "Description": col[4], "Location": col[5],"Picture": col[6],"Encryption": col[7],"DecryptionKey": col[8]}

        #print (RecipientDictionary)
        conn.commit()
        conn.close()
        return RecipientDictionary

    #This is the ping api the returns 0
    @cherrypy.expose
    def ping(self,sender=None):
        print("{} is checking ping API ".format(sender))
        return '0'
    #This is the listAPI that returns the list of the APIs
    @cherrypy.expose
    def listAPI(self):
        output_dict = { "Available APIs":  "/listAPI:/ping[sender]","/recieveMessage":"[sender][destination][message][stamp][markdown(opt)][encoding(opt)][encryption(opt)][hashing(opt)]","/getProfile":"[profile_username][sender]","/receiveFile":"[sender][destination][file][filename][content_type][stamp][encryption][hashing][hash][decryptionKey]" }
        data = json.dumps(output_dict).replace('"','')
        return data

#----------------------------------------------------------------------------API section finish----------------------------------------------------------------------#

def runMainApp():


    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)
    cherrypy.tree.mount(MainApp(), "/")

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,
                            'server.socket_port': listen_port,
                            'engine.autoreload.on': True,
                            })

    print ("=========================")
    print ("University of Auckland")
    print ("COMPSYS302 - Software Design Application")
    print ("========================================")

    # Start the web server
    cherrypy.engine.start()

    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()

#Run the function to start everything
runMainApp()
