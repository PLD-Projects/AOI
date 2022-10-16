import serial
import cv2
import math
import time
import os
import numpy as np
from datetime import datetime
import aoi

def init():
    print("cnc init")
    global cnc_ser
    cnc_ser = serial.Serial('COM8', 115200)
    data = cnc_ser.readline()
    data = cnc_ser.readline()

    cmd = '$H\n'
    cnc_ser.write(cmd.encode())
    print(cmd)
    data = cnc_ser.readline()

    cmd = 'G10 P0 L20 X0 Y0 Z0\n'
    cnc_ser.write(cmd.encode())
    print(cmd)
    data = cnc_ser.readline()

    goto_pos(0,-365)

    cmd = 'G10 P0 L20 X0 Y0 Z0\n'
    cnc_ser.write(cmd.encode())
    print(cmd)
    data = cnc_ser.readline()

    cnc_ser.close()

def scan(model,data,pcb_size):
    margin = [10,10,10,10]
    aov = [41,22.7]
    step = [41,22.7]
    fine_step = 2
    #pcb_size = [170,120]
    no_steps = [0,0]
    cnc_loc = [0,0]
    pic_cnt = 0
    images = []
    pad_cnts = []

    global cnc_ser
    cnc_ser = serial.Serial('COM8', 115200)
    #cam = cv2.VideoCapture(0)
    global cam
    cam = cv2.VideoCapture(0,cv2.CAP_DSHOW)
    cam.set(3,1280)
    cam.set(4,720)

    total_width = margin[0]+pcb_size[0]+margin[1]
    total_height = margin[2]+pcb_size[1]+margin[3]

    mov_x = total_width-aov[0]
    mov_y = total_height-aov[1]

    no_steps[0] = math.ceil(mov_x/step[0])
    print(no_steps[0])
    no_steps[1] = math.ceil(mov_y/step[1])
    print(no_steps[1])

    row_cnt = 0
    data = cnc_ser.readline()
    data = cnc_ser.readline()

    cmd = 'G10 P0 L20 X0 Y0 Z0\n'
    cnc_ser.write(cmd.encode())
    print(cmd)
    data = cnc_ser.readline()

    im_cnt = 0

    data_out = os.path.join(os.getcwd()+'/Data',datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(data_out)
    
    frame = cap_read()

    for y in range(no_steps[1]):
        for x in range(no_steps[0]):
            goto_pos(cnc_loc[0],cnc_loc[1])
            if(im_cnt > 0):
                img_out,pad_cnt = aoi.analyze_image(frame,model,data,data_out,im_cnt-1)
                images.append(img_out)
                pad_cnts.append(pad_cnt)
            wait_pos()
            time.sleep(0.2)
            frame = cap_read()
            name = 'Images/im'+str(im_cnt)+'.jpg'
            print(name)
            im_cnt = im_cnt+1
            cv2.imwrite(name,frame)
            if row_cnt%2 == 0:
                cnc_loc[0] = cnc_loc[0]+step[0]
            if row_cnt%2 == 1:
                cnc_loc[0] = cnc_loc[0]-step[0]
    
        goto_pos(cnc_loc[0],cnc_loc[1])
        img_out,pad_cnt = aoi.analyze_image(frame,model,data,data_out,im_cnt-1)
        images.append(img_out)
        pad_cnts.append(pad_cnt)
        wait_pos()
        time.sleep(0.2)
        frame = cap_read()
        name = 'Images/im'+str(im_cnt)+'.jpg'
        print(name)
        im_cnt = im_cnt+1
        cv2.imwrite(name,frame)
        row_cnt = row_cnt+1
        cnc_loc[1] = cnc_loc[1]+step[1]
        

    goto_pos(0,0)
    img_out,pad_cnt = aoi.analyze_image(frame,model,data,data_out,im_cnt-1)
    images.append(img_out)
    pad_cnts.append(pad_cnt)
    wait_pos()
    cnc_ser.close()
    #combine(no_steps,images)
    return images,no_steps,pad_cnts

def goto_pos(x,y):
    cmd = 'G00X'+str(x)+'Y'+str(y)+'\n'
    cnc_ser.write(cmd.encode())
    print(cmd)
    data = cnc_ser.readline()

def wait_pos():
    cmd = 'G4P0\n'
    cnc_ser.write(cmd.encode())
    print(cmd)
    data = cnc_ser.readline()

def cap_read():
    cap, frame = cam.read()
    cap, frame = cam.read()
    pts1 = np.float32([[11,3],[1270,10],[2,691],[1259,713]])
    pts2 = np.float32([[0,0],[1280,0],[0,720],[1280,720]])
    M = cv2.getPerspectiveTransform(pts1,pts2)
    dst = cv2.warpPerspective(frame,M,(1280,720))
    return dst

def combine(no_steps,images,w,h):
    pic_cnt = 0
    row_cnt = 0
    hor_image = []
    for y in range(no_steps[1]):
        temp = images[pic_cnt]
        for x in range(no_steps[0]):
            pic_cnt += 1
            if row_cnt%2 == 0:
                temp = np.hstack((images[pic_cnt], temp))
            if row_cnt%2 == 1:
                temp = np.hstack((temp, images[pic_cnt]))
        row_cnt += 1
        hor_image.append(temp)
        pic_cnt += 1

    final_img = hor_image[0]

    for y in range(1,no_steps[1]):
        final_img = np.vstack((hor_image[y], final_img))

    ih,iw,ic = final_img.shape
    print(ih,iw)
    hr = int(ih/h)
    wr = int(iw/w)
    if(hr >= wr):
        final_img = cv2.resize(final_img, dsize=(int(ih/hr), h))
    else:
        final_img = cv2.resize(final_img, dsize=(w, int(iw/wr)))
    
    cv2.imwrite("output.jpg", final_img)
    final_img = cv2.cvtColor(final_img, cv2.cv2.COLOR_BGR2RGB)
    return final_img
    #cv2.imshow('final',final_img)
    #cv2.waitKey(0)

def load_images_from_folder(folder,model,data):
    no_steps = [4,6]
    images = []
    pad_cnts = []
    cnt =0
    data_out = os.path.join(os.getcwd()+'/Data',datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(data_out)
    for filename in os.listdir(folder):
        path = ''+folder+'\im'+str(cnt)+'.jpg'
        print(path)
        img = cv2.imread(path)
        if img is not None:
            img_out,pad_cnt = aoi.analyze_image(img,model,data,data_out,cnt)
            images.append(img_out)
            pad_cnts.append(pad_cnt)
        cnt += 1
    return images,no_steps,pad_cnts

#scan()
#images = load_images_from_folder('Images')
#combine([4,6],images)