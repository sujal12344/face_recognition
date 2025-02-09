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

while True:
    sucess, img = cap.read()

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[2]    #===>modes shift

    # cv2.imshow("WebCam", img)
    cv2.imshow("Face Attendance",imgBackground)
    cv2.waitKey(1)