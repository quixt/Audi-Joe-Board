import pyaudio;
import sys;
import wave
import threading
import time
import keyboard
p = pyaudio.PyAudio()

info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))



class Soundboard:
    def __init__(self, p):
        self.p = p
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.soundThreads = []
        self.micThreads = []
        keyboard.add_hotkey('ctrl+alt+1', self.createStream1)
        keyboard.add_hotkey('ctrl+alt+p', self.pauseAll)
        keyboard.add_hotkey('ctrl+alt+r', self.resumeAll)
        keyboard.add_hotkey('ctrl+alt+s', self.cancelAll)

        for i in range(0,19):
            self.soundThreads.append(None)
            self.micThreads.append(None)
        self.micThread = threading.Thread(target=self.micInput).start()
    def micInput(self):
        micStream = p.open(format=pyaudio.paInt16,rate=44100,channels=2,input=True,frames_per_buffer=1024)
        outputStream = p.open(format=pyaudio.paInt16,rate=44100,channels=2,output=True,output_device_index=5,frames_per_buffer=1024)
        while True:
            data = micStream.read(self.CHUNK)
            outputStream.write(data)
    def createStream1(self):
        if(self.getRecentStream() != None):
            print("Starting...")
            threading.Thread(target=self.playSoundOverSpeakers,args=("bettercallsaul.wav",self.getRecentStream(),)).start()
            threading.Thread(target=self.playSoundOverMic,args=("bettercallsaul.wav",self.getRecentStream(),)).start()
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

        

def stayOpen():
    while True:
        time.sleep(1)


soundboard = Soundboard(p)
threading.Thread(target=stayOpen).start()
# micThread = threading.Thread(target=outputFreeBirdOverMic)
# micThread.start()

# stream = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True, frames_per_buffer=1024, output_device_index=5)
# data = wf.readframes(CHUNK)
# while len(data):
#     stream.write(data)
#     data = wf.readframes(CHUNK)

# stream.stop_stream()
# stream.close()
