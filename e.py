import cv2
import os
import pickle
import face_recognition

# importing student images
folderPath = 'images'
PathList = os.listdir(folderPath)
print(PathList)
imgList = []
studentIds = []
for path in PathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentIds.append(os.path.splitext(path)[0])

    fileName = f'{folderPath}/{path}'
    print(fileName)
    # bucket =storage.bucket()
    # blob = bucket.blob(fileName)
    # blob.upload_from_filename(fileName)
    # print(path)
    # print(os.path.splitext(path)[0])


print(studentIds)

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

print("Encodeing Started")
encodeListKnown = findEncodings(imgList)
print(encodeListKnown)
encodeListKnownWithIds = [encodeListKnown,studentIds]
print("Encoding Completed")

file = open("EncodeFile.p", 'wb')           #pickel file
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File saved")