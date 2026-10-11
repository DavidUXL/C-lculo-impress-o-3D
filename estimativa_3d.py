import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Gestão 3D", layout="centered")

# 1. Definição dos Ficheiros de Base de Dados
CSV_HISTORICO = "historico_orcamentos.csv"
CSV_MATERIAIS = "base_materiais.csv"

# 2. Criar a base de dados de materiais automaticamente se for a primeira vez
if not os.path.isfile(CSV_MATERIAIS):
    df_default = pd.DataFrame([
        {"Material": "PLA Padrão", "Preco_Bobina": 20.0, "Peso_Bobina": 1000.0, "Consumo_kW": 0.150},
        {"Material": "PETG Padrão", "Preco_Bobina": 22.0, "Peso_Bobina": 1000.0, "Consumo_kW": 0.200},
        {"Material": "PA-CF (Nylon Carbono)", "Preco_Bobina": 65.0, "Peso_Bobina": 500.0, "Consumo_kW": 0.300}
    ])
    df_default.to_csv(CSV_MATERIAIS, index=False)

# Carregar os materiais guardados
df_materiais = pd.read_csv(CSV_MATERIAIS)

# 3. Constantes Fixas da Máquina/Empresa
CUSTO_KWH = 0.16
CUSTO_MAQUINA = 800.0
VIDA_UTIL_HORAS = 8000.0
TEMPO_SETUP = 0.1
VALOR_HORA_SETUP = 15.0

st.title("🖨️ Gestão de Orçamentos 3D")
st.divider()

# 4. Criar Navegação por Separadores
tab1, tab2, tab3 = st.tabs(["⚡ Calculadora", "🛠️ Inventário de Materiais", "📂 Histórico"])

# ==========================================
# SEPARADOR 1: CALCULADORA
# ==========================================
with tab1:
    with st.form("orcamento_form"):
        st.subheader("📝 Dados do Projeto")
        col_proj1, col_proj2 = st.columns(2)
        with col_proj1:
            nome_cliente = st.text_input("Cliente / Projeto", placeholder="Ex: Peça R&D Motor v2")
        with col_proj2:
            numero_pecas = st.number_input("Quantidade de Peças", min_value=1, value=1)

        st.subheader("⚙️ Seleção de Material")
        # A dropdown agora lê diretamente da base de dados CSV visual
        lista_materiais = df_materiais["Material"].tolist()
        material_escolhido = st.selectbox("Escolhe o filamento da tua base:", lista_materiais)
        
        # Isolar os dados do material selecionado
        dados_mat = df_materiais[df_materiais["Material"] == material_escolhido].iloc[0]

        st.subheader("📦 Parâmetros de Impressão")
        colA, colB = st.columns(2)
        with colA:
            peso_1_peca = st.number_input("Peso de 1 Peça (gramas)", min_value=0.0, value=50.0)
        with colB:
            tempo_1_impressao = st.number_input("Tempo de 1 Impressão (horas)", min_value=0.0, value=2.5)

        margem_lucro = st.slider("Margem de Lucro (%)", 0, 200, 30)
        calcular = st.form_submit_button("Calcular e Guardar", use_container_width=True)

    if calcular:
        if not nome_cliente:
            st.warning("⚠️ Insere o nome do Cliente/Projeto para guardar.")
        else:
            peso_total = peso_1_peca * numero_pecas
            tempo_total = tempo_1_impressao * numero_pecas
            
            # Cálculos usando as variáveis do CSV
            custo_mat = (peso_total / dados_mat["Peso_Bobina"]) * dados_mat["Preco_Bobina"]
            custo_ene = tempo_total * dados_mat["Consumo_kW"] * CUSTO_KWH
            custo_dep = tempo_total * (CUSTO_MAQUINA / VIDA_UTIL_HORAS)
            custo_trab = (TEMPO_SETUP * numero_pecas) * VALOR_HORA_SETUP

            custo_prod = custo_mat + custo_ene + custo_dep + custo_trab
            preco_final = custo_prod * (1 + (margem_lucro / 100))
            
            # Guardar Histórico
            novo_registo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Projeto": nome_cliente,
                "Material Usado": material_escolhido,
                "Quantidade": numero_pecas,
                "Custo Prod(€)": round(custo_prod, 2),
                "Preço Final(€)": round(preco_final, 2)
            }])
            
            if os.path.isfile(CSV_HISTORICO):
                df_hist = pd.concat([pd.read_csv(CSV_HISTORICO), novo_registo], ignore_index=True)
            else:
                df_hist = novo_registo
            df_hist.to_csv(CSV_HISTORICO, index=False)
            
            st.success(f"**Preço Final a Cobrar:** € {preco_final:.2f}")
            st.info(f"*(Custo de Produção Base: € {custo_prod:.2f})*")

# ==========================================
# SEPARADOR 2: GESTÃO DE INVENTÁRIO
# ==========================================
with tab2:
    st.subheader("Base de Dados de Filamentos")
    st.dataframe(df_materiais, use_container_width=True)
    
    st.markdown("#### Adicionar Novo Rolo ao Inventário")
    with st.form("add_material_form"):
        n_nome = st.text_input("Nome do Material (Marca/Cor)", placeholder="Ex: Esun PLA+ Preto")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            n_preco = st.number_input("Preço da Bobina (€)", min_value=0.0, value=25.0)
        with col_m2:
            n_peso = st.number_input("Peso da Bobina (g)", min_value=1.0, value=1000.0)
        with col_m3:
            n_consumo = st.number_input("Consumo Máquina (kW)", min_value=0.0, value=0.150, step=0.05)
        
        adicionar = st.form_submit_button("Guardar Novo Material", type="primary")
        
    if adicionar and n_nome:
        novo_mat = pd.DataFrame([{
            "Material": n_nome, 
            "Preco_Bobina": n_preco, 
            "Peso_Bobina": n_peso, 
            "Consumo_kW": n_consumo
        }])
        df_atualizado = pd.concat([df_materiais, novo_mat], ignore_index=True)
        df_atualizado.to_csv(CSV_MATERIAIS, index=False)
        st.success(f"Material '{n_nome}' adicionado com sucesso!")
        st.rerun() # Atualiza a página automaticamente para o material aparecer na tabela e na calculadora

# ==========================================
# SEPARADOR 3: HISTÓRICO
# ==========================================
with tab3:
    st.subheader("Histórico Financeiro")
    if os.path.isfile(CSV_HISTORICO):
        df_historico = pd.read_csv(CSV_HISTORICO)
        st.dataframe(df_historico, use_container_width=True)
        
        st.download_button(
            label="📥 Descarregar para Excel (CSV)",
            data=df_historico.to_csv(index=False).encode('utf-8'),
            file_name='faturacao_3d.csv',
            mime='text/csv'
        )
    else:
        st.info("Ainda não há orçamentos guardados. Eles aparecerão aqui.")
