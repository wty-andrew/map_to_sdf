#!/usr/bin/env python
"""Create a sdf model for use in gazebo

The created model will have the following file structure:

model_name/
├── meshes/
|   └── model_name.dae (not generated from this script but the filename is assumed)
├── model.config
└── model.sdf

For more details, see http://gazebosim.org/tutorials?tut=model_structure
"""
from typing import Union, Callable, Any
import os
import shutil
from xml.etree import ElementTree as ET
from xml.dom import minidom

SDF_VERSION = '1.6'


def prettify(xml_string: Union[str, bytes], indent_size: int = 4) -> str:
    """Return the pretty-formatted xml string."""
    indent = ' ' * indent_size
    return minidom.parseString(xml_string).toprettyxml(indent=indent)


def write_xml(filename: str, xml_element: ET.Element):
    """Output the pretty-printed xml to disk."""
    with open(filename, 'w') as f:
        f.write(prettify(ET.tostring(xml_element), indent_size=2))


def el(tag: str, **attrs: Any) -> Callable[..., ET.Element]:
    """A helper function to make building xml easier, the return function takes either
    a single string argument as text node or several sub elements as child nodes.
    """
    element = ET.Element(tag, **attrs)

    def wrapper(*children: ET.Element) -> ET.Element:
        if len(children) == 1 and isinstance(children[0], str):
            element.text = children[0]
        else:
            for child in children:
                element.append(child)
        return element

    return wrapper


def build_config(
    name: str, version: str, author: str, email: str, description: str
) -> ET.Element:
    """Create the xml for meta-data of a model."""
    # fmt: off
    xml: ET.Element = \
        el('model')(
            el('name')(name),
            el('version')(version),
            el('sdf', version=SDF_VERSION)("model.sdf"),
            el('author')(
                el('name')(author),
                el('email')(email)),
            el('description')(description))
    # fmt: on
    return xml


def build_sdf(name: str) -> ET.Element:
    """Create the xml for SDF description of a model."""
    # fmt: off
    geometry = \
        el('geometry')(
            el('mesh')(
                el('uri')(f"model://{name}/meshes/{name}.dae")))

    sdf = \
        el('sdf', version=SDF_VERSION)(
            el('model', name=name)(
                el('static')("true"),
                el('link', name="link")(
                    el('collision', name="collision")(geometry),
                    el('visual', name="visual")(geometry))))
    # fmt: on
    return sdf


def create_sdf_model(
    output_dir: str,
    name: str,
    version: str,
    author: str,
    email: str,
    description: str,
) -> None:
    """Create the model structure inside output_dir."""
    root = os.path.join(output_dir, name)
    os.makedirs(os.path.join(root, "meshes"), exist_ok=True)
    write_xml(
        os.path.join(root, "model.config"),
        build_config(name, version, author, email, description),
    )
    write_xml(os.path.join(root, "model.sdf"), build_sdf(name))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-dir', required=True)
    parser.add_argument('-n', '--name', required=True)
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('--version', default="1.0")
    parser.add_argument('--author', default="Anonymous")
    parser.add_argument('--email', default="anon@todo.todo")
    parser.add_argument('--description', default="")

    args = parser.parse_args()

    model_dir = os.path.join(args.output_dir, args.name)
    if os.path.isfile(model_dir):
        raise OSError(f'Cannot create model, "{model_dir}" exists as a file.')
    elif os.path.isdir(model_dir):
        if args.force:
            shutil.rmtree(model_dir)
        else:
            raise OSError(f'Directory "{model_dir}" already exist, use --force to overwrite.')

    create_sdf_model(
        args.output_dir,
        args.name,
        args.version,
        args.author,
        args.email,
        args.description,
    )
