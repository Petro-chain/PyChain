import hashlib
import time
import requests
from flask import Flask, jsonify, request
from threading import Thread
from argparse import ArgumentParser


class Blockchain:
    def __init__(self, self_node):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.self_node = self_node
        self.create_genesis_block()

    def create_genesis_block(self):
        """Cria o bloco gênese"""
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
        """Calcula o hash do bloco"""
        block_string = f"{index}{data}{previous_hash}{nonce}"
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def mine_block(self, data):
        """Minerando um novo bloco com Prova de Trabalho"""
        if not self.nodes:
            return "Erro: Nenhum nó conectado. Conecte-se a um nó válido para minerar."

        # Verifica se todos os nós estão com a cadeia válida antes de minerar
        if not self.check_all_nodes_chain_valid():
            return jsonify({"error": "Não é possível minerar. Pelo menos um nó tem uma cadeia inválida."}), 400

        # Agora que todas as cadeias estão validadas, mineramos o bloco
        index = len(self.chain) + 1
        timestamp = time.time()
        previous_hash = self.chain[-1]["hash"]
        nonce = 0
        hash = self.calculate_hash(index, data, previous_hash, nonce)

        while not hash.startswith("0000"):
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
        self.current_transactions = []  # Limpa as transações após minerar
        self.broadcast_new_block(block)  # Informa todos os peers sobre o novo bloco
        return block

    def add_transaction(self, data):
        """Adiciona uma nova transação"""
        if not self.nodes:
            return "Erro: Nenhum nó conectado. Adicione um nó antes de adicionar transações."

        self.current_transactions.append(data)
        return {"message": "Transação adicionada!"}

    def validate_chain(self, chain):
        """Valida a cadeia recebida"""
        if not chain:
            return False
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]

            if current["previous_hash"] != previous["hash"]:
                print(f"Bloco {current['index']} tem hash anterior inválido!")
                return False

            if current["hash"] != self.calculate_hash(
                current["index"], current["data"], current["previous_hash"], current["nonce"]
            ):
                print(f"Bloco {current['index']} tem hash inválido!")
                return False
        return True

    def check_all_nodes_chain_valid(self):
        """Verifica se todas as cadeias dos nós estão válidas e compara com a sua cadeia"""
        last_local_block_hash = self.chain[-1]["hash"]
        
        for node in self.nodes:
            print(f"Verificando hash do último bloco no nó {node}")
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                remote_chain = response.json().get('chain')
                last_remote_block_hash = remote_chain[-1]["hash"]
                
                if last_local_block_hash != last_remote_block_hash:
                    print(f"Hash do último bloco do nó {node} é diferente. Minerando será bloqueado.")
                    return False  # Se os hashes não coincidirem, não permite minerar

        print("Os hashes dos últimos blocos são iguais em todos os nós. Pode-se prosseguir com a mineração.")
        return True

    def replace_chain(self, chain):
        """Substitui a cadeia atual pela cadeia recebida, se for válida"""
        if len(chain) > len(self.chain) and self.validate_chain(chain):
            self.chain = chain
            return True
        return False

    def add_node(self, address):
        """Adiciona um novo nó à rede e garante sincronização bidirecional"""
        if address not in self.nodes:
            self.nodes.add(address)

            try:
                # Primeiramente, sincronizar a cadeia com um nó existente
                self.sync_chain_with_node(address)

                # Verifica se a cadeia do nó adicionado é válida
                if not self.validate_chain(self.chain):
                    raise Exception(f"Falha: A cadeia do nó {address} é inválida ou inconsistente.")
                
                # Registrar o nó atual no novo nó
                requests.post(f'http://{address}/register_node', json={'node': self.self_node})

                # Agora, o novo nó precisa pegar a lista de todos os nós da rede
                response = requests.get(f'http://{address}/nodes')
                if response.status_code == 200:
                    # Adiciona todos os nós recebidos à lista de nós
                    new_nodes = response.json().get('nodes', [])
                    for node in new_nodes:
                        if node not in self.nodes and node != self.self_node:
                            self.nodes.add(node)

                else:
                    print(f"Erro ao obter lista de nós do nó {address}. Status code: {response.status_code}")
                    self.nodes.remove(address)
                    return  # Não permite adicionar o nó se falhar na obtenção da lista de nós

                # Agora, propaga a lista de nós do nó atual para o nó que foi adicionado
                for node in list(self.nodes):
                    if node != address:
                        try:
                            # Envia para o novo nó a lista de nós do nó atual
                            requests.post(f'http://{address}/register_node', json={'node': node})
                        except Exception as e:
                            print(f"Erro ao propagar nó {node}: {e}")

                # Agora envia para todos os nós da lista a inclusão do novo nó
                for node in list(self.nodes):
                    if node != address:
                        try:
                            # Propaga o novo nó para todos os nós existentes
                            requests.post(f'http://{node}/register_node', json={'node': address})
                        except Exception as e:
                            print(f"Erro ao propagar nó {node}: {e}")

                return {"message": "Nó adicionado e sincronizado!"}

            except Exception as e:
                print(f"Erro ao registrar o nó atual no nó {address}: {e}")
                self.nodes.remove(address)
                return  # Não permite adicionar o nó se houver erro
        else:
            print(f"O nó {address} já está na rede!")


    def broadcast_new_block(self, block):
        """Informa todos os nós sobre um novo bloco minerado"""
        for node in list(self.nodes):
            try:
                response = requests.post(f'http://{node}/add_block', json={'block': block})
                if response.status_code != 200:
                    print(f"Falha ao informar o nó {node} sobre o novo bloco")
            except Exception as e:
                print(f"Erro ao informar o nó {node}: {e}")

    def sync_chain_with_node(self, node):
        """Sincroniza a cadeia com outro nó"""
        try:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                if len(chain) > len(self.chain) and self.validate_chain(chain):
                    self.chain = chain
                    print(f"Sincronizando com o nó {node} - Nova cadeia adotada!")
                else:
                    print(f"A cadeia recebida do nó {node} é mais curta ou inválida.")
        except Exception as e:
            print(f"Erro ao sincronizar com o nó {node}: {e}")

    def sync_chain_from_all_nodes(self):
        """Sincroniza a cadeia de blocos com todos os nós conectados"""
        for node in self.nodes:
            self.sync_chain_with_node(node)

# Setup do servidor Flask
app = Flask(__name__)
blockchain = None

@app.route('/add_node', methods=['POST'])
def add_node():
    node = request.json.get('node')
    blockchain.add_node(node)
    # Verifica se as cadeias estão sincronizadas com todos os nós
    blockchain.sync_chain_from_all_nodes()
    return jsonify({"message": "Nó adicionado e sincronizado!"})

@app.route('/register_node', methods=['POST'])
def register_node():
    node = request.json.get('node')
    if node and node not in blockchain.nodes:
        blockchain.nodes.add(node)
    return jsonify({"message": "Nó registrado!", "nodes": list(blockchain.nodes)})

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json.get('data')
    response = blockchain.add_transaction(data)
    if isinstance(response, str):  # Se for erro, retorna como erro
        return jsonify({"error": response}), 400
    return jsonify(response)

@app.route('/mine', methods=['POST'])
def mine():
    # Verifica se todos os nós estão com a cadeia válida antes de minerar
    if not blockchain.check_all_nodes_chain_valid():
        return jsonify({"error": "Não é possível minerar. Pelo menos um nó tem uma cadeia inválida."}), 400

    if blockchain.current_transactions:
        block = blockchain.mine_block(blockchain.current_transactions)
        return jsonify({"message": "Bloco minerado!", "block": block})
    return jsonify({"message": "Nenhuma transação para minerar."})

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify({"chain": blockchain.chain, "length": len(blockchain.chain)})

@app.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify({"nodes": list(blockchain.nodes)})

@app.route('/add_block', methods=['POST'])
def add_block():
    block = request.json.get('block')
    blockchain.chain.append(block)
    return jsonify({"message": "Bloco adicionado!"}), 200
    
@app.route('/sync_chain_from_peer', methods=['POST'])
def sync_chain_from_peer():
    """Endpoint para sincronizar a cadeia de blocos com um nó específico"""
    peer_node = request.json.get('node')
    if peer_node:
        blockchain.sync_chain_with_node(peer_node)
        return jsonify({"message": f"Cadeia sincronizada com o nó {peer_node}!"})
    return jsonify({"error": "Nó não especificado."}), 400


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='porta a ser usada pelo nó')
    args = parser.parse_args()
    port = args.port

    blockchain = Blockchain(self_node=f"localhost:{port}")
    app.run(host='0.0.0.0', port=port)
