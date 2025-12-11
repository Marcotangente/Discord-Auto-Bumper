<a id="readme-top"></a>

<!-- ABOUT THE PROJECT -->
## About The Project

A CLI programm to automate bumping your discord servers on disboard.org.

## Installation

1. Clone the repo

2. (Optional but very recommanded) Create a virtual environnement
   The `discord.py-self` API installation may break the `discord.py`API,
   so I recommand creating a virtual environnement.

   For venv usage, check [https://www.w3schools.com/python/python_virtualenv.asp](this link)

3. Install requirements

   ```sh
   pip install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->
## Usage

Launch program

Linux:

```sh
python3 main.py
```

Windows:

```sh
python main.py
```

If it's your first time, the program will open the configuration manager. You
will have to register at least one server and one selfbot.
All the config options are straight forward, but maybe not the reorder option.
The inputs for reorder are "s" to save the new order, "q" to quit without saving
or "x y" to move a server from index x to index y.
