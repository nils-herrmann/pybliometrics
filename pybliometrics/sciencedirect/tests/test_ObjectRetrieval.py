"""Test class ObjectRetrieval"""
import xml.etree.ElementTree as ET

from io import BytesIO
from PIL import Image

from pybliometrics.sciencedirect import init, ObjectRetrieval

init()

or_1 = ObjectRetrieval('S156984322300331X',
                       'gr10.jpg',
                       refresh=30)
or_2 = ObjectRetrieval('10.1016/j.rcim.2020.102086',
                       'si92.svg',
                       id_type='doi',
                       refresh=30)


def test_object():
    """Tests whether the object is a BytesIO object."""
    assert isinstance(or_1.object, BytesIO)
    assert isinstance(or_2.object, BytesIO)


def test_is_jpg():
    """Tests whether the object is a JPEG image."""
    obj_1 = or_1.object
    with Image.open(obj_1) as img:
        assert img.format.lower() == 'jpeg'


def test_is_svg():
    """Tests whether the object is an SVG image."""
    obj_2 = or_2.object
    tree = ET.parse(obj_2)
    root = tree.getroot()
    assert root.tag == '{http://www.w3.org/2000/svg}svg'
