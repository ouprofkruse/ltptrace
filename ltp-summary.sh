#!/bin/bash
#
#Hans Kruse Oct 02, 2023
#The wireshark input file given on the command line is 
#parsed using tshark to create an intermediate data file.
#That datafile is the input to the LTPtrace python script.
#
if [ $# -ne 1 ]; then
    echo "Usage: ltp-summary.sh <capture-file>" >&2
    exit 2
fi
OF=`basename $1`
OF="$OF.summary"

#
#tshark options
#   -r for the input file *** needs protection for files with whitespace
#   -2 for 2-pass processing
#   -T fields specifies tab delimited output of fields set by the -e options
#   -e specifies fields (if fields have multiple values, they are comma delimited):
#       [0]frame number
#       [1]time the frame was capture in epoch time
#       [2]IP adresses (there should be two, 4 would indicate an ICMP message in most cases)
#       [3]UDP ports
#       [4]LTP session number
#       [5]LTP offset of data being sent
#       [6]LTP data segment length
#       [7]LTP type as hex
#       -- for report segments:
#       [8]Report claim counts
#       [9]Offset for each claim
#       [10]Length for each claim
#       [11]checkpoint id for data segments
#       [12]checkpoint id for report segments
#       [13]report upper bound
#       [14]report serial number
#   The "ltp" argumntents filter on the LTP protocol
#
tshark -r $1 -2 -T fields -e frame.number -e frame.time_epoch -e ip.addr -e udp.port \
 -e ltp.session.number -e ltp.data.offset -e ltp.data.length -e ltp.type -e ltp.rpt.clm.cnt \
 -e ltp.rpt.clm.off -e ltp.rpt.clm.len \
 -e ltp.data.chkp -e ltp.rpt.chkp -e ltp.rpt.ub -e ltp.rpt.sno -e ltp.rpt.ack.sno  \
 ltp > $OF
# *** need proper output file naming
echo "Summary saved in $OF"
