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

def clamp(x,a,b):
  return max(min(x,b),a)

HUDTIME=300000
KILLTIME=4000
class Hud(QWidget):
  def handleUdp(self):
    try:
      while self.udpSocket.hasPendingDatagrams():
        datagram = self.udpSocket.receiveDatagram(4096)
        data = datagram.data().data()
        self.process_data(data.decode())
    except KeyboardInterrupt:
      QApplication.instance().quit()

  def process_data(self,data):
    text = data[:256]
    self.show(text)

  def mousePressEvent(self,e):
    self.hide()
    super().mousePressEvent(e)

  def __init__(self,x,y,w,h,port=2708,hudtime=HUDTIME):
    super().__init__()

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

  
  def show(self,x):
    self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    self.setAttribute(Qt.WA_TranslucentBackground)
    x = x[:256]
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print(f"[{now}] HUD Show: {x}")
    self.showSmall = False
    if x.strip() == "@quit":
      return QCoreApplication.quit()
    elif x.strip() == "@help":
      self.content = control_messages
      self.showSmall = True
    elif x.strip() == "@hide":
      return self.hide()
    elif x.strip().startswith("@hudcolorh "):
      try:
        h = x.split(" ")[1]
        self.color = QColor(h)
      except ValueError:
        self.content = "Error, invalid: "+x
    elif x.strip().startswith("@hudhue "):
      try:
        h = x.split(" ")[1]
        h = int(h)
        self.sethue(h)
      except ValueError:
        self.content = "Error, invalid: "+x
    elif x.strip().startswith("@hudcolorf "):
      try:
        r,g,b = [clamp(int(255.9*float(y)),0,255) for y in x.split(" ")]
        self.color = QColor(r,g,b)
      except ValueError:
        self.content = "Error, invalid: "+x
    elif x.strip().startswith("@hudcolor "):
      try:
        r,g,b = [clamp(int(y),0,255) for y in x.split(" ")]
        self.color = QColor(r,g,b)
      except ValueError:
        self.content = "Error, invalid: "+x
        pass
    elif x.strip().startswith("@hudtime "):
      try:
        r,s = x.split(" ")
        hudtime = int(s)
        self.hudtime = hudtime*1000
      except ValueError:
        self.content = "Error, invalid: "+x
        pass
    elif x.strip().startswith("@fontsize "):
      try:
        r,s = x.split(" ")
        fs = int(s)
        self.fontsize = clamp(fs,36,120)
        self.font = QFont(self.fontname,self.fontsize)
      except ValueError:
        self.content = "Error, invalid: "+x
        pass
    elif not x.strip().startswith("@showlast"):
      self.content = x
    if not self.showing:
      super().show()
      self.showing = True
      self.timer.stop()
    self.update()
    self.timer.singleShot(self.hudtime,self.hide)

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
