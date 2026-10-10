import streamlit as st

st.set_page_config(page_title="Estimativa Rápida 3D", layout="centered")

st.title("⚡ Estimativa Rápida de Orçamento 3D")
st.markdown("Insira os parâmetros abaixo para calcular o preço final estimado para o cliente.")

# Constantes da Empresa (podem ser alteradas aqui)
PRECO_BOBINA = 25.0  # €
PESO_BOBINA = 1000.0 # g
CUSTO_KWH = 0.16     # €
CONSUMO_IMPRESSORA = 0.250 # kW (250W)
CUSTO_MAQUINA = 800.0
VIDA_UTIL_HORAS = 8000.0
TEMPO_SETUP_POR_PECA = 0.1 # horas (6 minutos por peça para tirar da mesa e limpar)
VALOR_HORA_SETUP = 15.0 # €
MARGEM_LUCRO_DEFAULT = 30 # %

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Parâmetros do Pedido")
    peso_1_peca = st.number_input("Peso de 1 Peça (gramas)", min_value=0.0, value=50.0, step=1.0)
    tempo_1_impressao = st.number_input("Tempo de 1 Impressão (horas)", min_value=0.0, value=2.5, step=0.5)

with col2:
    st.subheader("Volume e Margem")
    numero_pecas = st.number_input("Número de Peças", min_value=1, value=1, step=1)
    margem_lucro = st.slider("Margem de Lucro (%)", min_value=0, max_value=200, value=MARGEM_LUCRO_DEFAULT)

# Cálculos Totais
peso_total = peso_1_peca * numero_pecas
tempo_total = tempo_1_impressao * numero_pecas
tempo_setup_total = TEMPO_SETUP_POR_PECA * numero_pecas

# Custos
custo_material = (peso_total / PESO_BOBINA) * PRECO_BOBINA
custo_energia = tempo_total * CONSUMO_IMPRESSORA * CUSTO_KWH
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
    st.markdown(f"- Mão de Obra (Setup/Limpeza): € {custo_trabalho:.2f}")
with col_b:
    st.success(f"**Preço a Cobrar ao Cliente:** € {preco_final:.2f}")
    st.markdown(f"*(Inclui margem de {margem_lucro}%)*")
    
st.caption(f"Tempo total de máquina estimado: {tempo_total:.1f} horas | Material total: {peso_total:.1f}g")
