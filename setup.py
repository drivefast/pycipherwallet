from setuptools import setup

setup (
    name="pycipherwallet",
    version=open("VERSION").read(),
    author="drivefast",
    author_email="radu@cqr.io",
    packages=["cipherwallet"],
    include_package_data=True,
    url="https://github.com/drivefast/pycipherwallet",
    download_url="https://github.com/drivefast/pycipherwallet/tarball/" + open("VERSION").read(),
    description="cipherwallet python SDK",
    long_description=open("BASICS.md").read(),
    install_requires=["bottle", "sqlalchemy", "pylibmc","redis"],
)
