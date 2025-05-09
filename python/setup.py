from setuptools import setup, find_packages

setup(
    name="easygese",
    version="0.1.0",
    description="Minimal python package with functions to load and explore EasyGeSe data.",
    author="Quesada-Traver Carles, Ariza-Suarez Daniel, Studer Bruno, Yates Steven",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests"
    ],
    python_requires='>=3.6',
)