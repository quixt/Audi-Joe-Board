import ffmpeg
import pyaudio;
import sys;
import wave
import threading
import time
import keyboard
import shutil
import os
import pickle


from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QMainWindow
import PyQt6.QtWidgets as QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSlot
from PyQt6 import QtGui
soundsChoiceFile = None
try:
    soundsChoiceFile = pickle.load(open("sounds.pickle", "rb"))
except:
    soundsChoiceFile = [None, None, None, None, None, None, None, None, None, None]
    pickle.dump(soundsChoiceFile, open("sounds.pickle", "wb"))
#Initialize the pyaudio object
p = pyaudio.PyAudio()

#Create the pyqt app (for selecting soundboard)
app = QApplication([])


#Get the device information for selecting the output and input devices
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))



class Soundboard:
    def __init__(self, p, audioFiles):
        self.p = p
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.soundThreads = []
        self.micThreads = []
        self.audioFiles = audioFiles
        self.startHookHotkeys()
        keyboard.add_hotkey('ctrl+alt+p', self.pauseAll)
        keyboard.add_hotkey('ctrl+alt+r', self.resumeAll)
        keyboard.add_hotkey('ctrl+alt+s', self.cancelAll)
        # self.audioFiles = [None, None, None, None, None, None, None, None, None, None]
        
        for i in range(0,19):
            self.soundThreads.append(None)
            self.micThreads.append(None)
        self.micThread = threading.Thread(target=self.micInput).start()
    def startHookHotkeys(self):
        for i in range(0,9):
            self.hookHotkey(i)
    def unhookHotkey(self, i):
        keyboard.remove_hotkey('ctrl+alt+'+str(i+1))
    def hookHotkey(self,i):
        keyboard.add_hotkey('ctrl+alt+'+str(i+1), self.createStream,args=(self.audioFiles[i],))
    def micInput(self):
        micStream = p.open(format=pyaudio.paInt16,rate=44100,channels=2,input=True,frames_per_buffer=1024)
        outputStream = p.open(format=pyaudio.paInt16,rate=44100,channels=2,output=True,output_device_index=5,frames_per_buffer=1024)
        while True:
            data = micStream.read(self.CHUNK)
            outputStream.write(data)
    def createStream(self, filename:str):
        if(self.getRecentStream() != None and filename != None):
            print("Starting...")
            threading.Thread(target=self.playSoundOverSpeakers,args=(filename,self.getRecentStream(),)).start()
            threading.Thread(target=self.playSoundOverMic,args=(filename,self.getRecentStream(),)).start()
            #threading.Thread(target=self.playSoundOverMic,args=("freebirdsolo.wav",)).start()
    def resumeAll(self):
        for i in range(0,19):
            if self.soundThreads[i] != None and self.soundThreads[i]["paused"] == True:
                self.soundThreads[i]["stream"].start_stream()
                self.soundThreads[i]["paused"] = False
                self.micThreads[i]["stream"].start_stream()
                self.micThreads[i]["paused"] = False
    def cancelAll(self):
        for i in range(0,19):
            if self.soundThreads[i] != None:
                self.soundThreads[i]["paused"] = False
                self.soundThreads[i]["stream"].stop_stream()
                self.micThreads[i]["paused"] = False
                self.micThreads[i]["stream"].stop_stream()
                
        
    def pauseAll(self):
        for i in range(0,19):
            if self.soundThreads[i] != None:
                self.soundThreads[i]["paused"] = True
                self.soundThreads[i]["stream"].stop_stream()
                self.micThreads[i]["paused"] = True
                self.micThreads[i]["stream"].stop_stream()
    def getRecentStream(self):
        for i in range(0,19):
            if self.soundThreads[i] == None:
                return i
        return None
    def playSoundOverSpeakers(self, soundFile:str,recentStream:int):
        wf = wave.open(str(soundFile), 'rb')
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)
        
        rate = wf.getframerate()
        channels = wf.getnchannels()
        width = self.p.get_format_from_width(wf.getsampwidth())
        
        playStream = self.p.open(format=width,channels=channels, rate=rate,output=True,frames_per_buffer=self.CHUNK,output_device_index = 4, stream_callback = callback)
        self.soundThreads[recentStream] = {"stream":playStream, "paused":False}
        while (self.soundThreads[recentStream]["paused"] == False and playStream.is_active()) or (self.soundThreads[recentStream]["paused"] == True):
            time.sleep(0.1)
        playStream.close()
        wf.close()
        self.soundThreads[recentStream] = None
        exit()
    def playSoundOverMic(self, soundFile:str,recentStream:int):
        wf = wave.open(str(soundFile), 'rb')
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)
        
        rate = wf.getframerate()
        channels = wf.getnchannels()
        width = self.p.get_format_from_width(wf.getsampwidth())
        
        playStream = self.p.open(format=width,channels=channels, rate=rate,output=True,frames_per_buffer=self.CHUNK,output_device_index = 5, stream_callback = callback)
        self.micThreads[recentStream] = {"stream":playStream, "paused":False}
        while (self.micThreads[recentStream]["paused"] == False and playStream.is_active()) or (self.micThreads[recentStream]["paused"] == True):
            time.sleep(0.1)
        playStream.close()
        wf.close()
        self.micThreads[recentStream] = None
        exit()


    
class Application(QWidget):
    def __init__(self):
        super().__init__()
        global soundsChoiceFile
        self.setWindowTitle("Audi-Joe Board")
        self.setGeometry(100, 100, 1000, 500)
        titleMessage = QLabel("<h1>AUDI-JOE BOARD</h1>", parent=self)
        titleMessage.move(10, 10)
        uploadButton = QtWidgets.QPushButton("UPLOAD", parent=self)
        uploadButton.clicked.connect(self.fileUpload)
        uploadButton.resize(100, 50)
        uploadButton.move(10, 100)
        self.fileComboBox = QtWidgets.QComboBox(self)
        self.fileComboBox.move(10, 70)
        self.setComboItems()
        self.textLabels = []
        self.setSoundButtons = []
        for i in range(1,10):
            self.setSoundButtons.append(QtWidgets.QPushButton("SET SOUND " + str(i), parent=self))
            self.textLabels.append(QtWidgets.QLabel(str(soundsChoiceFile[i-1]), parent=self))
            self.textLabels[i-1].resize(95, 20)
            # if(i < 5):
            #     self.layout1.addWidget(self.setSoundButtons[i-1])
            # else:
            #     self.layout2.addWidget(self.setSoundButtons[i-1])
            self.setSoundButtons[i-1].resize(100, 50)
            if i > 5:
                self.textLabels[i-1].move(200 + ((i-1)%5 * 100), 330)
                self.setSoundButtons[i-1].move(200 + ((i-1)%5 * 100), 280)
            else:
                self.textLabels[i-1].move(200 + ((i-1) * 100), 250)
                self.setSoundButtons[i-1].move(200 + ((i-1) * 100), 200)
            
        self.setSoundButtons[0].clicked.connect(lambda: self.setSound(0))
        self.setSoundButtons[1].clicked.connect(lambda: self.setSound(1))
        self.setSoundButtons[2].clicked.connect(lambda: self.setSound(2))
        self.setSoundButtons[3].clicked.connect(lambda: self.setSound(3))
        self.setSoundButtons[4].clicked.connect(lambda: self.setSound(4))
        self.setSoundButtons[5].clicked.connect(lambda: self.setSound(5))
        self.setSoundButtons[6].clicked.connect(lambda: self.setSound(6))
        self.setSoundButtons[7].clicked.connect(lambda: self.setSound(7))
        self.setSoundButtons[8].clicked.connect(lambda: self.setSound(8))

    
    @pyqtSlot()
    def setSound(self,l):
        print(l)
        soundboard.audioFiles[l] = self.fileComboBox.currentText()
        self.textLabels[l].setText(self.fileComboBox.currentText())
        soundboard.unhookHotkey(l)
        soundboard.hookHotkey(l)
        pickle.dump(soundboard.audioFiles, open("sounds.pickle", "wb"))
        print(soundboard.audioFiles)
    def setComboItems(self):
        self.fileComboBox.addItems(self.getFiles())
    def getFiles(self):
        files = []
        for x in os.listdir():
            if x.endswith(".wav"):
                files.append(x)
        return files
        
    @pyqtSlot()
    def fileUpload(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self,'Open File', 'Downloads', "Audio Files (*.wav)")
        if(filename[0] != ""):
            
            file = filename[0].split("/",-1)[-1]
            if(file.split(".",-1)[-1] == "wav"):
                print("File: " + file)
                files = []
                for x in os.listdir():
                    if x.endswith(".wav"):
                        files.append(x)
                if(filename not in files):
                    shutil.copy(filename[0], ".")
        self.setComboItems()

soundboard = Soundboard(p, soundsChoiceFile)
# threading.Thread(target=stayOpen).start()
window = Application()
window.show()

sys.exit(app.exec())
