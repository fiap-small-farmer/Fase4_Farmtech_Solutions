import cx_Oracle
import random

# Configurações do banco de dados Oracle
db_config = {
    'user': 'rm560518',
    'password': '230186',
    'dsn': 'oracle.fiap.com.br:1521/ORCL',  # Exemplo: "host:porta/servicename"
}

# Função para inserir dados mockados no banco de dados
def insert_mock_data():
    conn = None
    cursor = None
    try:
        # Conectar ao banco de dados Oracle
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()

        # Gerar dados mockados
        sensor_data = {
            'umidade': round(random.uniform(30.0, 90.0), 2),
            'ph': round(random.uniform(5.5, 8.5), 2),
            'fosforo': round(random.uniform(1.0, 5.0), 2),
            'potassio': round(random.uniform(0.5, 3.0), 2)
        }

        # Montar e executar a consulta SQL
        sql_query = """
        INSERT INTO dados_sensores (umidade, ph, fosforo, potassio, timestamp)
        VALUES (:1, :2, :3, :4, SYSTIMESTAMP)
        """
        data_tuple = (
            sensor_data['umidade'],
            sensor_data['ph'],
            sensor_data['fosforo'],
            sensor_data['potassio']
        )
        cursor.execute(sql_query, data_tuple)
        conn.commit()
        print("Dados mockados inseridos com sucesso:", sensor_data)

    except cx_Oracle.DatabaseError as err:
        print(f"Erro ao inserir dados no banco: {err}")
    finally:
        # Fechar cursor e conexão apenas se foram inicializados
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# Função para consultar dados no banco de dados
def fetch_data():
    conn = None
    cursor = None
    try:
        # Conectar ao banco de dados Oracle
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()

        # Executar consulta SQL
        sql_query = "SELECT * FROM dados_sensores"
        cursor.execute(sql_query)

        # Exibir os dados obtidos
        rows = cursor.fetchall()
        if rows:
            print("Dados na tabela dados_sensores:")
            for row in rows:
                print(row)
        else:
            print("Nenhum dado encontrado na tabela.")

    except cx_Oracle.DatabaseError as err:
        print(f"Erro ao consultar dados no banco: {err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# Função de menu principal
def main_menu():
    while True:
        print("\n--- Menu Principal ---")
        print("1. Consultar dados")
        print("2. Inserir dados mockados")
        print("3. Sair")
        choice = input("Escolha uma opção: ")

        if choice == '1':
            fetch_data()
        elif choice == '2':
            insert_mock_data()
        elif choice == '3':
            print("Saindo do programa.")
            break
        else:
            print("Opção inválida. Tente novamente.")

# Executar o menu principal
if __name__ == "__main__":
    main_menu()
