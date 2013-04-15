'''
 *  Copyright (c) 2011
 *  http://teachthe.net/?page_id=1657
 *  Originally developed by Sean Kooyman | teachthe.net(at)gmail.com
 *
 *  License:  GPL version 3.
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy
 *  of this software and associated documentation files (the "Software"), to deal
 *  in the Software without restriction, including without limitation the rights
 *  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *  copies of the Software, and to permit persons to whom the Software is
 *  furnished to do so, subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be included in
 *  all copies or substantial portions of the Software.

 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 *  THE SOFTWARE.
'''
import platform
if platform.system() == 'Windows':
    settings = {"os_version": "win"}
else:
    settings = {"os_version": "osx"}
import json

import wx, random, Image
import os
import time
import toasterbox #popup in lower right for new pastes
import webbrowser #to open http links in user's preferred browser
import shutil #to copy files to the sent directory
import string
import screenshotRect
from time import gmtime, strftime

import cb_helper

import subprocess
import sys

from ftplib import FTP
ftp_conn = None

clipboxWindow = None
weburl = "http://teachthe.net/?page_id=1657"

settings['use_ftp'] = 1
settings['ftp_host'] = ""
settings['ftp_public_url'] = ""
settings['ftp_username'] = ""
settings['ftp_password'] = ""
settings['ftp_remote_dir'] = ""
settings['db_public_path'] = ""
settings['db_public_url'] = ""


class mainFrame(wx.Frame):
    global clipboxWindow, settings
    def __init__(self, parent, id, title):
        style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER
        self.window = wx.Frame.__init__(self, parent, id, title, size=(450,555), style=style)

        self.regHotKey()
        self.Bind(wx.EVT_HOTKEY, self.handleHotKey, id=self.hotCopy)
        self.Bind(wx.EVT_HOTKEY, self.handleHotKey, id=self.hotScreenRect)

        icon1 = wx.Icon("images/clipboard.png", wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon1)

        self.tskic = MyTaskBarIcon(self)

        self.Bind(wx.EVT_CLOSE,self.OnClose)

        wx.GetApp().Bind(wx.EVT_QUERY_END_SESSION, self.onFullClose)
        wx.GetApp().Bind(wx.EVT_END_SESSION, self.onFullClose)
        self.Bind(wx.EVT_CLOSE, self.onFullClose)

        wx.CallAfter(self.createSubWindows)
        self.Layout()

    def createSubWindows(self):
        self.toasterWindow = ToasterBox(None, -1, 'ToasterBox')

    def onFullClose(self, event):
        for w in wx.GetTopLevelWindows():
            w.Destroy()
        self.Destroy()

    def OnClose(self,event):
        self.Show(False)
        event.Veto()

    def regHotKey(self):
        mod_control = cb_helper.get_keycode('control_mod')
        mod_shift = cb_helper.get_keycode('shift_mod')
        self.hotCopy = 100
        self.RegisterHotKey(
            self.hotCopy, 
            mod_control | mod_shift, 
            cb_helper.get_keycode('c')) 

        self.hotScreenRect = 104
        self.RegisterHotKey(
            self.hotScreenRect, #a unique ID for this hotkey
            mod_control | mod_shift, #the modifier keys
            cb_helper.get_keycode('x'))

    def handleHotKey(self, evt):
        eventId = evt.GetId()
        if eventId == 104: #hotScreenRect

            if settings['os_version'] == 'osx':
                cb_helper.send_key('screenshot')
                self.onHotCopy()

            elif settings['os_version'] == 'win':
                """
                #use print screen to put screen contents on clipboard - results in unsolvable clipboard in use bug :(
                import ctypes
                user32 = ctypes.windll.user32
                keycode = int("0x2C", 16)
                time.sleep(1)
                user32.keybd_event(keycode,0,2,0) #is the code for KEYDOWN
                time.sleep(1)
                user32.keybd_event(keycode,0,0,0) #is the code for KEYDUP
                
                self.onHotCopy()
                """
                
                """
                # Take snapshot of desktop, allowing user to specify target area - results in unsolvable clipboard in use bug :(
                ssdlg = screenshotRect.Screen_Capture(None)
                ssdlg.ShowModal()
                ssdlg.Raise()
                x1 = min(ssdlg.c1.x, ssdlg.c2.x)
                x2 = max(ssdlg.c1.x, ssdlg.c2.x)
                y1 = min(ssdlg.c1.y, ssdlg.c2.y)
                y2 = max(ssdlg.c1.y, ssdlg.c2.y)
                captureBmapSize = (x2-x1, y2-y1)
                #captureBmapSize = (wx.SystemSettings.GetMetric( wx.SYS_SCREEN_X ),
                #wx.SystemSettings.GetMetric( wx.SYS_SCREEN_Y ) )
                captureStartPos = (x1, y1)    # Arbitrary U-L position anywhere within the screen
                scrDC = wx.ScreenDC()
                scrDcSize = scrDC.Size
                scrDcSizeX, scrDcSizeY = scrDcSize

                # Cross-platform adaptations :
                scrDcBmap     = scrDC.GetAsBitmap()
                scrDcBmapSize = scrDcBmap.GetSize()

                # Check if scrDC.GetAsBitmap() method has been implemented on this platform.
                if   scrDcBmapSize == (0, 0) :      # Not implemented :  Get the screen bitmap the long way.

                    scrDcBmap = wx.EmptyBitmap( *scrDcSize )
                    scrDcBmapSizeX, scrDcBmapSizeY = scrDcSize

                    memDC = wx.MemoryDC( scrDcBmap )

                    memDC.Blit( 0, 0,                           # Copy to this start coordinate.
                                scrDcBmapSizeX, scrDcBmapSizeY, # Copy an area this size.
                                scrDC,                          # Copy from this DC's bitmap.
                                0, 0,                    )      # Copy from this start coordinate.

                    memDC.SelectObject( wx.NullBitmap )     # Finish using this wx.MemoryDC.
                                                            # Release scrDcBmap for other uses.
                else :
                    scrDcBmap = scrDC.GetAsBitmap()     # So easy !  Copy the entire Desktop bitmap.

                bitmap = scrDcBmap.GetSubBitmap( wx.RectPS( captureStartPos, captureBmapSize ) )
                bitmap.SaveFile( 'temp/screenshot.png', wx.BITMAP_TYPE_PNG )

                bd = wx.BitmapDataObject()
                if wx.TheClipboard.Open():
                    successb = wx.TheClipboard.SetData(bd)
                    wx.TheClipboard.Close()
                    
                self.onHotCopy()
                """
                
                from PIL import ImageGrab
                im = ImageGrab.grab()
                im.save('temp/screenshot.png', 'PNG')
                self.file_paste('temp/screenshot.png', 'screenshot_'+strftime("%Y-%m-%d_%H-%M-%S", gmtime())+'.png')

                
        if eventId == 100: #hotCopy
            cb_helper.wait_for_key_up('copy')
            cb_helper.send_key('copy')
            time.sleep(1.5)
            self.onHotCopy()
            
    def file_paste(self, full_file_name, uploaded_name=""):
        global settings
        if uploaded_name == "":
            uploaded_name = os.path.basename(full_file_name)
        pasteID =  uploaded_name
        try:
            if settings['use_ftp'] == 1:
                ftp_conn = FTP(settings['ftp_host'], settings['ftp_username'], settings['ftp_password'])
                ftp_conn.storbinary('STOR '+settings['ftp_remote_dir']+pasteID, open(full_file_name, 'rb'))
                public_paste_url = settings['ftp_public_url']+pasteID
            else:
                shutil.copyfile(full_file_name, settings['db_public_path']+'.clipbox/'+pasteID)
                public_paste_url = 'http://dl.dropbox.com/u/'+settings['db_public_url']+'/' + '.clipbox/'+pasteID
            
            td = wx.TextDataObject()
            td.SetText(public_paste_url)
            if wx.TheClipboard.Open():
                successt = wx.TheClipboard.SetData(td)
                wx.TheClipboard.Close()
            clipboxWindow.toasterWindow.RunToaster('Download URL copied to your Clipboard!', 'file')
        except:
            clipboxWindow.toasterWindow.RunToaster('An Error Occurred.', 'file')

    def onHotCopy(self):
        global settings
        cb_helper.catch_clipboard_in_use_bug()
        if wx.TheClipboard.Open():
            td = wx.TextDataObject()
            fd = wx.FileDataObject()
            bd = wx.BitmapDataObject()
            successt = wx.TheClipboard.GetData(td)
            successf = wx.TheClipboard.GetData(fd)
            successb = wx.TheClipboard.GetData(bd)
            wx.TheClipboard.Close()
            text = td.GetText()
            ftext = ''.join(fd.GetFilenames())
            bimg = bd.GetBitmap() #this is a wx.Bitmap
            pasteText = text

        #on OSX, in a file 'copy' event, both these variables are true
        if successt and successf:
            successt = False
            successb = False

        self.Show(False)
        if settings['use_ftp'] == 0:
            #if clipbox dropbox folder doesn't exist, create it
            if not os.path.exists(settings['db_public_path'] + '.clipbox/'):
                os.makedirs(settings['db_public_path'] + '.clipbox/')
            
        if successt:
            pasteID = strftime("%Y-%m-%d_%H-%M-%S", gmtime())+''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))

            try:
                if settings['use_ftp'] == 1:
                    tmpf = open("tmptxt", 'w')
                    tmpf.write(pasteText)
                    tmpf.close()
                    ftp_conn = FTP(settings['ftp_host'], settings['ftp_username'], settings['ftp_password'])
                    ftp_conn.storbinary('STOR '+settings['ftp_remote_dir']+pasteID, open("tmptxt"))
                    public_paste_url = settings['ftp_public_url']+pasteID
                else:
                    datafo = open(settings['db_public_path']+'.clipbox/'+pasteID, 'w')
                    datafo.write(pasteText)
                    datafo.close()
                    public_paste_url = 'http://dl.dropbox.com/u/'+settings['db_public_url']+'/' + '.clipbox/'+pasteID
                
                clipboxWindow.toasterWindow.RunToaster('Download URL copied to your Clipboard!', 'text')
                td = wx.TextDataObject()
                td.SetText(public_paste_url)
                if wx.TheClipboard.Open():
                    successt = wx.TheClipboard.SetData(td)
                    wx.TheClipboard.Close()
            except:
                clipboxWindow.toasterWindow.RunToaster('An Error Occurred.', 'text')
                
        if successf:
            allFileNames = fd.GetFilenames()
            self.file_paste(allFileNames[0])
                
        if successb:
            tmpPasteName = strftime("%Y-%m-%d_%H-%M-%S", gmtime())+''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
            bimg.SaveFile('temp/'+tmpPasteName+'.png', wx.BITMAP_TYPE_PNG)
            fullpath = os.getcwd() + "/temp/"+tmpPasteName+".png"
            pasteID = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6)) + '_' + os.path.basename(fullpath)
            try:
                if settings['use_ftp'] == 1:
                    ftp_conn = FTP(settings['ftp_host'], settings['ftp_username'], settings['ftp_password'])
                    ftp_conn.storbinary('STOR '+settings['ftp_remote_dir']+pasteID, open(fullpath, 'rb'))
                    public_paste_url = settings['ftp_public_url']+pasteID
                else:
                    shutil.copyfile(fullpath, settings['db_public_path']+'.clipbox/'+pasteID)
                    public_paste_url = 'http://dl.dropbox.com/u/'+settings['db_public_url']+'/' + '.clipbox/'+pasteID
                td = wx.TextDataObject()
                td.SetText(public_paste_url)
                if wx.TheClipboard.Open():
                    successt = wx.TheClipboard.SetData(td)
                    wx.TheClipboard.Close()
                clipboxWindow.toasterWindow.RunToaster('Download URL copied to your Clipboard!', 'image')
            except ImportWarning:
                clipboxWindow.toasterWindow.RunToaster('An Error Occurred.', 'image')


class MyTaskBarIcon(wx.TaskBarIcon):
    global weburl, clipboxWindow, settings
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)

        self.frame = frame

        myimage = wx.Bitmap('images/spsprite.png', wx.BITMAP_TYPE_PNG)
        submyimage = myimage.GetSubBitmap(wx.Rect(0,0,16,16))
        myicon = wx.EmptyIcon()
        myicon.CopyFromBitmap(submyimage)
        self.SetIcon(myicon, 'ClipBox')
        self.Bind(wx.EVT_MENU, self.gotoweb, id=8)
        self.Bind(wx.EVT_MENU, self.showPreferences, id=14)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=3)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_click)


    def OnTaskBarClose(self, event):
        self.RemoveIcon()
        self.frame.Destroy()
        clipboxWindow.toasterWindow.Destroy()
        clipboxWindow.Destroy()
        for w in wx.GetTopLevelWindows():
            w.Destroy()
            
    def on_left_click(self, e):
        self.PopupMenu(self.CreatePopupMenu())

    def CreatePopupMenu(self):
        tbmenu = wx.Menu()
        tbmenu.Append(14, 'Preferences...')
        tbmenu.Append(8, 'Go To Website')
        tbmenu.Append(3, 'Exit')
        return tbmenu

    def gotoweb(self, event):
        global weburl
        webbrowser.open(weburl)

    def showPreferences(self, event):
        if settings['os_version'] == 'osx':
            subprocess.call("open config.txt", shell=True)
        elif settings['os_version'] == 'win':
            subprocess.call("start config.txt", shell=True)

class ToasterBox(wx.Frame):
   def __init__(self, parent, id, title):
       wx.Frame.__init__(self, parent, id, title)
       self.panel = wx.Panel(self)
       self.Show(False)

   def RunToaster(self, poptext, type):
        toaster = toasterbox.ToasterBox(self, tbstyle=toasterbox.TB_COMPLEX)
        toaster.SetPopupPositionByInt(3)
        toaster.SetPopupPauseTime(5000)

        tbpanel = toaster.GetToasterBoxWindow()
        panel = wx.Panel(tbpanel, -1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        horsizer1 = wx.BoxSizer(wx.HORIZONTAL)

        if type == "file":
            myimage = wx.Bitmap("images/file_icon_50.png", wx.BITMAP_TYPE_PNG)
        elif type == "text":
            myimage = wx.Bitmap("images/text_icon_50.png", wx.BITMAP_TYPE_PNG)
        elif type == "image":
            myimage = wx.Bitmap("images/image_icon_50.png", wx.BITMAP_TYPE_PNG)
        else:
            myimage = wx.Bitmap("images/text_icon_50.png", wx.BITMAP_TYPE_PNG)
        stbmp = wx.StaticBitmap(panel, -1, myimage)
        horsizer1.Add(stbmp, 0)

        sttext = wx.StaticText(panel, -1, poptext)
        sttext.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL, False, "Verdana"))
        horsizer1.Add(sttext, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        sizer.Add((0,5))
        sizer.Add(horsizer1, 0, wx.EXPAND)

        sizer.Layout()
        panel.SetSizer(sizer)

        toaster.AddPanel(panel)
        toaster.Play()

class MyApp(wx.App):
    global settings, clipboxWindow
    def OnInit(self):
        global settings, clipboxWindow
    
        forcelogin = 0
        try:
            spdatafile = open('config.txt', 'r')
            jsoncode = spdatafile.read()
            spdatafile.close()
            data = json.loads(jsoncode)
            if 'use_ftp' in data:
                settings['use_ftp'] = data['use_ftp']
            if settings['use_ftp'] == 1:
                settings['ftp_host'] = data['ftp_host']
                settings['ftp_public_url'] = data['ftp_public_url']
                settings['ftp_username'] = data['ftp_username']
                settings['ftp_password'] = data['ftp_password']
                settings['ftp_remote_dir'] = data['ftp_remote_dir']
                if settings['ftp_host'] != '' and settings['ftp_public_url'] != '' and settings['ftp_username'] != '' and settings['ftp_password'] != '':
                        clipboxWindow = mainFrame(None, -1, 'ClipBox') #already logged in
                else:
                    forcelogin = 1
            else:
                settings['db_public_path'] = data['db_public_path']
                settings['db_public_url'] = data['db_public_url']
                if settings['db_public_path'] != '' and settings['db_public_url'] != '':
                    if not os.path.isdir(settings['db_public_path']):
                        forcelogin = 1
                    else:
                        clipboxWindow = mainFrame(None, -1, 'ClipBox') #already logged in
                else:
                    forcelogin = 1
        except:
            forcelogin = 1
            

        if forcelogin == 1:
            if settings['os_version'] == 'osx':
                subprocess.call("open config.txt", shell=True)
            elif settings['os_version'] == 'win':
                subprocess.call("start config.txt", shell=True)
            sys.exit()

        return True

    def onCloseIt(self, event):
        for w in wx.GetTopLevelWindows():
            w.Destroy()
        self.Destroy()

app = MyApp(0)
app.MainLoop()
