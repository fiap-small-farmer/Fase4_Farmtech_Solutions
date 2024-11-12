import cx_Oracle
import paho.mqtt.client as mqtt
import json
import random
import time

# Configurações do banco de dados Oracle
db_config = {
    'user': 'rm560518',
    'password': '230186',
    'dsn': 'oracle.fiap.com.br',  # Pode ser o TNS ou uma string de conexão
}

# Configurações do broker MQTT
mqtt_broker = "broker.mqtt.com"
mqtt_port = 1883
mqtt_topic = "farmtech/sensorData"

# Função para inserir dados no banco de dados Oracle
def insert_into_db(sensor_data):
    try:
        # Conectar ao banco de dados Oracle
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()

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

        # Confirmar a transação
        conn.commit()
        print("Dados inseridos no banco de dados com sucesso.")

    except cx_Oracle.DatabaseError as err:
        print(f"Erro ao inserir dados no banco: {err}")
    finally:
        cursor.close()
        conn.close()

# Função callback para quando uma mensagem é recebida
def on_message(client, userdata, message):
    try:
        # Decodificar a mensagem recebida
        message_payload = message.payload.decode("utf-8")
        sensor_data = json.loads(message_payload)

        # Exibir e inserir dados no banco
        print(f"Dados recebidos: {sensor_data}")
        insert_into_db(sensor_data)

    except json.JSONDecodeError:
        print("Erro ao decodificar a mensagem JSON")

# Função para gerar dados mockados
def generate_mock_data():
    sensor_data = {
        'umidade': round(random.uniform(30.0, 90.0), 2),  # Umidade entre 30% e 90%
        'ph': round(random.uniform(5.5, 8.5), 2),         # pH entre 5.5 e 8.5
        'fosforo': round(random.uniform(1.0, 5.0), 2),    # Fósforo entre 1.0 e 5.0
        'potassio': round(random.uniform(0.5, 3.0), 2)    # Potássio entre 0.5 e 3.0
    }
    return sensor_data

# Função para publicar dados mockados no MQTT
def publish_mock_data():
    client = mqtt.Client("PythonMQTTClient")
    client.connect(mqtt_broker, mqtt_port)

    # Gerar e publicar dados mockados a cada 5 segundos
    while True:
        mock_data = generate_mock_data()
        payload = json.dumps(mock_data)
        client.publish(mqtt_topic, payload)
        print(f"Publicado dados no tópico {mqtt_topic}: {mock_data}")
        time.sleep(5)

# Iniciar a publicação de dados mockados
publish_mock_data()

# Configuração do cliente MQTT para receber dados
client = mqtt.Client("PythonMQTTClient")
client.connect(mqtt_broker, mqtt_port)

# Assinar o tópico e configurar o callback
client.subscribe(mqtt_topic)
client.on_message = on_message

# Iniciar o loop do cliente MQTT
print("Aguardando dados MQTT...")
client.loop_forever()
