import time
import numpy as np
import cv2
import torch
from torchvision import transforms
from .nets import S3FDNet
from .box_utils import nms_

PATH_WEIGHT = './detectors/s3fd/weights/sfd_face.pth'
img_mean = np.array([104., 117., 123.])[:, np.newaxis, np.newaxis].astype('float32')


class S3FD():

    def __init__(self, device='cuda'):

        tstamp = time.time()
        self.device = device

        print('[S3FD] loading with', self.device)
        self.net = S3FDNet(device=self.device).to(self.device)
        state_dict = torch.load(PATH_WEIGHT, map_location=self.device)
        self.net.load_state_dict(state_dict)
        self.net.eval()
        print('[S3FD] finished loading (%.4f sec)' % (time.time() - tstamp))
    
    def detect_faces(self, image, conf_th=0.8, scales=[1]):

        w, h = image.shape[1], image.shape[0]
        # print('width:{}. height:{}'.format(w,h))

        bboxes = np.empty(shape=(0, 5))

        with torch.no_grad():
            for s in scales:
                scaled_img = cv2.resize(image, dsize=(0, 0), fx=s, fy=s, interpolation=cv2.INTER_LINEAR)

                scaled_img = np.swapaxes(scaled_img, 1, 2)
                scaled_img = np.swapaxes(scaled_img, 1, 0)
                scaled_img = scaled_img[[2, 1, 0], :, :]
                scaled_img = scaled_img.astype('float32')
                scaled_img -= img_mean
                scaled_img = scaled_img[[2, 1, 0], :, :]
                x = torch.from_numpy(scaled_img).unsqueeze(0).to(self.device) # TODO 这儿可以改成batch>1
                y = self.net(x)

                detections = y.data
                scale = torch.Tensor([w, h, w, h])

                for i in range(detections.size(1)):
                    j = 0
                    while detections[0, i, j, 0] > conf_th:
                        score = detections[0, i, j, 0]
                        pt = (detections[0, i, j, 1:] * scale).cpu().numpy()
                        bbox = (pt[0], pt[1], pt[2], pt[3], score)
                        bboxes = np.vstack((bboxes, bbox))
                        j += 1

            keep = nms_(bboxes, 0.1)
            bboxes = bboxes[keep]

        return bboxes
    
    def detect_faces_batch(self, images, shape, conf_th=0.8):

        bboxes_list = []

        with torch.no_grad():
            # for s in scales:
            # scaled_imgs = []
            # for image in images:
            #     w, h = image.shape[1], image.shape[0]
            #     scaled_img = cv2.resize(image, dsize=(0, 0), fx=s, fy=s, interpolation=cv2.INTER_LINEAR)

            #     scaled_img = np.swapaxes(scaled_img, 1, 2)
            #     scaled_img = np.swapaxes(scaled_img, 1, 0)
            #     scaled_img = scaled_img[[2, 1, 0], :, :]
            #     scaled_img = scaled_img.astype('float32')
            #     scaled_img -= img_mean
            #     scaled_img = scaled_img[[2, 1, 0], :, :]
            #     scaled_imgs.append(scaled_img)
            w,h = shape[0], shape[1]
            # print('batch width:{}. height:{}'.format(w,h))
            x = images.to(self.device)
            # print('size:',images.size())
            # x = torch.stack([torch.from_numpy(img) for img in scaled_imgs]).to(self.device)
            y = self.net(x)
            
            # print(y.shape) # [32,2,750,5]
            for idx, detections in enumerate(y): # process one image at a time
                bboxes = np.empty(shape=(0, 5))
                scale = torch.Tensor([w, h, w, h])
                # print(detections.shape) #[2,750,5]
                for i in range(detections.size(0)):
                    j = 0
                    while detections[i, j, 0] > conf_th:
                        score = detections[i, j, 0]
                        pt = (detections[i, j, 1:] * scale).cpu().numpy()
                        bbox = (pt[0], pt[1], pt[2], pt[3], score)
                        bboxes = np.vstack((bboxes, bbox))
                        j += 1

                keep = nms_(bboxes, 0.1)
                bboxes = bboxes[keep]
                bboxes_list.append(bboxes)
        # print('bboxes_list[0] shape:',bboxes_list[0].shape) #[1,5]
        return bboxes_list
