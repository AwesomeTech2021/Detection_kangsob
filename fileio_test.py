import os 
#from pillow import Image
from glob import glob
import detect


print("TEAM AWESOMETECH")
# source data path
ImagesDATA_dir = "./data/images/"
#ImagesDATA_dir = '/media/kennethso/usbusb/data_test/images/'

# Team data directoru shoud be uniquely created
#꼭 끝이 / 로 끝나야한다.
teamDATA_dir = "./data/team_awesometech/"
#teamDATA_dir = '/media/kennethso/9015-6F9D/data_test/team_awesometech'
if os.path.exists(teamDATA_dir) ==False :
	os.makedirs(teamDATA_dir)

source ='./data/dev.txt'
#weights = './yolov3_45_best.pt'
#weights = './train95_735.pt'
weights = './best.pt'

dev_img_list = glob(ImagesDATA_dir+'*.jpg')

print('DIRS SETTING...')
print('Images Directory : ',ImagesDATA_dir) 
print('Result Directory : ',teamDATA_dir)
print('WEIGHT LOCATION : ',weights)
print('IMAGES SIZE = ',len(dev_img_list))

with open(source,'w') as f:
	f.write('\n'.join(dev_img_list) + '\n')
	
with open(source,'r') as f:
	img_list = f.read()
	
detect.do_detect(source=img_list ,imlist=True, weights=weights, result=teamDATA_dir)

#filelist = os.listdir(ImagesDATA_dir)

#sorted_filelist = sorted(filelist)

#for name in sorted_filelist :
#	imgsrc = os.path.join(ImagesDATA_dir, name)
#	image = Image.load(imgsrc).convert('RGB')
#	
#	#Detect Object and store the result
#	data = model(image)
#	
#	name = os.paht.splitext(name)[0] + '.txt'
#	fdes = open(TeamDATA_dir+'/'+name,"w")
#	fdes.write(' '.join(str(b) for b in data+'\n')
#	fdes.close()

