import json
import argparse
import sys
import cv2
import numpy as np
from datetime import datetime

draw_color = (0,0,0)
pencil_thickness = 5

def initialization():
    # Definição dos argumentos de entrada:
    parser = argparse.ArgumentParser(description='Ar Paint ')
    parser.add_argument('-j','--json',type = str, required= True, help='Full path to json file')
    parser.add_argument('-usp','--use_shake_prevention', action='store_true', help='Use shake prevention mode')
    args = vars(parser.parse_args())

    path = 'limits.json' if not args['json'] else args['json'] # A localização do ficheiro json
    usp = args['use_shake_prevention'] # Ativacao do use shake mode
    return path , usp

def readFile(path):
    try:
        with open(path, 'r') as openfile:
            json_object = json.load(openfile)
            limits = json_object['limits']
    # if the file doesn't exist, send out an error message and quit
    except FileNotFoundError:
        sys.exit('The .json file with the color data doesn\'t exist.')

    return limits

def get_centroid(mask) :
    # find all contours (objects)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    
    # if we detect objects, let's find the biggest one, make it green and calculate the centroid
    if cnts:

        # find the biggest object
        cnt = max(cnts, key=cv2.contourArea)

        # make it green (but still show other objects in white)
        biggest_obj = np.zeros(mask.shape, np.uint8)
        cv2.drawContours(biggest_obj, [cnt], -1, 255, cv2.FILLED)
        biggest_obj = cv2.bitwise_and(mask, biggest_obj) # mask-like image with only the biggest object
        all_other_objs = cv2.bitwise_xor(mask, biggest_obj) # all other objects except the biggest one
        
        b = all_other_objs
        g = mask
        r = all_other_objs

        image_result = cv2.merge((b, g, r))

        # calculate centroid coordinates
        M = cv2.moments(cnt)
        cX = int(M["m10"] / M["m00"]) if (M["m00"]!=0) else None
        cY = int(M["m01"] / M["m00"]) if (M["m00"]!=0) else None

        # draw small red cross to indicate the centroid point
        if cX: # it's enough to check either cX or cY, if one is None then both are None
            cv2.line(image_result, (cX-8, cY-8), (cX+8, cY+8), (0, 0, 255), 5)
            cv2.line(image_result, (cX+8, cY-8), (cX-8, cY+8), (0, 0, 255), 5)

    # if we don't detect any objects, we just show the mask as it is
    else:
        image_result = cv2.merge((mask, mask, mask))
        cX = None
        cY = None
        
    return (cX,cY), image_result 

def key_press(input,canvas):
    global draw_color, pencil_thickness
    if input == chr(255):
        print(input)
    match input:
            # quit program
        case 'q':
            return False
            # change color to Red
        case 'r':
            draw_color = (0,0,255)
            # change color to Green
        case 'g':
            draw_color = (0,255,0)
            # change color to Blue
        case 'b':
            draw_color = (255,0,0)
            # decrease pencil size
        case '-':
            if pencil_thickness > 0:
                pencil_thickness -= 5
            # increase pencil size
        case '+':
            if pencil_thickness < 50:
                pencil_thickness += 5
            #clear canvas
        case 'c':
            canvas.fill(255)
            # save canvas 
        case 'w':
            date = datetime.now()
            formatted_date = date.strftime("%a_%b_%d_%H:%M:%S")
            name_canvas = 'drawing_' + formatted_date + '.png'
            cv2.imwrite(name_canvas, canvas)
    return True
        

def main():
    global draw_color, pencil_thickness
    # setting up the video capture
    path, usp = initialization()
    ranges = readFile(path) 

    capture = cv2.VideoCapture(0)
    _, frame = capture.read()
    cv2.imshow("Original window",frame)

    height,width,_ = np.shape(frame)
    paint_window = np.zeros((height,width,4))
    paint_window.fill(255)
    cv2.imshow("Paint Window",paint_window)

    range_lows = (ranges['R']['min'], ranges['G']['min'], ranges['B']['min'])
    range_highs = (ranges['R']['max'], ranges['G']['max'], ranges['B']['max'])
        
    ## Operação em contínuo ##
    while True:
        _,frame = capture.read()
        
        frame_mask = cv2.inRange(frame, range_lows, range_highs)

        frame_wMask = cv2.bitwise_and(frame,frame, mask = frame_mask)
        cv2.imshow("Original window",frame_wMask)
        
        (cx,cy),frame_test = get_centroid(frame_mask)
        cv2.imshow("test window", frame_test)

        k = cv2.waitKey(1) & 0xFF
        if not key_press(str(chr(k)),paint_window) : break

        # 1st way - line connecting the current point to the previous position
        try:
            cv2.line(paint_window, (cx,cy),(cx_past,cy_past), draw_color, pencil_thickness) 
            cx_past, cy_past = cx ,cy
        except:
            cx_past, cy_past = cx ,cy
        # 2nd way - circle in the current position (skips due to reading delay)
        # cv2.circle(paint_window, (cx,cy), 1, draw_color, pencil_thickness) 
        cv2.imshow("Paint Window",paint_window)
    capture.release()
    cv2.destroyAllWindows()



if __name__ == '__main__':
    main()