import setuptools
import eventstudy as es

def readme():
    with open("README.md") as f:
        return f.read()

def get_dependencies():
    with open("requirements.txt","r") as f:
        return [pkg for pkg in f.read().split("\n")]

setuptools.setup(
    name="eventstudy",
    version=es.__version__,
    author=es.__author__,
    author_email=es.__email__,
    description=es.__description__,
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/LemaireJean-Baptiste/eventstudy",
    packages=setuptools.find_packages(),
    install_requires=get_dependencies(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)