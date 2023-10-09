# LTP Trace -- Hans Kruse 2023
#import math
import sys
import os
if (len(sys.argv) < 2):
    print("Usage: python ltptrace.py <filename>")
    quit()
INFILE=sys.argv[1]
#INFILE = "ltp-summary.txt" # need to pull file from command line late
infilename=os.path.basename(INFILE)
#PLOTFILE = "ltp-summary.xpl"
infilename = os.path.splitext(infilename)
while (infilename[1] != ""):
    infilename = os.path.splitext(infilename[0])

PLOTFILE = infilename[0]+".xpl"
print("Writing to",PLOTFILE)

class Segment:
    def __init__(self,datastring):
#        self.error="ok"
        items = datastring.split("\t")
        self.frame=int(items[0])
        self.time=float(items[1])
        self.type=int(items[7],0)
        ips=items[2].split(",")
        self.ports=items[3].split(",")
        if self.type < 8 :
            self.dsource=ips[0]
            self.ddest=ips[1]
        else:
            self.dsource=ips[1]
            self.ddest=ips[0]
        self.session=int(items[4])
        if self.type < 8 :
            self.offset=int(items[5])
            self.length=int(items[6])
        else:
            self.offset=-1
            self.length=-1
            if self.type == 8 :
                self.rptCount=int(items[8])
                temp=items[9].split(",")
                self.rptOffset = [int(x) for x in temp]
                temp=items[10].split(",")
                self.rptLength = [int(x) for x in temp]
class SessionData:
    def __init__(self,segment):
        self.count=1
        self.time_min=segment.time
        self.time_max=self.time_min
        self.data_start=segment.offset
        self.data_end=segment.offset+segment.length
        self.session=segment.session
    def update(self,segment):
        self.count+=1
        self.time_min=min(segment.time,self.time_min)
        self.time_max=max(segment.time,self.time_max)
        self.data_start=min(self.data_start,segment.offset)
        self.data_end=max(self.data_end,segment.offset+segment.length)


segList = []
session_list = {}

ofh = open(PLOTFILE,"w")
ifh = open(INFILE)
for line in ifh.readlines():
    segList.append(Segment(line))

print(len(segList), "segments found")
time0=segList[0].time
time1=time0
source=segList[0].dsource
#
# scan for sessions
#
currSession=segList[0].session
print("IP",source,"First session:",currSession)
for segment in segList:
    if segment.dsource == source:
        currTime=segment.time-time0
        currSession=segment.session
        if currSession not in session_list.keys():
            session_list[currSession]=SessionData(segment)
        else:
            session_list[currSession].update(segment)
        if segment.type < 8 :
            data=segment.offset+segment.length
            print("darrow",currTime,segment.offset,file=ofh)
            print("rtext",currTime,segment.offset,file=ofh)
            print("_",currSession,file=ofh)
            print("uarrow",currTime,segment.offset+segment.length,file=ofh)
            print("line",currTime,segment.offset,currTime,segment.offset+segment.length,file=ofh)
        elif segment.type == 8 :
            print("Report segment at",currTime,",",segment.rptCount,"claims")
            for i in range(0,segment.rptCount) :
                print("dline",currTime,segment.rptOffset[i],currTime,segment.rptOffset[i]+segment.rptLength[i],file=ofh)
                print("rtext",currTime,segment.rptOffset[i],file=ofh)
                print("_",currSession,file=ofh)
print("=== Session report ===")
print("Session, Segments, Start, End, Data(kB), Rate")
for s in session_list.keys():
    sdata=(session_list[s].data_end-session_list[s].data_start)/1000
    print(f'{s:8}',f'{session_list[s].count:6}',f'{(session_list[s].time_min-time0):8.4f}', \
          f'{(session_list[s].time_max-time0):8.4f}', \
          sdata,f'{(8*sdata/(session_list[s].time_max-session_list[s].time_min)/1000):8.3f}Mbps')
ifh.close()
ofh.close()
