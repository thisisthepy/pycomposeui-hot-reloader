import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileModificationDetectHandler(FileSystemEventHandler):
    """Class to handle filesystem change events."""
    def __init__(self,
                 os_list, directory_to_watch, zipfile_dir):
        super().__init__()
        self.os_list = os_list
        self.directory_to_watch = directory_to_watch
        self.zipfile_dir = zipfile_dir

    def on_new_os(self, event):
        """This method is for the situation when entered a new OS which is not in OS_LIST"""
        # The below code is just for an example.
        print(f'A New Directory has been founded, whose path is {event.src_path}.')

    def make_zip(self,
                 target_os: str, directory_to_watch: str,
                 zipfile_dir: str):
        """Make a zipfile which is composed with files in 'common' and target directory."""
        zipfile_dir += '\\zip_files'
        if not os.path.exists(zipfile_dir):
            # if there is no directory in the path, especially initializing, make the directory to store the zipFiles
            os.mkdir(zipfile_dir)

        FILE_NAME = f'{zipfile_dir}\\{target_os}.zip'
        zipped_dir = zipfile.ZipFile(FILE_NAME, 'w')

        for (path, _, files) in os.walk(directory_to_watch):
            if target_os in path or 'commonMain' in path:
                os.chdir(directory_to_watch)
                for file in files:
                    if "~" in path:
                        pass
                    else:
                        zipped_dir.write(os.path.join(
                            os.path.relpath(path, directory_to_watch), file),
                            compress_type=zipfile.ZIP_DEFLATED)
        zipped_dir.close()

    def on_any_event(self, event):
        """Handles any filesystem event Except Opening and Closing"""
        global INFORMATION_SENT
        if event.event_type != 'opened' and event.event_type != 'closed':
            if not ('~' in event.src_path and event.event_type != 'deleted'):
                global CURRENT_EVENT
                # Take actions for tracking changes of a file.
                current_path = self.directory_to_watch + "\\"
                event_dir = event.src_path.replace(current_path, '')

                if "\\" in event_dir:
                    # extract the OS tag of file
                    # Save the directory's name, not file, as the event_dir.
                    event_dir = event_dir.split('\\')[0].replace('Main', '')
                else:
                    event_dir.replace('Main', '')

                if event_dir != 'zip_files':
                    CURRENT_EVENT = [event.src_path, event_dir, event.event_type, event.is_directory]

                if event_dir == 'common' or event_dir == 'commonMain':
                    for OS in self.os_list:
                        self.make_zip(target_os=OS,
                                      directory_to_watch=self.directory_to_watch, zipfile_dir=self.zipfile_dir)
                elif event_dir in self.os_list:
                    self.make_zip(target_os=event_dir,
                                  directory_to_watch=self.directory_to_watch, zipfile_dir=self.zipfile_dir)
                elif event.is_directory:
                    print(f'event_dir is {event_dir}, and event_type is {event.event_type}.')

                else:
                    print(f'[Unnamed OS Error] The directory that has not been saved as OS was found: {event_dir}.')
                    print(f'The Tracked file is {event.src_path}.')
                    print(f'The event type is {event.event_type}.')
                    # If you want to make new OS, Take actions about this procedure.
                    self.on_new_os(event=event)

                INFORMATION_SENT = False  # Reset the flag when a new event occurs.
