import asyncio

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import os
import zipfile


class FileModificationEventPublisher(FileSystemEventHandler):
    """Class to detect filesystem change events and Create its message to channel"""
    def __init__(self,
                 os_list: list, directory_to_watch: str, zipfile_dir: str,
                 event_channel):
        super().__init__()
        self.os_list = os_list
        self.directory_to_watch = directory_to_watch
        self.zipfile_dir = zipfile_dir
        self.event_channel = event_channel
       # self.current_event = None
        self.current_event = asyncio.Future()

    def on_any_event(self, event):
        """Handles any filesystem event Except Opening and Closing"""
        if event.event_type != 'opened' and event.event_type != 'closed':
            if not '~' in event.src_path:
                # Take actions for tracking changes of a file.
                print(f'Changed file information: {event.src_path}')
                print(f'directory_to_watch: {self.directory_to_watch}')

                rel_event_dir = event.src_path.replace(self.directory_to_watch, '')[1:]
                event_dir = 'common'

                for os in self.os_list:
                    if os in rel_event_dir:
                        event_dir = os

                print(f'The OS which has been modified : [{event_dir}]')
                self.current_event.set_result({'src_path': event.src_path,
                                               'os_tag': event_dir,
                                               'event_type': event.event_type,
                                               'dir_flag': event.is_directory})
                if event_dir in self.os_list:
                    self.event_channel.trigger_event(event_dir,
                                                     target_os=event_dir,
                                                     directory_to_watch=self.directory_to_watch,
                                                     zipfile_dir=self.zipfile_dir)
                elif event_dir == 'common':
                    for os in self.os_list:
                        self.event_channel.trigger_event(os,
                                                         target_os=os,
                                                         directory_to_watch=self.directory_to_watch,
                                                         zipfile_dir=self.zipfile_dir)

                else:
                    print(f'[Unknown OS Error] The directory that has not been saved as OS was found: {event_dir}.')
                    print(f'The Tracked file is {event.src_path}.')
                    print(f'The event type is {event.event_type}.')


class FileModificationEventChannel:
    def __init__(self):
        self.event_handlers = {}
        self.current_event = None

    def add_event_handler(self, event_name, event_handler):
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(event_handler)

    def trigger_event(self, event_name, *args, **kwargs):
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                handler(*args, **kwargs)
        else:
            print(f'The event ({event_name}) is not on the list of event handlers.')
            print(f'Please check the process to create list. The current list is {self.event_handlers.keys()}.')


def make_zip(target_os: str, directory_to_watch: str, zipfile_dir: str):
    """Make a zipfile which is composed with files in 'common' and target directory."""

    if "\\" in zipfile_dir:
        zipfile_dir += "\\zip_files"
        file_name = f'{zipfile_dir}\\{target_os}.zip'

    elif "/" in zipfile_dir:
        zipfile_dir += "/zip_files"
        file_name = f'{zipfile_dir}/{target_os}.zip'

    if not os.path.exists(zipfile_dir):
        # if there is no directory in the path, especially initializing, make the directory to store the zipFiles
        os.mkdir(zipfile_dir)


    zipped_dir = zipfile.ZipFile(file_name, 'w')

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

    print(f'INFO:  Packaging the zipped files for {target_os} has just been completed!')


async def start_monitoring(os_list: list, directory_to_watch: str, zipfile_dir: str):
    """Starts tracking the directory"""

    event_channel = FileModificationEventChannel()

    for os_name in os_list:
        event_channel.add_event_handler(os_name, make_zip)

    # Create the event handler with the callback function.
    event_handler = FileModificationEventPublisher(os_list=os_list, directory_to_watch=directory_to_watch,
                                                   zipfile_dir=zipfile_dir, event_channel=event_channel)

    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=True)
    observer.start()

    return await event_handler.current_event

