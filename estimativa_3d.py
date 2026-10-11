import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Estimativa Rápida 3D", layout="centered")

st.title("⚡ Estimativa Rápida de Orçamento 3D")
st.markdown("Insira os parâmetros abaixo para calcular o preço final estimado para o cliente.")

# Nome do ficheiro da base de dados
CSV_FILE = "historico_orcamentos.csv"

# Base de Dados Dinâmica de Materiais (Preço €, Peso g, Consumo kW)
MATERIAIS = {
    "PLA": {"preco": 20.0, "peso": 1000.0, "consumo": 0.150},
    "PETG": {"preco": 22.0, "peso": 1000.0, "consumo": 0.200},
    "ABS / ASA": {"preco": 25.0, "peso": 1000.0, "consumo": 0.250},
    "TPU (Flexível)": {"preco": 35.0, "peso": 1000.0, "consumo": 0.150},
    "PA-CF (Nylon Fibra de Carbono)": {"preco": 65.0, "peso": 500.0, "consumo": 0.300}
}

# Constantes Fixas da Empresa
CUSTO_KWH = 0.16     # €
CUSTO_MAQUINA = 800.0
VIDA_UTIL_HORAS = 8000.0
TEMPO_SETUP_POR_PECA = 0.1 # horas (6 min)
VALOR_HORA_SETUP = 15.0 # €
MARGEM_LUCRO_DEFAULT = 30 # %

st.divider()

# Formulário para podermos submeter e limpar os dados facilmente
with st.form("orcamento_form"):
    
    # Secção: Informações do Cliente/Projeto (Novo)
    st.subheader("📝 Dados do Projeto")
    col_proj1, col_proj2 = st.columns(2)
    with col_proj1:
        nome_cliente = st.text_input("Nome do Cliente / Projeto", placeholder="Ex: Peça R&D Motor v2")
    with col_proj2:
        responsavel = st.text_input("Responsável", placeholder="O teu nome")

    # Secção: Seleção de Material
    st.subheader("⚙️ Configuração do Material")
    material_selecionado = st.selectbox("Escolha o tipo de filamento:", list(MATERIAIS.keys()))

    preco_base = MATERIAIS[material_selecionado]["preco"]
    peso_base = MATERIAIS[material_selecionado]["peso"]
    consumo_base = MATERIAIS[material_selecionado]["consumo"]

    col_mat1, col_mat2, col_mat3 = st.columns(3)
    with col_mat1:
        preco_bobina = st.number_input("Preço da Bobina (€)", value=preco_base, step=1.0)
    with col_mat2:
        peso_bobina = st.number_input("Peso da Bobina (g)", value=peso_base, step=100.0)
    with col_mat3:
        consumo_impressora = st.number_input("Consumo Máquina (kW)", value=consumo_base, step=0.05)

    st.divider()

    # Inputs Originais
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Parâmetros do Pedido")
        peso_1_peca = st.number_input("Peso de 1 Peça (gramas)", min_value=0.0, value=50.0, step=1.0)
        tempo_1_impressao = st.number_input("Tempo de 1 Impressão (horas)", min_value=0.0, value=2.5, step=0.5)

    with col2:
        st.subheader("📈 Volume e Margem")
        numero_pecas = st.number_input("Número de Peças", min_value=1, value=1, step=1)
        margem_lucro = st.slider("Margem de Lucro (%)", min_value=0, max_value=200, value=MARGEM_LUCRO_DEFAULT)
        
    # Botão de submissão do formulário
    calcular = st.form_submit_button("Calcular e Guardar Orçamento", use_container_width=True)

# Lógica após submeter o formulário
if calcular:
    if not nome_cliente:
        st.warning("⚠️ Por favor, insere o Nome do Cliente ou Projeto para poder guardar no histórico.")
    else:
        # Cálculos
        peso_total = peso_1_peca * numero_pecas
        tempo_total = tempo_1_impressao * numero_pecas
        tempo_setup_total = TEMPO_SETUP_POR_PECA * numero_pecas

        custo_material = (peso_total / peso_bobina) * preco_bobina
        custo_energia = tempo_total * consumo_impressora * CUSTO_KWH
        custo_depreciacao = tempo_total * (CUSTO_MAQUINA / VIDA_UTIL_HORAS)
        custo_trabalho = tempo_setup_total * VALOR_HORA_SETUP

        custo_producao = custo_material + custo_energia + custo_depreciacao + custo_trabalho
        preco_final = custo_producao * (1 + (margem_lucro / 100))
        
        # Obter data e hora atuais
        data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Preparar dados para o DataFrame
        novo_registo = pd.DataFrame([{
            "Data/Hora": data_hora_atual,
            "Projeto/Cliente": nome_cliente,
            "Responsável": responsavel if responsavel else "N/A",
            "Material": material_selecionado,
            "Peso Peça(g)": peso_1_peca,
            "Tempo Peça(h)": tempo_1_impressao,
            "Quantidade": numero_pecas,
            "Custo Produção(€)": round(custo_producao, 2),
            "Margem(%)": margem_lucro,
            "Preço Final(€)": round(preco_final, 2)
        }])

        # Lógica para guardar no CSV
        if os.path.isfile(CSV_FILE):
            # Se o ficheiro existe, carrega e anexa
            df_existente = pd.read_csv(CSV_FILE)
            df_atualizado = pd.concat([df_existente, novo_registo], ignore_index=True)
        else:
            # Se não existe, cria um novo
            df_atualizado = novo_registo
            
        # Gravar no ficheiro
        df_atualizado.to_csv(CSV_FILE, index=False)
        
        st.divider()
        st.subheader("💰 Estimativa Final")
        col_a, col_b = st.columns(2)
        with col_a:
            st.info(f"**Custo de Produção:** € {custo_producao:.2f}")
        with col_b:
            st.success(f"**Preço a Cobrar:** € {preco_final:.2f}")
            
        st.toast(f"✅ Orçamento de '{nome_cliente}' guardado com sucesso no histórico!", icon="💾")

st.divider()

# Secção de Visualização do Histórico
st.subheader("📂 Histórico de Orçamentos")
if os.path.isfile(CSV_FILE):
    df_historico = pd.read_csv(CSV_FILE)
    st.dataframe(df_historico, use_container_width=True)
    
    # Botão para descarregar o Excel/CSV para a contabilidade
    csv = df_historico.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descarregar Histórico (CSV)",
        data=csv,
        file_name='historico_orcamentos_3d.csv',
        mime='text/csv',
    )
else:
    st.info("Nenhum orçamento guardado ainda. Faz o teu primeiro cálculo acima.")
