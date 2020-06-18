"""
This program enables the communication with the MiR AGV plugin created previously by ARA integration team.

The communication is performed through ads, which is the underlying communication protocol that TwinCAT uses to pass
information in their devices.

This development was performed on the 9th of June, 2020.
Maintainer and creator: Walter Frank Pintor Ortiz, walterpintor@gmail.com
Special thanks to: Yadunund Vijay, yadunund@gmail.com
"""

import pyads
from FM import MIR
import time
import re


# add route to remote plc - Only for Linux systems - Not needed now
# pyads.add_route("192.168.1.100.1.1", "192.168.1.100")

def connect_to_plc():
    try:
        # connect to plc and open connection
        plc = pyads.Connection('192.168.1.100.1.1', pyads.PORT_TC3PLC1)
        plc.open()
        print("Connected to PLC successfully. \n PLC object: ", plc)
        return plc
    except:
        print("Connection to PLC not established.\n Trying again in 5 seconds...")
        time.sleep(5)
        connect_to_plc()


def disconnect_from_plc(plc_object):
    try:
        # write status value to Beckhoff
        plc_object.write_by_name("Variables.bIs_AGV_connected", False, pyads.PLCTYPE_BOOL)
    except:
        print("AGV status not updated. Check connectivity with PLC.")
        pass

    # close connection
    plc_object.close()
    print("AGV status updated in PLC. Disconnected.")


def read_plc_commands(plc_object, mir_object):
    try:
        while True:
            # Reading request command from PLC variable
            plc_cmd = plc_object.read_by_name("Variables.sRequestToAGV", pyads.PLCTYPE_STRING)
            # print(plc_cmd)

            if plc_cmd == "data":
                print(mir_object.get_data())
                data = mir_object.get_data()
                text = str(data)
                subtext1 = "{'orientation':"
                subtext2 = ", 'x':"
                try:
                    orientation_found = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                    if orientation_found is not None:
                        print("Orientation string found: ", orientation_found)
                except:
                    print("No orientation found")
                subtext1 = "'x':"
                subtext2 = ", 'y':"
                try:
                    pos_x_found = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                    if pos_x_found is not None:
                        print("Position in X string found: ", pos_x_found)
                except:
                    print("No position in Y found")

                subtext1 = "'y':"
                subtext2 = "}"
                try:
                    pos_y_found = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                    if pos_y_found is not None:
                        print("Position in Y string found: ", pos_y_found)
                except:
                    print("No position in Y found")

                subtext1 = "'mission_text': '"
                subtext2 = "...',"
                try:
                    has_mission = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                    # print("Mission found: ", has_mission)
                    # print(data)
                except:
                    has_mission = "None"

                if pos_x_found and pos_y_found and orientation_found is not None:
                    plc_object.write_by_name("Variables.arrfAGV_currentPos",
                                             [float(pos_x_found), float(pos_y_found), float(orientation_found)],
                                             pyads.PLCTYPE_ARR_REAL(3))
                    plc_object.write_by_name("Variables.sAGV_hasMission", has_mission, pyads.PLCTYPE_STRING)

            elif plc_cmd == "pause":
                mir.pause()
                plc_object.write_by_name("Variables.sRequestToAGV","idle", pyads.PLCTYPE_STRING)
            elif plc_cmd == "ready":
                mir.ready()
                plc_object.write_by_name("Variables.sRequestToAGV", "idle", pyads.PLCTYPE_STRING)
            elif plc_cmd == "go_to":
                agv_goto_pos = plc_object.read_by_name("Variables.arrfAGV_Pos", pyads.PLCTYPE_ARR_REAL(3))
                mir.move_to(0, agv_goto_pos)
                plc_object.write_by_name("Variables.sRequestToAGV", "idle", pyads.PLCTYPE_STRING)
                print("Robot moving to: ", agv_goto_pos)
            elif plc_cmd == "quit":
                break
            elif plc_cmd == "idle":
                pass
            else:
                print("Invalid option!")

            time.sleep(0.025)

    except KeyboardInterrupt:
        print("Program stopped by user.")
        # write status value to Beckhoff
        plc_object.write_by_name("Variables.bIs_AGV_connected", False, pyads.PLCTYPE_BOOL)
        print("Variables for AGV status updated in PLC. MiR Disconnected.")

    except Exception as e:
        print("Error occurred during selection of command: ", str(e))


def connect_to_mir(plc_object, ip):
    try:
        # Create MiR object(s)
        mir_object = MIR(url="http://"+ip, run_main=False, fleet=False)
        print("Connected to MiR")
    except:
        print("Failed to connect to MiR... \n Retrying in 5 secs...")
        time.sleep(5)
        connect_to_mir(plc_object, ip)
    try:
        # write status value to Beckhoff
        plc_object.write_by_name("Variables.bIs_AGV_connected", True, pyads.PLCTYPE_BOOL)
        print("Variables for AGV status updated in PLC. MiR Connected.")
    except:
        print("Variable for AGV status not updated. Check connectivity with PLC.")
        pass

    return mir_object


if __name__ == "__main__":
    """
    PLC variables to read and write as of today (10th June 2020)
    
    bIs_AGV_connected	AT %I*		: BOOL;
    sAGV_ip_address 	AT %Q*		: STRING;
    sRequestToAGV		AT %Q*		: STRING;
    arrfAGV_Pos			AT %Q*		: ARRAY[1..3] OF REAL;
    bMissionComplete	AT %I*		: BOOL;
    
    
    Adding additional variables (12th June 2020)
    
    arrfAGV_locations	AT %Q*		: ARRAY [1..4] OF WSTRING := ["Locations to go...","Hall","Conveyor","Collection Point"];
    arrfAGV_hall		AT %Q*		: ARRAY [1..3] OF REAL := [29.5, 22.885250091552734,90];
    arrfAGV_conveyor	AT %Q*		: ARRAY [1..3] OF REAL := [27.3, 26.79, 0.0];
    arrfAGV_collection  AT %Q*		: ARRAY [1..3] OF REAL := [29.5, 25.7, -90];
    
    arrfAGV_currentPos	AT %I*		: ARRAY [1..3] OF REAL;   
    
    
    These variables will need to be read and written.
    
    For general purpose information:
    AT %I* indicates input in the PLC side, meaning that we must write from here.
    On the contrary, %Q* indicates and output and we must subscribe to it.
    """

    # Connect to Beckhoff PLC
    plc = connect_to_plc()

    # Reading IP address of robot provided in PLC variables
    # TODO: At this point there is no verification of IP quality. Include it in the future.
    mir_ip = plc.read_by_name("Variables.sAGV_ip_address", pyads.PLCTYPE_STRING)

    # Connect to MiR AGV
    mir = connect_to_mir(plc, mir_ip)

    # Read the commands from PLC
    read_plc_commands(plc, mir)

    # Closing communication with PLC
    disconnect_from_plc(plc)
