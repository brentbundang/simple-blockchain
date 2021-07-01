import hashlib
import json
from time import altzone, time 
from uuid import uuid4
from flask import Flask
from urllib.parse import urlparse
import requests

class Blockchain(object):

    def __init__(self):
        self.chain=[]
        self.current_transactions=[]
        self.nodes = set()
        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new block in the blockchain
        :param proof: <int> The proof given by the proof of work algorithim
        :param previous_hash (Optional) <str> Hash of the previous Block
        :return: <dict> New block
        """

        block = {
        'index': len(self.chain) + 1,
        'timestamp': time(),
        'transactions': self.current_transactions,
        'proof': proof,
        'previous_hash': previous_hash,
        }

        # Reset the current list of transactions 
        self.current_transactions = []

        self.chain.append(block)
        return block


    def new_transaction(self, sender, recipient, amount):
        # Adds a new transaction to the list of transactions 
        """Creates a new transaction to go into the next mined block
        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the recipient 
        :param amount: <int> Amount
        :return: <int> The index of the block that will hold this transaction """

        self.current_transactions.append({
        'sender': sender,
        'recipient': recipient,
        'amount': amount
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # Returns the last block in the chain 
        return self.chain[-1]

    @staticmethod
    def hash(block):
        #Hashes a block
        """
        Creates a SHA-256 hash of a block
        :param block: <dict> Block
        :return: <str>
        """

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest() 

    def proof_of_work(self, last_proof):
        """Simple proof of work algorithim:

        Find a number p such that hash (pp') contains 4 zeroes, where p is the previous p' 
        p is the previous proof and p' is the new proof

        :param last_proof: <int>
        :return: <int>
        """

        proof = 0 
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """ 
        Validates the proof: Does hash(last_proof, proof) contain 4 leading zeros?
        :param last_proof: <int> Previous proof
        :param proof: <int> Current proof
        :return: <bool> True if correct, false if not. 
        """        

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    
    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of a node. Eg. 'http://192.168.0.5:5000'
        :return: None        
        """
        
        parser_url = urlparse(address)
        self.nodes.add(parser_url.netloc)


    def valid_chain(self,chain):
        """Determine if a given blockchain is valid

        Args:
            chain ([list]): A blockchain

        Returns:
            [bool]: True if valid, False if not
        """
        
        last_block = [0]
        current_index = 1
        
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n---------\n")
            # Check that the hash of the block is correct 
            if block['previous_hash'] != self.hash(last_block):
                return False
            
            #Check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False 
            
            last_block = block
            current_index += 1
            
        return True
    
    def resolve_conflicts(self):
        """ Resolve conflicts by replacing the chain with the longest one on the network.

        Returns:
            [bool]: True if our chained was replaced, return false if not
        """
        neighbors = self.nodes
        new_chain = None
        
        # Only get the chains that are longer than ours 
        
        max_length = len(self.chain)
        
        # Grab and verify the chains from all the nodes in the network 
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')
            
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                # Check if the length is longer and chain is valid 
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
                    
        # Replace our chain if we discovered a new, valid chain longer than ours 
        if new_chain:
            self.chain = new_chain
            return True
        
        return False