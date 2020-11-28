# My take on the RPA Challenge -
#       rpa.download doesn't work behind a proxy so I added an optional
#       'requests' code in case the bot needs to 'download' something while behind a proxy


import time as time

import pandas as pd
# --- Modules
import rpa as r

# --- Start of program
r.init()
# initialize TagUI - the first time you run rpa.init() the instruction will install TagUI on your AppData folder
#                 - if you are behind a proxy, the install might error out
#                 - see TagUI documentation for instructions on how to install it offline from a copy
#                 - see https://github.com/tebelorg/RPA-Python/issues/94  for details
#                 - after the initial installation you don't need to perform the setup


# rpa.wait is a timeout - time.sleep pauses python
time.sleep(5)

r.url('http://rpachallenge.com')

# rpa.download() is used here but you can also do a click() on the button
r.download('http://rpachallenge.com/assets/downloadFiles/challenge.xlsx')

# --- if you are behind a proxy - you can't use the rpa.download command; instead use requests.get
# proxies = {"http":"yourproxy.com/:port"} #proxy* see your internet options to find out the url
# fileurl = 'http://rpachallenge.com/assets/downloadFiles/challenge.xlsx'
# req = requests.get(fileurl, proxies=proxies)  #this gets the source
# output = open('challenge.xlsx', 'wb') #creates blank file
# output.write(req.content) #populates the source into the file
# output.close()  #closes and saves the file
# ---- at this point the file should be ready to be read

# if neither the download or the requests.get work - using rpa.click() to click on the css object to download works
# but takes extra steps


# load and prepare all data to string with pandas
df = pd.read_excel('challenge.xlsx')
df['Phone Number'] = df['Phone Number'].astype(str)

# timer starts after running this step
r.click('//*[text()="Start"]')

# iterate and populate each text box on the page
for i in range(len(df.axes[0])):
    r.type('//*[@ng-reflect-name="labelFirstName"]', df['First Name'][i])
    r.type('//*[@ng-reflect-name="labelLastName"]', df['Last Name '][i])
    r.type('//*[@ng-reflect-name="labelCompanyName"]', df['Company Name'][i])
    r.type('//*[@ng-reflect-name="labelRole"]', df['Role in Company'][i])
    r.type('//*[@ng-reflect-name="labelAddress"]', df['Address'][i])
    r.type('//*[@ng-reflect-name="labelEmail"]', df['Email'][i])
    r.type('//*[@ng-reflect-name="labelPhone"]', df['Phone Number'][i])
    r.click('//*[@value="Submit"]')

# page as identifier means the webpage
r.snap('page', 'score.png')
r.wait(10)
r.close()
