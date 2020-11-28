import pysftp as sftp

# i'm using a file to store the password, but a hardcoded string works as well if needed
with open('pass', 'r') as file:
    myPassword = file.read().replace('/n', '')

    myHostname = 'sftp-server'
    myUsername = 'username'

cnopts = sftp.CnOpts(knownhosts='known_hosts')  # known_hosts is a file, usually stored in the ftp /ect/ssh/
with sftp.Connection(host=myHostname,
                     username=myUsername,
                     password=myPassword,
                     cnopts=cnopts) as sftp:
    print("Connection successful..")
    sftp.cwd("path/to/find")
    directory_structure = sftp.listdir_attr()
    for attr in directory_structure:
        print(attr.filename, attr)
