# 🕗 CRONJOBZ: your simple and easy job monitor

## What is it? What it will be?

- Ideal to use with Crontab, Cronjobz is a tracker, a logger, a terminal app and a web app.

- Simple to configure (just a TOML).

- Simple to watch (just connect to your server via SSH and see what's going on with your terminal).

- A simple web dashboard for the babies

## Example of use

You can write this in your crontab.

```bash
30 10 * * * cronjobz daily-task "/bin/bash task.sh"
```

Or just do it manually and track it anyway.

```bash
cronjobz daily-task "uv run super_project/main.py"
```

It is a wrapper. You don't have to edit your scripts. No Python.
It is just a "smart" executor.
