import pathlib
from setuptools import setup
from re import findall

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

VERSION = findall(r"__version__ = '(.*)'", (HERE / "vk_sdk/__init__.py").read_text())[0]

# This call to setup() does all the work
setup(
    name="vk_sdk",
    version=VERSION,
    description="Wrapper around vk_api library",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/SPRAVEDLIVO/VK-SDK",
    author="SPRAVEDLIVO",
    author_email="spravedlivo@dimden.dev",
    license="AGPLv3",
    packages=["vk_sdk"],
    python_requires='>=3.9',
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],   
    include_package_data=True,
    install_requires=["pytz", "vk_api"],
    entry_points={
        "console_scripts": [
            "realpython=reader.__main__:main",
        ]
    },
)