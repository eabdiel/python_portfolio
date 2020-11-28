# ----Modules
import json
from difflib import get_close_matches

# -----Data variables
data = json.load(open("data.json"))  # data.json has the word list in the format of a dictionary;


# download from my git


# ---Subroutines/Functions
def translate(w):  # takes a single parameter
    w = w.lower()  # makes it lower case
    if w in data:  # if word is a key in data
        return data[w]  # return value of key
    elif w.title() in data:  # elseif capitalize the first letter with the tittle command and check again
        return data[w.title()]
    elif w.upper() in data:  # else check in full caps in case user enters words like USA or NATO
        return data[w.upper()]
    elif len(get_close_matches(w, data.keys())) > 0:  # IF nothing is found yet, len get_close_matches from current key
        # if a close match was found, get_close.. will be more than 0
        yn = input("Did you mean %s instead? Enter Y if yes, or N if no: " % get_close_matches(w, data.keys())[0])

        if yn == "Y":
            return data[get_close_matches(w, data.keys())[0]]  # if it is, return it
        elif yn == "N":
            return "The word doesn't exist. Please double check it."  # if not, then return that the word doesnt exist
        else:
            return "We didn't understand your entry."
    else:
        return "The word doesn't exist. Please double check it."


# ----Start of program
word = input("Enter word: ")
output = translate(word)
if type(output) == list:
    for item in output:
        print(item)
else:
    print(output)
