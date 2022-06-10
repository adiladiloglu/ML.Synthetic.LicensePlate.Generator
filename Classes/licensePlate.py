import countryConfiguration as cc
import licenseNumber as ln
import tools as tools
from PIL import Image, ImageDraw,ImageFont
import os
import json
from typing import List
import random
import numpy as np

class ConfigurationData:
    file_path:str
    data:cc.CountryConfiguration
    _file_directory:str

    def __init__(self,config_json_file):
        self.file_path = config_json_file
        self._file_directory=os.path.dirname(config_json_file)
        self.data = self._get_configuration(self.file_path)
        for t in self.data.templates:
            for f in t.fonts:
                f.file = self._file_directory+"/"+f.file
            if t.sticker != None:
                for i in range(0,len(t.sticker.files)):
                    t.sticker.files[i] = self._file_directory+"/"+t.sticker.files[i]
            for l in t.lines:
                for d in l.drawables:
                    for p in d.parts:
                        if d.type == cc.TypeEnum.SEAL:
                            for i in range(0,len(p.options)):
                                p.options[i]=self._file_directory+"/"+p.options[i]

    def _get_configuration(self,config_json_file):
        with open(config_json_file) as file:
            return cc.country_configuration_from_dict(json.load(file)) 

class LicensePlate:
    licensePlateImage:Image.Image
    template:cc.Template
    licensePlateNumberStr:str
    licenseNumber:ln.LicenseNumber
    font:ImageFont
    _background_color:(int,int,int)
    _foreground_color:(int,int,int)
    _border_color:(int,int,int)
    _font:ImageFont
    country:str

    def __init__(self,template:cc.Template, country:str=""):
        self.template = template
        self.country = country        
        self.generate()

    def generate(self):
        self._border_color = (tools.to_color_tuple(self.template.border_color))
        self._background_color = (tools.to_color_tuple(self.template.background_color))
        self._foreground_color = (tools.to_color_tuple(self.template.foreground_color))
        self.licensePlateImage = Image.new(mode = "RGBA", size = tools.to_size_tuple(self.template.size), color=self._border_color)
        background = Image.new("RGBA",tools.add_to_size_tuple(tools.to_size_tuple(self.template.size),-(self.template.border*2)),color=self._background_color )
        self.licensePlateImage.paste(background,(self.template.border,self.template.border))
        self.licenseNumber = ln.LicenseNumber(self.template)
        self.licensePlateNumberStr = ""
        self.licenseNumber.generate()
        self.licensePlateNumberStr = self.licenseNumber.tostring()         
        t_font = random.choice(self.template.fonts)      
        if t_font.size == None or t_font.size<=0:
            t_font.size = tools.get_font_size(self.licenseNumber.lines[0].area.height*0.8,t_font.file,int(self.licenseNumber.lines[0].area.height/10))
        self._font = ImageFont.truetype(t_font.file,t_font.size)
        for l in self.licenseNumber.lines:
            self._paste_line(l)
        if self.template.sticker!= None:
            sticker = Image.open(random.choice(self.template.sticker.files))
            self._place_sticker(sticker,self.template.sticker.placement_targets)
    
    def _paste_line(self,line:ln.LicenseNumberLine):
        box = tools.area_to_box(line.area)
        parts = line.parts
        if parts[0].partType == cc.TypeEnum.SEAL:
            box = self._paste_left(parts[0],box)
            parts.remove(parts[0])
        if len(parts) == 1:
            self._paste_center(parts[0],box)
            return
        else:
            offset = self._get_w_offset(parts,box)
            first = parts[0]
            parts.remove(first)
            last = parts[len(parts)-1]
            parts.remove(last)
            box = self._paste_left(first,box)
            box = (box[0]+offset,box[1],box[2],box[3])
            box = self._paste_right(last,box)
            box = (box[0],box[1],box[2]-offset,box[3])
            if len(parts) == 1:
                self._paste_center(parts[0],box)
                return
            else:
                for p in parts:
                    box = self._paste_left(p,box)
                    box = (box[0]+offset,box[1],box[2],box[3])
            
    def _get_w_offset(self,parts:List[ln.LicenseNumberPart], box:(int,int,int,int)):
        totalwidth = 0
        for p in parts:
            if p.offset != None:
                totalwidth+=p.offset
            if p.partType == cc.TypeEnum.SEAL:
                w,h = tools.combine_images(p.values).size
                totalwidth+=w
            else:
                w,h = self._font.getsize(p.tostring())
                totalwidth+=w
        p_width = box[2]-box[0]
        r_width = p_width-totalwidth
        return int(r_width/(len(parts)-1)) 

    def _paste_center(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        if part.partType == cc.TypeEnum.SEAL:
            return self._paste_seal_center(part,box)
        else:
            return self._paste_text_center(part,box)

    def _paste_left(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        if part.partType == cc.TypeEnum.SEAL:
            return self._paste_seal_left(part,box)
        else:
            return self._paste_text_left(part,box)

    def _paste_right(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        if part.partType == cc.TypeEnum.SEAL:
            return self._paste_seal_right(part,box)
        else:
            return self._paste_text_right(part,box)

    def _paste_seal_center(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        image = tools.combine_images(part.values)
        wi,hi = image.size
        wb,hb = (box[2]-box[0]),(box[3]-box[1])
        xb,yb = box[0],box[1]     
        x = int(wb/2-wi/2)+xb
        y = int(hb/2-hi/2)+yb
        self.licensePlateImage.paste(image,(x,y))
        return None

    def _paste_text_center(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        wt,ht = self._font.getsize(part.tostring())
        wb,hb = (box[2]-box[0]),(box[3]-box[1])
        xb,yb = box[0],box[1]      
        x = int(wb/2-wt/2)+xb
        y = int(hb/2-ht/2)+yb
        draw = ImageDraw.Draw(self.licensePlateImage)
        draw.text((x,y),part.tostring(),fill=self._foreground_color,font=self._font)
        #draw.rectangle(((box[0]-5,box[1]-5),(box[2]-5,box[3]-5)),outline=(255,0,0),width=5)
        return None

    def _paste_seal_left(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        image = tools.combine_images(part.values)
        wi,hi = image.size
        wb,hb = (box[2]-box[0]),(box[3]-box[1])
        xb,yb = box[0],box[1]
        if part.offset != None:
            xb+=part.offset
        x = int(xb)
        y = int(hb/2-hi/2)+yb
        self.licensePlateImage.paste(image,(x,y))
        return (x+wi,box[1],box[2],box[3])

    def _paste_seal_right(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        image = tools.combine_images(part.values)
        wi,hi = image.size
        wb,hb = (box[2]-box[0]),(box[3]-box[1])
        xb,yb = box[2]-wi,box[1]       
        x = int(xb)
        y = int(hb/2-hi/2)+yb
        self.licensePlateImage.paste(image,(x,y))
        if part.offset != None:
            x-=part.offset
        return (box[0],box[1],x,box[3])

    def _paste_text_left(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        wt,ht = self._font.getsize(part.tostring())
        wb,hb = (box[2]-box[0]),(box[3]-box[1])
        xb,yb = box[0],box[1]
        if part.offset != None:
            xb+=part.offset
        x = int(xb)
        y = int(hb/2-ht/2)+yb
        draw = ImageDraw.Draw(self.licensePlateImage)
        draw.text((x,y),part.tostring(),fill=self._foreground_color,font=self._font)
        return (x+wt,box[1],box[2],box[3])
    
    def _paste_text_right(self,part:ln.LicenseNumberPart,box:(int,int,int,int)):
        wt,ht = self._font.getsize(part.tostring())
        wb,hb = (box[2]-box[0]),(box[3]-box[1])
        xb,yb = box[2]-wt,box[1]       
        x = int(xb)
        y = int(hb/2-ht/2)+yb
        draw = ImageDraw.Draw(self.licensePlateImage)
        draw.text((x,y),part.tostring(),fill=self._foreground_color,font=self._font)
        if part.offset != None:
            x-=part.offset
        return (box[0],box[1],x,box[3])
  
    def _place_sticker(self,stickerImage:Image, areas:List[cc.Area]):
        w,h = stickerImage.size
        area = random.choice(areas)
        box = tools.area_to_box(area)
        ws,hs = int((w/2)),int((h/2))
        is_point = False
        trial = 0
        max = 10
        if random.random()<=0.8:
            wp = box[0]+ws
            hp = box[1]+hs
        else:
            wp = random.randint(box[0]+ws,box[2]-ws)
            hp = random.randint(box[1]+hs,box[3]-hs)
        while is_point==False and trial<=max:            
            if(self._is_point_inside((wp,hp),box)):
                is_point = self._check_sticker_point((wp,hp),(w,h))
            if is_point == False:
                wp = random.randint(box[0]+ws,box[2]-ws)
                hp = random.randint(box[1]+hs,box[3]-hs)
            trial+=1
        if is_point:
            self.licensePlateImage.alpha_composite(stickerImage,(int(wp-w/2),int(hp-h/2)))
    
    def _is_point_inside(self,xy:(int,int),box:(int,int,int,int)):
        x,y = xy[0],xy[1]
        return x>=box[0] and x<=box[2] and y>=box[1] and y<=box[3]

    def _check_sticker_point(self,xy:(int,int),sticker_size:(int,int)):
        sticker_size = (int(sticker_size[0]),int(sticker_size[1]))
        s = np.array(self.licensePlateImage)
        pVal = s[xy[1],xy[0],:3]
        _Pval = pVal.flatten()
        sPval = sum(_Pval)
        rVals = s[xy[1]-int(sticker_size[1]/2):xy[1]+int(sticker_size[1]/2),xy[0]-int(sticker_size[0]/2):xy[0]+int(sticker_size[0]/2),0]
        srVals = rVals.flatten()
        gVals = s[xy[1]-int(sticker_size[1]/2):xy[1]+int(sticker_size[1]/2),xy[0]-int(sticker_size[0]/2):xy[0]+int(sticker_size[0]/2),1]
        sgVals = gVals.flatten()
        bVals = s[xy[1]-int(sticker_size[1]/2):xy[1]+int(sticker_size[1]/2),xy[0]-int(sticker_size[0]/2):xy[0]+int(sticker_size[0]/2),2]
        sbVals = bVals.flatten()
        total_length = len(srVals)+len(sgVals)+len(sbVals)
        _sum = sum(srVals)+sum(sgVals)+sum(sbVals)
        avarage = _sum/total_length
        return int(avarage) == int(sPval/len(pVal))