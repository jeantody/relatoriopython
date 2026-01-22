import requests
import time
import csv
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from lxml import html
from urllib.parse import urljoin
from datetime import datetime, timedelta
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

    def executar(self, data_ini, data_fim, unidade, medicos_excluir, especialidades_excluir):
        try:
            self.log(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando extração...")
            self.log(f"Período: {data_ini} até {data_fim} | Unidade: {unidade}")
            
            if medicos_excluir:
                self.log(f"Médicos a excluir: {medicos_excluir}")
            if especialidades_excluir:
                self.log(f"Especialidades a excluir: {especialidades_excluir}")
            
            login_url = f"{self.base_url}/Account/Login?ReturnUrl=/Medico/RelatorioEstatistica"
            payload = {"login": config.LOGIN, "Senha": config.SENHA}
            self.session.post(login_url, data=payload, headers=self.headers)
            self.log("✓ Autenticação realizada")

            # Gera lista de datas do período
            data_inicio_obj = datetime.strptime(data_ini, "%Y-%m-%d")
            data_fim_obj = datetime.strptime(data_fim, "%Y-%m-%d")
            
            datas_para_processar = []
            data_atual = data_inicio_obj
            while data_atual <= data_fim_obj:
                datas_para_processar.append(data_atual.strftime("%Y-%m-%d"))
                data_atual += timedelta(days=1)
            
            self.log(f"📅 Total de dias a processar: {len(datas_para_processar)}")
            
            todos_links = set()  # Usar set para evitar duplicatas
            
            # Processa cada dia individualmente
            for idx, data_processamento in enumerate(datas_para_processar, 1):
                timestamp = int(time.time() * 1000)
                report_url = f"{self.base_url}/Medico/ListaRelatorioAtendimentoMedico?inicio={data_processamento}&fim={data_processamento}&unidade={unidade}&usuario=undefined&medId=&dia=true&_={timestamp}"
                
                self.log(f"   Buscando médicos para {data_processamento} ({idx}/{len(datas_para_processar)})...")
                
                res = self.session.get(report_url, headers=self.headers)
                tree_report = html.fromstring(res.content)
                
                links = tree_report.xpath("//a[contains(@href, 'CentralPagamento')]/@href")
                links_completos = [urljoin(self.base_url, l) for l in links]
                todos_links.update(links_completos)
                
                time.sleep(config.REQUEST_DELAY)
            
            links_finais = list(todos_links)
            
            if not links_finais:
                self.log("⚠ Nenhum médico encontrado no período")
                return

            self.log(f"✓ Encontrados {len(links_finais)} médicos únicos no período")

            dados_por_dia = {}  # Organiza dados por dia
            excluidos = 0

            for i, url in enumerate(links_finais, 1):
                time.sleep(config.REQUEST_DELAY)
                res_det = self.session.get(url, headers=self.headers)
                tree = html.fromstring(res_det.content)

                nome = tree.xpath("//strong[@id='retnomemedico']/text()")
                nome = nome[0].strip() if nome else "Desconhecido"

                especialidade = tree.xpath("//strong[@id='retnomemedico']/parent::label/following-sibling::label[1]/text()")
                esp = especialidade[0].strip() if especialidade else "N/D"

                # Verifica se deve excluir este médico ou especialidade
                if medicos_excluir and any(m.strip().upper() in nome.upper() for m in medicos_excluir):
                    self.log(f"[{i}/{len(links_finais)}] ⊗ Excluído: {nome}")
                    excluidos += 1
                    continue
                
                if especialidades_excluir and any(e.strip().upper() in esp.upper() for e in especialidades_excluir):
                    self.log(f"[{i}/{len(links_finais)}] ⊗ Excluído: {nome} ({esp})")
                    excluidos += 1
                    continue

                linhas = tree.xpath("//table[@id='tb_lista_dias']/tbody/tr")
                if linhas:
                    dias_processados = 0
                    
                    # Processa cada dia de atendimento
                    for idx, linha in enumerate(linhas):
                        try:
                            # Extrai a data do atendimento (primeiro text() da primeira coluna)
                            data_atend = linha.xpath("./td[1]/text()[1]")
                            data_atend = data_atend[0].strip() if data_atend else ""
                            
                            # Extrai quantidade de horários
                            qtd_h = linha.xpath("./td[1]/strong/text()")
                            qtd_h = qtd_h[0].replace('-', '').strip() if qtd_h else "0"
                            
                            # Extrai quantidade de atendimentos
                            qtd_a = linha.xpath("./td[2]/strong/text()")
                            qtd_a = qtd_a[0].replace('-', '').strip() if qtd_a else "0"
                            
                            # Extrai horário de trabalho
                            hora_tr = linha.xpath("./td[2]/text()[1]")
                            hora_tr = hora_tr[0].strip() if hora_tr else "N/D"

                            val_h = int(qtd_h) if qtd_h.isdigit() else 0
                            val_a = int(qtd_a) if qtd_a.isdigit() else 0
                            
                            perc = (val_a / val_h * 100) if val_h > 0 else 0
                            
                            # Organiza por dia
                            if data_atend not in dados_por_dia:
                                dados_por_dia[data_atend] = []
                            
                            dados_por_dia[data_atend].append({
                                "Data": data_atend,
                                "Médico": nome,
                                "Especialidade": esp,
                                "Horário Trabalho": hora_tr,
                                "Qtd Horários": val_h,
                                "Qtd Atendidos": val_a,
                                "% Eficiência": f"{perc:.2f}%"
                            })
                            
                            dias_processados += 1
                                
                        except Exception as e:
                            self.log(f"   Aviso: Erro ao processar linha {idx+1} - {str(e)}")
                            continue
                    
                    self.log(f"[{i}/{len(links_finais)}] {nome} - {esp} ({dias_processados} dia(s))")

            if excluidos > 0:
                self.log(f"\n⊗ Total de registros excluídos: {excluidos}")

            # Formata o nome do arquivo com o período
            if data_ini == data_fim:
                nome_arquivo = f"Relatorio_{data_ini.replace('-', '')}.csv"
                periodo_desc = data_ini
            else:
                nome_arquivo = f"Relatorio_{data_ini.replace('-', '')}_ate_{data_fim.replace('-', '')}.csv"
                periodo_desc = f"{data_ini} até {data_fim}"

            # Gera o CSV organizado por dia
            with open(nome_arquivo, mode='w', newline='', encoding='utf-8-sig') as f:
                colunas = ["Data", "Médico", "Especialidade", "Horário Trabalho", "Qtd Horários", "Qtd Atendidos", "% Eficiência"]
                writer = csv.DictWriter(f, fieldnames=colunas, delimiter=';')
                
                # Cabeçalho com informações do período
                writer.writerow({"Data": f"RELATÓRIO DE ATENDIMENTOS - PERÍODO: {periodo_desc}"})
                writer.writerow({"Data": f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"})
                writer.writerow({})
                
                writer.writeheader()
                
                # Ordena as datas e escreve os dados
                total_horar_geral = 0
                total_atend_geral = 0
                
                for data in sorted(dados_por_dia.keys()):
                    registros_dia = dados_por_dia[data]
                    total_horar_dia = 0
                    total_atend_dia = 0
                    
                    # Escreve os registros do dia
                    for registro in registros_dia:
                        writer.writerow(registro)
                        total_horar_dia += registro["Qtd Horários"]
                        total_atend_dia += registro["Qtd Atendidos"]
                    
                    # Subtotal do dia
                    perc_dia = (total_atend_dia / total_horar_dia * 100) if total_horar_dia > 0 else 0
                    writer.writerow({})
                    writer.writerow({
                        "Data": f"SUBTOTAL {data}",
                        "Qtd Horários": total_horar_dia,
                        "Qtd Atendidos": total_atend_dia,
                        "% Eficiência": f"{perc_dia:.2f}%"
                    })
                    writer.writerow({})
                    
                    total_horar_geral += total_horar_dia
                    total_atend_geral += total_atend_dia
                
                # Total geral
                perc_geral = (total_atend_geral / total_horar_geral * 100) if total_horar_geral > 0 else 0
                writer.writerow({})
                writer.writerow({
                    "Data": "TOTAIS GERAIS",
                    "Qtd Horários": total_horar_geral,
                    "Qtd Atendidos": total_atend_geral,
                    "% Eficiência": f"{perc_geral:.2f}%"
                })

            self.log(f"\n✓ Relatório gerado: {nome_arquivo}")
            self.log(f"Total de dias com atendimento: {len(dados_por_dia)}")
            self.log(f"Eficiência geral: {perc_geral:.2f}%")
            messagebox.showinfo("Concluído", 
                f"Relatório salvo com sucesso!\n\n"
                f"Arquivo: {nome_arquivo}\n"
                f"Período: {periodo_desc}\n"
                f"Dias com atendimento: {len(dados_por_dia)}\n"
                f"Eficiência: {perc_geral:.2f}%")

        except Exception as e:
            self.log(f"\n✗ ERRO: {str(e)}")
            messagebox.showerror("Erro", f"Falha na execução:\n{e}")


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
