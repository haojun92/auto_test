from setuptools import find_packages, setup

with open("requirements.txt") as f:
    install_requires = [_.strip() for _ in f.readlines()]

setup(
    name="test_ark",
    version="0.1.0",
    url="https://bitbucket.holomatic.ai/users/jianghui/repos/test_ark/browse",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        "console_scripts": ["test_ark = test_ark.__main__:cli"],
    },
    python_requires=">=3.11",
)
