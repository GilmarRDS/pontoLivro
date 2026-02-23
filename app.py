import os
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path

from dateutil import parser as date_parser
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ModuleNotFoundError:
    gspread = None
    Credentials = None

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
SHEETS_WORKSHEET = os.getenv("GOOGLE_SHEETS_WORKSHEET", "profissionais")
SHEETS_HEADERS = ["id", "nome", "cargo", "aulas", "pl", "created_at"]


def get_worksheet():
    if gspread is None or Credentials is None:
        raise RuntimeError("Dependências do Google Sheets não instaladas.")

    if not SHEETS_SPREADSHEET_ID:
        raise RuntimeError("Defina GOOGLE_SHEETS_SPREADSHEET_ID nas variáveis de ambiente.")

    credentials_path = Path(SHEETS_CREDENTIALS_FILE)
    if not credentials_path.exists():
        raise RuntimeError(
            f"Arquivo de credenciais não encontrado: {SHEETS_CREDENTIALS_FILE}."
        )

    creds = Credentials.from_service_account_file(str(credentials_path), scopes=SHEETS_SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEETS_SPREADSHEET_ID)

    try:
        worksheet = spreadsheet.worksheet(SHEETS_WORKSHEET)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=SHEETS_WORKSHEET, rows=1000, cols=10)

    first_row = worksheet.row_values(1)
    if first_row != SHEETS_HEADERS:
        worksheet.clear()
        worksheet.append_row(SHEETS_HEADERS)

    return worksheet


def list_professionals():
    ws = get_worksheet()
    rows = ws.get_all_records()

    professionals = []
    for row in rows:
        if not row.get("id"):
            continue
        professionals.append(
            {
                "id": str(row.get("id", "")).strip(),
                "nome": str(row.get("nome", "")).strip(),
                "cargo": str(row.get("cargo", "")).strip(),
                "aulas": str(row.get("aulas", "")).strip(),
                "pl": str(row.get("pl", "")).strip(),
                "created_at": str(row.get("created_at", "")).strip(),
            }
        )

    professionals.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return professionals


def create_professional_record(nome, cargo, aulas, pl):
    ws = get_worksheet()
    rows = ws.get_all_records()

    max_id = 0
    for row in rows:
        try:
            max_id = max(max_id, int(str(row.get("id", "0")).strip()))
        except ValueError:
            continue

    new_id = max_id + 1
    created_at = datetime.utcnow().isoformat()

    ws.append_row([new_id, nome, cargo, aulas or "", pl or "", created_at])


def get_professional_by_id(professional_id):
    for p in list_professionals():
        if p["id"] == str(professional_id):
            return p
    return None


def parse_calendar_dates(pdf_path: Path):
    reader = PdfReader(str(pdf_path))
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    patterns = [
        r"\b([0-3]?\d/[01]?\d/(?:\d{2}|\d{4}))\b",
        r"\b((?:0?[1-9]|[12]\d|3[01])[-](?:0?[1-9]|1[0-2])[-](?:\d{2}|\d{4}))\b",
        r"\b((?:0?[1-9]|[12]\d|3[01])\s+de\s+[A-Za-zçÇãõáéíóúâêô]+\s+de\s+\d{4})\b",
    ]

    dates = set()
    for pattern in patterns:
        for match in re.findall(pattern, all_text, flags=re.IGNORECASE):
            try:
                parsed = date_parser.parse(match, dayfirst=True, fuzzy=True)
                dates.add(parsed.date())
            except (ValueError, OverflowError):
                continue

    return sorted(dates)


def generate_attendance_pdf(professional, dates):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setTitle(f"Livro de Ponto - {professional['nome']}")

    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "Livro de Ponto")

    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Profissional: {professional['nome']}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Cargo: {professional['cargo']}")

    if professional["cargo"].lower() == "professor":
        y -= 6 * mm
        c.drawString(20 * mm, y, f"Aulas: {professional.get('aulas') or 'Não informado'}")
        y -= 6 * mm
        c.drawString(20 * mm, y, f"PL: {professional.get('pl') or 'Não informado'}")

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Data")
    c.drawString(60 * mm, y, "Entrada")
    c.drawString(95 * mm, y, "Saída")
    c.drawString(130 * mm, y, "Assinatura")
    c.line(20 * mm, y - 2 * mm, width - 20 * mm, y - 2 * mm)

    c.setFont("Helvetica", 9)
    y -= 8 * mm

    if not dates:
        c.drawString(20 * mm, y, "Nenhuma data encontrada no calendário PDF.")
    else:
        for day in dates:
            if y < 25 * mm:
                c.showPage()
                y = height - 20 * mm
                c.setFont("Helvetica-Bold", 10)
                c.drawString(20 * mm, y, "Data")
                c.drawString(60 * mm, y, "Entrada")
                c.drawString(95 * mm, y, "Saída")
                c.drawString(130 * mm, y, "Assinatura")
                c.line(20 * mm, y - 2 * mm, width - 20 * mm, y - 2 * mm)
                c.setFont("Helvetica", 9)
                y -= 8 * mm

            c.drawString(20 * mm, y, day.strftime("%d/%m/%Y"))
            c.line(58 * mm, y - 1.5 * mm, 85 * mm, y - 1.5 * mm)
            c.line(92 * mm, y - 1.5 * mm, 120 * mm, y - 1.5 * mm)
            c.line(128 * mm, y - 1.5 * mm, width - 20 * mm, y - 1.5 * mm)
            y -= 7 * mm

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


@app.route("/")
def index():
    try:
        professionals = list_professionals()
        sheets_ok = True
        sheets_error = ""
    except Exception as exc:
        professionals = []
        sheets_ok = False
        sheets_error = str(exc)

    return render_template(
        "index.html",
        professionals=professionals,
        sheets_ok=sheets_ok,
        sheets_error=sheets_error,
    )


@app.route("/profissionais", methods=["POST"])
def create_professional():
    nome = request.form.get("nome", "").strip()
    cargo = request.form.get("cargo", "").strip()
    aulas = request.form.get("aulas", "").strip()
    pl = request.form.get("pl", "").strip()

    if not nome or not cargo:
        flash("Nome e cargo são obrigatórios.", "error")
        return redirect(url_for("index"))

    if cargo.lower() == "professor" and not aulas:
        flash("Para professor, informe as aulas.", "error")
        return redirect(url_for("index"))

    try:
        create_professional_record(nome, cargo, aulas, pl)
    except Exception as exc:
        flash(f"Erro ao salvar no Google Sheets: {exc}", "error")
        return redirect(url_for("index"))

    flash("Profissional cadastrado com sucesso!", "success")
    return redirect(url_for("index"))


@app.route("/gerar-livro", methods=["POST"])
def generate_book():
    professional_id = request.form.get("professional_id")
    pdf_file = request.files.get("calendar_pdf")

    if not professional_id or not pdf_file or not pdf_file.filename:
        flash("Selecione um profissional e envie um PDF de calendário.", "error")
        return redirect(url_for("index"))

    try:
        professional = get_professional_by_id(professional_id)
    except Exception as exc:
        flash(f"Erro ao consultar Google Sheets: {exc}", "error")
        return redirect(url_for("index"))

    if professional is None:
        flash("Profissional não encontrado.", "error")
        return redirect(url_for("index"))

    filename = f"calendar_{professional_id}_{int(datetime.utcnow().timestamp())}.pdf"
    saved_path = UPLOAD_FOLDER / filename
    pdf_file.save(saved_path)

    try:
        dates = parse_calendar_dates(saved_path)
    except Exception:
        flash("Não foi possível processar o PDF. Verifique se ele contém texto selecionável.", "error")
        return redirect(url_for("index"))

    generated = generate_attendance_pdf(professional, dates)
    output_name = f"livro_ponto_{professional['nome'].replace(' ', '_')}.pdf"

    return send_file(
        generated,
        as_attachment=True,
        download_name=output_name,
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
