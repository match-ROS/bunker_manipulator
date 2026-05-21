#!/bin/bash
# Verzeichnis für den Workspace erstellen
mkdir -p ~/bunker_ur16e_ws/src
cd ~/bunker_ur16e_ws/src

# Fremde Repos clonen
git clone https://github.com/agilexrobotics/ugv_sdk.git
git clone https://github.com/agilexrobotics/bunker_ros2.git

# Den Bugfix automatisch anwenden (3 Motoren -> 2 Motoren)
sed -i 's/for (int i = 0; i < 3; ++i)/for (int i = 0; i < 2; ++i)/g' ~/bunker_ur16e_ws/src/ugv_sdk/include/ugv_sdk/details/robot_base/bunker_base.hpp

# Workspace bauen
cd ~/bunker_ur16e_ws
colcon build --symlink-install
echo "Setup abgeschlossen. Bitte 'source ~/bunker_ur16e_ws/install/setup.bash' ausführen."
