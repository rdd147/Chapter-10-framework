import sys
import struct
import re
import os
import binascii
from __builtin__ import sum
from datetime import datetime
from enum import Enum
chid1553=[]
chidnames=[]

class messagetype(Enum):
  BCtoRT=1
  RTtoBC=2
  RTtoRT=3
  broadcast_BCtoRT=4
  broadcast_RTtoRT=5
  modecode_without_dataword=6
  transmit_modecode_with_dataword=7
  recieve_modecode_with_dataword=8
  broadcast_transmit_modecode_with_dataword=9
  broadcast_transmit_modecode_without_dataword=10
  unknown=11
  
class Counter: #Counter class made to keep track of all messages and errors in each 1553 bus
  def __init__(self, channel_name):
    self.name = channel_name
    self.message_count_A = 0
    self.message_count_B = 0
    self.message_error_A = 0
    self.format_error_A = 0
    self.response_timeout_error_A = 0
    self.word_count_error_A = 0
    self.sync_type_error_A = 0
    self.invalid_word_error_A = 0
    self.message_error_B = 0
    self.format_error_B = 0
    self.response_timeout_error_B = 0
    self.word_count_error_B = 0
    self.sync_type_error_B = 0
    self.invalid_word_error_B = 0
    self.total_word_count_A = 0
    self.total_word_count_B = 0
    
  def getName(self):
    return self.name
    
  def increaseWordCountA(self, numofwords):
    self.total_word_count_A  = self.total_word_count_A  + numofwords
    
  def increaseWordCountB(self, numofwords):
    self.total_word_count_B  = self.total_word_count_B  + numofwords
    
  def returnWordCountA(self):
    return self.total_word_count_A 
    
  def returnWordCountB(self):
    return self.total_word_count_B

  def calcTotalWordCount(self):
    return self.total_word_count_A + self.total_word_count_B
    
  def increaseMessageCountA(self, numofmessages):
    self.message_count_A = self.message_count_A + numofmessages
    
  def returnMessageCountA(self):
    return self.message_count_A
  
  def increaseMessageCountB(self, numofmessages):
    self.message_count_B = self.message_count_B + numofmessages 
    
  def returnMessageCountB(self):
    return self.message_count_B  

  def calcTotalMessages(self):
    return (self.message_count_A + self.message_count_B)
    
  def increaseMessageErrorA(self, numoferrors):
    self.message_error_A = self.message_error_A + numoferrors
    
  def increaseFormatErrorA(self, numoferrors):
    self.format_error_A = self.format_error_A + numoferrors
    
  def increaseResponseTimeoutErrorA(self, numoferrors):
    self.response_timeout_error_A = self.response_timeout_error_A + numoferrors
    
  def increaseWordCountErrorA(self, numoferrors):
    self.word_count_error_A = self.word_count_error_A + numoferrors
    
  def increaseSyncTypeErrorA(self, numoferrors):
    self.sync_type_A = self.sync_type_error_A + numoferrors
    
  def increaseInvalidWordErrorA(self, numoferrors):
    self.invalid_word_error_A = self.invalid_word_error_A + numoferrors
    
  def increaseMessageErrorB(self, numoferrors):
    self.message_error_B = self.message_error_B + numoferrors
    
  def increaseFormatErrorB(self, numoferrors):
    self.format_error_B = self.format_error_B + numoferrors
    
  def increaseResponseTimeoutErrorB(self, numoferrors):
    self.response_timeout_error_B = self.response_timeout_error_B + numoferrors
    
  def increaseWordCountErrorB(self, numoferrors):
    self.word_count_error_B = self.word_count_error_B + numoferrors
    
  def increaseSyncTypeErrorB(self, numoferrors):
    self.sync_type_B = self.sync_type_error_B + numoferrors
    
  def increaseInvalidWordErrorB(self, numoferrors):
    self.invalid_word_error_B = self.invalid_word_error_B + numoferrors
    
  def returnAllErrorsA(self):
    listoferrorsA=[self.message_error_A, self.format_error_A, self.response_timeout_error_A, self.word_count_error_A, self.sync_type_error_A, self.invalid_word_error_A]
    return listoferrorsA
    
  def returnAllErrorsB(self):
    listoferrorsB=[self.message_error_B, self.format_error_B, self.response_timeout_error_B, self.word_count_error_B, self.sync_type_error_B, self.invalid_word_error_B]
    return listoferrorsB
  
def makeClassCounter(chidname):
  return Counter(chidname)
    
    
def readch10headerforchecksum(file):
  header=file.read(24)  #read the first packets 24 byte chapter 10 header
  if struct.unpack('<H',header[0:2])[0]!=0xeb25:
    print 'Packet sync not found where expected!'
    print 'Stopped at offset :', (file.tell()- 24)
    sys.exit(2)
  #rawheader=''.join(x.encode('hex') for x in header) #packet header printout for debugging purposes
  #print rawheader
  checksumpresent=False
  packetflags=header[14]
  test333=struct.unpack('B',header[14])[0]
  if test333==3:
    checksumpresent=True
  #if checksumpresent==True:
   # print 'Checksum True'
  #else:
   # print 'Checksum False'
  packetlength= struct.unpack('<H',header[4:6])[0]  #read out both packet and data length from the headere into their own tuples
  packetlengthhigh = struct.unpack('<H',header[6:8])[0]
  packetlengthnum = packetlengthhigh << 16 | packetlength
  datalength = struct.unpack('<H',header[8:10])[0]
  datalengthhigh = struct.unpack('<H',header[10:12])[0]
  datalengthnum = datalengthhigh << 16 | datalength
  #print datalengthnum
  #if packetlengthnum-24!=datalengthnum: #check to see if datalength includes filler or not, and adjust if needed
  #  datalengthnum=packetlengthnum-24
  return (packetlengthnum,datalengthnum,checksumpresent)
  
def readheaderfor1553(file):
  currentpacketoffset=file.tell()
  #print currentpacketoffset
  header=file.read(24)  #read the first packets 24 byte chapter 10 header
  if struct.unpack('<H',header[0:2])[0]!=0xeb25:
    print 'Packet sync not found where expected!'
    print 'Stopped at offset :', (file.tell()- 24)
    sys.exit(2)
  #rawheader=''.join(x.encode('hex') for x in header) #packet header printout for debugging purposes
  #print rawheader
  tmatspacket = False
  channelid=struct.unpack('<H',header[2:4])[0]
  if channelid==0x0:
    tmatspacket = True
  datatype=struct.unpack('>B',header[15])[0]
  packetlength= struct.unpack('<H',header[4:6])[0]  #read out both packet and data length from the headere into their own tuples
  packetlengthhigh = struct.unpack('<H',header[6:8])[0]
  packetlength = packetlengthhigh << 16 | packetlength
  datalength = struct.unpack('<H',header[8:10])[0]
  datalengthhigh = struct.unpack('<H',header[10:12])[0]
  datalength = datalengthhigh << 16 | datalength
  #time_low = struct.unpack('<H',header[16:18])[0]
  #time_mid = struct.unpack('<H',header[18:20])[0]
  #time_high = struct.unpack('<H',header[20:22])[0]
  ch10_counter=int(binascii.b2a_hex(header[21])+binascii.b2a_hex(header[20])+binascii.b2a_hex(header[19])+binascii.b2a_hex(header[18])+binascii.b2a_hex(header[17])+binascii.b2a_hex(header[16]),16)
  #print ch10_counter
  ##print hex(time_high), hex(time_mid), hex(time_low)
  if tmatspacket==True and datatype==1:
    tmatsbody=file.read(datalength)
    #print tmatsbody
    numof1553chans=re.findall(r'.+(\d+):1553IN;',tmatsbody) #find all 1553 channel IDs
    #print numof1553chans
    for a,b in enumerate(numof1553chans):
      match=re.search(r'TK1.'+numof1553chans[a]+':(\d+);', tmatsbody)
      if match:
        chid1553.append(int(match.group(1),10))
      match2=re.search(r'DSI-'+numof1553chans[a]+':(.+);', tmatsbody)
      if match2: #If no name tag is found, use channel id instead
        chidnames.append(match2.group(1))
      elif match:
        chidnames.append(int(match.group(1),10))
      chidnames[a] = makeClassCounter(chidnames[a])
    #print chid1553
    #print chidnames
  amountoffill=0
  if packetlength-24!=datalength: #check to see if datalength includes filler or not, and adjust if needed
    datalength=packetlength-24
    amountoffill = packetlength - datalength - 24
  #print datalength
  return (packetlength,datalength,datatype, channelid,tmatspacket,chid1553, ch10_counter, chidnames, amountoffill)
  
def decodeblockstatusword(blkstatusword, chidnames, index):
  worderror , syncerror, wordcounterror, responsetimeout, formaterror, RTtoRT, messageerror, busb, rsvbitset = (False,)*9
  #decodes all bits of block status word and makes sure no reserve bits are set
  if blkstatusword & (1<<13) !=0:
    busb=True
  if busb == True:
    chidnames[index].increaseMessageCountB(1)
  else:
    chidnames[index].increaseMessageCountA(1)  
  if blkstatusword & (1<<0) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<1) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<2) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<3) !=0:
    worderror=True
    if busb == True:
      chidnames[index].increaseInvalidWordErrorB(1)
    else:
      chidnames[index].increaseInvalidWordErrorA(1)     
  if blkstatusword & (1<<4) !=0:
    syncerror=True
    if busb == True:
      chidnames[index].increaseSyncTypeErrorB(1)
    else:
      chidnames[index].increaseSyncTypeErrorA(1)
  if blkstatusword & (1<<5) !=0:
    wordcounterror=True
    if busb == True:
      chidnames[index].increaseWordCountErrorB(1)
    else:
      chidnames[index].increaseWordCountErrorA(1)  
  if blkstatusword & (1<<6) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<7) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<8) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<9) !=0:
    responsetimeout=True
    if busb == True:
      chidnames[index].increaseResponseTimeoutErrorB(1)
    else:
      chidnames[index].increaseResponseTimeoutErrorA(1)  
  if blkstatusword & (1<<10) !=0:
    formaterror=True
    if busb == True:
      chidnames[index].increaseFormatErrorB(1)
    else:
      chidnames[index].increaseFormatErrorA(1)     
  if blkstatusword & (1<<11) !=0:
    RTtoRT=True
  if blkstatusword & (1<<12) !=0:
    messageerror=True
    if busb == True:
      chidnames[index].increaseMessageErrorB(1)
    else:
      chidnames[index].increaseMessageErrorA(1) 
  if blkstatusword & (1<<14) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  if blkstatusword & (1<<15) !=0:
    print 'Reserved bit set!'
    rsvbitset = True
  return worderror , syncerror, wordcounterror, responsetimeout, formaterror, RTtoRT, messageerror, busb, rsvbitset 
  
def decodestatusword(message, mtype):
# intialize 2 status variables to None 
  RCV_status = None
  TX_status = None
# assign status words, based on their message type
  if mtype==messagetype(1):
    RCV_status= message[-1]
  elif mtype==messagetype(2):
    TX_status= message[1]
  elif mtype==messagetype(3):
    TX_status= message[2]
    RCV_status= message[-1]   
  #no case 4 because there is no status word
  elif mtype==messagetype(5): 
    TX_status= message[2]
  elif mtype==messagetype(6): 
    RCV_status= message[1]
  elif mtype==messagetype(7): 
    RCV_status= message[-1] 
  elif mtype==messagetype(8): 
    TX_status= message[1]     
  #print RCV_status
  #print TX_status
#assign status word masks to read out status word information
  RT_mask = 0xf800
  Message_error_mask = 0x0400
  Instrument_mask = 0x0200
  Service_mask = 0x0100
  Reserve_mask = 0x00E0
  Brodcast_recieved_mask = 0x0010
  Busy_mask = 0x0008
  Subsystem_mask = 0x0004
  Dynamic_control_acceptance_mask = 0x0002
  Terminal_mask = 0x0001
  if RCV_status != None:
    statusRCV_RT_address = (int(RCV_status,16) & RT_mask) >> 11
    statusRCV_message_error = (int(RCV_status,16) & Message_error_mask) >> 10
    statusRCV_instrument = (int(RCV_status,16) & Instrument_mask) >> 9
    statusRCV_service = (int(RCV_status,16) & Service_mask) >> 8
    statusRCV_reservebits = (int(RCV_status,16) & Reserve_mask) >> 5
    statusRCV_broadcast_recieve = (int(RCV_status,16) & Brodcast_recieved_mask) >> 4
    statusRCV_busy = (int(RCV_status,16) & Busy_mask) >> 3
    statusRCV_subsystem = (int(RCV_status,16) & Subsystem_mask) >> 2
    statusRCV_dynamic_control_acceptance = (int(RCV_status,16) & Dynamic_control_acceptance_mask) >> 1
    statusRCV_terminal = (int(RCV_status,16) & Terminal_mask) 
    RCV_status = {'statusRCV_RT_address':statusRCV_RT_address, 'statusRCV_message_error':statusRCV_message_error, 'statusRCV_instrument':statusRCV_instrument, 'statusRCV_service':statusRCV_service , 'statusRCV_reservebits':statusRCV_reservebits, 'statusRCV_broadcast_recieve': statusRCV_broadcast_recieve, 'statusRCV_busy': statusRCV_busy, 'statusRCV_subsystem': statusRCV_subsystem, 'statusRCV_dynamic_control_acceptance': statusRCV_dynamic_control_acceptance, 'statusRCV_terminal': statusRCV_terminal}
    #print 'Recieve Status : ', RCV_status
  if TX_status != None:
    statusTX_RT_address = (int(TX_status,16) & RT_mask) >> 11
    statusTX_message_error = (int(TX_status,16) & Message_error_mask) >> 10 
    statusTX_instrument = (int(TX_status,16) & Instrument_mask) >> 9
    statusTX_service = (int(TX_status,16) & Service_mask) >> 8
    statusTX_reservebits = (int(TX_status,16) & Reserve_mask) >> 5
    statusTX_broadcast_recieve = (int(TX_status,16) & Brodcast_recieved_mask) >> 4
    statusTX_busy = (int(TX_status,16) & Busy_mask) >> 3
    statusTX_subsystem = (int(TX_status,16) & Subsystem_mask) >> 2
    statusTX_dynamic_control_acceptance = (int(TX_status,16) & Dynamic_control_acceptance_mask) >> 1
    statusTX_terminal = (int(TX_status,16) & Terminal_mask)
    TX_status = {'statusTX_RT_address':statusTX_RT_address, 'statusTX_message_error':statusTX_message_error, 'statusTX_instrument':statusTX_instrument, 'statusTX_service':statusTX_service , 'statusTX_reservebits':statusTX_reservebits, 'statusTX_broadcast_recieve': statusTX_broadcast_recieve, 'statusTX_busy': statusTX_busy, 'statusTX_subsystem': statusTX_subsystem, 'statusTX_dynamic_control_acceptance': statusTX_dynamic_control_acceptance, 'statusTX_terminal': statusTX_terminal}
    #print 'Transmit Status : ', TX_status
  if RCV_status != None and TX_status != None:
    return RCV_status, TX_status
  elif TX_status != None:
    return TX_status
  elif RCV_status != None:
    return RCV_status
  else:
    return
  
def decodecmdword(message, RTtoRT):
  wordcountmask =  0x001f
  subaddressmask = 0x03e0
  txorrcvmask =    0x0400
  rtaddressmask =  0xf800
  cmdword = None
  cmdword1 = None
  cmdword2 = None
  if RTtoRT == False:
    cmdword = message[0]
    RTaddress = (int(cmdword,16) & rtaddressmask) >> 11
    TXRXbit= (int(cmdword,16) & txorrcvmask) >> 10
    subaddress = (int(cmdword,16) & subaddressmask) >> 5 
    wordcount = int(cmdword,16) & wordcountmask
    if wordcount == 0: 
      wordcount = 32
    #print RTaddress, TXRXbit, subaddress,  wordcount
    return RTaddress, TXRXbit, subaddress,  wordcount
  else:
    cmdword1 = message[0]
    cmdword2 = message[1]
    RTaddress1 = (int(cmdword1,16) & rtaddressmask) >> 11
    TXRXbit1 = (int(cmdword1,16) & txorrcvmask) >> 10
    subaddress1 = (int(cmdword1,16) & subaddressmask) >> 5 
    wordcount1 = int(cmdword1,16) & wordcountmask
    if wordcount1 == 0: 
      wordcount1 = 32
    RTaddress2 = (int(cmdword2,16) & rtaddressmask) >> 11
    TXRXbit2 = (int(cmdword2,16) & txorrcvmask) >> 10
    subaddress2 = (int(cmdword2,16) & subaddressmask) >> 5 
    wordcount2 = int(cmdword2,16) & wordcountmask
    if wordcount2 == 0: 
      wordcount2 = 32  
    #print RTaddress1, TXRXbit1, subaddress1,  wordcount1, RTaddress2, TXRXbit2, subaddress2,  wordcount2
    return RTaddress1, TXRXbit1, subaddress1,  wordcount1, RTaddress2, TXRXbit2, subaddress2,  wordcount2
  
def readtimepacket(ch10_counter, packetlength , datalength, file):
    global ch10_counter_from_time_packet
    global start_of_year_seconds_from_time_packet
    ch10_counter_from_time_packet=ch10_counter
    b4 = file.read(1)
    b3 = file.read(1)
    b2 = file.read(1)
    b1 = file.read(1)
    #make full csdw
    csdw=binascii.b2a_hex(b1+b2+b3+b4)
    #print csdw
    milliseconds_byte = file.read(1)
    seconds_byte = file.read(1)
    minutes_byte = file.read(1)
    hours_byte = file.read(1)
    low_days_byte = file.read(1)
    high_days_byte = file.read(1)
    bytesread=10
    file.read(datalength-bytesread)
    time = binascii.hexlify(high_days_byte)+binascii.hexlify(low_days_byte)+':'+binascii.hexlify(hours_byte)+':'+binascii.hexlify(minutes_byte)+':'+binascii.hexlify(seconds_byte)+'.'+binascii.hexlify(milliseconds_byte)
    formatted_time=time[1:]
    #print formatted_time
    milliseconds_time_packet=int(binascii.b2a_hex(milliseconds_byte),10)
    seconds_time_packet=int(binascii.b2a_hex(seconds_byte),10)
    minutes_time_packet=int(binascii.b2a_hex(minutes_byte),10)
    hours_time_packet=int(binascii.b2a_hex(hours_byte),10)
    days_time_packet=int((binascii.b2a_hex(high_days_byte)+binascii.b2a_hex(low_days_byte)),10)
    start_of_year_seconds_from_time_packet = (days_time_packet*86400)+(hours_time_packet*3600)+(minutes_time_packet*60)+seconds_time_packet+(milliseconds_time_packet*.01)
    #print start_of_year_seconds_from_time_packet
    return
    
def getabsolutetime(counter):
  time=start_of_year_seconds_from_time_packet + ((counter-ch10_counter_from_time_packet)*0.0000001)
  #print time
  return time
  
def processpacket(file, packetnum, time_packet_counter):
  packetlength, datalength , datatype , channelid , tmatspacket , chid1553, ch10_counter, chidnames, amountoffill = readheaderfor1553(file)
  if tmatspacket==True and datatype==1:
    return None, time_packet_counter
  if datatype==0x11:
    #print 'Time packet found!'
    readtimepacket(ch10_counter, packetlength , datalength, file)
    time_packet_counter = time_packet_counter + 1
    return None , time_packet_counter
  if channelid in chid1553:
    index = chid1553.index(channelid)
    #print chidnames[index].returnAllErrorsA()
    #print chidnames[index].returnAllErrorsB()
    #print 'Yay'
    #log.write( 'Packet numbet '+str(packetnum)+ ' of channel ID '+str(channelid)+ ' conatins: \n')
    b4 = file.read(1)
    b3 = file.read(1)
    b2 = file.read(1)
    b1 = file.read(1)
    #make full csdw
    csdw=binascii.b2a_hex(b1+b2+b3+b4)
    #read number of 1553 messages in the packet in base 10
    numof1553messages=int(binascii.b2a_hex(b2+b3+b4),16)
    #print numof1553messages
    while numof1553messages != 0:
      message1553time=file.read(8) #read 64 bits of time to use later on and advance file position
      ch10_counter_1553=int(binascii.b2a_hex(message1553time[7])+binascii.b2a_hex(message1553time[6])+binascii.b2a_hex(message1553time[3])+binascii.b2a_hex(message1553time[2])+binascii.b2a_hex(message1553time[1])+binascii.b2a_hex(message1553time[0]),16)
      time=getabsolutetime(ch10_counter_1553)
      #low_time = struct.unpack('<H',message1553time[0:2])[0]
      #mid_time = struct.unpack('<H',message1553time[2:4])[0]
      #high_time = struct.unpack('<H',message1553time[6:8])[0]
      blkstatusword=struct.unpack('<H',file.read(2))[0]
      gaptimesword1=int(binascii.b2a_hex(file.read(1)),16)
      gaptimesword2=int(binascii.b2a_hex(file.read(1)),16)
      bytecount=struct.unpack('<H',file.read(2))[0]
      worderror , syncerror, wordcounterror, responsetimeout, formaterror, RTtoRT, messageerror, busb, rsvbitset = decodeblockstatusword(blkstatusword, chidnames, index)
      if busb == True:
        chidnames[index].increaseWordCountB(bytecount/2)
      else:
        chidnames[index].increaseWordCountA(bytecount/2)
      #print chidnames[index].calcTotalMessages()
      #undo little endian data and read entire 1553 message in
      #print worderror , syncerror, wordcounterror, responsetimeout, formaterror, RTtoRT, messageerror, busb
      file.seek(bytecount,1)
      '''message=[]
      for k in range(bytecount/2):
        message.append(hex(struct.unpack('<H',file.read(2))[0]))
      if RTtoRT== False:
        RTaddress, TXRXbit, subaddress,  wordcount=decodecmdword(message, RTtoRT)
      else:
        RTaddress1, TXRXbit1, subaddress1,  wordcount1, RTaddress2, TXRXbit2, subaddress2,  wordcount2 = decodecmdword(message, RTtoRT)
      #if worderror or syncerror or wordcounterror or responsetimeout or formaterror or messageerror or rsvbitset == True:
        #log.write('Block status word error detected at message number '+ str(numof1553messages)+'\n')
      if RTtoRT==False:
        mtype=whatmessage(RTaddress, TXRXbit, subaddress, wordcount, RTtoRT)
      else: # CHECK BELOW RT TO RT FOR CORRECTNESXS
        if RTaddress1!=31 and subaddress1 < 31  and TXRXbit1 == 0:
          mtype=messagetype(3)
          #print mtype
        elif RTaddress1==31 and subaddress1 < 31 and TXRXbit1 == 0:
          mtype=messagetype(5)
          #print mtype
        else:
          mtype=messagetype(11)
          #print mtype
      if mtype==messagetype(3): 
        RCV_status, TX_status = decodestatusword(message, mtype)
      elif mtype==messagetype(1) or mtype==messagetype(6) or mtype==messagetype(7):
        RCV_status = decodestatusword(message, mtype)
      else:
        TX_status = decodestatusword(message, mtype)'''
      numof1553messages=numof1553messages-1
      
      #print message
  else:
    file.seek(datalength,1)
    return None, time_packet_counter
  check = file.tell()%4
  if check!=0:
    file.seek(check,1)
  #return time, chidnames
  return time, time_packet_counter
 
def whatmessage(RTaddress, TXRXbit, subaddress, wordcount, RTtoRT):
  mtype=messagetype(11) #Assigns what message type the message is
  if RTaddress!=31 and subaddress < 31  and TXRXbit == 0:
    mtype=messagetype(1)
  elif RTaddress!=31 and subaddress < 31  and TXRXbit == 1:
    mtype=messagetype(2)
  elif RTaddress==31 and subaddress < 31 and TXRXbit == 0: #Cases 3 and 5 (RT to RT types) are set in process packet function
    mtype=messagetype(4)
  elif RTaddress!=31 and (subaddress == 0 or subaddress == 31) and TXRXbit == 1 and wordcount<16:
    mtype=messagetype(6)
  elif RTaddress!=31 and (subaddress == 0 or subaddress == 31) and TXRXbit == 0 and wordcount>15:
    mtype=messagetype(7)
  elif RTaddress!=31 and (subaddress == 0 or subaddress == 31) and TXRXbit == 1 and wordcount>15:
    mtype=messagetype(8)
  elif RTaddress==31 and (subaddress == 0 or subaddress == 31) and TXRXbit == 0 and wordcount>15:
    mtype=messagetype(9)
  elif RTaddress==31 and (subaddress == 0 or subaddress == 31) and TXRXbit == 1 and wordcount<16:
    mtype=messagetype(10)
  #print mtype
  return mtype
  
def writelogoutputs(time, chidnames, time_packet_counter, filename):
  log=open(filename[:-5]+'_log.txt','w')
  log.write('Log file for: '+ filename+ ' was created on ' + str(datetime.now())+ '\n\n')
  #listoferrorsA=[self.message_error_A, self.format_error_A, self.response_timeout_error_A, self.word_count_error_A, self.sync_type_error_A, self.invalid_word_error_A]
  for value in chidnames:
    channelAerrors = value.returnAllErrorsA()
    channelBerrors = value.returnAllErrorsB()
    log.write('1553 Channel Name ' + str(value.getName()) + ' statistics:\n\n')
    log.write('Total Number of Messages: ' + str(value.calcTotalMessages()) + '\n\n')
    log.write('Total Number of Messages on Bus A: ' + str(value.returnMessageCountA()) + '\n')
    log.write('Total Number of Message Errors on Bus A: ' + str(channelAerrors[0]) + '\n')
    log.write('Total Number of Format Errors on Bus A: ' + str(channelAerrors[1]) + '\n')
    log.write('Total Number of Response Timeouts on Bus A: ' + str(channelAerrors[2]) + '\n')
    log.write('Total Number of Word Count Errors on Bus A: ' + str(channelAerrors[3]) + '\n')
    log.write('Total Number of Sync Type Errors on Bus A: ' + str(channelAerrors[4]) + '\n')
    log.write('Total Number of Invalid Word Errors on Bus A: ' + str(channelAerrors[5]) + '\n')
    log.write('Total Number of Messages on Bus B: ' + str(value.returnMessageCountB()) + '\n')
    log.write('Total Number of Message Errors on Bus B: ' + str(channelBerrors[0]) + '\n')
    log.write('Total Number of Format Errors on Bus B: ' + str(channelBerrors[1]) + '\n')
    log.write('Total Number of Response Timeouts on Bus B ' + str(channelBerrors[2]) + '\n')
    log.write('Total Number of Word Count Errors on Bus B: ' + str(channelBerrors[3]) + '\n')
    log.write('Total Number of Sync Type Errors on Bus B: ' + str(channelBerrors[4]) + '\n')
    log.write('Total Number of Invalid Word Errors on Bus B: ' + str(channelBerrors[5]) + '\n\n')
    log.write('Bus Loading percentage: ' + str((value.calcTotalWordCount()/time_packet_counter)*0.00002*100) + '%' + '\n\n')
    
    
 
def count32bitwords(file, packetnum, dictofchecksums):
  (packetlength, datalength, checksumpresent)=readch10headerforchecksum(file) #recieve packet and modified data length to include fill from readch10header
  word32bit=[]
  datal=datalength
  while datal!=0:
    if datal == 2:
      a2 = file.read(1)
      a1 = file.read(1) #advances the file 2 bytes, they are filler data so they go nowhere
      break
    a4 = file.read(1)
    a3 = file.read(1)
    a2 = file.read(1)
    a1 = file.read(1)
    bit32 = binascii.b2a_hex(a1+a2+a3+a4)
    word32bit.append(int(bit32,16))
    datal=datal-4
  #print word32bit
  ##tobesummed=file.read(datalength) #read data length from file into string
  ##tobesummed=binascii.b2a_hex(tobesummed) #turn ascii encoded string into hex string
  
  #rawtobesummed=''.join(x.encode('hex') for x in tobesummed) #turn ascii encoded string into hex string
  ##print tobesummed
  
  
  ##segmentsbit32=[tobesummed[i:i+8] for i in range(0, len(tobesummed), 8)] #seperate into 8 character segments
  ##word32bit=[]
  ##test123 = []
  ##for a, b in enumerate(segmentsbit32):  #gives access to the index of 'a' of string 'b' in segmentsbit32
    ##word32bit.append(int(segmentsbit32[a],16)) #cast each element as an int with base 16 math (hex) into word32bit list
    #print format(word32bit[a],'08x')
    ##test123.append(format(word32bit[a],'08x'))
  ##print test123
  #print word32bit
  wholechecksum= sum (word32bit) #sum to make checksum
  #print hex(wholechecksum)
  string = hex(wholechecksum)
  if string [-1:] == 'L':
    d1= string[-3:-1]
    d2= string[-5:-3]
    d3= string[-7:-5]
    d4= string[-9:-7]
    #print d1, d2, d3 ,d4
    checkstring = d1+d2+d3+d4
    #print checkstring
  elif len(string) < 10:
    newstring = string [2:]
    newstring = newstring.zfill(8)
    #print newstring
    d1= newstring[-2:]
    d2= newstring[-4:-2]
    d3= newstring[-6:-4]
    d4= newstring[-8:-6]
    #print d1, d2, d3 ,d4
    checkstring = d1+d2+d3+d4
    #print checkstring
  else:
    d1= string[-2:-0]
    d2= string[-4:-2]
    d3= string[-6:-4]
    d4= string[-8:-6]
    #print d1, d2, d3 ,d4
    checkstring = d1+d2+d3+d4
    #print checkstring
  checksum= format(wholechecksum, '8x')[-8:] #save last 8 bytes of checksum only
  #rchecksum = struct.unpack('<I',checksum)[0]
  dictofchecksums[packetnum]=checksum
  #print rchecksum
  #print checksum
  #rawtobesummed=''.join(x.encode('hex') for x in tobesummed) #packet printout for debugging purposes
  if checksumpresent==True: #is checksum present in packet trailer
    left = packetlength-datalength-24
    if left == 4:
      trailer=file.read(left)
      #print binascii.b2a_hex(trailer)
    else:
      fill = left-4
      throwaway = file.read(fill)
      trailer=file.read(4)
      #print binascii.b2a_hex(trailer)
    trailerchecksum = binascii.b2a_hex(trailer)
    #trailerchecksum=struct.unpack('L',trailer[0:4])[0]
    if checkstring!=trailerchecksum:
      #print  'Packet trailer checksum= ' + trailerchecksum + 'does not equal calculated checksum= ' + checksum
      print 'Checksum read from packet', packetnum, 'of', trailerchecksum, 'does not equal calculated checksum of', checksum
      sys.exit(3)
    #else:
      #print 'Checksum read from packet', packetnum, 'of', trailerchecksum, 'is good!'
  return dictofchecksums
  
def statusoutput(prev_pack_offset ,curr_pack_offset ,file, step):
  if prev_pack_offset<step and curr_pack_offset>=step:
    print '\b*',
    step=step+(os.fstat(file.fileno()).st_size/20)
  if file.tell() == os.fstat(file.fileno()).st_size:
    print '\b]  Finished!'
  return step
    
def main():
  if len(sys.argv) != 3:
    print 'usage: ch10crdcheck.py -checksumcheck <file>'
    print 'usage: ch10crdcheck.py -ch101553check <file>'
    sys.exit(1)

  option = sys.argv[1]
  filename = sys.argv[2]
  if option == '-checksumcheck':
    file=open(filename,'rb')
    packetnum=1
    dictofchecksums={}
    step=os.fstat(file.fileno()).st_size/20
    print 'Starting [                    ]', 
    print '\b'*22, 
    while True:
      prev_pack_offset=file.tell()
      dictofchecksums= count32bitwords(file, packetnum, dictofchecksums)
      #print dictofchecksums
      curr_pack_offset=file.tell()
      step=statusoutput(prev_pack_offset,curr_pack_offset, file, step)
      packetnum+=1
      if file.tell() == os.fstat(file.fileno()).st_size:
        break
    print dictofchecksums
  elif option== '-ch101553check':
    file=open(filename,'rb')
    log=open(filename[:-5]+'_log.txt','w')
    #log.write('Log file for: '+ filename+ ' was created on ' + str(datetime.now())+ '\n')
    packetnum=1
    time_packet_counter=-1
    time=0.0
    step=os.fstat(file.fileno()).st_size/20
    print 'Starting [                    ]', 
    print '\b'*22, 
    while True:
      prev_pack_offset=file.tell()
      time, time_packet_counter = processpacket(file,packetnum,time_packet_counter)
      curr_pack_offset=file.tell()
      step=statusoutput(prev_pack_offset,curr_pack_offset, file, step)
      packetnum+=1
      if file.tell() == os.fstat(file.fileno()).st_size:
        break
    writelogoutputs(time, chidnames, time_packet_counter, filename)
  else:
    print 'unknown option: ' + option
    sys.exit(1)

if __name__ == '__main__':
  main()