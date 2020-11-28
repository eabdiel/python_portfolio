import json
from difflib import get_close_matches
from random import choice
from tkinter import Tk, Entry, Button, Text, Scrollbar


class Chatbot:
    def __init__(self, window):
        window.title('Thesaurus Bot')
        window.geometry('400x500')
        window.resizable(0, 0)

        self.message_position = 1.5

        self.message_window = Entry(window, width=30, font=('Times', 12))
        self.message_window.bind('<Return>', self.reply_to_you)
        self.message_window.place(x=128, y=400, height=88, width=260)

        self.chat_window = Text(window, bd=3, relief="flat", font=("Times", 10), undo=True, wrap="word")
        self.chat_window.place(x=6, y=6, height=385, width=370)
        self.overscroll = Scrollbar(window, command=self.chat_window.yview)
        self.overscroll.place(x=375, y=5, height=385)

        self.chat_window["yscrollcommand"] = self.overscroll.set

        self.send_button = Button(window, text='Submit', fg='white', bg='grey', width=12, height=5, font=('Times', 12),
                                  relief='flat', command=self.reply_to_you)
        self.send_button.place(x=6, y=400, height=88)

        self.data = json.load(open("data.json"))
        self.error = ["Sorry, I don't know that word", "What did you say?", "The word doesn't exist",
                      "Please double check."]

    def add_chat(self, message):
        self.message_position += 1.5
        print(self.message_position)
        self.message_window.delete(0, 'end')
        self.chat_window.config(state='normal')
        self.chat_window.insert(self.message_position, message)
        self.chat_window.see('end')
        self.chat_window.config(state='disabled')

    def reply_to_you(self, event=None):
        message = self.message_window.get()
        w = message.lower()
        message = f'You: {message} \n'
        if w in self.data:  # if word is a key in data
            reply = f'Bot: {self.data[w][0]} \n'
        elif w.title() in self.data:  # elseif capitalize the first letter with the tittle command and check again
            reply = f'Bot: {self.data[w.title()][0]} \n'
        elif w.upper() in self.data:  # else check in full caps in case user enters words like USA or NATO
            reply = f'Bot: {self.data[w.upper()][0]} \n'
        elif len(get_close_matches(w, self.data.keys())) > 0:
            reply = f'''Bot: Did you mean {get_close_matches(w, self.data.keys())[0]} instead? That one means: \n
            {self.data[get_close_matches(w, self.data.keys())[0]][0]} \n'''
        else:
            reply = f'Bot: {choice(self.error)}\n'
        self.add_chat(message)
        self.add_chat(reply)


root = Tk()
Chatbot(root)
root.mainloop()
