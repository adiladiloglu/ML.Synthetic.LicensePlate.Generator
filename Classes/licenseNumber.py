import countryConfiguration as cc
import random
#from dataclasses import dataclass
from typing import List
from PIL import Image

#@dataclass
class LicenseNumberPart:
    partType:cc.TypeEnum
    values:[]
    _drawable:cc.Drawable
    offset:int = 0

    def __init__(self,drawable:cc.Drawable):
        self.partType = drawable.type
        self._drawable = drawable
        self.offset = drawable.offset
        self.values = []

    def generate(self, maxvaluecount:int):
        self.values = []
        for p in self._drawable.parts:
            if (len(self.values) < maxvaluecount) & (random.random()<=p.probability):
                value = random.choice(p.options)
                if self.partType == cc.TypeEnum.SEAL:
                    self.values.append(Image.open(value))
                else:
                    self.values.append(value)
                
    def get_values_length(self):
        if self.partType == cc.TypeEnum.SEAL:
            return 0
        else:
            return len(self.values)
    
    def tostring(self):
        if self.partType == cc.TypeEnum.SEAL:
            return ""
        else:
            s = ""
            for v in self.values:
                s+=v
            return s

#@dataclass
class LicenseNumberLine:
    parts:List[LicenseNumberPart]
    _line:cc.Line
    area:cc.Area

    def __init__(self,line:cc.Line):
        self.parts  = []
        self._line = line
        for d in line.drawables:
            self.parts.append(LicenseNumberPart(d))
        self.area = line.area
    
    def generate(self, maxvaluecount:int):
        count = maxvaluecount
        for p in self.parts:
            p.generate(count)
            count-=p.get_values_length()

    
    def get_values(self):
        values = []
        for p in self.parts:
            for v in p.values:
                values.append(v)
        return values

    def get_text_values(self):
        values = []
        for p in self.parts:
            if p.partType == cc.TypeEnum.TEXT:
                for v in p.values:
                    values.append(v)
        return values
    
    def get_values_length(self):
        length = 0
        for p in self.parts:
            length+=p.get_values_length()
        return length

    def tostring(self):
        s=""
        for l in self.parts:
            values = l.tostring()
            s+= values+" "
        return s[:len(s)-1]

#@dataclass
class LicenseNumber:
    lines:List[LicenseNumberLine]
    totalchars:int

    def __init__(self,template:cc.Template):
        self.lines = []
        self.totalchars = template.totalchars
        for l in template.lines:
            self.lines.append(LicenseNumberLine(l))
    
    def generate(self):
        count = self.totalchars
        for l in self.lines:
            l.generate(count)
            count-=l.get_values_length()
    
    def get_text_values(self):
        values = []
        for l in self.lines:
            values += l.get_text_values()
        return values
    
    def tostring(self):
        s=""
        for l in self.lines:
            values = l.tostring()
            s+=values+" "
        return s[:len(s)-1]