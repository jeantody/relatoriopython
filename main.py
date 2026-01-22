 import requests
import time
import csv
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from lxml import html
from urllib.parse import urljoin
from datetime import datetime
import config

class SistemaBot:
    def __init__(self, log_widget):
        self.session = requests.Session()
        self.log_widget = log_widget
        self.base_url = config.BASE_URL
        self.headers = {
            "User-Agent": config.USER_AGENT
        }

    def log(self, mensagem):
        self.log_widget.insert(tk.END, mensagem + "\n")
        self.log_widget.see(tk.END)

    def executar(self, data_ini, data_fim, unidade):
        try:
            self.log(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando extração...")
            self.log(f"Período: {data_ini} até {data_fim} | Unidade: {unidade}")
            
            login_url = f"{self.base_url}/Account/Login?ReturnUrl=/Medico/RelatorioEstatistica"
            payload = {"login": config.LOGIN, "Senha": config.SENHA}
            self.session.post(login_url, data=payload, headers=self.headers)
            self.log("✓ Autenticação realizada")

            report_url = f"{self.base_url}/Medico/ListaRelatorioAtendimentoMedico?inicio={data_ini}&fim={data_fim}&unidade={unidade}&usuario=undefined&medId=&dia=true&_=1768241465692"
            res = self.session.get(report_url, headers=self.headers)
            tree_report = html.fromstring(res.content)
            
            links = tree_report.xpath("//a[contains(@href, 'CentralPagamento')]/@href")
            links_finais = [urljoin(self.base_url, l) for l in set(links)]
            
            if not links_finais:
                self.log("⚠ Nenhum médico encontrado no período")
                return

            self.log(f"✓ Encontrados {len(links_finais)} médicos")

            dados_relatorio = []
            total_atend = 0
            total_horar = 0

            for i, url in enumerate(links_finais, 1):
                time.sleep(config.REQUEST_DELAY)
                res_det = self.session.get(url, headers=self.headers)
                tree = html.fromstring(res_det.content)

                nome = tree.xpath("//strong[@id='retnomemedico']/text()")
                nome = nome[0].strip() if nome else "Desconhecido"

                especialidade = tree.xpath("//strong[@id='retnomemedico']/parent::label/following-sibling::label[1]/text()")
                esp = especialidade[0].strip() if especialidade else "N/D"

                linha = tree.xpath("//table[@id='tb_lista_dias']/tbody/tr[1]")
                if linha:
                    qtd_h = linha[0].xpath("./td[1]/strong/text()")[0].replace('-', '').strip()
                    qtd_a = linha[0].xpath("./td[2]/strong/text()")[0].replace('-', '').strip()
                    hora_tr = linha[0].xpath("./td[2]/text()[1]")[0].strip()

                    val_h = int(qtd_h) if qtd_h.isdigit() else 0
                    val_a = int(qtd_a) if qtd_a.isdigit() else 0
                    total_horar += val_h
                    total_atend += val_a
                    
                    perc = (val_a / val_h * 100) if val_h > 0 else 0
                    
                    dados_relatorio.append({
                        "Médico": nome, "Especialidade": esp, "Horas": hora_tr,
                        "Qtd Horários": val_h, "Qtd Atendidos": val_a, "% Aproveitamento": f"{perc:.2f}%"
                    })
                    self.log(f"[{i}/{len(links_finais)}] {nome} - {esp}")

            arquivo = f"Relatorio_{data_ini.replace('-', '')}.csv"
            with open(arquivo, mode='w', newline='', encoding='utf-8-sig') as f:
                colunas = ["Médico", "Especialidade", "Horas", "Qtd Horários", "Qtd Atendidos", "% Aproveitamento"]
                writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
                writer.writeheader()
                writer.writerows(dados_relatorio)
                
                perc_geral = (total_atend / total_horar * 100) if total_horar > 0 else 0
                writer.writerow({})
                writer.writerow({"Médico": "TOTAIS GERAIS", "Qtd Horários": total_horar, "Qtd Atendidos": total_atend})
                writer.writerow({"Médico": "PORCENTAGEM GERAL", "% Aproveitamento": f"{perc_geral:.2f}%"})

            self.log(f"\n✓ Relatório gerado: {arquivo}")
            self.log(f"Aproveitamento geral: {perc_geral:.2f}%")
            messagebox.showinfo("Concluído", f"Relatório salvo com sucesso!\n\nArquivo: {arquivo}\nAproveitamento: {perc_geral:.2f}%")

        except Exception as e:
            self.log(f"\n✗ ERRO: {str(e)}")
            messagebox.showerror("Erro", f"Falha ao executar:\n{e}")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Relatórios")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        
        self.configurar_estilos()
        self.criar_interface()
        
    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Segoe UI', 9), foreground='#7f8c8d')
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('Action.TButton', font=('Segoe UI', 11, 'bold'), padding=10)
        
    def criar_interface(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        header = ttk.Frame(main_frame)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, text="Gerador de Relatórios Médicos", style='Title.TLabel').pack()
        ttk.Label(header, text="Sistema de análise de atendimentos", style='Subtitle.TLabel').pack()
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)
        
        form_frame = ttk.LabelFrame(main_frame, text=" Parâmetros ", padding="15")
        form_frame.pack(fill="x", pady=(0, 15))
        
        campos = [
            ("Data Início:", "2026-01-09", "inicio"),
            ("Data Fim:", "2026-01-09", "fim"),
            ("ID Unidade:", "1", "unidade")
        ]
        
        self.entries = {}
        for i, (label, valor_padrao, nome) in enumerate(campos):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="w", pady=8, padx=(0, 10))
            entry = ttk.Entry(form_frame, width=30, font=('Segoe UI', 10))
            entry.insert(0, valor_padrao)
            entry.grid(row=i, column=1, sticky="ew", pady=8)
            self.entries[nome] = entry
        
        form_frame.columnconfigure(1, weight=1)
        
        # Frame de exclusões
        excl_frame = ttk.LabelFrame(main_frame, text=" Filtros de Exclusão (opcional) ", padding="15")
        excl_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(excl_frame, text="Excluir Médicos:", 
                  font=('Segoe UI', 9, 'italic')).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Label(excl_frame, text="(separar por vírgula)", 
                  font=('Segoe UI', 8), foreground='#7f8c8d').grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        self.entry_medicos_excluir = ttk.Entry(excl_frame, width=50, font=('Segoe UI', 9))
        self.entry_medicos_excluir.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(excl_frame, text="Excluir Especialidades:", 
                  font=('Segoe UI', 9, 'italic')).grid(row=2, column=0, sticky="w", pady=(0, 5))
        ttk.Label(excl_frame, text="(separar por vírgula)", 
                  font=('Segoe UI', 8), foreground='#7f8c8d').grid(row=2, column=1, sticky="w", pady=(0, 5))
        
        self.entry_especialidades_excluir = ttk.Entry(excl_frame, width=50, font=('Segoe UI', 9))
        self.entry_especialidades_excluir.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        excl_frame.columnconfigure(0, weight=1)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        self.btn_gerar = ttk.Button(btn_frame, text="GERAR RELATÓRIO", 
                                     command=self.iniciar_processamento, 
                                     style='Action.TButton')
        self.btn_gerar.pack(fill="x")
        
        log_frame = ttk.LabelFrame(main_frame, text=" Log de Execução ", padding="10")
        log_frame.pack(fill="both", expand=True)
        
        self.txt_log = scrolledtext.ScrolledText(log_frame, height=32, width=70,
                                                  font=('Consolas', 9),
                                                  bg='#2c3e50', fg='#ecf0f1',
                                                  insertbackground='white')
        self.txt_log.pack(fill="both", expand=True)
        
        self.bot = SistemaBot(self.txt_log)
        
    def iniciar_processamento(self):
        d_ini = self.entries['inicio'].get().strip()
        d_fim = self.entries['fim'].get().strip()
        unid = self.entries['unidade'].get().strip()
        
        if not d_ini or not d_fim or not unid:
            messagebox.showwarning("Atenção", "Preencha todos os campos obrigatórios!")
            return
        
        # Processa as exclusões
        medicos_excluir = [m.strip() for m in self.entry_medicos_excluir.get().split(',') if m.strip()]
        especialidades_excluir = [e.strip() for e in self.entry_especialidades_excluir.get().split(',') if e.strip()]
        
        self.btn_gerar.state(['disabled'])
        self.txt_log.delete(1.0, tk.END)
        
        def executar_e_habilitar():
            self.bot.executar(d_ini, d_fim, unid, medicos_excluir, especialidades_excluir)
            self.btn_gerar.state(['!disabled'])
        
        threading.Thread(target=executar_e_habilitar, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
