<a id="readme-top"></a>

## About

A CLI program to automate bumping your Discord servers on Disboard.org.

## Disclaimer

> Automating user accounts (self-botting) is a violation of Discord's Terms of Service and Disboard's rules.

This software is a proof of concept designed for educational purposes only.
I do not recommend using it on your main account or vital servers.
**Use this tool at your own risk.** I am not responsible for any consequences,
including account bans or restrictions from Discord or Disboard.

## Features

* **Multi-server support:** Register and bump multiple servers automatically.
* **Multi-account management:** Use several Discord accounts to handle cooldowns
and optimize bumping efficiency.

## Security Warning

⚠️ The file `data/selfbots.json` contains the Discord **tokens** of the registered accounts in plain text.

Please **NEVER** share this file with anyone.

Anyone with access to your token has full access to your Discord account.

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

[How do I get my discord token ?](https://discordpy-self.readthedocs.io/en/latest/authenticating.html)

Most configuration options are straightforward. For the **reorder** option, the inputs are:

* `s`: Save the new order.
* `q`: Quit without saving.
* `x y`: Move a server from index `x` to index `y`.
