from setuptools import find_packages, setup

setup(
    name="tinydist",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "requests",
        "send2trash",
        "Flask",
        "python-dotenv",
        "tqdm",
        "aiofiles",
        "aiosqlite",
    ],
    entry_points={
        "console_scripts": [
            "tinydist=tinydist:cli",
        ],
    },
)
