import os
import pickle
import cv2
import face_recognition
import numpy as np
import cvzone
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'student.db')
encoding_path = os.path.join(BASE_DIR, 'EncodeFile.p')

cap=cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)
background_path = os.path.join(BASE_DIR, "Resources", "background.jpg")
imgbackground = cv2.imread(background_path)


foldermodepath = os.path.join(BASE_DIR, "Resources", "modes")
modepathlist = os.listdir(foldermodepath)
imgModeList=[]
for path in modepathlist:
    imgModeList.append(cv2.imread(os.path.join(foldermodepath,path)))
#print(len(imgModeList))

print("loading encode file.....")
file = open(encoding_path, "rb")
encodelistknownwithIDs=pickle.load(file)
file.close()
encodelistknown,studentIds =encodelistknownwithIDs
print(studentIds)
print("Encode file loaded")

modetype=0
counter=0
id=0
last_id = None
frame_counter = 0
while True:
    success , img = cap.read()
    frame_counter += 1

    imgs=cv2.resize(img,(0,0),None,0.25,0.25)
    imgs=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

    faceCurrFr=face_recognition.face_locations(imgs)
    encodeCurrFr=face_recognition.face_encodings(imgs,faceCurrFr)

    #img = cv2.flip(img, 1)
    imgbackground[162:162+480,55:55+640]=img
    imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modetype]
    recognized_id = None

    if faceCurrFr:
        for encodeface,faceloc in zip(encodeCurrFr,faceCurrFr):
            matches=face_recognition.compare_faces(encodelistknown,encodeface)
            facedis=face_recognition.face_distance(encodelistknown,encodeface)
            #print('matches :',matches)
            #print('distance :',facedis)
            matchindex=np.argmin(facedis)
            #print(matchindex)
            if matches[matchindex]:
                #print(studentIds[matchindex])
                recognized_id = studentIds[matchindex]
                if recognized_id != id:
                    id = recognized_id
                    counter = 0
                y1,x2,y2,x1=faceloc
                y1, x2, y2, x1=(y1*4,x2*4,y2*4,x1*4)

                scale_factor = 0.3  # Adjust this factor as needed
                bbox = (int((-80 + x1) * scale_factor), int((200 + y1) * scale_factor), int((x2 - x1) * scale_factor),int((y2 - y1) * scale_factor))
                imgbackground = cvzone.cornerRect(imgbackground, bbox, rt=0)
                id=studentIds[matchindex]
                if counter==0:
                    counter=1
                    modetype=1

        if counter != 0:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE student_id = ?", (id,))
            studentinfo = cursor.fetchone()
            if counter == 1:
                if studentinfo:

                    datetimeobject = datetime.datetime.strptime(studentinfo[6], "%Y-%m-%d %H:%M:%S")
                    Timelapsed = (datetime.datetime.now() - datetimeobject).total_seconds()
                   # print(Timelapsed)

                    if Timelapsed>30:
                        studentinfo_placeholder = studentinfo[:-2] + ("<image blob data>",) + studentinfo[-1:]
                        #print("Student Found (with placeholder):", studentinfo_placeholder)
                        # Use the Database module's cursor/connection for updating
                        cursor.execute("SELECT total_attendance FROM students WHERE student_id = ?", (id,))
                        current_attendance = cursor.fetchone()[0]
                        updated_attendance = current_attendance + 1
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        cursor.execute("""
                                UPDATE students 
                                SET total_attendance = ?, 
                                    last_attendance_time = ? 
                                WHERE student_id = ?
                            """, (updated_attendance, current_time, id))
                        conn.commit()
                        conn.close()


                        def blob_to_image_file(blob_data, output_path=os.path.join(BASE_DIR, "recreated_student_image.jpg")):
                            with open(output_path, "wb") as file:
                                file.write(blob_data)
                            print(f"Image saved as {output_path}")


                        student_image_blob = studentinfo[7]
                        blob_to_image_file(student_image_blob)
                    else:
                        modetype=3
                        counter=0
                        imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modetype]


                else:
                    print(f"Student not found in the database with ID {id}")

            # Show student data for first 10 frames
            if modetype!=3:
                if 10 < counter < 20:
                    modetype = 2
                    imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modetype]
                if counter <= 10:
                    cv2.putText(imgbackground, str(studentinfo[4]), (870, 120), cv2.FONT_HERSHEY_COMPLEX,
                                1, (255, 255, 255), 1)
                    cv2.putText(imgbackground, str(studentinfo[2]), (1006, 550), cv2.FONT_HERSHEY_COMPLEX,
                                0.6, (255, 255, 255), 1)
                    cv2.putText(imgbackground, str(studentinfo[0]), (1006, 493), cv2.FONT_HERSHEY_COMPLEX,
                                0.6, (255, 255, 255), 1)
                    cv2.putText(imgbackground, str(studentinfo[5]), (1025, 625), cv2.FONT_HERSHEY_COMPLEX,
                                0.8, (100, 100, 100), 1)
                    cv2.putText(imgbackground, str(studentinfo[3]), (1125, 625), cv2.FONT_HERSHEY_COMPLEX,
                                0.7, (100, 100, 100), 1)
                    cv2.putText(imgbackground, str(studentinfo[8]), (910, 625), cv2.FONT_HERSHEY_COMPLEX,
                                0.7, (100, 100, 100), 1)
                    (w, h), _ = cv2.getTextSize(studentinfo[1], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgbackground, str(studentinfo[1]), (808 + offset, 430), cv2.FONT_HERSHEY_COMPLEX,
                                1, (100, 100, 100), 1)
                    student_img = cv2.imread(os.path.join(BASE_DIR, 'recreated_student_image.jpg'))
                    student_img_resized = cv2.resize(student_img, (216, 216), interpolation=cv2.INTER_AREA)
                    imgbackground[175:175 + 216, 909:909 + 216] = student_img_resized

                counter += 1

                # Reset after 20 frames and allow re-detection
                if counter > 20:
                    counter = 0
                    modetype = 0
                    id = None
                    imgbackground[44:44 + 633, 808:808 + 414] = imgModeList[modetype]
    else:
        modetype=0
        counter=0

    cv2.imshow("Face Attendance", imgbackground)
    cv2.waitKey(1)
    key = cv2.waitKey(1)
    if key == 27:  # Exit on ESC key
        break

cap.release()
cv2.destroyAllWindows()