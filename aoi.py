import math
import re
import time
import numpy as np
import cv2
import matplotlib
import matplotlib.pyplot as plt


# Import Mask RCNN
from mrcnn.config import Config
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn import visualize
from mrcnn.model import log

from data_prep import PCBDataset

from pascal_voc_writer import Writer

def MRCNN_Config(data):
    config = Config()
    config.NAME = "PCB_AOI"
    config.NUM_CLASSES = len(data.class_names)
    config.GPU_COUNT = 1
    config.IMAGES_PER_GPU = 1
    config.IMAGE_MIN_DIM = 448
    config.IMAGE_MAX_DIM = 448
    config.DETECTION_MIN_CONFIDENCE = 0.3
    config.__init__()
    config.display()
    return config

def data_init():
    data = PCBDataset()
    data.load_dataset()
    data.prepare()
    print(data.class_names)
    return data

def load_names():
    cn = []
    cn.append('BG')
    cn.append('Solder_good')
    cn.append('Solder_bad')
    cn.append('Solder_not')
    cn.append('Solder_ball')
    return cn

def model_init(data):
    inference_config = MRCNN_Config(data)
    model = modellib.MaskRCNN(mode="inference", config=inference_config, model_dir='Model1')
    model_path = 'model.h5'
    model.load_weights(model_path, by_name=True)
    return model

def image_det(images,model,data):
    cnt = 0
    model = model_init(data)
    for image in images:
        cnt = cnt + 1
        image_name = 'Images_Out/im'+str(cnt)+'.jpg'
        #image = cv2.resize(image, dsize=(448, 448))
        img_arr = np.array(image)
        results = model.detect([img_arr], verbose=0)
        r = results[0]
        print(r)
        #visualize.save_image(image, image_name, r['rois'], r['masks'],r['class_ids'],r['scores'],data.class_names,mode=2)
        #visualize.display_instances(image, r['rois'], r['masks'], r['class_ids'], data.class_names, r['scores'], figsize=(5,5))

def analyze_image(image,model,data,folder,cnt):
    img_arr = np.array(image)
    results = model.detect([img_arr], verbose=0)
    r = results[0]
    cn = load_names()
    #visualize.display_instances(image, r['rois'], r['masks'], r['class_ids'], cn, r['scores'], figsize=(5,5))
    save(image,r,data,folder,cnt)
    if(len(r) == 0):
        img = image
        pad_cnt = [0,0,0,0]
    else:
        img,pad_cnt = draw_rect(image,r)
    return img,pad_cnt
    #print(r)
    #visualize.save_image(image, image_name, r['rois'], r['masks'],r['class_ids'],r['scores'],data.class_names,mode=2)
    

def draw_rect(image,r):
    pad_cnt = [0,0,0,0]
    rois = r['rois']
    cls_ids = r['class_ids']
    img = image
    cnt = 0
    for roi in rois:
       if(cls_ids[cnt] == 1):
           img = cv2.rectangle(img, (roi[1],roi[0]), (roi[3],roi[2]), (255, 0, 0), 5)  
           pad_cnt[0] = pad_cnt[0] + 1
       elif(cls_ids[cnt] == 2):
           img = cv2.rectangle(img, (roi[1],roi[0]), (roi[3],roi[2]), (0, 255, 0), 5)  
           pad_cnt[1] = pad_cnt[1] + 1
       elif(cls_ids[cnt] == 3):
           img = cv2.rectangle(img, (roi[1],roi[0]), (roi[3],roi[2]), (0, 0, 255), 5) 
           pad_cnt[2] = pad_cnt[2] + 1
       elif(cls_ids[cnt] == 4):
           img = cv2.rectangle(img, (roi[1],roi[0]), (roi[3],roi[2]), (255, 255, 0), 5)  
           pad_cnt[3] = pad_cnt[3] + 1
       cnt = cnt + 1
    return img,pad_cnt

def save(image,r,data,folder,cnt):
    image_name = folder+'\im'+str(cnt)+'.jpg'
    cv2.imwrite(image_name,image)
    rois = r['rois']
    cls_ids = r['class_ids']
    writer = Writer(image_name, 1280, 720)
    temp = 0
    for roi in rois:
       if(cls_ids[temp] == 1):
           writer.addObject('Solder_good', roi[1], roi[0], roi[3], roi[2])
       elif(cls_ids[temp] == 2):
           writer.addObject('Solder_bad', roi[1], roi[0], roi[3], roi[2])
       elif(cls_ids[temp] == 3):
           writer.addObject('Solder_not', roi[1], roi[0], roi[3], roi[2])
       elif(cls_ids[temp] == 4):
           writer.addObject('Solder_ball', roi[1], roi[0], roi[3], roi[2])
       temp = temp + 1
    xml_name = folder+'\im'+str(cnt)+'.xml'
    writer.save(xml_name)