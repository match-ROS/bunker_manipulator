cmake_minimum_required(VERSION 3.8)
project(my_robot_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# --- NEU: Hier installieren wir die einzelne model.config Datei ---
install(FILES
  model.config
  DESTINATION share/${PROJECT_NAME}
)
# ------------------------------------------------------------------

install(DIRECTORY
  config
  launch
  urdf
  meshes
  DESTINATION share/${PROJECT_NAME}
)

# Install python executables
install(PROGRAMS
  scripts/robot_description_publisher.py
  scripts/diff_drive_converter.py
  scripts/wheel_force_applier.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
