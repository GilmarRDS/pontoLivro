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

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se o PowerShell bloquear scripts, rode antes:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Se aparecer `RequestsDependencyWarning` ao executar o app, atualize as dependências do ambiente virtual:

```bash
pip install --upgrade -r requirements.txt
```

Se ainda persistir, no **Windows/PowerShell** faça uma limpeza completa do ambiente virtual:

```powershell
# 1) sair do venv atual (se estiver ativo)
deactivate

# 2) apagar o ambiente antigo
Remove-Item -Recurse -Force .venv

# 3) recriar e ativar
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4) atualizar ferramentas de instalação
python -m pip install --upgrade pip setuptools wheel

# 5) reinstalar dependências do projeto
pip install --upgrade -r requirements.txt

# 6) validar versões principais
python -c "import requests,urllib3,charset_normalizer; print('requests', requests.__version__); print('urllib3', urllib3.__version__); print('charset_normalizer', charset_normalizer.__version__)"
```


## Configuração (Google Sheets)

Você pode configurar de duas formas:

### 1) Variáveis de ambiente (local/servidor)

```bash
export GOOGLE_SHEETS_SPREADSHEET_ID="SEU_ID_DA_PLANILHA"
export GOOGLE_SHEETS_CREDENTIALS_FILE="credentials.json"
# opcional
export GOOGLE_SHEETS_WORKSHEET="profissionais"
```

### 2) Streamlit Cloud - Secrets (TOML)

No painel **Secrets**, use algo como:

```toml
GOOGLE_SHEETS_SPREADSHEET_ID = "SEU_ID_DA_PLANILHA"
GOOGLE_SHEETS_WORKSHEET = "profissionais"

[google]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@...iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

> O app lê automaticamente `.streamlit/secrets.toml` (ou caminho definido em `STREAMLIT_SECRETS_PATH`).
> Existe um template seguro em `.streamlit/secrets.toml.example` para facilitar os testes.


### Como criar o secret no Google Cloud (passo a passo)

1. Acesse o **Google Cloud Console** e selecione/crie um projeto.
2. Ative as APIs:
   - **Google Sheets API**
   - **Google Drive API**
3. Vá em **IAM e administrador > Contas de serviço**.
4. Crie uma conta de serviço (ex: `ponto-livro-bot`).
5. Em **Chaves** da conta de serviço, clique em **Adicionar chave > Criar nova chave > JSON**.
6. Baixe o arquivo JSON (ele contém os dados do bloco `[google]`).
7. Abra sua planilha do Google Sheets e compartilhe com o `client_email` da conta de serviço (permissão **Editor**).
8. Para usar no Streamlit Cloud:
   - abra o JSON baixado;
   - copie os campos para o bloco `[google]` no Secrets;
   - configure também `GOOGLE_SHEETS_SPREADSHEET_ID` com o ID da URL da planilha.

> Dica de segurança: não suba o JSON no Git. Use sempre Secrets/variáveis de ambiente.

## Execução

### Linux / macOS

```bash
python app.py
```

### Windows (PowerShell)

```powershell
python .\app.py
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
