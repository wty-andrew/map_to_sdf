"""Generate the map model mesh file with blender from ROS map files
The map file format can be found from http://wiki.ros.org/map_server
"""
from typing import Optional, Sequence
import os
from operator import itemgetter

import numpy as np
import yaml
from PIL import Image

import bpy

# General utils
def get_filename(path: str) -> str:
    """Return only the filename without extension from the given path."""
    return os.path.splitext(os.path.basename(path))[0]


def read_img(path: str) -> np.ndarray:
    """Read the image in grayscale into a numpy array."""
    return np.asarray(Image.open(path).convert("L"))


# Blender utils
def remove_default_cube() -> None:
    """Remove the default cube if it exists."""
    bpy.ops.object.select_all(action='DESELECT')
    cube: Optional[bpy.types.Object] = bpy.data.objects.get('Cube')
    if cube is not None:
        cube.select_set(True)
        bpy.ops.object.delete()


def export_dae(filepath: str, *objects: bpy.types.Object) -> None:
    """Export the objects in collada format."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.wm.collada_export(filepath=filepath, selected=True)


# ROS utils
def make_binary_grid(
    grid: np.ndarray, threshold: float, negate: bool = False
) -> np.ndarray:
    """Convert the occupancy grid into boolean grid by the threshold value, negate
    determines if the free/occupied semantics should be reversed.
    """
    if not negate:
        grid = 255 - grid
    return (grid / 255) > threshold


def read_map(map_meta_path: str) -> dict:
    """Read the map meta as a dict, the image field is replaced with the loaded img
    array transformed into binary grid."""
    with open(map_meta_path, "r") as f:
        meta = yaml.load(f, yaml.SafeLoader)

    img_array = read_img(os.path.join(os.path.dirname(map_meta_path), meta['image']))
    grid = make_binary_grid(img_array, meta['occupied_thresh'], meta['negate'])
    return dict(meta, image=grid)


# Model construction
def create_wall(
    grid: np.ndarray,
    thickness: float,
    height: float,
    origin: Sequence[float] = (0, 0, 0),  # (x, y, theta)
) -> bpy.types.Object:
    """Return the created wall object from the given grid."""
    # create the wall object and add it to the scene
    h, w = grid.shape
    verts, faces = [], []
    for y in range(h + 1):
        for x in range(w + 1):
            verts.append((x, y, 0))
            if y < h and x < w and grid[y][x]:
                bottom_left = x + (w + 1) * y
                top_left = bottom_left + w + 1
                top_right, bottom_right = top_left + 1, bottom_left + 1
                faces.append([bottom_left, bottom_right, top_right, top_left])

    mesh = bpy.data.meshes.new(name="Wall")
    mesh.from_pydata(verts, [], faces)
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection = bpy.data.collections.get('Collection')
    collection.objects.link(obj)

    # activate the object for following operations
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # remove redundant geometry
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    # model transformation (according to origin, thickness, and height)
    bpy.ops.transform.resize(value=(thickness, thickness, 1))
    origin_x, origin_y, origin_theta = origin
    if origin_x or origin_y:
        bpy.ops.transform.translate(value=(origin_x, origin_y, 0))
    if origin_theta:
        bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
        bpy.ops.transform.rotate(value=origin_theta, orient_axis='Z')

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, height)})
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj


def create_mesh(map_meta_file: str, output_path: str, wall_height: float) -> None:
    grid, resolution, origin = itemgetter('image', 'resolution', 'origin')(
        read_map(map_meta_file)
    )

    remove_default_cube()
    wall = create_wall(
        np.flipud(grid),  # y-axis in blender points from bottom to top
        thickness=resolution,
        origin=origin,
        height=wall_height,
    )
    export_dae(output_path, wall)


if __name__ == "__main__":
    import sys
    import argparse

    argv = sys.argv
    argv = argv[argv.index('--') + 1 :]
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-map-meta', required=True)
    parser.add_argument('-o', '--output-dir', required=True)
    parser.add_argument('--wall-height', type=float, default=2)

    args = parser.parse_args(argv)

    output = os.path.join(args.output_dir, f"{get_filename(args.input_map_meta)}.dae")
    create_mesh(args.input_map_meta, output, args.wall_height)
