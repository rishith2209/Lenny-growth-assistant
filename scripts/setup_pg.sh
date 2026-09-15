#!/bin/bash
set -e
sed -i "s/port = 5432/port = 5433/" /etc/postgresql/18/main/postgresql.conf
cat << "EOF" > /etc/postgresql/18/main/pg_hba.conf
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               trust
host    all             all             ::/0                    trust
EOF

service postgresql restart
su - postgres -c "psql -p 5433 -c \"ALTER USER postgres WITH PASSWORD 'postgres';\""
su - postgres -c "createdb -p 5433 lenny_growth" || true
su - postgres -c "psql -p 5433 -d lenny_growth -c \"CREATE EXTENSION IF NOT EXISTS vector;\""
echo "POSTGRESQL_PORT_5433_READY"
