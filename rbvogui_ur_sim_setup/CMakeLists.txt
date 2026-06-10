cmake_minimum_required(VERSION 3.8)
project(rbvogui_ur_sim_setup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  config
  dependencies
  docs
  launch
  urdf
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/rbvogui_swerve_controller.py
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES
  README.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
