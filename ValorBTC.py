import yfinance as yf
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from winotify import Notification, audio
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime

# Caminho do WebDriver (Edge)
EDGE_DRIVER_PATH = "C:/WebDriver/msedgedriver.exe"

# Configuração do WebDriver
options = Options()
options.add_experimental_option("detach", True)  # Mantém o navegador aberto

# Iniciar o WebDriver
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=options)

# Função para abrir o WhatsApp Web
def iniciar_whatsapp():
    driver.get("https://web.whatsapp.com/")
    print("Escaneie o QR Code para continuar...")
    time.sleep(15)  # Tempo para escanear o QR Code

# Função para enviar mensagem no WhatsApp
def enviar_mensagem(numero, mensagem):
    url = f"https://web.whatsapp.com/send?phone={numero}&text={mensagem}"
    driver.get(url)
    time.sleep(10)  # Tempo para carregar a página
    
    try:
        wait = WebDriverWait(driver, 20)
        botao_enviar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Enviar']")))
        botao_enviar.click()
        print(f"Mensagem enviada para {numero}")
    except Exception as e:
        print(f"Erro ao enviar mensagem para {numero}: {e}")

# Dicionário para armazenar o último horário de alerta por ativo
ultimo_alerta = {}
COOLDOWN = 30  # 30 segundos de cooldown

# Função para emitir o alerta no Windows e WhatsApp
def emitir_alerta(ativo, valor_atual):
    global ultimo_alerta
    
    agora = datetime.datetime.now()
    
    # Verifica se já passou o cooldown
    if ativo not in ultimo_alerta or (agora - ultimo_alerta[ativo]).total_seconds() >= COOLDOWN:
        # Mensagem formatada com o nome do ativo e o valor atual
        mensagem = f"🚨 Alerta de Mercado! 🚨\n\n"
        mensagem += f"Ativo: {ativo}\n"
        mensagem += f"Valor Atual: {valor_atual:.2f}\n"
        mensagem += f"O preço está abaixo da Banda Inferior! Verifique o mercado."

        # Notificação aprimorada no Windows
        toast = Notification(
            app_id="Alerta de Mercado",
            title="📢 Alerta de Ativo!",
            msg=mensagem,
            icon="C:/caminho/para/seu/icone.ico"  # Opcional: ícone da notificação
        )
        
        # Adiciona som e botão na notificação
        toast.set_audio(audio.Default, loop=False)
        toast.add_actions(label="📈 Abrir Gráfico", launch="http://127.0.0.1:8050")
        toast.show()

        # Enviar alerta no WhatsApp
        numero = "5521984195580"  # Número no formato internacional
        enviar_mensagem(numero, mensagem)
        
        # Atualiza o horário do último alerta
        ultimo_alerta[ativo] = agora

# Função para obter os dados, calcular as bandas e verificar pontos de compra/venda
def calcular_bandas(ativo):
    acao = yf.Ticker(ativo)
    data = acao.history(period="2y")
    df = data[['Close']]
    mm = df.rolling(window=20).mean()
    dpm = df.rolling(window=20).std()
    sup_band = mm + 2 * dpm
    inf_band = mm - 2 * dpm
    sup_band = sup_band.rename(columns={'Close': 'superior'})
    inf_band = inf_band.rename(columns={'Close': 'inferior'})
    bandas_bollinger = df.join(sup_band).join(inf_band).dropna()
    compra = bandas_bollinger[bandas_bollinger['Close'] <= bandas_bollinger['inferior']]
    venda = bandas_bollinger[bandas_bollinger['Close'] >= bandas_bollinger['superior']]
    return df, mm, sup_band, inf_band, compra, venda

# Lista de ativos para monitorar
ativos = ["BTC-USD", "TVRI11.SA","HGLG11.SA", "BTLG11.SA", "CXSE3.SA", "GARE11.SA", "TRXF11.SA", "KNSC11.SA", "KNCA11.SA", "HGRU11.SA", "KNCR11.SA" , "EGIE3.SA", "BBAS3.SA", "XPLG11.SA", "PVBI11.SA", "MALL11.SA", "IRDM11.SA", "MXRF11.SA", "BCRI11.SA", "KNIP11.SA"]

# Função para gerar IDs válidos para o Dash
def gerar_id_valido(ativo):
    return ativo.replace(".", "_")  # Substitui pontos por sublinhados

# Salvar a hora de início
hora_inicio = datetime.datetime.now()

# Função para calcular o tempo de execução
def calcular_tempo_execucao():
    tempo_atual = datetime.datetime.now()
    delta = tempo_atual - hora_inicio
    return str(delta).split(".")[0]  # Remove os milissegundos

# Iniciar o WhatsApp Web
iniciar_whatsapp()

# Iniciar o aplicativo Dash
app = dash.Dash(__name__)

# Layout do Dash
app.layout = html.Div([
    html.H1("Monitor de Ativos"),
    html.H3(id='hora-inicio', children=f"Iniciado às: {hora_inicio.strftime('%H:%M:%S')}"),
    html.H3(id='tempo-execucao', children="Tempo rodando: 00:00:00"),
    
    # Gráficos para cada ativo
    html.Div([
        dcc.Graph(id=gerar_id_valido(f'grafico-{ativo}')) for ativo in ativos
    ]),
    
    # Intervalo para atualizar os gráficos a cada 10 segundos
    dcc.Interval(
        id='intervalo-atualizacao',
        interval=10*1000,  # 10 segundos para atualizar os gráficos
        n_intervals=0
    ),
    
    # Intervalo para enviar mensagem a cada 1 Hora
    dcc.Interval(
        id='intervalo-enviar-mensagem',
        interval=3600000,  # 1 Hora em milissegundos
        n_intervals=0
    ),
    
    # Intervalo para atualizar o tempo de execução
    dcc.Interval(
        id='intervalo-tempo',  
        interval=1000,  # Atualiza a cada 1 segundo
        n_intervals=0
    ),
])

# Callback para atualizar os gráficos
@app.callback(
    [Output(gerar_id_valido(f'grafico-{ativo}'), 'figure') for ativo in ativos],
    [Input('intervalo-atualizacao', 'n_intervals')]
)
def atualizar_graficos(n_intervals):
    figuras = []
    for ativo in ativos:
        df, mm, sup_band, inf_band, compra, venda = calcular_bandas(ativo)
        
        # Verificar se o preço está abaixo da banda inferior
        if df['Close'].iloc[-1] <= inf_band['inferior'].iloc[-1]:
            valor_atual = df['Close'].iloc[-1]  # Pega o valor atual do ativo
            emitir_alerta(ativo, valor_atual)  # Passa o nome do ativo e o valor atual

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=inf_band.index, y=inf_band['inferior'], name='Banda Inferior', line_color='rgba(173,204,255,0.2)'))
        fig.add_trace(go.Scatter(x=sup_band.index, y=sup_band['superior'], name='Banda Superior', fill='tonexty', fillcolor='rgba(173,204,255,0.2)', line_color='rgba(173,204,255,0.2)'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Preço Fechamento', line_color='#636EFA'))
        fig.add_trace(go.Scatter(x=mm.index, y=mm['Close'], name='Média Móvel', line_color='#FECB52'))
        fig.add_trace(go.Scatter(x=compra.index, y=compra['Close'], name='Compra', mode='markers', marker=dict(color='#00CC96', size=8)))
        fig.add_trace(go.Scatter(x=venda.index, y=venda['Close'], name='Venda', mode='markers', marker=dict(color='#EF553B', size=8)))
        
        fig.update_layout(title=f"Gráfico Bollinger Bands - {ativo}", xaxis_title="Data", yaxis_title="Preço", template="plotly_dark")
        figuras.append(fig)
    
    return figuras

# Callback para enviar mensagem a cada 1 hora
@app.callback(
    Output('intervalo-enviar-mensagem', 'n_intervals'),
    [Input('intervalo-enviar-mensagem', 'n_intervals')]
)
def enviar_mensagem_periodica(n_intervals):
    print(f"Callback de mensagem periódica acionado. Intervalo: {n_intervals}")
    if n_intervals > 0:  # Envia uma vez a cada 1 hora
        mensagem = "✅ O sistema ainda está rodando. Tudo certo!"
        numero = "5521984195580"  # Número no formato internacional
        enviar_mensagem(numero, mensagem)  # Envia a mensagem diretamente
        print("Mensagem de teste enviada: 'O sistema ainda está rodando.'")
    
    return n_intervals + 1

# Callback para atualizar o tempo de execução
@app.callback(
    Output('tempo-execucao', 'children'),
    Input('intervalo-tempo', 'n_intervals')
)
def atualizar_tempo(n):
    return f"Tempo rodando: {calcular_tempo_execucao()}"

# Rodando o servidor Dash
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)