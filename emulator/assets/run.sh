#!/bin/sh
if [ "$1" = "install" ]; then
    {{install_command}}
else
    {{run_command}}
fi
