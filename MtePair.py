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
import base64
import sys

from MteBase import MteBase
from MteEnc import MteEnc
from MteDec import MteDec
from MteMkeEnc import MteMkeEnc
from MteMkeDec import MteMkeDec
from MteStatus import MteStatus
import MteKyber
from MteRandom import MteRandom

class MtePair():
    """Class MteEnc

        This is the MTE Pair.

        Each of these will keep track of an MTE encoder state and an MTE 
        decoder state. These should each be matched up to another device/entity
        that will have a matching encoder/decoder.

        Upon init, MTE personalization strings will be created, along with 
        initial kyber setup. The type will determine if it will use the core
        MTE, or use the MKE add-on.

        Setup will require the necessary kyber and MTE initial information to 
        be properly passed in. Every encoding or decoding operation will restore
        and save the respective state.
    """
    def __init__(self, type):
       
        rand = MteRandom()
        self.enc_personal = base64.b64encode(rand.get_bytes(36)).decode("utf-8")
        self.dec_personal = base64.b64encode(rand.get_bytes(36)).decode("utf-8")
        self.enc_nonce = 0
        self.dec_nonce = 0
        self.enc_pub_key = ""
        self.dec_pub_key = ""
        
        # Create "pair_id"(s) for sending to the server to create encoder/decoder.
        self.pair_id = base64.b64encode(rand.get_bytes(36)).decode("utf-8")   

        # Set type of this class.
        if type == 1:
            self.type = 1
        else:
            self.type = 0   

        # Create initial encoder/decoder states.
        self.encoder_state = []
        self.decoder_state = []

        # Create kyber instances
        self.enc_kyber = MteKyber.MteKyber()
        self.dec_kyber = MteKyber.MteKyber()
        self.enc_kyber.init(512)
        self.dec_kyber.init(512)

        # Set entropy for kyber instances.
        kyber_entropy_size = self.enc_kyber.get_min_entropy_size()
        self.enc_kyber.set_entropy(rand.get_bytes(kyber_entropy_size))
        self.dec_kyber.set_entropy(rand.get_bytes(kyber_entropy_size))

        # Create keypairs for kyber.
        self.enc_pub_key = bytearray(self.enc_kyber.get_public_key_size())
        self.dec_pub_key = bytearray(self.dec_kyber.get_public_key_size())
        kyber_status = self.enc_kyber.create_keypair(self.enc_pub_key)
        if kyber_status != MteKyber.Success:
            raise Exception("Failed to create encoder public key: " + str(kyber_status))
        kyber_status = self.dec_kyber.create_keypair(self.dec_pub_key)
        if kyber_status != MteKyber.Success:
            raise Exception("Failed to create decoder public key: " + str(kyber_status))

    def setup(self, enc_nonce, dec_nonce, enc_encrypted_secret, dec_encrypted_secret):
        """Requires the nonces and kyber encrypted secrets from their counterpart
           device. 
        """
        # Decrypt secrets.
        enc_secret = bytearray(self.enc_kyber.get_secret_size())
        kyber_status = self.enc_kyber.decrypt_secret(enc_encrypted_secret, enc_secret)
        if kyber_status != MteKyber.Success:
           print("Failed to decrypt encoder kyber secret!")
           return kyber_status

        dec_secret = bytearray(self.dec_kyber.get_secret_size())
        kyber_status = self.dec_kyber.decrypt_secret(dec_encrypted_secret, dec_secret)
        if kyber_status != MteKyber.Success:
           print("Failed to decrypt decoder kyber secret!")
           return kyber_status

        # Create encoder.
        encoder = MteEnc.fromdefault()
        encoder.set_entropy(enc_secret)
        encoder.set_nonce(enc_nonce)
        status = encoder.instantiate(self.enc_personal)
        if status != MteStatus.mte_status_success:
            print("Failed to instantiate encoder!")
            return status
        
        # Save encoder state.
        self.encoder_state = encoder.save_state()
        del encoder

        # Create decoder.        
        decoder = MteDec.fromdefault()
        decoder.set_entropy(dec_secret)
        decoder.set_nonce(dec_nonce)
        status = decoder.instantiate(self.dec_personal)
        if status != MteStatus.mte_status_success:
            print("Failed to instantiate decoder!")
            return status
        
        # Save decoder state.
        self.decoder_state = decoder.save_state()
        del decoder
        
        # Success.
        return MteStatus.mte_status_success

    def encode(self, message):  
        """Encodes the given message. This will first restore the previous
            encoder state. The message will then be encoded. Following a
            successful outcome, the state will be saved.
        """
        # Restore encoder.
        encoder = self._restore_encoder()

        (encoded_message, status) = encoder.encode(message)
        if status != MteStatus.mte_status_success:
            print("Error encoding message: Status: ({0}): {1}".format(
                MteBase.get_status_name(status),
                MteBase.get_status_description(status)),
                file=sys.stderr)
            # Return none and status.
            return (None, status)
        
        # Save encoder.
        self._save_encoder(encoder)
        del encoder

        # Return the encoded message and success status.  
        return (encoded_message, status)
    
    def encode_b64(self, message):   
        """Encodes the given message. This will first restore the previous
            encoder state. The message will then be encoded. Following a
            successful outcome, the state will be saved.
        """    
        # Restore encoder.
        encoder = self._restore_encoder()

        (encoded_message, status) = encoder.encode_b64(message)
        if status != MteStatus.mte_status_success:
            print("Error base64 encoding message: Status: ({0}): {1}".format(
                MteBase.get_status_name(status),
                MteBase.get_status_description(status)),
                file=sys.stderr)
            # Return none and status.
            return (None, status)
        
        # Save encoder.
        self._save_encoder(encoder)
        del encoder

        # Return the encoded message and success status.  
        return (encoded_message, status)  
    
    def decode(self, encoded_message):
        """Decodes the given encoded message. This will first restore the
            previous decoder state. The message will then be decoded. Following
            a successful outcome, the state will be saved.
        """
        # Restore decoder.
        decoder = self._restore_decoder()

        (decoded_message, status) = decoder.decode(encoded_message)
        if MteBase.status_is_error(status):
            print("Error decoding message: Status: ({0}): {1}".format(
                MteBase.get_status_name(status),
                MteBase.get_status_description(status)),
                file=sys.stderr)
            # Return none and status.
            return (None, status)
        
        # Save decoder.
        self._save_decoder(decoder)
        del decoder
            
        # Return the decoded message and status.
        return (decoded_message, status)
    
    def decode_b64(self, encoded_message):
        """Decodes the given encoded message. This will first restore the
            previous decoder state. The message will then be decoded. Following
            a successful outcome, the state will be saved.
        """
        # Restore decoder.
        decoder = self._restore_decoder()

        (decoded_message, status) = decoder.decode_b64(encoded_message)
        if MteBase.status_is_error(status):
            print("Error base64 decoding message: Status: ({0}): {1}".format(
                MteBase.get_status_name(status),
                MteBase.get_status_description(status)),
                file=sys.stderr)
            # Return none and status.
            return (None, status)
        
        # Save decoder.
        self._save_decoder(decoder)
        del decoder
            
        # Return the decoded message and status.
        return (decoded_message, status)
    
    def _restore_encoder(self):
        """Restores the encoder state."""
        # Create encoder based on type.
        if self.type == 1:
            encoder = MteMkeEnc.fromdefault()
        else:
            encoder = MteEnc.fromdefault()

        # Restore encoder state.
        status = encoder.restore_state(self.encoder_state)

        if status != MteStatus.mte_status_success:
            return None

        self._save_encoder
        
        return encoder
    
    def _save_encoder(self, encoder):
        """Saves the encoder state."""
        # Save state.
        self.encoder_state = encoder.save_state()   

    def _restore_decoder(self):
        """Restores the decoder state."""
        # Create decoder based on type.
        if self.type == 1:
            decoder = MteMkeDec.fromdefault()
        else:
            decoder = MteDec.fromdefault()

        # Restore decoder state.
        status = decoder.restore_state(self.decoder_state)

        if status != MteStatus.mte_status_success:
            return None

        self._save_decoder
        
        return decoder
    
    def _save_decoder(self, decoder):
        """Saves the decoder state."""
        # Save state.
        self.decoder_state = decoder.save_state() 