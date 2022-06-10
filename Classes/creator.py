import os
import numpy as np
from skimage import io, transform
import licensePlate as lp
import licenseNumber as licenseNumber
import imageAnnotation as ia
import tools as tools
import augmentation as aug
from typing import List
import countryConfiguration as cc
from enum import Enum
import random
import uuid
import json
from collections import namedtuple
import math 

class Zones(Enum):
    TopLeft="TopLeft"
    TopRight="TopRight"
    Center = "Center"
    BottomLeft = "BottomLeft"
    BottomRight = "BottomRight"
    ALL = "ALL"

#TemplateInfo = namedtuple("TemplateInfo","country, template")

class Creator:
    baseImagesFolder:str
    configurations:List[cc.CountryConfiguration]
    _templates:[(str,cc.Template)] = []
    destinationFolder:str="Dataset"
    seperateTrainTestVal:bool=True
    useRelativeValues:bool=True
    preferredImageSize:(int,int)=(1280,720)
    preferedCutZone:Zones=Zones.Center
    _trainFolder:str = "Train"
    _testFolder:str="Test"
    _validationFolder:str="Validation"
    maxPlateImageArea:float=0.1
    minPlateImageArea:float=0.01
    reuseBaseImages:bool=True


    def __init__(self,configurations:List[cc.CountryConfiguration], baseImagesFolder:str, 
                 destinationFolder:str="Dataset", preferredImageSize:(int,int) = (1280,720), preferedCutZone:Zones=Zones.Center,
                 seperateTrainTestVal:bool=True, useRelativeValues:bool=False, reuseBaseImages:bool=True, maxPlateImageArea = 0.05, minPlateImageArea = 0.015):
        self.baseImagesFolder = baseImagesFolder
        if not os.path.exists(self.baseImagesFolder):
            raise FileNotFoundError(baseImagesFolder)
        self.configurations = configurations
        self.destinationFolder = destinationFolder
        self.seperateTrainTestVal = seperateTrainTestVal
        self.useRelativeValues = useRelativeValues
        self.preferredImageSize = preferredImageSize
        self.preferedCutZone = preferedCutZone
        self._trainFolder = os.path.join(self.destinationFolder,self._trainFolder)
        self._testFolder = os.path.join(self.destinationFolder,self._testFolder)
        self._validationFolder = os.path.join(self.destinationFolder,self._validationFolder)
        self._templates = []
        self.reuseBaseImages = reuseBaseImages
        self.maxPlateImageArea = maxPlateImageArea
        self.minPlateImageArea = minPlateImageArea
        for c in self.configurations:
            for t in c.templates:
                self._templates.append((c.country,t))        
        if not os.path.exists(self.destinationFolder):
            os.makedirs(self.destinationFolder)
        if self.seperateTrainTestVal:
            if not os.path.exists(self._trainFolder):
                os.makedirs(self._trainFolder)
            if not os.path.exists(self._testFolder):
                os.makedirs(self._testFolder)
            if not os.path.exists(self._validationFolder):
                os.makedirs(self._validationFolder)
        else:
            self._trainFolder = self.destinationFolder
            self._testFolder = self.destinationFolder
            self._validationFolder = self.destinationFolder
            

    def create(self,maxNumberofImages = 1000, maxNumberofPlates=5, augmentPlateImages = True):
        baseImageFiles = self._getImageFiles(self.baseImagesFolder)
        if len(baseImageFiles) == 0:
            return "No images found in given folder"
        if maxNumberofImages == None:
            maxNumberofImages = len(baseImageFiles)
        train = round(maxNumberofImages*0.70)
        test = round(maxNumberofImages*0.15)
        validation = round(maxNumberofImages*0.15)
        if self.seperateTrainTestVal:
            print("Started dataset creation. {} images will be generated.".format(train+test+validation))
            print("Generating train dataset. {} images will be generated.".format(train))
            self._generateImages(train, baseImageFiles,self._trainFolder,maxNumberofPlates,augmentPlateImages)
            print("Finished. {} images generated.".format(train))
            print("Generating test dataset {} images will be generated.".format(test))
            self._generateImages(test, baseImageFiles,self._testFolder,maxNumberofPlates,augmentPlateImages)
            print("Finished. {} images generated.".format(test))
            print("Generating test dataset {} images will be generated.".format(validation))
            self._generateImages(validation, baseImageFiles,self._validationFolder,maxNumberofPlates,augmentPlateImages)
            print("Finished. {} images generated.".format(validation))
        else:
            print("Started dataset creation. {} images will be generated.".format(maxNumberofImages))
            self._generateImages(maxNumberofImages, baseImageFiles,self._trainFolder,maxNumberofPlates,augmentPlateImages)
            print("Finished. {} images generated.".format(maxNumberofImages))
    
    def _getImageFiles(self,directory):
        if not os.path.exists(directory):
            return []
        else:
            return [os.path.join(directory,f) for f in os.listdir(directory) if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg")]

    def _generateImages(self, count, baseImageFiles,exportDir,maxNumberofPlates=5,augmentPlateImages = True):
        for i in range(int(count)):
            imfile = random.choice(baseImageFiles)
            if not self.reuseBaseImages:
                baseImageFiles.remove(imfile)
            base = self.getReshapedImage(imfile)
            base_hw = (base.shape[0],base.shape[1])
            fileNameRaw =  uuid.uuid4().hex
            lpcount = int(round(random.uniform(0,maxNumberofPlates)+0.1))
            info = ia.ImageAnnotation(fileNameRaw+".png",[],size=ia.Size(width=int(base_hw[1]),height=int(base_hw[0])))
            for p in range(lpcount):
                country,template = random.choice(self._templates)
                plate = lp.LicensePlate(template,country)
                plateImage = np.array(plate.licensePlateImage)
                
                ph,pw,pc = plateImage.shape
                if base_hw[0]*base_hw[1] < ph*pw:
                    r = (base_hw[0]*base_hw[1])/(ph*pw)
                    plateImage = (transform.resize(plateImage,(int(ph*r),int(pw*r)))*255).astype(np.uint8)
                    ph,pw,pc = plateImage.shape
                plate_hw = (ph,pw)
                plateAn = aug.randomAugmentation(plateImage,(plate_hw,base_hw, random.uniform(self.minPlateImageArea,self.maxPlateImageArea))) 
                
                #print("plateAnn,{},{},{},{}".format(plateAn.annotation.left,plateAn.annotation.top,plateAn.annotation.right,plateAn.annotation.bottom))
                ph,pw,pc = plateAn.image.shape  
                plate_hw = (ph,pw)
                point = self._getRandomPlacementPoint(plate_hw,base_hw,info.annotations)               
                if point != None:
                    #print("Point,{},{},{},{}".format(point[1],point[0],point[1]+pw,point[0]+ph))
                    plateAn.annotation.add(point)
                    #print("plateAnn_add,{},{},{},{}".format(plateAn.annotation.left,plateAn.annotation.top,plateAn.annotation.right,plateAn.annotation.bottom))
                    self._pasteImage(plateAn.image,point,base)
                    anbox = ia.Box(False,plateAn.annotation.left,plateAn.annotation.top,plateAn.annotation.right,plateAn.annotation.bottom)
                    ann = ia.Annotation(plate.licensePlateNumberStr,country,"LP",anbox,ia.Segmentation(False,[ia.Corner(c[1],c[0]) for c in plateAn.annotation.corners]))
                    info.annotations.append(ann)
                    #print("Ann,{},{},{},{}".format(ann.box.left,ann.box.top,ann.box.right,ann.box.bottom))
                    #print()
            self._save(base,info,exportDir,fileNameRaw)
            if i>0:
                print ("\033[A                             \033[A")
            print("{}/{} saved with {} license plates".format(i+1,count,len(info.annotations),end="\r"))
            if i+1==count:
                print ("\033[A                             \033[A")

    def _toRelativeValues(self,base_hw:(float,float),annotation:ia.Annotation):
        annotation.box.is_relative = True
        annotation.box.top /= base_hw[0]
        annotation.box.left /= base_hw[1]
        annotation.box.bottom /= base_hw[0]
        annotation.box.right /= base_hw[1]
        annotation.segmentation.is_relative = True
        for c in annotation.segmentation.corners:
            c.x /= base_hw[1]
            c.y /= base_hw[0]

    def _save(self,image:np.array,info:ia.ImageAnnotation,directory:str,fileNameRaw):
        info.file = fileNameRaw+".png"
        if self.useRelativeValues:
            for ann in info.annotations:
                self._toRelativeValues((info.size.height,info.size.width),ann)
        io.imsave(os.path.join(directory,info.file),aug.blurImage(image))
        imAnnDict = info.to_dict()
        jsonStr = json.dumps(imAnnDict)
        with open(os.path.join(directory,fileNameRaw+".json"),"w+") as jsonfile:
            jsonfile.write(jsonStr)

    def _pasteImage(self,plate,point,base):
        h,w,c = plate.shape
        hp,wp = point[0],point[1]
        hph = hp+h
        wph = wp+w
        if c != 4:
            base[hp:hph,wp:wph,:c] = plate
        else:
            basetmp = base[hp:hph,wp:wph,:]
            for y in range(h):
                for x in range(w):
                    if plate[y,x,3]>0:
                        basetmp[y,x,:3] = plate[y,x,:3]
            base[hp:hph,wp:wph,:] = basetmp

    def _getRandomPlacementPoint(self,plate_hw:(int,int),base_hw:(int,int),annotations:List[ia.Annotation]):
        trial = 0
        box1 = self._getRandomPoint(plate_hw,base_hw)
        #print("box1,{},{},{},{}".format(box1.left,box1.top,box1.right,box1.bottom))
        while tools.isOverlappingAny(tools.Box(box1.left,box1.top,box1.right,box1.bottom),[tools.Box(a.box.left,a.box.top,a.box.right,a.box.bottom) for a in annotations]) and trial<10:
            box1 = self._getRandomPoint(plate_hw,base_hw)
            trial+=1
        if trial<10:
            return (box1.top,box1.left)
        else:
            return None

    def _getRandomPoint(self,plate_hw:(int,int),base_hw:(int,int)):
        left = random.randint(plate_hw[1],base_hw[1]-plate_hw[1])
        top = random.randint(plate_hw[0],base_hw[0]-plate_hw[0])
        right = left+plate_hw[1]
        bottom=top+plate_hw[0]
        return tools.Box(left,top,right,bottom)
        


    def getReshapedImage(self,imageFile):
        return (self._getReshapedImage(imageFile)*255).astype(np.uint8)

    def _getReshapedImage(self,imageFile):
        im = io.imread(imageFile)
        h,w,c = im.shape
        if c == 3:
            tmp = np.zeros((h,w,4),np.uint8)+255
            tmp[:,:,:3] = im
            im = tmp
        phwr = self.preferredImageSize[1]/self.preferredImageSize[0]
        hwr = h/w
        if self.preferedCutZone == Zones.ALL or phwr==hwr:
            return transform.resize(im,(self.preferredImageSize[1],self.preferredImageSize[0]))
        if phwr<hwr:
            hn = int(w*phwr)
            if self.preferedCutZone == Zones.Center:
                tmp = im[int(h/2-hn/2):int(h/2+hn/2),:,:]
                return transform.resize(tmp,(self.preferredImageSize[1],self.preferredImageSize[0]))
            elif self.preferedCutZone == Zones.TopLeft or Zones.TopRight:
                tmp = im[:hn,:,:]
                return transform.resize(tmp,(self.preferredImageSize[1],self.preferredImageSize[0])) 
            elif self.preferedCutZone == Zones.BottomLeft or Zones.BottomRight:
                tmp = im[h-hn:h,:,:]
                return transform.resize(tmp,(self.preferredImageSize[1],self.preferredImageSize[0])) 
        elif phwr>hwr:
            wn = int(h/phwr)
            if self.preferedCutZone == Zones.Center:
                tmp = im[:,int(w/2-wn/2):int(w/2+wn/2),:]
                return transform.resize(tmp,(self.preferredImageSize[1],self.preferredImageSize[0]))
            elif self.preferedCutZone == Zones.TopLeft or Zones.BottomLeft:
                tmp = im[:,:wn,:]
                return transform.resize(tmp,(self.preferredImageSize[1],self.preferredImageSize[0])) 
            elif self.preferedCutZone == Zones.TopRight or Zones.BottomRight:
                tmp = im[:,w-wn:w,:]
                return transform.resize(tmp,(self.preferredImageSize[1],self.preferredImageSize[0])) 