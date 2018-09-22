from tkinter import filedialog
from tkinter import *
from tkinter.ttk import Treeview, Style
import os
import platform
from ModClass import *
from math import floor, ceil

#Build a list of index 
def GetIndexes(w, item, ListInd = []):
    ListInd.insert(0, w.index(item))
    if w.parent(item)!='':
        ListInd = GetIndexes(w, w.parent(item), ListInd)
    return ListInd

#Build a list of all offsets present in the file
def GetOffsets(content, ListInd, ListOff = []):
    ListOff.append(content[ListInd[0]*4]+content[ListInd[0]*4+1]*256+content[ListInd[0]*4+2]*(256**2)+content[ListInd[0]*4+3]*(256**3))
    del ListInd[0]
    if len(ListInd)!=0:
        ListOff = GetOffsets(content[ListOff[-1]:], ListInd, ListOff)
    return ListOff

#Correct all offsets to match to the modifications in text
def ChangeAllOffsets(content, Diff, ListOff):
    OffFirst = content[0]+content[1]*256+content[2]*(256**2)+content[3]*(256**3)
    Max = OffFirst//4+1
    if OffFirst%4==0:
        Max -= 1
    indexOff = -1
    if Max<len(content):
        for i in range(Max):
            Offset = content[i*4]+content[i*4+1]*256+content[i*4+2]*(256**2)+content[i*4+3]*(256**3)
            if Offset>ListOff[0]:
                Offset+=Diff
                content = content[:i*4]+bytes([Offset%256, (Offset//256)%256, (Offset//(256**2))%256, (Offset//(256**3))%256])+content[i*4+4:]
            if len(ListOff)>0:
                if Offset==ListOff[0]:
                    indexOff = Offset
    if indexOff!=-1:
        content = content[:indexOff]+ChangeAllOffsets(content[indexOff:], Diff, ListOff[1:])
    return content

#Save file
def Save():
    global content
    FileName = filedialog.asksaveasfilename(title="Save file",filetypes=[('Data files','.dat'), ('All files','.*')])
    if FileName != "" and FileName != None:
        with open(FileName, 'wb') as fichier:
            fichier.write(content)
            fichier.close()

#Open file
def Open():
    global content
    FileName = filedialog.askopenfilename(title="Open file",filetypes=[('Data files','.dat'), ('All files','.*')])
    if FileName != "" and FileName != None:
        contentBackup = content
        TreeVal.delete(*TreeVal.get_children())
        EntryVal.delete(0, END)
        try:
            with open(FileName, 'rb') as fichier:
                content = fichier.read()
                fichier.close()
        except:
                content = contentBackup
        if len(content)>=4:
            Ret = GenTree(TreeVal, content)
            if Ret=="Error":
                content = b"\x04\x00\x00\x00\x20\x20\xff\x0a"

#Change value in EntryVal for the one selected in TreeVal.
def onSelect(evt):
    global content
    w = evt.widget
    Text = w.item(w.selection(), "text")
    try:
        
        EntryVal.delete(0, END)
        EntryVal.insert(0, Text)
        EntryVal.focus()
        EntryVal.icursor(END)
    except:pass

#Change value of Debug each time you click in the debug button.
def checkDbg():
    global Debug
    if Debug:
        Debug = False
    else:
        Debug = True

#Change text in the file
def Change():
    global content, Debug
    ListOff = GetOffsets(content, GetIndexes(TreeVal, TreeVal.selection()), [])
    SumOff = sum(ListOff)
    SumOff+=2
    LastCont = content[SumOff:].split(b'\xff\x0a')[0]
    PreCont = GetCode("\n".join(EntryVal.get().split("|NL|")))
    Diff = len(PreCont)-len(LastCont)
    content = ChangeAllOffsets(content, Diff, ListOff)
    content = content[:SumOff]+PreCont+content[SumOff+len(LastCont):]
    if Debug:
        TreeVal.delete(*TreeVal.get_children())
        GenTree(TreeVal, content)
        if Ret=="Error":
            content = b"\x04\x00\x00\x00\x20\x20\xff\x0a"
    else:
        TreeVal.item(TreeVal.selection(), text=EntryVal.get())

#Check if a part of the file contains sub-offsets for other parts or data
def IsDecomposable(content):
    try:
        OffFirst = content[0]+content[1]*256+content[2]*(256**2)+content[3]*(256**3)
        Max = OffFirst//4+1
        if OffFirst%4==0:
            Max -= 1
        if Max<len(content):
            return True
        else:
            return False
    except:return None

#Build the Treeview from content in the file
def GenTree(Widget, content, parent="", column = 0):
    try:
        OffFirst = content[0]+content[1]*256+content[2]*(256**2)+content[3]*(256**3)
        Max = OffFirst//4+1
        if OffFirst%4==0:
            Max -= 1
        if Max<len(content):
            for i in range(Max):
                Offset = content[i*4]+content[i*4+1]*256+content[i*4+2]*(256**2)+content[i*4+3]*(256**3)
                ID = IsDecomposable(content[Offset:])
                if ID==None:pass
                elif ID:
                    Index = Widget.insert(parent, END, text = str(i))
                    Ret = GenTree(Widget, content[Offset:], Index)
                    if Ret=="Error":
                        return "Error"
                else:
                    Text = "|NL|".join(GetSel(content[Offset+2:].split(b'\xff\x0a')[0]).split("\n"))
                    Index = Widget.insert(parent, END, text = Text)
        return "OK"
    except:
        Widget.delete(*Widget.get_children())
        Widget.insert("", END, text="Error ! File could not be loaded.")
        return "Error"
        

content = ""

fen = Tk()
fen.geometry("450x600")
fen.title("Nazo Nazo Q Editor")
fen.resizable(width=True, height=True)

Label(text = "Tree", font="arial 10").pack(side=TOP, fill=X)

FrameChk = Frame()
FrameChk.pack(side=BOTTOM, fill=X)

FrameBtn = Frame()
FrameBtn.pack(side=BOTTOM, fill=X)

EntryVal = Entry(font="arial 10")
EntryVal.pack(side=BOTTOM, fill=BOTH, expand = 1)

Label(text = "Modify object", font="arial 10").pack(side=BOTTOM, fill=X)

ScrollY = Scrollbar(orient=VERTICAL)
ScrollY.pack(side=RIGHT, fill=Y)

FrameList = Frame()
FrameList.pack(fill=BOTH)

StyleTree = Style()
StyleTree.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Arial', 10))
StyleTree.configure("mystyle.Treeview.Heading", font=('Arial', 10))
StyleTree.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
TreeVal = Treeview(height = 50, selectmode="browse", style="mystyle.Treeview")
TreeVal.pack(side=TOP, fill=BOTH, expand = 1)
TreeVal.bind('<<TreeviewSelect>>', onSelect)

ButtonAdd = Button(FrameBtn, text="Edit", command=Change, font="arial 10")
ButtonAdd.pack(side=LEFT, fill=BOTH, expand = 1)
ButtonOpen = Button(FrameBtn, text="Open", command=Open, font="arial 10")
ButtonOpen.pack(side=LEFT, fill=BOTH, expand = 1)
ButtonSave = Button(FrameBtn, text="Save", command=Save, font="arial 10")
ButtonSave.pack(side=LEFT, fill=BOTH, expand = 1)
ChkDebug = Checkbutton(FrameChk, text="Debug Mode", command=checkDbg, font="arial 10", bd=0)
ChkDebug.pack(side=LEFT, fill=BOTH, expand = 1)
Debug = False

ScrollY.config(command=TreeVal.yview)
TreeVal.config(yscrollcommand=ScrollY.set)

fen.mainloop()
