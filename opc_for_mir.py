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



class BackgroundTask():

    def __init__(self, taskFuncPointer):
        __taskFuncPointer_ = taskFuncPointer
        __workerThread_ = None
        __isRunning_ = False

    def taskFuncPointer(self): return __taskFuncPointer_

    def isRunning(self):
        return __isRunning_ and __workerThread_.isAlive()

    def start(self):
        if not __isRunning_ :
            __isRunning_ = True
            __workerThread_ = WorkerThread(self)
            __workerThread_.start()

    def stop(self): __isRunning_ = False

    class WorkerThread(threading.Thread):
        def __init__(self, bgTask):
            threading.Thread.__init__( self )
            __bgTask_ = bgTask

        def run(self):
            try:
                __bgTask_.taskFuncPointer()(__bgTask_.isRunning)
            except Exception as e: print(repr(e))
            __bgTask_.stop()

"""

 Due to the nature of the API, we can't overload it with many requests at the same time.
 OPC-UA needs to define what information is cascading down to perform what actions.
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
# Priority variables #
writing_flag = False
reading_flag = True

# Variables #

# MiR #
set_send_action_to_AGV = ""

set_AGV_e_stop = False
set_AGV_pos = []
set_pause_AGV = False
set_ready_AGV = True

get_AGV_status = False
get_battery_life = 0.0
get_AGV_pos = []
get_AGV_imu = [][]
get_AGV_odom = [][]

##############################################################################
########## Connect function ##################################################
##############################################################################


# Connect to OPC server #
try:    
    ip_server_address = "192.168.1.200"
    port_server_no = 40880
    opc_client = connect_to_opc_server(ip=ip_server_address, port=port_server_no)
except:
    # Closing communication with PLC
    disconnect_from_opc_server(opc_client)
#########################


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


def connect_to_mir(ip):
    try:
        # Create MiR object(s)
        mir_object = MIR(url="http://"+ip, run_main=False, fleet=False)
        print("Connected to MiR")
    except:
        print("Failed to connect to MiR... \n Retrying in 5 secs...")
        time.sleep(5)
        connect_to_mir(ip)

    return mir_object

###############################################################################
########## End of connect functions #################
###############################################################################



###############################################################################
##########Capture and set Robot Variables########################
###############################################################################

def get_info_constantly_from_MiR(robot, isRunningFunc=None):
    i = 0
    #for i in range(1, 50):
    while 1:
        i = i + 1
        print("Attempt # :", i)

        try:
            if not isRunningFunc():
                ua_info_set_update(False)
        except: pass


        try:
            while reading_flag is True and writing_flag is not True:
                
                print(robot.get_data())
                data = robot.get_data()
                text = str(data)
                subtext1 = "{'orientation':"
                subtext2 = ", 'x':"
                try:
                    orientation_found = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                except:
                    print("No orientation found")
                subtext1 = "'x':"
                subtext2 = ", 'y':"
                try:
                    pos_x_found = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                except:
                    print("No position in Y found")

                subtext1 = "'y':"
                subtext2 = "}"
                try:
                    pos_y_found = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                except:
                    print("No position in Y found")

                subtext1 = "'mission_text': '"
                subtext2 = "...',"
                try:
                    has_mission = text[text.index(subtext1)+len(subtext1):text.index(subtext2)]
                except:
                    has_mission = "None"  


                if (orientation_found is not None) and (pos_x_found is not None)
                       and (pos_y_found is not None) and (has_mission is not None):
                       get_AGV_pos[0] = float(pos_x_found)
                       get_AGV_pos[1] = float(pos_y_found)
                       get_AGV_pos[2] = float(orientation_found)
                       


                time.sleep(0.025)

                # Update OPC UA #
                ua_info_set_update(True)

        except KeyboardInterrupt:
            print("Program stopped by user.")
            # write status value to OPC Server            
            print("Variables for AGV status updated in PLC. MiR Disconnected.")

        except Exception as e:
            print("Error occurred during selection of command: ", str(e))

def set_info_to_MiR(robot, isRunningFunc=None):
    i = 0
    #for i in range(1, 50):
    while 1:
        i = i + 1
        print("Attempt # :", i)

        try:
            if not isRunningFunc():
                ua_info_get_update(False)
        except: pass


        try:
            while reading_flag is not True and writing_flag is True:
                # Update OPC UA #
                ua_info_get_update(True)
                
                if set_send_action_to_AGV == "pause":
                    mir.pause()
                    set_send_action_to_AGV = "idle"
                elif set_send_action_to_AGV == "ready":
                    mir.ready()
                    set_send_action_to_AGV = "idle"
                elif set_send_action_to_AGV == "go_to":                    
                    agv_goto_pos = set_AGV_pos                    
                    mir.move_to(0, agv_goto_pos)
                    set_send_action_to_AGV = "idle")
                    print("Robot moving to: ", agv_goto_pos)
                elif set_send_action_to_AGV == "quit":
                    break
                elif set_send_action_to_AGV == "idle":
                    pass
                else:
                    print("Invalid option!")
                
                # Return to normal state
                writing_flag = False
                reading_flag = True

                time.sleep(0.025)

                
        except KeyboardInterrupt:
            print("Program stopped by user.")
            # write status value to OPC Server            
            print("Variables for AGV status updated in PLC. MiR Disconnected.")

        except Exception as e:
            print("Error occurred during selection of command: ", str(e))

        time.sleep(0.025)

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
        opc_set_send_action_to_AGV = opc_client.get_node("ns=4;s=MiRVariables.bSet_send_action_to_AGV")

        # Robot and sensor get data
        opc_get_AGV_status = opc_client.get_node("ns=4;s=MiRVariables.bGet_AGV_status")

        opc_get_AGV_battery_life = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_battery_life")
        opc_get_AGV_pos_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_pos_x")
        opc_get_AGV_pos_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_pos_y")
        opc_get_AGV_pos_theta = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_pos_theta")

        opc_get_AGV_imu_orient_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_orient_x")
        opc_get_AGV_imu_orient_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_orient_y")
        opc_get_AGV_imu_orient_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_orient_z")
        opc_get_AGV_imu_orient_w = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_orient_w")

        opc_get_AGV_imu_ang_vel_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_ang_vel_x")
        opc_get_AGV_imu_ang_vel_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_ang_vel_y")
        opc_get_AGV_imu_ang_vel_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_ang_vel_z")

        opc_get_AGV_imu_lin_acc_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_lin_acc_x")
        opc_get_AGV_imu_lin_acc_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_lin_acc_y")
        opc_get_AGV_imu_lin_acc_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_imu_lin_acc_z")
        
        opc_get_AGV_odom_pose_lin_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_odom_pose_lin_x")
        opc_get_AGV_odom_pose_lin_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_odom_pose_lin_y")
        opc_get_AGV_odom_pose_lin_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_odom_pose_lin_z")

        opc_get_AGV_odom_twist_orien_x = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_odom_twist_orien_x")
        opc_get_AGV_odom_twist_orien_y = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_odom_twist_orien_y")
        opc_get_AGV_odom_twist_ang_z = opc_client.get_node("ns=4;s=MiRVariables.fGet_AGV_odom_twist_ang_z")       

        
        # Set Robot variables 
        dv = ua.DataValue(ua.Variant(set_send_action_to_AGV, ua.VariantType.String))
        opc_set_send_action_to_AGV.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_status, ua.VariantType.Boolean))
        opc_get_AGV_status.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_battery_life, ua.VariantType.Float))
        opc_get_AGV_battery_life.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AGV_pos[0], ua.VariantType.Float))
        opc_get_AGV_pos_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_pos[1], ua.VariantType.Float))
        opc_get_AGV_pos_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_pos[2], ua.VariantType.Float))
        opc_get_AGV_pos_theta.set_value(dv)

        # IMU data - orient(X-Y-Z-W), angvel(rX,rY,rZ), linacc(X,Y,Z)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[0][0], ua.VariantType.Float))
        opc_get_AGV_imu_orient_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[0][1], ua.VariantType.Float))
        opc_get_AGV_imu_orient_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[0][2], ua.VariantType.Float))
        opc_get_AGV_imu_orient_z.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[0][3], ua.VariantType.Float))
        opc_get_AGV_imu_orient_w.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AGV_imu[1][0], ua.VariantType.Float))
        opc_get_AGV_imu_ang_vel_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[1][1], ua.VariantType.Float))
        opc_get_AGV_imu_ang_vel_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[1][2], ua.VariantType.Float))
        opc_get_AGV_imu_ang_vel_z.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AGV_imu[2][0], ua.VariantType.Float))
        opc_get_AGV_imu_lin_acc_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[2][1], ua.VariantType.Float))
        opc_get_AGV_imu_lin_acc_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_imu[2][2], ua.VariantType.Float))
        opc_get_AGV_imu_lin_acc_z.set_value(dv)
        

        # IMU data - Odom, linear(X-Y-Z), orient(X,Y,Z,W)
        dv = ua.DataValue(ua.Variant(get_AGV_odom[0][0], ua.VariantType.Float))
        opc_get_AGV_odom_pose_lin_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_odom[0][1], ua.VariantType.Float))
        opc_get_AGV_odom_pose_lin_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_odom[0][2], ua.VariantType.Float))
        opc_get_AGV_odom_pose_lin_z.set_value(dv)

        dv = ua.DataValue(ua.Variant(get_AGV_odom[1][0], ua.VariantType.Float))
        opc_get_AGV_odom_twist_orien_x.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_odom[1][1], ua.VariantType.Float))
        opc_get_AGV_odom_twist_orien_y.set_value(dv)
        dv = ua.DataValue(ua.Variant(get_AGV_odom[1][2], ua.VariantType.Float))
        opc_get_AGV_odom_twist_ang_z.set_value(dv)


        #dv = ua.DataValue(ua.Variant(get_AGV_odom[1][3], ua.VariantType.Float))

def ua_info_get_update(ready):

    """
        Gets the updates and requests from the OPC-UA server
    """

    if (ready):

        # Robot set data
        opc_set_action_to_AGV = opc_client.get_node("ns=4;s=MiRVariables.bSet_action_to_AGV")
        set_send_action_to_AGV = opc_set_action_to_AGV.get_value()

        if (set_send_action_to_AGV != "data"):
            writing_flag = True
            reading_flag = False

        opc_set_AGV_e_stop = opc_client.get_node("ns=4;s=MiRVariables.bSet_AGV_e_stop")
        set_AGV_e_stop = opc_set_AGV_e_stop.get_value()
        opc_set_AGV_pos_x = opc_client.get_node("ns=4;s=MiRVariables.fSet_AGV_pos_x")
        set_AGV_pos[0] = opc_set_AGV_pos_x.get_value()
        opc_set_AGV_pos_y = opc_client.get_node("ns=4;s=MiRVariables.fSet_AGV_pos_y")
        set_AGV_pos[1] = opc_set_AGV_pos_y.get_value()
        opc_set_AGV_pos_theta = opc_client.get_node("ns=4;s=MiRVariables.fSet_AGV_pos_theta")
        set_AGV_pos[2] = opc_set_AGV_pos_theta.get_value()

        opc_set_pause_AGV = opc_client.get_node("ns=4;s=MiRVariables.bSet_pause_AGV")
        opc_set_pause_AGV.get_value()
        opc_set_ready_AGV = opc_client.get_node("ns=4;s=MiRVariables.bSet_ready_AGV")
        opc_set_ready_AGV.get_value()
        # opc_set_ctrl_option_AGV = opc_client.get_node("ns=4;s=MiRVariables.nSet_ctrl_option_AGV")

###############################################################################
##########End of UA information update#################
###############################################################################




if __name__ == "__main__":
    """
        This program connects to an OPC-UA server, retrieves information from the server,
        retrieves information from the MiR and continuously writes/reads it.
    """

    # Connect to MiR AMR
    mir_ip = "192.168.0.20"
    mir_port = 520    
    mir = connect_to_mir(ip=mir_ip)

    # Reads robot information from MiR and sends to OPC-UA server
    bgTaskMiRread = BackgroundTask(get_info_constantly_from_MiR(robot=mir))

    # Write robot information to MiR from OPC-UA server
    bgTaskMiRwrite = BackgroundTask(set_info_to_MiR(robot=mir))

    




