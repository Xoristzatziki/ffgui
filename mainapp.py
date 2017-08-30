#!/usr/bin/python3
#Copyright Ηλίας Ηλιάδης

import time
import os, sys
try:
    import gi
    gi.require_version('Gtk', '3.0')
except:
    sys.exit(1)

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GLib
from gi.repository import GObject

import datetime

from _lib.OCP import *
import _lib.maingui as myMainGui

APPNAME = 'ffgui'
#TODO:set version before production
version = ''

class App:
    def __init__( self, realfile_dir):
        self.appname = APPNAME
        #TODO: on producted game get it from version
        #print(os.path.basename(realfile_dir))
        #relversionnums = os.path.basename(realfile_dir)[1:].split('.')
        if version == '':
            self.version = os.path.basename(realfile_dir)[2:]
        else:
            self.version = version
        self.workingdir = realfile_dir
        self.icon = GdkPixbuf.Pixbuf.new_from_file(os.path.join(self.workingdir, '_icons', "logo.png"))
        userdir = os.getenv('USERPROFILE') or os.getenv('HOME')
        confpath = os.path.join(userdir, '.OCP' + self.appname)
        #TODO: what if we cannot create conf directory?
        if not os.path.exists(confpath):
            os.mkdir(confpath)
        self.conf = os.path.join(confpath, 'OCP.conf')
        self.MySettings = vbpPrivateProfile(self.conf)

        self.iamonline = False#no need to save in conf
        self.wantsfromonline = False#no need to save in conf

def main(realfile_dir):
    myApp = App(realfile_dir)
    gladenongraphicstuple =('adjustmentnew','adjustmentwidth','adjustmentheight')
    mainwindow = myMainGui.MainGui(myApp,'maingui.glade',gladenongraphicstuple,mainbox='grid1')
    mainwindow.set_position(Gtk.WindowPosition.CENTER)
    response = mainwindow.run()
    sys.exit(response)

if __name__ == "__main__":
    realfile = os.path.realpath(__file__)
    realfile_dir = os.path.dirname(os.path.abspath(realfile))
#    try:
#        print realfile_dir
#    except:
#        pass
    test = main(realfile_dir)
