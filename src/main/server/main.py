from ..server.server import *
import uvicorn
import os


def run_server(directory_to_watch: str = None, zipfile_dir: str = None,
               os_list: list = None, os_exception_list: list = None,
               host: str = "127.0.0.1", port: int = 8000):
    """This function is used to initialize the circumstances of reloading.

        Args:
            directory_to_watch: This determines the directory to be watched.
            zipfile_dir: This determines the directory to save the zipped files.
            os_list : (Optional) This saves the list of OS.
            os_exception_list: (Optional) This excludes the directory which should not be identified as an OS.
            Initialized list is ["common", "__pycache__", "zip_files"]
            host:  (Optional) This determines the host of the FastAPI.  Initialized as "127.0.0.1"
            port:  (Optional) This determines the port of the FastAPI.  Initialized as "8000"

        Global variable (Don't initialize) :
            CURRENT_EVENT: This saves the current event that was tracked lately.
            INFORMATION_SENT : This is the flag about sending information.
            ws_connections : This is the list to save the WebSockets currently saved.
    """
    if directory_to_watch is None:
        print(f"The directory to be watched was not initialized.  Please initialize before running the server.")
        return "[initializing_error]"

    if zipfile_dir is None:
        print(f"The directory to save zipped files was not initialized.  Please initialize before running the server.")
        return "[initializing_error]"

    if os_exception_list is None:
        os_exception_list = ["common", "__pycache__", "zip_files"]

    if os_list is None:  # Populate the os_list with directories that are not in the exception_list.
        os_list = []
        for item in os.listdir(directory_to_watch):
            sub_folder = os.path.join(directory_to_watch, item)
            print(f'Checking current directories.... : {sub_folder}')
            dir_name = item.replace('Main', '')
            print(f'A current dir_name is {dir_name}.')
            if os.path.isdir(sub_folder) and dir_name not in os_exception_list:
                os_list.append(dir_name)
        print(f'OS list is {os_list}')

    fastAPI_app = start_reloading(directory_to_watch=directory_to_watch, zipfile_dir=zipfile_dir,
                                  os_list=os_list)

    uvicorn.run(fastAPI_app, host=host, port=port)
