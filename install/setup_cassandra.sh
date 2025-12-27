#!/bin/bash
# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2015 reddit
# Inc. All Rights Reserved.
###############################################################################

###############################################################################
# Configure Cassandra
###############################################################################

# load configuration
RUNDIR=$(dirname $0)
source $RUNDIR/install.cfg

source /etc/lsb-release

if [ "$DISTRIB_RELEASE" == "24.04" ]; then
    ###########################################################################
    # Ubuntu 24.04 - Use cqlsh and cassandra-driver (Python 3)
    ###########################################################################

    # Create keyspace using cqlsh
    cqlsh -e "CREATE KEYSPACE IF NOT EXISTS reddit WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'};" || true

    # Create permacache table
    cqlsh -e "CREATE TABLE IF NOT EXISTS reddit.permacache (key text PRIMARY KEY, value blob);" || true

    echo "Cassandra keyspace and tables created."

else
    ###########################################################################
    # Ubuntu 14.04 - Use pycassa (Python 2)
    ###########################################################################

    # update the per-thread stack size. this used to be set to 256k in cassandra
    # version 1.2.19, but we recently downgraded to 1.2.11 where it's set too low
    sed -i -e 's/-Xss180k/-Xss256k/g' /etc/cassandra/cassandra-env.sh

    python <<END
import pycassa
sys = pycassa.SystemManager("localhost:9160")

if "reddit" not in sys.list_keyspaces():
    print "creating keyspace 'reddit'"
    sys.create_keyspace("reddit", "SimpleStrategy", {"replication_factor": "1"})
    print "done"

if "permacache" not in sys.get_keyspace_column_families("reddit"):
    print "creating column family 'permacache'"
    sys.create_column_family("reddit", "permacache")
    print "done"
END

fi
