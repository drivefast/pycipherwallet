from setuptools import setup

setup (
    name="pycipherwallet",
    version="0.1.0",
    author="drivefast",
    author_email="radu@cqr.io",
    packages=["cipherwallet"],
    include_package_data=True,
    url="http://cipherwallet.com/devs",
    description="Free. You won't get sued for using this.",
    long_description=open("README.txt").read(),
    install_requires=["bottle", "sqlalchemy", "pylibmc","redis"],
)
