# Passagem: agente de promoções de passagens aéreas ✈️

Um robô que **pesquisa preços de passagens sozinho, de tempos em tempos**, guarda
o histórico e **avisa no Telegram** quando encontra uma promoção.

Ele roda de graça no **GitHub Actions** (a cada 6 horas, por padrão), sem precisar
de computador ligado.

## Quando ele considera "promoção" (passagens em dinheiro)

Para cada rota, o agente pega a oferta mais barata e avisa se:

1. o preço ficou **abaixo do seu limite** (`preco_maximo`);
2. o preço está **X% abaixo do típico** daquela rota (mediana das medições
   anteriores; `queda_minima_pct`, padrão 20%);
3. (Google Flights) o próprio Google classifica o preço como **baixo**.

Se, além disso, for o **menor preço já registrado**, o aviso diz isso também.
O critério 2 precisa de pelo menos 5 medições da rota (uns 5 dias) para começar.

Para não lotar seu celular, ele só repete o aviso da mesma rota depois de 3 dias
ou se o preço cair pelo menos mais 3%.

## Resumo semanal

Todo domingo, por volta das 9h (horário do Nordeste), o bot manda um resumo com o
menor preço de cada destino e a variação em relação à semana anterior, mesmo sem
promoção. Configure na seção `resumo_semanal` do `config.yaml`. Para receber um
resumo na hora: aba **Actions → Monitorar passagens → Run workflow**, marcando
"Enviar o resumo semanal agora".

## Fontes

| Seção do `config.yaml` | Fonte | Custo | Observações |
|---|---|---|---|
| `explorar` | "Explorar" do Google Flights (SerpApi) | Grátis até 250 buscas/mês | **Fonte principal.** Uma busca traz ~90 destinos a partir de uma cidade. Filtra por cidades/países e duração em dias. Roda 1x por dia para caber na cota. |
| `rotas` | Travelpayouts (cache da Aviasales) | Grátis | Complemento, roda a cada 6h. Bom para rotas populares; tem poucos dados para origens menores e datas distantes. |
| `milhas` | Blogs de milhas (RSS) | Grátis | Avisa notícias de promoções da **Smiles** (ou outras palavras). Não acessa o site da Smiles. |

## Como configurar (passo a passo)

### 1. Escolha as rotas

Edite o [`config.yaml`](config.yaml):

```yaml
rotas:
  - origem: SAO        # código IATA (SAO = todos os aeroportos de SP)
    destino: LIS
    ida: "2027-03"     # mês inteiro ou data exata "2027-03-15"
    volta: "2027-03"   # remova para "só ida"
    preco_maximo: 3500
```

### 2. Crie as chaves (gratuitas)

- **Travelpayouts:** crie uma conta em <https://www.travelpayouts.com/> e copie o
  *API token* no seu perfil.
- **Bot do Telegram:**
  1. No Telegram, fale com **@BotFather**, envie `/newbot` e copie o **token**.
  2. Mande qualquer mensagem para o seu bot novo.
  3. Abra `https://api.telegram.org/bot<TOKEN>/getUpdates` no navegador e copie
     o número em `"chat":{"id": ...}`. Esse é o **chat id**.
- **SerpApi** (busca do Google Flights): crie a conta em <https://serpapi.com/> e copie a *API key*.

### 3. Cadastre as chaves no GitHub

No repositório: **Settings → Secrets and variables → Actions → New repository secret**:

| Nome | Valor |
|---|---|
| `TRAVELPAYOUTS_TOKEN` | token da Travelpayouts |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ID` | seu chat id |
| `SERPAPI_KEY` | chave da SerpApi |

### 4. Ligue o agente

- Em **Settings → Actions → General → Workflow permissions**, marque
  **Read and write permissions**. Assim o agente consegue salvar o histórico de preços.
- Na aba **Actions**, abra *Monitorar passagens* e clique em **Run workflow**
  para testar na hora.

> ⚠️ Agendamentos do GitHub Actions só funcionam no **branch padrão** do
> repositório. Depois de juntar estas mudanças no `main`, ele passa a rodar sozinho.

Para mudar a frequência, edite a linha `cron` em
[`.github/workflows/monitorar.yml`](.github/workflows/monitorar.yml).

## Rodar no seu computador

```bash
pip install -r requirements.txt
export TRAVELPAYOUTS_TOKEN=...
python -m agente --simular   # só mostra na tela, sem Telegram e sem salvar histórico
python -m agente             # execução normal
```

Testes: `pip install pytest && python -m pytest`

## Estrutura

```
agente/
  __main__.py        # orquestra: busca → analisa → avisa → salva histórico
  analise.py         # regras de "é promoção?"
  explorar.py        # busca "Explorar" do Google (várias origens × destinos)
  milhas.py          # promoções de milhas lidas dos blogs (RSS)
  historico.py       # histórico de preços em data/historico.json
  notificacao.py     # mensagens do Telegram
  fontes/            # integrações com as APIs de preço
config.yaml          # suas rotas
```
