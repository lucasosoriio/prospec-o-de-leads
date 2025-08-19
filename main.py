import requests
import time
import pandas as pd
import json
import phonenumbers
from phonenumbers import carrier
import re

# Configurações do WPPConnect
WPPCONNECT_API_URL = "http://localhost:3000/api"

# Chave da API do Google Maps
API_KEY = 'AIzaSyAHtYhCLgfTao-oMPJhm0qU4F_tv4lyc2o'

# Carregar templates de mensagens
def carregar_templates():
    try:
        with open('templates_mensagens.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Arquivo templates_mensagens.json não encontrado!")
        return {}

# Função para validar número de telefone
def validar_numero_telefone(numero):
    try:
        # Remover caracteres especiais
        numero_limpo = re.sub(r'[^\d+]', '', numero)
        # Adicionar +55 se não tiver código do país (para números brasileiros)
        if numero_limpo.startswith('55'):
            numero_formatado = '+' + numero_limpo
        elif numero_limpo.startswith('0'):
            numero_formatado = '+55' + numero_limpo[1:]
        elif len(numero_limpo) == 11 and numero_limpo[0] in ['9']:
            numero_formatado = '+55' + numero_limpo
        elif len(numero_limpo) == 10:
            numero_formatado = '+55' + numero_limpo
        else:
            numero_formatado = '+' + numero_limpo if not numero_limpo.startswith('+') else numero_limpo
        # Validar número
        parsed_number = phonenumbers.parse(numero_formatado, "BR")
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        else:
            return None
    except:
        return None

# Função para verificar se número tem WhatsApp (simulação)
def verificar_whatsapp(numero):
    # Esta é uma simulação - na prática, você precisaria de uma API específica
    # ou usar serviços como Twilio Lookup API
    numero_valido = validar_numero_telefone(numero)
    if numero_valido:
        # Simulação: assume que números brasileiros válidos têm WhatsApp
        return numero_valido
    return None

# Função para enviar mensagem via WPPConnect (WhatsApp não oficial)
def enviar_whatsapp(numero, mensagem):
    """
    Envia mensagem via WPPConnect (API não oficial)
    """
    try:
        # Formatar número para o padrão internacional (sem +)
        # Ex: +5511999999999 -> 5511999999999
        numero_formatado = numero.replace('+', '')
        
        url = f"{WPPCONNECT_API_URL}/send-message"
        payload = {
            "phone": numero_formatado,
            "message": mensagem
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Mensagem enviada para {numero}: {response.json()}")
            return True
        else:
            print(f"❌ Erro ao enviar mensagem para {numero}: Status {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para {numero}: {str(e)}")
        return False

# Função para chamar a API do Google Places Text Search
def chamar_places_api(query):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Erro na API do Google Places: {str(e)}")
        return None

# Função para pegar detalhes do local
def get_place_details(place_id):
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,international_phone_number,website,url,rating,user_ratings_total,photos,opening_hours',
        'key': API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json().get('result')
    except Exception as e:
        print(f"Erro ao obter detalhes do local: {str(e)}")
        return None

# Função para analisar o perfil
def analisar_perfil(place_details):
    if not place_details.get('website'):
        return 'Sem Website - Alta Prioridade'
    elif not place_details.get('photos') or len(place_details.get('photos', [])) < 3:
        return 'Poucas Fotos - Média Prioridade'
    elif not place_details.get('user_ratings_total') or place_details['user_ratings_total'] < 5:
        return 'Poucas Avaliações - Média Prioridade'
    elif place_details.get('rating', 0) < 4.0:
        return 'Avaliação Baixa - Média Prioridade'
    elif not place_details.get('opening_hours'):
        return 'Sem Horário de Funcionamento - Média Prioridade'
    else:
        return 'Potencialmente Otimizado'

# Função para selecionar template baseado no status
def selecionar_template(status_otimizacao, templates):
    if 'Alta Prioridade' in status_otimizacao:
        return templates.get('template_alta_prioridade', {})
    elif 'Média Prioridade' in status_otimizacao:
        return templates.get('template_media_prioridade', {})
    else:
        return templates.get('template_baixa_prioridade', {})

# Função principal de prospecção
def prospectar_empresas(config_data):
    resultados = []
    templates = carregar_templates()
    for cidade, tipo_negocio in config_data:
        if cidade and tipo_negocio:
            print(f"\n🔍 Prospectando {tipo_negocio} em {cidade}...")
            query = f"{tipo_negocio} em {cidade}"
            places_data = chamar_places_api(query)
            if places_data and 'results' in places_data:
                for place in places_data['results']:
                    place_details = get_place_details(place['place_id'])
                    if place_details:
                        nome = place_details.get('name', '')
                        endereco = place_details.get('formatted_address', '')
                        telefone = place_details.get('international_phone_number', '')
                        website = place_details.get('website', '')
                        google_maps_url = place_details.get('url', '')
                        rating = place_details.get('rating', 0)
                        user_ratings_total = place_details.get('user_ratings_total', 0)
                        status_otimizacao = analisar_perfil(place_details)
                        # Tentar extrair e validar número de WhatsApp
                        numero_whatsapp = None
                        if telefone:
                            numero_whatsapp = verificar_whatsapp(telefone)
                        # Selecionar template apropriado
                        template = selecionar_template(status_otimizacao, templates)
                        assunto = template.get('assunto', '')
                        resultados.append({
                            'Nome': nome,
                            'Endereço': endereco,
                            'Telefone': telefone,
                            'WhatsApp Validado': numero_whatsapp,
                            'Website': website,
                            'Google Maps URL': google_maps_url,
                            'Avaliações': user_ratings_total,
                            'Nota': rating,
                            'Status Otimização': status_otimizacao,
                            'Template Usado': assunto,
                            'Data': pd.Timestamp.now(),
                            'Email': '',
                            'Mensagem Enviada': False,
                            'Observações': ''
                        })
                    time.sleep(1)  # Evitar rate limiting
    return resultados

# Função para carregar números de WhatsApp validados de arquivo
def carregar_numeros_validados():
    try:
        df_validados = pd.read_csv('numeros_whatsapp_validados.csv')
        # Criar dicionário para lookup rápido
        numeros_dict = {}
        for _, row in df_validados.iterrows():
            telefone = row.get('Telefone', '')
            whatsapp = row.get('WhatsApp Validado', '')
            if telefone and whatsapp and pd.notna(whatsapp):
                numeros_dict[telefone] = whatsapp
        return numeros_dict
    except FileNotFoundError:
        print("Arquivo numeros_whatsapp_validados.csv não encontrado!")
        return {}

# Função para enviar mensagens automáticas
def enviar_mensagens_automaticas(df_resultados):
    templates = carregar_templates()
    numeros_validados = carregar_numeros_validados()
    
    # Verificar se WPPConnect está online
    try:
        status_response = requests.get(f"{WPPCONNECT_API_URL}/status", timeout=5)
        if status_response.status_code != 200:
            print("⚠️ WPPConnect não está respondendo! Certifique-se que está rodando.")
            return
        print("✅ WPPConnect está online e pronto para enviar mensagens")
    except:
        print("⚠️ Não foi possível conectar ao WPPConnect! Certifique-se que está rodando em http://localhost:3000")
        return
    
    for index, lead in df_resultados.iterrows():
        # Primeiro, tentar usar número já validado
        numero_whatsapp = None
        # Verificar se já temos o número validado
        telefone_original = lead['Telefone']
        if telefone_original in numeros_validados:
            numero_whatsapp = numeros_validados[telefone_original]
        else:
            # Usar número validado da prospecção
            numero_whatsapp = lead['WhatsApp Validado']
            
        if numero_whatsapp and pd.notna(numero_whatsapp):
            # Verificar se já foi enviada mensagem
            if not lead['Mensagem Enviada']:
                # Personalizar mensagem
                status = lead['Status Otimização']
                template = selecionar_template(status, templates)
                mensagem_base = template.get('mensagem', '')
                # Substituir variáveis na mensagem
                mensagem_personalizada = mensagem_base.replace('{nome}', lead['Nome'].split()[0])
                print(f"\n📨 Enviando mensagem para {lead['Nome']} ({numero_whatsapp})")
                sucesso = enviar_whatsapp(numero_whatsapp, mensagem_personalizada)
                df_resultados.at[index, 'Mensagem Enviada'] = sucesso
                if sucesso:
                    df_resultados.at[index, 'Observações'] = 'Mensagem enviada com sucesso'
                else:
                    df_resultados.at[index, 'Observações'] = 'Erro no envio'
                time.sleep(2)  # Pequeno delay entre mensagens
        else:
            print(f"📱 Número de WhatsApp não encontrado/validado para {lead['Nome']}")
            df_resultados.at[index, 'Observações'] = 'Número WhatsApp não disponível'

# Função principal
def main():
    print("🚀 Iniciando prospecção de empresas...")
    # Ler dados de entrada do CSV
    try:
        df_config = pd.read_csv('configuracoes.csv')
        config_data = df_config[['Cidade', 'Tipo de Negócio']].values.tolist()
        print(f"📋 Carregados {len(config_data)} combinações para prospecção")
    except FileNotFoundError:
        print("❌ Arquivo configuracoes.csv não encontrado!")
        # Usar dados de exemplo
        config_data = [
            ('São Paulo', 'Advogado'),
            ('Rio de Janeiro', 'Médico'),
        ]
        print("⚠️ Usando dados de exemplo")
    # Executar a prospecção
    resultados = prospectar_empresas(config_data)
    if not resultados:
        print("❌ Nenhum resultado encontrado!")
        return
    # Converter para DataFrame
    df = pd.DataFrame(resultados)
    # Salvar resultados iniciais
    df.to_excel("prospects_com_whatsapp.xlsx", index=False)
    df.to_csv("prospects_com_whatsapp.csv", index=False, encoding='utf-8')
    print(f"\n✅ Prospecção concluída! {len(resultados)} leads encontrados.")
    print("💾 Arquivos salvos: prospects_com_whatsapp.xlsx e prospects_com_whatsapp.csv")
    # Perguntar se deseja enviar mensagens
    enviar = input("\n📨 Deseja enviar mensagens automáticas para os leads? (s/n): ").lower().strip()
    if enviar in ['s', 'sim', 'y', 'yes']:
        print("\n📤 Iniciando envio de mensagens...")
        enviar_mensagens_automaticas(df)
        # Salvar resultados atualizados
        df.to_excel("prospects_com_whatsapp_atualizado.xlsx", index=False)
        df.to_csv("prospects_com_whatsapp_atualizado.csv", index=False, encoding='utf-8')
        print("\n✅ Mensagens enviadas! Arquivos atualizados salvos.")
    else:
        print("\n⏭️ Envio de mensagens pulado. Os arquivos foram salvos com os dados de prospecção.")

if __name__ == "__main__":
    main()