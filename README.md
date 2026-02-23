# Sistema Inteligente de Livro de Ponto

Aplicação web em Flask para:

- Cadastrar profissionais no **Google Sheets**.
- Registrar informações extras para professores (aulas e PL).
- Enviar um PDF de calendário escolar.
- Extrair automaticamente as datas encontradas no PDF.
- Gerar um **livro de ponto em PDF** pronto para impressão.

## Requisitos

- Python 3.10+
- Conta Google + planilha Google Sheets
- Conta de serviço (service account) com JSON de credenciais

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração do Google Sheets

1. Crie uma planilha no Google Sheets e copie o ID da URL.
2. Crie uma service account no Google Cloud e baixe o arquivo `credentials.json`.
3. Compartilhe a planilha com o e-mail da service account (permissão de editor).
4. Configure as variáveis de ambiente:

```bash
export GOOGLE_SHEETS_SPREADSHEET_ID="SEU_ID_DA_PLANILHA"
export GOOGLE_SHEETS_CREDENTIALS_FILE="credentials.json"
# opcional
export GOOGLE_SHEETS_WORKSHEET="profissionais"
```

## Execução

```bash
python app.py
```

Acesse: `http://localhost:5000`

## Como usar

1. Cadastre os profissionais.
2. Para professor, preencha também as aulas e o PL.
3. Em "Gerar livro de ponto", selecione o profissional e envie um PDF de calendário.
4. O sistema devolve um PDF com as linhas de entrada, saída e assinatura para cada data identificada.

## Observações

- O parser tenta reconhecer datas em formatos comuns como `dd/mm/aaaa`, `dd-mm-aaaa` e `dd de mês de aaaa`.
- Se o PDF for apenas imagem (sem texto selecionável), pode ser necessário OCR antes de enviar.
- A aba do Google Sheets é criada automaticamente com o cabeçalho: `id, nome, cargo, aulas, pl, created_at`.
