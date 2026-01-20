from setuptools import find_packages, setup

with open("README.md") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    install_requires = [_.strip() for _ in f.readlines()]

setup(
    name="pcan_ext",
    version="4.0.0",
    description="PCAN Extension",
    long_description=long_description,
    install_requires=install_requires,
    packages=find_packages(),
    py_modules=[
        "PCANBasic",
    ],
    python_requires=">=3.8.0",
    url="https://bitbucket.holomatic.ai/projects/SWTEST/repos/pcan_ext/browse",
)
