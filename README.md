# IOS Mock GPS Agent

A simple agent service for executing GPS Simulator commands (sent from remote windows controller machine) received by a Python `Flask` based HTTP server hosted on LAN network. The underlying GPS location simulation operation relies on Python `pymobiledevice3` module.

## Installation

```bash
pip install git+https://github.com/stcheng1982/IOSMockGPSAgent.git
```

## Usage

```bash
sudo iosmockgpsagent
```

```bash
sudo iosmockgpsagent --host 0.0.0.0 --port 8888
```