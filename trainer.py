import cv2
import math
import time
import numpy as np
import mediapipe as mp

cap = cv2.VideoCapture(0) # 0 -> default webcam

class poseDetector():

    def __init__(self, mode=False, upBody=False, smooth=True, detectionCon=0.5, trackCon=0.5):

        self.mode = mode
        self.upBody = upBody
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose()

    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)
        return img

    def findPosition(self, img, draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        return self.lmList

    def findAngle(self, img, p1, p2, p3, draw=True):

        # Get the landmarks
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        x3, y3 = self.lmList[p3][1:]

        angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
        if angle < 0:
            angle += 360
        # Draw
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
            cv2.line(img, (x3, y3), (x2, y2), (255, 255, 255), 3)
            cv2.circle(img, (x1, y1), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x1, y1), 15, (0, 0, 255), 2)
            cv2.circle(img, (x2, y2), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (0, 0, 255), 2)
            cv2.circle(img, (x3, y3), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x3, y3), 15, (0, 0, 255), 2)
            cv2.putText(img, str(int(angle)), (x2 - 50, y2 + 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
        return angle

def empty(a) :
    pass

detector = poseDetector()
countReps = 0
countSets = 0
dir = 0
pTime = 0

cv2.namedWindow('Settings')  # Creating trackbars to isolate required color
cv2.resizeWindow('Settings', 450, 150)
cv2.createTrackbar('Arm', 'Settings', 0, 1, empty)
cv2.createTrackbar('Reps', 'Settings', 1, 16, empty)
cv2.createTrackbar('Sets', 'Settings', 1, 8, empty)

while True:

    isLeft = cv2.getTrackbarPos('Arm', 'Settings')
    targetReps = cv2.getTrackbarPos('Reps', 'Settings')
    targetSets = cv2.getTrackbarPos('Sets', 'Settings')

    success, img = cap.read()
    img = cv2.resize(img, (854, 480))

    img = detector.findPose(img, False)
    lmList = detector.findPosition(img, False)
    if len(lmList) != 0:

        if isLeft == 0:  # Left Arm
            angle = detector.findAngle(img, 11, 13, 15)

        if isLeft == 1:  # Right Arm
            angle = detector.findAngle(img, 12, 14, 16)

        per = np.interp(angle, (210, 310), (0, 100))
        bar = np.interp(angle, (220, 310), (450, 100))

        # Check for full range of motion
        color = (255, 0, 255)
        if per == 100:
            color = (0, 255, 0)
            if dir == 0:
                countReps += 0.5
                dir = 1
        if per == 0:
            color = (0, 255, 0)
            if dir == 1:
                countReps += 0.5
                dir = 0

        cv2.putText(img, 'Set your targets and preferences in the trackbar window before you start', (20, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)
        cv2.putText(img, 'The arm setting indicates which arm you would like to work out (left : 0 & right : 1)', (20, 40), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)
        cv2.putText(img, 'Make sure the left side of your body faces the camera', (20, 60), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 1)

        # Draw Bar
        cv2.rectangle(img, (700, 100), (775, 450), color, 3)
        cv2.rectangle(img, (700, int(bar)), (775, 450), color, cv2.FILLED)
        cv2.putText(img, f'{int(per)}%', (700, 85), cv2.FONT_HERSHEY_PLAIN, 2, color, 2)

        # Draw Curl Count
        cv2.putText(img, str(int(countReps))+'/'+str(int(countSets)), (45, 380), cv2.FONT_HERSHEY_PLAIN, 7, (0, 255, 0), 10)
        cv2.putText(img, f'Target : {targetReps}/{targetSets}', (45, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (50, 150), cv2.FONT_HERSHEY_PLAIN, 3,(255, 0, 0), 5)

    if countReps == targetReps :
        countSets += 1
        countReps = 0

    if countSets >= targetSets :
        cv2.putText(img, 'Target reached', (50, 470), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 255), 2)

    cv2.imshow("Bicep curl assistant", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break