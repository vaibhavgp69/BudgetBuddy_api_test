from rest_framework import serializers
from .models import *
import uuid
import os
import re
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
aeval = Interpreter()



openai.organization = "org-cRn4NpYi0Ew4VA8lvOsfRIBN"
openai.api_key =os.environ.get("OPENAI_KEY")


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
    amount = serializers.DecimalField(required=False, read_only=True, max_digits = 10, decimal_places=3)
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
            res = x.strip('][').split(', ')
            a_m.append(res)
        for i in a_m:
            g=f"{i}"
            print(type(g))
            print(g)
            single_message = g.strip('][').split(',')
            data['timestamp'] = single_message[0]
            
            
            if Transaction.objects.filter(pk= data['timestamp']).exists():
                print("Data Already Exists , skipping OPENAI api call")
                continue
            else:
                data['t_type'],data['sender'],data['receiver'],data['receiver_category'], data['amount']  = self.get_receiver(g)
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
        single_message = single_message.strip('][').split(',')
        timestamp = single_message[0]
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

        Ensure that the output adheres to the specified structure, with the timestamp representing the transaction_type of the financial message to a limited set of "Debit" ,"Credit". the receiver indicating the recipient, and the receiver_category denoting a limited set of categories such as 'Entertainment,' 'Food,' 'Medical' or 'Individual Person.' """
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
        except json.decoder.JSONDecodeError:
            goto .begin
            
            
        return data_3['transaction_type'].lower(),sender,data_3['receiver'], data_3['receiver_category'],float(amount)