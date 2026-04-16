from setuptools import setup, find_packages

setup(
    name="kiro-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "requests",
        "click",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "kiro=kiro_cli.cli:cli",
        ],
    },
)
