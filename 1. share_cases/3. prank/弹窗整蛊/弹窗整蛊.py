import win32api,win32con

while True:
    ret=win32api.MessageBox(0, "试试你能关掉么", "你中招了",win32con.MB_OKCANCEL)
    if ret==1:
        win32api.MessageBox(0, "确认也关不掉吧", "你中招了", win32con.MB_OKCANCEL)
    elif ret==2:
        win32api.MessageBox(0, "再来一次", "你中招了", win32con.MB_OKCANCEL)

