# Gerador de Relatórios WebScrapping

Aplicação desktop para extração e análise de relatórios médicos .
- Extração automatizada de dados de atendimentos médicos
- Cálculo de eficiência por profissional e especialidade
- Geração de relatórios em formato CSV
- Interface gráfica intuitiva com log em tempo real
# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
# Instale as dependências
pip install -r requirements.txt
# Configure suas credenciais
cp config.example.py config.py

O arquivo CSV gerado contém as seguintes informações:
- Médico
- Especialidade
- Horas trabalhadas
- Quantidade de horários disponíveis
- Quantidade de atendimentos realizados
- Percentual de eficiência
## Observações
- As credenciais devem ser configuradas no arquivo `config.py`
