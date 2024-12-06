import random
from datetime import datetime, timedelta
import json

def gerar_dados_aleatorios(qtd: int, ano: int):
    dados = []

    for _ in range(qtd):
        humidade = random.randint(40, 70)  # Umidade entre 40% e 70% 
        ph = round(random.uniform(5.5, 7.0), 1)  # pH entre 5.5 e 7.0
        fosforo = random.randint(0, 1)
        potassio = random.randint(0, 1)

        dia_do_ano = random.randint(1, 365)
        data = datetime(ano, 1, 1) + timedelta(days=dia_do_ano - 1)
        data_formatada = data.strftime('%d/%m/%Y')

        hora = (datetime(2024, 12, 6, 2, 17, 26) + timedelta(seconds=random.randint(0, 36000))).time()
        irrigacao = random.randint(0, 1)

        dados.append({
            'humidade': humidade,
            'ph': ph,
            'fosforo': fosforo,
            'potassio': potassio,
            'data': data_formatada,
            'hora': hora.strftime('%H:%M:%S'),
            'irrigacao': irrigacao
        })

    return dados

def salvar_dados_em_json(dados, nome_arquivo):
    with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)

dados_gerados = gerar_dados_aleatorios(10000, 2024)  # ESPECIFIQUE A QTD DE DADOS E O ANO REFERENTE A DATA
salvar_dados_em_json(dados_gerados, 'dados_simulados.json')  # Salva os dados em um arquivo JSON
