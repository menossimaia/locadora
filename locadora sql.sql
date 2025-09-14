CREATE TABLE IF NOT EXISTS veiculos (
    id SERIAL PRIMARY KEY,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano INTEGER NOT NULL,
    disponivel BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cpf TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS alugueis (
    id SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    id_veiculo INTEGER NOT NULL,
    data_aluguel TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES clientes (id),
    FOREIGN KEY (id_veiculo) REFERENCES veiculos (id)
);