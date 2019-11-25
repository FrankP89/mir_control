# -*- coding: utf-8 -*-
"""
@author: Yadunund Vijay, yadunund@gmail.com

Class definitions for 
    1. creating objects to connect to MIR and Husky AGVs
    2. Send commands to receive position, set goals and pause/stop/resume operations

"""

import json
import threading
import time 
from enum import Enum
from datetime import datetime
#import numpy as np
import requests
from requests.exceptions import HTTPError
import logging
import sys

logging.basicConfig(filename='FM.log', format='%(asctime)s %(message)s', filemode='w', level=logging.INFO)

class MIR:
  def __init__(self, url="http://192.168.12.241", authorization="",timeout=5,rate=0.5,fleet=True,run_main=False,mission="move"):
    
    self.url=url
    self.headers={'Authorization':authorization,'Accept-Language':'en-US','Content-Type': 'application/json'}
    if(self.headers['Authorization']=='' or self.headers['Authorization']==None):
            self.headers['Authorization']="Basic YWRtaW46NzkzNWUyZGJkYzExMWZkYjhkOTExNjFjMzI3Y2UxNDhhMTRkZDc5MGUxM2Q1MWE5ZjFhMTk3ZTA0M2VhN2QwZg=="
    self.message_body={}
    self.response={}
    self.timeout=timeout
    self.rate=rate
    self.fleet=fleet
    
    self.mission=mission
    
    self.url=self.url+'/api/v2.0.0'
    self.run_main=run_main

    
    
    self.send_json=''
    self.receive_json=''
    self.send_dict={}
    self.receive_dict={}
    
    self.initialized=False
    self.isbusy=False
    
    self.robot_count=0
    self.fleet_info=[]
    self.robot_data=[]
    self.robot_positions=[]
    
    self.initialize()
    self.start_thread=threading.Thread(target=self.main)
    self.start_thread.start()


  def isconnected(self):
     try:
            response=requests.get(self.url,timeout=self.timeout,headers=self.headers)
            response.raise_for_status()
     except HTTPError as http_err:
                print("HTTP error occurred:"+str(http_err))
                logging.info("HTTP error occurred:"+str(http_err))
                return False
     except Exception as err:
                print("Other error occurred:"+str(err))
                logging.info("Other error occurred:"+str(err))
                return False
     else:
                print("Successfully connected with MIR")
                logging.info("Successfully connected with MIR")
                return True
    
  def initialize(self): 
      if(self.isconnected()):
          if(self.fleet):
              self.get_fleet_info()
          else:
              self.robot_count=1
              self.robot_data.append({})
          self.initialized=True
          self.get_data()
      else:
        print("Initialization failed. Please reinitialize with correct parameters")
        logging.info("Initialization failed. Please reinitialize with correct parameters")
  
  def get_fleet_info(self):
        try:   
            url=self.url+ "/robots"
            response=requests.get(url,headers=self.headers,timeout=self.timeout)
            response.raise_for_status()
        except HTTPError as http_err:
                print("HTTP error occurred:"+str(http_err))
                logging.info("HTTP error occurred:"+str(http_err))
                return False
        except Exception as err:
                print("Other error occurred:"+str(err))
                logging.info("Other error occurred:"+str(err))
                return False
        else:
                self.fleet_info=response.json()
                self.robot_count=len(self.fleet_info)
                for i in range(self.robot_count):
                    self.robot_data.append({})
                print("Found "+ str(self.robot_count)+" robots in the fleet with details:\n"+str(self.fleet_info))
                logging.info("Found "+ str(self.robot_count)+" robots in the fleet with details:\n"+str(self.fleet_info))

  def _get_data(self,index):
                #print("Getting data for robot: "+str(index))
                logging.info("Getting data for robot: "+str(index))
                if(self.fleet):
                    robot=self.fleet_info[index]
                    url=self.url+'/robots/'+ str(robot['id'])
                else:
                    url=self.url+'/status'
                try:
                    response=requests.get(url,headers=self.headers,timeout=self.timeout)
                    response.raise_for_status()
                except HTTPError as http_err:
                    print("HTTP error occurred:"+str(http_err))
                    logging.info("HTTP error occurred:"+str(http_err))
                    return False
                except Exception as err:
                    print("Other error occurred:"+str(err))
                    logging.info("Other error occurred:"+str(err))
                    return False
                else:
                    self.robot_data[index]=response.json()
                    #print("Data successfuly retrieved")
                    logging.info("Data successfuly retrieved for robot:" +str(index))
                
  def get_data(self,index=-1):
        if(self.initialized):
            if(index<0 or index>self.robot_count-1):
                #print("Index out of range. Getting all available data")
                logging.info("Index out of range. Getting all available data")
                for i in range(self.robot_count):
                    self._get_data(i)            
            else:
                self._get_data(index)
        return self.robot_data
                   
  def _display_position(self,index):
    robot_data=self.robot_data[index]
    if(self.fleet):
        position=robot_data['status']['position']
    else:
        position=robot_data['position']
    position['x']=round(position['x'],3)
    position['y']=round(position['y'],3)
    position['orientation']=round(position['orientation'],3)
    print("Positon of Robot:"+str(index))
    print(position)
    
  def display_position(self,index=-1):
            if(self.initialized):
                if(index<0 or index>self.robot_count-1):
                    for i in range(self.robot_count):
                        self._display_position(i)            
                else:
                    self._display_position(index)
    

  def set_pose(self):
      return 0

  def _put(self,url,data):
        print("Connecting to channel:"+url)
        try:
            response=requests.put(url,headers=self.headers,timeout=self.timeout,json=data)
            logging.info(str(response.json()))
            print(str(response.json()))
            response.raise_for_status()
        except HTTPError as http_err:
            print("HTTP error occurred:"+str(http_err))
            logging.info("HTTP error occurred:"+str(http_err))
            return False
        except Exception as err:
            print("Other error occurred:"+str(err))
            logging.info("Other error occurred:"+str(err))
            return False
        else:
            return(response)
            
  def _post(self,url,data):
    print("Connecting to channel:"+url)
    try:
        response=requests.post(url,headers=self.headers,timeout=self.timeout,json=data)
        logging.info(str(response.json()))
        print(str(response.json()))
        response.raise_for_status()
    except HTTPError as http_err:
        print("HTTP error occurred:"+str(http_err))
        logging.info("HTTP error occurred:"+str(http_err))
        return False
    except Exception as err:
        print("Other error occurred:"+str(err))
        logging.info("Other error occurred:"+str(err))
        return False
    else:
        return(response)
        
            
  def _delete(self,url):
      logging.info("Sending Delete command to url:"+url)
      print("Sending Delete command to url:"+url)
      try:
          response=requests.delete(url,headers=self.headers)
          response.raise_for_status()
      except HTTPError as http_err:
        print("HTTP error occurred:"+str(http_err))
        logging.info("HTTP error occurred:"+str(http_err))
        return False
      except Exception as err:
        print("Other error occurred:"+str(err))
        logging.info("Other error occurred:"+str(err))
        return False
      else:
        return(response)
        
  def reset_queue(self,index):
      if(self.fleet):
          robot=self.robot_data[index]
          url='http://'+ robot['ip']+'/api/v2.0.0/mission_queue'
      else:
          url=self.url+'/mission_queue'
          
      response=self._delete(url)
      if(response):
          print("Mission Queue successfully reset. Robot is paused")
      
  def _pause(self,index):
        logging.info("Pausing robot: "+str(index))
        if(self.fleet):
            robot=self.robot_data[index]
            url='http://'+ robot['ip']+'/api/v2.0.0/status'
        else:
            url=self.url+'/status'
        data={'state_id':4}
        response=self._put(url,data)
        if(response):
            #print("Data successfuly retrieved")
            print("Robot:" +str(index)+" successfully paused")
            logging.info("Robot:" +str(index)+" successfully paused")
    
  def pause(self,index=-1):
    if(self.initialized):
            if(index<0 or index>self.robot_count-1):
                #print("Index out of range. Getting all available data")
                logging.info("Index out of range. Getting all available data")
                for i in range(self.robot_count):
                    self._pause(i)            
            else:
                self._pause(index)
                
  def _ready(self,index):
        logging.info("Readying robot: "+str(index))
        if(self.fleet):
            robot=self.robot_data[index]
            url='http://'+ robot['ip']+'/api/v2.0.0/status'
        else:
            url=self.url+'/status'
        data={'state_id':3}
        response=self._put(url,data)
        if(response):
            #print("Data successfuly retrieved")
            print("Robot:" +str(index)+" successfully readied")
            logging.info("Robot:" +str(index)+" successfully readied")
            
  def ready(self,index=-1):
    if(self.initialized):
            if(index<0 or index>self.robot_count-1):
                #print("Index out of range. Getting all available data")
                logging.info("Index out of range. Getting all available data")
                for i in range(self.robot_count):
                    self._ready(i)            
            else:
                self._ready(index)

  def add_mission(self,index,ID):
      data={"mission_id": ID}
      if(self.fleet):
          robot=self.robot_data[index]
          url='http://'+ robot['ip']+'/api/v2.0.0/mission_queue'
      else:
          url=self.url+'/mission_queue'
      response=self._post(url,data)
      if(response):
          print("Mission successfully added")
      

  def move_to(self,index,pose) :
    #pose is an array containing [x,y,orientation]
    if(self.fleet):
        robot=self.robot_data[index]
        url='http://'+ robot['ip']+'/api/v2.0.0/missions'
    else:
        url=self.url+'/missions'
    mission_guid=""
    action_guid=""
    pos_guid=""
    pos_flag=False
    
    try:
        self.pause(index)
        self.reset_queue(index)
        data= {'orientation':pose[2],'pos_x':pose[0],'pos_y':pose[1]}
        response=self._get(url)
        if(response):
            for mission in response.json():
                #find the active mission guid
                if(mission['name']==self.mission):
                    #print(mission)
                    mission_guid=mission['guid']
                    url=url+"/"+mission_guid+"/actions"
                    #find the action guid containing move command
                    action_response=self._get(url)
                    if(action_response):
                        for action in action_response.json():
                            if(action['action_type']=='move'):
                                #get guid of positon inside move command
                                #print(action)
                                action_guid=action['guid']
                                for parameter in action['parameters']:
                                    if(parameter['id']=='position'):
                                        #print(parameter)
                                        pos_guid=parameter['value']
                                        if(self.fleet):
                                            modify_pos_url='http://'+ robot['ip']+'/api/v2.0.0/positions/' +pos_guid
                                        else:
                                             modify_pos_url=self.url+'/positions/' +pos_guid
                                        pos_response=self._put(modify_pos_url,data)
                                        if(pos_response):
                                            print('Mission position successfully modified!')
                                            pos_flag=True
                          
        if(pos_flag):
            self.add_mission(index,mission_guid)
            self.ready(index)
        else:
            print("Error updating position in Mission")
    except Exception as e:
        print(str(e))
        
            
        
  def _get(self,url):
        try:
            response=requests.get(url,headers=self.headers,timeout=self.timeout)
            response.raise_for_status()
        except HTTPError as http_err:
            print("HTTP error occurred:"+str(http_err))
            logging.info("HTTP error occurred:"+str(http_err))
            return False
        except Exception as err:
            print("Other error occurred:"+str(err))
            logging.info("Other error occurred:"+str(err))
            return False
        else:
            return response

                                    
  def main(self):
        while True:
            if self.initialized and self.run_main:
                try:
                    time.sleep(1/self.rate)
                    print("Timestamp:"+str(datetime.now()))
                    self.get_data()
                    self.display_position()
                except Exception as err_main:
                    print("Main Error:"+str(err_main))
            else:
                    break

  def terminate(self):
        self.run_main = False


                        
