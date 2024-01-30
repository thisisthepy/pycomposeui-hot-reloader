import importlib
import time

def load_module(module_name):
    try:
        # Attempt to reload the module
        module = importlib.reload(importlib.import_module(module_name))
        print(f"Reloaded module: {module_name}")
        return module
    except ImportError:
        # If the module hasn't been imported yet, import it for the first time
        module = importlib.import_module(module_name)
        print(f"Loaded module: {module_name}")
        return module

def main():
    module_name = "sample"  # Change this to the name of your module
    
    try:
        while True:
            # Load the module
            module = load_module(module_name)
            
            # Your main logic using the reloaded module goes here
            # For example, call a function from the reloaded module
            module.example_function()
            
            # Sleep for a short duration before checking for updates
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()