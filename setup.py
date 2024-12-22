from setuptools import setup, find_packages

setup(
    name="IOSMockGPSAgent",
    version="1.0.0",
    author="Juntao Cheng",
    author_email="juntao.cheng.tf@gmail.com",
    description="A simple agent service for executing GPS Simulator commands (sent from remote windows controller machine) received by a Python `Flask` based HTTP server hosted on LAN network.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/stcheng1982/IOSMockGPSAgent",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "Flask>=3.0.0",
        "pymobiledevice3>=4.14.16",
    ],
    entry_points={
        "console_scripts": [
            "iosmockgpsagent=py_ios_mockgpsagent.server:main",
        ],
    },
    python_requires=">=3.11.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
