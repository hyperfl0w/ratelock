# -*- coding: utf-8 -*-
import boto3   
from boto3.dynamodb.conditions import Key, Attr
import sys

# Get the service resource.
table_to_create = 'authdb'

import zipfile
import StringIO

class InMemoryZip(object):
    def __init__(self):
        # Create the in-memory file-like object
        self.in_memory_zip = StringIO.StringIO()

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of 
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0        

        return self

    def read(self):
        '''Returns a string with the contents of the in-memory zip.'''
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def writetofile(self, filename):
        '''Writes the in-memory zip to a file.'''
        f = file(filename, "w")
        f.write(self.read())
        f.close()

class AuthDB(object):
    def __init__(self, dbname):
        self.dbname = dbname
        self.resource = boto3.resource('dynamodb')
        self.client   = boto3.client('dynamodb')
        self.table = None

    def start(self):
        table_exists = False
        try:
          tabledescription = self.client.describe_table(TableName=self.dbname)
          table_exists = True
        except Exception as e:  
           if "Requested resource not found: Table" in str(e):
              self.table = self.resource.create_table(
                  TableName            =table_to_create,
                  KeySchema            =[{'AttributeName': 'username'   ,'KeyType': 'HASH' }, 
                                        ],
                  AttributeDefinitions =[{'AttributeName': 'username','AttributeType': 'S' },
                                        ],
                  ProvisionedThroughput={'ReadCapacityUnits': 5,'WriteCapacityUnits': 5}
              )
        
              self.table.meta.client.get_waiter('table_exists').wait(TableName=self.dbname)
              table_exists = True
           else:
             raise
        self.table = self.resource.Table(self.dbname)
        

    def delete(self):
       try: self.client.delete_table(TableName=self.dbname)
       except: raise
        
    def do_scrypt_XXXSTUBXXX(self, password):
        # scrypt goes here, to be executed as close as possible to the actual write,
        # but not implemented twice.
        # XXX kept out for demo/dependency purposes
        return password
    
    def add(self, username, password):
       if not self.table: self.start()
       print username, password
       try:
           self.table.update_item(Key={'username':username},
                            UpdateExpression="SET password = :password",                   
                            ExpressionAttributeValues={':password': self.do_scrypt_XXXSTUBXXX(password)})
           return True
       except Exception as e:
           print e.args
           return False
            
    
    def check(self, username, password):
       if not self.table: self.start()
       response = self.table.query(KeyConditionExpression=Key('username').eq(username))
       if response[u'Count'] == 1 and response['Items'][0]['password']==self.do_scrypt_XXXSTUBXXX(password):
           return True
       else:
           return False

if __name__ == "__main__":
   db = AuthDB("authdb")

   verb = sys.argv[1]
   if verb == "delete":
       print db.delete()
       sys.exit(0)
       
   verb, username, password = sys.argv[1:4]

   if verb == "add":   print db.add(username, password)
   if verb == "check": print db.check(username, password)
   if verb == "dump":  print "just because I don't exist, doesn't mean I don't have the permissions to"

def handler(event, context):
    verb, username, password = (event.get('verb'), event.get('username'), event.get('password'))
    db = AuthDB("authdb")
    if verb == "add":   return db.add(username, password)
    if verb == "check": return db.check(username, password)
