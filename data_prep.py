import os
import numpy as np
from mrcnn import utils
import xml.etree.ElementTree as ET
import skimage.io

class PCBDataset(utils.Dataset):
    def load_dataset(self):
        self.add_class('dataset', 1, 'Solder_good')
        self.add_class('dataset', 2, 'Solder_bad')
        self.add_class('dataset', 3, 'Solder_not')
        self.add_class('dataset', 4, 'Solder_ball')
        
        # find all images
        #for i, filename in enumerate(os.listdir(dataset_dir)):
        #    if '.jpg' in filename:
        #        self.add_image('dataset', 
        #                       image_id=i, 
        #                       path=os.path.join(dataset_dir, filename), 
        #                       annotation=os.path.join(dataset_dir, filename.replace('.jpg', '.xml')))
    
    # extract bounding boxes from an annotation file
    def extract_boxes(self, filename):
        # load and parse the file
        tree = ET.parse(filename)
        # get the root of the document
        root = tree.getroot()
        # extract each bounding box
        boxes = []
        classes = []
        for member in root.findall('object'):
            xmin = int(member[4][0].text)
            ymin = int(member[4][1].text)
            xmax = int(member[4][2].text)
            ymax = int(member[4][3].text)
            boxes.append([xmin, ymin, xmax, ymax])
            classes.append(self.class_names.index(member[0].text))
        # extract image dimensions
        width = int(root.find('size')[0].text)
        height = int(root.find('size')[1].text)
        return boxes, classes, width, height
 
    # load the masks for an image
    def load_mask(self, image_id):
        # get details of image
        info = self.image_info[image_id]
        # define box file location
        path = info['annotation']
        # load XML
        boxes, classes, w, h = self.extract_boxes(path)
        # create one array for all masks, each on a different channel
        masks = np.zeros([h, w, len(boxes)], dtype='uint8')
        # create masks
        for i in range(len(boxes)):
            box = boxes[i]
            row_s, row_e = box[1], box[3]
            col_s, col_e = box[0], box[2]
            masks[row_s:row_e, col_s:col_e, i] = 1
        return masks, np.asarray(classes, dtype='int32')
    
    def image_reference(self, image_id):
        info = self.image_info[image_id]
        return info['path']
    def load_image(self, image_id):
        image = skimage.io.imread(self.image_info[image_id]['path'])
        return image
