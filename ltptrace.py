# LTP Trace -- Hans Kruse 2023
""" 
    Input: text file created by ltp-summary.sh
    Output: Summary of sessions found, and an xplot formatted file similar to the
    tcptrace time-sequence graph.
    Version 0.8.0
    - Sessions are processed in order of the time of the first segment in the session
    - In the graph, the cumulative data seen in previous sessions is added to data offsets to
        shift the segement indicators up on the y axis
    Missing/Limitations in 0.8.0
    - Green and Red data are not distinguished
    - Report acknowledgements are not processed
    - Checkpoints are not indicated on the graph
    - Cancel segments are not processed or graphed
    - ltptrace records the IP of the sender of the first segment and processes only sessions from the IP
"""
# Segment type list from RFC 5326
"""
   CTRL EXC Flag 1 Flag 0 Code  Nature of segment
   ---- --- ------ ------ ----  ---------------------------------------
     0   0     0      0     0   Red data, NOT {Checkpoint, EORP or EOB}
     0   0     0      1     1   Red data, Checkpoint, NOT {EORP or EOB}
     0   0     1      0     2   Red data, Checkpoint, EORP, NOT EOB
     0   0     1      1     3   Red data, Checkpoint, EORP, EOB

     0   1     0      0     4   Green data, NOT EOB
     0   1     0      1     5   Green data, undefined
     0   1     1      0     6   Green data, undefined
     0   1     1      1     7   Green data, EOB

     1   0     0      0     8   Report segment
     1   0     0      1     9   Report-acknowledgment segment
     1   0     1      0    10   Control segment, undefined
     1   0     1      1    11   Control segment, undefined

     1   1     0      0    12   Cancel segment from block sender
     1   1     0      1    13   Cancel-acknowledgment segment
                                to block sender

     1   1     1      0    14   Cancel segment from block receiver
     1   1     1      1    15   Cancel-acknowledgment segment
                                to block receiver

"""
#import math
import sys
import os
from operator import itemgetter

VERSION = "0.8.1"

#status and error messages
MSGLIST = ["Only sessions to/from the first IP found are analyzed", \
           "Green data part found - not analyzed", \
           "Cancel segment found - not analyzed", \
           "Session starts with a control segment", \
           "Undefined control segment seen" \
           ]
MSGSTATUS = [False, False, False, False, False]


class Segment:
    def __init__(self,datastring):
#        self.error="ok"
        items = datastring.split("\t")
        self.frame=int(items[0])
        self.time=float(items[1])
        self.type=int(items[7],0)
        if self.type >=12:
            MSGSTATUS[2]=True
        ips=items[2].split(",")
        self.ports=items[3].split(",")
        if self.type < 8 or self.type == 9 or self.type == 12 or self.type == 15:
            self.dsource=ips[0]
            self.ddest=ips[1]
        elif self.type == 8 or self.type == 13 or self.type == 14:
            self.dsource=ips[1]
            self.ddest=ips[0]
        else:
            MSGSTATUS[4] = True

# Cancel acknowlegements do not contain a session number
        if items[4] == "" :
            self.session = -1
        else:
            self.session=int(items[4])

        if self.type < 8:
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
        if segment.type >= 8:
            MSGSTATUS[3] = True
        self.count=1
        self.time_min=segment.time
        self.time_max=self.time_min
        self.dtime_min=segment.time
        self.dtime_max=segment.time
        self.data_start=segment.offset
        self.data_end=segment.offset+segment.length
        self.session=segment.session
        self.segments = [segment]
    def update(self,segment):
        self.count+=1
        self.segments.append(segment)
        self.time_min=min(segment.time,self.time_min)
        self.time_max=max(segment.time,self.time_max)
        if segment.type < 8:
            self.data_start=min(self.data_start,segment.offset)
            self.data_end=max(self.data_end,segment.offset+segment.length)
            self.dtime_min=min(segment.time,self.dtime_min)
            self.dtime_max=max(segment.time,self.dtime_max)

print("ltptrace version",VERSION)
segList = []
session_list = {}
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
        if currSession >= 0:
            if currSession not in session_list.keys():
                session_list[currSession]=SessionData(segment)
            else:
                session_list[currSession].update(segment)
    else:
        MSGSTATUS[0] = True

#print status/error messages
for i in range(len(MSGLIST)):
    if MSGSTATUS[i]:
        print(MSGLIST[i])

session_index = []
for s in session_list.keys():
    session_index.append((s,session_list[s].time_min))
session_sorted = sorted(session_index, key=itemgetter(1))

print("=== Session report ===")
print("Session, Segments, Start, End, End-of-Data, Data(kB), Rate")

yshift = session_list[session_sorted[0][0]].data_start
for index in session_sorted:
    s = index[0]
    sdata=(session_list[s].data_end-session_list[s].data_start)/1000
    print(f'{s:8}',f'{session_list[s].count:6}',f'{(session_list[s].time_min-time0):8.4f}', \
          f'{(session_list[s].time_max-time0):8.4f}', f'{(session_list[s].dtime_max-time0):8.4f}', \
          sdata,f'{(8*sdata/(session_list[s].dtime_max-session_list[s].dtime_min)/1000):8.3f}Mbps')
    for segment in session_list[s].segments:
        currTime=segment.time-time0
        currSession=segment.session
        if segment.type < 8 :
            print("darrow",currTime,segment.offset+yshift,file=ofh)
            print("rtext",currTime,segment.offset+yshift,file=ofh)
            print("_",currSession,file=ofh)
            print("uarrow",currTime,segment.offset+segment.length+yshift,file=ofh)
            print("line",currTime,segment.offset+yshift,currTime,segment.offset+segment.length+yshift,file=ofh)
        elif segment.type == 8 :
#            print("Report segment at",currTime,",",segment.rptCount,"claims")
            for i in range(0,segment.rptCount) :
                print("dline",currTime,segment.rptOffset[i]+yshift,currTime,segment.rptOffset[i]+segment.rptLength[i]+yshift,file=ofh)
                print("rtext",currTime,segment.rptOffset[i]+yshift,file=ofh)
                print("_",currSession,file=ofh)
    yshift += session_list[s].data_end

ifh.close()
ofh.close()
       