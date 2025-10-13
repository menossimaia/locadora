# --- Documentação do Programa ---
# ... (mesma de antes)

# --- Importações ---
from flask import Flask, request, jsonify, g, render_template
import sqlite3

# --- Configuração da Aplicação Flask ---
app = Flask(__name__)
DATABASE = 'locadora.db'

# --- Funções de Gerenciamento do Banco de Dados ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def inicializar_banco():
    # ... (esta função continua exatamente a mesma de antes)
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            disponivel BOOLEAN NOT NULL DEFAULT 1
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alugueis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER NOT NULL,
            id_veiculo INTEGER NOT NULL,
            data_aluguel TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_cliente) REFERENCES clientes (id),
            FOREIGN KEY (id_veiculo) REFERENCES veiculos (id)
        );
    ''')
    db.commit()
    db.close()

# --- Rota Principal para servir o Front-end ---
@app.route('/')
def index():
    return render_template('index.html')

# --- ROTAS PARA VEÍCULOS (sem alterações) ---
@app.route('/veiculos', methods=['POST'])
def cadastrar_veiculo():
    dados = request.get_json()
    if not dados or 'marca' not in dados or 'modelo' not in dados or 'ano' not in dados:
        return jsonify({'erro': 'Dados incompletos para o cadastro do veículo.'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO veiculos (marca, modelo, ano) VALUES (?, ?, ?)",
        (dados['marca'], dados['modelo'], dados['ano'])
    )
    db.commit()
    return jsonify({'mensagem': 'Veículo cadastrado com sucesso!'}), 201

@app.route('/veiculos', methods=['GET'])
def listar_veiculos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM veiculos ORDER BY marca, modelo")
    lista_de_veiculos = [dict(row) for row in cursor.fetchall()]
    return jsonify(lista_de_veiculos), 200

@app.route('/veiculos/<int:id>', methods=['DELETE'])
def descadastrar_veiculo(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM veiculos WHERE id = ?", (id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({'erro': 'Veículo não encontrado.'}), 404
    return jsonify({'mensagem': 'Veículo removido com sucesso!'}), 200

# --- ROTAS PARA CLIENTES (NOVO) ---
@app.route('/clientes', methods=['POST'])
def cadastrar_cliente():
    """
    Rota para cadastrar um novo cliente.
    Espera um JSON com 'nome' e 'cpf'.
    """
    dados = request.get_json()
    if not dados or 'nome' not in dados or 'cpf' not in dados:
        return jsonify({'erro': 'Dados incompletos para o cadastro do cliente.'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, cpf) VALUES (?, ?)",
            (dados['nome'], dados['cpf'])
        )
        db.commit()
    except sqlite3.IntegrityError: # Ocorre quando o CPF (UNIQUE) já existe
        return jsonify({'erro': 'CPF já cadastrado.'}), 409 # 409 Conflict

    return jsonify({'mensagem': 'Cliente cadastrado com sucesso!'}), 201

@app.route('/clientes', methods=['GET'])
def listar_clientes():
    """
    Rota para listar todos os clientes cadastrados.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY nome")
    lista_de_clientes = [dict(row) for row in cursor.fetchall()]
    return jsonify(lista_de_clientes), 200

@app.route('/clientes/<int:id>', methods=['DELETE'])
def descadastrar_cliente(id):
    """
    Rota para remover um cliente específico pelo seu ID.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
    db.commit()
    if cursor.rowcount == 0:
        return jsonify({'erro': 'Cliente não encontrado.'}), 404
    return jsonify({'mensagem': 'Cliente removido com sucesso!'}), 200

# --- Bloco de Execução Principal ---
if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True)