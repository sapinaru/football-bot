import telebot
import requests
from datetime import datetime

BOT_TOKEN = "8791813323:AAF-xrGjC50sAErY7PKhs_VU1zHk8m2Us6g"
API_KEY = "ae5092f97932ef372a04bacd5b96512a"
BASE_URL = "https://v3.football.api-sports.io"

bot = telebot.TeleBot(BOT_TOKEN)

# Günlük tüm liglerdeki maçlar
def get_daily_predictions():
    headers = {"x-apisports-key": API_KEY}
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={today}&season=2025"
    response = requests.get(url, headers=headers)
    data = response.json()

    predictions = []
    for match in data["response"]:
        lig_adi = match["league"]["name"]
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        fixture_id = match["fixture"]["id"]

        predictions.append({
            "lig": lig_adi,
            "match": f"{home} vs {away}",
            "fixture_id": fixture_id
        })
    return predictions

# Canlı maçlar
def get_live_matches_all():
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/fixtures?live=all"
    response = requests.get(url, headers=headers)
    data = response.json()

    live_matches = []
    for match in data["response"]:
        lig_adi = match["league"]["name"]
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        goals_home = match["goals"]["home"]
        goals_away = match["goals"]["away"]
        status = match["fixture"]["status"]["long"]
        fixture_id = match["fixture"]["id"]

        live_matches.append({
            "lig": lig_adi,
            "match": f"{home} vs {away}",
            "score": f"{goals_home}-{goals_away}",
            "status": status,
            "fixture_id": fixture_id
        })
    return live_matches

# Ayrıntılı analiz
def get_match_analysis(fixture_id):
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/predictions?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    data = response.json()

    if not data["response"]:
        return None

    pred = data["response"][0]
    home = pred["teams"]["home"]["name"]
    away = pred["teams"]["away"]["name"]

    analysis = {
        "match": f"{home} vs {away}",
        "winner": pred["winner"]["name"] if pred["winner"] else "Berabere",
        "advice": pred["advice"],
        "percent_home": pred["predictions"]["percent"]["home"],
        "percent_draw": pred["predictions"]["percent"]["draw"],
        "percent_away": pred["predictions"]["percent"]["away"]
    }
    return analysis

# Günün en güçlü 3 tahmin
def get_top_predictions():
    headers = {"x-apisports-key": API_KEY}
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?date={today}&season=2025"
    response = requests.get(url, headers=headers)
    data = response.json()

    analyses = []
    for match in data["response"]:
        fixture_id = match["fixture"]["id"]
        pred_url = f"{BASE_URL}/predictions?fixture={fixture_id}"
        pred_resp = requests.get(pred_url, headers=headers).json()
        if not pred_resp["response"]:
            continue

        pred = pred_resp["response"][0]
        home = pred["teams"]["home"]["name"]
        away = pred["teams"]["away"]["name"]
        percent_home = pred["predictions"]["percent"]["home"]
        percent_draw = pred["predictions"]["percent"]["draw"]
        percent_away = pred["predictions"]["percent"]["away"]

        max_prob = max(percent_home, percent_draw, percent_away)
        analyses.append({
            "match": f"{home} vs {away}",
            "winner": pred["winner"]["name"] if pred["winner"] else "Berabere",
            "advice": pred["advice"],
            "probability": max_prob
        })

    top3 = sorted(analyses, key=lambda x: x["probability"], reverse=True)[:3]
    return top3

# Komutlar
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "⚽ Günlük futbol tahmin botuna hoş geldin!")

@bot.message_handler(commands=['tahmin'])
def send_predictions(message):
    preds = get_daily_predictions()
    if not preds:
        bot.send_message(message.chat.id, "Bugün maç yok.")
        return
    text = "📊 Günün Maçları\n"
    for p in preds:
        text += f"- {p['lig']} | {p['match']} | Fixture ID: {p['fixture_id']}\n"
    text += "\nDetaylı analiz için: /analiz <fixture_id>"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['canli'])
def send_live_matches_all_cmd(message):
    matches = get_live_matches_all()
    if not matches:
        bot.send_message(message.chat.id, "Şu anda canlı maç yok.")
        return
    text = "🔥 Canlı Maçlar\n"
    for m in matches:
        text += f"🏆 {m['lig']} | {m['match']} | Skor: {m['score']} | Durum: {m['status']} | Fixture ID: {m['fixture_id']}\n"
    text += "\nDetaylı analiz için: /analiz <fixture_id>"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['analiz'])
def send_analysis(message):
    try:
        fixture_id = int(message.text.split()[1])
    except:
        bot.send_message(message.chat.id, "Lütfen geçerli bir fixture_id gir: /analiz <id>")
        return
    analysis = get_match_analysis(fixture_id)
    if not analysis:
        bot.send_message(message.chat.id, "Bu maç için analiz bulunamadı.")
        return
    text = f"📊 Maç Analizi: {analysis['match']}\n"
    text += f"- Kazanma İhtimali: Ev {analysis['percent_home']}% | Beraberlik {analysis['percent_draw']}% | Deplasman {analysis['percent_away']}%\n"
    text += f"- Tahmin: {analysis['advice']}\n"
    text += f"- Önerilen Sonuç: {analysis['winner']}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['top3'])
def send_top_predictions(message):
    top_matches = get_top_predictions()
    if not top_matches:
        bot.send_message(message.chat.id, "Bugün için öne çıkan maç bulunamadı.")
        return
    text = "🔥 Günün En Güçlü 3 Tahmini\n"
    for m in top_matches:
        text += f"- {m['match']} | Önerilen Sonuç: {m['winner']} | Tahmin: {m['advice']} | Güven: %{m['probability']}\n"
    bot.send_message(message.chat.id, text)

print("Bot çalışıyor...")
bot.polling()
