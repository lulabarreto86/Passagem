# Progresso da configuração

Última atualização: 12/11/2026

- [x] Criar bot no Telegram (@passagens_lula_bot)
- [x] Descobrir o TELEGRAM_CHAT_ID (anotado na conversa com o Claude)
- [ ] Trocar o token do bot com `/revoke` no @BotFather (o token antigo apareceu em um print)
- [x] Criar conta na Travelpayouts
- [ ] **← PAROU AQUI:** achar o **API token** da Travelpayouts
  - Ícone 👤 no canto inferior esquerdo do painel → Profile / Account → campo "API token"
  - O token certo é longo, com letras e números (~32 caracteres). Um código curto, só com números, é o ID de parceiro e não serve.
  - Se pedir um projeto, use o link `https://t.me/passagens_lula_bot` (o link do GitHub foi recusado)
- [ ] Cadastrar no GitHub (Settings → Secrets and variables → Actions): `TRAVELPAYOUTS_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- [ ] Settings → Actions → General → Workflow permissions → "Read and write permissions"
- [ ] Testar: aba Actions → Monitorar passagens → Run workflow
- [ ] Trocar as rotas de exemplo do `config.yaml` pelas viagens reais
