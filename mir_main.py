# -*- coding: utf-8 -*-
"""

@author: Yadunund Vijay, yadunund@gmail.com
@contributor: Walter Pintor, walterpintor@gmail.com
"""

from FM import MIR
import time


def display_menu():
    print("----------------------")
    print("1.Get Current Data\n2.Pause")
    print("3.Resume\n4.Move To")
    print("5.Exit")
    print("----------------------")
    
if __name__=="__main__":
    # mir=MIR(url='http://192.168.12.20',run_main=False,fleet=False)
    mir=MIR(url='http://192.168.1.20',run_main=False,fleet=False)
    try:
        while True:
            display_menu()
            arg=int(input("Enter Option Number:"))
            if(arg==1):
                print(mir.get_data())
            elif(arg==2):
                mir.pause()
            elif(arg==3):
                mir.ready()
            elif(arg==4):
               _val=input("Enter x,y,ori:")
               val=[float(x) for x in _val.split(",")]
               mir.move_to(0,val)
            elif(arg==5):
               break 
               #exit(0) 
	      # mir.pause()		
            else:
               print("Invalid Option!")
               break
            time.sleep(0.01)
    except Exception as e:
        print(str(e))
                
    
