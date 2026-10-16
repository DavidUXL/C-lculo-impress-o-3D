import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Gestão 3D", layout="centered", page_icon="🖨️")

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

df_materiais = pd.read_csv(CSV_MATERIAIS)

# 3. Constantes Fixas da Máquina/Empresa
CUSTO_KWH = 0.16
CUSTO_MAQUINA = 800.0
VIDA_UTIL_HORAS = 8000.0
TEMPO_SETUP = 0.1 # 6 min preparacao base por peça
VALOR_HORA_TRABALHO = 15.0

st.title("🖨️ Gestão de Orçamentos 3D")
st.divider()

tab1, tab2, tab3 = st.tabs(["⚡ Calculadora", "🛠️ Inventário", "📂 Histórico"])

# ==========================================
# SEPARADOR 1: CALCULADORA
# ==========================================
with tab1:
    with st.form("orcamento_form"):
        st.subheader("📝 Dados do Projeto")
        col_proj1, col_proj2 = st.columns(2)
        with col_proj1:
            nome_cliente = st.text_input("Cliente / Projeto", placeholder="Ex: Engrenagem PA-CF v2")
        with col_proj2:
            numero_pecas = st.number_input("Quantidade de Peças", min_value=1, value=1)

        st.subheader("⚙️ Produção e Material")
        lista_materiais = df_materiais["Material"].tolist()
        material_escolhido = st.selectbox("Escolhe o filamento da tua base:", lista_materiais)
        dados_mat = df_materiais[df_materiais["Material"] == material_escolhido].iloc[0]

        colA, colB = st.columns(2)
        with colA:
            peso_1_peca = st.number_input("Peso de 1 Peça (g)", min_value=0.0, value=50.0)
        with colB:
            tempo_1_impressao = st.number_input("Tempo de 1 Impressão (h)", min_value=0.0, value=2.5)

        # NOVA SECÇÃO: Engenharia e Risco
        st.subheader("🔧 Engenharia e Risco")
        col_eng1, col_eng2 = st.columns(2)
        with col_eng1:
            tempo_pos = st.number_input("Pós-processamento Total (h)", min_value=0.0, value=0.0, step=0.1, help="Tempo a remover suportes, lixar ou cravar inserts térmicos.")
        with col_eng2:
            taxa_falha = st.number_input("Taxa de Refugo/Falha (%)", min_value=0, max_value=100, value=5, help="Margem para absorver peças que falham (warping, entupimentos).")

        margem_lucro = st.slider("Margem de Lucro Comercial (%)", 0, 200, 30)
        calcular = st.form_submit_button("Calcular e Guardar", use_container_width=True)

    if calcular:
        if not nome_cliente:
            st.warning("⚠️ Insere o nome do Cliente/Projeto para guardar.")
        else:
            peso_total = peso_1_peca * numero_pecas
            tempo_total = tempo_1_impressao * numero_pecas
            
            # Cálculos Base com aplicação da Taxa de Falha
            multiplicador_falha = 1 + (taxa_falha / 100)
            
            custo_mat = ((peso_total / dados_mat["Peso_Bobina"]) * dados_mat["Preco_Bobina"]) * multiplicador_falha
            custo_ene = (tempo_total * dados_mat["Consumo_kW"] * CUSTO_KWH) * multiplicador_falha
            custo_dep = (tempo_total * multiplicador_falha) * (CUSTO_MAQUINA / VIDA_UTIL_HORAS)
            
            # Trabalho = Setup inicial por peça + Pós-processamento geral do lote
            custo_trab = ((TEMPO_SETUP * numero_pecas) + tempo_pos) * VALOR_HORA_TRABALHO

            custo_prod = custo_mat + custo_ene + custo_dep + custo_trab
            preco_final = custo_prod * (1 + (margem_lucro / 100))
            
            # Guardar Histórico
            novo_registo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Projeto": nome_cliente,
                "Material": material_escolhido,
                "Qtd": numero_pecas,
                "Custo Prod(€)": round(custo_prod, 2),
                "Preço Final(€)": round(preco_final, 2)
            }])
            
            if os.path.isfile(CSV_HISTORICO):
                df_hist = pd.concat([pd.read_csv(CSV_HISTORICO), novo_registo], ignore_index=True)
            else:
                df_hist = novo_registo
            df_hist.to_csv(CSV_HISTORICO, index=False)
            
            st.success(f"**Preço Final a Cobrar ao Cliente:** € {preco_final:.2f}")
            
            # NOVO: Breakdown Visual de Custos
            st.write("📊 **Breakdown de Custos de Produção:**")
            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            col_res1.metric("Material", f"€ {custo_mat:.2f}")
            col_res2.metric("Energia", f"€ {custo_ene:.2f}")
            col_res3.metric("Máquina", f"€ {custo_dep:.2f}")
            col_res4.metric("Mão de Obra", f"€ {custo_trab:.2f}")

# ==========================================
# SEPARADOR 2: GESTÃO DE INVENTÁRIO
# ==========================================
with tab2:
    st.subheader("Base de Dados de Filamentos")
    st.dataframe(df_materiais, use_container_width=True)
    
    st.divider()
    col_add, col_del = st.columns(2)
    
    with col_add:
        st.markdown("#### ➕ Adicionar")
        with st.form("add_material_form"):
            n_nome = st.text_input("Marca/Cor")
            n_preco = st.number_input("Preço (€)", min_value=0.0, value=25.0)
            n_peso = st.number_input("Peso (g)", min_value=1.0, value=1000.0)
            n_consumo = st.number_input("Consumo (kW)", min_value=0.0, value=0.150, step=0.05)
            if st.form_submit_button("Guardar Material", type="primary") and n_nome:
                novo_mat = pd.DataFrame([{"Material": n_nome, "Preco_Bobina": n_preco, "Peso_Bobina": n_peso, "Consumo_kW": n_consumo}])
                df_atualizado = pd.concat([df_materiais, novo_mat], ignore_index=True)
                df_atualizado.to_csv(CSV_MATERIAIS, index=False)
                st.success("Adicionado com sucesso!")
                st.rerun()
                
    # NOVA SECÇÃO: Apagar Materiais
    with col_del:
        st.markdown("#### 🗑️ Apagar")
        with st.form("del_material_form"):
            mat_apagar = st.selectbox("Selecionar rolo a remover", df_materiais["Material"].tolist())
            if st.form_submit_button("Remover Material"):
                if len(df_materiais) > 1:
                    df_atualizado = df_materiais[df_materiais["Material"] != mat_apagar]
                    df_atualizado.to_csv(CSV_MATERIAIS, index=False)
                    st.warning(f"'{mat_apagar}' removido do inventário!")
                    st.rerun()
                else:
                    st.error("Não podes apagar o último material da lista.")

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
