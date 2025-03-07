<h1 align="center">mozi</h1>

<h4 align="center"><em>A repository of essential tools and functions that can be used across various projects and applications..</em></h4>

<p align="center">
    <a href="https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/vscode-remote-try-java">
        <img alt="dev-container" src="https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode" />
    </a>
</p>

# Installation

```
pip install git+https://github.com/tonsh/mozi.git@master

pip install "mozi[api] @ git+https://github.com/tonsh/mozi.git@master"
```

# Project Config

```python
# .env
APP_NAME = 'your_app_name'
APP_DEV = 'dev|pro|test'
```

# How to use fastapi app
Using mozi.api.app will automatically log request and error logs.

```
# main.py

from mozi.api.app import app

@app.get("/")
async def hello():
    return {"message": "Hello world"}
```
