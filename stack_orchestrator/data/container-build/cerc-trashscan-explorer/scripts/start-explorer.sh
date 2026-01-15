#!/usr/bin/env bash
set -e

if [ -n "$CERC_SCRIPT_DEBUG" ]; then
    set -x
fi

echo "TrashScan Explorer starting..."

# Wait for database to be ready
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."

    # Parse DATABASE_URL: postgres://user:pass@host:port/db
    DB_HOST=$(echo $DATABASE_URL | sed -e 's|.*@||' -e 's|:.*||' -e 's|/.*||')
    DB_PORT=$(echo $DATABASE_URL | sed -e 's|.*@[^:]*:||' -e 's|/.*||')

    if [ -z "$DB_PORT" ] || [ "$DB_PORT" = "$DB_HOST" ]; then
        DB_PORT=5432
    fi

    timeout=60
    counter=0
    until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
        counter=$((counter + 1))
        if [ $counter -ge $timeout ]; then
            echo "Error: Database not available after ${timeout} seconds"
            exit 1
        fi
        echo "Waiting for database at ${DB_HOST}:${DB_PORT}... ($counter/$timeout)"
        sleep 1
    done
    echo "Database is available!"
fi

# Run database migrations if needed
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Running database migrations..."
    npx drizzle-kit push --config=drizzle.config.ts 2>&1 || echo "Migration warning (tables may already exist), continuing..."
fi

# Start the application
echo "Starting TrashScan Explorer on port ${PORT:-5000}..."
exec node dist/index.js
