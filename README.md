<a id="readme-top"></a>

## About

A CLI program to automatically bump your Discord servers on Disboard.org.

## Disclaimer

> Automating user accounts (self-botting) is a violation of [Discord's Terms of Service](https://discord.com/terms) and [Disboard's guidelines](https://disboard.org/site/guidelines).

This software is a proof of concept designed for educational purposes only.
I do not recommend using it on your main account or important servers.
**Use this tool at your own risk.** I am not responsible for any consequences,
including account bans or restrictions from Discord or Disboard.

## Features

* **Multi-server support:** Register and bump multiple servers automatically.
* **Multi-account management:** Use several Discord accounts to handle cooldowns
and maximize bumping efficiency.

## Security Warning

⚠️ The file `data/selfbots.json` contains the Discord **tokens** of the registered accounts in plain text.

Please **NEVER** share this file with anyone, not even your favourite e-kitten.

Anyone with access to your token has full access to your Discord account.

## Installation

1. Ensure you have [Docker](https://docs.docker.com/get-started/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your system.

2. Clone the repository.
```sh
    git clone https://github.com/Marcotangente/Discord-Auto-Bumper.git
    cd Discord-Auto-Bumper
```

3. Configurate the container.
    Copy the `.env.example` file to `.env`
    Edit the value of the `RESTART` variable to set the restart policy of the main program.

    ------
    **Linux only**

    Create a `data` folder (if not Docker Compose will create it as root user)
    ```sh
        mkdir data
    ```

    Edit the values of the `FIXUID` and `FIXGID` so the container can give you the ownership of the `data` folder.

    To see your UID and GID:
    ```sh
        id
    ```

## Usage

1. Run the config service of the docker-compose file. If you don't know how to do it, you can just run the `config.sh` script (or look at the command inside).
Most configuration options are straightforward. For the **reorder** option, the inputs are:
* `s`: Save the new order.
* `q`: Quit without saving.
* `x y`: Move a server from index `x` to index `y`.
2. Register at least one selfbot then one server. [How do I get my discord token?](https://discordpy-self.readthedocs.io/en/latest/authenticating.html)
3. Start the main service in detached mode:
```sh
    docker compose up -d
```
4. Enjoy your free bumps!

To stop the program, you can run:
```sh
    docker compose down
```

If the program does not seem to work, you can read the logs:
```sh
    docker logs discord-auto-bumper 
```

----------

Remember: Do not share `data/selfbots.json` and do not use this program in a way that violates Discord's TOS or Disboard's guidelines.
