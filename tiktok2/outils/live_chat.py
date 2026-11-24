"""Enregistre le chat Twitch d'une chaîne (anonyme) : <fichier> = lignes « epoch<TAB>pseudo<TAB>message ».
Usage : python3 live_chat.py <chaine> <fichier>"""
import os, sys, time, random, websocket
ch, path = sys.argv[1], sys.argv[2]
px = os.environ.get("HTTPS_PROXY", "").replace("http://", "").split(":")
while True:
    try:
        ws = websocket.create_connection("wss://irc-ws.chat.twitch.tv:443", http_proxy_host=px[0] if px[0] else None,
                                         http_proxy_port=int(px[1]) if len(px) > 1 else None, proxy_type="http", timeout=300)
        ws.send("CAP REQ :twitch.tv/tags"); ws.send("PASS SCHMOOPIIE"); ws.send(f"NICK justinfan{random.randint(10000, 99999)}")
        ws.send(f"JOIN #{ch}")
        with open(path, "a") as f:
            while True:
                for line in ws.recv().split("\r\n"):
                    if line.startswith("PING"): ws.send("PONG :tmi.twitch.tv"); continue
                    if " PRIVMSG " in line:
                        user = line.split("display-name=")[1].split(";")[0] if "display-name=" in line else "?"
                        msg = line.split(" PRIVMSG ", 1)[1].split(" :", 1)[1]
                        f.write(f"{time.time():.1f}\t{user}\t{msg}\n"); f.flush()
    except Exception as e:
        print("chat erreur", e, flush=True); time.sleep(5)
