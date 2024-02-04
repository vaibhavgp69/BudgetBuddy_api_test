from rest_framework import serializers
from .models import *
import uuid
import os
import re
import time
import openai
import requests
import string
import dj_database_url
import json
import ast
from asteval import Interpreter
import ast
from goto import with_goto
from goto import goto, label

import pathlib
import textwrap
import google.generativeai as genai

import PIL.Image

GOOGLE_API_KEY=os.environ.get('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)


aeval = Interpreter()
openai.organization = os.environ.get("ORG_KEY")
openai.api_key =os.environ.get("OPENAI_KEY")


# openai.organization = "org-cRn4NpYi0Ew4VA8lvOsfRIBN"
# openai.api_key =os.environ.get("OPENAI_KEY")


class UserSerializer(serializers.ModelSerializer):
    if_logged = serializers.CharField(required=False, read_only=True)
    status = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = User
        fields = ['username','phonenumber', 'password', 'if_logged', 'status']

    def create(self, data):        
 
        newuser= User.objects.create(
            username = data.get("username"),
            phonenumber = data.get("phonenumber"),
            password = data.get("password"),
            ifLogged = True,
        )

        newuser.save()
        data['status'] = 'User Created Sucessfully'
        return data
    
    
class TransactionSerializer(serializers.ModelSerializer):
    timestamp = serializers.CharField(required=False, read_only=True)
    sender = serializers.CharField(required=False, read_only=True)
    t_type = serializers.CharField(required=False, read_only=True)
    receiver = serializers.CharField(required=False, read_only=True)
    amount = serializers.DecimalField(required=False, read_only=True, max_digits = 100, decimal_places=3)
    receiver_category = serializers.CharField(required=False, read_only=True)
    advice = serializers.CharField(required=False, read_only=True)
    status = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = Transaction
        fields = ['username','all_messages','timestamp', 'sender', 'receiver', 'amount','receiver_category','advice','status','t_type']

    def create(self, data):          
        c_user = User.objects.get(username=data.get('username'))
        all_messages = rf"{data.get('all_messages')}"
        result = ast.literal_eval(all_messages)
        a_m=[]
        for x in result.values():
            a_m.append(x)
        for i in a_m:
            data['timestamp'] = i[0]
            
            
            if Transaction.objects.filter(pk= data['timestamp']).exists():
                print("Data Already Exists , skipping OPENAI api call")
                continue
            else:
                data['t_type'],data['sender'],data['receiver'],data['receiver_category'], data['amount']  = self.get_receiver(i)
                print("------------------------ T I M E R   ---- S T A R T E D ------------------- ")
                time.sleep(20)
                data['advice'] = 'future implementation incoming'
                newtrans= Transaction.objects.create(
                    username = data.get("username"),
                    all_messages = data.get('all_messages'),
                    user=c_user,
                    timestamp = data["timestamp"],
                    sender = data["sender"],
                    amount = data["amount"],
                    receiver = data["receiver"],
                receiver_category = data["receiver_category"],
                advice = data['advice'],
                t_type=data['t_type'],
                )
            
                newtrans.save()
            
            
        data['status'] = "created succesfully"
        return data
    
    def use_regex_amount(self, text):
        amount_pattern = re.compile(r'Rs\. ?(\d+(?:\.\d{1,2})?)')
        match = amount_pattern.search(text)
        amount_spent = match.group(1)
        return amount_spent
    
    @with_goto
    def get_receiver(self, single_message):
        sender=single_message[1]
        notif=single_message[2]
        amount = self.use_regex_amount(notif)
        print(notif)
        message= ""

        t=f""" Given a financial message, process it and categorize the information into the following format:

        {notif}

        "transaction_type": "<debit_or_credit>",
        "receiver": "<receiver>",
        "receiver_category": "<receiver_category>"

        Ensure that the output adheres to the specified structure, with the transaction_type representing the transaction_type of the financial message to a limited set of "Debit" ,"Credit". the receiver indicating the recipient, and the receiver_category denoting a limited set of categories such as 'Entertainment,' 'Food,' 'Medical' 'Individual Person,' or 'Government Utilities' """
        prompt = t

        content=f"""Please give proper JSON format answer"""
        
        label .begin
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[
            {"role": "system", "content": content },
            {"role": "user", "content": prompt}
            ]
        )

        res=completion.choices[0].message
        print(res['content'])
        res['content'] = res['content'].replace("\n", "")
        # print(res['content'])
        try : 
            data_3 = json.loads(res['content'])
            return data_3['transaction_type'].lower(),sender,data_3['receiver'], data_3['receiver_category'],float(amount)
        except json.decoder.JSONDecodeError:
            goto .begin
            
class MicSerializer(serializers.ModelSerializer):
    timestamp = serializers.CharField(required=False, read_only=True)
    sender = serializers.CharField(required=False, read_only=True)
    t_type = serializers.CharField(required=False, read_only=True)
    receiver = serializers.CharField(required=False, read_only=True)
    amount = serializers.DecimalField(required=False, read_only=True, max_digits = 100, decimal_places=3)
    receiver_category = serializers.CharField(required=False, read_only=True)
    advice = serializers.CharField(required=False, read_only=True)
    status = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = Transaction
        fields = ['username','all_messages','timestamp', 'sender', 'receiver', 'amount','receiver_category','advice','status','t_type']

    def create(self, data):          
        c_user = User.objects.get(username=data.get('username'))
        all_messages = rf"{data.get('all_messages')}"
        result = ast.literal_eval(all_messages)
        all_message = result["mic"]
        data['timestamp'] = all_message[0]
        if Transaction.objects.filter(pk= data['timestamp']).exists():
            print("Data Already Exists , skipping OPENAI api call")
        else:
            data['amount'],data['t_type'],data['sender'],data['receiver'],data['receiver_category']   = self.get_mic(all_message[1])
            data['advice'] = 'future implementation incoming'
            newtrans= Transaction.objects.create(
                username = data.get("username"),
                all_messages = data.get('all_messages'),
                user=c_user,
                timestamp = data["timestamp"],
                sender = data["sender"],
                amount = data["amount"],
                receiver = data["receiver"],
            receiver_category = data["receiver_category"],
            advice = data['advice'],
            t_type=data['t_type'],
            )
        
            newtrans.save()
        
        
        data['status'] = "created succesfully"
        return data
    
    
    @with_goto
    def get_mic(self, single_message):

        message= ""

        t=f""" Given a financial message, process it and categorize the information into the following format:

        {single_message}

        "amount": "<amount_spent_decimal_only",
        "transaction_type": "<debit_or_credit>",
        "receiver": "<receiver>",
        "receiver_category": "<receiver_category>"

        Ensure that the output adheres to the specified structure, with the amount , transaction_type representing the transaction_type of the financial message to a limited set of "Debit" ,"Credit". the receiver indicating the recipient, and the receiver_category denoting a limited set of categories such as 'Entertainment,' 'Food,' 'Medical' 'Individual Person,' or 'Government Utilities' """
        prompt = t

        content=f"""Please give proper JSON format answer"""
        
        label .begin
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[
            {"role": "system", "content": content },
            {"role": "user", "content": prompt}
            ]
        )

        res=completion.choices[0].message
        print(res['content'])
        res['content'] = res['content'].replace("\n", "")
        # print(res['content'])
        try : 
            data_3 = json.loads(res['content'])
            return float(data_3['amount']),data_3['transaction_type'].lower(),"Mic",data_3['receiver'], data_3['receiver_category']
        except json.decoder.JSONDecodeError:
            goto .begin
            
class ImgSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(required=False, read_only=True)
    t_type = serializers.CharField(required=False, read_only=True)
    receiver = serializers.CharField(required=False, read_only=True)
    amount = serializers.DecimalField(required=False, read_only=True, max_digits = 100, decimal_places=3)
    receiver_category = serializers.CharField(required=False, read_only=True)
    advice = serializers.CharField(required=False, read_only=True)
    text = serializers.CharField(required=False, read_only=True)
    img_url = serializers.CharField(required=False, read_only=True)
    status = serializers.CharField(required=False, read_only=True)
    class Meta:
        model = Image
        fields = ['username','text','timestamp', 'sender', 'img_file', 'img_url' ,'receiver', 'amount','receiver_category','advice','status','t_type']

    def create(self, data):          
        c_user = User.objects.get(username=data.get('username'))
        data['timestamp'] = data.get('timestamp')
        newimg = Image.objects.create(
            timestamp = data['timestamp'],
            username=data.get("username"),
            user=c_user,
            img_file=data.get("img_file"),
            text="x"
        )
        newimg.save()
        data['img_url']  = newimg.img_file.url
        if Transaction.objects.filter(pk= data['timestamp']).exists():
            print("Data Already Exists , skipping OPENAI api call")
        else:
            data['amount'],data['sender'],data['receiver'],data['receiver_category'],data['t_type'],data['text']   = self.get_img_value(data['img_url'])
            newimg.text=data['text']
            newimg.save()
            data['advice'] = 'future implementation incoming'
            newtrans= Transaction.objects.create(
                username = data.get("username"),
                all_messages = data['text'] ,
                user=c_user,
                timestamp = data["timestamp"],
                sender = data["sender"],
                amount = data["amount"],
                receiver = data["receiver"],
            receiver_category = data["receiver_category"],
            advice = data['advice'],
            t_type=data['t_type'],
            )
        
            newtrans.save()
        
        
        data['status'] = "created succesfully"
        return data
    
    @with_goto    
    def get_img_value(self,url):
        img = PIL.Image.open("."+url) 
        model = genai.GenerativeModel('gemini-pro-vision')
        t="""
        Given an image containing a financial document or receipt, extract and categorize the information into the following format:

        {
            "receiver": "<receiver>",
            "receiver_category": "<receiver_category>",
            "transaction_type": "<debit_or_credit>",
            "amount": "<transaction_amount>"
        }
        Ensure that the output adheres to the specified structure, with the receiver indicating the recipient, receiver_category denoting a limited set of categories
        (e.g., "Entertainment," "Food," "Medical," "Individual Person," or "Government Utilites"), transaction_type indicating whether the transaction was a debit or credit, and amount representing the transaction amount.

        """
        label .begin
        try : 
            response = model.generate_content([t, img], stream=True)
            response.resolve()
            j =response.text
            j=j.replace("```json\n", "")
            j=j.replace("\n", "")
            j_neat=j.replace("```", "")
            text = json.loads(j)
            return float(text['amount']),"By Cash",text['receiver'],text['receiver_category'],text['transaction_type'],j_neat
        
        except json.decoder.JSONDecodeError:
            goto .begin

            
