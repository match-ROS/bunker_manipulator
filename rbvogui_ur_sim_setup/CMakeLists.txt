cmake_minimum_required(VERSION 3.8)
project(rbvogui_ur_sim_setup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  dependencies
  docs
  DESTINATION share/${PROJECT_NAME}
)

install(FILES
  README.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
