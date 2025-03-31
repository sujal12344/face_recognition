from datetime import datetime
import pickle
import cv2
import os
import face_recognition
import numpy as np
import cvzone
from firebase_admin import credentials, db
import firebase_admin
import time
import threading

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-fb9f2-default-rtdb.firebaseio.com/"
})

# Cache for student data to avoid repeated database calls
student_cache = {}

# Track which students have already been marked in this session
marked_attendance = set()

# Function to get student info with caching
def get_student_info(student_id):
    if student_id in student_cache:
        return student_cache[student_id]
    student_info = db.reference(f'Students/{student_id}').get()
    student_cache[student_id] = student_info
    return student_info

# Function to update attendance in a separate thread
def update_attendance(student_id, attendance_count):
    ref = db.reference(f'Students/{student_id}')
    ref.child('total_attendance').set(attendance_count)
    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load background image once
imgBackground = cv2.imread('Resources/background.png')

# Load mode images once
folderModePath = 'Resources/modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
print(len(imgModeList))

# Load already marked image if it exists
already_marked_img = None
if os.path.exists('rec/4.png'):
    already_marked_img = cv2.imread('rec/4.png')
    if already_marked_img is not None:
        already_marked_img = cv2.resize(already_marked_img, (414, 633))

# Load encodings
print("Loading the encoded file...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print("Encoded file loaded...")

# Preload student images to avoid disk I/O during recognition
student_images = {}
for student_id in studentIds:
    img_path = f'images/{student_id}.png'
    if os.path.exists(img_path):
        img = cv2.imread(img_path)
        if img is not None:
            student_images[student_id] = cv2.resize(img, (216, 216))

modeType = 0
counter = 0
id = -1
imgStudent = None
frame_skip = 2  # Process every 3rd frame for better performance
frame_count = 0
last_id = None
last_recognition_time = 0
recognition_cooldown = 1.0  # Reduced cooldown for better responsiveness
is_unknown_face = False
is_already_marked = False
display_message_until = 0
unknown_counter = 0

while True:
    success, img = cap.read()
    if not success:
        print("Failed to capture frame")
        continue
    
    # Skip frames to improve performance
    frame_count += 1
    if frame_count % frame_skip != 0 and id == -1 and not is_unknown_face and not is_already_marked:
        # Always show the current frame in the background
        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        cv2.imshow("Face Attendance", imgBackground)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break
        continue

    # Resize image for face recognition (even smaller for faster processing)
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    
    # Reset unknown face status if not actively detecting one
    current_time = time.time()
    if current_time > display_message_until:
        is_unknown_face = False
        is_already_marked = False
    
    # Process face recognition only if enough time has passed since last recognition
    if current_time - last_recognition_time >= recognition_cooldown or id == -1:
        faceCurFrame = face_recognition.face_locations(imgS)
        
        if faceCurFrame:
            encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
            
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                
                # Check if any match found
                if True in matches:
                    matchIndex = np.argmin(faceDis)
                    
                    if matches[matchIndex]:
                        y1, x2, y2, x1 = faceLoc
                        y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                        bbox = 55+x1, 162+y1, x2-x1, y2-y1
                        imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                        id = studentIds[matchIndex]
                        
                        # Check if student already marked attendance in this session
                        if id in marked_attendance:
                            # Show already marked message and special image
                            is_already_marked = True
                            display_message_until = current_time + 3.0  # Show for 3 seconds
                            
                            # Display the already marked image if available
                            if already_marked_img is not None:
                                imgBackground[44:44 + 633, 808:808 + 414] = already_marked_img
                            else:
                                # Fallback to a mode image
                                modeType = 3  # Use mode 3 for already marked (if available)
                                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList)-1)]
                            
                            # Display "Already Marked" message prominently
                            cvzone.putTextRect(imgBackground, "Already Marked!", (275, 400), 
                                            colorR=(0, 0, 255), scale=2, thickness=2)
                            
                            # Still get student info to display details
                            if last_id != id:
                                studentInfo = get_student_info(id)
                                last_id = id
                                last_recognition_time = current_time
                                
                                # Display student info text
                                cv2.putText(imgBackground, str(studentInfo['name']), (275, 350), 
                                            cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)
                        else:
                            if id != last_id:
                                counter = 0
                                last_id = id
                                last_recognition_time = current_time
                            
                            if counter == 0:
                                cvzone.putTextRect(imgBackground, "Loading...", (275, 400))
                                cv2.imshow("Face Attendance", imgBackground)
                                cv2.waitKey(1)
                                counter = 1
                                modeType = 1
                else:
                    # Handle unknown face
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
                    bbox = 55+x1, 162+y1, x2-x1, y2-y1
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0, colorR=(0, 0, 255))
                    
                    # Set unknown face status and display timer
                    is_unknown_face = True
                    display_message_until = current_time + 2.0  # Show for 2 seconds
                    unknown_counter = 10  # Show for 10 frames
                    
                    # Display unauthorized message
                    cvzone.putTextRect(imgBackground, "Unauthorized Person!", (200, 400), 
                                     colorR=(0, 0, 255), scale=1.5, thickness=2)
    
    # Show the current frame in background
    imgBackground[162:162 + 480, 55:55 + 640] = img
    
    # Handle unknown face counter
    if is_unknown_face:
        if unknown_counter > 0:
            cvzone.putTextRect(imgBackground, "Unauthorized Person!", (200, 400), 
                             colorR=(0, 0, 255), scale=1.5, thickness=2)
            unknown_counter -= 1
        else:
            is_unknown_face = False
    
    # Normal processing for recognized faces
    if counter != 0 and not is_already_marked and not is_unknown_face:
        if counter == 1:
            # Get student info (cached if already fetched)
            studentInfo = get_student_info(id)
            print("Student recognized:", studentInfo['name'])
            
            # Use preloaded image if available
            if id in student_images:
                imgStudent = student_images[id]
                imgBackground[175:175+216, 909:909+216] = imgStudent
            
            # Update attendance only if not already marked in this session
            if id not in marked_attendance:
                datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                
                if secondsElapsed > 30:
                    studentInfo['total_attendance'] += 1
                    # Update database in a separate thread
                    threading.Thread(target=update_attendance, 
                                    args=(id, studentInfo['total_attendance'])).start()
                    student_cache[id] = studentInfo  # Update the cache
                    
                    # Add to marked attendance set to prevent repeated marking
                    marked_attendance.add(id)
                else:
                    modeType = 3
                    counter = 0
        
        if 10 < counter < 20:
            modeType = 2
        
        if not is_already_marked:  # Only update mode image if not showing "already marked"
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList)-1)]
        
        if modeType != 3 and counter <= 10 and 'studentInfo' in locals():
            # Display student information only when needed
            cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550), 
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(id), (1006, 493), 
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625), 
                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
            cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625), 
                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
            cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625), 
                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
            
            (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
            offset = (414-w)//2
            cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)
            
            if imgStudent is not None:
                imgBackground[175:175+216, 909:909+216] = imgStudent
        
        counter += 1
        
        if counter >= 20:
            counter = 0
            modeType = 0
            studentInfo = None
            imgStudent = None
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList)-1)]
    
    elif not is_already_marked and not is_unknown_face:
        modeType = 0
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[min(modeType, len(imgModeList)-1)]
    
    cv2.imshow("Face Attendance", imgBackground)
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()