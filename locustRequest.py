# The MIT License (MIT)
#
# Copyright (c) Eclypses, Inc.
#
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import sys
from locust import HttpUser, task, between, run_single_user, events
import json
import base64
import urllib.parse
import logging

from MteBase import MteBase
from MtePair import MtePair
from MteStatus import MteStatus

class ApiUser(HttpUser): 
    """Class ApiUser 
        This represents a user that can be spawned from locust.
    """

    @events.init_command_line_parser.add_listener
    def init_parser(parser):
        """Parses any custom arguments that this class may use."""
        parser.add_argument(
            '--test_type'
            )
        parser.add_argument(
            '--mte_type'
            )
        parser.add_argument(
            '--total_pairs'
            )

    logging.basicConfig(filename="errors.log",filemode='a',level = logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger().setLevel(logging.ERROR)
    # Simulate user wait time between tasks.
    wait_time = between(1, 5)
   
    # Initialize MTE license. If a license code is not required (e.g., trial mode), this can be skipped.
    if not MteBase.init_license("LicenseCompany", "LicenseKey"):
        status = MteStatus.mte_status_license_error
        print("this is a test")
        logging.error(f"Encountered an error with license: {status}")
        print("License init error ({0}): {1}.".format(
            MteBase.get_status_name(status),
            MteBase.get_status_description(status)),
            file=sys.stderr)
        sys.exit("License init error.")

    def on_start(self):
        """Initial setup each time a user is created by locust."""
           
        self.one_kb = """Lorem ipsum dolor sit amet, consectetur adipiscing 
           elit, sed do eiusmod tempor incididunt ut labore et dolore magna 
           aliqua. Tincidunt nunc pulvinar sapien et ligula. Feugiat nibh 
           sed pulvinar proin gravida hendrerit lectus a. Metus aliquam 
           eleifend mi in. Erat imperdiet sed euismod nisi porta lorem. 
           Nascetur ridiculus mus mauris vitae ultricies leo. Purus sit amet 
           volutpat consequat mauris nunc. Adipiscing elit duis tristique 
           sollicitudin. Non pulvinar neque laoreet suspendisse interdum 
           consectetur libero id. Diam ut venenatis tellus in metus vulputate 
           eu scelerisque. Leo in vitae turpis  massa sed elementum tempus 
           egestas sed. Sapien eget mi proin sed libero enim sed faucibus 
           turpis. Vitae turpis massa sed elementum. Amet commodo nulla 
           facilisi nullam vehicula. Metus aliquam eleifend mi in nulla 
           posuere. Magna eget est lorem ipsum dolor sit. Pellentesque 
           adipiscing commodo elit at imperdiet dui.\n\nFringilla urna 
           porttitor rhoncus dolor purus non enim praesent elementum. 
           Dictumst quisque"""
           

        # Set test type here or use --test_type command argument.
        if self.environment.parsed_options.test_type != None:
            self.test_type = self.environment.parsed_options.test_type
        
        if not hasattr(self, 'test_type') or self.test_type == None:
            self.test_type = "echo"        

        # type:
        # MTE Core: 0
        # MKE Add-on: 1
        # Set type here or use --mte_type command argument.
        if self.environment.parsed_options.mte_type != None:
            self.mte_type = self.environment.parsed_options.mte_type

        if not hasattr(self, 'mte_type') or self.mte_type == None:
            self.mte_type = 0            
        
        if self.mte_type != None and self.mte_type == 1:
            self.mte_type = 1

        # Check if possily using "mke" for type.
        if isinstance(self.mte_type, str) and (self.mte_type == "1" or self.mte_type.lower() == "mke"):
            self.mte_type = 1  
        
        # Set total number of MTE pairs or use --total_pairs command argument.
        if self.environment.parsed_options.total_pairs != None:
            try:
                self.mte_pair_total = int(self.environment.parsed_options.total_pairs)
            except ValueError:
                print("total_pairs not properly set, using default.")

        if not hasattr(self, 'mte_pair_total') or self.mte_pair_total == None or self.mte_pair_total <= 0:
            self.mte_pair_total = 1

        # Limit the maximum.
        if self.mte_pair_total > 300:
            self.mte_pair_total = 300
        
        # The starting index.
        self.mte_pair_index = 0

         # Create list of MtePair instances.
        self.mte_pair_list = self.add_mte_pairs(self.mte_pair_total)    

    def add_mte_pairs(self, count):
        """Communicates with the MTE server to establish MTE encoder/decoder
            pairs using the MTE kyber implementation."""
        # Perform a HEAD request to get the client_id.
        response = self.client.head("api/mte-relay")

        # Check if client_id has been set.
        if not hasattr(self, 'client_id'):
            self.client_id = response.headers.get('x-mte-relay', 'Header not present')

        # Variable for holding number of failures - used currently to track catastrophic failures.
        self.fail_num = 0       

        # Create local list of MTE pairs.
        mte_pair_list = []

        # Create list to hold each payload.
        payload_list = []

        # Loop to create all needed MTE pairs.
        for i in range(count):
            # Create new MtePair.
            m_pair = MtePair(self.mte_type)

            # Create payload for the "api/mte-pair" call.
            payload = {
                "pairId": m_pair.pair_id,
                "encoderPersonalizationStr": m_pair.enc_personal,
                "encoderPublicKey": base64.b64encode(m_pair.enc_pub_key).decode("utf-8"),
                "decoderPersonalizationStr": m_pair.dec_personal,
                "decoderPublicKey": base64.b64encode(m_pair.dec_pub_key).decode("utf-8")
            }

            # Append to the MTE pair list.
            mte_pair_list.append(m_pair)

            # Append to the payload list.
            payload_list.append(payload)

        # JSON dump the whole payload list.
        payload = json.dumps(payload_list)

        # Create headers for the "api/mte-pair" call.
        headers = {
            'x-mte-relay': self.client_id,
            'Content-Type': 'application/json'
        }

        # Post to "api/mte-pair".
        response = self.client.post("api/mte-pair", headers=headers, data=payload)

        # Check if response is valid.
        if response == None:
            print("Invalid response")
            return None

        # Receive the response back.
        try:
            data = response.json()  
        except json.JSONDecodeError as ex:
            print("Invalid JSON decoding.", ex)
            return None      

        # Loop through each data item received from server.
        for i in range(count):
            # Encoder/Decoder is from the perspective of the server, i.e., decoder from the server will pair up with client encoder.
            encoder_secret = base64.b64decode(data[i]['decoderSecret'])
            encoder_nonce = int(data[i]['decoderNonce'])
            decoder_secret = base64.b64decode(data[i]['encoderSecret'])
            decoder_nonce = int(data[i]['encoderNonce'])
            status = mte_pair_list[i].setup(encoder_nonce, decoder_nonce, encoder_secret, decoder_secret)
            if status != MteStatus.mte_status_success:
                sys.exit("Failed to setup MTE pair: " + str(status))

        # Return local pair list.
        return mte_pair_list                

    def replace_mte_pair(self, mte_pair):   
        """Removes an MTE pair from the list and then adds one."""
        # Remove the MtePair.   
        self.mte_pair_list.remove(mte_pair)              

        # Add new MTE pair.
        mte_list = self.add_mte_pairs(1)
        if mte_list != None and len(mte_list) > 0:
            self.mte_pair_list.extend(mte_list)

        self.increment_mte_pair_list()

    def increment_mte_pair_list(self):
        """Increments the index for the next encoder/decoder use. Rolls the
            index over if it gets past the total number of pairs.
        """
        # Increment index.
        self.mte_pair_index += 1

        # Roll index back to zero if greater or equal to total number of pairs.
        if self.mte_pair_index >= len(self.mte_pair_list):
            self.mte_pair_index = 0

    @task
    def test(self):      
        """The test that locust will call upon at th intervals supplied. This 
            will pick the test based on test_type.
        """
        # If no test_type or not in the list, then use echo.       
        if self.test_type.strip().lower() == "login":
            self.mte_login()
        elif self.test_type.strip().lower() == "patient":
            self.mte_patient()
        elif self.test_type.strip().lower() == "credit":
            self.mte_credit()
        elif self.test_type.strip().lower() == "onekb" or self.test_type.strip().lower() == "1kb":
            self.mte_one_kb()
        elif self.test_type.strip().lower() == "tenkb" or self.test_type.strip().lower() == "10kb":
            self.mte_ten_kb()
        elif self.test_type.strip().lower() == "twentyfivekb" or self.test_type.strip().lower() == "25kb":
            self.mte_twenty_five_kb()
        elif self.test_type.strip().lower() == "fiftykb" or self.test_type.strip().lower() == "50kb":
            self.mte_fifty_kb()
        else:
            self.mte_echo()      

    def mte_echo(self):
        """The basic echo test without any MTE involvment."""
        response = self.client.get("api/mte-echo/test")

        pass
   
    def mte_login(self):
        """Performs the login test with a "valid" user and password that will
            be encoded and then sent to the server.
        """
        # Create payload to deliver with the post.
        login_payload = {
            'email': "trevor.blackman@eclypses.com",
            'password': "P@ssw0rd!"
        }
       
        (status, response) = self.encode_and_send_message(name="login", header_type=None, payload=login_payload, query_string=None, method=None)
                      
        pass

    def mte_patient(self):
        """Performs a patient test with a basic search pattern to send to the
        server. No payload given."""

        (status, response) = self.encode_and_send_message(name="patients", header_type='text/plain; charset=utf-8', payload=None, query_string="?search=Test", method="get")

        pass

    
    def mte_credit(self):
        """Performs the credit card test with a credit card sample to encode
        and send to the server."""

        # Create payload to deliver with the post.
        credit_payload = {
            'creditCardNumber': "6489-6201-3912-5555",
            'creditCardCVV': "958",
            'creditCardIssuer': "visa",
            'pin': "6524",
            'name': "Trevor J Blackman",
            'address': "1234 Elm Street",
            'city': "Springfield",
            'state': "IL",
            'zip': "62701",
        }

        (status, response) = self.encode_and_send_message(name="credit-card", header_type=None, payload=credit_payload, query_string=None, method=None)

        pass

    def mte_one_kb(self):
        """Performs the one kb test with the placeholder text."""
        payload = {
            'data': self.one_kb,
        }

        (status, response) = self.encode_and_send_message(name="echo", header_type=None, payload=payload, query_string=None, method=None)
        
        pass

    def mte_ten_kb(self):
        """Performs the ten kb test with the placeholder text."""

        payload = {
            'data': self.one_kb * 10,
        }

        (status, response) = self.encode_and_send_message(name="echo", header_type=None, payload=payload, query_string=None, method=None)
                
        pass

    def mte_twenty_five_kb(self):
        """Performs the 25 kb test with the placeholder text."""

        payload = {
            'data': self.one_kb * 25,
        }
        
        (status, response) = self.encode_and_send_message(name="echo", header_type=None, payload=payload, query_string=None, method=None)
        pass

    def mte_fifty_kb(self):
        """Performs the 50 kb test with the placeholder text."""

        payload = {
            'data': self.one_kb * 50,
        }
        
        (status, response) = self.encode_and_send_message(name="echo", header_type=None, payload=payload, query_string=None, method=None)
        pass

    def encode_and_send_message(self, name, header_type, payload, query_string, method):
        """Using the next available MTE pair, this will encode the url, header,
            and payload (if using one) to send to the MTE server relay. """
        successful = False # Check if there were successful encodings and responses from the server.
        limit = 5 # The number of attempts before giving up.
        attempts = 0

        while successful == False and attempts < limit:
            # Get the MTE pair based off current index.
            mte_pair = self.mte_pair_list[self.mte_pair_index]     
        
            # Start with api for the url and the base_url.
            url = "api/" + name
            base_url = "/" + url

            # Check if there is a query string, attach this to url.
            if query_string:
                url += query_string

            encoded_url = ""
            # Encode the api path with MTE base64 for use in api post request path.
            (encoded_url, status) = mte_pair.encode_b64(url)

            # Check if base 64 encoding was successful.
            if status != MteStatus.mte_status_success:
                print("Failed to encode the url.")
                self.replace_mte_pair(mte_pair)
                continue

            # Create header to be encoded based on header_type.
            if not header_type:
                header_type = 'application/json'

            header = {
                'Content-Type': header_type,
            }

            # Stringify the header to be MTE encoded.
            header_string = json.dumps(header)

            (encoded_header, status) = mte_pair.encode_b64(header_string)
            # Check if base 64 encoding was successful.
            if status != MteStatus.mte_status_success:
                print("Failed to encode the header.")
                self.replace_mte_pair(mte_pair)
                continue

            # Below is the format needed in the header "x-mte-relay":
            # client_id
            # pair_id
            # MTE or MKE: 0 = MTE, 1 = MKE
            # isUrlEncoded: 0 false, 1 true,
            # isHeaders Encoded: 0 false, 1 true,
            # is Body encoded: 0 false, 1 true
            mte_header_info = self.client_id + ',' + mte_pair.pair_id + "," + str(self.mte_type) + ",1,1,"

            # Check if there is a payload. Append appropriate header info.            
            encoded_payload = None
            if payload:
                mte_header_info += "1"
                content_type = "application/octet-stream"
                # Stringify the payload for encoding.
                payload_string = json.dumps(payload)

                # Encode the payload with MTE for use in api post data variable.
                (encoded_payload, status) = mte_pair.encode(payload_string)

                # Check if encoding was successful.
                if status != MteStatus.mte_status_success:
                    print("Failed to encode the payload")
                    self.replace_mte_pair(mte_pair)
                    continue
            else:
                mte_header_info += "0"
                content_type = "application/json; charset=utf-8"

            # Create request header that will include the base 64 encoded header info.
            # Determine content based on type.
            headers = {
                    'Content-Type': content_type,
                    'x-mte-relay': mte_header_info,
                    'x-mte-relay-eh': encoded_header,
                    'Content-Length': str(len(encoded_payload))
            }         

            # Parse URL to change unprintable characters that would confuse the system.
            parsed_url = urllib.parse.quote(encoded_url)

            # Send the post request to server.
            # Check method type. If more method types, expand here.
            if str(method) == "get":
                response = self.client.get(parsed_url, name=base_url, headers=headers, data=encoded_payload)
            else:
                response = self.client.post(parsed_url, name=base_url, headers=headers, data=encoded_payload)

            # Check if response was successful.
            if response == None:
                print("this was an error, no response")
                self.replace_mte_pair(mte_pair)  
            elif response.status_code != 200:
                print("this was an error, code: ", str(response.status_code))
                self.replace_mte_pair(mte_pair)  
            else:
                successful = True              

            attempts += 1

        if successful:
            # Increment pair list.
            self.increment_mte_pair_list()

            # Return status and response.
            return (status, response)
        
        else:
            # Return failure.
            print("was never able to get response")
            return (-1, None)

# if launched directly, e.g. "python3 locustRequest.py", not "locust -f locustRequest.py"
if __name__ == "#__main__":
    run_single_user(ApiUser)
