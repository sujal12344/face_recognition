import cv2
import os

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')

# importing modes images
folderModePath = 'Resources/modes'
modePathList = os.listdir(folderModePath)
imgModeList = []

for path in modePathList:
  imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

print(len(imgModeList))

# loding the encodeing file
print("loading the encoded file...")
file = open('EncodeFile.p', 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
print(studentIds)
print("encoded file loaded...")

modeType = 0
counter = 0
id = -1
imgStudent =[]

while True:
    sucess, img = cap.read()

    imgS = cv2.resize(img,(0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[2]    #===>modes shift

    # cv2.imshow("WebCam", img)
    cv2.imshow("Face Attendance",imgBackground)
    cv2.waitKey(1)