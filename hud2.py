#!/usr/bin/env python3
import sys
import os
from hud import Hud
from threading import Thread

from PySide6.QtWidgets import QApplication
hudtime = int(os.getenv("HUDTIME",10000))
app = QApplication(sys.argv)
huds = []
n = 4
for i in range(n):
  huds.append( hud:=Hud(100,100,1720,880,2708+i,hudtime) )
  hud.sethue(int(360*i/n))
huds[-1].fontsize = 64
try:
  exit(app.exec())
except KeyboardInterrupt:
  print("Ctrl-C 2")
