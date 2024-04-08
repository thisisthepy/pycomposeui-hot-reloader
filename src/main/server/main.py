from src.main.server.server import *


def run_server(DIRECTORY_TO_WATCH: str = None, ZIPFILE_DIR: str = None,
               OS_LIST: list = None, OS_EXCEPTION_LIST: list = None,
               HOST: str = "127.0.0.1", PORT: int = 8000):
    """This function is used to initialize the circumstances of reloading.

        Args:
            DIRECTORY_TO_WATCH: This determines the directory to be watched.
            ZIPFILE_DIR: This determines the directory to save the zipped files.
            OS_LIST : (Optional) This saves the list of OS.
            OS_EXCEPTION_LIST: (Optional) This excludes the directory which should not be identified as an OS.
            Initialized list is ["common", "__pycache__", "zip_files"]
            HOST:  (Optional) This determines the host of the FastAPI.  Initialized as "127.0.0.1"
            PORT:  (Optional) This determines the Port of the FastAPI.  Initialized as "8000"

        Global variable (Don't initialize) :
            CURRENT_EVENT: This saves the current event that was tracked lately.
            INFORMATION_SENT : This is the flag about sending information.
            ws_connections : This is the list to save the WebSockets currently saved.
    """
    if DIRECTORY_TO_WATCH is None:
        print(f"The directory to be watched was not initialized.  Please initialize before running the server.")
        return "[initializing_error]"

    if ZIPFILE_DIR is None:
        print(f"The directory to save zipped files was not initialized.  Please initialize before running the server.")
        return "[initializing_error]"

    if OS_EXCEPTION_LIST is None:
        OS_EXCEPTION_LIST = ["common", "__pycache__", "zip_files"]

    if OS_LIST is None:  # Populate the OS_LIST with directories that are not in the exception_list.
        OS_LIST = []
        for item in os.listdir(DIRECTORY_TO_WATCH):
            sub_folder = os.path.join(DIRECTORY_TO_WATCH, item)
            print(f'Checking current directories.... : {sub_folder}')
            dir_name = item.replace('Main', '')
            print(f'A current dir_name is {dir_name}.')
            if os.path.isdir(sub_folder) and dir_name not in OS_EXCEPTION_LIST:
                OS_LIST.append(dir_name)
        print(f'OS list is {OS_LIST}')

    fastAPI_app = start_reloading(DIRECTORY_TO_WATCH=DIRECTORY_TO_WATCH, ZIPFILE_DIR=ZIPFILE_DIR,
                                  OS_LIST=OS_LIST)

    uvicorn.run(fastAPI_app, host=HOST, port=PORT)
