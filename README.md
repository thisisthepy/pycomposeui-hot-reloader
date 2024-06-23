# PyComposeHotReloader
**Hot Reload (Live Update) Server & Client for PyCompose Application**

## Overview
The **PyComposeUI Hot Reloader** is a tool designed to enhance the development experience by automatically reloading the UI when changes are detected in the source code. This allows for a more efficient workflow, eliminating the need to manually restart the application after each modification.

### Description of Two Side Assistance
#### 1. Server-side
The Server of the PyComposeHotReloader assists HotReloading the files through FastAPI Server.
#### 2. Client-side
The Client Assistance provides the beter experience through three procedures.
```shell
a. Get the newest files from the server as zipped
b. Unzip the files
c. Update the application in the background
```

## Features
- **Automatic Reloading**: Detects changes in the source code and reloads the UI seamlessly.
- **Configurable Watcher**: Allows customization of the directories.
- **Minimal Setup**: Easy integration with existing PyComposeUI projects.

## Installation
### 1. Server-side
To install the PyComposeUI Hot Reloader, clone the repository and navigate to the project directory

```shell
git clone https://github.com/thisisthepy/pycomposeui-hot-reloader.git
cd pycomposeui-hot-reloader
```


### 2. Client-side

## Dependencies

### 1. Server-side

### 2. Client-side

## Usage
### 1. Server-side
#### Put the following code in the cmd.
```shell
python -m pycomposeui_hot_reloader.run server 
```
Users can also specify the directories to watch and the destination to store the zipped files.
- Use -m to specify the directories to watch
- Use -z to specify the directory to store the zipped files.
```shell
python -m pycomposeui_hot_reloader.run server -w ./src/test/app/src -z ./test/app/zip_files
```

#### OR

#### import the module in your code
```cython
### in the top of your code

import PyComposeHotReloader
PyComposeHotReloader.run(server)
```

### 2. Client-side


## Configuration

## Contribution

## License

