import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import os
import sys

class ProspeccaoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Prospecção WhatsApp")
        self.root.geometry("700x600")
        self.root.minsize(700, 600)
        
        # Variáveis
        self.cidades_tipos = []
        
        self.criar_interface()
        
    def criar_interface(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar pesos para redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="Prospecção de Leads WhatsApp", 
                          font=('Arial', 16, 'bold'))
        titulo.grid(row=0, column=0, columnspan=5, pady=(0, 20))
        
        # Seção de entrada manual
        ttk.Label(main_frame, text="Adicionar Cidade e Tipo:", 
                 font=('Arial', 12, 'bold')).grid(row=1, column=0, columnspan=5, sticky=tk.W)
        
        # Entrada de cidade
        ttk.Label(main_frame, text="Cidade:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cidade_entry = ttk.Entry(main_frame, width=20)
        self.cidade_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))
        self.cidade_entry.bind('<Return>', lambda event: self.tipo_entry.focus())
        
        # Entrada de tipo de negócio
        ttk.Label(main_frame, text="Tipo:").grid(row=2, column=2, sticky=tk.W, pady=5)
        self.tipo_entry = ttk.Entry(main_frame, width=20)
        self.tipo_entry.grid(row=2, column=3, sticky=(tk.W, tk.E), pady=5)
        self.tipo_entry.bind('<Return>', lambda event: self.adicionar_cidade_tipo())
        
        # Botão adicionar
        ttk.Button(main_frame, text="Adicionar (+)", width=15, 
                  command=self.adicionar_cidade_tipo).grid(row=2, column=4, padx=(10, 0), sticky=tk.W)
        
        # Lista de cidades/tipos
        ttk.Label(main_frame, text="Cidades/Tipo configuradas:", 
                 font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=5, sticky=tk.W, pady=(20, 5))
        
        # Treeview para mostrar cidades/tipos
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, columns=('Cidade', 'Tipo'), show='headings', height=8)
        self.tree.heading('Cidade', text='Cidade')
        self.tree.heading('Tipo', text='Tipo de Negócio')
        self.tree.column('Cidade', width=250)
        self.tree.column('Tipo', width=250)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Botões de manipulação da lista
        list_buttons_frame = ttk.Frame(main_frame)
        list_buttons_frame.grid(row=5, column=0, columnspan=5, pady=5)
        
        ttk.Button(list_buttons_frame, text="Remover Selecionado", 
                  command=self.remover_selecionado).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(list_buttons_frame, text="Limpar Tudo", 
                  command=self.limpar_tudo).pack(side=tk.LEFT)
        
        # Botões de arquivo
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=6, column=0, columnspan=5, pady=10)
        
        ttk.Button(file_frame, text="📂 Carregar CSV", 
                  command=self.carregar_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="💾 Salvar CSV", 
                  command=self.salvar_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="🔄 Carregar Configuração Atual", 
                  command=self.carregar_config_atual).pack(side=tk.LEFT)
        
        # Botões de ação
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=7, column=0, columnspan=5, pady=20)
        
        self.prospec_button = ttk.Button(action_frame, text="🔍 Iniciar Prospecção", 
                                       command=self.iniciar_prospecção)
        self.prospec_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.enviar_button = ttk.Button(action_frame, text="✉️ Enviar Mensagens", 
                                      command=self.enviar_mensagens, state='disabled')
        self.enviar_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="📊 Abrir Resultados", 
                  command=self.abrir_resultados).pack(side=tk.LEFT)
        
        # Status
        self.status_var = tk.StringVar(value="Aguardando... Pronto para começar!")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                    font=('Arial', 10), foreground='blue')
        self.status_label.grid(row=8, column=0, columnspan=5, pady=(20, 0))
        
        # Carregar configuração atual
        self.carregar_config_atual()
        
    def adicionar_cidade_tipo(self):
        cidade = self.cidade_entry.get().strip()
        tipo = self.tipo_entry.get().strip()
        
        if cidade and tipo:
            self.cidades_tipos.append((cidade, tipo))
            self.tree.insert('', tk.END, values=(cidade, tipo))
            self.cidade_entry.delete(0, tk.END)
            self.tipo_entry.delete(0, tk.END)
            self.cidade_entry.focus()
            self.atualizar_status()
        else:
            messagebox.showwarning("Aviso", "Preencha ambos os campos!")
    
    def remover_selecionado(self):
        selecionado = self.tree.selection()
        if selecionado:
            item = selecionado[0]
            valores = self.tree.item(item, 'values')
            self.tree.delete(item)
            # Remover da lista
            self.cidades_tipos = [ct for ct in self.cidades_tipos if ct != valores]
            self.atualizar_status()
        else:
            messagebox.showwarning("Aviso", "Selecione um item para remover!")
    
    def limpar_tudo(self):
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar tudo?"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.cidades_tipos.clear()
            self.atualizar_status()
    
    def carregar_csv(self):
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                df = pd.read_csv(filename)
                if 'Cidade' in df.columns and 'Tipo de Negócio' in df.columns:
                    # Limpar treeview e lista
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    self.cidades_tipos.clear()
                    
                    # Adicionar itens
                    for _, row in df.iterrows():
                        cidade = str(row['Cidade']).strip()
                        tipo = str(row['Tipo de Negócio']).strip()
                        if cidade and tipo:
                            self.cidades_tipos.append((cidade, tipo))
                            self.tree.insert('', tk.END, values=(cidade, tipo))
                    
                    self.atualizar_status()
                    messagebox.showinfo("Sucesso", f"Carregado {len(self.cidades_tipos)} combinações")
                else:
                    messagebox.showerror("Erro", "CSV deve ter colunas 'Cidade' e 'Tipo de Negócio'")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar CSV: {str(e)}")
    
    def salvar_csv(self):
        if not self.cidades_tipos:
            messagebox.showwarning("Aviso", "Nenhuma combinação para salvar")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Salvar como CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                df = pd.DataFrame(self.cidades_tipos, columns=['Cidade', 'Tipo de Negócio'])
                df.to_csv(filename, index=False)
                messagebox.showinfo("Sucesso", f"Arquivo salvo: {filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar CSV: {str(e)}")
    
    def carregar_config_atual(self):
        # Carregar do arquivo configuracoes.csv existente
        try:
            if os.path.exists('configuracoes.csv'):
                df = pd.read_csv('configuracoes.csv')
                if 'Cidade' in df.columns and 'Tipo de Negócio' in df.columns:
                    # Limpar treeview e lista
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    self.cidades_tipos.clear()
                    
                    # Adicionar itens
                    for _, row in df.iterrows():
                        cidade = str(row['Cidade']).strip()
                        tipo = str(row['Tipo de Negócio']).strip()
                        if cidade and tipo:
                            self.cidades_tipos.append((cidade, tipo))
                            self.tree.insert('', tk.END, values=(cidade, tipo))
                    
                    self.atualizar_status()
            else:
                # Carregar do seu arquivo txt
                if os.path.exists('configuracoes.txt'):
                    df = pd.read_csv('configuracoes.txt')
                    if 'Cidade' in df.columns and 'Tipo de Negócio' in df.columns:
                        # Limpar treeview e lista
                        for item in self.tree.get_children():
                            self.tree.delete(item)
                        self.cidades_tipos.clear()
                        
                        # Adicionar itens
                        for _, row in df.iterrows():
                            cidade = str(row['Cidade']).strip()
                            tipo = str(row['Tipo de Negócio']).strip()
                            if cidade and tipo:
                                self.cidades_tipos.append((cidade, tipo))
                                self.tree.insert('', tk.END, values=(cidade, tipo))
                        
                        self.atualizar_status()
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
    
    def atualizar_status(self):
        self.status_var.set(f"Configurações: {len(self.cidades_tipos)} combinações prontas")
    
    def iniciar_prospecção(self):
        if not self.cidades_tipos:
            messagebox.showwarning("Aviso", "Adicione pelo menos uma combinação")
            return
            
        # Salvar configuração atual
        try:
            df = pd.DataFrame(self.cidades_tipos, columns=['Cidade', 'Tipo de Negócio'])
            df.to_csv('configuracoes.csv', index=False)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configuração: {str(e)}")
            return
            
        # Executar em thread separada para não travar interface
        threading.Thread(target=self.executar_prospecção, daemon=True).start()
    
    def executar_prospecção(self):
        self.status_var.set("🔍 Iniciando prospecção... Aguarde...")
        self.prospec_button.config(state='disabled')
        
        try:
            # Importar e executar a prospecção
            from main import prospectar_empresas
            import time
            
            self.status_var.set("🔍 Buscando empresas no Google Maps...")
            resultados = prospectar_empresas(self.cidades_tipos)
            
            if resultados:
                import pandas as pd
                df = pd.DataFrame(resultados)
                df.to_excel("prospects_com_whatsapp.xlsx", index=False)
                df.to_csv("prospects_com_whatsapp.csv", index=False, encoding='utf-8')
                
                self.status_var.set(f"✅ Prospecção concluída! {len(resultados)} leads encontrados.")
                self.enviar_button.config(state='normal')
                messagebox.showinfo("Sucesso", f"Prospecção concluída!\n{len(resultados)} leads encontrados.\n\nArquivos gerados:\n- prospects_com_whatsapp.xlsx\n- prospects_com_whatsapp.csv")
            else:
                self.status_var.set("⚠️ Prospecção concluída, mas nenhum lead encontrado.")
                messagebox.showinfo("Aviso", "Prospecção concluída, mas nenhum lead foi encontrado.")
                
        except Exception as e:
            self.status_var.set(f"❌ Erro na prospecção: {str(e)}")
            messagebox.showerror("Erro", f"Erro na prospecção: {str(e)}")
        finally:
            self.prospec_button.config(state='normal')
    
    def enviar_mensagens(self):
        # Verificar se arquivo de resultados existe
        if not os.path.exists('prospects_com_whatsapp.xlsx'):
            messagebox.showwarning("Aviso", "Arquivo de resultados não encontrado!\nExecute a prospecção primeiro.")
            return
            
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja enviar mensagens para todos os leads?\n\nATENÇÃO: Esta ação não pode ser desfeita e pode gerar custos na sua API de WhatsApp."):
            # Executar em thread separada
            threading.Thread(target=self.executar_envio, daemon=True).start()
    
    def executar_envio(self):
        self.status_var.set("✉️ Iniciando envio de mensagens...")
        self.enviar_button.config(state='disabled')
        
        try:
            import pandas as pd
            from main import enviar_mensagens_automaticas
            
            # Carregar resultados
            df = pd.read_excel('prospects_com_whatsapp.xlsx')
            
            if len(df) == 0:
                self.status_var.set("⚠️ Nenhum lead para enviar mensagens")
                messagebox.showinfo("Aviso", "Não há leads para enviar mensagens")
                return
                
            self.status_var.set(f"✉️ Enviando mensagens para {len(df)} leads...")
            
            # Enviar mensagens
            enviar_mensagens_automaticas(df)
            
            # Salvar resultados atualizados
            df.to_excel("prospects_com_whatsapp_atualizado.xlsx", index=False)
            df.to_csv("prospects_com_whatsapp_atualizado.csv", index=False, encoding='utf-8')
            
            # Contar mensagens enviadas
            enviadas = df[df['Mensagem Enviada'] == True].shape[0]
            
            self.status_var.set(f"✅ Envio concluído! {enviadas}/{len(df)} mensagens enviadas.")
            messagebox.showinfo("Sucesso", f"Envio de mensagens concluído!\n\n{enviadas} de {len(df)} mensagens enviadas com sucesso.\n\nArquivos atualizados salvos.")
            
        except Exception as e:
            self.status_var.set(f"❌ Erro no envio: {str(e)}")
            messagebox.showerror("Erro", f"Erro no envio de mensagens: {str(e)}")
        finally:
            self.enviar_button.config(state='normal')
    
    def abrir_resultados(self):
        # Verificar se arquivos existem
        arquivos = []
        if os.path.exists('prospects_com_whatsapp_atualizado.xlsx'):
            arquivos.append('prospects_com_whatsapp_atualizado.xlsx')
        elif os.path.exists('prospects_com_whatsapp.xlsx'):
            arquivos.append('prospects_com_whatsapp.xlsx')
        
        if arquivos:
            import subprocess
            try:
                for arquivo in arquivos:
                    if sys.platform == "win32":
                        os.startfile(arquivo)
                    elif sys.platform == "darwin":
                        subprocess.call(["open", arquivo])
                    else:
                        subprocess.call(["xdg-open", arquivo])
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir o arquivo: {str(e)}")
        else:
            messagebox.showwarning("Aviso", "Nenhum arquivo de resultados encontrado!")

def main():
    root = tk.Tk()
    app = ProspeccaoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()