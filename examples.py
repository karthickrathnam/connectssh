from SSHLib.ConnectSSH import ConnectSSH

hostName = 'hostname or ip'
userName = 'your host username'
passWord = 'your host password'
passKey = '~/.ssh/id_rsa'

#With password authentication
credentials = {
    'hostname' : hostName,
    'username' : userName,
    'password' : passWord
}

'''
#Without any password authentication. Trust should be made between two hosts
credentials = {
    'hostname' : hostName,
    'username' : userName
}

#Authentication with passkey
credentials = {
    'hostname' : hostName,
    'username' : userName,
    'passkey'  : passKey
}
'''

#Create SSH connection
# parameter options: tcptimeout, bannertimeout, authtimeout, numofattempt(number of attempt to try), responsesleeptime
liveConnection = ConnectSSH(credentials, tcptimeout = 30, bannertimeout = 30, authtimeout = 30, numofattempt = 2, responsesleeptime = 1, verbose = True) 

#Example 1: List directory of remote server
stdout, stderr = liveConnection.executeCommand('ls -la', verbose = True)
print("Stderr: "+ stderr)
print("Stdout: "+ stdout)



#Example 2: Change new password for the current logged on user
#Create new shell stream on the ssh connection
sshStream = liveConnection.getSshStream(verbose = True)

if not sshStream:
    exit()

newPassword = "your new password"
stdout, stderr = liveConnection.executeCommandOnSshStreamWithFullOutput(sshStream, 'sudo passwd', verbose = True)
print("Stderr: "+ stderr)
print("Stdout: "+ stdout)

while True:
    if "New Password" in stdout:
        stdout, stderr = liveConnection.executeCommandOnSshStreamWithFullOutput(sshStream, newPassword, verbose = True)
        print("Stderr: "+ stderr)
        print("Stdout: "+ stdout)
    elif "Re-enter new Password" in stdout:
        stdout, stderr = liveConnection.executeCommandOnSshStreamWithFullOutput(sshStream, newPassword, verbose = True)
        print("Stderr: "+ stderr)
        print("Stdout: "+ stdout)
    elif "Password:" in stdout:
        stdout, stderr = liveConnection.executeCommandOnSshStreamWithFullOutput(sshStream, passWord, verbose = True)
        print("Stderr: "+ stderr)
        print("Stdout: "+ stdout)
    elif "successfully changed" in stdout:
        print("Password changed successfully")
        break
    else:
        print("We didn't receive expected string from the shell. So failed to change password.")
        break


#you can also read the shell stream manually
stdout, stderr = liveConnection.readSshStream(sshStream, bufferSize = 4048, verbose = True)

#Close the connection
liveConnection.closeSSHConnection(verbose = True)