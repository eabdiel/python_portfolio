"""
Modified version of github.com/petemc89's craXel's 'MS password remove' tool.
Arguments were replaced with tkinter UI with bot-like functionality
Program has text based input with results being sent out to text area
Automatically identifies list.txt files and macro content
--this standalone version is part of the dev_bot_toolkit |
"""

import abc
import binascii
import os
import shutil
import uuid
import zipfile
from tkinter import Tk, Entry, Button, Text, Scrollbar

from lxml import etree

# Initial Variables
APP_NAME = 'MS_Unlocked'

APP_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
APP_SAVE_DIR = os.path.join(APP_ROOT_DIR, 'unlocked')
APP_TEMP_DIR = os.path.join(APP_ROOT_DIR, 'temp')

MICROSOFT_EXCEL = 'MicrosoftExcel'
MICROSOFT_WORD = 'MicrosoftWord'
MICROSOFT_POWERPOINT = 'MicrosoftPowerpoint'

# Supported extensions dictionary
SUPPORTED_EXTENSIONS = {
    '.xlsx': MICROSOFT_EXCEL,
    '.xlsm': MICROSOFT_EXCEL,
    '.docx': MICROSOFT_WORD,
    '.docm': MICROSOFT_WORD,
    '.pptx': MICROSOFT_POWERPOINT,
    '.pptm': MICROSOFT_POWERPOINT
}


class FileInfo():
    """
    Class that encapsulates information related to a specified filepath.
    """

    def __init__(self, filepath):
        self.full_name = filepath
        self.name = os.path.basename(filepath)
        self.directory, self.extension = os.path.splitext(filepath)


class MicrosoftOfficeFile(metaclass=abc.ABCMeta):
    """
    Base class containing common logic for unlocking Microsoft Office XML
    based applications.
    """

    def __init__(self, filepath, xml_root_dir_name):
        self._file = FileInfo(filepath)

        # Creates a universally unique path in the app temp directory
        self._temp_processing_dir = os.path.join(APP_TEMP_DIR, str(uuid.uuid4()))

        # The root directory where XML files are stored when unpackaged
        self._xml_root_dir = os.path.join(self._temp_processing_dir, xml_root_dir_name)

        self._vba_filepath = os.path.join(self._xml_root_dir, 'vbaProject.bin')

    def unlock(self):
        """
        Unlocks the specified file according to arguments passed in by the user.
        """
        self._unpackage()

        self._remove_application_specific_protection()
        # # If the vba argument is True, unlock vba protection
        # #
        # if self._args.vba:
        self._remove_vba_protection()

        self._repackage()
        # # if the --debug argument is not true, cleanup
        # comment cleanup if not using args to see temp folder content
        # if not self._args.debug:
        self._cleanup()

        print('Completed unlocking file!')

    def _unpackage(self):
        """
        Treats the target file as if it were a ZIP file and extracts the
        underlying XMLs.
        """
        zipfile.ZipFile(self._file.full_name, 'r').extractall(self._temp_processing_dir)

        print('File unpacked...')

    def _repackage(self):
        """
        Takes the unpackaged XML files and repackages them into a ZIP file
        with the original file's extension restored. This makes the newly
        repackaged file openable by the original application.
        """
        file_suffix = f'_{APP_NAME}{self._file.extension}'
        filename = self._file.name.replace(self._file.extension, file_suffix)
        unlocked_filepath = os.path.join(APP_SAVE_DIR, filename)

        filepaths = self._get_file_listing(self._temp_processing_dir)
        with zipfile.ZipFile(unlocked_filepath, 'w') as repackaged_zip:
            for filepath in filepaths:
                rel_filepath = filepath.replace(self._temp_processing_dir, '')
                repackaged_zip.write(filepath, arcname=rel_filepath)

        print('File repackaged...')

    def _cleanup(self):
        """
        Recursively deletes all files in the temporary processing directory.
        """
        shutil.rmtree(self._temp_processing_dir)

        print('Cleaning up temporary files...')

    def _get_file_listing(self, directory):
        """
        Retrieves a list of files from the specified directory.
        """
        filepaths = []
        for root, folder, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                filepaths.append(filepath)

        return filepaths

    def _remove_protection_element(self, xml_filepath, tag_names_to_remove):
        """
        Reads through the XML in the specified filepath and removes the
        elements containing the specified tag names.
        """
        tree = etree.parse(xml_filepath)
        root = tree.getroot()

        for element in root.iter():
            for tag_name in tag_names_to_remove:
                if tag_name in element.tag:
                    root.remove(element)

        tree.write(xml_filepath, encoding='UTF-8', xml_declaration=True)

    def _remove_vba_protection(self):
        """
        Reads the file's underlying vbaProject.bin file in HEX form,
        replacing the string responsible for protecting the file with a
        password.
        """
        if os.path.isfile(self._vba_filepath):
            with open(self._vba_filepath, 'rb') as f:
                content = f.read()

            hex_content = binascii.hexlify(content)

            unlocked_hex = hex_content.replace(b'445042', b'445078')

            unlocked_bin = binascii.unhexlify(unlocked_hex)

            with open(self._vba_filepath, 'wb') as f:
                f.write(unlocked_bin)

            print('VBA protection removed...')

    @abc.abstractmethod
    def _remove_application_specific_protection(self):
        """
        Removes protection specific to the target application. Abstract method
        that requires implementation in all child classes.
        """


class MicrosoftExcel(MicrosoftOfficeFile):
    """
    Class encapsulating all specifc fields and logic required for the unlocking
    of Microsoft Excel XML based files.
    """

    def __init__(self, locked_filepath):
        super().__init__(locked_filepath, 'xl')
        self._workbook_xml_filepath = os.path.join(self._xml_root_dir, 'workbook.xml')
        self._worksheet_xml_dir = os.path.join(self._xml_root_dir, 'worksheets')
        self._workbook_tag_names = ['fileSharing', 'workbookProtection']
        self._worksheet_tag_names = ['sheetProtection']

    def _remove_application_specific_protection(self):
        ##Coming soon - need to replace args with text based commands for bot
        # #if the workbook only argument is passed
        # if self._args.workbook:
        #     self._remove_workbook_protection()
        # #if the worksheet only argument is passed
        # elif self._args.worksheet:
        #    self._remove_worksheet_protection()
        # #if no arguments are passed
        # else:
        self._remove_workbook_protection()
        self._remove_worksheet_protection()

    def _remove_workbook_protection(self):
        """
        Takes the workbook XML and removes the protections within.
        """
        self._remove_protection_element(self._workbook_xml_filepath, self._workbook_tag_names)

        print('Workbook protection removed...')

    def _remove_worksheet_protection(self):
        """
        Iterates through the directory holding the worksheet XMLs and removes
        the protections in each file.
        """
        worksheet_xml_filepaths = self._get_file_listing(self._worksheet_xml_dir)

        for xml_filepath in worksheet_xml_filepaths:
            self._remove_protection_element(xml_filepath, self._worksheet_tag_names)

        print('Worksheet protection removed...')


class MicrosoftWord(MicrosoftOfficeFile):
    """
    Class encapsulating all specifc fields and logic required for the unlocking
    of Microsoft Word XML based files.
    """

    def __init__(self, locked_filepath):
        super().__init__(locked_filepath, 'word')
        self._document_xml_filepath = os.path.join(self._xml_root_dir, 'settings.xml')
        self._document_tag_names = ['writeProtection', 'documentProtection']

    def _remove_application_specific_protection(self):
        self._remove_protection_element(self._document_xml_filepath, self._document_tag_names)

        print('Document protection removed...')


class MicrosoftPowerpoint(MicrosoftOfficeFile):
    """
    Class encapsulating all specifc fields and logic required for the unlocking
    of Microsoft Powerpoint XML based files.
    """

    def __init__(self, locked_filepath):
        super().__init__(locked_filepath, 'ppt')
        self._presentation_xml_filepath = os.path.join(self._xml_root_dir, 'presentation.xml')
        self._presentation_tag_names = ['modifyVerifier']

    def _remove_application_specific_protection(self):
        self._remove_protection_element(self._presentation_xml_filepath, self._presentation_tag_names)
        print('Presentation protection removed...')


class Terminal:
    def __init__(self, window):

        window.title('Unlock MS Files')
        window.geometry('400x500')
        window.resizable(0, 0)

        self.message_position = 1.5

        self.message_window = Entry(window, width=30, font=('Times', 12))
        self.message_window.bind('<Return>', self.submit_update)
        self.message_window.place(x=128, y=400, height=88, width=260)

        self.chat_window = Text(window, bd=3, relief="flat", font=("Times", 10), undo=True, wrap="word")
        self.chat_window.place(x=6, y=6, height=385, width=370)
        self.overscroll = Scrollbar(window, command=self.chat_window.yview)
        self.overscroll.place(x=375, y=5, height=385)

        self.chat_window["yscrollcommand"] = self.overscroll.set

        self.send_button = Button(window, text='Unlock->', fg='white', bg='grey', width=12, height=5,
                                  font=('Times', 12),
                                  relief='flat', command=self.submit_update)
        self.send_button.place(x=6, y=400, height=88)

        # Instructions Here
        self.update_text_screen('Steps:\n')
        self.update_text_screen('1. Enter the path/filename.xlsx or path/filelist.txt\n')
        self.update_text_screen('2. Press Unlock and see unlocked folder in root directory.\n')

    def update_text_screen(self, message):
        self.message_position += 1.5
        print(self.message_position)
        self.message_window.delete(0, 'end')
        self.chat_window.config(state='normal')
        self.chat_window.insert(self.message_position, message)
        self.chat_window.see('end')
        self.chat_window.config(state='disabled')

    def submit_update(self, event=None):
        """
        Creates the directory structure if it doesn't already exist.
        """
        if not os.path.exists(APP_SAVE_DIR):
            os.mkdir(APP_SAVE_DIR)

        if not os.path.exists(APP_TEMP_DIR):
            os.mkdir(APP_TEMP_DIR)

        filepath = [self.message_window.get()]
        filepath_check = filepath
        message = self.message_window.get()
        message = f'You: {message} \n'
        reply = 'Bot: MS Unlocker started\n'

        self.update_text_screen(message)
        self.update_text_screen(reply)
        for fp in filepath_check:
            ext = os.path.splitext(fp)[-1].lower()
            if ext == '.txt':
                reply = 'Bot: .txt submitted - assuming List mode...\n'
                self.update_text_screen(reply)
                filepaths = [line.rstrip() for line in open(fp, 'r')]

                reply = f'Bot: {len(filepaths)} files detected\n'
                self.update_text_screen(reply)
            else:
                filepaths = filepath

        files_unlocked = 0
        for locked_filepath in filepaths:
            reply = f'Bot: Checking file {locked_filepath}...\n'
            self.update_text_screen(reply)

            if os.path.isfile(locked_filepath):
                file_info = FileInfo(locked_filepath)

                # Checks the extension of the file against the dictionary of
                # supported applications, returning the application name.
                try:
                    detected_application = SUPPORTED_EXTENSIONS[file_info.extension]
                except:
                    detected_application = 'Bot: unsupported file type\n'

                # Uses the deteted application to create the correct instance.
                if detected_application == MICROSOFT_EXCEL:
                    cxl = MicrosoftExcel(locked_filepath)
                elif detected_application == MICROSOFT_WORD:
                    cxl = MicrosoftWord(locked_filepath)
                elif detected_application == MICROSOFT_POWERPOINT:
                    cxl = MicrosoftPowerpoint(locked_filepath)
                elif file_info.extension == '.txt':
                    reply = 'Bot: File rejected. Did you mean to upload a list.txt?\n'
                    self.update_text_screen(reply)
                    break
                else:
                    reply = 'Bot: File rejected. Unsupported file extension.\n'
                    self.update_text_screen(reply)
                    break

                reply = 'Bot: File accepted...\n'
                self.update_text_screen(reply)

                try:
                    cxl.unlock()
                    reply = 'Completed unlocking file!\n'
                    self.update_text_screen(reply)

                    files_unlocked += 1
                except Exception:
                    reply = f'Bot: An error occured while unlocking {locked_filepath}\n'
                    self.update_text_screen(reply)
            else:
                reply = '\nBot: File not found...'
                self.update_text_screen(reply)

            if locked_filepath.endswith('.xlsm'):
                reply = 'Bot: Macro identified...\n'
                self.update_text_screen(reply)
                reply = 'When opening these types of files in MS-Office:\n'
                self.update_text_screen(reply)
                reply = '1. If popup comes up - select Yes\n'
                self.update_text_screen(reply)
                reply = '2. Click Enable Macros if prompted\n'
                self.update_text_screen(reply)
                reply = '3. Go to Dev tab-Visual Basic\n'
                self.update_text_screen(reply)
                reply = '4. On new screen click Tools\n'
                self.update_text_screen(reply)
                reply = '5. Select VBA Project Properties\n'
                self.update_text_screen(reply)
                reply = '6. Enter a new password and save\n'
                self.update_text_screen(reply)
                reply = '7. You should be able to access the macro code now\n'
                self.update_text_screen(reply)

        reply = f'\nBot: Summary: {files_unlocked}/{len(filepaths)} files unlocked\n'
        self.update_text_screen(reply)
        reply = '\nBot: MS Unlocker finished'
        self.update_text_screen(reply)


root = Tk()
Terminal(root)
root.mainloop()
