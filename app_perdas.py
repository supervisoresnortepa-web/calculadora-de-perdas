import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Calculadora de Perdas", page_icon="⚡", layout="centered")

# Dicionários com os códigos
codigos_negativos = {
    "B07": -1, "C13": -1, "C15": -1, "D04": -1, 
    "E01": -1, "E03": -1, "E04": -1, "E08": -1
}

codigos_positivos = {
    "B01": 1, "B02": 1, "B03": 1, "B05": 1, "B06": 1, "B12": 1, "B17": 1, "B18": 1,
    "C04": 1, "C05": 1, "C06": 1, "C07": 1, "C09": 1, "C11": 1, "C12": 1, "C14": 1, "C16": 1,
    "D01": 1, "D03": 1, "D05": 1, "D06": 1,
    "E02": 1, "E11": 1, "F02": 1, "F03": 1
}

todos_codigos = {**codigos_negativos, **codigos_positivos}
# Adicionando a opção LIDO com valor 0
todos_codigos["LIDO"] = 0 

lista_codigos = ["Selecione..."] + sorted(list(todos_codigos.keys()))

st.title("⚡ Diagnóstico de Perdas em kWh")
st.divider()

# --- INÍCIO DA NOVA MELHORIA: PESQUISA DE INSTALAÇÃO ---
st.subheader("🔍 Consulta de Perda Prevista")
st.markdown("Digite o número da instalação para verificar a perda prevista na base deste mês.")

# Função para carregar a base de dados
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel('base_perdas.xlsx')
        
        # Converte a coluna INSTALACAO para texto, remove '.0' e IGNORA ZEROS À ESQUERDA
        if 'INSTALACAO' in df.columns:
            df['INSTALACAO'] = df['INSTALACAO'].astype(str).str.replace(r'\.0$', '', regex=True).str.lstrip('0')
            
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df_base = carregar_dados()

instalacao_input = st.text_input("Número da Instalação (Ex: 36218):")

if instalacao_input:
    # Remove também os zeros à esquerda do que o usuário digitar na caixinha, por segurança
    instalacao_input_limpo = instalacao_input.lstrip('0')

    if df_base is not None:
        # ATUALIZADO: Nome da coluna alterado para PERDA_PREVISTA_MENSAL
        colunas_necessarias = ['INSTALACAO', 'STATUS_PERDA', 'PERDA_PREVISTA_MENSAL']
        
        if all(col in df_base.columns for col in colunas_necessarias):
            
            # Limpa espaços em branco que possam vir da planilha
            df_base['STATUS_PERDA'] = df_base['STATUS_PERDA'].astype(str).str.strip().str.upper()
            
            # Filtra pela instalação digitada E pelo STATUS_PERDA
            resultado = df_base[
                (df_base['INSTALACAO'] == instalacao_input_limpo) & 
                (df_base['STATUS_PERDA'].isin(['COM PERDA', 'COMPERDA']))
            ]
            
            if not resultado.empty:
                # ATUALIZADO: Pega o valor da nova coluna
                perda = resultado['PERDA_PREVISTA_MENSAL'].values[0]
                st.success(f"⚠️ A instalação **{instalacao_input_limpo}** possui o status COM PERDA e uma previsão de **{perda} kW**.")
            else:
                # Se achou a instalação mas ela NÃO tem perda
                tem_instalacao = df_base[df_base['INSTALACAO'] == instalacao_input_limpo]
                if not tem_instalacao.empty:
                    st.info(f"✅ A instalação **{instalacao_input_limpo}** foi encontrada, mas NÃO possui status de 'COM PERDA' ativo.")
                else:
                    st.warning(f"A instalação **{instalacao_input_limpo}** não foi encontrada na base de dados.")
        else:
             st.error("⚠️ As colunas 'INSTALACAO', 'STATUS_PERDA' e/ou 'PERDA_PREVISTA_MENSAL' não foram encontradas na planilha. Verifique os nomes dos cabeçalhos.")
    else:
        st.error("⚠️ Arquivo 'base_perdas.xlsx' não encontrado no repositório. Faça o upload da planilha no GitHub.")

st.divider()
# --- FIM DA NOVA MELHORIA ---

# 1. Seleção do Status do Cliente
st.subheader("1️⃣ Status Atual do Cliente")
status_cliente = st.radio(
    "Como o cliente se encontra hoje?",
    ["Ligado (LG)", "Cortado (CR)", "Religado (Saiu de CR para LG no mês atual)"],
    index=0
)

st.divider()

# 2. Histórico de Apontamentos
st.subheader("2️⃣ Preencha o histórico de apontamentos")
st.markdown("Se a leitura foi normal em algum mês, selecione a opção **LIDO**.")

resp_m2 = st.selectbox("Qual foi o código apontado há 2 meses (Mês -2)?", lista_codigos)
resp_m1 = st.selectbox("Qual foi o código apontado no mês passado (Mês -1)?", lista_codigos)
resp_atual = st.selectbox("Qual código você quer simular para o mês atual?", lista_codigos)

st.write("")

# Botão de cálculo
if st.button("Gerar Diagnóstico", type="primary"):
    if "Selecione..." in [resp_m2, resp_m1, resp_atual]:
        st.warning("⚠️ Por favor, responda a todas as 3 perguntas selecionando um código válido ou LIDO.")
    else:
        # Pega os valores
        val_m2 = todos_codigos[resp_m2]
        val_m1 = todos_codigos[resp_m1]
        val_atual = todos_codigos[resp_atual]
        
        # Faz a soma da regra padrão
        soma = val_m2 + val_m1 + val_atual
        
        st.divider()
        st.subheader("📊 Resultado do Diagnóstico")
        
        # Exibe a memória de cálculo padrão
        st.markdown(f"**Cálculo dos Pesos:** `{val_m2}` + `{val_m1}` + `{val_atual}` = **`{soma}`**")
        
        # LOGICA DE NEGOCIO
        if status_cliente == "Cortado (CR)":
            if (resp_m1 == "LIDO" or resp_m2 == "LIDO") and resp_atual == "D01":
                st.error("🚨 **DIAGNÓSTICO: COM PERDA (EXCEÇÃO DE FATURAMENTO)**")
                st.info("Motivo: Embora o cliente esteja CR, ele possui um histórico recente de LIDO e o apontamento atual (D01) aciona a regra de faturamento pelo MÍNIMO.")
            else:
                st.success("✅ **DIAGNÓSTICO: SEM PERDA**")
                st.info("Motivo: Clientes com status CR (Cortado) não geram perda em kWh, independentemente de a soma ser positiva ou negativa.")
                
        else:
            if soma > 0:
                st.error("🚨 **DIAGNÓSTICO: COM PERDA**")
                if status_cliente == "Religado (Saiu de CR para LG no mês atual)":
                    st.info("Motivo: O cliente foi religado, portanto a regra padrão volta a se aplicar. A soma dos 3 apontamentos resultou em um número positivo.")
                else:
                    st.info("Motivo: A soma dos 3 apontamentos resultou em um número positivo.")
            else:
                st.success("✅ **DIAGNÓSTICO: SEM PERDA**")
                st.info("Motivo: A soma dos 3 apontamentos resultou em zero ou negativo.")