import tempfile
import uuid
from fpdf import FPDF
import os
import random
from datetime import datetime
import cv2
from io import BytesIO


class PDF(FPDF):
    def header(self):
        self.set_fill_color(70, 130, 180)
        self.rect(0, 0, self.w, 20, 'F')
        self.set_xy(10, 10)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 50)
        self.cell(0, 10, 'SafeView', 0, 0, 'L')

    def footer(self):
        self.set_fill_color(70, 130, 180)
        self.rect(0, self.h - 20, self.w, 20, 'F')
        self.set_y(-15)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')


def create_pdf_report(nome_pessoa, all_ok, img):
    # Obter a data e hora atual e formatar para o nome do arquivo
    now = datetime.now()
    data_hora = now.strftime("%d-%m-%Y_%Hh%M") 
    data_hora_pdf = now.strftime("%d/%m/%Y %H:%M")

    # Gerar um ID aleatório para o relatório
    report_id = uuid.uuid4().int >> 100
    report_id_str = str(report_id)

    # Nome do arquivo PDF com ID, nome e data
    pdf_filename = f"{report_id_str}_{nome_pessoa}_{data_hora}.pdf"

    # Gerar o PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.ln(10)

    # Título do relatório
    pdf.ln(10)
    pdf.cell(0, 10, "Relatório de Análise de Segurança", ln=True, align="C")

    # Inserir a imagem analisada no PDF
    pdf.ln(10)
    pdf.cell(0, 10, "Imagem Analisada:", ln=True)

    # Salvar a imagem temporariamente no sistema de arquivos
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_image_filename = temp_file.name
        cv2.imwrite(temp_image_filename, img)

    # Adicionar a imagem temporária no PDF
    image_width = 100
    image_height = 100
    x_center = (pdf.w - image_width) / 2
    y_center = (pdf.h - image_height) / 2 - 35
    pdf.image(temp_image_filename, x=x_center, y=y_center, w=image_width, h=image_height)
    
    pdf.ln(image_height / 2 + 40)

    # Detalhes do relatório
    pdf.set_font("Arial", size=12)
    pdf.ln(18)
    pdf.cell(0, 10, f"Nome: {nome_pessoa}", ln=True)
    pdf.cell(0, 10, f"Status de Segurança: {'OK' if all_ok else 'Faltando itens de segurança'}", ln=True)
    pdf.cell(0, 10, f"Data e Hora da Análise: {data_hora_pdf}", ln=True)

    # Salvar o PDF em memória
    byte_string = pdf.output(dest="S").encode('latin1')

    # Remover o arquivo temporário da imagem
    os.remove(temp_image_filename)

    return byte_string, pdf_filename
