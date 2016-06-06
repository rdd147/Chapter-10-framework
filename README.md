#Chapter 10 framework script

Chapter 10 is a binary encoded onboard recording standard for the aircraft recorders. It is comprised of many different packets of data, from several independent input channels of different types of data.

Dependencies:

To run this script, you need to have the Enum module installed on the PC of use in addition to Python 2.7:

https://pypi.python.org/pypi/enum34


The Chapter 10 framework script has 2 different functions:

1. If a data checksum exists on any packet of data, calcualte the checksum on the data portion of the packet and compare to the checksum stored in the packet. If it matches, proceed, if it does not, warn the user there is bad data or an incorrectly calculated checksum.

Usage (from command prompt):

ch10_framework.py -checksumcheck <filename or filepath>

2. For the 1553 data type only, find all 1553 channels in the recording from the TMATS packet (first packet of recording defining the contents of the recording), and find all errors flagged in the block status word data portion of every 1553 message in the file. Write a log file, documenting all the errors with each 1553 bus and calculate a bus loading percentage for each 1553 bus (what percentage was the bus active for the length of the recording) and include it in the report.

Usage (from command prompt):

ch10_framework.py -ch101553check <filename or filepath>