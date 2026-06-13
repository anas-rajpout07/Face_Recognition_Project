import cv2
import face_recognition
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
folderpath = os.path.join(BASE_DIR, 'Images')
encode_file_path = os.path.join(BASE_DIR, 'EncodeFile.p')

imgpathlist=os.listdir(folderpath)
print(imgpathlist)
imgList=[]
studentIds=[]
for path in imgpathlist:
    imgList.append(cv2.imread(os.path.join(folderpath,path)))
    studentIds.append(os.path.splitext(path)[0])
    #print(path)
    #print(os.path.splitext(path)[0])
print(studentIds)

def findEncoddings(imageslist):
    encodelist=[]
    for img in imageslist:
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode=face_recognition.face_encodings(img)[0]
        encodelist.append(encode)

    return encodelist

print("Encoding started....")
encodelistknown=findEncoddings(imgList)
encodelistknownwithIDs=[encodelistknown,studentIds]
#print(encodelistknownwithIDs)
print("Encoding completed")

file = open(encode_file_path, "wb")
pickle.dump(encodelistknownwithIDs,file)
file.close()
print("File Saved")


