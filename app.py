import os
import psycopg2
import psycopg2.extras 
from dotenv import load_dotenv
from flask import Flask, request, jsonify, g, render_template


load_dotenv()

app = Flask(__name__)

DATABASE_URL="postgresql://locadora_user:admin@localhost:5432/locadora_db"


def get_db():
    """
    Função para conectar ao banco de dados PostgreSQL.
    A conexão é reutilizada durante a mesma requisição.
    """
    if 'db' not in g:
        g.db = psycopg2.connect(DATABASE_URL)
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """ Fecha a conexão com o banco de dados ao final da requisição. """
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/carros')
def pagina_carros():
    return render_template('carros.html')

@app.route('/clientes')
def pagina_clientes():
    return render_template('clientes.html')



@app.route('/veiculos', methods=['POST'])
def cadastrar_veiculo():
    dados = request.get_json()
    if not dados or 'marca' not in dados or 'modelo' not in dados or 'ano' not in dados:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        "INSERT INTO veiculos (marca, modelo, ano) VALUES (%s, %s, %s)",
        (dados['marca'], dados['modelo'], dados['ano'])
    )
    db.commit()
    cursor.close()
    return jsonify({'mensagem': 'Veículo cadastrado!'}), 201

@app.route('/veiculos', methods=['GET'])
def listar_veiculos():
    db = get_db()
   
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM veiculos ORDER BY id")
    veiculos = cursor.fetchall()
    cursor.close()
    return jsonify(veiculos), 200

@app.route('/veiculos/<int:id>', methods=['DELETE'])
def descadastrar_veiculo(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM veiculos WHERE id = %s", (id,))
    db.commit()
    rowcount = cursor.rowcount
    cursor.close()
    if rowcount == 0:
        return jsonify({'erro': 'Veículo não encontrado.'}), 404
    return jsonify({'mensagem': 'Veículo removido!'}), 200


@app.route('/clientes', methods=['POST'])
def cadastrar_cliente():
    dados = request.get_json()
    if not dados or 'nome' not in dados or 'cpf' not in dados:
        return jsonify({'erro': 'Dados incompletos.'}), 400
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO clientes (nome, cpf) VALUES (%s, %s)",
            (dados['nome'], dados['cpf'])
        )
        db.commit()
    except psycopg2.IntegrityError:
        db.rollback() 
        return jsonify({'erro': 'CPF já cadastrado.'}), 409
    finally:
        cursor.close()

    return jsonify({'mensagem': 'Cliente cadastrado!'}), 201

@app.route('/clientes', methods=['GET'])
def listar_clientes():
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM clientes ORDER BY id")
    clientes = cursor.fetchall()
    cursor.close()
    return jsonify(clientes), 200

@app.route('/clientes/<int:id>', methods=['DELETE'])
def descadastrar_cliente(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
    db.commit()
    rowcount = cursor.rowcount
    cursor.close()
    if rowcount == 0:
        return jsonify({'erro': 'Cliente não encontrado.'}), 404
    return jsonify({'mensagem': 'Cliente removido!'}), 200


if __name__ == '__main__':
    app.run(debug=True)