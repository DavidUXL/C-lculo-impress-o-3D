import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Gestão Snapmaker U1", layout="centered", page_icon="🖨️")

CSV_HISTORICO = "historico_orcamentos.csv"
CSV_MATERIAIS = "base_materiais.csv"

if not os.path.isfile(CSV_MATERIAIS):
    pd.DataFrame([
        {"Material": "PLA Padrão", "Preco_Bobina": 20.0, "Peso_Bobina": 1000.0, "Consumo_kW": 0.350},
        {"Material": "PETG Padrão", "Preco_Bobina": 22.0, "Peso_Bobina": 1000.0, "Consumo_kW": 0.400},
        {"Material": "PVA (Suportes Solúveis)", "Preco_Bobina": 45.0, "Peso_Bobina": 500.0, "Consumo_kW": 0.350},
        {"Material": "PA-CF (Nylon Carbono)", "Preco_Bobina": 65.0, "Peso_Bobina": 500.0, "Consumo_kW": 0.450}
    ]).to_csv(CSV_MATERIAIS, index=False)

df_materiais = pd.read_csv(CSV_MATERIAIS)

# Constantes U1
CUSTO_KWH = 0.16
CUSTO_MAQUINA = 1300.0 # Valor ajustado para CoreXY c/ Toolchanger
VIDA_UTIL_HORAS = 8000.0
TEMPO_SETUP_BASE = 0.1 
VALOR_HORA_TRABALHO = 15.0

st.title("🖨️ Gestão Orçamentos: Snapmaker U1")
st.caption("Otimizado para a mecânica CoreXY e 4 Cabeças Independentes (SnapSwap™)")
st.divider()

tab1, tab2, tab3 = st.tabs(["⚡ Calculadora U1", "🛠️ Inventário", "📂 Histórico"])

with tab1:
    with st.form("orcamento_form"):
        st.subheader("📝 Dados do Projeto")
        col_proj1, col_proj2 = st.columns(2)
        with col_proj1:
            nome_cliente = st.text_input("Cliente / Projeto", placeholder="Ex: Peça Mecânica PVA+PA-CF")
        with col_proj2:
            numero_pecas = st.number_input("Quantidade", min_value=1, value=1)

        st.subheader("🎨 Configuração de Cabeças (Multi-Material)")
        st.info("A U1 suporta até 4 cabeças. Aloca o peso a cada extrusor usado.")
        
        num_cabecas = st.slider("Quantas cabeças vais usar nesta impressão?", 1, 4, 1)
        
        lista_materiais = df_materiais["Material"].tolist()
        
        pesos_por_cabeca = []
        materiais_usados = []
        custo_materiais_total = 0.0
        consumo_kw_medio = 0.0
        
        for i in range(num_cabecas):
            c1, c2 = st.columns(2)
            with c1:
                mat = st.selectbox(f"Extrusor {i+1} (Material)", lista_materiais, key=f"mat_{i}")
                materiais_usados.append(mat)
            with c2:
                peso = st.number_input(f"Peso Usado (g)", min_value=0.0, value=50.0 if i==0 else 0.0, step=5.0, key=f"peso_{i}")
                pesos_por_cabeca.append(peso)
                
            dados_m = df_materiais[df_materiais["Material"] == mat].iloc[0]
            custo_materiais_total += (peso / dados_m["Peso_Bobina"]) * dados_m["Preco_Bobina"]
            consumo_kw_medio += dados_m["Consumo_kW"]
        
        consumo_final_kw = consumo_kw_medio / num_cabecas
        
        st.markdown("##### Torre de Purga / Desperdício")
        peso_torre_purga = st.number_input("Peso de Desperdício da Torre (g)", min_value=0.0, value=0.0, step=1.0, help="Ao trocar de cabeça (SnapSwap), o peso gasto na torre de purga.")
        
        custo_medio_g = custo_materiais_total / sum(pesos_por_cabeca) if sum(pesos_por_cabeca) > 0 else 0
        custo_materiais_total += (peso_torre_purga * custo_medio_g)
        
        st.subheader("📦 Tempos e Risco")
        colA, colB = st.columns(2)
        with colA:
            tempo_1_impressao = st.number_input("Tempo Total (h)", min_value=0.0, value=2.5)
            taxa_falha = st.number_input("Risco de Falha/Refugo (%)", min_value=0, max_value=100, value=2, help="A U1 tem calibração precisa, mas materiais como ABS/PA requerem margem de erro.")
        with colB:
            tempo_pos = st.number_input("Tempo de Pós-Processamento (h)", min_value=0.0, value=0.0, step=0.1, help="Ex: Tempo a dissolver PVA ou remover suportes densos.")
            margem_lucro = st.slider("Margem de Lucro (%)", 0, 200, 30)
            
        calcular = st.form_submit_button("Calcular e Guardar (U1)", use_container_width=True)

    if calcular:
        if not nome_cliente:
            st.warning("⚠️ Insere o nome do Cliente para guardar.")
        else:
            tempo_total = tempo_1_impressao * numero_pecas
            multiplicador_falha = 1 + (taxa_falha / 100)
            
            custo_mat_final = (custo_materiais_total * numero_pecas) * multiplicador_falha
            custo_ene_final = (tempo_total * consumo_final_kw * CUSTO_KWH) * multiplicador_falha
            custo_dep_final = (tempo_total * multiplicador_falha) * (CUSTO_MAQUINA / VIDA_UTIL_HORAS)
            
            # Setup extra: carregar 4 filamentos dá mais trabalho que 1
            tempo_setup_real = TEMPO_SETUP_BASE + (0.05 * num_cabecas) 
            custo_trab_final = ((tempo_setup_real * numero_pecas) + tempo_pos) * VALOR_HORA_TRABALHO

            custo_prod_total = custo_mat_final + custo_ene_final + custo_dep_final + custo_trab_final
            preco_final = custo_prod_total * (1 + (margem_lucro / 100))
            
            mat_str = " | ".join(set(materiais_usados))
            
            novo_registo = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Projeto": nome_cliente,
                "Materiais Usados": mat_str,
                "Qtd": numero_pecas,
                "Custo Prod(€)": round(custo_prod_total, 2),
                "Preço Final(€)": round(preco_final, 2)
            }])
            
            if os.path.isfile(CSV_HISTORICO):
                df_hist = pd.concat([pd.read_csv(CSV_HISTORICO), novo_registo], ignore_index=True)
            else:
                df_hist = novo_registo
            df_hist.to_csv(CSV_HISTORICO, index=False)
            
            st.success(f"**Preço Final a Cobrar ao Cliente:** € {preco_final:.2f}")
            
            # --- ADIÇÃO DAS LEGENDAS E FÓRMULAS ---
            st.write("📊 **Breakdown de Custos de Produção (Lote Total):**")
            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            
            col_res1.metric(
                "Material + Purga", 
                f"€ {custo_mat_final:.2f}",
                help="Soma do custo de cada filamento pelo seu peso + o custo da torre de purga, ajustado pela margem de risco."
            )
            col_res2.metric(
                "Energia", 
                f"€ {custo_ene_final:.2f}",
                help=f"Tempo Total × Consumo Médio Máquina ({consumo_final_kw:.3f} kW) × Preço kWh (€{CUSTO_KWH}), ajustado pelo risco."
            )
            col_res3.metric(
                "Máquina (Desgaste)", 
                f"€ {custo_dep_final:.2f}",
                help=f"Depreciação: Tempo de Impressão × (Custo U1: €{CUSTO_MAQUINA} / Vida Útil: {VIDA_UTIL_HORAS}h)."
            )
            col_res4.metric(
                "Mão de Obra", 
                f"€ {custo_trab_final:.2f}",
                help=f"Setup ({tempo_setup_real:.2f}h por peça) + Pós-Processamento ({tempo_pos}h) × Valor/Hora (€{VALOR_HORA_TRABALHO})."
            )
            
            with st.expander("Ver descritivo matemático completo"):
                st.markdown(f"""
                **1. Material:** Custo Base + Desperdício Torre = €{custo_materiais_total:.2f} / peça. Multiplicado por {numero_pecas} peças e adicionado o risco de falha ({taxa_falha}%).
                **2. Energia:** {tempo_total}h totais × {consumo_final_kw:.3f} kW/h × €{CUSTO_KWH}/kWh × Multiplicador de risco.
                **3. Depreciação:** {tempo_total}h totais × (€{CUSTO_MAQUINA} / {VIDA_UTIL_HORAS}h) × Multiplicador de risco.
                **4. Mão de Obra:** Setup inicial ajustado a {num_cabecas} cabeça(s) = {tempo_setup_real:.2f}h × {numero_pecas} peças, mais {tempo_pos}h de pós-processamento, a €{VALOR_HORA_TRABALHO}/hora.
                """)

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
            n_consumo = st.number_input("Consumo (kW)", min_value=0.0, value=0.350, step=0.05)
            if st.form_submit_button("Guardar Material", type="primary") and n_nome:
                novo_mat = pd.DataFrame([{"Material": n_nome, "Preco_Bobina": n_preco, "Peso_Bobina": n_peso, "Consumo_kW": n_consumo}])
                df_atualizado = pd.concat([df_materiais, novo_mat], ignore_index=True)
                df_atualizado.to_csv(CSV_MATERIAIS, index=False)
                st.success("Adicionado!")
                st.rerun()
                
    with col_del:
        st.markdown("#### 🗑️ Apagar")
        with st.form("del_material_form"):
            mat_apagar = st.selectbox("Selecionar rolo", df_materiais["Material"].tolist())
            if st.form_submit_button("Remover"):
                if len(df_materiais) > 1:
                    df_atualizado = df_materiais[df_materiais["Material"] != mat_apagar]
                    df_atualizado.to_csv(CSV_MATERIAIS, index=False)
                    st.warning("Removido!")
                    st.rerun()
                else:
                    st.error("Não podes apagar o último.")

with tab3:
    st.subheader("Histórico Financeiro (U1)")
    if os.path.isfile(CSV_HISTORICO):
        df_historico = pd.read_csv(CSV_HISTORICO)
        st.dataframe(df_historico, use_container_width=True)
        st.download_button(
            label="📥 Descarregar para Excel (CSV)",
            data=df_historico.to_csv(index=False).encode('utf-8'),
            file_name='faturacao_3d_u1.csv',
            mime='text/csv'
        )
    else:
        st.info("Ainda não há orçamentos guardados.")
