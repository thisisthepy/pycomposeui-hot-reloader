import configparser
import os
import time
from datetime import datetime 

class HotReloader:
    def __init__(self, target_path = ''):
        #initialize the absolute path current repository (it can be customized.)
        if not target_path == '': 
            self.target_path = target_path
        else:
            self.target_path = os.path.abspath(os.getcwd())
        
        #make the class "ConfigParser" to set the config.ini file.
        self.config_file = configparser.ConfigParser()
        #read the file.
        self.check_repos()

    def check_repos(self):
        self.config_file.read(f'{self.target_path}\\config.ini')
        
        CONFIG_VERSION = self.config_file["CONFIG_VERSION"] #Select the section
        if CONFIG_VERSION["last_config"] == 'YYMMDD-hhmmss':#if it is the first time to check
            files = os.listdir(self.target_path)
            for file in files:
                self.config_file.add_section(file)
                tmp_section = self.config_file[file]
                file_titles = file.split('.')
                #Defining the name and extension of files
                if (file_titles[0] is not '') and (len(file_titles) is 2) :
                    file_name, file_ext = file_titles
                elif not '.' in file:
                    file_name = file
                    file_ext = 'Null'
                else:
                    file_name = 'Null'
                    file_ext = file_titles[0]
                #Distinguish between file and Directory
                if os.path.isdir(file):
                    file_type = 'Directory'
                else:
                    file_type = 'File'
                file_last_modified = os.path.getmtime(f'{self.target_path}\\{file}')
                tmp_section['name'] = file_name
                tmp_section['extension'] = file_ext
                tmp_section['last_modified'] = str(file_last_modified)
                tmp_section['type'] = file_type

            CONFIG_VERSION["last_config"] = str(datetime.now()) #set the Key - Value

            with open(f'{self.target_path}\\\config.ini', "w") as f: #save them
                self.config_file.write(f)
        else: #Already initialized config.ini
            files = os.listdir(self.target_path)
            for file in files:
                try:
                    tmp_section = self.config_file[file]
                    #if there is an initialized file on the config.ini
                    saved_last_modified = tmp_section['last_modified'] 
                    if os.path.getmtime(f'{self.target_path}\\{file}') > float(saved_last_modified):
                        #run what we intended after catching the changes of files.
                        print(f'{file} has just been changed!')
                        file_last_modified = os.path.getmtime(f'{self.target_path}\\{file}')
                        tmp_section['last_modified'] = str(file_last_modified)

                except configparser.NoSectionError and KeyError: #if user created new file
                    print(f'A new file named {file} is created!')
                    self.config_file.add_section(file)
                    tmp_section = self.config_file[file]
                    file_titles = file.split('.')

                    if (file_titles[0] is not '') and (len(file_titles) is 2) :
                        file_name, file_ext = file_titles
                    elif not '.' in file:
                        file_name = file
                        file_ext = 'Null'
                    else:
                        file_name = 'Null'
                        file_ext = file_titles[0]

                    if os.path.isdir(file):
                        file_type = 'Directory'
                    else:
                        file_type = 'File'
                    file_last_modified = os.path.getmtime(f'{self.target_path}\\{file}')
                    tmp_section['name'] = file_name
                    tmp_section['extension'] = file_ext
                    tmp_section['last_modified'] = str(file_last_modified)
                    tmp_section['type'] = file_type

            CONFIG_VERSION["last_config"] = str(datetime.now())
            with open(f'{self.target_path}\\\config.ini', "w") as f: #save them
                self.config_file.write(f)
    def check_deleted(self):
        current_config_sections = self.config_file.sections()
        current_files = os.listdir(self.target_path) + ["DEFAULT", "CONFIG_VERSION"]
        
        deleted_files = list(set(current_config_sections) - set(current_files)) #Check if there is already deleted item in the config.ini
        if len(deleted_files) > 0:
            print("Some deleted files are found!")
            for file in deleted_files:
                with open(f'{self.target_path}\\\config.ini', "r") as f: #read ini file
                    self.config_file.read_file(f)
                self.config_file.remove_section(file)
                
                print(f"We've just deleted {file}.")

                with open(f'{self.target_path}\\\config.ini', "w") as f: #save change
                    self.config_file.write(f)
                



if __name__ == "__main__":
   #module_names = ["sample1", "sample2"]  # Add all your module names here
    hot_reloader = HotReloader()

    while True:
        hot_reloader.check_repos()
        hot_reloader.check_deleted()

        time.sleep(10) #Slow Down
