import yfinance as yf
import pandas as pd
import requests
import os

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SAHAM = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "AMMN.JK", "GOTO.JK", "TLKM.JK", "ASII.JK", "ICBP.JK", "UNVR.JK"]

def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "HTML"})

def hitung_macd(df, fast=10, slow=20, signal=7):
    macd = df['Close'].ewm(span=fast, adjust=False).mean() - df['Close'].ewm(span=slow, adjust=False).mean()
    return macd, macd.ewm(span=signal, adjust=False).mean()

for kode in SAHAM:
    try:
        df = yf.download(kode, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 50: continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['MACD'], df['Signal'] = hitung_macd(df)
        df['TR'] = abs(df['High'] - df['Low'])
        atr = df['TR'].rolling(14).mean().iloc[-1]
        last, prev, prev2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
        close, ema20 = float(last['Close']), float(last['EMA20'])
        macd, signal = float(last['MACD']), float(last['Signal'])
        breakout = close > ema20 and float(prev['Close']) <= float(prev['EMA20'])
        golden = (macd > signal and float(prev['MACD']) <= float(prev['Signal'])) or (float(prev['MACD']) > float(prev['Signal']) and float(prev2['MACD']) <= float(prev2['Signal']))
        diatas_nol = macd > 0 and signal > 0
        if breakout and golden and diatas_nol:
            buy_bawah, buy_atas = round(ema20, 0), round(close, 0)
            sl = round(min(float(last['Low']), ema20) - atr * 0.5, 0)
            risk = buy_atas - sl
            tp1, tp2 = round(buy_atas + risk * 1.5, 0), round(buy_atas + risk * 2.5, 0)
            pesan = f"""🚀 <b>SINYAL BREAKOUT - {kode.replace('.JK','')}</b>
💰 <b>Harga:</b> {buy_atas}
📈 <b>EMA20:</b> {buy_bawah}
🎯 <b>AREA BUY:</b> {buy_bawah} - {buy_atas}
🛑 <b>SL:</b> {sl} | ✅ <b>TP1:</b> {tp1} | ✅ <b>TP2:</b> {tp2}
📊 MACD: {macd:.2f} | Signal: {signal:.2f}"""
            kirim_telegram(pesan)
    except Exception as e:
        print(f"Error {kode}: {e}")
