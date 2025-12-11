<a id="readme-top"></a>

## About

A CLI program to automate bumping your Discord servers on Disboard.org.

## Installation

1. Clone the repository.

2. **(Optional but highly recommended) Create a virtual environment.**
   The `discord.py-self` API installation may break the standard `discord.py` API,
   so I recommend creating a virtual environment.

   For venv usage, check [this link](https://www.w3schools.com/python/python_virtualenv.asp).

3. Install requirements:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

Launch the program:

**Linux:**

```sh
python3 main.py
```

**Windows:**

```sh
python main.py
```

If this is your first time running the program, the configuration manager will
open. You will need to register at least one server and one selfbot.

Most configuration options are straightforward. For the **reorder** option, the inputs are:

* `s`: Save the new order.
* `q`: Quit without saving.
* `x y`: Move a server from index `x` to index `y`.
