import os
import json
import urllib.request
import urllib.parse

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Armazena a API key do Gemini por usuário (em memória)
user_gemini_keys = {}
# Aguardando API key
waiting_for_key = set()
# Histórico de conversa por usuário
user_history = {}

def telegram_request(method, data):
    url = f"{TELEGRAM_API}/{method}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Telegram API error: {e}")
        return {}

def send_message(chat_id, text, parse_mode="Markdown"):
    return telegram_request("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    })

def send_action(chat_id, action="typing"):
    telegram_request("sendChatAction", {"chat_id": chat_id, "action": action})

def ask_gemini(api_key, history, user_message):
    history.append({"role": "user", "parts": [{"text": user_message}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = json.dumps({"contents": history}).encode()
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        history.append({"role": "model", "parts": [{"text": reply}]})
        return reply, history
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        msg = body.get("error", {}).get("message", "Erro desconhecido")
        return f"❌ Erro no Gemini: {msg}", history
    except Exception as e:
        return f"❌ Erro: {str(e)}", history

def process_update(update):
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text:
        return

    # /start
    if text == "/start":
        user_history[chat_id] = []
        waiting_for_key.add(chat_id)
        user_gemini_keys.pop(chat_id, None)
        send_message(chat_id,
            "👋 Olá! Sou um bot com IA do Google Gemini.\n\n"
            "Para começar, me manda sua *API Key do Gemini*.\n\n"
            "Você pode gerar uma gratuitamente em:\n"
            "https://aistudio.google.com/app/apikey"
        )
        return

    # /reset
    if text == "/reset":
        user_history[chat_id] = []
        send_message(chat_id, "🔄 Conversa reiniciada!")
        return

    # /newkey
    if text == "/newkey":
        waiting_for_key.add(chat_id)
        user_gemini_keys.pop(chat_id, None)
        send_message(chat_id, "🔑 Me manda a nova API Key do Gemini:")
        return

    # Aguardando API key
    if chat_id in waiting_for_key:
        api_key = text.strip()
        # Validar a key rapidamente
        test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(test_url)
        try:
            with urllib.request.urlopen(req) as resp:
                json.loads(resp.read())
            user_gemini_keys[chat_id] = api_key
            waiting_for_key.discard(chat_id)
            user_history[chat_id] = []
            send_message(chat_id,
                "✅ API Key válida! Pode começar a conversar.\n\n"
                "Comandos disponíveis:\n"
                "• /reset — reinicia a conversa\n"
                "• /newkey — troca a API key"
            )
        except urllib.error.HTTPError:
            send_message(chat_id,
                "❌ API Key inválida. Tenta de novo ou gera uma nova em:\n"
                "https://aistudio.google.com/app/apikey"
            )
        return

    # Sem API key configurada
    if chat_id not in user_gemini_keys:
        send_message(chat_id,
            "⚠️ Você ainda não configurou sua API Key.\n"
            "Use /start para começar."
        )
        return

    # Responder com Gemini
    send_action(chat_id, "typing")
    api_key = user_gemini_keys[chat_id]
    history = user_history.get(chat_id, [])
    reply, updated_history = ask_gemini(api_key, history, text)
    user_history[chat_id] = updated_history
    send_message(chat_id, reply)

def run():
    print("🤖 Bot iniciado! Aguardando mensagens...")
    offset = 0

    while True:
        try:
            url = f"{TELEGRAM_API}/getUpdates?timeout=30&offset={offset}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read())

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                try:
                    process_update(update)
                except Exception as e:
                    print(f"Erro ao processar update: {e}")

        except Exception as e:
            print(f"Erro no loop principal: {e}")
            import time
            time.sleep(5)

if __name__ == "__main__":
    run()
