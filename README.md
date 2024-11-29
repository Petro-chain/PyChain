
# Documentação do Uso da Blockchain com Flask

Este projeto implementa uma blockchain simples com funcionalidades de mineração, sincronização de nós e gerenciamento de peers, utilizando Flask como API.

---

## **Requisitos**
- Python 3.7 ou superior
- Bibliotecas:
  - `Flask`
  - `Flask-CORS`
  - `requests`

Instale as dependências com:
```bash
pip install flask flask-cors requests
```

---

## **Como Executar**
### **Iniciar um Nó**
Execute o script e defina a porta do nó:
```bash
python blockchain.py --port <porta>
```
Se a porta não for especificada, o nó será executado na porta `5001` por padrão.

### **Endpoints Disponíveis**
A API fornece os seguintes endpoints:

---

### **1. Adicionar um Peer**
**Rota:**  
`POST /add_peer`

**Descrição:**  
Adiciona um novo peer à lista de peers do nó atual e sincroniza a cadeia com ele.

**Payload:**
```json
{
  "peer": "IP:porta"
}
```

**Adicionar um Peer:**
```bash
curl -X POST http://127.0.0.1:5001/add_peer -H "Content-Type: application/json" -d '{"peer": "127.0.0.1:5002"}'
```

---

### **2. Adicionar Dados**
**Rota:**  
`POST /add_data`

**Descrição:**  
Adiciona dados à fila de transações.

**Payload:**
```json
{
  "data": "Informação para a transação"
}
```

**Adicionar transações:**
```bash
curl -X POST http://127.0.0.1:5001/add_data -H "Content-Type: application/json" -d '{"data": "Transação exemplo"}'
```

---

### **3. Minerar um Bloco**
**Rota:**  
`POST /mine`

**Descrição:**  
Mineria um novo bloco utilizando as transações na fila e sincroniza o bloco com todos os peers.

**Minerar:**
```bash
curl -X POST http://127.0.0.1:5001/mine
```

**Resposta:**
```json
{
  "message": "Bloco minerado e sincronizado com todos os peers!",
  "block": {
    "index": 2,
    "timestamp": 1681928801.123456,
    "data": ["Transação exemplo"],
    "previous_hash": "0000abc123...",
    "hash": "0000def456...",
    "nonce": 10456
  }
}
```

---

### **4. Obter a Cadeia**
**Rota:**  
`GET /chain`

**Descrição:**  
Obtém a cadeia de blocos do nó.

**Obter cadeia:**
```bash
curl -X GET http://127.0.0.1:5001/chain
```

**Resposta:**
```json
{
  "chain": [
    {
      "index": 1,
      "timestamp": 1681928800.123456,
      "data": "Genesis Block",
      "previous_hash": "0",
      "hash": "0000abc123...",
      "nonce": 0
    },
    {
      "index": 2,
      "timestamp": 1681928801.123456,
      "data": ["Transação exemplo"],
      "previous_hash": "0000abc123...",
      "hash": "0000def456...",
      "nonce": 10456
    }
  ],
  "length": 2
}
```

---



## **Personalização**
O ID do nó pode ser alterado no construtor da classe `Blockchain`.  
Exemplo:
```python
blockchain = Blockchain("meu_nodo_personalizado")
```

---

## **Documentação do Endpoint `add_peer`**
Adiciona um novo peer à lista de peers do nó atual e sincroniza a cadeia com ele.  
Os peers representam outros nós na rede blockchain, identificados por `IP:porta`.  
Ao adicionar um peer, a cadeia do nó atual é automaticamente sincronizada com o peer adicionado. Isso garante consistência na rede.

---

## **Rota**
`POST /add_peer`

---

## **Payload**
```json
{
  "peer": "IP:porta"
}
```

---

## **Funcionamento Interno**
1. O endereço do peer é armazenado no conjunto `peers` do nó atual.
2. O nó tenta sincronizar sua cadeia local com a cadeia do peer adicionado.
3. Mensagens de sucesso ou erro são exibidas no console.

---

## **Add peer**
```bash
curl -X POST http://127.0.0.1:5001/add_peer -H "Content-Type: application/json" -d '{"peer": "127.0.0.1:5002"}'
```
## Sincronizar
```bash
curl -X POST -H "Content-Type: application/json" -d '{"node": "localhost:5001"}' http://localhost:5002/sync_chain_from_peer
```

---

## **Resposta**
### **Sucesso**
```json
{
  "message": "Peer adicionado e sincronizado automaticamente!"
}
```

