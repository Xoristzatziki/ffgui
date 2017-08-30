#Copyright Ηλιάδης Ηλίας, 2017
#v.0.0.31

try:
    import sys, os
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk

except:
    sys.exit(1)

#assuming window contains also App contents
class AboutBox:
    def __init__(self, appwindow):
        aboutdialog = Gtk.AboutDialog()
        aboutdialog.set_program_name(appwindow.App.appname)
        print(appwindow.App.appname)
        aboutdialog.set_version('v.' + appwindow.App.version + ' ')
        #TODO aboutdialog.set_license_type(Gtk.GTK_LICENSE_LGPL_3_0)
        with open(os.path.join(appwindow.App.workingdir, '_data', 'AUTHORS'), mode='rt', encoding='utf-8') as f:
            aboutdialog.set_authors(f.readlines())
        with open(os.path.join(appwindow.App.workingdir, '_data', 'COPYRIGHT'), mode='rt', encoding='utf-8') as f:
            aboutdialog.set_copyright(f.read())
        with open(os.path.join(appwindow.App.workingdir, '_data', 'COMMENTS'), mode='rt', encoding='utf-8') as f:
            aboutdialog.set_comments(f.read())
        aboutdialog.set_transient_for(appwindow)
        aboutdialog.set_logo(appwindow.App.icon)
        aboutdialog.run()
        aboutdialog.destroy()
