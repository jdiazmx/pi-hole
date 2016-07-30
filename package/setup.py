from setuptools import setup, find_packages

setup(
    name="pihole",
    version="3.0.0",
    packages=find_packages(),
    scripts=["bin/pihole"],

    install_requires=["docopt", "requests"],

    url="https://pi-hole.net",
    license="AGPL"
)
