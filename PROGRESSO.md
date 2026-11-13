# Progresso da configuração

Última atualização: 13/11/2026

- [x] Criar bot no Telegram (@passagens_lula_bot)
- [x] Descobrir o TELEGRAM_CHAT_ID (anotado na conversa com o Claude)
- [x] Trocar o token do bot com `/revoke` no @BotFather (o token antigo apareceu em um print)
- [x] Criar conta na Travelpayouts
- [x] Achar o **API token** da Travelpayouts
  - Ícone 👤 no canto inferior esquerdo do painel → Profile / Account → campo "API token"
  - O token certo é longo, com letras e números (~32 caracteres). Um código curto, só com números, é o ID de parceiro e não serve.
  - Se pedir um projeto, use o link `https://t.me/passagens_lula_bot` (o link do GitHub foi recusado)
- [x] Cadastrar no GitHub (Settings → Secrets and variables → Actions): `TRAVELPAYOUTS_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- [x] Settings → Actions → General → Workflow permissions → "Read and write permissions"
- [x] Testar: aba Actions → Monitorar passagens → Run workflow
- [x] Trocar as rotas de exemplo pelas viagens reais (abril/2027 saindo de Natal, João Pessoa e Recife)
- [x] Criar conta na SerpApi e cadastrar `SERPAPI_KEY` no GitHub
- [x] Busca "Explorar" do Google Flights (1x por dia) + alertas de promoções Smiles pelos blogs de milhas
- [ ] Acompanhar os primeiros dias: os alertas de "abaixo do normal" começam depois de ~5 dias de histórico
- [ ] (Opcional) Seats.aero para acompanhar a quantidade exata de milhas por rota (pago)
