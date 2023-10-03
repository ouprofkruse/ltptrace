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
OF="ltp-summary.txt"
#
#tshark options
#   -r for the input file *** needs protection for files with whitespace
#   -2 for 2-pass processing
#   -T fields specifies tab delimited output of fields set by the -e options
#   -e specifies fields (if fields have multiple values, they are comma delimited):
#       frame number
#       time the frame was capture in epoch time
#       IP adresses (there should be two, 4 would indicate an ICMP message in most cases)
#       UDP ports
#       LTP session number
#       LTP offset of data being sent
#       LTP type as hex
#       -- for report seghements:
#       Report claim counts
#       Offset for each claim
#       Length for each claim
#   The "ltp" argumntents filter on the LTP protocol
#
tshark -r $1 -2 -T fields -e frame.number -e frame.time_epoch -e ip.addr -e udp.port \
 -e ltp.session.number -e ltp.data.offset -e ltp.type -e ltp.rpt.clm.cnt -e ltp.rpt.clm.off -e ltp.rpt.clm.len \
 ltp > $OF
# *** need proper output file naming
echo "Out saved in $OF"
