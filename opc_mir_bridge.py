"""
This variation of code enables the communication with the MiR AGV plugin and the SMG 5G server.

The communication is performed through OPC-UA. For this proposed architecture, the NUC will be the opc_client.

This development was performed on the 18th of June, 2020.
Maintainer and creator: Walter Frank Pintor Ortiz, walterpintor@gmail.com
Maintainer: Lim GuoWei, nnn@xxx.com
"""

from opcua import Client, ua
from FM import MIR
import time
import re
import platform
import subprocess

"""
 Due to the nature of the API, we can't overload it with many requests at the same time.
 OPC-UA needs to define what information is cascading down to perform which actions.
 For instance, if the AMR needs to move to a different location, the following actions should occur:
    * reading_flag has to be false
    * writing_flag to turn true
    * A ready request has to be sent from server
    * A ready request has to be posted to MiR
    * A move_to request has to be sent from server with the parameters
    * A move_to request has to be posted to MiR with the parameters
    * writing_flag has to return to false
    * reading_flag goes back up
"""


###############################################################################

# Priority variables #
writing_flag = False
reading_flag = True

# Variables #

# MiR #
set_send_action_to_AMR = ""

set_AMR_e_stop = False
set_AMR_pos = []
set_pause_AMR = False
set_ready_AMR = True

get_AMR_status = False
get_battery_life = 0.0
get_AMR_pos = []
get_AMR_imu = [], []
get_AMR_odom = [], []


##############################################################################
########## Connect function ##################################################
##############################################################################

# Pinging function to check if AGV is there #
def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    Answer provided in: https://stackoverflow.com/questions/2953462/pinging-servers-in-python and
    adapated to Windows.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    check = subprocess.Popen(["ping.exe", host], stdout=subprocess.PIPE).communicate()[0]

    if 'unreachable' in str(check):
        return 0
    else:
        return subprocess.call(command) == 0

################################
### Connect OPC-UA functions ###
################################

# Connect to OPC server #
def connect_to_opc_server(ip, port):
    # Valid pattern for accepting IP addresses
    valid_pattern = r"((^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$)|(^[a-zA-Z\.]+[a-zA-Z\.]+[a-zA-Z]$))"
    if re.match(valid_pattern, ip):
        print("Connecting to OPC-UA server in " + ip + " ...")
        url = 'opc.tcp://' + str(ip) + ':' + str(port)
        client = Client(url)
        # client.set_user("user1")
        # client.set_password("pw1")
        # client.set_security_string("Basic256Sha256,SignAndEncrypt,certificate-example.der,private-key-example.pem")
        client.connect()
        print("Connected!")
        return client
    else:
        print("Error!", "Incorrect IP address/Domain!")
        client = None
    return client


# Disconnect from OPC server #
def disconnect_from_opc_server(client):
    if client is not None:
        print(client)
        client.disconnect()

        print("Process has been stopped...")
        print("Disconnected")

        return True
    else:
        print("Nothing to stop...")
        return False

###############################
#### Connect MiR functions ####
###############################

def connect_to_mir(ip):
    if ping(ip):
        try:
            # Create MiR object(s)
            mir_object = MIR(url="http://" + ip, run_main=False, fleet=False)
            print("Connected to MiR")
        except:
            print("Failed to connect to REST API... \n Retrying in 5 secs...")
            time.sleep(5)
            connect_to_mir(ip)
        try:
            # write status value to OPC-UA server
            print("Variables for AGV status updated in OPC-UA server. MiR Connected.")
        except:
            print("Variable for AGV status not updated. Check connectivity with OPC-UA server.")
            pass
    else:
        print("Failed to connect to the provided MiR IP... \n Retrying in 20 secs...")
        time.sleep(20)
        connect_to_mir(ip)

    return mir_object

###############################################################################
########## End of connect functions #################
###############################################################################


###############################################################################
##########Capture and set Robot Variables########################
###############################################################################

def read_opc_commands(opc_client, mir):
    try:
        while True:
            # Reading request command from PLC variable
            ua_info_get_update(True)

            if set_send_action_to_AMR == "data":
                print(mir.get_data())
                data = mir.get_data()
                text = str(data)
                subtext1 = "{'orientation':"
                subtext2 = ", 'x':"
                try:
                    orientation_found = text[text.index(subtext1) + len(subtext1):text.index(subtext2)]
                except:
                    print("No orientation found")
                subtext1 = "'x':"
                subtext2 = ", 'y':"
                try:
                    pos_x_found = text[text.index(subtext1) + len(subtext1):text.index(subtext2)]
                except:
                    print("No position in Y found")

                subtext1 = "'y':"
                subtext2 = "}"
                try:
                    pos_y_found = text[text.index(subtext1) + len(subtext1):text.index(subtext2)]
                except:
                    print("No position in Y found")

                subtext1 = "'mission_text': '"
                subtext2 = "...',"
                try:
                    has_mission = text[text.index(subtext1) + len(subtext1):text.index(subtext2)]
                except:
                    has_mission = "None"

                if (orientation_found is not None) and (pos_x_found is not None) \
                        and (pos_y_found is not None) and (has_mission is not None):
                    get_AMR_pos[0] = float(pos_x_found)
                    get_AMR_pos[1] = float(pos_y_found)
                    get_AMR_pos[2] = float(orientation_found)

                time.sleep(0.25)

                # Return to non-reading, non-writing state
                writing_flag = False
                reading_flag = False

                # Update OPC UA #
                ua_info_set_update(True)

            elif set_send_action_to_AMR == "pause":
                mir.pause()
                set_send_action_to_AMR = "idle"
            elif set_send_action_to_AMR == "ready":
                mir.ready()
                set_send_action_to_AMR = "idle"
            elif set_send_action_to_AMR == "go_to":
                agv_goto_pos = set_AMR_pos
                mir.move_to(0, agv_goto_pos)
                set_send_action_to_AMR = "idle"
                print("Robot moving to: ", agv_goto_pos)
            elif set_send_action_to_AMR == "idle":
                pass
            else:
                print("Invalid option!")
                pass

            time.sleep(0.025)

    except KeyboardInterrupt:
        print("Program stopped by user.")
        # write status value to Beckhoff
        print("Variables for AGV status updated in PLC. MiR Disconnected.")

    except Exception as e:
        print("Error occurred during selection of command: ", str(e))

###############################################################################
##########End of Capture and set Robot Variables#################
###############################################################################


###############################################################################
##########UA information update#################
###############################################################################

def ua_info_set_update(ready):
    """
        Sets the updates coming from the MiR to the OPC-Server
    """

    if (ready):
        # Robot target variables for OPC-UA
        # Get info for set_send_data
        opc_set_send_action_to_AMR = opc_client.get_node("ns=4;s=MiRVariables.sSet_send_action_to_AMR")

        # Robot and sensor get data
        opc_get_AMR_status = opc_client.get_node("ns=4;s=MiRVariables.bGet_AMR_status")

        opc_get_AMR_battery_life = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_battery_life")
        opc_get_AMR_pos_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_pos_x")
        opc_get_AMR_pos_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_pos_y")
        opc_get_AMR_pos_theta = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_pos_theta")

        opc_get_AMR_imu_orient_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_orient_x")
        opc_get_AMR_imu_orient_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_orient_y")
        opc_get_AMR_imu_orient_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_orient_z")
        opc_get_AMR_imu_orient_w = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_orient_w")

        opc_get_AMR_imu_ang_vel_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_ang_vel_x")
        opc_get_AMR_imu_ang_vel_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_ang_vel_y")
        opc_get_AMR_imu_ang_vel_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_ang_vel_z")

        opc_get_AMR_imu_lin_acc_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_lin_acc_x")
        opc_get_AMR_imu_lin_acc_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_lin_acc_y")
        opc_get_AMR_imu_lin_acc_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_imu_lin_acc_z")

        opc_get_AMR_odom_pose_lin_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_odom_pose_lin_x")
        opc_get_AMR_odom_pose_lin_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_odom_pose_lin_y")
        opc_get_AMR_odom_pose_lin_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_odom_pose_lin_z")

        opc_get_AMR_odom_twist_orien_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_odom_twist_orien_x")
        opc_get_AMR_odom_twist_orien_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_odom_twist_orien_y")
        opc_get_AMR_odom_twist_ang_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AMR_odom_twist_ang_z")

        # Set Robot variables 
        dv = ua.DataValue(ua.Variant(set_send_action_to_AMR, ua.VariantType.String))
        opc_set_send_action_to_AMR.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_status, ua.VariantType.Boolean))
        opc_get_AMR_status.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_battery_life, ua.VariantType.Float))
        opc_get_AMR_battery_life.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AMR_pos[0], ua.VariantType.Float))
        opc_get_AMR_pos_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_pos[1], ua.VariantType.Float))
        opc_get_AMR_pos_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_pos[2], ua.VariantType.Float))
        opc_get_AMR_pos_theta.set_value(dv)

        # IMU data - orient(X-Y-Z-W), angvel(rX,rY,rZ), linacc(X,Y,Z)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[0][0], ua.VariantType.Float))
        opc_get_AMR_imu_orient_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[0][1], ua.VariantType.Float))
        opc_get_AMR_imu_orient_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[0][2], ua.VariantType.Float))
        opc_get_AMR_imu_orient_z.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[0][3], ua.VariantType.Float))
        opc_get_AMR_imu_orient_w.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AMR_imu[1][0], ua.VariantType.Float))
        opc_get_AMR_imu_ang_vel_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[1][1], ua.VariantType.Float))
        opc_get_AMR_imu_ang_vel_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[1][2], ua.VariantType.Float))
        opc_get_AMR_imu_ang_vel_z.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AMR_imu[2][0], ua.VariantType.Float))
        opc_get_AMR_imu_lin_acc_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[2][1], ua.VariantType.Float))
        opc_get_AMR_imu_lin_acc_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_imu[2][2], ua.VariantType.Float))
        opc_get_AMR_imu_lin_acc_z.set_value(dv)

        # IMU data - Odom, linear(X-Y-Z), orient(X,Y,Z,W)
        dv = ua.DataValue(ua.Variant(get_AMR_odom[0][0], ua.VariantType.Float))
        opc_get_AMR_odom_pose_lin_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_odom[0][1], ua.VariantType.Float))
        opc_get_AMR_odom_pose_lin_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_odom[0][2], ua.VariantType.Float))
        opc_get_AMR_odom_pose_lin_z.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AMR_odom[1][0], ua.VariantType.Float))
        opc_get_AMR_odom_twist_orien_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_odom[1][1], ua.VariantType.Float))
        opc_get_AMR_odom_twist_orien_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AMR_odom[1][2], ua.VariantType.Float))
        opc_get_AMR_odom_twist_ang_z.set_value(dv)

        # dv = ua.DataValue(ua.Variant(get_AMR_odom[1][3], ua.VariantType.Float))


def ua_info_get_update(ready):
    """
        Gets the updates and requests from the OPC-UA server
    """

    if ready:

        # Robot set data
        opc_set_action_to_AMR = opc_client.get_node("ns=4;s=MiRVariables.sSet_action_to_AMR")
        set_send_action_to_AMR = opc_set_action_to_AMR.get_value()

        if (set_send_action_to_AMR != "data"):
            writing_flag = True
            reading_flag = False

        opc_set_AMR_e_stop = opc_client.get_node("ns=4;s=MiRVariables.bSet_AMR_e_stop")
        set_AMR_e_stop = opc_set_AMR_e_stop.get_value()
        opc_set_AMR_pos_x = opc_client.get_node("ns=4;s=MiRVariables.fSet_AMR_pos_x")
        set_AMR_pos[0] = opc_set_AMR_pos_x.get_value()
        opc_set_AMR_pos_y = opc_client.get_node("ns=4;s=MiRVariables.fSet_AMR_pos_y")
        set_AMR_pos[1] = opc_set_AMR_pos_y.get_value()
        opc_set_AMR_pos_theta = opc_client.get_node("ns=4;s=MiRVariables.fSet_AMR_pos_theta")
        set_AMR_pos[2] = opc_set_AMR_pos_theta.get_value()

        opc_set_pause_AMR = opc_client.get_node("ns=4;s=MiRVariables.bSet_pause_AMR")
        opc_set_pause_AMR.get_value()
        opc_set_ready_AMR = opc_client.get_node("ns=4;s=MiRVariables.bSet_ready_AMR")
        opc_set_ready_AMR.get_value()

###############################################################################
##########End of UA information update#################
###############################################################################


if __name__ == "__main__":
    """
        This program connects to an OPC-UA server, retrieves information from the server,
        retrieves information from the MiR and continuously writes/reads it.
    """

    """
    Variables to read and write as of today (21st July 2020)

    bIs_AMR_connected	AT %I*		: BOOL;
    sAGV_ip_address 	AT %Q*		: STRING;
    sRequestToAGV		AT %Q*		: STRING;
    arrfAGV_Pos			AT %Q*		: ARRAY[1..3] OF REAL;
    bMissionComplete	AT %I*		: BOOL;


    Adding additional variables (12th June 2020)


    These variables will need to be read and written.

    For general purpose information:
    AT %I* indicates input in the OPC-UA server side, meaning that we must write from here.
    On the contrary, %Q* indicates and output and we must subscribe to it.
    """

    # Connect to OPC-UA server
    try:
        ip_opc_server_address = "192.168.1.200"
        opc_port_server_no = 40880
        opc_client = connect_to_opc_server(ip=ip_opc_server_address, port=opc_port_server_no)
    except:
        # Closing communication with OPC-UA server
        disconnect_from_opc_server(opc_client)

    # Connect to MiR AMR
    mir_ip = "192.168.1.20"
    mir_port = 520
    mir = connect_to_mir(ip=mir_ip)

    # Connect to MiR AGV
    mir = connect_to_mir(mir_ip)

    # Read the commands from OPC-UA server
    read_opc_commands(opc_client, mir)

    # Closing communication with OPC-UA server
    disconnect_from_opc_server(opc_client)
