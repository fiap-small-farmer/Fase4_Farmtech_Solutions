# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="public/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

### FarmTech Solutions Versão atualizada
### Cap 1 - Automação e inteligência na FarmTech Solutions
---
## Nome do grupo

## 👨‍🎓 Integrantes: 
- <a href="https://www.linkedin.com/in/a1exlima/">RM559784@fiap.com.br - Alex da Silva Lima </a>
- <a href="https://www.linkedin.com/in/johnatanloriano/">RM559546@fiap.com.br - Johnatan Sousa Macedo Loriano</a>
- <a href="https://www.linkedin.com/in/matheus-maia-655bb1250/">RM560683@fiap.com.br - Matheus Augusto Rodrigues Maia</a>
- <a href="https://www.linkedin.com/in/brunoconter/">RM560518@fiap.com.br - Bruno Henrique Nielsen Conter</a>
- <a href="https://www.linkedin.com/in/fabiosantoscardoso/">RM560479@fiap.com.br - Fabio Santos Cardoso</a>

## 👩‍🏫 Professores:
### Tutor(a) 
- <a href="https://www.linkedin.com/in/lucas-gomes-moreira-15a8452a/">Lucas Gomes Moreira</a>
### Coordenador(a)
- <a href="https://www.linkedin.com/in/profandregodoi/">André Godoi</a>


## 📜 Descrição

O sistema realiza o monitoramento de parâmetros do solo através de sensores conectados a um ESP32, controlando automaticamente a irrigação com base nas leituras. Os dados são armazenados em um banco de dados SQL para análise histórica.
Funcionalidades Principais

- Monitoramento de umidade do solo (DHT22)
- Simulação de níveis de fósforo e potássio (botões)
- Medição de pH simulada (sensor LDR)
- Controle automatizado de irrigação (relé)
- Armazenamento de dados em banco SQL
- Operações CRUD para gestão dos dados

## Diagrama do Circuito Eletronico

#### Link para o diagrama e código no Wokwi https://wokwi.com/projects/414301079540361217
<p align="center">
<a href= "https://wokwi.com/projects/414301079540361217"><img src="public/circuito_eletronico.png" alt="Circuito eletronico do projeto elaborado no WOKWI" border="0" width=80% height=80%></a>
</p>

#### Link para o diagrama, versão atualizada: https://wokwi.com/projects/414443493615587329
<p align="center">
<a href= "https://wokwi.com/projects/414443493615587329"><img src="public/circuito_eletronico_v2.0.png" alt="Circuito eletronico do projeto elaborado no WOKWI V2.0" border="0" width=80% height=80%></a>
</p>

## Monitor Serial

Monitor Serial mostrando o acionamento e comunicação dos dados de leitura e timestamp.

<p align="center">
<a href= ""><img src="public/monitor_serial.png" alt="Monitor serial apresentando o acionamento do sistema de irrigação e comunicação com o banco de dados" border="0" width=80% height=80%></a>
</p>

Monitor Serial após as atualizações para envio dos dados via MQTT.

<p align="center">
<a href= ""><img src="public/monitor_serial_v2.0.png" alt="Monitor serial atualizado" border="0" width=80% height=80%></a>
</p>

## Funcionamento do Equipamento

Este projeto visa a implementação de um sistema de irrigação inteligente e automatizado que monitora as condições do solo em tempo real e ajusta a irrigação conforme a necessidade. Utilizando um ESP32 e sensores simulados na plataforma Wokwi, o sistema capta informações cruciais sobre a qualidade do solo, executando o controle automatizado da irrigação.

#### Componentes Principais

1. **Microcontrolador ESP32**:
   - Atua como núcleo de controle do sistema, recebendo dados de sensores e acionando a irrigação conforme parâmetros definidos. Também envia dados para armazenamento e consulta posterior no banco de dados SQL.

2. **Sensores Simulados**:
   - **Sensor de Umidade (DHT22)**: Mede a umidade do solo em percentual. Quando a umidade cai abaixo de um limite (ex.: 60%), a irrigação é acionada.
   - **Sensor de pH (LDR - Resistor Dependente de Luz)**: Simula o nível de pH variando de 0 a 14 (representando a faixa de pH). Este sensor permite que a irrigação seja ajustada com base no pH.
   - **Sensor de Fósforo (Botão)** e **Sensor de Potássio (Botão)**: Simulam os sensores de nutrientes em um nível binário (ativo/inativo). A irrigação é ativada apenas quando pelo menos um dos nutrientes está em nível "ativo".

3. **Atuador de Irrigação (Relé)**:
   - Representa a bomba de água. Quando a irrigação é ativada, o relé liga a bomba e permite que a água flua. Seu status é exibido por um LED de acionamento do relé.

#### Lógica de Funcionamento

1. **Leitura dos Sensores**:
   - A cada ciclo, o sistema lê a umidade (DHT22), o pH (LDR) e o status dos botões de fósforo e potássio.
   - Esses dados são exibidos no Monitor Serial e armazenados para análise.

2. **Decisão de Irrigação**:
   - A bomba d’água é ativada somente quando:
     - A umidade está abaixo do limite (ex.: 60%);
     - O nível de pH está entre os valores mínimo e máximo definidos (ex.: entre 6 e 8);
     - Pelo menos um dos nutrientes (representados pelos botões de fósforo ou potássio) está em estado ativo.
   - Se todas as condições são atendidas, o sistema aciona o relé, ligando a bomba. Caso contrário, o relé permanece desligado.

3. **Envio e Armazenamento dos Dados**:
   - Dados do monitor serial são transferidos para um banco de dados SQL por meio de operações CRUD, em um sistema Python, onde podem ser armazenados, visualizados e analisados.

4. **Consulta e Monitoramento via Python**:
   - O sistema de consulta em Python permite visualizar o histórico de dados coletados, possibilitando a análise de padrões de umidade, pH e status dos nutrientes.
   - O código Python integrado ao banco de dados registra o histórico de acionamento da irrigação (quando o relé ligou ou desligou), criando uma base de dados para análise futura e tomada de decisão mais precisa.

#### Aplicação do Projeto

Este sistema de irrigação inteligente é projetado para otimizar o uso da água, atendendo as necessidades agrícolas com maior precisão e eficiência. Em uma aplicação real, essa abordagem ajudaria a reduzir desperdícios e aumentar a produtividade agrícola ao monitorar continuamente as condições do solo e agir em tempo real para ajustar a irrigação.


## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- <b>.github</b>: Nesta pasta ficarão os arquivos de configuração específicos do GitHub que ajudam a gerenciar e automatizar processos no repositório.

- <b>assets</b>: aqui estão os arquivos relacionados a elementos não-estruturados deste repositório, como imagens.

- <b>config</b>: Posicione aqui arquivos de configuração que são usados para definir parâmetros e ajustes do projeto.

- <b>document</b>: aqui estão todos os documentos do projeto que as atividades poderão pedir. Na subpasta "other", adicione documentos complementares e menos importantes.

- <b>scripts</b>: Posicione aqui scripts auxiliares para tarefas específicas do seu projeto. Exemplo: deploy, migrações de banco de dados, backups.

- <b>src</b>: Todo o código fonte criado para o desenvolvimento do projeto ao longo das 7 fases.

- <b>README.md</b>: arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

## Arquivos Importantes

- **Circuito Eletrônico**: Diagrama eletrônico do sistema.
  - [circuito_eletronico.png](document/diagramas/circuito_eletronico.png)

- **Projeto Wokwi**: Link para o projeto no Wokwi.
  - [projeto_wokwi.md](document/diagramas/projeto_wokwi.md)
  
- **Código Arduino**: Código desenvolvido para o ESP32.
  - [sketch.ino](src/WOKWI/sketch.ino)
  
- **Diagrama do Wokwi**: Diagrama das peças no Wokwi.
  - [diagram.json](src/WOKWI/diagram.json)
  
- **Código Python (CRUD)**: Código responsável por alimentar o banco SQL.
  - [CRUD.py](src/Python/CRUD.py)
  
- **Link para o Video no YouTube**: Link para o vídeo
	- [link_para_o_video.txt](document/youtube/link_para_o_video.txt)
  
## 📺 **Link para o vídeo no YouTube**

- [Assistir ao vídeo do projeto no YouTube](https://www.youtube.com/watch?v=bDgtLsDA9ik)


## 🔧 Como executar o código

### Ferramentas Necessárias

1. **IDE Arduino**: Para compilar e carregar o código para o microcontrolador ESP32.
   - **Versão recomendada**: 1.8.x ou superior.
   - **Bibliotecas**: 
     - `DHT.h` para o sensor DHT22.
     - `WiFi.h` para conectividade com a rede Wi-Fi.
  
2. **Python**:
   - **Versão recomendada**: 3.6 ou superior.
   - **Bibliotecas**:
     - `cx_Oracle` para conectar ao banco de dados Oracle.
     - `datetime` para manipulação de data e hora.
     - `os` para manipulação do sistema operacional.
  
3. **Banco de Dados Oracle** (Local ou Nuvem):
   - Deve estar configurado com as tabelas adequadas para armazenar os dados dos sensores e do sistema de irrigação.

### Passo a Passo para Rodar o Projeto

#### 1. Configuração do Banco de Dados

- **Criar as Tabelas**: O banco de dados deve ter uma estrutura que armazene as leituras dos sensores e os eventos de irrigação. Exemplo de tabela:

```sql
CREATE TABLE sensor_data (
  id NUMBER PRIMARY KEY,
  humidity NUMBER,
  ph_value NUMBER,
  phosphorus BOOLEAN,
  potassium BOOLEAN,
  irrigation_status BOOLEAN,
  timestamp TIMESTAMP
);
```
#### 2.Carregar o Código para o ESP32
- Abra o arquivo src/WOKWI/sketch.ino na IDE Arduino.
- Conecte o ESP32 ao seu computador.
- Selecione a placa ESP32 e a porta correta na IDE.
- Carregue o código no ESP32.

#### 3. Executar o Código Python
- Instale as dependências necessárias para conectar ao banco de dados Oracle:
```bash
pip install cx_Oracle
```
- Configure as credenciais do banco de dados Oracle no código Python.
- Execute o arquivo **src/Python/CRUD.py** para que os dados sejam inseridos no banco de dados a partir das leituras simuladas dos sensores.

#### 4. Testar o Sistema

- Acompanhe as leituras no Monitor Serial da IDE Arduino.
- Observe a ativação/desativação da bomba de irrigação com base nas condições dos sensores.
- Verifique a inserção dos dados no banco de dados via script Python.


## 🗃 Histórico de lançamentos

* 1.0.0 - 12/11/2024


## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>


