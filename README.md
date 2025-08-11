# 🕗 CRONJOBZ: your simple and easy job monitor

## What is it? What will it be?

- Ideal for use with Crontab, Cronjobz is a tracker, a logger, a terminal app, and a web app.

- Simple to configure (just a TOML file).

- Simple to monitor (just connect to your server via SSH and see what's going on with your terminal).

- A simple web dashboard for the babies.

## Example of use

You can add this to your crontab:

```bash
30 10 * * * cronjobz daily-task "/bin/bash task.sh"
```

Or you can run it manually and still track it:

```bash
cronjobz daily-task "uv run super_project/main.py"
```

It is a wrapper. **You don’t need to edit your scripts or write any Python.**

It is just a "smart" executor.
