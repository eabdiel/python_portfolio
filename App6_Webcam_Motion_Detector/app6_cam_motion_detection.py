from datetime import datetime

import cv2  # cv2 is from opencv-python lib
import pandas

# Data and PVariables
first_frame = None
status_list = [None, None]
times = []
df = pandas.DataFrame(columns=["Start", "End"])
video = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # the cv2.CAP_DSHOW is to avoid warn errors on quit

# Start of code
while True:
    check, frame = video.read()
    status = 0
    # this is the active frame, the first time we'll assign this to the first_frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)  # blur the img to remove noise and increase accuracy
    # see opencv.org documentation for details

    if first_frame is None:
        first_frame = gray
        continue

    # calculate the different between the first and current frame
    delta_frame = cv2.absdiff(first_frame, gray)
    thresh_delta = cv2.threshold(delta_frame, 30, 255, cv2.THRESH_BINARY)[1]  # first value of the tuple is the frame
    thresh_frame = cv2.dilate(thresh_delta, None, iterations=2)  # the higher the iteration the smoother the image

    # find the contours
    (cnts, _) = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in cnts:
        if cv2.contourArea(contour) < 10000:  # 100 x 100 px
            continue
        status = 1  # if something changes on the frame, this keeps the contour on it

        # this draws the rectangle
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
    status_list.append(status)

    if status_list[-1] == 1 and status_list[-2] == 0:
        times.append(datetime.now())
    if status_list[-1] == 0 and status_list[-2] == 1:
        times.append(datetime.now())

    cv2.imshow('Gray Frame', gray)  # name of the 1st window, and type of output
    cv2.imshow('Delta Frame', delta_frame)
    cv2.imshow('Threshold Frame', thresh_frame)
    cv2.imshow('Color Frame', frame)

    key = cv2.waitKey(1)

    if key == ord('q'):  # key to exit program
        if status == 1:
            times.append(datetime.now)
        break

print(status_list)
print(times)

for i in range(0, len(times), 2):
    df = df.append({"Start": times[i], "End": times[i + 1]}, ignore_index=True)
df.to_csv("Log.csv")
video.release()
cv2.destroyAllWindows()

# github.com/eabdiel