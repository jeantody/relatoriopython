# Gerador de Relatórios

Aplicação desktop para extração e análise de relatórios médicos .
## Funcionalidades
- Extração automatizada de dados de atendimentos médicos
- Cálculo de eficiência por profissional e especialidade
- Geração de relatórios em formato CSV
- Interface gráfica intuitiva com log em tempo real
## Instalação
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/sistema-accb.git
cd sistema-accb

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure suas credenciais
cp config.example.py config.py
# Edite config.py com suas credenciais de acesso
```

Preencha os campos solicitados:
- **Data Início**: Data inicial do período (formato: AAAA-MM-DD)
- **Data Fim**: Data final do período (formato: AAAA-MM-DD)
- **ID Unidade**: Identificador da unidade médica

Clique em "GERAR RELATÓRIO" e acompanhe o progresso no log.

## Estrutura do Projeto

```
sistema-accb/
├── main.py              # Aplicação principal
├── config.py            # Configurações (não versionado)
├── config.example.py    # Exemplo de configuração
├── requirements.txt     # Dependências do projeto
├── README.md           # Documentação
└── .gitignore          # Arquivos ignorados pelo Git
```

## Formato do Relatório

O arquivo CSV gerado contém as seguintes informações:

- Médico
- Especialidade
- Horas trabalhadas
- Quantidade de horários disponíveis
- Quantidade de atendimentos realizados
- Percentual de eficiência

Ao final, são incluídos totais gerais e percentual geral de eficiência.

## Observações

- O sistema realiza pausas de 2 segundos entre requisições para evitar sobrecarga no servidor
- As credenciais devem ser configuradas no arquivo `config.py` (não incluído no repositório)
- Os relatórios são salvos no diretório de execução com nome `Relatorio_AAAAMMDD.csv`
- **Importante**: Nunca commite o arquivo `config.py` com suas credenciais reais
