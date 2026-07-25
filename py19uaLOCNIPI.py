'''
Completed as of 01/05/23
Code was developed on macOS 12.5.1 M1 with Python 3.7.13 and OpenCV 4.1.0.

This script is for analysing droplets in the LOC-NIPI apparatus. It will count droplets,
measure their diameters and velocities, and count freezing events. The script is fixed
to analyse videos captured at a frame rate of 177fps of a channel width of 300 microns.

Required input files:
    ***.mp4 : The MP4 file is of the droplets passing through the LOC-NIPI. The script
    works best with MP4 files, AVI files can sometimes cause errors depending on the version 
    of Python being used. VLC media player can be used to convert AVI to MP4.
    ***.png : The image is a screen capture of a frozen droplet. No particular file type
    is needed, PNG and JPEG work fine.

Output: 
    data.csv : File containing all the gathered information about the droplets in the 
    LOC-NIPI. Will automatically create and save file. File can be found in C:\\Users\\username.
    
Usage and requirements: 
    0) Install all needed packages, e.g., OpenCV.
    1) Once ran, the GUI will appear, select 'Browse Image File' and select your
    image of the frozen droplet.
    2) Then select 'Browse Video File' and select the LOC-NIPI recording.
    3) A window for channel wall sampling will then appear, select the upper channel 
    and lower channel wall three times each.
    4) A window for background intensity calibration will appear, select a few points
    (at least one) in the region where the cold plate is expected to be.
    5) A window for frozen droplet intensity calibration will appear, select a few points
    (at least one) on the droplet.
    6) The first region of interest (ROI) selection window will appear, select the region
    where the cold plate lies. Then the second ROI selection window will appear, select
    the leftmost region of the channel, ideally around a third of the total channel length.
    7) The program will begin running and write the found values to the data.csv file. Once
    the video has run its course, all values will be averaged and inserted in the last row 
    of the data.csv file.

Questions: py19ua@leeds.ac.uk 
'''

import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog
import time
import csv

class VideoPlayer(tk.Frame):
    def __init__(self, master):
        """Initialises all objects needed throughout the script.
        """  
        super().__init__(master)
        self.master = master
        self.master.title("LOC-NIPI Analyser")
        self.video_source = ""

        #Block below creates a csv file called data and formats, if one exists with 
        # name 'data.csv' then clear file and reformat. 
        data = ['Frame count:', 'Time elapsed (seconds):','Total droplet count:',
                'Total frozen droplet count:', 'Live Velocity (microns/second)',
                'Live Diameter (microns):' ]
        with open('data.csv', mode='w', newline='') as file:
            file.truncate()
            writer = csv.writer(file)
            writer.writerow(data)
            
        self.speedavg=[]
        self.diameters=[]
        self.diameter=0

        # First window for droplet counter and velocity tracker.
        self.canvas = tk.Canvas(self.master, width=500, height=200)
        self.canvas.create_text(250, 10, text="Droplet Counter & Velocity Tracker")
        self.canvas.pack()

        # Second window for freeze detector.
        self.canvas1 = tk.Canvas(self.master, width=500, height=200)
        self.canvas1.create_text(250, 10, text="Frozen Droplet Counter")
        self.canvas1.pack()

        # Creates first text box for droplet information.
        self.text = tk.Text(self.master, width=50, height=10)
        self.text.pack()

        # Creates second text box for video information.
        self.text1 = tk.Text(self.master, width=50, height=10)
        self.text1.pack()

        # Creates the background subtractor needed.
        self.back_sub = cv2.createBackgroundSubtractorMOG2()

        # Particle counter
        self.particle_count = 0
        
        # Temporary variable to hold distance travelled of each particle.
        self.distance = 0

        # Particle distance storage.
        self.particle_distances = []

        # Counts the frames each time it loops through the video.
        self.framecount=[]

        ################################
        # Objects needed for speed calculation.

        # Counts the number of frames when there is a droplet present.
        self.activeframes=0

        # Stores the speed for each droplet.
        self.speed=0

        # Stores the distances in a list.
        self.distancelist=[]
        ################################
        # Objects needed for the frozen detector.

        self.colors=[]
        self.t=[]
        self.countarray=[]
        self.areaarray=[]

        self.freezeSanityChecker=[]
        self.vidtime=0
        
        ################################

    def click_event(self,event, x, y, flags, params):
        '''
        Extracts information on click events, in this case: x and y coords.
        '''
        
        # Looks for left button clicks.
        if event == cv2.EVENT_LBUTTONDOWN:
    
            print(x, ' ', y)
            
            params.append(y)
            
            # Prints the coords on the cropped frame
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(self.cap_chan_width, str(x) + ',' +
                        str(y), (x,y), font,
                        1, (255, 0, 0), 2)
            
            cv2.imshow('Channel Width Finder', self.cap_chan_width)
        
        return params
    
    def channelPlotter(self):
        '''
        Processes the information extracted by the click_event function.
        '''
        by=[]
        _, self.cap_chan_width = self.cap.read()
        cv2.putText(self.cap_chan_width,
                            str('Please select upper channel and lower channel 3 times'), 
                            (5, 40), 
                            cv2.FONT_HERSHEY_PLAIN, 1.7, (255, 0, 0),2)
        cv2.putText(self.cap_chan_width, str('Press q once done'), 
                            (5, 70), 
                            cv2.FONT_HERSHEY_PLAIN, 1.7, (255, 0, 0),2)
        cv2.imshow('Channel Width Finder', self.cap_chan_width)
        
        cv2.setMouseCallback('Channel Width Finder', self.click_event, by)
        
        # wait for a key to be pressed to exit
        while True:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # close the window
        cv2.destroyAllWindows()
        
        # The logic below sorts the list of pixel values and calculated the average width.
        by.sort()
        chan=[]
        for i in range(6):
            
            if i > 2:
                break
            
            diff=by[-(i+1)]-by[i]
            chan.append(diff)
        
        avgchan=sum(chan)/len(chan)
        return avgchan
    
    def browse_file(self):
        '''
        Browses for video file.
        '''
        self.video_source = filedialog.askopenfilename()
        self.play()

    def browse_imagefile(self):
        '''
        Browses for image file.
        '''
        self.image_source = filedialog.askopenfilename()

    def imageProcessing(self):
        '''
        Image cleaning for droplet detection (diameter measurement etc).
        '''
        gray = cv2.cvtColor(self.framer, cv2.COLOR_BGR2GRAY)

        # applies the background subtraction
        foreground_mask = self.back_sub.apply(gray)
        
        # removes noise in the foreground mask, and blurs
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        foreground_mask = cv2.morphologyEx(foreground_mask, cv2.MORPH_CLOSE, kernel)
        foreground_mask = cv2.medianBlur(foreground_mask, 9)

        # finds circles in the foreground mask.
        self.circles = cv2.HoughCircles(foreground_mask, cv2.HOUGH_GRADIENT, 
                                dp=1, minDist=100, param1=100, param2=10, 
                                minRadius=0, maxRadius=100)

        return foreground_mask
    
    def estimate_droplet_diameter(self):
        '''
        Finds the largest circle from the Hough circle transform.
        '''
        # Finds the largest circle assuming that it's the droplet.
        max_circle = max(self.circles[0], key=lambda x: x[2])
        print(self.circles)
        print(max_circle)
        # Gets the diameter of the circle.
        self.diameter = 2 * max_circle[2]

    def update_textbox(self):
        '''
        Updates the first text box with the latest droplet information.
        '''
        self.particle_count=int(self.particle_count)
        self.distance=int(self.distance)
        self.speed=int(self.speed)

        n1 = 'Droplet count: {}\n'.format(self.particle_count) 
        n2 = 'Distance travelled (px): {}\n'.format(self.distance) 
        n3 = 'Live Velocity (microns/second): {}\n'.format(self.speed) 
       
        
        self.text.delete('1.0', tk.END) # delete the current text
        self.text.insert(tk.END, n1) # insert the new text
        self.text.insert(tk.END, n2)
        self.text.insert(tk.END, n3)

        # logic to avoid errors div by 0 errors.
        if len(self.diameters)>0:
            buffer=int(sum(self.diameters)/len(self.diameters))
            n4 = 'Live Average Diameter (microns): {}\n'.format(buffer)

        if len(self.countarray)>0:
            n5 = 'Frozen Droplet Count: {}\n'.format(len(self.countarray))
            self.text.insert(tk.END, n5)
        
    def update_textbox1(self):
        '''
        Updates the second text box with the latest video information.
        Updates csv with rows of new information.
        '''
        
        n1 = (
            'Frame count: '
            + str(len(self.framecount))
            + '/'
            + str(self.tot_frames)
            + '\n'
            )
        n2 = (
            'Time elapsed (seconds): '
            + str(int(len(self.framecount) / self.fps))
            + '/'
            + str(int(self.duration))
        )

        self.text1.delete('1.0', tk.END) # delete the current text
        self.text1.insert(tk.END, n1) # insert the new text
        self.text1.insert(tk.END, n2) # insert the new text

        # Conditional statements below to update and add rows to the 
        # csv file with new info. 
        # Logic to avoid div by zero errors.
        if len(self.diameters)>0:

            data = [str(int(len(self.framecount)))+ '/' 
                    + str(int(self.tot_frames)), 
                    str(len(self.framecount)/self.fps) + '/' + str(self.duration),
                    self.particle_count,len(self.countarray),
                    int(self.speed),int(self.microndiameter)]  
        
        #int(sum(self.diameters)/len(self.diameters))
        else:
            data = [str(int(len(self.framecount)))+ '/' 
                    + str(int(self.tot_frames)), 
                    str(len(self.framecount)/self.fps) + '/' + str(self.duration),
                    self.particle_count,len(self.countarray),
                    int(self.speed),0]  

        with open('data.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)

    def on_mouse_click_background (self,event, x, y, flags, frame):
        '''
        Extracts information on click events for sampling the
        background colour.
        '''
        
        if event == cv2.EVENT_LBUTTONUP:
            sample = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.colors.append(sample[y,x].tolist())
            cv2.circle(frame,(x,y),12,(255,0,0),3)

    def on_mouse_click_droplet (self,event, x, y, flags, frame):
        '''
        Extracts information on click events for sampling the
        frozen droplet colour.
        '''
        
        if event == cv2.EVENT_LBUTTONUP:
            sample = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.colors.append(sample[y,x].tolist())

    def eyeDropper(self,ans):
        '''
        Extracts information on click events for sampling the
        frozen droplet colour.
        '''
        self.colors=[]
        if ans == 'vid':
            _, frame = self.cap.read()

            while True:
                sample = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if self.colors:
                    cv2.putText(sample, str(self.colors), (450, 40),
                                 cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0),2)
                cv2.imshow('Background Colour Sampler (Eye Dropper Tool A)', sample)
                cv2.setMouseCallback('Background Colour Sampler (Eye Dropper Tool A)',
                                      self.on_mouse_click_background, frame)

                
                # press q once done.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        if ans =='pic':
            self.capImage = cv2.imread(self.image_source) 
            frame = self.capImage

            while True:
                sample = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if self.colors:
                    cv2.putText(sample, str(self.colors), (450, 40),
                                 cv2.FONT_HERSHEY_PLAIN, 2,
                                   (255, 0, 0),2)
                cv2.imshow('Frozen Droplet Colour Sampler (Eye Dropper Tool B)', sample)
                cv2.setMouseCallback('Frozen Droplet Colour Sampler (Eye Dropper Tool B)',
                                      self.on_mouse_click_droplet, frame)
                
                # press q once done.
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        print(self.colors)
        ColorList=self.colors
        cv2.destroyAllWindows()

        return ColorList

    def freezeImageProcessing(self):
        '''
        Image processing for frozen droplet detection.
        '''
        # This will blur the frames slightly to get rid of granularity and hence
        # an easier freeze detection.
        blur = cv2.medianBlur(self.framerfreeze, 9)

        # Calculations below find halfway point between frozen droplet colour and background.
        self.backgroundColor=sum(self.backgroundColorList)/len(self.backgroundColorList)
        self.frozenDropletColor=sum(self.frozenDropletColorList)/len(self.frozenDropletColorList)
        self.lim_back=int((self.frozenDropletColor+self.backgroundColor)/2)
        
        #This will change the frame to greyscale, and threshold based on the calibrated value.
        gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, self.lim_back ,255, cv2.THRESH_BINARY_INV)[1]
        return gray, thresh

    def speedCalc(self):
        '''
        Speed calcuation based on active frames and pixel distance. 1/176
        is the capture frame rate. 300 for the channel width being fixed
        at 300 microns.
        '''
        self.micronsTravelled=(self.distance/self.avgC)*300
        speed=self.micronsTravelled/(self.activeframes*(1/176))

        return speed

    def play(self):
        labelList=[]
        # Sets initial droplet distance to none.
        prevPt = None
        # Collects the capture data from the video pathway.
        self.cap = cv2.VideoCapture(self.video_source)
        # Gets number of total frames in video
        self.tot_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Gets total video time.
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)   
        self.duration = self.tot_frames/self.fps
        # Puts total frame count and total video duration in the second textbox.
        self.text1.insert(tk.END, f'Total frames:{self.tot_frames} Duration:{self.duration}')
        ###########
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.avgC=self.channelPlotter()
        print(self.avgC)
        self.backgroundColorList=self.eyeDropper('vid')
        self.frozenDropletColorList=self.eyeDropper('pic')
        # Gets the region of interest coordiantes for the coldplate, and 
        # the furthest left channel region.
        ret, firstFrame = self.cap.read()
        self.rfreeze = cv2.selectROI('Cold Plate ROI (Frozen Droplet Detection Area)',firstFrame)
        self.r = cv2.selectROI('Furthest Left ROI (Droplet Counting/Tracking)',firstFrame)

        while True:
            # Reads self.cap.read() will read the frame from the video 
            # that is being looped through.
            ret, frame = self.cap.read()
            if ret:
                # Process the frame here
                # self.framer is the far left ROI and self.framerfreeze is the cold plate area
                self.framer = frame[int(self.r[1]):int(self.r[1]+self.r[3]),
                                     int(self.r[0]):int(self.r[0]+self.r[2])]
                self.framerfreeze = frame[int(self.rfreeze[1]):int(self.rfreeze[1]
                                                                   + self.rfreeze[3]),
                                           int(self.rfreeze[0]):int(self.rfreeze[0]
                                                                    + self.rfreeze[2])]
                
                self.framecount.append(1)
                self.update_textbox1()
                foregroundMask=self.imageProcessing()
                ################# Circle Diameter Stuff ##################
                self.microndiameter=0
                if self.circles is not None:
                    # Conditional statement checks for detected circles, then processes.
                    self.estimate_droplet_diameter()
                    # Conversion to microns.
                    self.microndiameter=(self.diameter/self.avgC)*300
                    self.diameters.append(self.microndiameter)
                    

                    # Draws the largest circle and displays the diameter on the frame
                    for circle in self.circles[0, :]:
                        center = (int(circle[0]), int(circle[1]))
                        radius = int(circle[2])
                        cv2.circle(self.framer, center, radius, (0, 255, 0), 2)

                ##########################################################

                ################# Freeze Event Counting Stuff ##################
                # Finds an extracts contours from the processed frame.
                self.framerfreeze, thresh = self.freezeImageProcessing()
                cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = cnts[0] if len(cnts) == 2 else cnts[1]

                for c in cnts:
                    #Uses the cv2 module to find the area of the contour.
                    area = cv2.contourArea(c)
                    # Square box of chan width is (self.avgC)^2 is max and the 
                    # avg size of droplet is 100micron diam. So do min of 50micron.
                    if  (self.avgC/6)**2 < area < (self.avgC)**2:
                        #Draws the contouring line around the area.
                        cv2.drawContours(self.framerfreeze,[c], 0, (36,255,12), 2)

                        #Once it has met criteria and fell into it statement, 1 
                        # is added to the count array.
                        self.countarray.append(1)
                        print(self.countarray)
                        
                        #Saved the area of the freezing event into the array.
                        self.areaarray.append(area)

                        # Double check it against the main count to make sure
                        #  artefacts aren't detected.
                        self.freezeSanityChecker.append(self.particle_count)
                        
                        # Conditional statement making sure that freezing event
                        #  from only once frame was
                        # accepted, sometimes freezing events appear in more
                        #  than one frame and to avoid
                        # double counting or accepting an artefact, it was
                        #  compared to the main droplets count.
                        if (len(self.freezeSanityChecker) >= 2 and
                                self.freezeSanityChecker[-1] == self.freezeSanityChecker[-2]):

                            # Deletes the extra count and areas.
                            del self.countarray[-1]
                            del self.areaarray[-1]
            
                #Puts the count of the freezing events on the frame.
                self.framerfreeze = cv2.putText(self.framerfreeze,
                                                str(len(self.countarray)), (520, 40),
                                                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0),2)
                self.update_textbox()
                ##########################################################

                ################# Droplet Detection Counting Stuff ##################

                # Labels all the connected components in the foreground mask.
                (num_labels, labels, stats, centroids
                ) = cv2.connectedComponentsWithStats(foregroundMask, connectivity=8)

                
                ######UPTIL HERE######14/4/23
                    
                labelList.append(num_labels)
                
                if len(self.framecount) != 1 and num_labels >1:
                
                    x, y, w, h, area = stats[1]
                    # Draws a bounding rectangle around the droplet.
                    cv2.rectangle(self.framer, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # Counts the amount of frames where there is a present 
                    self.activeframes +=1

                    # Get the center of the droplet
                    centerX, centerY = int(centroids[1][0]), int(centroids[1][1])
                    cv2.circle(self.framer, (centerX, centerY), 5, (0, 0, 255), -1)
                    
                    # Condition to check if a new particle has entered the frame.
                    # else: it will assume the particle isn't a new particle entering the frame.
                    if prevPt is None:
                        # increment particle count
                        self.particle_count += 1

                        self.update_textbox()
                        # Initialises distance at 0 and adds to a list.
                        self.distance = 0
                        self.distancelist.append(self.distance)
                    else:
                        # Increments the distance value by calulating the distance 
                        # the droplet moved from the previous previous point (prevPt).
                        self.distance += np.sqrt(
                            (centerX - prevPt[0])**2 + (centerY - prevPt[1])**2
                        )
                        cv2.putText(self.framer, "Distance: {:.2f} pixels".format(self.distance),
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.6, (0, 0, 255), 2)
                    
                        ####### Speed Calculation Stuff #######
                        self.speed=self.speedCalc()
                        # Calculates the speed between frames then adds to list of speed values.
                        self.speedavg.append(self.speed)

                        # Updates the live output and saves the distance moved in a list.
                        self.update_textbox()
                        self.distancelist.append(self.distance)
                    # Assigns a previous point after droplet parameter processing.
                    prevPt = (centerX, centerY)

                # Checks if the droplet has left the frame.
                if len(labelList)>2 and labelList[-1]==1 and labelList[-2]>1 :
                    # store the final total distance traveled by the droplet
                    self.particle_distances.append(self.distance)
                    print(
                        f'Particle {self.particle_count} left the frame, '
                        f'distance traveled: {self.distance} pixels'
                        )
                    # Resets all the information from the last droplet.
                    prevPt = None
                    self.activeframes=0
                    self.speed=0

                cv2.waitKey(1)
                # Allows the video feeds to be displayed in the GUI. 
                photo = tk.PhotoImage(data=cv2.imencode('.png', self.framer)[1].tobytes())
                self.canvas.create_image(250,50, image=photo, anchor=tk.CENTER)
                photo1 = tk.PhotoImage(data=cv2.imencode('.png', foregroundMask)[1].tobytes())
                self.canvas.create_image(250,120, image=photo1, anchor=tk.CENTER)

                # Same as above but for the second canvas.
                photo0 = tk.PhotoImage(data=cv2.imencode('.png', self.framerfreeze)[1].tobytes())
                self.canvas1.create_image(250,50, image=photo0, anchor=tk.CENTER)
                photo01 = tk.PhotoImage(data=cv2.imencode('.png', thresh)[1].tobytes())
                self.canvas1.create_image(250,120, image=photo01, anchor=tk.CENTER)
                self.master.update()
            
            # Once all frames in the video have been looped through, the final 
            # totals/averages are added to the data.csv file.
            else:
                data = [str(int(len(self.framecount)))+ '/' + str(int(self.tot_frames)), 
                    str(len(self.framecount)/self.fps) + '/' + str(self.duration),
                    self.particle_count,len(self.countarray),
                    int(sum(self.speedavg)/len(self.speedavg)),
                    int(sum(self.diameters)/len(self.diameters))] 
                with open('data.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(data)
                break

root = tk.Tk()
root.geometry("400x800")
player = VideoPlayer(root)
player.pack()

browse_button = tk.Button(root, text="Browse Video File", command=player.browse_file)
browse_button.pack()

browse_button1 = tk.Button(root, text="Browse Image File", command=player.browse_imagefile)
browse_button1.pack()

root.mainloop()


