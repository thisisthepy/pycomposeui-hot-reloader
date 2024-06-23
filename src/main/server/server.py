import os
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from .observer import start_monitoring, ConnectionManager


async def put_file_change_info(current_event: dict, connection_manager: ConnectionManager, base_directory: str):
    """This Function put the information of the file's change on the asyncio.Queue.
        Args:
            current_event (dict): This saves the information about file changes.
            connection_manager (ConnectionManage): This manages the connection with clients through asyncio.Queue.
            base_directory (str): This indicates the basic directory which need to all OS.

        Return: None
    """
    os_name = current_event['os_tag']
    connected_os_dict = await connection_manager.get_client_connections()
    connected_os_list = list(connected_os_dict.keys())

    if os_name in connected_os_list:
        for queue in connected_os_dict[os_name]:
            await queue.put(current_event)

    elif base_directory in os_name:
        for connected_os in connected_os_list:
            for queue in connected_os_dict[connected_os]:
                await queue.put(current_event)


async def on_startup(directories_to_watch: list, zipfile_dir: str, os_list: list,
                     connection_manager: ConnectionManager, exception_dir: list,
                     default_name_tail: str = '', base_directory: str = ''):
    """This Function goes up when the server has been called.
        Args:
            directories_to_watch (list): This determines the directory to be watched.
            zipfile_dir (str): This determines the directory to save the zipped files.
            os_list (list): This saves the list of OS.
            connection_manager (ConnectionManager): This manages the connection with clients through asyncio.Queue.
            exception_dir (list): This determines the directories not be watched.
            base_directory (str): This indicates the basic directory which need to all OS.
            default_name_tail (str): This indicates the tail of directory name that always follows.
        Return: None
    """
    while True:
        current_event = await start_monitoring(os_list=os_list, directories_to_watch=directories_to_watch,
                                               zipfile_dir=zipfile_dir, exception_dir=exception_dir,
                                               base_directory=base_directory, default_name_tail=default_name_tail)
        sys.stdout.write(f'Received event is {current_event}.\n')
        await put_file_change_info(current_event=current_event, connection_manager=connection_manager,
                                   base_directory=base_directory)


def start_reloading(directories_to_watch: list = None, zipfile_dir: str = None, os_list: list = None,
                    current_event: dict = None, exception_dir: list = None,
                    default_name_tail: str = '', base_directory: str = ''):
    """This function is used to run the server and main.client.commonMain.kotlin.main processes.
        Args:
            directories_to_watch (list): This determines the directory to be watched.
            zipfile_dir (str): This determines the directories to save the zipped files.
            os_list (list): This saves the list of OS.
            current_event (dict): This saves the information about file changes.
            exception_dir (list): This determines the directories not be watched.
            base_directory (str): This indicates the basic directory which need to all OS.
            default_name_tail (str): This indicates the tail of directory name that always follows.
        Return: None
    """
    app = FastAPI()
    connection_manager = ConnectionManager()
    app.add_event_handler("startup",
                          lambda: asyncio.create_task(
                              on_startup(directories_to_watch=directories_to_watch,
                                         os_list=os_list, zipfile_dir=zipfile_dir,
                                         connection_manager=connection_manager,
                                         exception_dir=exception_dir,
                                         base_directory=base_directory, default_name_tail=default_name_tail)))

    async def send_zipped_file(current_event: dict, zipfile_dir: str, os_name: str):
        """This function returns target clients the zipped file of the newest version.
            Args:
                current_event (dict): This saves the information about file changes.
                zipfile_dir (str): This determines the directory to save the zipped files.
                os_name (str): This indicates the type of main.client.commonMain.kotlin.getClient which whill receive the file.
            Return: None
        """
        zip_filename = os_name + '.zip'
        paths = [zipfile_dir, 'zip_files', f'{os_name}.zip']
        return FileResponse(path=os.path.join(*paths), filename=zip_filename, media_type='application/zip')

    @app.get("/")
    @app.get("/index.html")
    async def index():
        """Show the change logs on the Web."""
        template_path = [os.path.dirname(sys.argv[0]), "res", "static", "templates", "index.template"]
        with open(os.path.join(*template_path), "r", encoding="UTF-8") as idx:
            index_template = idx.readlines()
        if str(type(index_template)) == "<class 'list'>":
            index_template = "\n".join(index_template)
        return HTMLResponse(index_template)

    @app.get("/main.client.commonMain.kotlin.client/{os_name}")
    async def register_client(os_name: str):
        """Register Client at the client_connections and asyncio.Queue"""
        client_connections = await connection_manager.get_client_connections()
        connections_os_list = list(client_connections.keys())

        if os_name in os_list:
            sys.stdout.write(f'INFO: {os_name} main.client.commonMain.kotlin.getClient is trying to connect to the server.\n')
            if os_name not in connections_os_list:
                await connection_manager.add_os(os_name=os_name)
            queue = asyncio.Queue()
            await connection_manager.add_queue(os_name=os_name, queue=queue)
            sys.stdout.write(f'INFO: The current client_connections is {client_connections}.\n')

            try:
                current_event = await queue.get()
                # print(f'now the Queue {queue} received th event information')
                response = await send_zipped_file(current_event=current_event, zipfile_dir=zipfile_dir, os_name=os_name)
                return response
            finally:
                print(f'The Queue {queue} is deleted.')
                await connection_manager.delete_queue(os_name=os_name, queue=queue)
                # client_connections = await connection_manager.get_client_connections()
                # print(f'{client_connections}')

        else:
            raise HTTPException(status_code=404,
                                detail="The main.client.commonMain.kotlin.getClient's os name is not registered during the initialization process.")

    @app.get("/main.client.commonMain.kotlin.client/{os_name}/zip")
    async def os_zip(os_name: str):
        """Enable main.client.commonMain.kotlin.getClient to download the newest zip file."""
        if os_name in os_list:
            paths = [zipfile_dir, 'zip_files', f'{os_name}.zip']
            return FileResponse(path=os.path.join(*paths), filename=f"{os_name}.zip")

        else:
            raise HTTPException(status_code=404,
                                detail="The main.client.commonMain.kotlin.getClient's os name is not registered during the initialization process.")

    return app
