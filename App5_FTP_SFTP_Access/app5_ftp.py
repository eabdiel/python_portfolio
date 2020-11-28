# testing ftplib to connect to an ftp server -
# in this public file I took out server, user and password for obvious reasons - just replace with the valid strings
import os
from ftplib import FTP


def ftpDownloader(filename, host="ftp.server.com", user="userid", passwd="mypassword"):
    ftp = FTP(host)
    ftp.login(user, passwd)
    ftp.cwd("Data")
    os.chdir("C:\\CS")
    with open(filename, 'wb') as file:
        ftp.retrbinary('RETR %s' % filename, file.write)


ftpDownloader("filetodownload.zip")
