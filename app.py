from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)

# ---------- CONFIGURAÇÃO DO BANCO ----------
DB_CONFIG = {
    "host": "localhost",
    "dbname": "locadora_db",
    "user": "admin",
    "password": "admin",
    "port": 5432
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ---------- INICIALIZAÇÃO DO BANCO ----------
def inicializar_banco():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(200),
        cpf VARCHAR(30)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS veiculos (
        id SERIAL PRIMARY KEY,
        marca VARCHAR(100),
        modelo VARCHAR(100),
        ano INTEGER,
        disponivel BOOLEAN DEFAULT TRUE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alugueis (
        id SERIAL PRIMARY KEY,
        id_cliente INTEGER REFERENCES clientes(id),
        id_veiculo INTEGER REFERENCES veiculos(id),
        data_aluguel TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        data_devolucao TIMESTAMP WITH TIME ZONE,
        valor_total NUMERIC(10,2)
    );
    """)

    # garante coluna valor_total (idempotente)
    cur.execute("""
    ALTER TABLE alugueis
    ADD COLUMN IF NOT EXISTS valor_total NUMERIC(10,2);
    """)

    conn.commit()
    cur.close()
    conn.close()


# ---------- ROTAS DE PÁGINA ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/carros")
def carros_page():
    return render_template("carros.html")

@app.route("/clientes")
def clientes_page():
    return render_template("clientes.html")


# ---------- API: CLIENTES ----------
@app.route("/api/clientes", methods=["GET"])
def api_listar_clientes():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nome, cpf FROM clientes ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200


@app.route("/api/clientes", methods=["POST"])
def api_cadastrar_cliente():
    data = request.get_json()
    if not data or not data.get("nome") or not data.get("cpf"):
        return jsonify({"erro": "Dados incompletos"}), 400
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO clientes (nome, cpf) VALUES (%s, %s);",
                    (data["nome"], data["cpf"]))
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"erro": "CPF já cadastrado"}), 409
    cur.close()
    conn.close()
    return jsonify({"status": "ok"}), 201


# ---------- API: VEÍCULOS ----------
@app.route("/api/veiculos", methods=["GET"])
def api_listar_veiculos():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, marca, modelo, ano, disponivel FROM veiculos ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200


@app.route("/api/veiculos", methods=["POST"])
def api_cadastrar_veiculo():
    data = request.get_json()
    if not data or not data.get("marca") or not data.get("modelo") or not data.get("ano"):
        return jsonify({"erro": "Dados incompletos"}), 400
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO veiculos (marca, modelo, ano) VALUES (%s, %s, %s);",
                (data["marca"], data["modelo"], int(data["ano"])))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"}), 201


# ---------- API: ALUGAR ----------
@app.route("/api/alugar", methods=["POST"])
def api_alugar():
    data = request.get_json()
    id_cliente = data.get("id_cliente")
    id_veiculo = data.get("id_veiculo")
    if not id_cliente or not id_veiculo:
        return jsonify({"erro": "Dados incompletos"}), 400

    conn = get_conn()
    cur = conn.cursor()
    # verificar disponibilidade
    cur.execute("SELECT disponivel FROM veiculos WHERE id = %s;", (id_veiculo,))
    res = cur.fetchone()
    if not res:
        cur.close(); conn.close()
        return jsonify({"erro": "Veículo não encontrado"}), 404
    disponivel = res[0]
    if not disponivel:
        cur.close(); conn.close()
        return jsonify({"erro": "Veículo indisponível"}), 400

    # cria aluguel e marca veículo indisponível
    cur.execute("INSERT INTO alugueis (id_cliente, id_veiculo) VALUES (%s, %s);",
                (id_cliente, id_veiculo))
    cur.execute("UPDATE veiculos SET disponivel = FALSE WHERE id = %s;", (id_veiculo,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok"}), 201


# ---------- API: LISTAR ALUGUÉIS ----------
@app.route("/api/alugueis", methods=["GET"])
def api_listar_alugueis():
    """
    Retorna lista de aluguéis com cliente e veículo (serializando datetimes).
    """
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.id,
               a.id_cliente,
               a.id_veiculo,
               a.data_aluguel,
               a.data_devolucao,
               a.valor_total,
               c.nome AS cliente,
               v.marca || ' ' || v.modelo AS veiculo
        FROM alugueis a
        LEFT JOIN clientes c ON c.id = a.id_cliente
        LEFT JOIN veiculos v ON v.id = a.id_veiculo
        ORDER BY a.data_aluguel DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Serializar datetimes para ISO strings (JSON-friendly)
    out = []
    for r in rows:
        item = {
            "id": r["id"],
            "id_cliente": r["id_cliente"],
            "id_veiculo": r["id_veiculo"],
            "cliente": r["cliente"],
            "veiculo": r["veiculo"],
            "data_aluguel": r["data_aluguel"].astimezone(timezone.utc).isoformat() if r["data_aluguel"] else None,
            "data_devolucao": r["data_devolucao"].astimezone(timezone.utc).isoformat() if r["data_devolucao"] else None,
            "valor_total": float(r["valor_total"]) if r["valor_total"] is not None else None
        }
        out.append(item)

    return jsonify(out), 200


# ---------- API: DEVOLVER (com cobrança) ----------
@app.route("/api/devolver", methods=["POST"])
def api_devolver():
    data = request.get_json()
    id_veiculo = data.get("id_veiculo")
    valor_dia = data.get("valor_dia")

    if id_veiculo is None or valor_dia is None:
        return jsonify({"erro": "Dados incompletos"}), 400

    try:
        valor_dia = float(valor_dia)
    except:
        return jsonify({"erro": "valor_dia inválido"}), 400

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # busca o aluguel aberto para esse veículo
    cur.execute("""
        SELECT id, data_aluguel, id_veiculo
        FROM alugueis
        WHERE id_veiculo = %s AND data_devolucao IS NULL
        ORDER BY data_aluguel DESC
        LIMIT 1;
    """, (id_veiculo,))

    aluguel = cur.fetchone()
    if not aluguel:
        cur.close(); conn.close()
        return jsonify({"erro": "Veículo não está alugado"}), 400

    id_aluguel = aluguel['id']
    data_aluguel = aluguel['data_aluguel']  # may be timezone-aware

    if data_aluguel is None:
        cur.close(); conn.close()
        return jsonify({"erro": "Registro de aluguel sem data"}), 500

    # ensure timezone-aware in UTC
    if data_aluguel.tzinfo is None:
        data_aluguel = data_aluguel.replace(tzinfo=timezone.utc)
    else:
        data_aluguel = data_aluguel.astimezone(timezone.utc)

    agora = datetime.now(timezone.utc)
    delta = agora - data_aluguel
    dias = delta.days
    if dias < 1:
        dias = 1

    total = round(dias * valor_dia, 2)

    # atualiza aluguel e libera veículo
    cur.execute("""
        UPDATE alugueis
        SET data_devolucao = %s, valor_total = %s
        WHERE id = %s;
    """, (agora, total, id_aluguel))

    cur.execute("UPDATE veiculos SET disponivel = TRUE WHERE id = %s;", (id_veiculo,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "dias": dias, "valor_total": float(total)}), 200


# ---------- START ----------
if __name__ == "__main__":
    inicializar_banco()
    app.run(debug=True)
