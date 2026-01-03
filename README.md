## Tippr Python 3 fork

This repository is a fork of the original tippr codebase updated
for modern systems. Highlights:

- **Python:** Upgraded to Python 3 (tested with Python 3.12).
- **Platform:** Targeted for Ubuntu 24.04 (noble).
- **Compatibility:** Includes compatibility shims and updated install/build
	scripts to work with current packaging and system tooling.

This fork is intended for local development and experimentation. For the
original upstream project and documentation refer to the upstream repository.

---

### Quickstart (Ubuntu 24.04)

The following steps produce a development-ready environment on Ubuntu 24.04.

1. Create the runtime user (adjust `tippr` as needed):

```bash
useradd -m -s /bin/bash tippr
```

2. Clone the repository:

```bash
git clone https://github.com/acalcutt/tippr.git /opt/tippr
cd /opt/tippr
```

3. Run the installer as root, specifying the user and domain:

```bash
REDDIT_USER=tippr REDDIT_DOMAIN=tippr.local ./install-tippr.sh
```

The installer will handle system dependencies, Python virtual environment setup, database configuration, and service installation. A Python venv is created at `/home/tippr/venv`.

4. Add the domain to your hosts file (on the host machine if using a VM):

```bash
echo "127.0.0.1 tippr.local" >> /etc/hosts
```

### Configuration Options

You can customize the install by setting environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDDIT_USER` | (required) | User to run tippr as |
| `REDDIT_DOMAIN` | `tippr.local` | Domain for the site (must contain a dot) |
| `REDDIT_HOME` | `/home/$REDDIT_USER` | Base directory for install |
| `REDDIT_VENV` | `/home/$REDDIT_USER/venv` | Python virtual environment location |
| `REDDIT_PLUGINS` | `about gold` | Plugins to install |

### Notes

- If you encounter locale errors when creating the Postgres DB, run: `localedef -i en_US -f UTF-8 en_US.UTF-8`
- The domain must contain a dot (e.g., `tippr.local`) as browsers don't support cookies for dotless domains.
