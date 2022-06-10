from skimage import  transform, exposure, filters,io, img_as_float,util,color
from skimage.feature import corner_harris, corner_subpix, corner_peaks
import operator
import random
import numpy as np
import matplotlib.pyplot as plt
from operator import itemgetter
import math
class Annotation:
    left:float
    top:float
    bottom:float
    right:float
    corners = []
    def __init__(self,left = None, top = None, bottom=None, right=None, corners=None):
        self.left = float(left if left!=None else min([c[0] for c in corners]) if corners != None else 0)
        self.top= float(top if top!=None else min([c[1] for c in corners]) if corners != None else 0)
        self.bottom = float(bottom if bottom!=None else max([c[1] for c in corners]) if corners != None else 0)
        self.right = float(right if right!=None else max([c[0] for c in corners]) if corners != None else 0)
        if corners == None:
            self.corners =  [[float(top),float(left)], [float(bottom),float(left)], [float(bottom),float(right)],[float(top),float(right)]]
        else:
            self.corners = corners

    def add(self,offset:(float,float)):
        self.left+=offset[1]
        self.top+=offset[0]
        self.bottom+=offset[0]
        self.right+=offset[1]
        for c in self.corners:
            c[0]+=offset[1]
            c[1]+=offset[0]
        return self

class AugmentedImage:
    image:np.array
    annotation:Annotation
    augmentations = []
    def __init__(self,image,annotation:Annotation=None,augmentations=[]):
        self.image = image
        h,w,c = image.shape
        if annotation == None:
            self.annotation = Annotation(top=0,left=0,right=w,bottom=h)
        else:
            self.annotation = annotation
        self.augmentations = augmentations

    def getaugmentationslog(self):
        ret = ""
        if self.augmentations == None:
            return ""
        for s in self.augmentations:
            ret+=s.tostring()+"\n"
        return ret[:len(ret)-2]

class AugmentationOperationLog:
    operation:str=""
    value:int
    def __init__(self, operation:str = "", value = None):
        self.operation = operation
        self.value = value

    def tostring(self):
        ret = "{}-> value:{}".format(self.operation,self.value)        

class Augmentation:
    image:np.array
    operations=[]
    def __init__(self,image):
        self.image = image
        self.operations = []
    def blur(self,sigma=None,sigma_min=0.5, sigma_max=5):
        if sigma ==None:
            sigma = random.uniform(sigma_min,sigma_max)
        tmp = filters.gaussian(self.image,sigma = (sigma,sigma),multichannel=True,truncate=3.5)*255
        self.image = tmp.astype(np.uint8)   
        self.operations.append(AugmentationOperationLog("blur",value=sigma))       
        return self.image,sigma
    
    def darken(self,sigma=None,sigma_min=0.9, sigma_max=1):
        if sigma ==None:
            sigma = random.uniform(sigma_min,sigma_max)
        image = self.image
        info = np.iinfo(image.dtype)
        image = image.astype(np.float64)/info.max
        image *= sigma
        image *= 255
        self.image = image.astype(np.uint8)     
        self.operations.append(AugmentationOperationLog("darken",value=sigma))     
        return self.image,sigma
    
    def saturation(self,gamma=None, gamma_min=0.5, gamma_max=2):
        if gamma ==None:
            gamma = random.uniform(gamma_min,gamma_max)
        image = self.image
        image = exposure.adjust_gamma(image,gamma,1) 
        self.image = image.astype(np.uint8)
        self.operations.append(AugmentationOperationLog("saturation",value=gamma))   
        return self.image,gamma
    
    def dirt(self,amount=None,amount_min = 0, amount_max = 0.2):
        if amount == None:
            amount=random.uniform(amount_min,amount_max)
        image = self.image/255
        h,w,c = image.shape
        hn,wn = int(20), int(w/h*20)
        tmp =  np.random.normal(scale=0.01,size=(hn,wn))  
        tmp = transform.resize(tmp,(h,w))*amount   
        noise = np.ones((h,w,c))
        noise[:,:,0] = tmp
        noise[:,:,1] = tmp
        noise[:,:,2] = tmp
        noise[:,:,3] = tmp   
        mask = np.stack([noise[:,:,3] for _ in range(3)],axis=2)
        inv_mask = 1.-mask 
        ret = np.ones((h,w,c))
        ret[:,:,:3] = image[:,:,:3]*inv_mask + noise[:,:,:3]*mask
        ret *= 255
        self.image = ret.astype(np.uint8)
        self.operations.append(AugmentationOperationLog("dirt",value=amount))   
        return self.image,amount
    
    def perspective(self,ratio = None,ratio_min = -0.5,ratio_max = 0.5):
        image = self.image
        h,w,c = image.shape
        if ratio == None:
            ratio = random.uniform(ratio_min,ratio_max)
        ho = int((h/4)*ratio)
        if ratio == 0 or ho == 0:
            return image,ratio
        wo = ho
        # P0...P3 
        # .     .  P:(w,h)
        # P1...P2    
        P0 = [0,0]
        P1 = [0,h]
        P2 = [w,h]
        P3 = [w,0]

        src = np.array([P0,P1,P2,P3])
        if ho>0:
            P0d = [P0[0],P0[1]-ho]
            P1d = [P1[0],P1[1]+ho]
            P2d = P2
            P3d = P3
        elif ho<0:
            P0d = P0
            P1d = P1
            P2d = [P2[0],P2[1]-ho]
            P3d = [P3[0],P3[1]+ho]
        dst = np.array([P0d,P1d,P2d,P3d])
        tran = transform.ProjectiveTransform()
        tran.estimate(src,dst)
        warped = transform.warp(image,tran)*255
        self.image = warped.astype(np.uint8)
        self.operations.append(AugmentationOperationLog("perspetive",value=ratio))   
        return self.image,ratio
    
    def rotate(self,angle = None, angle_min = -15, angle_max=15,rotation_point:(int,int)=None):
        if angle == None:
            angle = random.randint(angle_min,angle_max)
        image = self.image
        image = transform.rotate(image,angle,True, center=rotation_point)*255
        self.image = image.astype(np.uint8)
        self.operations.append(AugmentationOperationLog("rotate",value=angle))   
        return self.image,angle
    
    def shear(self,ratio = None):
        ratio if ratio != None else random.uniform(-1,1)
        afine_tf = transform.AffineTransform(shear=ratio)
        image = transform.warp(self.image, inverse_map=afine_tf)*255
        self.image = image.astype(np.uint8)
        self.operations.append(AugmentationOperationLog("shear",value=ratio))
        return self.image,ratio

    def resize(self, size):
        self.image = (transform.resize(self.image,size)*255).astype(np.uint8)
        self.operations.append(AugmentationOperationLog("resize",value=size))   
        return self.image,size
   
    def getCorners(self):
        image = self.image
        h,w,c = image.shape
        offset = 10
        bin = np.zeros((h+offset,w+offset),np.uint8)
        o = int(offset/2)
        ho = o+h
        wo = o+w
        bin[o:ho,o:wo] = image[:,:,3] > 100
        coords = corner_peaks(corner_harris(bin))
        points = [[float(c[1]-o),float(c[0]-o)] for c in coords]  
        points = self._orderCorners(points)
        return points

    def _orderCorners(self,points):
        points.sort(key=itemgetter(0))
        ordered =[points[0]]
        points.remove(points[0])
        while len(points)>0:
            last = ordered[len(ordered)-1]
            selected = None
            closest = math.inf
            for p in points:
                #dist = math.sqrt(math.pow(last[0]-p[0],2) + math.pow(last[1]-p[1],2))
                dist = abs(last[0]-p[0]) + abs(last[1]-p[1])
                if dist<closest:
                    selected = p
                    closest = dist
            points.remove(selected)
            ordered.append(selected)
        return ordered
    def getAugmentedImage(self):       
        coords = self.getCorners() 
        left = float(min([c[0] for c in coords]))
        top= float(min([c[1] for c in coords]))
        bottom = float(max([c[1] for c in coords]))
        right = float(max([c[0] for c in coords]))
        return AugmentedImage(self.image, Annotation(left=left,top=top,right=right,bottom=bottom,corners=coords),self.operations) 

def _getPlateImageSize(plate_hw:(int,int),base_hw:(int,int),finalSizeAreaRatio):
    r = finalSizeAreaRatio
    area = r * (base_hw[0]*base_hw[1])
    plateArea = plate_hw[0]*plate_hw[1]
    aR = area/plateArea
    return (int(plate_hw[0]*aR),int(plate_hw[1]*aR))


def randomAugmentation(image, finalImageSizeInfo:((int,int),(int,int),float) = None):
    aug = Augmentation(image)    
    im,val = aug.dirt()    
    im,val = aug.darken()
    im,val = aug.blur()
    im,val = aug.saturation()
    im,val = aug.perspective() if random.randint(0,300) % 3 == 0 else aug.shear()
    im,val = aug.rotate()
    if finalImageSizeInfo != None:
        im,val = aug.resize(_getPlateImageSize(finalImageSizeInfo[0],finalImageSizeInfo[1],finalImageSizeInfo[2]))
    #coords = aug.getCorners()
    h,w,c = aug.image.shape
    alpha = (aug.image[:,:,3]>(255/4))*255
    #alpha = (aug.image[:,:,3]>=0)*255
    aug.image[:,:,3] = alpha
    return aug.getAugmentedImage()

def blurImage(image,sigma = 1):
    aug = Augmentation(image)
    im,val = aug.blur(sigma)
    return im