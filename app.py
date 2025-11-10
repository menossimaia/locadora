from flask import Flask, request, jsonify, render_template
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# --- CONFIGURAÇÃO DO BANCO ---
DB_CONFIG = {
    "host": "localhost",
    "database": "locadora_db",
    "user": "admin",
    "password": "admin",
    "port": 5432
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def inicializar_banco():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id SERIAL PRIMARY KEY,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER NOT NULL,
            disponivel BOOLEAN NOT NULL DEFAULT TRUE
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alugueis (
            id SERIAL PRIMARY KEY,
            id_cliente INTEGER NOT NULL,
            id_veiculo INTEGER NOT NULL,
            data_aluguel TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_cliente) REFERENCES clientes (id),
            FOREIGN KEY (id_veiculo) REFERENCES veiculos (id)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- ROTA PRINCIPAL ---
@app.route('/')
def index():
    return render_template('index.html')

# --- ROTAS DE VEÍCULOS ---
@app.route('/veiculos', methods=['GET'])
def listar_veiculos():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM veiculos ORDER BY marca, modelo")
    veiculos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(veiculos), 200

@app.route('/veiculos', methods=['POST'])
def cadastrar_veiculo():
    dados = request.get_json()
    if not dados or 'marca' not in dados or 'modelo' not in dados or 'ano' not in dados:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO veiculos (marca, modelo, ano) VALUES (%s, %s, %s)", 
                (dados['marca'], dados['modelo'], dados['ano']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensagem': 'Veículo cadastrado com sucesso!'}), 201

@app.route('/veiculos/<int:id>', methods=['DELETE'])
def excluir_veiculo(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM veiculos WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensagem': 'Veículo excluído com sucesso!'}), 200

# --- ROTAS DE CLIENTES ---
@app.route('/clientes', methods=['GET'])
def listar_clientes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM clientes ORDER BY nome")
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(clientes), 200

@app.route('/clientes', methods=['POST'])
def cadastrar_cliente():
    dados = request.get_json()
    if not dados or 'nome' not in dados or 'cpf' not in dados:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO clientes (nome, cpf) VALUES (%s, %s)", 
                    (dados['nome'], dados['cpf']))
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({'erro': 'CPF já cadastrado.'}), 409
    finally:
        cur.close()
        conn.close()
    return jsonify({'mensagem': 'Cliente cadastrado com sucesso!'}), 201

@app.route('/clientes/<int:id>', methods=['DELETE'])
def excluir_cliente(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM clientes WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'mensagem': 'Cliente excluído com sucesso!'}), 200

# --- NOVA ROTA: ALUGAR VEÍCULO ---
@app.route('/alugar', methods=['POST'])
def alugar_veiculo():
    dados = request.get_json()
    if not dados or 'id_cliente' not in dados or 'id_veiculo' not in dados:
        return jsonify({'erro': 'Dados incompletos para aluguel.'}), 400

    conn = get_connection()
    cur = conn.cursor()
    # Verifica se o veículo está disponível
    cur.execute("SELECT disponivel FROM veiculos WHERE id = %s", (dados['id_veiculo'],))
    veiculo = cur.fetchone()
    if not veiculo:
        cur.close()
        conn.close()
        return jsonify({'erro': 'Veículo não encontrado.'}), 404
    if not veiculo[0]:
        cur.close()
        conn.close()
        return jsonify({'erro': 'Veículo já alugado.'}), 409

    # Faz o aluguel e marca como indisponível
    cur.execute("""
        INSERT INTO alugueis (id_cliente, id_veiculo) VALUES (%s, %s);
    """, (dados['id_cliente'], dados['id_veiculo']))
    cur.execute("UPDATE veiculos SET disponivel = FALSE WHERE id = %s", (dados['id_veiculo'],))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'mensagem': 'Veículo alugado com sucesso!'}), 201


if __name__ == '__main__':
    inicializar_banco()
    app.run(debug=True)
