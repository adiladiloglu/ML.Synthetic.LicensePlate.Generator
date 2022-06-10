# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = country_configuration_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, List, Optional, TypeVar, Callable, Type, cast
from enum import Enum

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


@dataclass
class Color:
    r: int
    g: int
    b: int

    @staticmethod
    def from_dict(obj: Any) -> 'Color':
        assert isinstance(obj, dict)
        r = from_int(obj.get("R"))
        g = from_int(obj.get("G"))
        b = from_int(obj.get("B"))
        return Color(r, g, b)

    def to_dict(self) -> dict:
        result: dict = {}
        result["R"] = from_int(self.r)
        result["G"] = from_int(self.g)
        result["B"] = from_int(self.b)
        return result


@dataclass
class Font:
    size: int
    file: str

    @staticmethod
    def from_dict(obj: Any) -> 'Font':
        assert isinstance(obj, dict)
        size = from_int(obj.get("Size"))
        file = from_str(obj.get("File"))
        return Font(size, file)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Size"] = from_int(self.size)
        result["File"] = from_str(self.file)
        return result


@dataclass
class Area:
    x: int
    y: int
    height: int
    width: int

    @staticmethod
    def from_dict(obj: Any) -> 'Area':
        assert isinstance(obj, dict)
        x = from_int(obj.get("X"))
        y = from_int(obj.get("Y"))
        height = from_int(obj.get("Height"))
        width = from_int(obj.get("Width"))
        return Area(x, y, height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["X"] = from_int(self.x)
        result["Y"] = from_int(self.y)
        result["Height"] = from_int(self.height)
        result["Width"] = from_int(self.width)
        return result


@dataclass
class Part:
    probability: float
    options: List[str]

    @staticmethod
    def from_dict(obj: Any) -> 'Part':
        assert isinstance(obj, dict)
        probability = from_float(obj.get("Probability"))
        options = from_list(from_str, obj.get("Options"))
        return Part(probability, options)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Probability"] = to_float(self.probability)
        result["Options"] = from_list(from_str, self.options)
        return result


class TypeEnum(Enum):
    SEAL = "Seal"
    TEXT = "Text"


@dataclass
class Drawable:
    type: TypeEnum
    parts: List[Part]
    offset: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Drawable':
        assert isinstance(obj, dict)
        type = TypeEnum(obj.get("Type"))
        parts = from_list(Part.from_dict, obj.get("Parts"))
        offset = from_union([from_int, from_none], obj.get("Offset"))
        return Drawable(type, parts, offset)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Type"] = to_enum(TypeEnum, self.type)
        result["Parts"] = from_list(lambda x: to_class(Part, x), self.parts)
        result["Offset"] = from_union([from_int, from_none], self.offset)
        return result


@dataclass
class Line:
    area: Area
    drawables: List[Drawable]

    @staticmethod
    def from_dict(obj: Any) -> 'Line':
        assert isinstance(obj, dict)
        area = Area.from_dict(obj.get("Area"))
        drawables = from_list(Drawable.from_dict, obj.get("Drawables"))
        return Line(area, drawables)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Area"] = to_class(Area, self.area)
        result["Drawables"] = from_list(lambda x: to_class(Drawable, x), self.drawables)
        return result


@dataclass
class Size:
    height: int
    width: int

    @staticmethod
    def from_dict(obj: Any) -> 'Size':
        assert isinstance(obj, dict)
        height = from_int(obj.get("Height"))
        width = from_int(obj.get("Width"))
        return Size(height, width)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Height"] = from_int(self.height)
        result["Width"] = from_int(self.width)
        return result


@dataclass
class Sticker:
    files: List[str]
    placement_targets: List[Area]
    probability: float

    @staticmethod
    def from_dict(obj: Any) -> 'Sticker':
        assert isinstance(obj, dict)
        files = from_list(from_str, obj.get("Files"))
        placement_targets = from_list(Area.from_dict, obj.get("PlacementTargets"))
        probability = from_float(obj.get("Probability"))
        return Sticker(files, placement_targets, probability)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Files"] = from_list(from_str, self.files)
        result["PlacementTargets"] = from_list(lambda x: to_class(Area, x), self.placement_targets)
        result["Probability"] = to_float(self.probability)
        return result


@dataclass
class Template:
    size: Size
    totalchars: int
    border: int
    border_color: Color
    background_color: Color
    foreground_color: Color
    fonts: List[Font]
    lines: List[Line]
    sticker: Optional[Sticker] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Template':
        assert isinstance(obj, dict)
        size = Size.from_dict(obj.get("Size"))
        totalchars = from_int(obj.get("Totalchars"))
        border = from_int(obj.get("Border"))
        border_color = Color.from_dict(obj.get("BorderColor"))
        background_color = Color.from_dict(obj.get("BackgroundColor"))
        foreground_color = Color.from_dict(obj.get("ForegroundColor"))
        fonts = from_list(Font.from_dict, obj.get("Fonts"))
        lines = from_list(Line.from_dict, obj.get("Lines"))
        sticker = from_union([Sticker.from_dict, from_none], obj.get("Sticker"))
        return Template(size, totalchars, border, border_color, background_color, foreground_color, fonts, lines, sticker)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Size"] = to_class(Size, self.size)
        result["Totalchars"] = from_int(self.totalchars)
        result["Border"] = from_int(self.border)
        result["BorderColor"] = to_class(Color, self.border_color)
        result["BackgroundColor"] = to_class(Color, self.background_color)
        result["ForegroundColor"] = to_class(Color, self.foreground_color)
        result["Fonts"] = from_list(lambda x: to_class(Font, x), self.fonts)
        result["Lines"] = from_list(lambda x: to_class(Line, x), self.lines)
        result["Sticker"] = from_union([lambda x: to_class(Sticker, x), from_none], self.sticker)
        return result


@dataclass
class CountryConfiguration:
    country: str
    templates: List[Template]

    @staticmethod
    def from_dict(obj: Any) -> 'CountryConfiguration':
        assert isinstance(obj, dict)
        country = from_str(obj.get("Country"))
        templates = from_list(Template.from_dict, obj.get("Templates"))
        return CountryConfiguration(country, templates)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Country"] = from_str(self.country)
        result["Templates"] = from_list(lambda x: to_class(Template, x), self.templates)
        return result


def country_configuration_from_dict(s: Any) -> CountryConfiguration:
    return CountryConfiguration.from_dict(s)


def country_configuration_to_dict(x: CountryConfiguration) -> Any:
    return to_class(CountryConfiguration, x)
