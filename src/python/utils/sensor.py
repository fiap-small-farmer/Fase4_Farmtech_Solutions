# encoding: utf8

from pathlib import Path
from queue import Queue
from paho.mqtt import client as mqtt
import datetime, duckdb, json, time


class FarmTechSensorData:

    # Metodo padrão de instancia
    def __init__(self, broker = 'broker.mqtt-dashboard.com', topic = 'farmTechSolutions', port= 1883):
        self.connection = None
        self.broker = broker
        self.topic = topic
        self.port = port
        self.client = None
        self.messages = Queue()


    # Realiza conexão com banco de dados
    def get_db_connection(self):
        # Cria dirtorio para o database
        root_dir = Path.cwd().parent
        data_dir = root_dir / 'data'
        data_file = data_dir / 'farmtech.db'

        try:
            assert data_file.exists() == True, \
                'Database nao existe ou não foi encontrado'
            connection = duckdb.connect(data_file)
        except Exception as exc:
            print(str(exc))
            raise
        else:
            # Define conexao de referencia
            self.connection = connection


    # Callback executado quando o cliente se conecta ao broker
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.topic)
            print('Conexão realizada com sucesso.')
        else:
            print(f'Falha na conexão, código de retorno: {rc}.')


    # Callback executado quando a conexão é perdida
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print('Conexão com o broker perdida. Tentando reconectar...')
        else:
            print('Desconectado do broker com sucesso.')


    # Callback executado ao receber uma mensagem no tópico inscrito e gravar no banco de dados
    def on_message(self, client, userdata, msg):
        try:
            # Estabelece conexão com database
            if not self.connection:
                self.get_db_connection()

            message = json.loads(msg.payload.decode('utf-8'))

            sensor_date = [*datetime.datetime.strptime(message.get('data'), '%d/%m/%Y').timetuple()]
            sensor_time = [int(t) for t in message.get('hora').split(':')]
            sensor_datetime = datetime.datetime(*sensor_date[:3], *sensor_time[:3])
            meteo_datetime = datetime.datetime(*sensor_date[:3], *sensor_time[:1])

            # Define registro a ser incluida no banco
            sensor_data = {
                'id_sensor': int(time.mktime(sensor_datetime.timetuple())),
                'id_tempo': int(time.mktime(meteo_datetime.timetuple())),
                'dh_sensor': sensor_datetime,
                'dt_sensor': sensor_datetime.date(),
                'hr_sensor': sensor_datetime.time(),
                'nr_umidade_ar': message.get('humidade'),
                'nr_ph_solo': message.get('ph'),
                'ic_fosforo': message.get('fosforo'),
                'ic_potassio': message.get('potassio'),
                'ic_irrigacao': message.get('irrigacao')
            }

            self.connection.execute(
                """
                create table if not exists t_sensor_historic
                (
                    id_sensor integer PRIMARY KEY,
                    id_tempo integer,
                    dh_sensor timestamp,
                    dt_sensor date,
                    hr_sensor time,
                    nr_umidade_ar double,
                    nr_ph_solo double,
                    ic_fosforo integer,
                    ic_potassio integer,
                    ic_irrigacao integer
                )
                """
            )

            sensor_query = \
                """
                insert into t_sensor_historic
                (
                    id_sensor,
                    id_tempo,
                    dh_sensor,
                    dt_sensor,
                    hr_sensor,
                    nr_umidade_ar,
                    nr_ph_solo,
                    ic_fosforo,
                    ic_potassio,
                    ic_irrigacao
                )
                values
                (
                    ?,?,?,?,?,?,?,?,?,?
                )
                on conflict do nothing
                """

            self.connection.execute(
                sensor_query, (
                    sensor_data.get('id_sensor'),
                    sensor_data.get('id_tempo'),
                    sensor_data.get('dh_sensor'),
                    sensor_data.get('dt_sensor'),
                    sensor_data.get('hr_sensor'),
                    sensor_data.get('nr_umidade_ar'),
                    sensor_data.get('nr_ph_solo'),
                    sensor_data.get('ic_fosforo'),
                    sensor_data.get('ic_potassio'),
                    sensor_data.get('ic_irrigacao')
                )
            )

            # Exibe os dados recebidos em formato JSON
            self.messages.put(item= message)

        except json.JSONDecodeError as exc:
            print(f'Erro ao decodificar a mensagem JSON. {str(exc)}')
            raise


    # Recupera client baseado em parametros de instancia
    def get_session(self):
        try:
            self.client = mqtt.Client()  
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
        except Exception as exc:
            print(f'Problemas ao adquirir client {str(exc)}')
            raise


    # Recupera mensagem enviada para o tópico do broker
    def get_messages(self):
        while True:
            yield self.messages.get(block= True)


    # Métodos para inicializar o context manager
    def __enter__(self):
        if not self.client:
            self.get_session()
        return self


    # Métodos para finalizar o context manager
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.loop_stop()
