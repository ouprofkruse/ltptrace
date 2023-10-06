# LTP Trace -- Hans Kruse 2023
INFILE = "ltp-summary.txt" # need to pull file from command line late
PLOTFILE = "ltp-summary.xpl"
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

segList = []

ofh = open(PLOTFILE,"w")
ifh = open(INFILE)
for line in ifh.readlines():
    segList.append(Segment(line))

print(len(segList), "segments found")
time0=segList[0].time
time1=time0
source=segList[0].dsource
currSession=segList[0].session
print("IP",source,"Session:",currSession)
for segment in segList:
    if segment.dsource == source:
        if segment.session != currSession:
            currSession=segment.session
            time1=segment.time
            print("Switching to session",currSession)
        currTime=segment.time-time0
        if segment.type < 8 :
            data=segment.offset+segment.length
            if segment.offset != 0 :
                print(data/1000000,"MB,",segment.time-time1,"sec")
                rate=8*data/(segment.time-time1)/1000000
            else:
                rate="n/a"
            print("At",currTime,"Rate",rate)
            print("darrow",currTime,segment.offset,file=ofh)
            print("rtext",currTime,segment.offset,file=ofh)
            print("_",currSession,file=ofh)
            print("uarrow",currTime,segment.offset+segment.length,file=ofh)
            print("line",currTime,segment.offset,currTime,segment.offset+segment.length,file=ofh)
        elif segment.type == 8 :
            print("Report segment at",currTime,",",segment.rptCount,"claims")
            for i in range(0,segment.rptCount) :
                print("dline",currTime,segment.rptOffset[i],currTime,segment.rptOffset[i]+segment.rptLength[i],file=ofh)

ifh.close()
ofh.close()
