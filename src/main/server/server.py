import os
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from .observer import start_monitoring, ConnectionManager

async def put_file_change_info(current_event: dict, connection_manager: ConnectionManager, os_list: list):
    """This Function put the information of the file's change on the asyncio.Queue.
        Args:
            current_event (dict): This saves the information about file changes.
            connection_manager (ConnectionManage): This manages the connection with clients through asyncio.Queue.
            os_list (list): This indicates the list of os which are initialized.

        Return: None
    """
    os_name = current_event['os_tag']
    #print('Now in the process to put info on the Queue.')
    connected_os_dict = await connection_manager.get_client_connections()
    connected_os_list = list(connected_os_dict.keys())

    if os_name in connected_os_list:
        for queue in connected_os_dict[os_name]:
            await queue.put(current_event)

    elif common in os_name:
        for os in connected_os_list:
            for queue in connected_os_dict[os]:
                await queue.put(current_event)
async def on_startup(directories_to_watch: list, zipfile_dir: str, os_list: list,
                     connection_manager: ConnectionManager, exception_dir: list):
    """This Function goes up when the server has been called.
        Args:
            directories_to_watch (list): This determines the directory to be watched.
            zipfile_dir (str): This determines the directory to save the zipped files.
            os_list (list): This saves the list of OS.
            connection_manager (ConnectionManager): This manages the connection with clients through asyncio.Queue.
        Return: None
    """
    while True:
        current_event = await start_monitoring(os_list=os_list, directories_to_watch=directories_to_watch,
                                               zipfile_dir=zipfile_dir, exception_dir=exception_dir)
        sys.stdout.write(f'Received event is {current_event}.\n')
        await put_file_change_info(current_event=current_event, connection_manager=connection_manager, os_list=os_list)

def start_reloading(directories_to_watch: list = None, zipfile_dir: str = None, os_list: list = None,
                    current_event: dict = None, exception_dir: list = None):
    """This function is used to run the server and main processes.
        Args:
            directories_to_watch (list): This determines the directory to be watched.
            zipfile_dir (str): This determines the directories to save the zipped files.
            os_list (list): This saves the list of OS.
            current_event (dict): This saves the information about file changes.
            exception_dir (list): This determines the directories not be watched.
        Return: None
    """
    app = FastAPI()
    connection_manager = ConnectionManager()
    app.add_event_handler("startup",
                          lambda: asyncio.create_task(
                              on_startup(directories_to_watch=directories_to_watch,
                                         os_list=os_list, zipfile_dir=zipfile_dir,
                                         connection_manager=connection_manager,
                                         exception_dir = exception_dir)))

    async def send_zipped_file(current_event: dict, zipfile_dir: str, os_list: list):
        """This function returns target clients the zipped file of the newest version.
            Args:
                current_event (dict): This saves the information about file changes.
                zipfile_dir (str): This determines the directory to save the zipped files.
                os_list (list): This saves the list of OS.
            Return: None
        """
        zip_filename = current_event['os_tag'] + '.zip'
        os_name = current_event['os_tag']
        paths = [zipfile_dir, 'zip_files', f'{os_name}.zip']
        #print('Now Sending!')

        return FileResponse(path=os.path.join(*paths), filename=f"{os_name}.zip", media_type='application/zip')


    @app.get("/")
    @app.get("/index.html")
    async def index():
        """Show the change logs on the Web."""
        index_template = ""
        template_path = [os.path.dirname(sys.argv[0]), "res", "static", "templates", "index.template"]
        with open(os.path.join(*template_path), "r", encoding="UTF-8") as index:
            index_template = index.readlines()
        if str(type(index_template)) == "<class 'list'>":
            index_template = "\n".join(index_template)
        return HTMLResponse(index_template)

    @app.get("/client/{os_name}")
    async def register_client(os_name: str):
        """Register Client at the client_connections and asyncio.Queue"""
        client_connections = await connection_manager.get_client_connections()
        connections_os_list = list(client_connections.keys())

        if os_name in os_list:
            sys.stdout.write(f'INFO: {os_name} client is trying to connect to the server.\n')
            if os_name not in list():
                await connection_manager.add_os(os_name=os_name)
            queue = asyncio.Queue()
            await connection_manager.add_queue(os_name=os_name, queue=queue)
            sys.stdout.write(f'INFO: The current client_connections is {client_connections}.\n')

            try:
                current_event = await queue.get()
                #print(f'The client now got information by the Queue {queue}.')
                response =  await send_zipped_file(current_event=current_event,
                                                   zipfile_dir=zipfile_dir, os_list=os_list)
                return response
            finally:
                #print(f'The Queue {queue} is deleted.')
                await connection_manager.delete_queue(os_name=os_name, queue=queue)
                client_connections = await connection_manager.get_client_connections()
                #print(f'{client_connections}')

        else:
            raise HTTPException(status_code=404,
                                detail="The client's os name is not registered during the initialization process.")



    @app.get("/client/{os_name}/zip")
    async def os_zip(os_name: str):
        """Enable client to download the newest zip file."""
        if os_name in os_list:
            paths = [zipfile_dir, 'zip_files', f'{os_name}.zip']
            return FileResponse(path=os.path.join(*paths), filename=f"{os_name}.zip")

        else:
            raise HTTPException(status_code=404,
                                detail="The client's os name is not registered during the initialization process.")


    return app
