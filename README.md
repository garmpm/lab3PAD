
# lab3PAD (Web Proxy)

## Prerequisites

- Use of venv for python virtual environment
- Use of pip for installing dependencies

Command to install libraries:

```bash
pip install -r requirements.txt
```

## Run Code locally

To run the project locally, please follow the steps given below.

- Clone this Repository

  ```bash
      git clone https://github.com/garmpm/lab3PAD.git
  ```

- Go to Project directory

  ```bash
  cd lab3PAD
  ```

- Create python virtual environment for project

  ```bash
  python3 -m venv .venv
  ```

- Activate virtual environment

  ```bash
  source .venv/bin/activate
  ```
- Install all dependencies from requirements.txt

  ```bash
  pip install -r requirements.txt
  ```

- Run the server
  ```bash
  python app.py
  ```

- Run the proxy
  ```bash
  python proxy.py
  ```

- Access Swagger
  ```bash
  http://localhost:5001/api
  ```

