import requests
import time
import pandas as pd
import json
import phonenumbers
from phonenumbers import carrier
import re
import os
import random  # Adicionado para o delay aleatório
from dotenv import load_dotenv # Adicionado para carregar variáveis de ambiente

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações da API WhatsApp Local (ajuste conforme sua API)
# Você pode colocar essas variáveis no seu arquivo .env também
WHATSAPP_API_BASE_URL = os.getenv('WHATSAPP_API_BASE_URL', 'http://localhost:3000')
WHATSAPP_SESSION_ID = os.getenv('WHATSAPP_SESSION_ID', 'ABCD') # Substitua 'ABCD' pelo ID correto se for diferente

# Chave da API do Google Maps
API_KEY = 'AIzaSyAHtYhCLgfTao-oMPJhm0qU4F_tv4lyc2o' # Considere mover isso para .env também por segurança

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

# Função para enviar mensagem via API WhatsApp Local
def enviar_whatsapp(numero, mensagem):
    """
    Envia mensagem via API WhatsApp Local.
    Endpoint descoberto: POST http://localhost:3000/client/sendMessage/{sessionId}
    """
    try:
        # Limpar o número
        numero_limpo = str(numero).replace('+', '').replace(' ', '').replace('-', '').strip()

        # Montar URL conforme descoberto
        url_envio = f"{WHATSAPP_API_BASE_URL}/client/sendMessage/{WHATSAPP_SESSION_ID}"
        
        # Montar payload no formato esperado pela API
        payload = {
            "chatId": f"{numero_limpo}@c.us",
            "contentType": "string",
            "content": mensagem
        }

        print(f"📤 Tentando enviar para {numero} via {url_envio}")
        
        # Enviar requisição
        resp = requests.post(url_envio, json=payload, timeout=30)

        print(f"[{numero_limpo}] → Status da requisição: {resp.status_code}")
        
        if resp.status_code in [200, 201]:
            try:
                resposta_json = resp.json()
                # Verificar sucesso. A lógica exata depende da resposta da sua API.
                # Como vimos que ela pode retornar 500 mesmo enviando, vamos ser tolerantes.
                if resposta_json.get('success') == True:
                    print(f"✅ Mensagem enviada para {numero} (API confirmou sucesso)")
                    return True
                elif 'message' in resposta_json:
                     # A API respondeu com alguma mensagem, pode ser sucesso mesmo com erro 500
                     print(f"⚠️ API respondeu. Verifique no WhatsApp. Detalhes: {resposta_json}")
                     # Como a mensagem chegou antes, vamos considerar sucesso.
                     # Você pode ajustar essa lógica.
                     return True
                else:
                     print(f"⚠️ API respondeu com status 200/201, mas formato inesperado: {resposta_json}")
                     return True # Assume sucesso por ora
            except requests.exceptions.JSONDecodeError:
                print(f"✅ Mensagem possivelmente enviada para {numero} (resposta não JSON, status {resp.status_code})")
                return True
        else:
            # Status de erro (4xx, 5xx)
            print(f"❌ Erro ao enviar para {numero}: {resp.status_code} - {resp.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão ao enviar para {numero}: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar para {numero}: {e}")
        return False

    # Delay entre envios pode ser colocado aqui ou no loop principal
    # time.sleep(2) 

# Função para chamar a API do Google Places Text Search
def chamar_places_api(query):
    # Corrigido: Removido espaço extra na URL
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
    # Corrigido: Removido espaço extra na URL
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

# Função principal de prospecção (com filtro de avaliação opcional)
def prospectar_empresas(config_data, nota_min=None, nota_max=None):
    """
    Prospecta empresas com base em configurações e filtros de avaliação opcionais.

    Args:
        config_data: Lista de tuplas (cidade, tipo_negocio).
        nota_min: Nota mínima de avaliação para incluir o lead (opcional).
        nota_max: Nota máxima de avaliação para incluir o lead (opcional).

    Returns:
        Lista de dicionários com os dados dos leads que atendem aos critérios.
    """
    resultados = []
    templates = carregar_templates()
    
    # Contador para feedback ao usuário
    total_places_considerados = 0
    total_places_filtrados = 0

    for cidade, tipo_negocio in config_data:
        if cidade and tipo_negocio:
            print(f"\n🔍 Prospectando {tipo_negocio} em {cidade}...")
            query = f"{tipo_negocio} em {cidade}"
            places_data = chamar_places_api(query)
            
            if places_data and 'results' in places_data:
                for place in places_data['results']:
                    total_places_considerados += 1
                    place_details = get_place_details(place['place_id'])
                    
                    if place_details:
                        nome = place_details.get('name', '')
                        endereco = place_details.get('formatted_address', '')
                        telefone = place_details.get('international_phone_number', '')
                        website = place_details.get('website', '')
                        google_maps_url = place_details.get('url', '')
                        rating = place_details.get('rating', 0)
                        user_ratings_total = place_details.get('user_ratings_total', 0)

                        # --- FILTRO POR AVALIAÇÃO ---
                        # Verifica se o lead está dentro da faixa de avaliação desejada
                        atende_filtro_nota = True
                        if nota_min is not None and rating < nota_min:
                            atende_filtro_nota = False
                        if nota_max is not None and rating > nota_max:
                            atende_filtro_nota = False
                        
                        if not atende_filtro_nota:
                            total_places_filtrados += 1
                            # Opcional: Print para debug
                            # print(f"  ⏭️  Ignorado (Nota {rating}): {nome}")
                            continue # Pula para o próximo lugar
                        # --- FIM DO FILTRO ---

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
                            'Nota': rating, # Inclui a nota no resultado
                            'Status Otimização': status_otimizacao,
                            'Template Usado': assunto,
                            'Data': pd.Timestamp.now(),
                            'Email': '',
                            'Mensagem Enviada': False,
                            'Observações': ''
                        })
                    time.sleep(1)  # Evitar rate limiting

    print(f"\nℹ️  Total de lugares considerados: {total_places_considerados}")
    print(f"⏭️  Total de lugares filtrados (fora da faixa de nota): {total_places_filtrados}")
    print(f"✅ Total de leads capturados: {len(resultados)}")
    
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

# Função para enviar mensagens automáticas (ATUALIZADA)
def enviar_mensagens_automaticas(df_resultados): # Recebe o DataFrame
    templates = carregar_templates()
    # numeros_validados = carregar_numeros_validados() # Se usar
    
    # Verificação de conectividade básica (opcional)
    # try:
    #     status_response = requests.get(f"{WHATSAPP_API_BASE_URL}/algum_endpoint_de_status", timeout=5)
    #     if status_response.status_code != 200:
    #         print("⚠️ API WhatsApp não está respondendo!")
    #         return
    #     print("✅ API WhatsApp está online.")
    # except Exception as e:
    #     print(f"⚠️ Não foi possível conectar à API WhatsApp: {e}")
    #     return

    for index, lead in df_resultados.iterrows(): # Itera sobre o DataFrame recebido
        numero_whatsapp = lead['WhatsApp Validado'] # Ou 'Telefone' se não tiver validado
        
        if numero_whatsapp and pd.notna(numero_whatsapp):
            if not lead['Mensagem Enviada']: # Só envia se ainda não foi enviada
                # Personalizar mensagem
                status = lead['Status Otimização']
                template = selecionar_template(status, templates)
                mensagem_base = template.get('mensagem', 'Mensagem padrão.')
                
                # Substituir variáveis
                nome_lead = str(lead['Nome']) if pd.notna(lead['Nome']) else "Profissional"
                mensagem_personalizada = mensagem_base.replace('{nome}', nome_lead.split()[0])

                print(f"\n📨 Enviando mensagem para {nome_lead} ({numero_whatsapp})")
                sucesso = enviar_whatsapp(numero_whatsapp, mensagem_personalizada) # Chama a função de envio
                
                # --- ATUALIZAÇÃO CRÍTICA NO DATAFRAME ---
                df_resultados.at[index, 'Mensagem Enviada'] = sucesso
                if sucesso:
                    df_resultados.at[index, 'Observações'] = 'Mensagem enviada com sucesso'
                else:
                    df_resultados.at[index, 'Observações'] = 'Erro no envio'
                # --- FIM DA ATUALIZAÇÃO ---
                
                # --- DELAY ALEATÓRIO ENTRE 5 E 15 SEGUNDOS (ATUALIZAÇÃO) ---
                delay = random.randint(5, 15)
                print(f"⏳ Aguardando {delay} segundos antes de enviar a próxima mensagem...")
                time.sleep(delay)
                # --- FIM DO DELAY ---
        else:
            print(f"📱 Número de WhatsApp não encontrado/validado para {lead['Nome']}")
            df_resultados.at[index, 'Observações'] = 'Número WhatsApp não disponível'

    print("\n✅ Processo de envio de mensagens concluído (função enviar_mensagens_automaticas).")

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