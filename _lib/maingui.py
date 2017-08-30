#!/usr/bin/python3
# Copyright Ηλιάδης Ηλίας, 2017.

import os, sys
import glob
import shlex
import subprocess
import tempfile
import re
import time, datetime
from time import gmtime, strftime
from datetime import date

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GLib
from gi.repository import GObject

from multiprocessing import Process, Manager
from multiprocessing.sharedctypes import Array
import threading

from _lib.OCP import *

#For future usage
INSTANCENAMESTART = 'OCPffmpg-'

FF1 = '/usr/bin/ffmpeg'
FF2 = '/usr/bin/ffprobe'

def getseconds(thetimetext):
    if ":" in thetimetext:
        splitted = thetimetext.split(":")
        if len(splitted) == 3:
            fromhours = int(splitted[0]) * 60 * 60
            fromminutes = int(splitted[1]) * 60
            fromseconds = float(splitted[2])
            theseconds = fromhours + fromminutes + fromseconds
            return theseconds

class VideoInfo():
    def __init__( self, filename=None, text=None):
        self.fulltext = text
        self.filename = filename
        self.fps = None
        self.duration = 0.
        print(text)
        if text:
            thelines = text.splitlines()
            thethreemusketeers = {}
            xcounter = 0
            for line in thelines:
                ycounter = 0
                otherdict = {}
                if line.strip().startswith('Stream'):
                    for theintext in line.strip().split(":", maxsplit=3):
                        otherdict[ycounter] = theintext
                        ycounter += 1
                    thethreemusketeers[xcounter] = otherdict
                    xcounter += 1
                if line.strip().startswith('Duration:'):

                    splitted = line.strip()[len('Duration:'):].split(",")
                    self.duration = getseconds(splitted[0])

            for musketeer in thethreemusketeers:
                if thethreemusketeers[musketeer][2].strip() == "Video":
                    for info in thethreemusketeers[musketeer][3].split(","):
                        if info.strip().endswith('fps'):
                            self.fps = info.strip().split(' ')[0]
                            self.spf = 1/float(self.fps)
                            #print('fps', info)
                        #else:
                            #print('##', info)

                #else:
                    #print('$$', thethreemusketeers[musketeer])

class ForSettings:
    '''Keeps tracking of user's gui preferences

    '''
    def __init__( self):
        self.W = 0
        self.H = 0
        self.Maximized = False
        self.vpaned_position = 0
        self.hpaned1_position = 0
        self.hpaned2_position = 0
        self.dumps_path = ''

class MainGui(AbstractGui):
    def __exit__(self):
        try:
            self.savemysetings()
        except Exception as e:
            print(e)

    def __init__( self, myApp, gladefilename, otherwidjets = (),parent = None,mainbox=None):
        AbstractGui.__init__(self, myApp, gladefilename, otherwidjets=otherwidjets, mainbox=mainbox,savemysettings=self.savemysetings)

        mydir = os.path.realpath(__file__)
        self.videoinfo = VideoInfo()
        #print("----")
        if (not os.path.isfile(FF1)) or (not os.path.isfile(FF2)):
            self.show_ok( FF1 + ' or ' + FF2 + 'not found.\n Exiting.')
            sys.exit(1)

        self.clearonexit = False
        self.ismaximized = False
        lastfile = self.MySettings.readconfigvalue('Paths','inputfile','')
        #TODO: change to current dir in production
        if lastfile == '':
            videofilepath = os.path.abspath(os.path.join(mydir,'..','..','..'))
            #videofilepath = os.getcwd()

            #print(os.listdir(videofilepath))
            files = [os.path.join(videofilepath,f) for f in os.listdir(videofilepath) if os.path.isfile(os.path.join(videofilepath,f))]
            #print(glob.glob(videofilepath + '/*.*'))
            #print(files[0])
            if len(files):
                myfile = files[0]
                self.videofilepath = os.path.split(myfile)[0]
                #print(myfile)

                self.updatevideoinfo(myfile)
                #print("videoinfoupdated")
            else:
                myfile = ''
                self.videofilepath = os.getcwd()
        else:
            myfile = lastfile
            self.videofilepath = os.path.split(myfile)[0]
            self.updatevideoinfo(myfile)
        screenW = self.get_screen().get_width()
        screenH = self.get_screen().get_height()
        W = int(self.MySettings.readconfigvalue('windowMain','width',str(screenW)))
        H = int(self.MySettings.readconfigvalue('windowMain','height', str(screenH-100)) )

        self.resize(W,H)
        if self.MySettings.readconfigvalue('windowMain','maximized','False')  == 'True':
              self.maximize()

        self.outputfilepath =  self.MySettings.readconfigvalue('Paths','outputpath',os.path.join(self.videofilepath,'ready'))
        self.mybuilder.get_object('entry1').set_text(myfile)
        self.mybuilder.get_object('entrysavepath').set_text(self.outputfilepath)

        self.mybuilder.get_object('entrynename').set_text(self.MySettings.readconfigvalue('Paths','outfile','newfile'))
        #counter =
        self.mybuilder.get_object('adjustmentnew').set_value(int(self.MySettings.readconfigvalue('Paths','outputcounter',1)))
        #print('but',self.mybuilder.get_object('spinbutton1').get_text())
        imgW = int(self.MySettings.readconfigvalue('Images','W','50'))
        imgH = int(self.MySettings.readconfigvalue('Images','H','50'))
        self.mybuilder.get_object('adjustmentwidth').set_value(imgW-5)
        self.mybuilder.get_object('adjustmentheight').set_value(imgH-5)
        #print("#" + self.MySettings.readconfigvalue('Create', 'exact', 'True') + "#")
        createexact = (self.MySettings.readconfigvalue('Create', 'exact', 'True') == 'True')

        self.mybuilder.get_object('checkexact').set_active(createexact)

        self.recreateall()

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)


        print(self.outputfilepath)

    def savemysetings(self):
        '''Saves user preferences in the predefined conf file.

        '''
        #print 'saving...'self.mybuilder.get_object("hpaned1").get_position()
        #print('windowMain','height',str(self.CS.H))

        W = ''
        H = ''
        ismaxed = False
        infile = ''
        outpath = ''
        outfile = 'thenew'
        outputcounter = '1'
        imgW = '50'
        imgH = '50'

        if not self.clearonexit:
            W, H = self.get_size()
            ismaxed = str(self.ismaximized)
            infile = self.mybuilder.get_object('entry1').get_text().strip()
            outpath = self.mybuilder.get_object('entrysavepath').get_text().strip()
            outfile = self.mybuilder.get_object('entrynename').get_text().strip()
            #outputcounter = self.mybuilder.get_object('adjustmentnew').get_value()
            outputcounter = str(int(self.mybuilder.get_object('adjustmentnew').get_value()))
            #print(outputcounter)
            imgW = str(self.mybuilder.get_object('imagestop').get_allocated_width())
            imgH = str(self.mybuilder.get_object('imagestop').get_allocated_height())
            createexact = str(self.mybuilder.get_object('checkexact').get_active())

        self.MySettings.writeconfigvalue('windowMain','Width',str(W))#.encode('utf-8')
        self.MySettings.writeconfigvalue('windowMain','Height',str(H))#.encode('utf-8')
        try:
            self.MySettings.writeconfigvalue('windowMain','maximized',ismaxed)#.encode('utf-8')
        except:
            pass
        self.MySettings.writeconfigvalue('Paths', 'inputfile', infile)
        self.MySettings.writeconfigvalue('Paths', 'outputpath', outpath)
        self.MySettings.writeconfigvalue('Paths', 'outfile', outfile)
        self.MySettings.writeconfigvalue('Paths', 'outputcounter', outputcounter)
        self.MySettings.writeconfigvalue('Images', 'W', imgW)
        self.MySettings.writeconfigvalue('Images', 'H', imgH)
        self.MySettings.writeconfigvalue('Create', 'exact', createexact)
        #print(str(self.CS.hpaned1_position))

    def on_txtsearchtext_key_press_event(self, w, e):
        txt = Gdk.keyval_name(e.keyval)
        if type(txt) == type(None):
            # Make sure we don't trigger on unplugging the A/C charger etc
            return
        #self.testkeycodes(e,txt)
        txt = txt.replace('KP_', '')
        #print(txt)
        #print('-----')
        #if e.state & Gdk.ModifierType.CONTROL_MASK:
            #print(txt, 'with control')
            #print('--C---')
        if txt in ['Enter','Return']:
            self.on_bfind_clicked(self, w, e)
        #pass

    def on_windowMain_key_release_event(self, w, e):
        txt = Gdk.keyval_name(e.keyval)
        if type(txt) == type(None):
            # Make sure we don't trigger on unplugging the A/C charger etc
            return
        txt = txt.replace('KP_', '')
        #print(txt)
        #print('-----')
        #if e.state & Gdk.ModifierType.CONTROL_MASK:
            #print(txt, 'with control')
            #print('--C---')
        if txt == 'F4':
            #self.on_bfind_clicked(self, w, e)
            print(w,e)

    def on_entrystarttime_changed(self, *args):
        start = self.mybuilder.get_object('entrystarttime').get_text()
        startS = float(start)
        #print(startS)
        if startS >= self.videoinfo.duration:
            #print(self.videoinfo.duration)
            #print(float(self.videoinfo.fps))
            #newtime = self.videoinfo.duration - float(self.videoinfo.fps)
            self.mybuilder.get_object('entrystarttime').set_text('%6.2f' % (self.videoinfo.duration - self.videoinfo.spf))
            return
        duration = self.mybuilder.get_object('durationentrytime').get_text()
        endS = startS  + float(duration)
        if endS > self.videoinfo.duration:
            leaked = self.videoinfo.duration - startS
            self.mybuilder.get_object('durationentrytime').set_text('%6.2f' %  leaked)
            return
        self.recreateall()

    def on_durationentrytime_changed(self, *args):
        self.on_entrystarttime_changed(self, *args)

    def on_buttongotostart_clicked(self, *args):
        thetimetext = self.mybuilder.get_object('entrychecktime').get_text().strip()
        if ":" in thetimetext:
            splitted = thetimetext.split(":")
            fromhours = int(splitted[0]) * 60 * 60
            fromminutes = int(splitted[1]) * 60
            fromseconds = int(splitted[2])
            theseconds = fromhours + fromminutes + fromseconds
            #does nothing only shows in label
            self.mybuilder.get_object('labelconvertedseconds').set_text('%6.2f' % theseconds)
            #triggers update all
            self.mybuilder.get_object('entrystarttime').set_text(self.mybuilder.get_object('labelconvertedseconds').get_text())

    def on_buttonsetdiff_clicked(self, *args):
        thetimetext = self.mybuilder.get_object('entrychecktime2').get_text().strip()
        if ":" in thetimetext:
            splitted = thetimetext.split(":")
            fromhours = int(splitted[0]) * 60 * 60
            fromminutes = int(splitted[1]) * 60
            fromseconds = int(splitted[2])
            theseconds = fromhours + fromminutes + fromseconds
            thestart = float(self.mybuilder.get_object('entrystarttime').get_text())
            if theseconds > thestart:
                thediff = theseconds - thestart
            else:
                thediff = theseconds
            #does nothing only shows in label
            self.mybuilder.get_object('labelconvertedseconds2').set_text('%6.2f' % theseconds)
            #triggers update all
            self.mybuilder.get_object('durationentrytime').set_text('%6.2f' % thediff)

    def on_buttonincreaseS_clicked(self, *args):
        old = float(self.mybuilder.get_object('entrystarttime').get_text())
        new = old + float(self.mybuilder.get_object('entryincreaseStart').get_text())
        self.mybuilder.get_object('entrystarttime').set_text('%6.3f' % new)

    def on_buttonincreaseST_clicked(self, *args):
        old = float(self.mybuilder.get_object('durationentrytime').get_text())
        new = old + float(self.mybuilder.get_object('entryincreaseDuration').get_text())
        #triggers update all
        self.mybuilder.get_object('durationentrytime').set_text('%6.3f' % new)

    def on_buttonincreaseSF_clicked(self, *args):
        self.show_not_yet()

    def updatevideoinfo(self, text):
        '''Update internal video info.

        Update the suffix label.
        Update the 1/fps label.
        '''
        self.theextention =  os.path.splitext(text)[1]
        self.videofilepath = os.path.split(text)[0]
        thecommand = FF2 + ' ' + '-i "' + text.strip() + '" '
        tmp = tempfile.NamedTemporaryFile(mode='wt',encoding ='utf_8', suffix = '.txt', delete=False)
        with open(tmp.name, 'w', encoding ='utf_8') as f:
            p1 = subprocess.Popen(thecommand, stdout=f, stderr=f, shell = True)
            p1.wait()
        with open(tmp.name, 'rt', encoding ='utf_8') as f:
            mytext = f.read()
        infotext = ''
        for line in mytext.splitlines():
            if line.strip().startswith('encoder'):
                #print(line)
                infotext += line + '\n'
            if line.strip().startswith('Duration:'):
                #print(line)
                infotext += line + '\n'
            if line.strip().startswith('Stream'):
                #print(line)
                infotext += line + '\n'
        os.remove(tmp.name)
        self.videoinfo = VideoInfo(text,infotext)
        if self.videoinfo.fps:
            self.mybuilder.get_object('entryincreaseStart').set_text('%0.4f' % self.videoinfo.spf )
            self.mybuilder.get_object('entryincreaseDuration').set_text('%0.4f' % self.videoinfo.spf )
            self.mybuilder.get_object('labelfps').set_text('%0.5f' % self.videoinfo.spf )
            self.mybuilder.get_object('labeltotaltime').set_text('%0.2f' % (self.videoinfo.duration) + 's')
        self.updatesuffix()

    def updatesuffix(self):
        if self.mybuilder.get_object('spinbutton1').get_text() == '':
            return
        thenum = int(self.mybuilder.get_object('spinbutton1').get_text())
        if thenum < 1 or thenum > 999:
            return
        self.mybuilder.get_object('labelsuffix').set_label('%03d' % thenum + self.theextention)

    def gettimes(self):
        #print('in gettimes')
        #print(self.mybuilder.get_object('durationentrytime').get_text())
        #print(self.mybuilder.get_object('entrystarttime').get_text())
        #print(self.mybuilder.get_object('entry1').get_text())
        #print(os.path.isfile(self.mybuilder.get_object('entry1').get_text().strip()))
        #print(self.videoinfo.fps)

        if self.mybuilder.get_object('durationentrytime').get_text().strip() == '' or \
                self.mybuilder.get_object('entrystarttime').get_text().strip() == '' or \
                not os.path.isfile(self.mybuilder.get_object('entry1').get_text().strip()) or \
                not self.videoinfo.fps:#aka: no valid video
            return None,None
        #print('found seconds0')
        theseconds =  float(self.mybuilder.get_object('entrystarttime').get_text())
        durationseconds = float(self.mybuilder.get_object('durationentrytime').get_text())
        #print('found seconds')
        return theseconds, durationseconds

    def on_checkexact_toggled(self, *args):
        self.createcommand()

    def createcommand(self):
        theseconds, durationseconds = self.gettimes()
        #print(theseconds, durationseconds)
        if not theseconds:
            return
        endtime = theseconds + durationseconds
        inputfile = self.mybuilder.get_object('entry1').get_text().strip()
        outputfile = os.path.join(self.outputfilepath,self.mybuilder.get_object('entrynename').get_text().strip())
        outputfile += self.mybuilder.get_object('labelsuffix').get_label()
        startcomand = '-ss ' + '%0.2f' % theseconds + ' '
        if self.mybuilder.get_object('checkexact').get_active():
            copycommand = '-async 1 -strict -2 "' + outputfile + '" '
        else:
            copycommand = '-avoid_negative_ts 1 -codec copy "' + outputfile + '" '
#
        #if self.mybuilder.get_object('checkexact').get_active():
            #thecommand = FF1 + ' -y -ss ' + '%0.2f' % theseconds + ' -accurate_seek '
        #else:
        thecommand = FF1 + ' -y '
        if not self.mybuilder.get_object('checkexact').get_active():
            thecommand += startcomand
        thecommand += '-i "' + inputfile + '" '
        if self.mybuilder.get_object('checkexact').get_active():
            thecommand += startcomand
        thecommand += '-t ' + '%0.2f' % durationseconds + ' '
        thecommand += copycommand

        self.mybuilder.get_object('labelcommand').set_label(thecommand)

    def createimages(self):
        theseconds, durationseconds = self.gettimes()
        if not theseconds:
            return

        thewidth = int(self.mybuilder.get_object('adjustmentwidth').get_value())
        theheight = int(self.mybuilder.get_object('adjustmentheight').get_value())

        tmpjpg = os.path.join(self.outputfilepath, "out1.jpg")
        thecommand = FF1 + ' -ss ' + '%0.3f' % theseconds + ' ' + '-i "' + self.mybuilder.get_object('entry1').get_text().strip() + '" ' + ' -vframes 1 -q:v 2 "' + tmpjpg +'"'
        #print(thecommand)
        p1 = subprocess.Popen(thecommand, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell = True)
        p1.wait()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
        filename=tmpjpg,
        width=thewidth,
        height=theheight,
        preserve_aspect_ratio=True)
        self.mybuilder.get_object('imagestart').set_from_pixbuf(pixbuf)
        os.remove(tmpjpg)
        tmpjpg = os.path.join(self.outputfilepath, "out1.jpg")
        thecommand = FF1 + ' -ss ' + '%0.3f' % (theseconds + durationseconds) + ' ' + '-i "' + self.mybuilder.get_object('entry1').get_text().strip() + '" ' + ' -vframes 1 -q:v 2 "' + tmpjpg +'"'
        #print(thecommand)
        p1 = subprocess.Popen(thecommand, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell = True)
        p1.wait()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
        filename=tmpjpg,
        width=thewidth,
        height=theheight,
        preserve_aspect_ratio=True)
        self.mybuilder.get_object('imagestop').set_from_pixbuf(pixbuf)
        os.remove(tmpjpg)

    #def on_grid1_check_resize(self, *args):
    def on_buttonfixsize_clicked(self, *args):
        print (self.get_size()[0])
        #print (self.get_width())
        #get_preferred_height()
        print ('scaleh',self.mybuilder.get_object('scaleH').get_allocated_height())
        print ('scalehw',self.mybuilder.get_object('scaleH').get_allocated_width())
        print ('image',self.mybuilder.get_object('imagestop').get_allocated_height())
        print (self.mybuilder.get_object('imagestop').get_preferred_size ()[0])#'minimum_size'])
        #print (self.mybuilder.get_object('imagestop').get_preferred_size ()['natural_size'])
        #self.mybuilder.get_object('adjustmentwidth').set_value()
        w = int((self.get_size()[0] - self.mybuilder.get_object('scaleH').get_allocated_width()) / 2)-5
        h = self.mybuilder.get_object('imagestop').get_allocated_height()
        self.mybuilder.get_object('adjustmentwidth').set_value(w-5)
        self.mybuilder.get_object('adjustmentheight').set_value(h-5)
        self.createimages()
        print ('image',self.mybuilder.get_object('imagestop').get_allocated_height())
        print ('image',self.mybuilder.get_object('imagestop').get_allocated_width())

    def recreateall(self):
        self.createcommand()
        self.createimages()

    def on_entrysavepath_changed(self, *args):
        self.createcommand()

    def on_spinbutton1_changed(self, *args):
        if self.mybuilder.get_object('spinbutton1').get_text() == '':
            return
        thenum = int(self.mybuilder.get_object('spinbutton1').get_text())
        if thenum < 1 or thenum > 999:
            return
        self.mybuilder.get_object('labelsuffix').set_label('%03d' % thenum + self.theextention)
        self.createcommand()


    def on_buttoninfo_clicked(self, *args):
        '''Display some info about the input file.

        '''
        if self.videoinfo.fulltext:
            self.show_ok(self.videoinfo.fulltext)
        else:
            self.show_ok("NO INFO")


    def on_buttonsavepath_clicked(self, *args):
        '''Select folder for output.

        Folder will be used for temporary files also

        '''
        dialog = Gtk.FileChooserDialog("Please choose a folder", self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             "Select", Gtk.ResponseType.OK))
        dialog.set_current_folder(self.outputfilepath)
        dialog.set_default_size(800, 400)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Select clicked")
            print("Folder selected: " + dialog.get_filename())
            self.outputfilepath = dialog.get_filename()
            self.mybuilder.get_object('entrysavepath').set_text(self.outputfilepath)
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")
        dialog.destroy()


    def on_buttonrun_clicked(self, *args):
        '''Execute the cut.

        '''
        p1 = subprocess.Popen(self.mybuilder.get_object('labelcommand').get_label(), stdout=subprocess.PIPE, shell = True)
        p1.wait()
        self.show_ok("Created!")

    def on_buttonconcat_clicked(self, *args):
        files = [os.path.join(self.outputfilepath,f) for f in os.listdir(self.outputfilepath) if os.path.isfile(os.path.join(self.outputfilepath,f))]
        tmp = tempfile.NamedTemporaryFile(mode='wt',encoding ='utf_8', suffix = '.txt', delete=False)
        with open(tmp.name, 'w', encoding ='utf_8') as f:
            for filename in sorted(files):
                f.write("file '" + filename + "'" + '\n')
        print(tmp.name)

        #new_file, filename = tempfile.mkstemp(suffix = '.txt', text=True)
        #for aname in sorted(files):
            #os.write(new_file, "file '" + filename + "'")
        #os.close(new_file)
        #print(filename)
        #b = tempfile.mkstemp
        #with open(b, 'w', encoding ='utf_8') as f:
            #for filename in sorted(files):
                #b.write("file '" + filename + "'")
        #print(sorted(files))
        n = self.mybuilder.get_object('entrynename').get_text().strip() + self.theextention
        outputfile = os.path.join(self.outputfilepath,n)
        print(outputfile)
        concatcommand = '/usr/bin/ffmpeg -f concat -safe 0 -i "' + tmp.name + '" -c copy ' + outputfile
        p1 = subprocess.Popen(concatcommand, stdout=subprocess.PIPE, shell = True)
        p1.wait()
        os.remove(tmp.name)
        self.show_ok("Concatenated!")

    def on_buttonselectinputfile_clicked(self, *args):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_current_folder(self.videofilepath)
        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            #print("Open clicked")
            #print("File selected: " + dialog.get_filename())
            self.updatevideoinfo(dialog.get_filename())
            print('fps',self.videoinfo.fps)
            self.mybuilder.get_object('entry1').set_text(self.videoinfo.filename)
            self.recreateall()
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("video files")
        filter_text.add_mime_type("video/mp4")
        filter_text.add_mime_type("video/x-matroska")
        filter_text.add_mime_type("video/x-msvideo")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def on_checkclearonexit_toggled(self, *args):
        self.clearonexit = self.mybuilder.get_object('checkclearonexit').get_active()

    def on_buttoncopycommand_clicked(self, *args):
        self.clipboard.set_text(self.mybuilder.get_object('labelcommand').get_label(), -1)

    def on_entrynename_changed(self, *args):
        print('on_entrynename_changed')
        self.createcommand()
    def on_keyeeepressed(self, *args):
        self.show_not_yet()

    def show_not_yet(self):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "NOT yet")
        dialog.format_secondary_text("Not yet implemented")
        dialog.run()
        dialog.destroy()

    def show_ok(self,title):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "OK")
        dialog.format_secondary_text(title)
        dialog.run()
        dialog.destroy()

    def exactcopy(self):
        #First do a fast copy
        #probe the file to find start and duration
        #substruct this temporary start from original start and from duration
        #copy the temp file using vsync and new original start
        pass
