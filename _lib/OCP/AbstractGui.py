# Copyright Ηλιάδης Ηλίας, 2017.
# contact http://gnu.kekbay.gr/OCPcompanion/  -- mailto:OCPcompanion@kekbay.gr
#
# This file is part of OCPcompanion.
#
# OCPcompanion is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3.0 of the License, or (at your option) any
# later version.
#
# OCPcompanion is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with OCPcompanion.  If not, see <http://www.gnu.org/licenses/>.

'''An abstrract class for a modal like window.

Provides a "modal" window with the following predefined functions:
: run : which does the modality and returns with the window hidden
: on_bexit_clicked
: on_babout_clicked


It assumes you have:
1. An object with
1.1 workingdir property which is used to obtain the main path
1.2 icon property with a main icon for all windows (can be overriden before "run")
2. A lib repository inside the main path with
2.1 OCPconfigParser (parser for conf files)
3. A glade file inside the main path, inside a directory named _glades
3.1 with a main container named box1
3.2 with a label named lblversion
3.3 with a button named babout
USAGE 1:
class mymodalWindow(OCPAbstractGui):
    def __init__( self, myApp, gladename):
        OCPAbstractGui.__init__(self,myApp, gladename)

    #if you have a button named say mybutton
    #and you have connected the click event to this function
    def on_mybutton_clicked(self, widget,*args):
        #do something here like
        self.returnparameter = 1
        #and hide window to return to your code
        self.hide()

in your code create an object of this class (mymodalWindow)
(passing the appropriate parameters
testwindow = mymodalWindow(objectwithappinfo, agladefilename)
)
then
response = testwindow.run()
and when user closes the window the code will return here.
response variable will have a value based either on

DO NOT:
override self.wecanexitnow, since it is used to actually return to your code

'''

import time
import os, sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GLib
from gi.repository import GObject

import datetime

def dummyfunction():
    pass

class OCPAbstractGui(Gtk.Window):

    def __init__( self, myApp, gladename, otherwidjets = (),parent = None,mainbox=None,savemysettings=None ):
        Gtk.Window.__init__(self, name='windowMain')
        #print(otherwidjets)
        if parent != None:
            self.set_transient_for(parent)
            #print('has parent', parent)
            self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)#_ON_PARENT
            self.set_modal(True)
            #self.set_position = Gdk.CENTER_ON_PARENT
            #print('=====')
            #print('center', Gtk.WindowPosition.CENTER_ON_PARENT,parent, int(Gtk.WindowPosition.CENTER))
        self.fs = None
        self.App = myApp
        #print(self.App.appname)
        self.set_title(self.App.appname)
        self.myrootpath = self.App.workingdir
        from . import configarser as myconfig
        #from self.myrootpath import pyvb.*
        self.MySettings = myconfig.MyConfigs(self.App.conf)
        self.naivetime = datetime.datetime(2000,1,1)
        self.operationstarted = False
        self.InstanceName = 'OCP' + self.App.appname + self.App.version + '-' + str(datetime.datetime.now())
        #LOAD ui
        self.mybuilder = Gtk.Builder()
        if mainbox == None:
            mainbox = 'box1'
        if otherwidjets == None:
            self.mybuilder.add_objects_from_file(os.path.join(self.myrootpath, '_glades', gladename),
                    (mainbox,) )
        else:
            list1 = [x for x in otherwidjets]
            list1.append( mainbox )
            b = tuple(list1)
            #b.extend(zip(otherwidjets))
            #print (b)
            self.mybuilder.add_objects_from_file(os.path.join(self.myrootpath, '_glades', gladename), b )
            #print('added more widgets')
            #print(b)

        self.add(self.mybuilder.get_object(mainbox))
        self.mybuilder.connect_signals(self)

        self.connect("hide", self.hideme)
        self.mybuilder.get_object('bexit').connect("clicked", self.on_bexit_clicked)
        self.mybuilder.get_object('babout').connect("clicked", self.on_babout_clicked)
        self.mybuilder.get_object('lblversion').set_label('Version: ' + self.App.version + ' ')
        self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#228b22"))#forest green
        self.set_icon(self.App.icon)

        if savemysettings == None:
            self.savemysettings = dummyfunction
        else:
            self.savemysettings = savemysettings

        self.wecanexitnow = False
        self.returnparameter = None

    def run(self):
        #now we can show the window
        self.show_all()
        #loop eternaly
        while True:
            #if we want to exit
            if self.wecanexitnow:
                #print('wecanexitnow')
                #break the loop
                break
            #else...
            #give others a change...
            while Gtk.events_pending():
                Gtk.main_iteration()
        #we can now return to calling procedure
        #can return any variable we want
        #or we can check the widgets and/or variables
        #from inside calling procedure
        #print('from abstract',self.returnparameter)
        return self.returnparameter

    def on_bexit_clicked(self, widget,*args):
        #self.on_windowMain_destroy(*args)
        self.set_transient_for()
        self.set_modal(False)
        self.hide()

    def hideme(self, *args):
        self.savemysettings()
        #print('hide triggered')
        self.wecanexitnow = True

    def on_babout_clicked(self, widget,*args):
        from .aboutbox import AboutBox #as AboutBox
        app = AboutBox(self)
