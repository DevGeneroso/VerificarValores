from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
import time

# Caminho do WebDriver do Edge
EDGE_DRIVER_PATH = r"C:\WebDriver\msedgedriver.exe"

def enviar_mensagem_whatsapp(numero, mensagem):
    """Envia uma mensagem via WhatsApp Web usando Microsoft Edge e Selenium."""
    
    # Configurações do Edge WebDriver
    options = webdriver.EdgeOptions()
    options.add_experimental_option("detach", True)  # Mantém o navegador aberto

    # Configuração do serviço do WebDriver
    service = Service(EDGE_DRIVER_PATH)
    driver = webdriver.Edge(service=service, options=options)  # 🚀 Correto!

    # Acessa o WhatsApp Web
    driver.get("https://web.whatsapp.com")
    print("Escaneie o QR Code do WhatsApp Web, se necessário.")
    time.sleep(15)  # Tempo para escanear o QR Code

    # Monta a URL do WhatsApp com a mensagem
    url = f"https://web.whatsapp.com/send?phone=55{numero}&text={mensagem}"
    driver.get(url)
    time.sleep(10)

    try:
        # Encontra a caixa de texto e envia a mensagem
        input_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        input_box.send_keys(Keys.ENTER)
        print("Mensagem enviada com sucesso!")

    except Exception as e:
        print("Erro ao enviar a mensagem:", e)

    # Fecha o navegador após o envio
    time.sleep(5)
    driver.quit()

# Teste manual (REMOVA ESTA PARTE NO CÓDIGO FINAL)
if __name__ == "__main__":
    enviar_mensagem_whatsapp("21984195580", "Teste de mensagem automática pelo WhatsApp Web.")