# encoding: utf8

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import datetime, duckdb, requests, pyarrow, time, random


# Classe criada para captura de historico de dados, armazenamento em banco e previsão de indicadores
class FarmTechMeteoData:

    def __init__(self, database):
        self.database = database
        self.connection = None
        self.scaler = StandardScaler()
        self.model = None
        self.trained_model = False
        self.feature_vars = ['nr_temperatura_ambiente', 'nr_temperatura_solo', 'nr_umidade_ar', 'nr_ph_solo']
        self.target_var = 'ic_irrigacao'
        self.refreshed_data = False


    # Realiza conexão com banco de dados
    def get_db_connection(self):
        self.connection = duckdb.connect(self.database)


    def exe_model_training(self, dataframe):
        try:
            # Normalizando as variáveis independentes
            x_scaled = self.scaler.fit_transform(
                dataframe[self.feature_vars]
            )

            # Dividindo os dados em conjunto de treino e teste
            x_train, x_test, y_train, y_test = train_test_split(
                x_scaled, # Dados normalizados para equilibrio de escalas
                dataframe[self.target_var], # dataset com variavel a ser reproduzida na previsao
                test_size= 0.2,  # 20% dos dados para teste e 80% para treino
                random_state= 42 # GPT: Garante que a divisão dos dados seja sempre a mesma, permitindo a reprodutibilidade do processo.
            )

            # Criando o modelo de Random Forest
            self.model = RandomForestClassifier(
                n_estimators= 100, # Quantidade de arvores
                random_state= 42   # Fator de reprodutividade utilizado no treino
            )

            # Treinamento
            self.model.fit(x_train, y_train)
            self.trained_model = True

        except Exception as exc:
            print(str(exc))
            raise


    def get_model_prediction(self, dataframe):
        try:
            # Assegura que o modelo foi treinado previamente
            assert self.trained_model == True, 'O modelo precisa ser treinado'

            dataframe[self.target_var] = self.model.predict(self.scaler.transform(dataframe[self.feature_vars]))

            # Fazendo a previsão com o modelo
            return dataframe

        except Exception as exc:
            print(str(exc))
            raise


    # Função para calcular ph do solo
    def get_ph(
        self,
        temperatura_solo,
        umidade_ar,
        umidade_solo,
        cobertura_nuvem,
        cobertura_nuvem_3km,
        precipitacao
    ):
        """
        O CHAT GPT Disse:
        -
        Temperatura do Solo:
            Quanto mais alta a temperatura do solo, mais ácido ele tende a ser devido à maior atividade microbiana e decomposição orgânica.
            O peso é maior do que a temperatura do ar, pois a temperatura do solo é mais diretamente ligada às propriedades do solo.
        Umidade do Solo:
            Alta umidade do solo tende a neutralizar o pH, evitando que o solo fique muito ácido.
        Umidade Relativa do Ar e Cobertura de Nuvens:
            Indicam condições climáticas que podem afetar indiretamente a retenção de umidade no solo, mas têm um impacto menor no cálculo do pH.
        Cobertura de Nuvens Baixa:
            Pode ter maior impacto local, como manter o solo mais úmido e fresco.
        Precipitação:
            Cada mm de chuva (precipitação) contribui com um aumento proporcional no pH, já que ela dilui a concentração de íons ácidos no solo.
        Limitações:
            O pH é limitado entre 3 e 9 para refletir valores realistas encontrados em solos agrícolas e naturais.
        """

        try:
            # Fatores que influenciam o pH
            fator_temperatura_solo = 7 - (temperatura_solo - 25) * 0.15 # Ajuste para temperatura do solo
            fator_umidade_solo = umidade_solo * 0.05 # Umidade do solo tem maior peso no pH
            fator_umidade_ar = umidade_ar * 0.01 # Umidade do ar tem impacto secundário
            fator_nuvens = (cobertura_nuvem + cobertura_nuvem_3km) * 0.005 # Nuvens têm impacto indireto
            fator_precipitacao = precipitacao * 0.1 # Chuva alta neutraliza a acidez (aumenta pH)

            # Estimativa de pH
            ph_base = fator_temperatura_solo + fator_umidade_solo + fator_umidade_ar + fator_nuvens + fator_precipitacao
            ph_referencia = random.randint(5, 9)

            return round(max(3, min(ph_base, ph_referencia)), 2)
        except Exception as exc:
            print(str(exc))
            raise


    # Função para recuperar dados metereologicos
    def get_weather(
        self,
        latitude= None,
        longitude = None,
        start= None,
        end= None
    ):
        try:
            # Validação de datas de referencia
            date = [*datetime.datetime.now(tz= datetime.timezone.utc).timetuple()]

            if start and end:
                start_date = start
                end_date = end
            else:
                start_date = (datetime.datetime(*date[:4], 0) - datetime.timedelta(days= 90)).date()
                end_date = (datetime.datetime(*date[:4], 0) + datetime.timedelta(days= 7)).date()

            # Validação de latitude e longitude
            if latitude and longitude:
                lat = latitude
                lon = longitude
            else:
                lat = '36.74068642011221'   # PXR7+7JH Kerman, Califórnia, EUA
                lon = '-120.03588642549094' # PXR7+7JH Kerman, Califórnia, EUA

            # Composição de url
            url_absolute = 'https://api.open-meteo.com/v1/forecast{}'
            url_relative = '?timezone={}&latitude={}&longitude={}&start_date={}&end_date={}&hourly={}'
            url_timezone = 'America/Sao_Paulo'
            url_latitude =  lat # PXR5+JXJ Kerman, Califórnia, EUA
            url_longitude = lon # PXR5+JXJ Kerman, Califórnia, EUA
            url_vars = [
                'temperature_2m', # °C (°F) | Temperatura ambiente (2m do solo)
                'relative_humidity_2m', # % | Umidade relativa do ar (2m do solo)
                'precipitation', # mm (inch) | Precipitação total
                'rain', # mm (inch) | Volume de chuva
                'soil_temperature_54cm', # °C (°F) | Temperatura do solo
                'soil_moisture_9_to_27cm', # m³/m³ | Umidade média do solo
                'cloud_cover', # % | Cobertura de nuvens total
                'cloud_cover_low' # % | Cobertura de nuvens a 3km de altitude
            ]

            # Recupera dados de tempo dos ultimos 90 dias
            response = requests.get(
                url = url_absolute.format(
                    url_relative.format(
                        url_timezone,
                        url_latitude,
                        url_longitude,
                        start_date.isoformat(),
                        end_date.isoformat(),
                        ','.join(url_vars)
                    )
                ),
                headers= {
                    'Content-Type': 'application/json'
                }
            )

            assert response.status_code == 200, \
                f'Error getting data. status_code= {response.status_code} | message= {response.text}'

            data = response.json()
            tempo = data.get('hourly', {}).get('time')
            temperatura = data.get('hourly', {}).get('temperature_2m')
            temperatura_solo = data.get('hourly', {}).get('soil_temperature_54cm')
            umidade_ar = data.get('hourly', {}).get('relative_humidity_2m')
            umidade_solo = data.get('hourly', {}).get('soil_moisture_9_to_27cm')
            cobertura_nuvem = data.get('hourly', {}).get('cloud_cover')
            cobertura_nuvem_3km = data.get('hourly', {}).get('cloud_cover_low')
            chuva = data.get('hourly', {}).get('rain')
            precipitacao = data.get('hourly', {}).get('precipitation')

            return [
                {
                    'id_tempo': int(time.mktime(datetime.datetime.strptime(tempo[t], '%Y-%m-%dT%H:%M').timetuple())),
                    'ds_localidade': 'Small Ville',
                    'nr_latitude': response.json().get('latitude'),
                    'nr_longitude': response.json().get('longitude'),
                    'dh_indicador': datetime.datetime.strptime(tempo[t], '%Y-%m-%dT%H:%M'),
                    'dt_indicador': datetime.datetime.strptime(tempo[t], '%Y-%m-%dT%H:%M').date(),
                    'hr_indicador': datetime.datetime.strptime(tempo[t], '%Y-%m-%dT%H:%M').time(),
                    "nr_elevacao": response.json().get('elevation'),
                    'nr_pct_nuvens': cobertura_nuvem[t],
                    'nr_pct_nuvens_baixas': cobertura_nuvem_3km[t],
                    'nr_volume_chuva': chuva[t],
                    'nr_precipitacao': precipitacao[t],
                    'nr_temperatura_ambiente': temperatura[t],
                    'nr_temperatura_solo': temperatura_solo[t],
                    'nr_umidade_ar': umidade_ar[t],
                    'nr_umidade_solo': umidade_solo[t],
                    'nr_ph_solo': self.get_ph(
                        temperatura_solo= temperatura_solo[t],
                        umidade_ar= umidade_ar[t],
                        umidade_solo= umidade_solo[t],
                        cobertura_nuvem= cobertura_nuvem[t],
                        cobertura_nuvem_3km= cobertura_nuvem_3km[t],
                        precipitacao= precipitacao[t]
                    )
                } \
                for t in range(0, len(tempo) , 1) \
                    if None not in [
                        temperatura[t],
                        temperatura_solo[t],
                        umidade_ar[t],
                        umidade_solo[t],
                        cobertura_nuvem[t],
                        cobertura_nuvem_3km[t],
                        precipitacao[t]
                    ]
            ]

        except Exception as exc:
            print(str(exc))
            raise


    # Função para atualizar dadbase com dados metereologicos
    def exe_refresh_meteo_data(self):
        try:
            # Estabelece conexão com database, caso nao exista
            if not self.connection:
                self.get_db_connection()

            # Verifica cria tabela, caso nao exista
            self.connection.execute(
                """
                create table if not exists t_meteo_historic
                (
                    id_tempo integer PRIMARY KEY,
                    ds_localidade varchar,
                    nr_latitude double,
                    nr_longitude double,
                    dh_indicador timestamp,
                    dt_indicador date,
                    hr_indicador time,
                    nr_elevacao double,
                    nr_pct_nuvens double,
                    nr_pct_nuvens_baixas double,
                    nr_volume_chuva double,
                    nr_precipitacao double,
                    nr_temperatura_ambiente double,
                    nr_temperatura_solo double,
                    nr_umidade_ar double,
                    nr_umidade_solo double,
                    nr_ph_solo double
                )
                """
            )

            # Constroi arrow table baseado no resultado da API
            t_meteo_temp = pyarrow.Table.from_pylist(mapping= self.get_weather())

            # Insere dados metereologicos recuperados de API
            self.connection.execute(
                """
                insert into
                    t_meteo_historic
                (
                    id_tempo,
                    ds_localidade,
                    nr_latitude,
                    nr_longitude,
                    dh_indicador,
                    dt_indicador,
                    hr_indicador,
                    nr_elevacao,
                    nr_pct_nuvens,
                    nr_pct_nuvens_baixas,
                    nr_volume_chuva,
                    nr_precipitacao,
                    nr_temperatura_ambiente,
                    nr_temperatura_solo,
                    nr_umidade_ar,
                    nr_umidade_solo,
                    nr_ph_solo
                )
                select
                    x.id_tempo,
                    x.ds_localidade,
                    x.nr_latitude,
                    x.nr_longitude,
                    x.dh_indicador,
                    x.dt_indicador,
                    x.hr_indicador,
                    x.nr_elevacao,
                    x.nr_pct_nuvens,
                    x.nr_pct_nuvens_baixas,
                    x.nr_volume_chuva,
                    x.nr_precipitacao,
                    x.nr_temperatura_ambiente,
                    x.nr_temperatura_solo,
                    x.nr_umidade_ar,
                    x.nr_umidade_solo,
                    x.nr_ph_solo
                from
                    t_meteo_temp as x
                left join
                    t_meteo_historic as y
                on
                    x.id_tempo = y.id_tempo
                where
                    y.id_tempo is null
                """
            )

            self.refreshed_data = True

        except Exception as exc:
            print(str(exc))
            raise


    # Recupera dados metereologicos dos ultimos 90 dias do banco e retorna dataframe pandas
    def get_meteo_training_data(self):
        try:
            # Estabelece conexão com database, caso nao exista
            if not self.connection:
                self.get_db_connection()

            # Garante atualizacao de dados para uso
            if not self.refreshed_data:
                self.exe_refresh_meteo_data()

            # Apaga tabela com dados defasados, caso exista
            self.connection.execute(
                """
                drop table if exists t_meteo_trained
                """
            )

            # Cria tabela de treino com dados mais recentes
            self.connection.execute(
                """
                create table t_meteo_trained as
                select
                    x.id_tempo,
                    x.nr_temperatura_ambiente,
                    x.nr_temperatura_solo,
                    x.nr_umidade_ar,
                    x.nr_ph_solo
                from
                    t_meteo_historic as x
                where
                    x.dt_indicador >= current_date - INTERVAL 90 DAY
                and
                    x.dt_indicador <  current_date
                """
            )

            df = self.connection.sql('select * from t_meteo_trained').df()

            df[self.target_var] = df.apply(lambda _: \
                1 if (_['nr_umidade_ar'] > 60.0) and (_['nr_ph_solo'] >= 6.0 and _['nr_ph_solo'] <= 8.0) else 0, \
                axis=1)

            # Retorna dataframe com base para testes
            return df

        except Exception as exc:
            print(str(exc))
            raise


    # Recupera dados metereologicos dos ultimos 90 dias do banco e retorna dataframe pandas
    def get_meteo_prediction_data(self):
        try:
            # Estabelece conexão com database, caso nao exista
            if not self.connection:
                self.get_db_connection()

            # Garante atualizacao de dados para uso
            if not self.refreshed_data:
                self.exe_refresh_meteo_data()

            if not self.trained_model:
                self.exe_model_training(dataframe= self.get_meteo_training_data())

            # Apaga tabela com dados defasados, caso exista
            self.connection.execute(
                """
                drop table if exists t_meteo_predicted
                """
            )

            # Recupera dataframe para previsao de irrigação
            df = self.connection.sql(
                """
                select
                    x.id_tempo,
                    x.ds_localidade,
                    x.nr_latitude,
                    x.nr_longitude,
                    x.dh_indicador,
                    x.dt_indicador,
                    x.hr_indicador,
                    x.nr_elevacao,
                    x.nr_pct_nuvens,
                    x.nr_pct_nuvens_baixas,
                    x.nr_volume_chuva,
                    x.nr_precipitacao,
                    x.nr_temperatura_ambiente,
                    x.nr_temperatura_solo,
                    x.nr_umidade_ar,
                    x.nr_umidade_solo,
                    x.nr_ph_solo
                from
                    t_meteo_historic as x
                where
                    x.dt_indicador >= current_date - INTERVAL 90 DAY
                """
            )\
            .df()

            # Executa previsao
            df_predicted = self.get_model_prediction(dataframe= df)

            # Grava dataframe de previsao no banco
            self.connection.execute(
                """
                create table t_meteo_predicted as select * from df_predicted
                """
            )

            return df_predicted

        except Exception as exc:
            print(str(exc))
            raise
