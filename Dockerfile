
FROM python:3.7


#평가자가 마운트 해줄 폴더를 이미지내에 생성
#mount directory
RUN mkdir /data


#개발환경에서 동작하던 프로그램을 이미지속으로 복사
#Make a folder in the docker file system
#RUN mkdir /src

#copy your program to docker file system
#ADD labels ./labels 일단 지워봄
ADD models ./models
ADD utils ./utils
COPY detect.py ./
COPY fileio_test.py ./
COPY train95_735.pt ./
COPY requirements.txt ./

RUN pip3 install -r requirements.txt

RUN apt update
RUN apt-get install libgl1-mesa-glx -y

# 이미지가 평가위원에 의해서 컨테이너 변환후 실행될 때 수행되는 명령어
#execute when docker image is running
CMD ["python3", "./fileio_test.py"] 


