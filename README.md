## Reddit Python 3 fork

This repository is a fork of the original reddit codebase updated
for modern systems. Highlights:

- **Python:** Upgraded to Python 3 (tested with Python 3.12).
- **Platform:** Targeted for Ubuntu 24.04 (noble).
- **Compatibility:** Includes compatibility shims and updated install/build
	scripts to work with current packaging and system tooling.

This fork is intended for local development and experimentation. For the
original upstream project and documentation refer to the upstream repository.

---

### Quickstart (Ubuntu 24.04)

The following steps produce a development-ready environment on Ubuntu 24.04. They assume you're running as root while creating the local `apprunner` user and installing system packages; adapt commands for your environment.

1. Update apt and install system dependencies:

```bash
apt update
apt install -y git python3 python3-venv python3-dev build-essential libpq-dev libmemcached-dev gperf wget curl
```

2. Create the runtime user and directories (adjust `apprunner` as needed):

```bash
useradd -m -s /bin/bash apprunner || true
mkdir -p /home/apprunner/src
chown apprunner:apprunner /home/apprunner/src
```

3. Create a Python virtualenv for builds and installs:

```bash
sudo -u apprunner python3 -m venv /home/apprunner/venv
sudo -u apprunner /home/apprunner/venv/bin/pip install --upgrade pip setuptools wheel build
```

4. Clone the repositories into `/home/apprunner/src` and install local packages editable:

```bash
# Example for baseplate
sudo -u apprunner git clone https://github.com/your-fork/baseplate /home/apprunner/src/baseplate
sudo -u apprunner /home/apprunner/venv/bin/pip install -e /home/apprunner/src/baseplate
```

5. Run the installer from the repo root as root (it will invoke per-user build steps):

```bash
cd /path/to/reddit
./install-reddit.sh
```

Notes:
- Use the venv's `python` for manual package builds when necessary: `/home/apprunner/venv/bin/python setup.py build`.
- If the OS blocks system pip installs, prefer editable installs into the apprunner venv.
- If you encounter locale errors when creating the Postgres DB, generate `en_US.UTF-8` with `localedef -i en_US -f UTF-8 en_US.UTF-8`.
