# MapFind.py - Launches a map in the browser using an address from the
# command line or clipboard.

# --- Modules
import pyperclip
import sys
import webbrowser

# --- Start of program
if len(sys.argv) > 1:  # check to see if the command line has extra inputs
    address = ' '.join(sys.argv[1:])  # Get input from command line.
else:
    address = pyperclip.paste()  # if no parameter was added to command line, get address from clipboard

webbrowser.open(f"https://www.google.com/maps/place/{address}")

###File notes to run program from batch script
"""To run from windows search task bar - 
 Make a bat file that calls the scripts and accepts an argument | use code below - just save as bat and name it
                                                                  as something relevant (ex. MapFind.bat)
                                                                  then just type the bat file's name on the search box
                                                                  add an address by the name and execute (or copy an
                                                                  address and run it without parameters);
 @py D:\PythonRelated\Projects\MapFind.py %*
 @pause 
"""
