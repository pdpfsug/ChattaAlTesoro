# Chatta Al Tesoro

Bot Telegram per realizzare una caccia al tesoro.

## Quick start

- Installare il pacchetto `zbar`
- Installare i requisiti python con `pip install -r requirements.txt`
- Copiare `settings_dist.py` in `settings.py`
- Creare il database per la caccia al tesoro con `python init_db.py`
- Inserire il proprio token in `TOKEN_GAME` e `TOKEN_ADMIN`
- Eseguire `python chatta_al_tesoro_adminbot.py` e configurare la caccia al tesoro
- Eseguire `python chatta_al_tesoro_bot.py` e giocare

TODO: Dovremmo scrivere un README fatto meglio... 

TITOLO DEL PROGETTO: Il titolo del nostro progetto sarà "L'evoluzione dei chat bot".

DESCRIZIONE DEL PROGETTO: Per definizione i Chat bot, chatbot o chatterbot, sono software progettati per simulare conversazioni con gli esseri umani. Alcuni utilizzano sofisticati sistemi di elaborazione del linguaggio naturale per generare risposte in modo autonomo, ma molti si limitano a eseguire la scansione delle parole chiave nel messaggio di input e tentare di fornire una risposta adeguata scegliendola tra quelle che “conoscono”. Proprio per questo uso discorsivo dei chat bot abbiamo deciso di creare, tramite domande appropriate, una sorta di caccia al tesoro, incentrata sulla risoluzione degli indovinelli previsti dal percorso e sulla eventuale vittoria del gioco.
Per questo progetto abbiamo utilizzato due bot: un Parole chiave: intelligenza artificiale, sperimentazione, etica.

bot amministratore e un bot giocatore.

Il bot amministratore chiederà all'utente l'indovinello da porre al bot giocatore, e come risposta il bot invierà un QR Code; successivamente chiederà la locazione del prossimo indovinello e l'utente risponderà con il luogo prestabilito. Dopo aver impostato tre quesiti il gioco terminerà.

// Le domande da porre saranno molteplici, infatti prevedono indovinelli a risposta aperta ma anche quesiti a risposta multipla che varieranno dalle due alle quattro opzioni di scelta.

// Le domande verranno poste in maniera sequenziale

Il bot giocatore invia il QR Code all’amministratore di gioco per ricevere la domanda da risolvere, se la risposta è sbagliata il giocatore non può proseguire con il percorso ed è costretto a ripetere la domanda dopo un tempo prestabilito(nel nostro caso sarà di 60 secondi).

// Per migliorare l’applicazione, dopo una risposta corretta, il bot amministratore manderà un messaggio di riuscita che varierà per tutte le risposte. La stessa cosa accadrà nel caso di una risposta errata però il messaggio ricevuto sarà negativo.
