#!/bin/sh

set -eu

echo "Starting Application lacrosse-tx-reader-service ..."

main()
{
    verify_configuration
    run_application
}

verify_configuration()
{
    echo "Checking configuration file ..."

    if [ -s "config.json" ]; then
        echo "[OK] Configuration file exists."
    else
        echo "Configuration file not existent. Will exit after 5 seconds."
        sleep 5
        exit 1
    fi
}

run_application()
{
    rtl_433 -q -F json -U -R 75 -R 76 -f 868240000 | ./lacrosse-tx-reader-service.py
}
