# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = image_annotation_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, List, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


@dataclass
class Box:
    is_relative: bool
    left: float
    top: float
    right: float
    bottom: float

    @staticmethod
    def from_dict(obj: Any) -> 'Box':
        assert isinstance(obj, dict)
        is_relative = from_bool(obj.get("IsRelative"))
        left = from_float(obj.get("Left"))
        top = from_float(obj.get("Top"))
        right = from_float(obj.get("Right"))
        bottom = from_float(obj.get("Bottom"))
        return Box(is_relative, left, top, right, bottom)

    def to_dict(self) -> dict:
        result: dict = {}
        result["IsRelative"] = from_bool(self.is_relative)
        result["Left"] = to_float(self.left)
        result["Top"] = to_float(self.top)
        result["Right"] = to_float(self.right)
        result["Bottom"] = to_float(self.bottom)
        return result


@dataclass
class Corner:
    x: float
    y: float

    @staticmethod
    def from_dict(obj: Any) -> 'Corner':
        assert isinstance(obj, dict)
        x = from_float(obj.get("X"))
        y = from_float(obj.get("Y"))
        return Corner(x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["X"] = to_float(self.x)
        result["Y"] = to_float(self.y)
        return result


@dataclass
class Segmentation:
    is_relative: bool
    corners: List[Corner]

    @staticmethod
    def from_dict(obj: Any) -> 'Segmentation':
        assert isinstance(obj, dict)
        is_relative = from_bool(obj.get("IsRelative"))
        corners = from_list(Corner.from_dict, obj.get("Corners"))
        return Segmentation(is_relative, corners)

    def to_dict(self) -> dict:
        result: dict = {}
        result["IsRelative"] = from_bool(self.is_relative)
        result["Corners"] = from_list(lambda x: to_class(Corner, x), self.corners)
        return result


@dataclass
class Annotation:
    plate_number: str
    country: str
    annotation_class: str
    box: Box
    segmentation: Segmentation

    @staticmethod
    def from_dict(obj: Any) -> 'Annotation':
        assert isinstance(obj, dict)
        plate_number = from_str(obj.get("PlateNumber"))
        country = from_str(obj.get("Country"))
        annotation_class = from_str(obj.get("Class"))
        box = Box.from_dict(obj.get("Box"))
        segmentation = Segmentation.from_dict(obj.get("Segmentation"))
        return Annotation(plate_number, country, annotation_class, box, segmentation)

    def to_dict(self) -> dict:
        result: dict = {}
        result["PlateNumber"] = from_str(self.plate_number)
        result["Country"] = from_str(self.country)
        result["Class"] = from_str(self.annotation_class)
        result["Box"] = to_class(Box, self.box)
        result["Segmentation"] = to_class(Segmentation, self.segmentation)
        return result


@dataclass
class Size:
    width: int
    height: int

    @staticmethod
    def from_dict(obj: Any) -> 'Size':
        assert isinstance(obj, dict)
        width = from_int(obj.get("Width"))
        height = from_int(obj.get("Height"))
        return Size(width, height)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Width"] = from_int(self.width)
        result["Height"] = from_int(self.height)
        return result


@dataclass
class ImageAnnotation:
    file: str
    annotations: List[Annotation]
    size: Size

    @staticmethod
    def from_dict(obj: Any) -> 'ImageAnnotation':
        assert isinstance(obj, dict)
        file = from_str(obj.get("File"))
        annotations = from_list(Annotation.from_dict, obj.get("Annotations"))
        size = Size.from_dict(obj.get("Size"))
        return ImageAnnotation(file, annotations, size)

    def to_dict(self) -> dict:
        result: dict = {}
        result["File"] = from_str(self.file)
        result["Annotations"] = from_list(lambda x: to_class(Annotation, x), self.annotations)
        result["Size"] = to_class(Size, self.size)
        return result


def image_annotation_from_dict(s: Any) -> ImageAnnotation:
    return ImageAnnotation.from_dict(s)


def image_annotation_to_dict(x: ImageAnnotation) -> Any:
    return to_class(ImageAnnotation, x)
