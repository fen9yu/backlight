import numpy as np
import cv2
import os
import re
import sys
import math
from diffdetect import imdiff
from binary_search_edge import search_v_edge
from binary_search_edge import search_h_edge
from edge_detect import edge_detect
from angle_detect import angle_detect

side=64 #the length of side for cutting images
margin=6 #if defects are in the range of margin, it will not be marked neither 0 nor 1. To improve accuracy.
#the offset of the starting point
if len(sys.argv)==1:
	offset=0
elif len(sys.argv)==2:
	offset=int(sys.argv[1])
else:
	print("too much arguments")

#get all the files/directory in the current directory
files=os.listdir("./")
origpath=os.getcwd()
date=os.path.split(os.getcwd())[1]
#open a txt file which named by the directory(date recommanded), in order to write in it
with open(os.path.split(os.getcwd())[0]+'/train.txt','a') as f:
	for image in files:
		#only deal with the images start with "a" and include decfect type 10, e.g.: a12-1002.bmp
		if re.match(r'^a.*?-10.*',image)==None or os.path.exists('./_'+image):
			continue

		#remove images with more than one type of defect, which need manual process
		#you can decide whether to use it or not
		if re.match(r'.*?-.*?-.*?',image)!=None:
			continue

		seg=[]
		img = cv2.imread(image,0)

		#find the coordinate of defects
		image2 = 'b'+re.match(r'^a(\S*?).bmp',image).group(1)+'.png'
		img2 = cv2.imread(image2,0)
		defect = imdiff(img,img2)

		#find the angle of the backlight panel with respect to the border of the picture
		ang=angle_detect(img)
		#rotate the picture so that the backlight panel is put straight
		rows,cols=img.shape
		M0 = cv2.getRotationMatrix2D((cols/2,rows/2),-ang*180/math.pi,1)
		img = cv2.warpAffine(img,M0,(cols,rows))

		#detect the border of the backlight panel in the rotated picture
		up,down,left,right=edge_detect(img)
		#select the region of backlight panel in the picture
		img=img[int(round(up[0])):int(round(down[0])),int(round(left[1])):int(round(right[1]))]

		#transformation matrix
		tm=np.array([[math.cos(ang),math.sin(ang),(1-math.cos(ang))*cols/2-math.sin(ang)*rows/2],[-math.sin(ang),math.cos(ang),math.sin(ang)*cols/2+(1-math.cos(ang))*rows/2],[0,0,1]])
		#coordinate of the defects after rotation
		defectrot=[]
		#calculate the coordinate of the defects after rotation
		for i in range(len(defect)):
			df=np.array([[defect[i][0]],[defect[i][1]],[1]])
			prod=np.dot(tm,df)
			tempdefect=[prod[1][0],prod[0][0]]
			#calculate the coordinate of the defects after selecting the region of backlight panel
			defectrot.append([int(round(tempdefect[1]))-int(round(up[0])),int(round(tempdefect[0])-int(round(left[1])))])
		defect=defectrot


		#make a directory for each image and go into the directory
		#os.mkdir('_'+image)
		#os.chdir("./_"+image)
		remain_v=img.shape[0]-offset
		remain_h=img.shape[1]-offset
		i=0
		j=0

		#cut the images
		while remain_v > side:
			seg.append([])
			while remain_h > side:
				seg[i].append(img[side*i+offset:side*(i+1)+offset,side*j+offset:side*(j+1)+offset])
				imgname=date+'_'+image.split('.')[0]+'_'+str(i)+'_'+str(j)+'+'+str(offset)
				remain_h-=side
				'''if cv2.mean(seg[i][j])[0] < 3.9:
					j+=1
					continue'''
				
				#mark defect for cut images 0/1
				flag=0
				rows,cols=seg[i][j].shape
				for point in defect:
					if point[0]>i*side+offset and point[0]<(i+1)*side+offset and point[1]>j*side+offset and point[1]<(j+1)*side+offset:
						if point[0]>i*side+offset+margin and point[0]<(i+1)*side+offset-margin and point[1]>j*side+offset+margin and point[1]<(j+1)*side+offset-margin:
							M1 = cv2.getRotationMatrix2D((cols/2,rows/2),90,1)
							M2 = cv2.getRotationMatrix2D((cols/2,rows/2),180,1)
							M3 = cv2.getRotationMatrix2D((cols/2,rows/2),270,1)
							dst0f1=cv2.flip(seg[i][j],0)
							dst1 = cv2.warpAffine(seg[i][j],M1,(cols,rows))
							dst1f1=cv2.flip(dst1,0)
							dst2 = cv2.warpAffine(seg[i][j],M2,(cols,rows))
							dst2f1=cv2.flip(dst2,0)
							dst3 = cv2.warpAffine(seg[i][j],M3,(cols,rows))
							dst3f1=cv2.flip(dst3,0)
							imgname='1_'+imgname
							imgname1=imgname+'_0_0'+'.bmp'
							imgname1flip1=imgname+'_0_1'+'.bmp'
							imgname2=imgname+'_90_0'+'.bmp'
							imgname2flip1=imgname+'_90_1'+'.bmp'
							imgname3=imgname+'_180_0'+'.bmp'
							imgname3flip1=imgname+'_180_1'+'.bmp'
							imgname4=imgname+'_270_0'+'.bmp'
							imgname4flip1=imgname+'_270_1'+'.bmp'
							f.write(imgname1+' '+str(1)+'\n')
							f.write(imgname1flip1+' '+str(1)+'\n')
							f.write(imgname2+' '+str(1)+'\n')
							f.write(imgname2flip1+' '+str(1)+'\n')
							f.write(imgname3+' '+str(1)+'\n')
							f.write(imgname3flip1+' '+str(1)+'\n')
							f.write(imgname4+' '+str(1)+'\n')
							f.write(imgname4flip1+' '+str(1)+'\n')
							os.chdir(os.path.split(os.getcwd())[0])
							cv2.imwrite(imgname1,seg[i][j])
							cv2.imwrite(imgname1flip1,dst0f1)
							cv2.imwrite(imgname2,dst1)
							cv2.imwrite(imgname2flip1,dst1f1)
							cv2.imwrite(imgname3,dst2)
							cv2.imwrite(imgname3flip1,dst2f1)
							cv2.imwrite(imgname4,dst3)
							cv2.imwrite(imgname4flip1,dst3f1)
							os.chdir(origpath)
						flag=1
						break
					elif point[0]>i*side+offset-margin and point[0]<(i+1)*side+offset+margin and point[1]>j*side+offset-margin and point[1]<(j+1)*side+offset+margin:
						flag=-1
				if flag == 0:
					imgname='0_'+imgname+'.bmp'
					f.write(imgname+' '+str(0)+'\n')
					os.chdir(os.path.split(os.getcwd())[0])
					cv2.imwrite(imgname,seg[i][j])
					os.chdir(origpath)
				j+=1

			seg[i].append(img[side*i+offset:side*(i+1)+offset,img.shape[1]-side:img.shape[1]])
			imgname=date+'_'+image.split('.')[0]+'_'+str(i)+'_'+str(j)+'+'+str(offset)
			remain_h-=side
			'''if cv2.mean(seg[i][j])[0] < 3.9:
				j+=1
				continue'''
			
			#mark defect for cut images 0/1
			flag=0
			rows,cols=seg[i][j].shape
			for point in defect:
				if point[0]>i*side+offset and point[0]<(i+1)*side+offset and point[1]>j*side+offset and point[1]<(j+1)*side+offset:
					if point[0]>i*side+offset+margin and point[0]<(i+1)*side+offset-margin and point[1]>j*side+offset+margin and point[1]<(j+1)*side+offset-margin:
						M1 = cv2.getRotationMatrix2D((cols/2,rows/2),90,1)
						M2 = cv2.getRotationMatrix2D((cols/2,rows/2),180,1)
						M3 = cv2.getRotationMatrix2D((cols/2,rows/2),270,1)
						dst0f1=cv2.flip(seg[i][j],0)
						dst1 = cv2.warpAffine(seg[i][j],M1,(cols,rows))
						dst1f1=cv2.flip(dst1,0)
						dst2 = cv2.warpAffine(seg[i][j],M2,(cols,rows))
						dst2f1=cv2.flip(dst2,0)
						dst3 = cv2.warpAffine(seg[i][j],M3,(cols,rows))
						dst3f1=cv2.flip(dst3,0)
						imgname='1_'+imgname
						imgname1=imgname+'_0_0'+'.bmp'
						imgname1flip1=imgname+'_0_1'+'.bmp'
						imgname2=imgname+'_90_0'+'.bmp'
						imgname2flip1=imgname+'_90_1'+'.bmp'
						imgname3=imgname+'_180_0'+'.bmp'
						imgname3flip1=imgname+'_180_1'+'.bmp'
						imgname4=imgname+'_270_0'+'.bmp'
						imgname4flip1=imgname+'_270_1'+'.bmp'
						f.write(imgname1+' '+str(1)+'\n')
						f.write(imgname1flip1+' '+str(1)+'\n')
						f.write(imgname2+' '+str(1)+'\n')
						f.write(imgname2flip1+' '+str(1)+'\n')
						f.write(imgname3+' '+str(1)+'\n')
						f.write(imgname3flip1+' '+str(1)+'\n')
						f.write(imgname4+' '+str(1)+'\n')
						f.write(imgname4flip1+' '+str(1)+'\n')
						os.chdir(os.path.split(os.getcwd())[0])
						cv2.imwrite(imgname1,seg[i][j])
						cv2.imwrite(imgname1flip1,dst0f1)
						cv2.imwrite(imgname2,dst1)
						cv2.imwrite(imgname2flip1,dst1f1)
						cv2.imwrite(imgname3,dst2)
						cv2.imwrite(imgname3flip1,dst2f1)
						cv2.imwrite(imgname4,dst3)
						cv2.imwrite(imgname4flip1,dst3f1)
						os.chdir(origpath)
					flag=1
					break
				elif point[0]>i*side+offset-margin and point[0]<(i+1)*side+offset+margin and point[1]>j*side+offset-margin and point[1]<(j+1)*side+offset+margin:
					flag=-1
			if flag == 0:
				imgname='0_'+imgname+'.bmp'
				f.write(imgname+' '+str(0)+'\n')
				os.chdir(os.path.split(os.getcwd())[0])
				cv2.imwrite(imgname,seg[i][j])
				os.chdir(origpath)
			remain_v-=side
			remain_h=img.shape[1]-offset
			j=0
			i+=1
			
		seg.append([])
		while remain_h > side:
			seg[i].append(img[img.shape[0]-side:img.shape[0],side*j+offset:side*(j+1)+offset])
			imgname=date+'_'+image.split('.')[0]+'_'+str(i)+'_'+str(j)+'+'+str(offset)
			remain_h-=side
			'''if cv2.mean(seg[i][j])[0] < 3.9:
				j+=1
				continue'''
			
			#mark defect for cut images 0/1
			flag=0
			rows,cols=seg[i][j].shape
			for point in defect:
				if point[0]>i*side+offset and point[0]<(i+1)*side+offset and point[1]>j*side+offset and point[1]<(j+1)*side+offset:
					if point[0]>i*side+offset+margin and point[0]<(i+1)*side+offset-margin and point[1]>j*side+offset+margin and point[1]<(j+1)*side+offset-margin:
						M1 = cv2.getRotationMatrix2D((cols/2,rows/2),90,1)
						M2 = cv2.getRotationMatrix2D((cols/2,rows/2),180,1)
						M3 = cv2.getRotationMatrix2D((cols/2,rows/2),270,1)
						dst0f1=cv2.flip(seg[i][j],0)
						dst1 = cv2.warpAffine(seg[i][j],M1,(cols,rows))
						dst1f1=cv2.flip(dst1,0)
						dst2 = cv2.warpAffine(seg[i][j],M2,(cols,rows))
						dst2f1=cv2.flip(dst2,0)
						dst3 = cv2.warpAffine(seg[i][j],M3,(cols,rows))
						dst3f1=cv2.flip(dst3,0)
						imgname='1_'+imgname
						imgname1=imgname+'_0_0'+'.bmp'
						imgname1flip1=imgname+'_0_1'+'.bmp'
						imgname2=imgname+'_90_0'+'.bmp'
						imgname2flip1=imgname+'_90_1'+'.bmp'
						imgname3=imgname+'_180_0'+'.bmp'
						imgname3flip1=imgname+'_180_1'+'.bmp'
						imgname4=imgname+'_270_0'+'.bmp'
						imgname4flip1=imgname+'_270_1'+'.bmp'
						f.write(imgname1+' '+str(1)+'\n')
						f.write(imgname1flip1+' '+str(1)+'\n')
						f.write(imgname2+' '+str(1)+'\n')
						f.write(imgname2flip1+' '+str(1)+'\n')
						f.write(imgname3+' '+str(1)+'\n')
						f.write(imgname3flip1+' '+str(1)+'\n')
						f.write(imgname4+' '+str(1)+'\n')
						f.write(imgname4flip1+' '+str(1)+'\n')
						os.chdir(os.path.split(os.getcwd())[0])
						cv2.imwrite(imgname1,seg[i][j])
						cv2.imwrite(imgname1flip1,dst0f1)
						cv2.imwrite(imgname2,dst1)
						cv2.imwrite(imgname2flip1,dst1f1)
						cv2.imwrite(imgname3,dst2)
						cv2.imwrite(imgname3flip1,dst2f1)
						cv2.imwrite(imgname4,dst3)
						cv2.imwrite(imgname4flip1,dst3f1)
						os.chdir(origpath)
					flag=1
					break
				elif point[0]>i*side+offset-margin and point[0]<(i+1)*side+offset+margin and point[1]>j*side+offset-margin and point[1]<(j+1)*side+offset+margin:
					flag=-1
			if flag == 0:
				imgname='0_'+imgname+'.bmp'
				f.write(imgname+' '+str(0)+'\n')
				os.chdir(os.path.split(os.getcwd())[0])
				cv2.imwrite(imgname,seg[i][j])
				os.chdir(origpath)
			j+=1

		seg[i].append(img[img.shape[0]-side:img.shape[0],img.shape[1]-side:img.shape[1]])
		imgname=date+'_'+image.split('.')[0]+'_'+str(i)+'_'+str(j)+'+'+str(offset)
		remain_h-=side
		'''if cv2.mean(seg[i][j])[0] < 3.9:
			j+=1
			continue'''
		
		#mark defect for cut images 0/1
		flag=0
		rows,cols=seg[i][j].shape
		for point in defect:
			if point[0]>i*side+offset and point[0]<(i+1)*side+offset and point[1]>j*side+offset and point[1]<(j+1)*side+offset:
				if point[0]>i*side+offset+margin and point[0]<(i+1)*side+offset-margin and point[1]>j*side+offset+margin and point[1]<(j+1)*side+offset-margin:
					M1 = cv2.getRotationMatrix2D((cols/2,rows/2),90,1)
					M2 = cv2.getRotationMatrix2D((cols/2,rows/2),180,1)
					M3 = cv2.getRotationMatrix2D((cols/2,rows/2),270,1)
					dst0f1=cv2.flip(seg[i][j],0)
					dst1 = cv2.warpAffine(seg[i][j],M1,(cols,rows))
					dst1f1=cv2.flip(dst1,0)
					dst2 = cv2.warpAffine(seg[i][j],M2,(cols,rows))
					dst2f1=cv2.flip(dst2,0)
					dst3 = cv2.warpAffine(seg[i][j],M3,(cols,rows))
					dst3f1=cv2.flip(dst3,0)
					imgname='1_'+imgname
					imgname1=imgname+'_0_0'+'.bmp'
					imgname1flip1=imgname+'_0_1'+'.bmp'
					imgname2=imgname+'_90_0'+'.bmp'
					imgname2flip1=imgname+'_90_1'+'.bmp'
					imgname3=imgname+'_180_0'+'.bmp'
					imgname3flip1=imgname+'_180_1'+'.bmp'
					imgname4=imgname+'_270_0'+'.bmp'
					imgname4flip1=imgname+'_270_1'+'.bmp'
					f.write(imgname1+' '+str(1)+'\n')
					f.write(imgname1flip1+' '+str(1)+'\n')
					f.write(imgname2+' '+str(1)+'\n')
					f.write(imgname2flip1+' '+str(1)+'\n')
					f.write(imgname3+' '+str(1)+'\n')
					f.write(imgname3flip1+' '+str(1)+'\n')
					f.write(imgname4+' '+str(1)+'\n')
					f.write(imgname4flip1+' '+str(1)+'\n')
					os.chdir(os.path.split(os.getcwd())[0])
					cv2.imwrite(imgname1,seg[i][j])
					cv2.imwrite(imgname1flip1,dst0f1)
					cv2.imwrite(imgname2,dst1)
					cv2.imwrite(imgname2flip1,dst1f1)
					cv2.imwrite(imgname3,dst2)
					cv2.imwrite(imgname3flip1,dst2f1)
					cv2.imwrite(imgname4,dst3)
					cv2.imwrite(imgname4flip1,dst3f1)
					os.chdir(origpath)
				flag=1
				break
			elif point[0]>i*side+offset-margin and point[0]<(i+1)*side+offset+margin and point[1]>j*side+offset-margin and point[1]<(j+1)*side+offset+margin:
				flag=-1
		if flag == 0:
			imgname='0_'+imgname+'.bmp'
			f.write(imgname+' '+str(0)+'\n')
			os.chdir(os.path.split(os.getcwd())[0])
			cv2.imwrite(imgname,seg[i][j])
			os.chdir(origpath)
		remain_v-=side
		remain_h=img.shape[1]-offset
