# **************************************************************************
#   Library makes easy go for connecting hosts using SSH with more reliable. 
#
#
#   Although we have paramiko with us, we are facing hard time to connect
#   to the host when server response get delayed. And also hard to compose
#   the code by finding the options available in paramiko. So comes this 
#   module, which makes easy go to deal with paramiko to connect hosts. 
#
#   Author: Karthickraja R
# **************************************************************************

import platform
import os
import sys
import subprocess
import time
import csv
import paramiko

class ConnectSSH:
    def __init__(self, credentials, tcptimeout = 60, bannertimeout = 30, authtimeout = 30, numofattempt = 2, responsesleeptime = 2, verbose = False):
        self.sleepTimeForServerPing = 3
        self.sleepTimeForServerResponse = responsesleeptime
        self.tcptimeout = tcptimeout
        self.sshClientConnection = False
        self.lastStatusMessage = 'Yet to connect...'
        self.PythonVersion3 = sys.version_info.major >= 3

        if 'hostname' not in credentials or 'username' not in credentials:
            self.updateStatusMessage("hostname or username is not found", verbose)
            return

        self.hostName = credentials['hostname']
        hostName = credentials['hostname']
        userName = credentials['username']
        if 'hostport' not in credentials:
            hostPort = 22
        else:
            hostPort = credentials['hostport']

        #Ping test
        serverStatus = self.pingServer(hostName, verbose)
        if not serverStatus:
            return

        self.updateStatusMessage("Trying to connect the host: "+ hostName, verbose)
        self.sshClientConnection = paramiko.SSHClient()
        self.sshClientConnection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshClientConnection.known_hosts = None

        counter = 0
        while counter < numofattempt:
            try:
                if 'password' in credentials:
                    self.updateStatusMessage("Password authentication method triggered to connect host: "+ hostName, verbose)
                    passWord = credentials['password']

                    self.sshClientConnection.connect(
                        hostname = hostName, 
                        port = hostPort,
                        username = userName, 
                        password = passWord,
                        timeout = tcptimeout,
                        banner_timeout = bannertimeout,
                        auth_timeout = authtimeout,
                        allow_agent = False,
                        look_for_keys = False
                    )

                elif 'passkey' in credentials:
                    self.updateStatusMessage("Pass key authentication method triggered to connect host: "+ hostName, verbose)
                    passKeyPath = credentials['passkey']
                    passKeyPath = os.path.expanduser(passKeyPath)
                    passKey = paramiko.RSAKey.from_private_key_file(passKeyPath)

                    self.sshClientConnection.load_system_host_keys()
                    self.sshClientConnection.connect(
                        hostname = hostName, 
                        port = hostPort,
                        username = userName, 
                        pkey = passKey,
                        timeout = tcptimeout,
                        banner_timeout = bannertimeout,
                        auth_timeout = authtimeout,
                        look_for_keys = False
                    )

                elif platform.system().lower() == 'linux' or platform.system().lower() == 'sunos':
                    self.updateStatusMessage("Trying automatic pass key authentication method triggered to connect host: "+ hostName, verbose)
                    passKeyPath = os.path.expanduser('~/.ssh/id_rsa')
                    passKey = paramiko.RSAKey.from_private_key_file(passKeyPath)

                    self.sshClientConnection.load_system_host_keys()
                    self.sshClientConnection.connect(
                        hostname = hostName, 
                        port = hostPort,
                        username = userName, 
                        pkey = passKey,
                        timeout = tcptimeout,
                        banner_timeout = bannertimeout,
                        auth_timeout = authtimeout,
                        look_for_keys = False
                    )

                else:
                    self.updateStatusMessage("No matching method found to authenticate the host: "+ hostName, verbose)
                    self.sshClientConnection.close()
                    self.sshClientConnection = False
                    return
                
                self.updateStatusMessage("Connected to host: "+ hostName, verbose)
                return

            except paramiko.ssh_exception.AuthenticationException:
                counter += 1
                self.updateStatusMessage("Authentication problem", verbose)
                self.sshClientConnection.close()
                self.sshClientConnection = False
                return
                
            except Exception:
                unknownException = str(sys.exc_info()[1])
                counter += 1
                self.sshClientConnection.close()
                self.sshClientConnection = False
                self.updateStatusMessage("Error occured: "+ unknownException, verbose)
                return


        #If connection not established, then make it as false
        self.sshClientConnection.close()
        self.sshClientConnection = False
        pass

    def closeSSHConnection(self, verbose = False):
        if self.sshClientConnection:
            self.updateStatusMessage("SSH Connection closed for the host: "+ self.hostName, verbose)
            self.sshClientConnection.close()
        pass

    def updateStatusMessage(self, message, verbose = False):
        if verbose:
            if platform.system().lower() == 'linux' or platform.system().lower() == 'sunos':
                print("\033[93m VERBOSE: " + message + " \033[0m")
            else:
                print("VERBOSE: " + message)
        self.lastStatusMessage = message
        pass

    def pingServer(self, hostName, verbose = False):
        pingResult = False

        #Try to ping server...
        #We will try 3 attempts to ping server. If it failed on all 3 attempts, then we fix server is offline.
        for n in range(0, 3):
            self.updateStatusMessage("Pinging the host: " + hostName, verbose)
            try:
                output = subprocess.check_output("ping -{} 1 {}".format('n' if platform.system().lower()=="windows" else 'c', hostName), shell=True)
            except Exception:
                unknownException = str(sys.exc_info()[1])
                self.updateStatusMessage(str(n + 1) + " attempt of ping test failed for the host: " + hostName, verbose)
                self.updateStatusMessage("Error occured: "+ unknownException, verbose)
                time.sleep(self.sleepTimeForServerPing)
                continue
            else:
                #If our ping command executed without facing any error, then its pingable!!!
                pingResult = True
                break

        if pingResult:
            self.updateStatusMessage("Ping test success for the host: "+ hostName, verbose)            
            return True
        else:
            self.updateStatusMessage("Ping test failed for the host: "+ hostName, verbose)            
            return False
        pass

    def getSshStream(self, verbose = False):
        if self.sshClientConnection == False:
            return False

        try:
            getSshStream = self.sshClientConnection.invoke_shell()

            #Give 3 attempts to make sure the stream is ready
            for n in range(0, 3):
                time.sleep(self.sleepTimeForServerResponse)

                if getSshStream.recv_ready():
                    self.updateStatusMessage("SSH Stream has been created", verbose)
                    stdout, stderr = self.executeCommandOnSshStream(getSshStream, "stty -echo\n")
                    #Returning the successful result
                    return getSshStream

            self.updateStatusMessage("No response from the server for create SSH stream", verbose)
            return False

        except Exception:
            unknownException = str(sys.exc_info()[1])
            self.updateStatusMessage("No response from the server for create SSH stream", verbose)
            self.updateStatusMessage("Error occured: "+ unknownException, verbose)
            return False

    def readSshStream(self, sshStream, bufferSize = 4048, verbose = False):
        stdout = ''
        stderr = ''
        try:
            self.updateStatusMessage("Reading the ssh stream...", verbose)
            time.sleep(self.sleepTimeForServerResponse)

            #Try 3 attempts to verify the ready status of stdin
            for n in range(0, 3):
                if sshStream.recv_ready():
                    stdout += self.receiveDataFromSshStream(sshStream, 'stdout', bufferSize)
                    break
                else:
                    time.sleep(self.sleepTimeForServerResponse)
            
            #Try 3 attempts to verify the ready status of stderr
            for n in range(0, 3):
                if sshStream.recv_stderr_ready():
                    stdout += self.receiveDataFromSshStream(sshStream, 'stderr', bufferSize)
                    break
                else:
                    time.sleep(self.sleepTimeForServerResponse)

            return stdout, stderr

        except Exception:
            unknownException = str(sys.exc_info()[1])
            self.updateStatusMessage("Failed to read SSH stream", verbose)
            return stdout, stderr

    def receiveDataFromSshStream(self, sshStream, readType = 'stdout', bufferSize = 4048):
        outputText = ''
        if readType == 'stdout':
            for n in range(0, 2):
                outputText = sshStream.recv(bufferSize)
                if outputText:
                    break
                else:
                    time.sleep(self.sleepTimeForServerResponse)
        elif readType == 'stderr':
            for n in range(0, 2):
                outputText = sshStream.recv_stderr(bufferSize)
                if outputText:
                    break
                else:
                    time.sleep(self.sleepTimeForServerResponse)

        if not self.PythonVersion3:
            #If its python 2.x
            return outputText
        else:
            #If its python 3.x
            return outputText.decode('ascii')

    def executeCommandOnSshStream(self, sshStream, command, verbose = False):
        stdout = ''
        stderr = ''
        if self.sshClientConnection == False:
            self.updateStatusMessage("Invalid ssh connection. Can't execute command", verbose)
            return stdout, stderr

        try:
            #Try 2 attempts to send command
            for n in range(0, 2):

                #Try 2 attempts to get to know the stream is ready for sending commands
                for n in range(0, 2):
                    if sshStream.send_ready():
                        break
                    else:
                        time.sleep(self.sleepTimeForServerResponse)


                self.updateStatusMessage("Injecting the command for " + str(n + 1) + " time on ssh stream", verbose)
                sshStream.send(command + '\r')

                stdout, stderr = self.readSshStream(sshStream, 4048, verbose)
                #Returning the successful result back
                return stdout, stderr

            #We failed to execute command on 2 attempts
            self.updateStatusMessage("Failed to execute the command", verbose)
            return stdout, stderr

        except Exception:
            unknownException = str(sys.exc_info()[1])
            self.updateStatusMessage("Problem executing the command on the stream", verbose)
            self.updateStatusMessage("Error occured: "+ unknownException, verbose)
            return False

    def executeCommandOnSshStreamWithFullOutput(self, sshStream, command, verbose = False):
        fullStdout = []
        #First execution of the command.
        stdout, stderr = self.executeCommandOnSshStream(sshStream, command, verbose)
        if stdout == False or stdout == '':
            return stdout, stderr

        stdout = stdout.split('\r\n')
        lastLine = stdout[-1]

        while '--More--' in lastLine:
            self.updateStatusMessage("Collecting more data as we recieved --More-- on last line", verbose)
            #Delete the last line that is having "--More--"
            stdout.pop()
            fullStdout += stdout

            stdout, stderr = self.executeCommandOnSshStream(sshStream, " ", verbose)
            stdout = stdout.split('\r\n')
            lastLine = stdout[-1]

        fullStdout += stdout
        fullStdout = '\r\n'.join(fullStdout)

        #We are pushing only last stderr.
        return fullStdout, stderr
    
    def executeCommand(self, command, verbose = False):
        stdoutFullString = ''
        stderrFullString = ''

        if self.sshClientConnection == False:
            self.updateStatusMessage("Invalid ssh connection. Can't execute command", verbose)
            return stdoutFullString, stderrFullString

        errorFlag = True
        #Try 2 attempts to execute the command
        for n in range(0, 2):
            self.updateStatusMessage("Trying to execute the command for " + str(n + 1) + " time", verbose)
            try:
                stdin, stdout, stderr = self.sshClientConnection.exec_command(command, timeout = self.tcptimeout, get_pty = False)
                #We assume that we don't inject any input, so closing the stdin
                stdin.close()
                errorFlag = False
                break
            except Exception:
                unknownException = str(sys.exc_info()[1])
                self.updateStatusMessage("Error occured: "+ unknownException, verbose)
                time.sleep(self.sleepTimeForServerResponse)
                pass
            
        if errorFlag:
            self.updateStatusMessage("Failed to execute the command on the host", verbose)
            return stdoutFullString, stderrFullString
        
        self.updateStatusMessage("Please wait...", verbose)
        #Wait for the exit status to be TRUE to retrieve the stdout.
        while not stdout.channel.exit_status_ready():
            time.sleep(self.sleepTimeForServerResponse)
            pass
        
        self.updateStatusMessage("Command execution has been finished", verbose)
        stdoutFullString = stdout.readlines()
        if stdoutFullString:
            stdoutFullString = ''.join(stdoutFullString)
        else:
            stdoutFullString = ''

        stderrFullString = stderr.readlines()
        if stderrFullString:
            stderrFullString = ''.join(stderrFullString)
        else:
            stderrFullString = ''

        return stdoutFullString, stderrFullString

