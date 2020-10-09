#!/bin/sh

set -eux

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
    echo "Starting rtl_433 and piping output to lacrosse-tx-reader-service ..."

    rtl_433 -F json -M utc -R 75 -R 76 -f 868240000 -Y classic -s 250k | python3 -u ./lacrosse-tx-reader-service.py
}

main
