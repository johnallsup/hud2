control_messages = """
@fontsize <n>
@showlast
@quit
@hide
@hudcolor
@hudcolorf
@hudtime
@help
"""

import sys
import re
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtNetwork import *
from datetime import datetime
from pythonosc import osc_message
from pythonosc.osc_message import OscMessage

def clamp(x,a,b):
  return max(min(x,b),a)

HUDTIME=300000
KILLTIME=4000
class HudOsc(QWidget):
  def handleUdp(self):
    try:
      while self.udpSocket.hasPendingDatagrams():
        datagram = self.udpSocket.receiveDatagram(4096)
        data = datagram.data().data()
        self.process_data(data)
    except KeyboardInterrupt:
      QApplication.instance().quit()

  def process_data(self,data):
    message = OscMessage(data)
    addr = message.address
    params = message.params
    self.handle_message(addr,params)

  def mousePressEvent(self,e):
    self.hide()
    super().mousePressEvent(e)

  def __init__(self,x,y,w,h,port=2708,hudtime=HUDTIME):
    super().__init__()
    self.already = False

    print(f"Creating HUD on port {port}")
    self.hudtime = hudtime
    self.showSmall = False
    self.showSmallSize = 50

    self.udpSocket = QUdpSocket()
    self.udpSocket.readyRead.connect(self.handleUdp)
    self.udpSocket.bind(QHostAddress.Any,port)

    self.x = x
    self.y = y
    self.w = w
    self.h = h

    # size and position – possibly necessary to recompute, resize and move depending on hud contents
    self.resize(w,h)
    self.move(x,y)
    #self.resize(600,600)

    # attributes for display
    self.content = ""
    self.fontname = "Optima"
    self.fontsize = 100
    self.font = QFont(self.fontname,self.fontsize)
    self.smallFont = QFont(self.fontname,self.showSmallSize)
    self.color = QColor(100,255,100)
    self.ocolor = Qt.black
    self.pen = QPen(self.ocolor,16)
    self.showtime = 5

    # two timers: one to auto-hide the hud, the second to kill the entire application
    self.timer = QTimer(self)
    self.dtimer = QTimer(self)

    # so a call to show() knows whether we are already showing or not (and vice versa for hide())
    self.showing = False

    # window attributes
    self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    self.setAttribute(Qt.WA_TranslucentBackground)

  def paintEvent(self,event):
    with QPainter(self) as p:
      rect = self.rect()
      width = rect.width()
      text = self.content
      lines = text.splitlines()
      font = self.smallFont if self.showSmall else self.font
      metrics = QFontMetrics(font)
      h = metrics.height()
      #print(h)
      for i,line in enumerate(lines):
        dlines = []
        dline = ""
        lastspace = 0
        j = 0
        for char in line:
          dline1 = dline + char
          if re.match(r"\s",char):
            lastspace = j
          drect = metrics.boundingRect(dline1)
          dlinew = drect.width()
          if dlinew >= width:
            if lastspace == 0:
              lastspace = j-1
            dlines.append(dline1[:lastspace+1].rstrip())
            dline = dline1[lastspace+1:].lstrip()
            j = 0
            lastspace = 0
          else:
            dline = dline1
          j += 1
        dlines.append(dline)

        for dline in dlines:
          path = QPainterPath()
          path.addText(0,0,font,str(dline))
          p.translate(0,h)

          # draw twice so that the black outline is _behind_ the fill
          p.setPen(self.pen)
          p.drawPath(path)
          p.setBrush(self.color)
          p.setPen(Qt.NoPen)
          p.drawPath(path)

  def sethue(self,h):
    self.color = QColor.fromHsl(h%360,255,180)

  def doshow(self):
    self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    self.setAttribute(Qt.WA_TranslucentBackground)
    if not self.showing:
      super().show()
      self.showing = True
      self.timer.stop()
    self.update()
    self.timer.singleShot(self.hudtime,self.hide)

  def handle_message(self,addr,params):
    self.showSmall = False
    addr = addr.lstrip("/")
    match addr:
      case "quit":
        return QCoreApplication.quit()
      case "help":
        self.content = control_messages
        self.showSmall = True
        return self.doshow()
      case "hide":
        return self.hide()
      case "hudcolorh":
        try:
          h = params[0]
          self.color = QColor(h)
        except IndexError:
          self.content = "Error Missing Color (hudcolorh)"
          return self.doshow()
        except ValueError:
          self.content = f"Error Invalid Colour: {h} (hudcolorh)"
          return self.doshow()
      case "hudhue":
        try:
          h = params[0]
          h = int(h)
          self.sethue(h)
          self.content = f"Hue now {h}"
          return self.doshow()
        except IndexError:
          self.content = "Error Missing Color (hudhue)"
          return self.doshow()
        except ValueError:
          self.content = f"Error Invalid Hue: {h} (hue)"
          return self.doshow()
      case "hudcolor":
        try:
          r,g,b = params[0]
        except ValueError:
          self.content = "Error Missing Color Components (color)"
          return self.doshow()
        try:
          r,g,b = map(int,(r,g,b))
        except ValueError:
          self.content = f"Error Invalid Params: {(r,g,b)} (color)"
          return self.doshow()
        try:
          self.color = QColor(r,g,b)
        except Exception:
          self.content = f"Error QColor Params: {(r,g,b)} (color)"
          return self.doshow()
      case "hudtime":
        if len(params) != 1:
          self.content = f"Error Invalid hudtime {params} wrong number"
          return self.doshow()
        try:
          s = int(params[0])
        except ValueError:
          self.content = f"Error Invalid hudtime {params} not int"
          return self.doshow()
        s = max(s,5)
        self.hudtime = hudtime*1000
      case "fontsize":
        if len(params) != 1:
          self.content = f"Error Invalid fontsize {params} wrong number"
          return self.doshow()
        try:
          fs = int(params[0])
        except ValueError:
          self.content = f"Error Invalid fontsize {params} not int"
          return self.doshow()
        self.fontsize = clamp(fs,36,120)
        self.font = QFont(self.fontname,self.fontsize)
      case "showlast":
        return self.doshow()
      case "message":
        text = " ".join(map(str,params))
        self.content = text
        return self.doshow()

  def hide(self):
    if self.showing:
      self.showing = False
      super().hide()
    self.timer.stop()

  def test(self):
    timer = QTimer(self)
    self.show("My")
    timer.singleShot(1000, lambda *t: self.show("Xy"))
    self.dtimer.singleShot(KILLTIME,self.finish)

  def finish(self):
    app.quit()
