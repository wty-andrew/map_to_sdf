# Quick Start
- Download [blender](https://www.blender.org/download/) (version > 2.9)
- Install dependencies
  - ` cd <path/to/blender-2.9X-linux64/2.9X/python/bin>`
  - `./python3.7m -m ensurepip`
  - `./python3.7m -m pip install numpy pyyaml Pillow`

## Standalone Usage (without ROS)
- `./scripts/map_to_sdf <path/to/blender-2.9X-linux64/blender> <map_meta_file> <output_dir>`
  - ex: `./scripts/map_to_sdf BLENDER ./maps/robocup.yaml ./models`

## Run with ROS
- Generate a model
  - Edit the arguments in `launch/map_to_sdf.launch`
  - `roslaunch map_to_sdf map_to_sdf.launch blender_executable:=<path/to/blender-2.9X-linux64/blender>`

# Notes
- Blender installed from snap store won't work since snap files are read-only ([see here](https://developer.blender.org/T83085))
- The example map is taken from the [turtlebot_simulator](https://github.com/turtlebot/turtlebot_simulator) repository
