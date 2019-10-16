from tkinter import Tk,Label,YES,BOTH
from PIL import Image, ImageTk


import win32api,win32con

image_path='1.jpg'
top = Tk()  # 导入tk模块
top.attributes("-fullscreen", True)
width = top.winfo_screenwidth()
height = top.winfo_screenheight()
print(width, height)
ret=win32api.MessageBox(0, "请问你准备好了么？", "系统提示",win32con.MB_OKCANCEL)
image = Image.open(image_path)
photo = ImageTk.PhotoImage(image.resize((width, height)))
label = Label(top)
label.pack(expand=YES, fill=BOTH)  # 让图像在中央填充
label.configure(image=photo)
top.mainloop()
