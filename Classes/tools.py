import countryConfiguration as cc
from PIL import Image, ImageFont
import numpy as np
from skimage.feature import  corner_harris,corner_peaks
from skimage import  io
from typing import List
from collections import namedtuple

def to_color_tuple(color:cc.Color):
    return (color.r,color.g,color.b)

def to_size_tuple(size:cc.Size):
    return (size.width,size.height)
    
def add_to_size_tuple(size:(int,int),value:int):
    return (size[0]+value,size[1]+value)

def combine_images(images):
    widths = []
    maxHeight = 0
    for v in images:
        w,h = v.size
        widths.append(w)
        if h > maxHeight:
            maxHeight = h
    tmp_Im = Image.new("RGBA",(sum(widths),maxHeight))
    x_offset = 0
    for im in images:
        tmp_Im.paste(im, (x_offset,0))
        x_offset += im.size[0]
    return tmp_Im

def area_to_box(area:cc.Area):
    return (area.x,area.y,area.x+area.width,area.y+area.height)

def get_font_size(height:int, fontfile:str, start = 12, end = None, test_text:str="1AB2", step = 5):
    if end == None or end <= start:
        i = start
        i_last = start
        h = 0
        while  h < height:
            i_last = i
            font = ImageFont.truetype(font=fontfile,size=i)
            w,h = font.getsize(test_text)
            i+=step
        return i_last
    else:
        for i in range(start,end,step):
            font = ImageFont.truetype(font=fontfile,size=i)
            w,h = font.getsize(test_text)
            if h>=height:
                return i_last
            else:
                i_last = i
        return end

def get_box_height(box:(int,int,int,int)):
    return box[3]-box[1]

def remove_excess(image, tolerance=0):
    mask = image[:,:,3]>tolerance
    m,n = mask.shape
    mask0,mask1 = mask.any(0),mask.any(1)
    col_start,col_end = mask0.argmax(),n-mask0[::-1].argmax()
    row_start,row_end = mask1.argmax(),m-mask1[::-1].argmax()
    return image[row_start:row_end,col_start:col_end]

Box=namedtuple("Box","left,top,right,bottom")

def isOverlapping(box1:Box,box2:Box):
    x1min = min([box1.left,box1.right])
    x1max = max([box1.left,box1.right])
    x2min = min([box2.left,box2.right])
    x2max = max([box2.left,box2.right])
    y1min = min([box1.top,box1.bottom])
    y1max = max([box1.top,box1.bottom])
    y2min = min([box2.top,box2.bottom])
    y2max = max([box2.top,box2.bottom])
    ret =  (x1min < x2max and x2min < x1max and y1min < y2max and y2min < y1max)
    #print("box1_isoverlapping,{},{},{},{}".format(box1.left,box1.top,box1.right,box1.bottom))
    #print("box2_isoverlapping,{},{},{},{}".format(box2.left,box2.top,box2.right,box2.bottom))
    #print(ret)
    if ret:
        pass
    return ret
def isOverlappingAny(box1:Box,boxes:List[Box]):
    for b in boxes:
        if isOverlapping(box1,b):
            return True
    return False