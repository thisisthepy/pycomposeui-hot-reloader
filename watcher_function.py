import importlib
import time
import os

def load_modules(module_names):
    modules = {}

    for module_name in module_names:
        try:
            # Attempt to reload the module
            module = importlib.reload(importlib.import_module(module_name))
            print(f"Reloaded module: {module_name}")
            modules[module_name] = module
        except ImportError:
            # If the module hasn't been imported yet, import it for the first time
            module = importlib.import_module(module_name)
            print(f"Loaded module: {module_name}")
            modules[module_name] = module
            

    return modules

def main():
    module_names = ["sample1", "sample2"]  # Add all your module names here
    modules = load_modules(module_names)

    try:
        while True:
            # Your main logic using the reloaded modules goes here
            for module_name, module in modules.items():
                module.example_function()

            # Sleep for a short duration before checking for updates
            time.sleep(5)

            # Check for changes in the modules and reload if necessary
            for module_name in module_names:
                module_path = f"{module_name}.py"
                print(f"The Time {os.path.getmtime(module_path) }")
                print(f"And Then {os.path.getmtime(modules[module_name].__file__)}")
                if os.path.getmtime(module_path) >  os.path.getmtime(modules[module_name].__file__):
                    print(f"Detected change in {module_name}. Reloading...")
                    modules = load_modules(module_names)
                    break

    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == '__main__':
    #if run the function directly
    main()
elif __name__ == 'multiple_watcher':
    #if this module was imported.
    main()
else:
    print('Nobody called me.')