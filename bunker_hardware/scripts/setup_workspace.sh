#!/bin/bash
# Workspace bauen
cd ../../../../..
colcon build --symlink-install
source install/setup.bash
echo "Setup abgeschlossen."
