# encoding: utf8

from pathlib import Path
from utils import meteo as m, sensor as s
import duckdb, streamlit as st, time


# Page config | fav icon e layout base
st.set_page_config(
    page_title="FarmTech", page_icon="✅", layout="wide"
)

# Titulo da pagina
st.title(
    "Farmtech - Acompanhamento de sensores"
)

# Container de um elemento
placeholder = st.empty()


def main():

    # Resolve diretorio onde o database será armazenado
    def get_database_path():
        try:
            database_dir = Path.cwd().parent / 'data'
            databse_name = 'farmtech.db'
            if not database_dir.exists():
                _ = database_dir.mkdir(parents= True)
            with duckdb.connect(f'{database_dir}/{databse_name}') as _:
                pass
            return f'{database_dir}/{databse_name}'
        except Exception as exc:
            print(str(exc))
            raise


    # Gerador de indicadores
    def get_kpi(connection):
        df_sensor_ultimos_indicadores = connection.sql(
            """
            with
                t_meteo as
            (
                select
                    cast(cast(dt_indicador as date) as varchar) as data,
                    cast(cast(hr_indicador as time) as varchar) as hora,
                    cast(avg(nr_temperatura_ambiente) as integer) as nr_temperatura_ambiente,
                    cast(avg(nr_temperatura_solo) as integer) as nr_temperatura_solo,
                    cast(avg(nr_umidade_ar) as integer) as nr_umidade_ar,
                    cast(avg(nr_umidade_solo) as integer) as nr_umidade_solo
                from
                    t_meteo_predicted
                where
                    dt_indicador = current_date
                group by
                    dt_indicador, hr_indicador
                order by
                    dt_indicador, hr_indicador
            ),
                t_sensor as
            (
                select
                    cast(dt_sensor as varchar) as data,
                    cast(hr_sensor as varchar) as hora,
                    hr_sensor,
                    nr_umidade_ar,
                    nr_ph_solo,
                    ic_fosforo,
                    ic_potassio,
                    ic_irrigacao,
                    row_number() over(order by dh_sensor asc)  as cd_evento,
                    row_number() over(order by dh_sensor desc) as ix_evento
                from
                    t_sensor_historic
                where
                    cast(dt_sensor as date)
                =
                    cast(current_date as date)
            )
            select distinct
                x.data,
                x.hora,
                x.nr_umidade_ar,
                y.nr_umidade_solo,
                x.nr_ph_solo,
                x.ic_fosforo,
                x.ic_potassio,
                x.ic_irrigacao
            from
                t_sensor as x
            left join
                t_meteo as y
            on
                cast(x.data as date) = cast(y.data as date)
            and
                hour(cast(x.hora as time)) = hour(cast(y.hora as time))
            order by
                ix_evento
            """
        )\
        .fetchnumpy()

        qt_avaliacaoes_realizadas_hoje = connection.sql(
            """
            select
                cast(count(*) as integer) as qt_evento
            from
                t_sensor_historic
            where
                cast(dt_sensor as date)
            =
                cast(current_date as date)
            """
        )\
        .fetchnumpy()

        qt_irrigacoes_realizadas_hoje = connection.sql(
            """
            select
                cast(sum(ic_irrigacao) as integer) as qt_evento
            from
                t_sensor_historic
            where
                cast(dt_sensor as date)
            =
                cast(current_date as date)
            """
        ).fetchnumpy()


        qt_irrigacoes_previstas_hoje = connection.sql(
            """
            select
                cast(sum(ic_irrigacao) as integer) as qt_evento
            from
                t_meteo_predicted
            where
                cast(dt_indicador as date)
            =
                cast(current_date as date)
            """
        ).fetchnumpy()

        df_sensor_proximos_indicadores_7d = connection.sql(
            """
            select
                cast(cast(dt_indicador as date) as varchar) as data,
                cast(avg(nr_temperatura_ambiente) as integer) as nr_temperatura_ambiente,
                cast(avg(nr_temperatura_solo) as integer) as nr_temperatura_solo,
                cast(avg(nr_umidade_ar) as integer) as nr_umidade_ar,
                cast(avg(nr_umidade_solo) as integer) as nr_umidade_solo,
                cast(avg(nr_ph_solo) as integer) as nr_ph_solo,
                cast(sum(ic_irrigacao) as integer) as qt_irrigacao
            from
                t_meteo_predicted
            where
                dt_indicador > current_date
            and
                dt_indicador < current_date + INTERVAL 8 DAY
            group by
                dt_indicador
            order by
                dt_indicador
            """
        )\
        .fetchnumpy()

        return [
            df_sensor_ultimos_indicadores,
            qt_avaliacaoes_realizadas_hoje,
            qt_irrigacoes_realizadas_hoje,
            qt_irrigacoes_previstas_hoje,
            df_sensor_proximos_indicadores_7d
        ]


    # Endereços de referencia | Database e Broker
    BROKER = 'broker.mqtt-dashboard.com'
    TOPIC = 'farmTechSolutions'
    DATABASE = get_database_path()

    # Inicializa database e atualiza bases
    meteo = m.FarmTechMeteoData(database= DATABASE)

    # Recupera dataset meterologico com previsoes realizadas
    _ = meteo.get_meteo_prediction_data()

    # Abre conexão com broker para recebimento de dados
    with s.FarmTechSensorData(database= DATABASE, broker= BROKER, topic= TOPIC) \
        as session:

        # Contador de eventos. Utilizado para renovar base de previsao
        counter = 0

        while True:
            # Recupera novas mensagens no broker
            _ = session.get_messages()

            with duckdb.connect(database= DATABASE) as connection:

                kpis = get_kpi(connection= connection)

                # Controla renovação de base de previsões para nao interferir no desempenho geral
                if counter == 100:
                    _ = meteo.exe_refresh_meteo_data()
                    counter = 0
                else:
                    counter += 1

                ###### Geração de indicadores

                df_sensor_ultimos_indicadores = kpis[0]
                qt_avaliacaoes_realizadas_hoje = kpis[1]
                qt_irrigacoes_realizadas_hoje = kpis[2]
                qt_irrigacoes_previstas_hoje = kpis[3]
                df_sensor_proximos_indicadores_7d = kpis[4]

                # Indicadores streamlit
                with placeholder.container():
                    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6, kpi7, kpi8 = st.columns(8)

                    kpi1.metric(label="Data Referência",
                        value= df_sensor_ultimos_indicadores['data'][0],
                        delta= df_sensor_ultimos_indicadores['data'][0], label_visibility= 'visible')

                    kpi2.metric(label="Qtd. Avaliações",
                        value= qt_avaliacaoes_realizadas_hoje['qt_evento'].item(),
                        delta= qt_avaliacaoes_realizadas_hoje['qt_evento'].item(), label_visibility= 'visible')
                    
                    kpi3.metric(label="Qtd. Irrigações Previstas",
                        value= qt_irrigacoes_previstas_hoje['qt_evento'].item(),
                        delta= qt_irrigacoes_previstas_hoje['qt_evento'].item(), label_visibility= 'visible')

                    kpi4.metric(label="Qtd. Irrigações Realizadas",
                        value= qt_irrigacoes_realizadas_hoje['qt_evento'].item(),
                        delta= qt_irrigacoes_realizadas_hoje['qt_evento'].item(), label_visibility= 'visible')

                    table1, table2 = st.columns(2)

                    with table1:
                        st.markdown("### Avaliações Realizadas")
                        st.dataframe(df_sensor_ultimos_indicadores, hide_index= True)

                    with table2:
                        st.markdown("### Irrigações Previstas (7 Dias)")
                        st.dataframe(df_sensor_proximos_indicadores_7d, hide_index= True)
                    
            # Intervalo entre atualização de indicadores
            time.sleep(1)


if __name__ == '__main__':
    main()
