from setuptools import setup, find_packages
from glob import glob


setup(
    name="PyComposeHotReloader",
    version="0.0.1",
    description="PyComposeHotReloader for hot-reloading the files through FastAPI",
    author="thisisthepy",
    author_email="",
    url="https://https://github.com/thisisthepy/pycomposeui-hot-reloader",
    packages=list(set(['/'.join(path.removesuffix(".py").split('/')[:-1]) for path in glob("PyComposeHotReloader/**/*.py", recursive=True)])),
    install_requires=[
        "fastapi",
        "watchdog",
        "uvicorn",
        "asyncio"
    ]
)