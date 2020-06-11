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
        print("Connection not established.\n Trying again in 5 seconds...")
        time.sleep(5)
        connect_to_plc()


def disconnect_from_plc(plc_object):
    # close connection
    plc_object.close()
    try:
        # write status value to Beckhoff
        plc_object.write_by_name("Variables.bIs_AGV_connected", False, pyads.PLCTYPE_BOOL)
        print("AGV status updated in PLC. Disconnected.")
    except:
        print("AGV status not updated. Check connectivity with PLC.")
        pass


def read_plc_commands(plc_object, mir_object):
    try:
        while True:
            # Reading request command from PLC variable
            plc_cmd = plc_object.read_by_name("Variables.sRequestToAGV", pyads.PLCTYPE_STRING)
            # print(plc_cmd)

            if plc_cmd == "data":
                print(mir_object.get_data())
            elif plc_cmd == "pause":
                mir.pause()
            elif plc_cmd == "ready":
                mir.ready()
            elif plc_cmd == "go_to":
                agv_goto_pos = plc_object.read_by_name("Variables.arrfAGV_Pos", pyads.PLCTYPE_ARR_REAL(3))
                mir.move_to(0, agv_goto_pos)
                print("Robot moving to: ", agv_goto_pos)
            elif plc_cmd == "quit":
                break
            elif plc_cmd == "idle":
                pass
            else:
                print("Invalid option!")

            time.sleep(0.025)

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
        print("AGV status updated in PLC. Connected.")
    except:
        print("AGV status not updated. Check connectivity with PLC.")
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
