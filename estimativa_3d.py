import streamlit as st

st.set_page_config(page_title="Estimativa Rápida 3D", layout="centered")

st.title("⚡ Estimativa Rápida de Orçamento 3D")
st.markdown("Insira os parâmetros abaixo para calcular o preço final estimado para o cliente.")

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

# Nova Secção: Seleção de Material
st.subheader("⚙️ Configuração do Material")
material_selecionado = st.selectbox("Escolha o tipo de filamento:", list(MATERIAIS.keys()))

# Carregar os valores por defeito da base de dados
preco_base = MATERIAIS[material_selecionado]["preco"]
peso_base = MATERIAIS[material_selecionado]["peso"]
consumo_base = MATERIAIS[material_selecionado]["consumo"]

# Layout de 3 colunas para permitir ajuste manual caso o rolo específico seja diferente
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

# Cálculos Totais
peso_total = peso_1_peca * numero_pecas
tempo_total = tempo_1_impressao * numero_pecas
tempo_setup_total = TEMPO_SETUP_POR_PECA * numero_pecas

# Custos atualizados com as variáveis dinâmicas
custo_material = (peso_total / peso_bobina) * preco_bobina
custo_energia = tempo_total * consumo_impressora * CUSTO_KWH
custo_depreciacao = tempo_total * (CUSTO_MAQUINA / VIDA_UTIL_HORAS)
custo_trabalho = tempo_setup_total * VALOR_HORA_SETUP

custo_producao = custo_material + custo_energia + custo_depreciacao + custo_trabalho
preco_final = custo_producao * (1 + (margem_lucro / 100))

st.divider()
st.subheader("💰 Estimativa Final")

col_a, col_b = st.columns(2)
with col_a:
    st.info(f"**Custo de Produção (Total):** € {custo_producao:.2f}")
    st.markdown(f"- Material: € {custo_material:.2f}")
    st.markdown(f"- Energia: € {custo_energia:.2f}")
    st.markdown(f"- Depreciação: € {custo_depreciacao:.2f}")
    st.markdown(f"- Mão de Obra (Setup): € {custo_trabalho:.2f}")
with col_b:
    st.success(f"**Preço a Cobrar ao Cliente:** € {preco_final:.2f}")
    st.markdown(f"*(Inclui margem de {margem_lucro}%)*")
    
st.caption(f"Tempo total de máquina estimado: {tempo_total:.1f} horas | Material total: {peso_total:.1f}g")
