import pandas as pd
import requests
import time
import random
# Configurações
arquivo = "prospects_com_whatsapp_atualizado.xlsx"
coluna_telefone = "whatsapp_validado"
coluna_nome = "nome"

url_base = "http://localhost:3000/client/sendMessage"
session_id = "ABCD"  # Substitua pelo ID real da sessão
url_envio = f"{url_base}/{session_id}"

# Função para montar payload da mensagem
def montar_payload(telefone, texto):
    return {
        "chatId": f"{telefone}@c.us",  # formato correto para usuários individuais
        "contentType": "string",
        "content": texto
    }

# Função para criar mensagem personalizada
def montar_mensagem_padrao(nome_do_local):
    return f"Olá {nome_do_local},\n\nTESTE de envio automático via API 🚀"

# Leitura da planilha
df = pd.read_excel(arquivo)

# Itera linha a linha
for _, row in df.iterrows():
    telefone = str(row[coluna_telefone]).strip()
    nome = str(row[coluna_nome]).strip()

    mensagem_padrao = montar_mensagem_padrao(nome)
    payload = montar_payload(telefone, mensagem_padrao)

    try:
        resp = requests.post(url_envio, json=payload)

        print(f"[{telefone}] ({nome}) → {resp.status_code}: {resp.text}")
        time.sleep(random.randint(5,15))
    except Exception as e:
        print(f"[{telefone}] ({nome}) → Erro: {e}")