import argparse
import time
import os
from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized
import time
import logging
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, dump, ElementTree

def detect(save_img=False):
    logging.basicConfig(filename='detect.log', level=logging.INFO)
    source, weights, view_img, save_txt, imgsz = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://'))
    
    imglist = opt.imlist
    print('this is imglist = ', imglist)
    source_list = source.split('\n') 
    
    # Directories
    save_dir = Path(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir
#     save_dir = Path(increment_path(Path(opt.project) / opt.name))  # increment run
#     (save_dir / 'labels' if save_txt else save_dir).mkdir  # make dir

    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    if half:
        model.half()  # to FP16

    # Second-stage classifier
    classify = False
    if classify:
        modelc = load_classifier(name='resnet101', n=2)  # initialize
        modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()

    # Set Dataloader
    vid_path, vid_writer = None, None
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    else:
        save_img = True
        if imglist:
            dataset_list = []
            for i in range(len(source_list)):
                print("source_list : ", source_list[i])
                try:
                    dataset_list.append(LoadImages(source_list[i], img_size=imgsz, stride=stride))
                except:
                    print("error!!!!!: ", source_list[i])

        else:    
            dataset = LoadImages(source, img_size=imgsz, stride=stride)
    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
    t0 = time.time()
    
     #sujin
    if imglist:
        j = len(dataset_list)
        print("imglist True,  j = ", j)
    else:
        j = 1
        
    print("j = ", j)
    count = 0
    for k in range(j):

        if imglist:
            dataset = dataset_list[k]
            for path, img, im0s, vid_cap in dataset:

                img = torch.from_numpy(img).to(device)
                img = img.half() if half else img.float()  # uint8 to fp16/32
                img /= 255.0  # 0 - 255 to 0.0 - 1.0


                if img.ndimension() == 3:
                    img = img.unsqueeze(0)

                # Inference
                t1 = time_synchronized()
                pred = model(img, augment=opt.augment)[0]

                # Apply NMS
                pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
                t2 = time_synchronized()

                # Apply Classifier
                if classify:
                    pred = apply_classifier(pred, modelc, img, im0s)
                prevTime = 0

                # Process detections
                for i, det in enumerate(pred):  # detections per image

                    curTime = time.time() * 1000
                    sec = curTime - prevTime
                    prevTime = curTime #이전 시간을 현재시간으로 다시 저장시킴

                    if webcam:  # batch_size >= 1
                        p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
                        fps_ = 1/(sec)

                    else:
                        p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

                    p = Path(p)  # to Path
                    print("p.name=", p.name)

                    save_path = str(save_dir / p.name)  # img.jpg
                    txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # img.txt
                    s += '%gx%g ' % img.shape[2:]  # print string
                    gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh

                    if len(det):
                        # Rescale boxes from img_size to im0 size
                        det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                        # Print results
                        for c in det[:, -1].unique():
                            n = (det[:, -1] == c).sum()  # detections per class
                            s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                        # Write results
                        for *xyxy, conf, cls in reversed(det):
                            if save_txt:  # Write to file
                                xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                                line = (cls, *xywh, conf) if opt.save_conf else (cls, *xywh)  # label format
                                with open(txt_path + '.txt', 'a') as f:
                                    f.write(('%g ' * len(line)).rstrip() % line + '\n')

                            if save_img or view_img:  # Add bbox to image
                                label = f'{names[int(cls)]} {conf:.2f}'
                                pt_start = time.time()*1000

                                plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=3)

                                pt_end = time.time()*1000  
                                
                        
                        if os.path.exists('./data/team_awesometech/')  == False: 
                        	os.makedirs('./data/team_awesometech/')
                                                	
                        with open('./data/team_awesometech/' + p.name[4:-4] + '.txt', 'w') as f:
                            xmin=(int(xyxy[0]))
                            ymin=(int(xyxy[1]))
                            xmax=(int(xyxy[2]))
                            ymax=(int(xyxy[3]))
                            h, w, bs = im0.shape

                            print("bs h w = ",bs, h,  w)
                            absolute_x = xmin + 0.5 * (xmax - xmin)
                            absolute_y = ymin + 0.5 * (ymax - ymin)

                            absolute_width = xmax - xmin
                            absolute_height = ymax - ymin

                            x = str(absolute_x / w)
                            y = str(absolute_y / h)
                            width = str(absolute_width / w)
                            height = str(absolute_height / h)

                            f.write(str(int(cls))+ " " + x + " " + y + " " + width + " " + height)
                            count += 1
                    else:
                        tl = 3 or round(0.002 * (im0.shape[0] + im0.shape[1]) / 2) + 1  # line/font thickness
                        tf = max(tl - 1, 1)  # font thickness

                        cv2.putText(im0, "0", (0, 100), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


                    # Print time (inference + NMS)
                    print(f'{s}Done. ({t2 - t1:.3f}s)')

                    # Stream results
                    if view_img:
                        cv2.imshow(str(p), im0)
                        cv2.waitKey(1)  # 1 millisecond

                    # Save results (image with detections)
                    if save_img:
                        if dataset.mode == 'image':
                            print("Save path=", save_path)
                            cv2.imwrite(save_path, im0)
                        else:  # 'video'
                            if vid_path != save_path:  # new video
                                vid_path = save_path
                                if isinstance(vid_writer, cv2.VideoWriter):
                                    vid_writer.release()  # release previous video writer

                                fourcc = 'mp4v'  # output video codec
                                fps = int(vid_cap.get(cv2.CAP_PROP_FPS))
                                print("fps is : ", fps)
                                w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*fourcc), fps, (w, h))
                            vid_writer.write(im0)

    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        print(f"Results saved to {save_dir}{s}")

    print(f'Done. ({time.time() - t0:.3f}s)')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default='yolov5s.pt', help='model.pt path(s)')
    parser.add_argument('--source', type=str, default='data/images', help='source')  # file/folder, 0 for webcam
    parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='display results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default='runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--imlist', action='store_true', help='existing project/name ok, do not increment')

    opt = parser.parse_args()
    print(opt)
    check_requirements()
    
    detect_start = time.time()*1000
    print("detect start : ", detect_start)
    
    with torch.no_grad():
        if opt.update:  # update all models (to fix SourceChangeWarning)
            for opt.weights in ['yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt']:
                detect()
                strip_optimizer(opt.weights)
        else:
            detect()
    
    detect_end = time.time()*1000-detect_start
    logging.info("hfgf"+str(detect_end))
    print("detect time : ", time.time()*1000-detect_start)
    

def test(source = ' ', weights =' ', imlist= True):
	print('this is detect_inhwa.py')
	parser = argparse.ArgumentParser()
	parser.add_argument('--weights', nargs='+', type=str, default='yolov5s.pt', help='model.pt path(s)')
	parser.add_argument('--source', type=str, default='data/images', help='source')  # file/folder, 0 for webcam
	parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
	parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
	parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
	parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
	parser.add_argument('--view-img', action='store_true', help='display results')
	parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
	parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
	parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
	parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
	parser.add_argument('--augment', action='store_true', help='augmented inference')
	parser.add_argument('--update', action='store_true', help='update all models')
	parser.add_argument('--project', default='runs/detect', help='save results to project/name')
	parser.add_argument('--name', default='exp', help='save results to project/name')
	parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
	parser.add_argument('--imlist', action='store_true', help='existing project/name ok, do not increment')
	
	global opt
	opt = parser.parse_args()
	opt.source = source
	opt.imlist = True
	
	
	opt.weights= [weights]
	print('this is image list: ', opt.imlist)
	
	check_requirements()

	detect_start = time.time()*1000
	print("detect start : ", detect_start)
	
	with torch.no_grad():
		detect()
	
	detect_end = time.time()*1000-detect_start
	logging.info("hfgf"+str(detect_end))
	print("detect time : ", time.time()*1000-detect_start)
