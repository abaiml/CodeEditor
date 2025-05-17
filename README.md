# Backend for WebSocket Code Executor 

This backend provides a WebSocket endpoint to execute code snippets in various languages (Python, JavaScript, C++). It requires a secret token for authentication to secure WebSocket connections.

---

## Features

- Supports Python, JavaScript (Node.js), and C++ code execution.
- WebSocket authentication using a secret token (`EDITOR_TOKEN`).
- Runs code inside temporary directories and cleans up after execution.
- Supports stopping execution via WebSocket message.
- CORS configured to allow connections from a specific frontend origin.

---

## Setup

### Requirements

- Python 3.8+
- `fastapi`, `uvicorn`
- Node.js and `node` command available (for JavaScript execution)
- `g++` compiler (for C++ execution)

Install dependencies:

```bash
pip install fastapi uvicorn
