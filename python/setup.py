from setuptools import setup, find_packages

setup(
    name="easygese",
    version="0.1.0",
    description="Package with functions to load and explore EasyGeSe data.",
    author="Quesada-Traver Carles, Ariza-Suarez Daniel, Studer Bruno, Yates Steven",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests",
        "appdirs",
        "tabulate"
    ],
    python_requires='>=3.6',
)