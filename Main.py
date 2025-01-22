from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicroPhoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicroPhoneStatus,
    GetAssistantStatus,)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecoginition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'''{Username} : Hello I am {Assistantname}, How are you?
{Assistantname}: Welcom {Username}. I am your personal assistant. How can I assist you today?'''

subprocessess = []
Functions = ["open", "close", "system", "play", "google search","youtube search", "content"]
def ShowDefaultChatIfNoChats():
    File = open(r'Data\ChatLog.json',"r",encoding="utf-8")
    if len(File.read())<5:
        with open(TempDirectoryPath('Database.data'),'w',encoding="utf-8") as file:
            file.write("")
        
        with open(TempDirectoryPath('Responses.data'),'w',encoding="utf-8") as file:
            file.write(DefaultMessage)
            
def ReadChatLogJson():
    with open(r'Data\ChatLog.json', "r", encoding="utf-8") as file:
        chatlog_data = json.load(file)
    return chatlog_data

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_cahtlog = ""
    for entry in json_data:
        if entry['role'] == "user":
            formatted_cahtlog += f"User: {entry['content']}\n"
        elif entry['role'] == "assistant":
            formatted_cahtlog += f"Assistant: {entry['content']}\n"
    formatted_cahtlog = formatted_cahtlog.replace("User",Username + " ")
    formatted_cahtlog = formatted_cahtlog.replace("Assistant",Assistantname + " ")
    
    with open(TempDirectoryPath('Database.data'),'w',encoding="utf-8") as file:
        file.write(AnswerModifier(formatted_cahtlog))
        
def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'),"r",encoding="utf-8")
    Data = File.read()
    if len(str(Data))>0:
        lines = Data.split("\n")
        result = "\n".join(lines)
        File.close()
        File = open(TempDirectoryPath('Responses.data'),"w",encoding="utf-8")
        File.write(result)
        File.close()
        
def InitialExecution():
    SetMicroPhoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
InitialExecution()

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery= ""
    
    SetAssistantStatus("Listening...........")
    Query = SpeechRecoginition()
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Processing.........")
    Decision = FirstLayerDMM(Query)
    
    print("")
    print(f"Decision: {Decision}")
    print("")
    
    G = any([i for i in Decision if i.startswith("general")])
    R = any([i for i in Decision if i.startswith("realtime")])
    print(f"General {G}, Real Time {R}")
    
    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )
    
    for quires in Decision:
        if "generate" in quires:
            ImageGenerationQuery = str(quires)
            ImageExecution = True
            
    for quires in Decision:
        if TaskExecution == False:
            if any (quires.startswith(func) for func in Functions):
                run(Automation(list(Decision)))
                TaskExecution = True
                
    if ImageExecution == True:
        
        with open(r"Frontend\Files\ImageGeneration.data","w") as file:
            file.write(f"{ImageGenerationQuery},True")
            
        try:
            p1 = subprocess.Popen(["python", r"Backend\ImageGeneration.py"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE, shell=False)
            subprocessess.append(p1)
        
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")
            
    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True
    else:
        for Queries in Decision:
            if "general" in Queries:
                SetAssistantStatus("Processing...")
                QueryFinal = Queries.replace("general", "")
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Ready...")
                TextToSpeech(Answer)
                return True
            elif "realtime" in Queries:
                SetAssistantStatus("Searching.........")
                QueryFinal = Queries.replace("realtime", "")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering...")
                TextToSpeech(Answer)
                return True
            elif "exit" in Queries:
                QueryFinal = "Okay, Bye!"
                Answer = ChatBot(QueryModifier(QueryFinal))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Ready...")
                TextToSpeech(Answer)
                SetAssistantStatus("Offline")
                os._exit(1)
                

def FirstThread():
    while True:
        CurrentStatus = GetMicroPhoneStatus()
        
        if CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            
            if "Available..." in AIStatus:
                sleep(0.1)
                
            else:
                SetAssistantStatus("Available...")

def SecondThread():
    GraphicalUserInterface()
    

if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
        
        
            
    