// central JS usado por todas as páginas
const API = "/api";

// ----------------- Helpers -----------------
async function getJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function postJSON(url, body) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    return res;
}

// ----------------- Dashboard helpers -----------------
async function dashCadastrarVeiculo() {
    const marca = document.getElementById("dash-marca").value;
    const modelo = document.getElementById("dash-modelo").value;
    const ano = document.getElementById("dash-ano").value;
    if (!marca || !modelo || !ano) return alert("Preencha todos os campos");
    await postJSON(API + "/veiculos", { marca, modelo, ano });
    document.getElementById("dash-marca").value = "";
    document.getElementById("dash-modelo").value = "";
    document.getElementById("dash-ano").value = "";
    alert("Veículo cadastrado");
}

async function dashCadastrarCliente() {
    const nome = document.getElementById("dash-nome").value;
    const cpf = document.getElementById("dash-cpf").value;
    if (!nome || !cpf) return alert("Preencha todos os campos");
    await postJSON(API + "/clientes", { nome, cpf });
    document.getElementById("dash-nome").value = "";
    document.getElementById("dash-cpf").value = "";
    alert("Cliente cadastrado");
}

// ----------------- Carros page -----------------
async function carregarCarrosPage() {
    try {
        const veiculos = await getJSON(API + "/veiculos");
        const clientes = await getJSON(API + "/clientes");

        const container = document.getElementById("lista-veiculos-container");
        container.innerHTML = "";

        veiculos.forEach(v => {
            const div = document.createElement("div");
            div.style.padding = "10px 0";
            div.style.borderBottom = "1px solid #eee";
            div.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong>${v.marca} ${v.modelo}</strong> (${v.ano})<br>
                        <small style="color:${v.disponivel ? '#0a7' : '#c33'}">${v.disponivel ? "Disponível" : "Alugado"}</small>
                    </div>
                    <div style="display:flex; gap:8px; align-items:center;"></div>
                </div>
            `;

            const right = div.querySelector("div > div:last-child");
            if (v.disponivel) {
                const sel = document.createElement("select");
                sel.innerHTML = `<option value="">Cliente...</option>` + clientes.map(c => `<option value="${c.id}">${c.nome}</option>`).join("");
                const btn = document.createElement("button");
                btn.textContent = "Alugar";
                btn.style.background = "var(--blue-2)";
                btn.style.color = "white";
                btn.onclick = async () => {
                    if (!sel.value) return alert("Selecione um cliente");
                    const res = await postJSON(API + "/alugar", { id_cliente: sel.value, id_veiculo: v.id });
                    if (res.ok) {
                        alert("Alugado com sucesso");
                        carregarCarrosPage();
                    } else {
                        const e = await res.json().catch(()=>({erro: res.status}));
                        alert("Erro: " + (e.erro || res.status));
                    }
                };
                right.appendChild(sel);
                right.appendChild(btn);
            } else {
                const input = document.createElement("input");
                input.placeholder = "Valor por dia (R$)";
                input.type = "number";
                input.style.width = "120px";
                const btn = document.createElement("button");
                btn.textContent = "Devolver";
                btn.style.background = "#28a745";
                btn.style.color = "white";
                btn.onclick = async () => {
                    if (!input.value) return alert("Informe valor por dia");
                    const res = await postJSON(API + "/devolver", { id_veiculo: v.id, valor_dia: input.value });
                    if (res.ok) {
                        const body = await res.json();
                        alert(`Devolução registrada.\nDias: ${body.dias}\nTotal: R$ ${body.valor_total.toFixed(2)}`);
                        carregarCarrosPage();
                    } else {
                        const e = await res.json().catch(()=>({erro: res.status}));
                        alert("Erro: " + (e.erro || res.status));
                    }
                };
                right.appendChild(input);
                right.appendChild(btn);
            }

            container.appendChild(div);
        });

        // populate mini-client list if present
        const mini = document.getElementById("lista-clientes-mini");
        if (mini) {
            mini.innerHTML = "<ul style='list-style:none; padding:0; margin:0;'>" + clientes.map(c => `<li style="padding:6px 0; border-bottom:1px solid #f0f0f0">${c.nome} (${c.cpf})</li>`).join("") + "</ul>";
        }
    } catch (err) {
        console.error("Erro ao carregar carros page:", err);
        document.getElementById("lista-veiculos-container").innerHTML = "<div style='color:#c33'>Erro ao carregar lista de veículos. Veja console.</div>";
    }
}

// ----------------- Clientes page -----------------
async function carregarClientesPage() {
    try {
        const clientes = await getJSON(API + "/clientes");
        const alugueis = await getJSON(API + "/alugueis").catch(()=>[]);

        const listaFull = document.getElementById("lista-clientes-full");
        if (listaFull) {
            listaFull.innerHTML = "<ul style='list-style:none;padding:0;margin:0;'>" + clientes.map(c=>`<li style="padding:8px 0;border-bottom:1px solid #eee">${c.nome} (${c.cpf})</li>`).join("") + "</ul>";
        }

        const listaAlug = document.getElementById("lista-alugueis");
        if (listaAlug) {
            const ativos = alugueis.filter(a => !a.data_devolucao);
            listaAlug.innerHTML = ativos.length ? ativos.map(a => `<div style="padding:8px;border-bottom:1px solid #eee"><strong>${a.veiculo}</strong><br>Cliente: ${a.cliente}<br>Alugado em: ${new Date(a.data_aluguel).toLocaleString()}</div>`).join("") : "<div>Sem aluguéis ativos</div>";
        }
    } catch (err) {
        console.error("Erro ao carregar clientes page:", err);
    }
}

// ----------------- General utilities -----------------
async function cadastrarVeiculo() {
    const marca = document.getElementById("marca").value;
    const modelo = document.getElementById("modelo").value;
    const ano = document.getElementById("ano").value;
    if (!marca || !modelo || !ano) return alert("Preencha todos os campos");
    await postJSON(API + "/veiculos", { marca, modelo, ano });
    document.getElementById("marca").value = "";
    document.getElementById("modelo").value = "";
    document.getElementById("ano").value = "";
    alert("Veículo cadastrado");
    carregarCarrosPage();
}

async function cadastrarCliente() {
    const nome = document.getElementById("nome").value;
    const cpf = document.getElementById("cpf").value;
    if (!nome || !cpf) return alert("Preencha todos os campos");
    await postJSON(API + "/clientes", { nome, cpf });
    document.getElementById("nome").value = "";
    document.getElementById("cpf").value = "";
    alert("Cliente cadastrado");
    carregarCarrosPage(); // atualiza mini-lista também
}

// ----------------- Initialize -----------------
document.addEventListener("DOMContentLoaded", async () => {
    try {
        if (document.getElementById("lista-veiculos-container")) {
            await carregarCarrosPage();
        }
        if (document.getElementById("lista-clientes-full") || document.getElementById("lista-alugueis")) {
            await carregarClientesPage();
        }
    } catch (err) {
        console.error("Erro na inicialização do script:", err);
    }
});
