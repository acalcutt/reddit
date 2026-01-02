# install-reddit.sh — development installer

This document summarizes what `install-reddit.sh` (the dev environment installer) does and which services it provisions when run. The script is intended for local development only — do not run it on production or personal machines you rely on for other tasks.

Overview
- The installer must be run as root (it exits if not run with elevated privileges).
- It expects to live next to an `install/` directory containing helper install scripts. If those helpers are missing it will download them from the canonical repo.
- It sources `install/install.cfg` for configuration values and respects environment variable overrides (for example `REDDIT_USER` and `REDDIT_DOMAIN`).
- At the end it runs `install/reddit.sh`, which orchestrates the individual setup scripts.

Typical invocation

REDDIT_USER and REDDIT_DOMAIN are commonly provided when invoking the installer. In this project's docs we use `reddit.local` as the development domain. Example:

```
REDDIT_USER=appuser REDDIT_DOMAIN=reddit.local ./install-reddit.sh
```

Configurable variables (from `install/install.cfg`)

You can override these variables by exporting them on the command line when invoking the installer. The installer will use the value from the environment if provided, otherwise it falls back to the defaults shown here.

- `REDDIT_USER` — user to install the code for (default: `$SUDO_USER`).
- `REDDIT_GROUP` — group to run reddit code as (default: `nogroup`).
- `REDDIT_HOME` — root directory for the install (default: `/home/$REDDIT_USER`).
- `REDDIT_SRC` — source directory under the home (default: `$REDDIT_HOME/src`).
- `REDDIT_VENV` — Python virtualenv path (default: `$REDDIT_HOME/venv`).
- `REDDIT_DOMAIN` — domain used to access the install (default: `reddit.local`).
- `REDDIT_PLUGINS` — space-separated plugins to install (default: `about gold`).
- `APTITUDE_OPTIONS` — flags passed to `apt`/`apt-get` (default: `-y`).
- `PYTHON_VERSION` — Python version to install/use (default: `3.12`).
- `REDDIT_BASEPLATE_PIP_URL` — pip URL or requirement spec for `baseplate` installation (default: git+https://github.com/acalcutt/baseplate.py.git@develop#egg=baseplate).
- `REDDIT_FORMENERGY_OBSERVABILITY_PIP_URL` — pip URL for formenergy-observability fork (default: git+https://github.com/acalcutt/formenergy-observability.git@main#egg=formenergy-observability).
- `REDDIT_WEBSOCKETS_REPO` — owner/repo for the websockets service (default: `acalcutt/reddit-service-websockets`).
- `REDDIT_ACTIVITY_REPO` — owner/repo for the activity service (default: `acalcutt/reddit-service-activity`).
- `CASSANDRA_SOURCES_LIST` — path for a custom datastax APT sources list (default: `/etc/apt/sources.list.d/cassandra.sources.list`).
- `DEBIAN_FRONTEND` — installer sets this to `noninteractive` by default to avoid interactive prompts.

Example override (same as above):

```
REDDIT_USER=appuser REDDIT_DOMAIN=reddit.local ./install-reddit.sh
```


What the script does (high level)
- Verifies it is running as root.
- Ensures the `install/` helper scripts are available — downloads them if they are missing.
- Loads configuration from `install/install.cfg` (you can edit this file or override settings via environment variables at runtime).
- Prompts for confirmation before proceeding.
- Executes `install/reddit.sh`, which in turn runs the platform-specific setup scripts (listed below).

Primary components and services created/installed
Note: exact names and init/systemd units depend on the helper scripts and the target distribution. The installer intends to set up a working development stack including:

- System packages and dependencies (`install_apt.sh` or equivalent)
- Cassandra (data store) — `install_cassandra.sh` / `setup_cassandra.sh`
- Zookeeper (coordination) — `install_zookeeper.sh`
- mcrouter / Memcached (caching layer) — `setup_mcrouter.sh`
- PostgreSQL (relational DB) — `setup_postgres.sh`
- RabbitMQ (message queue) — `setup_rabbitmq.sh`
- Any system service wrappers or unit files for the above so they run on boot (handled by `install_services.sh`)
- Reddit-specific setup (`reddit.sh`) which typically:
  - creates the `REDDIT_USER` account (if configured),
  - clones/places the reddit codebase under the chosen user/home,
  - creates configuration files (pointing at the installed DBs/caches),
  - optionally prepares CI/dev helpers (e.g. `travis.sh`) and finalization steps (`done.sh`).

Important notes and warnings
- This installer is destructive in places: it installs and configures system-level services, and may truncate or reinitialize databases. Only run it on throwaway VMs, containers, or dedicated dev hosts.
- DNS: the script will not configure DNS or `/etc/hosts` on your host. If you want to use `reddit.local` you must map that name to the VM/container IP yourself (for example by adding an `/etc/hosts` entry on your host machine).
- Configuration: edit `install/install.cfg` to change defaults, or export environment variables to override per-run.
- If you run the installer without the `install/` helper scripts present it will fetch them from the network — ensure your network and firewall allow `wget` access.

Next steps after install
- Verify the installed services are running (systemd or init scripts depending on platform).
- Check the configuration files in the installed code and update `REDDIT_DOMAIN` if necessary.
- Start the reddit dev server/process as the configured `REDDIT_USER` and visit `https://reddit.local` (or whatever domain you used) in your browser.

If you want, I can also:
- Add an example `/etc/hosts` entry for `reddit.local` to this doc, or
- Create a small checklist of verification commands to run after installation.

File: `install-reddit.sh` (source) — refer to that script for exact filenames called; the installer downloads/uses helpers such as:
`done.sh`, `install_apt.sh`, `install_cassandra.sh`, `install_services.sh`, `install_zookeeper.sh`, `reddit.sh`, `setup_cassandra.sh`, `setup_mcrouter.sh`, `setup_postgres.sh`, `setup_rabbitmq.sh`, `travis.sh`.

Example `/etc/hosts` entry

If you want `reddit.local` to resolve on your host machine, add an `/etc/hosts` entry mapping the chosen hostname to the VM/container IP or to localhost for a local install. Examples:

Local development on the same machine (binds to localhost):

```
127.0.0.1 reddit.local
```

When running inside a VM or container, replace `192.168.33.10` with the VM/container IP:

```
192.168.33.10 reddit.local
```

After adding the host mapping, you should be able to visit `https://reddit.local` in your browser (or the HTTP/HTTPS endpoint the installer configures).

Systemd / init scripts and service names created by the installer

The installer creates several service units, init scripts, and helper scripts so the reddit stack can be managed via `systemctl` (preferred) or Upstart on older systems. Common files/units created by `install/reddit.sh` and the helper scripts include:

- Systemd unit files (written to `/etc/systemd/system/`):
  - `reddit-serve.service` — the main web app (paster serve) unit.
  - `reddit-websockets.service` — websockets service (baseplate-serve).
  - `reddit-activity.service` — activity service (baseplate-serve).
  - `gunicorn-click.service` — gunicorn process for the click/tracker app (binds to a unix socket).
  - `gunicorn-geoip.service` — gunicorn geoip server (binds to 127.0.0.1:5000).

- Upstart jobs (if `/etc/init` exists):
  - `/etc/init/reddit-websockets.conf` — websockets upstart job.
  - `/etc/init/reddit-activity.conf` — activity upstart job.
  - The installer also copies any plugin-provided `upstart/` jobs into `/etc/init` or `/etc/init.d` via `copy_upstart`.

- Other init / service-related files created or enabled:
  - `/etc/gunicorn.d/click.conf` and `/etc/gunicorn.d/geoip.conf` — per-app gunicorn configs.
  - `/etc/nginx/sites-available/reddit-media`, `/etc/nginx/sites-available/reddit-pixel`, `/etc/nginx/sites-available/reddit-ssl` and corresponding symlinks in `/etc/nginx/sites-enabled/`.
  - `/etc/haproxy/haproxy.cfg` is modified (backed up) and `haproxy` is restarted.
  - A cron file at `/etc/cron.d/reddit` is created to schedule periodic reddit maintenance jobs.

- System services installed/enabled by `install_services.sh` (package-provided units):
  - `memcached` (unit name may be `memcached.service`)
  - `postgresql` (e.g. `postgresql.service`)
  - `rabbitmq-server` (e.g. `rabbitmq-server.service`)
  - `redis-server` (e.g. `redis-server.service`)
  - On older Ubuntu targets `mcrouter` may be installed instead of mcrouter availability varies by distro/ppa.

- Helper CLI wrappers installed to `/usr/local/bin/`:
  - `reddit-run`, `reddit-shell`, `reddit-start`, `reddit-stop`, `reddit-restart`, `reddit-flush`, `reddit-serve` — thin helpers that call into the venv and service scripts.

Notes
- Unit names can vary slightly between distributions (for example `postgresql` vs `postgresql@12-main`), and `install_services.sh` uses package names when enabling services where appropriate. Check the exact unit name with `systemctl list-units | grep reddit` or `systemctl status <unit>` on your host.
- To follow the main web app logs live, run:

```
journalctl -u reddit-serve -f -o cat
```

