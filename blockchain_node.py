import hashlib
import time
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

class Blockchain:
    def __init__(self, node_id):
        self.chain = []
        self.current_transactions = []
        self.peers = set()  # Peers conectados
        self.node_id = node_id
        self.generate_genesis_block()

    def generate_genesis_block(self):
        genesis_block = {
            "index": 1,
            "timestamp": time.time(),
            "data": "Genesis Block",
            "previous_hash": "0",
            "hash": self.calculate_hash(1, "Genesis Block", "0", 0),
            "nonce": 0
        }
        self.chain.append(genesis_block)

    def calculate_hash(self, index, data, previous_hash, nonce):
        block_string = f"{index}{data}{previous_hash}{nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine_new_block(self, data):
        index = len(self.chain) + 1
        timestamp = time.time()
        previous_hash = self.chain[-1]["hash"]
        nonce = 0
        hash = self.calculate_hash(index, data, previous_hash, nonce)

        # Processo de mineração (forçando a busca por um nonce correto)
        while not hash.startswith("0000"):  # Prova de Trabalho (Proof of Work)
            nonce += 1
            hash = self.calculate_hash(index, data, previous_hash, nonce)

        block = {
            "index": index,
            "timestamp": timestamp,
            "data": data,
            "previous_hash": previous_hash,
            "hash": hash,
            "nonce": nonce
        }

        self.chain.append(block)
        return block

    def add_transaction(self, data):
        self.current_transactions.append(data)

    def sync_chain_with_peer(self, peer):
        try:
            url = f'http://{peer}/sync_chain'
            response = requests.post(url, json={"chain": self.chain})
            if response.status_code == 200:
                print(f"Cadeia sincronizada com sucesso para o peer {peer}")
            else:
                print(f"Falha ao sincronizar com o peer {peer}")
        except Exception as e:
            print(f"Erro ao sincronizar com {peer}: {e}")

    def sync_chain_with_all_peers(self):
        # Sincroniza com todos os peers registrados
        for peer in self.peers:
            self.sync_chain_with_peer(peer)

    def add_peer(self, peer):
        # O peer é adicionado automaticamente
        self.peers.add(peer)
        # Após adicionar o peer, sincronize com ele automaticamente
        self.sync_chain_with_peer(peer)

    def get_chain(self):
        return self.chain

    def get_peers(self):
        return list(self.peers)

# Instanciando a blockchain para o nó
blockchain = Blockchain("node_1")

@app.route('/add_peer', methods=['POST'])
def add_peer():
    peer = request.json.get('peer')
    blockchain.add_peer(peer)
    return jsonify({"message": "Peer adicionado e sincronizado automaticamente!"})

@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.json.get('data')
    blockchain.add_transaction(data)
    return jsonify({"message": "Dados adicionados à fila de transações!"})

@app.route('/mine', methods=['POST'])
def mine():
    if blockchain.current_transactions:
        # Minerando o novo bloco
        block = blockchain.mine_new_block(blockchain.current_transactions)
        blockchain.current_transactions = []

        # Sincronizando com todos os peers registrados
        blockchain.sync_chain_with_all_peers()

        return jsonify({
            "message": "Bloco minerado e sincronizado com todos os peers!",
            "block": block
        })
    return jsonify({"message": "Não há transações para minerar!"})

@app.route('/get_chain', methods=['GET'])
def get_chain():
    return jsonify({
        "chain": blockchain.get_chain(),
        "length": len(blockchain.get_chain())
    })

@app.route('/sync_chain', methods=['POST'])
def sync_chain():
    new_chain = request.json.get("chain")
    if len(new_chain) > len(blockchain.chain):
        blockchain.chain = new_chain
        return jsonify({"message": "Cadeia sincronizada com sucesso!"}), 200
    else:
        return jsonify({"message": "A cadeia local já está atualizada!"}), 200

if __name__ == '__main__':
    app.run(port=5004)
