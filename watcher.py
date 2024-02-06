import importlib
import time
import os
import sys

class HotReloader:
    def __init__(self, module_names):
        self.module_names = module_names
        self.module_paths = {name: f"{name}.py" for name in module_names}
        self.modules = {}

    def load_modules(self):
        for module_name in self.module_names:
            try:
                # Attempt to reload the module
                module = importlib.reload(sys.modules[module_name])
                print(f"Reloaded module: {module_name}")
                self.modules[module_name] = module
            except KeyError:
                # If the module hasn't been imported yet, import it for the first time
                module = importlib.import_module(module_name)
                print(f"Loaded module: {module_name}")
                self.modules[module_name] = module

    def check_module_changes(self):
        for module_name, module_path in self.module_paths.items():
            if os.path.exists(module_path):
                last_modified = os.path.getmtime(module_path)
                if module_name in self.modules:
                    if last_modified > self.modules[module_name].__file_last_modified:
                        print(f"Detected change in {module_name}. Reloading...")
                        self.load_modules()
                        break
                else:
                    self.load_modules()
                    break

    def run(self):
        try:
            while True:
                self.check_module_changes()

                # Your main logic using the reloaded modules goes here
                for module_name, module in self.modules.items():
                    module.example_function()

                # Sleep for a short duration before checking for updates
                time.sleep(5)

        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == "__main__":
    module_names = ["sample1", "sample2"]  # Add all your module names here
    hot_reloader = HotReloader(module_names)
    hot_reloader.run()
