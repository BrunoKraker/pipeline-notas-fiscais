import logging
import os
import xml.etree.ElementTree as ET
import pyodbc
import azure.functions as func
import json

app = func.FunctionApp()

NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

@app.blob_trigger(arg_name="myblob", path="bruto/{name}", connection="AzureWebJobsStorage")
@app.blob_output(arg_name="outputblob", path="tratado/{name}.json", connection="AzureWebJobsStorage")

def ProcessarXML(myblob: func.InputStream, outputblob: func.Out[str]):
    logging.info(f"Processando blob: {myblob.name}")

    xml_content = myblob.read()
    root = ET.fromstring(xml_content)

    inf_nfe = root.find('.//nfe:infNFe', NS)
    chave_acesso = inf_nfe.attrib['Id'].replace('NFe', '')

    ide = root.find('.//nfe:ide', NS)
    numero_nota = ide.find('nfe:nNF', NS).text
    data_emissao = ide.find('nfe:dhEmi', NS).text[:10]

    emit = root.find('.//nfe:emit', NS)
    cnpj_emitente = emit.find('nfe:CNPJ', NS).text
    razao_social_emitente = emit.find('nfe:xNome', NS).text

    dest = root.find('.//nfe:dest', NS)
    cnpj_tomador = dest.find('nfe:CNPJ', NS).text
    razao_social_tomador = dest.find('nfe:xNome', NS).text

    total = root.find('.//nfe:ICMSTot', NS)
    valor_total = total.find('nfe:vNF', NS).text

    dados_nota = {
        "chave_acesso": chave_acesso,
        "numero_nota": numero_nota,
        "data_emissao": data_emissao,
        "cnpj_emitente": cnpj_emitente,
        "razao_social_emitente": razao_social_emitente,
        "cnpj_tomador": cnpj_tomador,
        "razao_social_tomador": razao_social_tomador,
        "valor_total": valor_total
    }

    outputblob.set(json.dumps(dados_nota, ensure_ascii=False, indent=2))

    salvar_no_sql(
        chave_acesso, numero_nota, data_emissao,
        cnpj_emitente, razao_social_emitente,
        cnpj_tomador, razao_social_tomador, valor_total
    )

    logging.info(f"Nota {numero_nota} processada com sucesso")


def salvar_no_sql(chave_acesso, numero_nota, data_emissao,
                   cnpj_emitente, razao_social_emitente,
                   cnpj_tomador, razao_social_tomador, valor_total):
    conn_str = os.environ["SQL_CONNECTION_STRING"]
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (SELECT 1 FROM notas_fiscais WHERE chave_acesso = ?)
        INSERT INTO notas_fiscais
            (chave_acesso, numero_nota, data_emissao, cnpj_emitente,
             razao_social_emitente, cnpj_tomador, razao_social_tomador, valor_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, chave_acesso, chave_acesso, numero_nota, data_emissao, cnpj_emitente,
         razao_social_emitente, cnpj_tomador, razao_social_tomador, valor_total)

    conn.commit()
    cursor.close()
    conn.close()