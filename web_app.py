import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import base64
import io
import json  # Adicionado para carregar os templates

# Configuração da página
st.set_page_config(
    page_title="Prospecção WhatsApp",
    page_icon="📱",
    layout="wide"
)

# Função para verificar se usuário está logado
def check_login():
    if 'user_email' not in st.session_state:
        st.warning("Por favor, faça login primeiro!")
        st.stop()

# Função para simular login (você vai integrar com Google Auth)
def login_placeholder():
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    
    if st.button("Login"):
        if email and password:
            st.session_state.user_email = email
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Preencha todos os campos!")

# Função para logout
def logout():
    if 'user_email' in st.session_state:
        del st.session_state.user_email
    st.success("Logout realizado!")
    st.rerun()

# Página principal
def main_page():
    st.title("📱 Prospecção de Leads WhatsApp")
    
    # Header com usuário logado
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"👤 Logado como: **{st.session_state.user_email}**")
    with col2:
        if st.button("🚪 Logout"):
            logout()
    
    st.divider()
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Configuração", "🔍 Prospecção", "✉️ Envio WhatsApp", "📈 Resultados"])
    
    with tab1:
        configuracao_tab()
    
    with tab2:
        prospeccao_tab()
    
    with tab3:
        whatsapp_tab()
    
    with tab4:
        resultados_tab()

def configuracao_tab():
    st.subheader("⚙️ Configurações de Prospecção")
    
    # Upload de configuração (agora aceita Excel e CSV)
    st.subheader("📂 Upload de Configuração")
    uploaded_file = st.file_uploader("Upload Excel ou CSV", type=['xlsx', 'xls', 'csv'])
    
    if uploaded_file is not None:
        try:
            # Detectar tipo de arquivo e ler adequadamente
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Verificar colunas necessárias (agora Bairro em vez de Cidade)
            if 'Bairro' in df.columns and 'Tipo de Negócio' in df.columns:
                st.session_state.config_data = df.to_dict('records')
                st.success(f"✅ Configuração carregada: {len(df)} combinações")
                
                # Mostrar preview
                st.subheader("📋 Preview da Configuração")
                st.dataframe(df.head(10))
                
                # Estatísticas
                st.metric("Total de Combinações", len(df))
                
            else:
                st.error("Arquivo deve ter colunas 'Bairro' e 'Tipo de Negócio'")
                st.info("Dica: As colunas devem estar na primeira linha")
        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {str(e)}")
            st.info("Tente novamente com um arquivo válido")
    
    # Configuração manual (mantém igual, mas com Bairro)
    st.subheader("➕ Adicionar Manualmente")
    col1, col2 = st.columns(2)
    with col1:
        bairro = st.text_input("Bairro")  # Alterado de Cidade para Bairro
    with col2:
        tipo_negocio = st.text_input("Tipo de Negócio")
    
    if st.button("➕ Adicionar"):
        if bairro and tipo_negocio:  # Alterado de cidade para bairro
            if 'config_data' not in st.session_state:
                st.session_state.config_data = []
            st.session_state.config_data.append({
                'Bairro': bairro,  # Alterado de Cidade para Bairro
                'Tipo de Negócio': tipo_negocio
            })
            st.success("✅ Adicionado com sucesso!")
        else:
            st.warning("Preencha ambos os campos!")
    
    # Mostrar configurações atuais
    if 'config_data' in st.session_state and st.session_state.config_data:
        st.subheader("📋 Configurações Atuais")
        df_config = pd.DataFrame(st.session_state.config_data)
        st.dataframe(df_config)
        
        # Opções de download
        st.subheader("💾 Salvar Configuração")
        col1, col2 = st.columns(2)
        
        with col1:
            # Download como Excel
            excel_buffer = io.BytesIO()
            df_config.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            st.download_button(
                label="📥 Download como Excel (.xlsx)",
                data=excel_buffer,
                file_name="configuracao_prospeccao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # Download como CSV
            csv_buffer = df_config.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download como CSV (.csv)",
                data=csv_buffer,
                file_name="configuracao_prospeccao.csv",
                mime="text/csv"
            )
        
        # Limpar configurações
        if st.button("🗑️ Limpar Todas Configurações"):
            st.session_state.config_data = []
            st.success("✅ Configurações limpas!")
            st.rerun()

def prospeccao_tab():
    st.subheader("🔍 Iniciar Prospecção")
    
    if 'config_data' not in st.session_state or not st.session_state.config_data:
        st.warning("⚠️ Adicione configurações primeiro na aba 'Configuração'")
        return
    
    st.info(f"📊 {len(st.session_state.config_data)} combinações prontas para prospecção")
    
    # Adicionar controles de filtro por avaliação
    st.subheader("🎯 Filtros de Avaliação (Opcional)")
    col1, col2 = st.columns(2)
    
    with col1:
        nota_min = st.slider("Nota mínima", 0.0, 5.0, 0.0, 0.1, 
                            help="Incluir apenas negócios com nota maior ou igual a este valor")
    
    with col2:
        nota_max = st.slider("Nota máxima", 0.0, 5.0, 5.0, 0.1,
                            help="Incluir apenas negócios com nota menor ou igual a este valor")
    
    # Mostrar faixa selecionada
    if nota_min > 0.0 or nota_max < 5.0:
        st.info(f"🔍 Filtrando negócios com nota entre {nota_min} e {nota_max} estrelas")
    
    if st.button("🚀 Iniciar Prospecção", type="primary"):
        with st.spinner("🔍 Buscando empresas no Google Maps..."):
            try:
                # Importar função de prospecção
                from main import prospectar_empresas
                
                # Executar prospecção com filtros (agora com Bairro em vez de Cidade)
                config_data = [(item['Bairro'], item['Tipo de Negócio'])  # Alterado de Cidade para Bairro
                              for item in st.session_state.config_data]
                
                # Passar os filtros de nota para a função
                resultados = prospectar_empresas(config_data, nota_min=nota_min, nota_max=nota_max)
                
                if resultados:
                    # Salvar resultados
                    df_resultados = pd.DataFrame(resultados)
                    df_resultados.to_excel("prospects_web.xlsx", index=False)
                    df_resultados.to_csv("prospects_web.csv", index=False)
                    
                    st.session_state.resultados = resultados
                    st.success(f"✅ Prospecção concluída! {len(resultados)} leads encontrados")
                    st.dataframe(df_resultados.head(10))
                    
                    # Mostrar estatísticas das notas
                    st.subheader("📊 Estatísticas das Avaliações")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Nota Média", f"{df_resultados['Nota'].mean():.2f}")
                    with col2:
                        st.metric("Nota Mínima", f"{df_resultados['Nota'].min():.1f}")
                    with col3:
                        st.metric("Nota Máxima", f"{df_resultados['Nota'].max():.1f}")
                        
                else:
                    st.warning("⚠️ Nenhum lead encontrado com os critérios especificados")
                    
            except Exception as e:
                st.error(f"❌ Erro na prospecção: {str(e)}")

# --- Função configurar_mensagens adicionada/corrigida ---
def configurar_mensagens():
    st.subheader("📝 Configuração de Mensagens")
    
    # Carregar templates atuais
    try:
        with open('templates_mensagens.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
    except FileNotFoundError:
        st.warning("Arquivo templates_mensagens.json não encontrado. Criando um padrão.")
        templates = {
            "template_alta_prioridade": {
                "assunto": "Alta Prioridade",
                "mensagem": "Olá {nome}! Tudo bem?\n\nIdentificamos oportunidades para sua empresa...\n\nQuer 3 dicas rápidas?"
            },
            "template_media_prioridade": {
                "assunto": "Média Prioridade", 
                "mensagem": "Olá {nome}!\n\nPodemos te ajudar a melhorar sua presença digital?"
            },
            "template_baixa_prioridade": {
                "assunto": "Perfil Otimizado",
                "mensagem": "Olá {nome}!\n\nParabéns pelo seu perfil! Quer descobrir pontos de melhoria?"
            }
        }
    except json.JSONDecodeError as e:
        st.error(f"Erro ao ler templates_mensagens.json: {e}")
        return
    
    # Selecionar template
    st.subheader("📧 Escolher Template por Perfil")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🔴 Alta Prioridade**")
        alta_msg = st.text_area("Mensagem Alta Prioridade", 
                               value=templates.get('template_alta_prioridade', {}).get('mensagem', ''),
                               height=150,
                               key="alta_prioridade")
    
    with col2:
        st.markdown("**🟡 Média Prioridade**")
        media_msg = st.text_area("Mensagem Média Prioridade",
                                value=templates.get('template_media_prioridade', {}).get('mensagem', ''),
                                height=150,
                                key="media_prioridade")
    
    with col3:
        st.markdown("**🟢 Baixa Prioridade**")
        baixa_msg = st.text_area("Mensagem Baixa Prioridade",
                                value=templates.get('template_baixa_prioridade', {}).get('mensagem', ''),
                                height=150,
                                key="baixa_prioridade")
    
    # Salvar templates atualizados
    if st.button("💾 Salvar Configurações de Mensagens"):
        novos_templates = {
            "template_alta_prioridade": {
                "assunto": "Alta Prioridade",
                "mensagem": alta_msg
            },
            "template_media_prioridade": {
                "assunto": "Média Prioridade",
                "mensagem": media_msg
            },
            "template_baixa_prioridade": {
                "assunto": "Baixa Prioridade", 
                "mensagem": baixa_msg
            }
        }
        
        try:
            with open('templates_mensagens.json', 'w', encoding='utf-8') as f:
                json.dump(novos_templates, f, ensure_ascii=False, indent=2)
            st.success("✅ Templates salvos com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao salvar templates: {e}")
# --- Fim da função configurar_mensagens ---

# --- Função whatsapp_tab CORRIGIDA ---
def whatsapp_tab():
    st.subheader("✉️ Envio de Mensagens WhatsApp")

    # Verificar se resultados existem
    prospects_file = 'prospects_web.xlsx'
    if not os.path.exists(prospects_file):
        st.warning("⚠️ Execute a prospecção primeiro para gerar leads")
        return

    try:
        df_leads = pd.read_excel(prospects_file)
        # Garantir que as colunas necessárias existem
        if 'Mensagem Enviada' not in df_leads.columns:
             df_leads['Mensagem Enviada'] = False
        if 'Observações' not in df_leads.columns:
             df_leads['Observações'] = ''
    except Exception as e:
        st.error(f"❌ Erro ao carregar leads do arquivo {prospects_file}: {e}")
        return

    # Tabs para configuração e envio
    msg_tab, envio_tab = st.tabs(["📝 Configurar Mensagens", "🚀 Enviar Mensagens"])

    with msg_tab:
        # --- CORREÇÃO: Chamar a função que cria os campos de configuração ---
        configurar_mensagens()
        # --- FIM DA CORREÇÃO ---

    with envio_tab:
        st.info(f"📊 {len(df_leads)} leads disponíveis para envio")

        # --- Seção de Preview das Mensagens ---
        st.subheader("👁️ Preview das Mensagens")

        # Carregar templates atuais para preview
        try:
            with open('templates_mensagens.json', 'r', encoding='utf-8') as f:
                templates = json.load(f)
        except FileNotFoundError:
            st.warning("Arquivo templates_mensagens.json não encontrado. Usando padrões.")
            templates = {
                "template_alta_prioridade": {"mensagem": "Mensagem padrão alta prioridade"},
                "template_media_prioridade": {"mensagem": "Mensagem padrão média prioridade"},
                "template_baixa_prioridade": {"mensagem": "Mensagem padrão baixa prioridade"}
            }
        except json.JSONDecodeError as e:
            st.error(f"Erro ao ler templates_mensagens.json: {e}")
            templates = {
                "template_alta_prioridade": {"mensagem": "Erro no template"},
                "template_media_prioridade": {"mensagem": "Erro no template"},
                "template_baixa_prioridade": {"mensagem": "Erro no template"}
            }

        # Mostrar exemplos (se houver leads)
        if len(df_leads) > 0:
            # Tenta pegar um lead de cada categoria, senão pega o primeiro disponível
            exemplo_lead_alta = df_leads[df_leads['Status Otimização'].str.contains("Alta Prioridade", case=False, na=False)].head(1)
            exemplo_lead_media = df_leads[df_leads['Status Otimização'].str.contains("Média Prioridade", case=False, na=False)].head(1)

            exemplo_lead = None
            if not exemplo_lead_alta.empty:
                exemplo_lead = exemplo_lead_alta.iloc[0]
            elif not exemplo_lead_media.empty:
                exemplo_lead = exemplo_lead_media.iloc[0]
            else:
                # Tenta encontrar um lead com nota baixa como exemplo alternativo
                exemplo_lead_baixa_nota = df_leads[df_leads['Nota'] < 3.0].head(1)
                if not exemplo_lead_baixa_nota.empty:
                    exemplo_lead = exemplo_lead_baixa_nota.iloc[0]
                else:
                    exemplo_lead = df_leads.iloc[0] # Pega o primeiro se não achar pelos status

            # Obter nome para o preview
            if exemplo_lead is not None and pd.notna(exemplo_lead.get('Nome')):
                nome_exemplo = str(exemplo_lead.get('Nome')).split()[0]
            else:
                nome_exemplo = "Exemplo"

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**🔴 Alta Prioridade**")
                msg_alta = templates.get('template_alta_prioridade', {}).get('mensagem', 'Template não encontrado')
                st.caption(msg_alta.replace('{nome}', nome_exemplo))

            with col2:
                st.markdown("**🟡 Média Prioridade**")
                msg_media = templates.get('template_media_prioridade', {}).get('mensagem', 'Template não encontrado')
                st.caption(msg_media.replace('{nome}', nome_exemplo))

            with col3:
                st.markdown("**🟢 Baixa Prioridade**")
                msg_baixa = templates.get('template_baixa_prioridade', {}).get('mensagem', 'Template não encontrado')
                st.caption(msg_baixa.replace('{nome}', nome_exemplo))
        else:
            st.write("Nenhum lead disponível para preview.")

        # --- Seção de Envio Real ---
        st.divider()
        st.subheader("📤 Enviar Mensagens")

        # Checkbox de confirmação (movido para antes do botão de envio)
        confirmacao = st.checkbox("⚠️ Confirmo que li os termos de uso e privacidade e estou ciente das políticas de envio.", key="confirmacao_envio")

        # Botão de envio
        if st.button("✉️ Enviar Mensagens para Todos", type="primary", disabled=not confirmacao):
            if confirmacao: # Verificação redundante, mas clara
                # Spinner para indicar processamento
                with st.spinner("✉️ Enviando mensagens... Isso pode levar alguns minutos."):
                    try:
                        # Importar a função de envio do main.py
                        from main import enviar_mensagens_automaticas

                        # --- AQUI ESTÁ A CHAMADA CRÍTICA ---
                        st.write("Iniciando processo de envio...")
                        # A função abaixo DEVE modificar o df_leads diretamente
                        enviar_mensagens_automaticas(df_leads)
                        st.write("Processo de envio concluído pela função `enviar_mensagens_automaticas`.")
                        # --- FIM DA CHAMADA CRÍTICA ---

                        # Salvar resultados atualizados
                        # Como df_leads foi modificado diretamente pela função, podemos salvá-lo agora.
                        output_file = "prospects_web_atualizado.xlsx"
                        df_leads.to_excel(output_file, index=False)
                        df_leads.to_csv("prospects_web_atualizado.csv", index=False)
                        st.success(f"✅ Processo de envio finalizado! Arquivo `{output_file}` atualizado.")

                        # Atualizar métricas de sucesso/falha
                        try:
                            # Recarregar o DataFrame para garantir que as mudanças estejam refletidas
                            # (geralmente não é necessário, mas pode ajudar em alguns casos)
                            # df_leads = pd.read_excel(output_file) # Descomente se tiver problemas

                            enviadas_com_sucesso = df_leads[df_leads['Mensagem Enviada'] == True].shape[0]
                            total_leads = len(df_leads)
                            if total_leads > 0:
                                percentual_sucesso = (enviadas_com_sucesso / total_leads) * 100
                                st.metric("Mensagens Enviadas com Sucesso", f"{enviadas_com_sucesso}/{total_leads}", f"{percentual_sucesso:.1f}%")
                            else:
                                st.info("Nenhum lead para enviar.")
                        except Exception as metric_e:
                            st.warning(f"Não foi possível calcular as métricas: {metric_e}")

                    except Exception as e:
                        st.error(f"❌ Erro durante o processo de envio: {str(e)}")
                        # st.code(traceback.format_exc()) # Opcional: para debug intenso
            else:
                st.warning("Por favor, confirme os termos antes de enviar.")

        # --- Informações Adicionais ---
        st.divider()
        st.info("""
        **Dicas para Envio:**
        - Certifique-se de que o servidor da API WhatsApp (`npm run start` na pasta `whatsapp-api`) está rodando.
        - Verifique se a sessão do WhatsApp Web está ativa (QR Code escaneado).
        - O processo de envio pode levar alguns minutos dependendo do número de leads.
        - Verifique o terminal do servidor da API para ver os logs de envio em tempo real.
        - As colunas 'Mensagem Enviada' e 'Observações' no arquivo `prospects_web_atualizado.xlsx` indicam o status de cada envio.
        """)

# --- Fim da função whatsapp_tab corrigida ---

def resultados_tab():
    st.subheader("📈 Resultados e Relatórios")
    
    # Verificar arquivos de resultados
    arquivos = []
    if os.path.exists('prospects_web_atualizado.xlsx'):
        arquivos.append('prospects_web_atualizado.xlsx')
    elif os.path.exists('prospects_web.xlsx'):
        arquivos.append('prospects_web.xlsx')
    
    if arquivos:
        for arquivo in arquivos:
            st.subheader(f"📄 {arquivo}")
            try:
                df = pd.read_excel(arquivo)
                st.dataframe(df)
                
                # Estatísticas
                st.subheader("📊 Estatísticas")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total de Leads", len(df))
                
                with col2:
                    if 'Mensagem Enviada' in df.columns:
                        enviadas = df[df['Mensagem Enviada'] == True].shape[0]
                        st.metric("Mensagens Enviadas", enviadas)
                
                with col3:
                    if 'Status Otimização' in df.columns:
                        status_counts = df['Status Otimização'].value_counts()
                        st.metric("Maior Prioridade", status_counts.index[0] if len(status_counts) > 0 else "N/A")
                
                # Download do arquivo
                with open(arquivo, 'rb') as f:
                    st.download_button(
                        label=f"📥 Download {arquivo}",
                        data=f,
                        file_name=arquivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            except Exception as e:
                st.error(f"❌ Erro ao carregar {arquivo}: {str(e)}")
    else:
        st.warning("⚠️ Nenhum arquivo de resultados encontrado. Execute a prospecção primeiro.")

# Main App
def main():
    st.sidebar.title("📱 Prospecção WhatsApp")
    
    # Verificar login
    if 'user_email' not in st.session_state:
        # Mostrar página de login
        login_placeholder()
    else:
        # Mostrar aplicação principal
        main_page()

if __name__ == "__main__":
    main()