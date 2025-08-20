import os
from dotenv import load_dotenv
load_dotenv()

# Importar função de envio do seu main.py
from main import enviar_whatsapp

def teste_envio_whatsapp():
    """Teste de envio para seu próprio número"""
    
    # SEU NÚMERO DE WHATSAPP (substitua)
    seu_numero = "+5521964644993"  # ← Mude para seu número real
    
    # Mensagem de teste
    mensagem_teste = """🧪 TESTE DE SISTEMA
    
Olá! Esta é uma mensagem de teste do sistema de prospecção.
Se você recebeu, significa que a integração WhatsApp está funcionando!

✅ Tudo certo para prosseguir com os envios reais.
    
Atenciosamente,
Sistema de Prospecção"""

    print(f"📤 Enviando teste para: {seu_numero}")
    print(f"📝 Mensagem:\n{mensagem_teste}")
    print("-" * 50)
    
    # Enviar mensagem
    sucesso = enviar_whatsapp(seu_numero, mensagem_teste)
    
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print(" WhatsApp conectado e funcionando corretamente.")
    else:
        print("❌ FALHA NO TESTE")
        print(" Verifique sua conexão com a API WhatsApp.")

if __name__ == "__main__":
    teste_envio_whatsapp()