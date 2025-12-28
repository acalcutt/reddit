#!/bin/bash
###############################################################################
# reddit dev environment installer
# --------------------------------
# This script installs a reddit stack suitable for development. DO NOT run this
# on a system that you use for other purposes as it might delete important
# files, truncate your databases, and otherwise do mean things to you.
#
# By default, this script will install the reddit code in the current user's
# home directory and all of its dependencies (including libraries and database
# servers) at the system level. The installed reddit will expect to be visited
# on the domain "reddit.local" unless specified otherwise.  Configuring name
# resolution for the domain is expected to be done outside the installed
# environment (e.g. in your host machine's /etc/hosts file) and is not
# something this script handles.
#
# Several configuration options (listed in the "Configuration" section below)
# are overridable with environment variables. e.g.
#
#    sudo REDDIT_DOMAIN=example.com ./install/reddit.sh
#
###############################################################################

# load configuration
RUNDIR=$(dirname $0)
source $RUNDIR/install.cfg


###############################################################################
# Sanity Checks
###############################################################################
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Must be run with root privileges."
    exit 1
fi

if [[ -z "$REDDIT_USER" ]]; then
    # in a production install, you'd want the code to be owned by root and run
    # by a less privileged user. this script is intended to build a development
    # install, so we expect the owner to run the app and not be root.
    cat <<END
ERROR: You have not specified a user. This usually means you're running this
script directly as root. It is not recommended to run reddit as the root user.

Please create a user to run reddit and set the REDDIT_USER variable
appropriately.
END
    exit 1
fi

if [[ "amd64" != $(dpkg --print-architecture) ]]; then
    cat <<END
ERROR: This host is running the $(dpkg --print-architecture) architecture!

Because of the pre-built dependencies in our PPA, and some extra picky things
like ID generation in liveupdate, installing reddit is only supported on amd64
architectures.
END
    exit 1
fi

# Check for supported Ubuntu versions
source /etc/lsb-release
if [ "$DISTRIB_ID" != "Ubuntu" ]; then
    echo "ERROR: Only Ubuntu is supported."
    exit 1
fi

# Support Ubuntu 24.04 (noble) with Python 3.12
if [ "$DISTRIB_RELEASE" != "24.04" ] && [ "$DISTRIB_RELEASE" != "14.04" ]; then
    echo "ERROR: Only Ubuntu 14.04 and 24.04 are supported."
    exit 1
fi

if [[ "2000000" -gt $(awk '/MemTotal/{print $2}' /proc/meminfo) ]]; then
    LOW_MEM_PROMPT="reddit requires at least 2GB of memory to work properly, continue anyway? [y/n] "
    read -er -n1 -p "$LOW_MEM_PROMPT" response
    if [[ "$response" != "y" ]]; then
      echo "Quitting."
      exit 1
    fi
fi

REDDIT_AVAILABLE_PLUGINS=""
for plugin in $REDDIT_PLUGINS; do
    if [ -d $REDDIT_SRC/$plugin ]; then
        if [[ -z "$REDDIT_PLUGINS" ]]; then
            REDDIT_AVAILABLE_PLUGINS+="$plugin"
        else
            REDDIT_AVAILABLE_PLUGINS+=" $plugin"
        fi
        echo "plugin $plugin found"
    else
        echo "plugin $plugin not found"
    fi
done

###############################################################################
# Install prerequisites
###############################################################################

# install primary packages
$RUNDIR/install_apt.sh

# install cassandra from datastax
$RUNDIR/install_cassandra.sh

# install zookeeper
$RUNDIR/install_zookeeper.sh

# install services (rabbitmq, postgres, memcached, etc.)
$RUNDIR/install_services.sh

###############################################################################
# Install the reddit source repositories
###############################################################################
if [ ! -d $REDDIT_SRC ]; then
    mkdir -p $REDDIT_SRC
    chown $REDDIT_USER $REDDIT_SRC
fi

function copy_upstart {
    if [ -d ${1}/upstart ]; then
        # Prefer Upstart directory if present (older Ubuntu), otherwise
        # place the files in /etc/init.d so they are available on systemd
        # hosts for later conversion or wrapper usage.
        if [ -d /etc/init ]; then
            cp ${1}/upstart/* /etc/init/
        else
            mkdir -p /etc/init.d
            cp ${1}/upstart/* /etc/init.d/
            # Make copied files executable so they can be used as simple
            # wrappers or inspected by administrators.
            chmod +x /etc/init.d/* || true
        fi
    fi
}

function clone_reddit_repo {
    local destination=$REDDIT_SRC/${1}
    local repository_url=https://github.com/${2}.git

    if [ ! -d $destination ]; then
        sudo -u $REDDIT_USER -H git clone $repository_url $destination
    fi

    copy_upstart $destination
}

function clone_reddit_service_repo {
    clone_reddit_repo $1 reddit/reddit-service-$1
}

clone_reddit_repo reddit acalcutt/reddit
clone_reddit_repo i18n reddit/reddit-i18n
clone_reddit_service_repo websockets
clone_reddit_service_repo activity

# Patch activity and websockets setup.py to use new baseplate module path
# (baseplate.integration was renamed to baseplate.frameworks in baseplate 1.0)
for repo in activity websockets; do
    if [ -f "$REDDIT_SRC/$repo/setup.py" ]; then
        sed -i 's/baseplate\.integration\./baseplate.frameworks./g' "$REDDIT_SRC/$repo/setup.py"
    fi
done

# (legacy) i18n Python 2 conversion will run after the virtualenv is created

###############################################################################
# Configure Services
###############################################################################

# Configure Cassandra
$RUNDIR/setup_cassandra.sh

# Configure PostgreSQL
$RUNDIR/setup_postgres.sh

# Configure mcrouter
$RUNDIR/setup_mcrouter.sh

# Configure RabbitMQ
$RUNDIR/setup_rabbitmq.sh

###############################################################################
# Install and configure the reddit code
###############################################################################

# Create Python virtual environment for reddit
# This avoids PEP 668 issues and keeps dependencies isolated
echo "Creating Python virtual environment at $REDDIT_VENV"
sudo -u $REDDIT_USER python3 -m venv $REDDIT_VENV

# Create 'python' symlink for compatibility with Makefiles that expect 'python'
sudo -u $REDDIT_USER ln -sf python3 $REDDIT_VENV/bin/python

# Upgrade pip and install build tools in venv
sudo -u $REDDIT_USER $REDDIT_VENV/bin/pip install --upgrade pip setuptools wheel

# Install baseplate and other runtime dependencies
sudo -u $REDDIT_USER $REDDIT_VENV/bin/pip install \
    baseplate \
    gunicorn \
    PasteScript \
    pyramid-mako \
    Paste \
    PasteDeploy \
    pylibmc \
    simplejson \
    pytz \
    pytest \
    Babel \
    Cython \
    raven

# Additional packages that `r2` currently lists as runtime/test deps.
# Install them into the venv as the reddit user. Some packages require
# system libs (e.g. libpq-dev, libxml2-dev); failures will be reported
# but won't abort the installer.
sudo -u $REDDIT_USER $REDDIT_VENV/bin/pip install \
    amqp \
    bcrypt \
    beautifulsoup4 \
    captcha \
    cassandra-driver \
    chardet \
    httpagentparser \
    kazoo \
    lxml \
    stripe \
    tinycss2 \
    unidecode \
    PyYAML \
    Pillow \
    python-snappy \
    pylibmc \
    webtest \
    mock \
    nose \
    coverage \
    "snudown @ https://github.com/nicnacnic/snudown/archive/refs/heads/master.zip" || true

# Prefer psycopg2-binary to avoid requiring system postgres headers during
# install; if you need the real psycopg2 build from source, install
# libpq-dev and python3-dev on the host instead.
sudo -u $REDDIT_USER $REDDIT_VENV/bin/pip install psycopg2-binary || true

# Convert legacy Python 2 sources in i18n to Python 3 using lib2to3
if [ -d "$REDDIT_SRC/i18n" ]; then
    echo "Converting i18n Python files to Python 3 with lib2to3"
    for pyf in $(find "$REDDIT_SRC/i18n" -name "*.py"); do
        sudo -u $REDDIT_USER PATH="$REDDIT_VENV/bin:$PATH" python3 -m lib2to3 -w "$pyf" || true
    done
fi

function install_reddit_repo {
    pushd $REDDIT_SRC/$1
    sudo -u $REDDIT_USER $REDDIT_VENV/bin/python setup.py build
    # --no-build-isolation uses the venv's packages (like baseplate) instead of isolated env
    sudo -u $REDDIT_USER $REDDIT_VENV/bin/pip install --no-build-isolation -e .
    popd
}

install_reddit_repo reddit/r2
# Only install the external `i18n` package if its setup.py contains a
# valid version string. Some historical `i18n` checkouts have an empty
# version which breaks modern packaging tools; in that case skip the
# install and rely on local compatibility shims in the tree.
# Ensure i18n is installed; if its setup.py lacks a version, inject a
# minimal default to satisfy modern packaging tools.
if [ -f "$REDDIT_SRC/i18n/setup.py" ]; then
    if ! grep -Eq "version\s*=\s*['\"][^'\"]+['\"]" "$REDDIT_SRC/i18n/setup.py"; then
        echo "Patching i18n/setup.py to add default version 0.0.1"
        # Backup original for debugging
        cp "$REDDIT_SRC/i18n/setup.py" "$REDDIT_SRC/i18n/setup.py.orig" || true
        # Replace with a minimal, safe setup.py to avoid legacy packaging issues
        cat > "$REDDIT_SRC/i18n/setup.py" <<'PYSETUP'
from setuptools import setup, find_packages

setup(
    name='i18n',
    version='0.0.1',
    packages=find_packages(),
)
PYSETUP
    fi
    install_reddit_repo i18n
else
    echo "i18n checkout not present; skipping i18n install"
    SKIP_I18N=1
fi
for plugin in $REDDIT_AVAILABLE_PLUGINS; do
    copy_upstart $REDDIT_SRC/$plugin
    install_reddit_repo $plugin
done
install_reddit_repo websockets
install_reddit_repo activity

# generate binary translation files from source
if [ "${SKIP_I18N}" != "1" ]; then
    # Use venv's python for make commands
    sudo -u $REDDIT_USER PATH="$REDDIT_VENV/bin:$PATH" make -C $REDDIT_SRC/i18n clean all
else
    echo "Skipping i18n message compilation because i18n package was not installed"
fi

# this builds static files and should be run *after* languages are installed
# so that the proper language-specific static files can be generated and after
# plugins are installed so all the static files are available.
pushd $REDDIT_SRC/reddit/r2
# Use venv's python for make commands
sudo -u $REDDIT_USER PATH="$REDDIT_VENV/bin:$PATH" PYTHONPATH="$REDDIT_SRC/reddit:$REDDIT_SRC" make clean pyx

plugin_str=$(echo -n "$REDDIT_AVAILABLE_PLUGINS" | tr " " ,)
if [ ! -f development.update ]; then
    cat > development.update <<DEVELOPMENT
# after editing this file, run "make ini" to
# generate a new development.ini

[DEFAULT]
# global debug flag -- displays pylons stacktrace rather than 500 page on error when true
# WARNING: a pylons stacktrace allows remote code execution. Make sure this is false
# if your server is publicly accessible.
debug = true

disable_ads = true
disable_captcha = true
disable_ratelimit = true
disable_require_admin_otp = true

domain = $REDDIT_DOMAIN
oauth_domain = $REDDIT_DOMAIN

plugins = $plugin_str

media_provider = filesystem
media_fs_root = /srv/www/media
media_fs_base_url_http = http://%(domain)s/media/

[server:main]
port = 8001
DEVELOPMENT
    chown $REDDIT_USER development.update
else
    sed -i "s/^plugins = .*$/plugins = $plugin_str/" $REDDIT_SRC/reddit/r2/development.update
    sed -i "s/^domain = .*$/domain = $REDDIT_DOMAIN/" $REDDIT_SRC/reddit/r2/development.update
    sed -i "s/^oauth_domain = .*$/oauth_domain = $REDDIT_DOMAIN/" $REDDIT_SRC/reddit/r2/development.update
fi

sudo -u $REDDIT_USER PATH="$REDDIT_VENV/bin:$PATH" PYTHONPATH="$REDDIT_SRC/reddit:$REDDIT_SRC" make ini || true

# Ensure `development.ini` exists. If `make ini` didn't create it (CI or
# permission issues), try generating it directly with `updateini.py`.
if [ ! -f development.ini ]; then
    echo "development.ini not found; attempting to generate with updateini.py"
    sudo -u $REDDIT_USER PATH="$REDDIT_VENV/bin:$PATH" PYTHONPATH="$REDDIT_SRC/reddit:$REDDIT_SRC" \
        python updateini.py example.ini development.update > development.ini || true
fi

# Ensure run.ini is a symlink to a real ini. Prefer development.ini, fall
# back to example.ini if generation failed.
if [ -f development.ini ]; then
    # Create a real file (not a symlink) to avoid broken-link surprises in CI
    sudo -u $REDDIT_USER cp -f development.ini run.ini
    sudo -u $REDDIT_USER chown $REDDIT_USER run.ini || true
else
    echo "Falling back to example.ini for run.ini (development.ini missing)"
    sudo -u $REDDIT_USER cp -f example.ini run.ini
    sudo -u $REDDIT_USER chown $REDDIT_USER run.ini || true
fi

popd

###############################################################################
# some useful helper scripts
###############################################################################
function helper-script() {
    cat > $1
    chmod 755 $1
}

# Create a Python script for reddit-run that bypasses paster's plugin discovery
cat > $REDDIT_VENV/bin/reddit-run-cmd <<PYCMD
#!/usr/bin/env python3
"""Direct invocation of r2's RunCommand, bypassing paster plugin discovery."""
import sys
import os

# Add reddit repo root to Python path for local shims (e.g., pylons)
# This must come before site-packages so local shims take precedence
reddit_root = '$REDDIT_SRC/reddit'
r2_dir = reddit_root + '/r2'
sys.path.insert(0, reddit_root)
sys.path.insert(0, r2_dir)
os.chdir(r2_dir)

from r2.commands import RunCommand
cmd = RunCommand('run')
# Args: config file + any additional args
cmd.run(sys.argv[1:])
PYCMD
chmod +x $REDDIT_VENV/bin/reddit-run-cmd

helper-script /usr/local/bin/reddit-run <<REDDITRUN
#!/bin/bash
# Direct invocation of r2 RunCommand
cd $REDDIT_SRC/reddit/r2
exec $REDDIT_VENV/bin/python $REDDIT_VENV/bin/reddit-run-cmd run.ini "\$@"
REDDITRUN

helper-script /usr/local/bin/reddit-shell <<REDDITSHELL
#!/bin/bash
# Use paster shell command
cd $REDDIT_SRC/reddit/r2
exec $REDDIT_VENV/bin/paster shell run.ini
REDDITSHELL

helper-script /usr/local/bin/reddit-start <<REDDITSTART
#!/bin/bash
initctl emit reddit-start
REDDITSTART

helper-script /usr/local/bin/reddit-stop <<REDDITSTOP
#!/bin/bash
initctl emit reddit-stop
REDDITSTOP

helper-script /usr/local/bin/reddit-restart <<REDDITRESTART
#!/bin/bash
initctl emit reddit-restart TARGET=${1:-all}
REDDITRESTART

helper-script /usr/local/bin/reddit-flush <<REDDITFLUSH
#!/bin/bash
echo flush_all | nc localhost 11211
REDDITFLUSH

helper-script /usr/local/bin/reddit-serve <<REDDITSERVE
#!/bin/bash
cd $REDDIT_SRC/reddit/r2
exec $REDDIT_VENV/bin/paster serve --reload run.ini
REDDITSERVE

###############################################################################
# pixel and click server
###############################################################################
mkdir -p /var/opt/reddit/
chown $REDDIT_USER:$REDDIT_GROUP /var/opt/reddit/

mkdir -p /srv/www/pixel
chown $REDDIT_USER:$REDDIT_GROUP /srv/www/pixel
cp $REDDIT_SRC/reddit/r2/r2/public/static/pixel.png /srv/www/pixel

if [ ! -d /etc/gunicorn.d ]; then
    mkdir -p /etc/gunicorn.d
fi
if [ ! -f /etc/gunicorn.d/click.conf ]; then
    cat > /etc/gunicorn.d/click.conf <<CLICK
CONFIG = {
    "mode": "wsgi",
    "working_dir": "$REDDIT_SRC/reddit/scripts",
    "user": "$REDDIT_USER",
    "group": "$REDDIT_USER",
    "python": "$REDDIT_VENV/bin/python",
    "args": (
        "--bind=unix:/var/opt/reddit/click.sock",
        "--workers=1",
        "tracker:application",
    ),
}
CLICK
fi

# Create a per-app systemd service for the click server so it can be managed
# under systemd on modern systems. Only create/enable when systemd is present.
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    cat > /etc/systemd/system/gunicorn-click.service <<UNIT
[Unit]
Description=Gunicorn click server for reddit
After=network.target

[Service]
Type=simple
User=$REDDIT_USER
Group=$REDDIT_GROUP
WorkingDirectory=$REDDIT_SRC/reddit/scripts
Environment=PATH=$REDDIT_VENV/bin
ExecStart=$REDDIT_VENV/bin/gunicorn --bind unix:/var/opt/reddit/click.sock --workers=1 tracker:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload || true
    systemctl enable --now gunicorn-click.service || true
fi

###############################################################################
# nginx
###############################################################################

mkdir -p /srv/www/media
chown $REDDIT_USER:$REDDIT_GROUP /srv/www/media

cat > /etc/nginx/sites-available/reddit-media <<MEDIA
server {
    listen 9000;

    expires max;

    location /media/ {
        alias /srv/www/media/;
    }
}
MEDIA

cat > /etc/nginx/sites-available/reddit-pixel <<PIXEL
upstream click_server {
  server unix:/var/opt/reddit/click.sock fail_timeout=0;
}

server {
  listen 8082;
    access_log      /var/log/nginx/traffic/traffic.log directlog;

  location / {

    rewrite ^/pixel/of_ /pixel.png;

    add_header Last-Modified "";
    add_header Pragma "no-cache";

    expires -1;
    root /srv/www/pixel/;
  }

  location /click {
    proxy_pass http://click_server;
  }
}
PIXEL

cat > /etc/nginx/sites-available/reddit-ssl <<SSL
map \$http_upgrade \$connection_upgrade {
  default upgrade;
  ''      close;
}

server {
    listen 443;

    ssl on;
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;

    ssl_session_cache shared:SSL:1m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$http_host;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_pass_header Server;

        # allow websockets through if desired
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
    }
}
SSL

# remove the default nginx site that may conflict with haproxy
rm -rf /etc/nginx/sites-enabled/default
# put our config in place
ln -nsf /etc/nginx/sites-available/reddit-media /etc/nginx/sites-enabled/
ln -nsf /etc/nginx/sites-available/reddit-pixel /etc/nginx/sites-enabled/
ln -nsf /etc/nginx/sites-available/reddit-ssl /etc/nginx/sites-enabled/

# make the pixel log directory
mkdir -p /var/log/nginx/traffic

# Ensure the custom log_format is defined in the http context (conf.d)
cat > /etc/nginx/conf.d/reddit-log.conf <<'LOGCONF'
log_format directlog '$remote_addr - $remote_user [$time_local] '
                   '"$request_method $request_uri $server_protocol" $status $body_bytes_sent '
                   '"$http_referer" "$http_user_agent"';
LOGCONF

# link the ini file for the Flask click tracker
ln -nsf $REDDIT_SRC/reddit/r2/development.ini $REDDIT_SRC/reddit/scripts/production.ini

service nginx restart

###############################################################################
# haproxy
###############################################################################
if [ -e /etc/haproxy/haproxy.cfg ]; then
    BACKUP_HAPROXY=$(mktemp /etc/haproxy/haproxy.cfg.XXX)
    echo "Backing up /etc/haproxy/haproxy.cfg to $BACKUP_HAPROXY"
    cat /etc/haproxy/haproxy.cfg > $BACKUP_HAPROXY
fi

# make sure haproxy is enabled
cat > /etc/default/haproxy <<DEFAULT
ENABLED=1
DEFAULT

# configure haproxy
cat > /etc/haproxy/haproxy.cfg <<HAPROXY
global
    maxconn 350

frontend frontend
    mode http

    bind 0.0.0.0:80
    bind 127.0.0.1:8080

    timeout client 24h
    option forwardfor except 127.0.0.1
    option httpclose

    # ensure X-Forwarded-Proto is set to 'https' when requests arrive via TLS
    http-request del-header X-Forwarded-Proto
    acl is-ssl dst_port 8080
    http-request add-header X-Forwarded-Proto https if is-ssl

    # send websockets to the websocket service
    acl is-websocket hdr(Upgrade) -i WebSocket
    use_backend websockets if is-websocket

    # send media stuff to the local nginx
    acl is-media path_beg /media/
    use_backend media if is-media

    # send pixel stuff to local nginx
    acl is-pixel path_beg /pixel/
    acl is-click path_beg /click
    use_backend pixel if is-pixel || is-click

    default_backend reddit

backend reddit
    mode http
    timeout connect 4000
    timeout server 30000
    timeout queue 60000
    balance roundrobin

    server app01-8001 localhost:8001 maxconn 30

backend websockets
    mode http
    timeout connect 4s
    timeout server 24h
    balance roundrobin

    server websockets localhost:9001 maxconn 250

backend media
    mode http
    timeout connect 4000
    timeout server 30000
    timeout queue 60000
    balance roundrobin

    server nginx localhost:9000 maxconn 20

backend pixel
    mode http
    timeout connect 4000
    timeout server 30000
    timeout queue 60000
    balance roundrobin

    server nginx localhost:8082 maxconn 20
HAPROXY

# this will start it even if currently stopped
service haproxy restart

###############################################################################
# websocket service
###############################################################################
 
# Only install Upstart jobs if /etc/init exists (do not create it)
if [ -d /etc/init ]; then
    if [ ! -f /etc/init/reddit-websockets.conf ]; then
        cat > /etc/init/reddit-websockets.conf << UPSTART_WEBSOCKETS
description "websockets service"

stop on runlevel [!2345] or reddit-restart all or reddit-restart websockets
start on runlevel [2345] or reddit-restart all or reddit-restart websockets

respawn
respawn limit 10 5
kill timeout 15

limit nofile 65535 65535

exec $REDDIT_VENV/bin/baseplate-serve2 --bind localhost:9001 $REDDIT_SRC/websockets/example.ini
UPSTART_WEBSOCKETS
    fi
fi

# Create a systemd unit for websockets (preferred on modern systems)
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    cat > /etc/systemd/system/reddit-websockets.service <<UNIT
[Unit]
Description=Reddit Websockets Service
After=network.target

[Service]
Type=simple
User=$REDDIT_USER
Group=$REDDIT_GROUP
WorkingDirectory=$REDDIT_SRC/websockets
Environment=PATH=$REDDIT_VENV/bin
ExecStart=$REDDIT_VENV/bin/baseplate-serve2 --bind localhost:9001 $REDDIT_SRC/websockets/example.ini
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload || true
    systemctl enable --now reddit-websockets.service || service reddit-websockets restart || true
fi

###############################################################################
# activity service
###############################################################################

# Only install Upstart jobs if /etc/init exists (do not create it)
if [ -d /etc/init ]; then
    if [ ! -f /etc/init/reddit-activity.conf ]; then
        cat > /etc/init/reddit-activity.conf << UPSTART_ACTIVITY
description "activity service"

stop on runlevel [!2345] or reddit-restart all or reddit-restart activity
start on runlevel [2345] or reddit-restart all or reddit-restart activity

respawn
respawn limit 10 5
kill timeout 15

exec $REDDIT_VENV/bin/baseplate-serve2 --bind localhost:9002 $REDDIT_SRC/activity/example.ini
UPSTART_ACTIVITY
    fi
fi

# Create a systemd unit for activity service
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    cat > /etc/systemd/system/reddit-activity.service <<UNIT
[Unit]
Description=Reddit Activity Service
After=network.target

[Service]
Type=simple
User=$REDDIT_USER
Group=$REDDIT_GROUP
WorkingDirectory=$REDDIT_SRC/activity
Environment=PATH=$REDDIT_VENV/bin
ExecStart=$REDDIT_VENV/bin/baseplate-serve2 --bind localhost:9002 $REDDIT_SRC/activity/example.ini
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload || true
    systemctl enable --now reddit-activity.service || service reddit-activity restart || true
fi

###############################################################################
# geoip service
###############################################################################
if [ ! -f /etc/gunicorn.d/geoip.conf ]; then
    cat > /etc/gunicorn.d/geoip.conf <<GEOIP
CONFIG = {
    "mode": "wsgi",
    "working_dir": "$REDDIT_SRC/reddit/scripts",
    "user": "$REDDIT_USER",
    "group": "$REDDIT_USER",
    "python": "$REDDIT_VENV/bin/python",
    "args": (
        "--bind=127.0.0.1:5000",
        "--workers=1",
         "--limit-request-line=8190",
         "geoip_service:application",
    ),
}
GEOIP
fi

# Create a per-app systemd service for the geoip server
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    cat > /etc/systemd/system/gunicorn-geoip.service <<UNIT
[Unit]
Description=Gunicorn geoip server for reddit
After=network.target

[Service]
Type=simple
User=$REDDIT_USER
Group=$REDDIT_GROUP
WorkingDirectory=$REDDIT_SRC/reddit/scripts
Environment=PATH=$REDDIT_VENV/bin
ExecStart=$REDDIT_VENV/bin/gunicorn --bind 127.0.0.1:5000 --workers=1 --limit-request-line=8190 geoip_service:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

    systemctl daemon-reload || true
    systemctl enable --now gunicorn-geoip.service || true
fi

###############################################################################
# Job Environment
###############################################################################
CONSUMER_CONFIG_ROOT=$REDDIT_HOME/consumer-count.d

if [ ! -f /etc/default/reddit ]; then
    cat > /etc/default/reddit <<DEFAULT
export REDDIT_ROOT=$REDDIT_SRC/reddit/r2
export REDDIT_INI=$REDDIT_SRC/reddit/r2/run.ini
export REDDIT_USER=$REDDIT_USER
export REDDIT_GROUP=$REDDIT_GROUP
export REDDIT_CONSUMER_CONFIG=$CONSUMER_CONFIG_ROOT
alias wrap-job=$REDDIT_SRC/reddit/scripts/wrap-job
alias manage-consumers=$REDDIT_SRC/reddit/scripts/manage-consumers
DEFAULT
fi

###############################################################################
# Queue Processors
###############################################################################
mkdir -p $CONSUMER_CONFIG_ROOT

function set_consumer_count {
    if [ ! -f $CONSUMER_CONFIG_ROOT/$1 ]; then
        echo $2 > $CONSUMER_CONFIG_ROOT/$1
    fi
}

set_consumer_count search_q 0
set_consumer_count del_account_q 1
set_consumer_count scraper_q 1
set_consumer_count markread_q 1
set_consumer_count commentstree_q 1
set_consumer_count newcomments_q 1
set_consumer_count vote_link_q 1
set_consumer_count vote_comment_q 1
set_consumer_count automoderator_q 0
set_consumer_count butler_q 1
set_consumer_count author_query_q 1
set_consumer_count subreddit_query_q 1
set_consumer_count domain_query_q 1

chown -R $REDDIT_USER:$REDDIT_GROUP $CONSUMER_CONFIG_ROOT/

###############################################################################
# Complete plugin setup, if setup.sh exists
###############################################################################
for plugin in $REDDIT_AVAILABLE_PLUGINS; do
    if [ -x $REDDIT_SRC/$plugin/setup.sh ]; then
        echo "Found setup.sh for $plugin; running setup script"
        $REDDIT_SRC/$plugin/setup.sh $REDDIT_SRC $REDDIT_USER
    fi
done

###############################################################################
# Start everything up
###############################################################################

# the initial database setup should be done by one process rather than a bunch
# vying with eachother to get there first
reddit-run -c 'print("ok done")'

# ok, now start everything else up
initctl emit reddit-stop
initctl emit reddit-start

###############################################################################
# Cron Jobs
###############################################################################
if [ ! -f /etc/cron.d/reddit ]; then
    cat > /etc/cron.d/reddit <<CRON
0    3 * * * root /sbin/start --quiet reddit-job-update_sr_names
30  16 * * * root /sbin/start --quiet reddit-job-update_reddits
0    * * * * root /sbin/start --quiet reddit-job-update_promos
*/5  * * * * root /sbin/start --quiet reddit-job-clean_up_hardcache
*/2  * * * * root /sbin/start --quiet reddit-job-broken_things
*/2  * * * * root /sbin/start --quiet reddit-job-rising
0    * * * * root /sbin/start --quiet reddit-job-trylater

# liveupdate
*    * * * * root /sbin/start --quiet reddit-job-liveupdate_activity

# jobs that recalculate time-limited listings (e.g. top this year)
PGPASSWORD=password
*/15 * * * * $REDDIT_USER $REDDIT_SRC/reddit/scripts/compute_time_listings link year "['hour', 'day', 'week', 'month', 'year']"
*/15 * * * * $REDDIT_USER $REDDIT_SRC/reddit/scripts/compute_time_listings comment year "['hour', 'day', 'week', 'month', 'year']"

# disabled by default, uncomment if you need these jobs
#*    * * * * root /sbin/start --quiet reddit-job-email
#0    0 * * * root /sbin/start --quiet reddit-job-update_gold_users
CRON
fi

###############################################################################
# Finished with install script
###############################################################################
# print this out here. if vagrant's involved, it's gonna do more steps
# afterwards and then re-run this script but that's ok.
$RUNDIR/done.sh
