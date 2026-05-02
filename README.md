# 🤖 Bot Telegram + Gemini

Bot do Telegram que responde mensagens usando a API do Gemini (Google AI).

## Como usar

1. Adicione o secret `TELEGRAM_BOT_TOKEN` no repositório
   - Settings → Secrets and variables → Actions → New repository secret
2. Rode o workflow manualmente em Actions → "Telegram Bot" → Run workflow

## Comandos

- `/start` — configura sua API Key do Gemini
- `/reset` — reinicia a conversa
- `/newkey` — troca a API Key

## Observação

O GitHub Actions tem limite de 6 horas por execução.
Para manter o bot rodando continuamente, re-execute o workflow manualmente
ou configure um cron no workflow.
