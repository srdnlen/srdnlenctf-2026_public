# MSN Chat - React Frontend

Reimplementazione del frontend MSN Chat usando React e Vite.

## 🚀 Caratteristiche

- ✅ Interfaccia utente MSN Messenger classica
- ✅ Login con selezione profilo
- ✅ Lista contatti
- ✅ Finestra chat con messaggistica
- ✅ Dati completamente mockati (nessuna chiamata API)
- ✅ Design retrò fedele all'originale

## 📦 Installazione

```bash
npm install
```

## 🏃‍♂️ Avvio

```bash
npm run dev
```

L'applicazione sarà disponibile su `http://localhost:5173`

## 🏗️ Build

```bash
npm run build
```

## 📁 Struttura del Progetto

```
msn-chat-react/
├── public/
│   └── assets/          # Immagini, icone e altri assets statici
├── src/
│   ├── components/      # Componenti React
│   │   ├── Login.jsx    # Componente login
│   │   ├── Contacts.jsx # Lista contatti
│   │   └── Chat.jsx     # Finestra chat
│   ├── data/
│   │   └── mockData.js  # Dati mockati (contatti, messaggi)
│   ├── styles/          # File CSS
│   ├── App.jsx          # Componente principale
│   ├── main.jsx         # Entry point
│   └── index.css        # Stili globali
├── index.html
├── package.json
└── vite.config.js
```

## 🎨 Funzionalità Implementate

### Login
- Form di login con username e password
- Selezione immagine profilo
- Toggle tra Sign in e Sign up
- Animazione di caricamento

### Contacts
- Lista contatti online
- Ricerca contatti
- Visualizzazione stato e messaggio personalizzato
- Design fedele a MSN Messenger

### Chat
- Invio e ricezione messaggi (simulati)
- Indicatore "sta scrivendo"
- Funzione Nudge
- Visualizzazione avatar
- Scroll automatico ai nuovi messaggi

## 📝 Note

- Tutti i dati sono mockati e memorizzati in `src/data/mockData.js`
- Non ci sono chiamate API reali
- Il design è basato sul progetto originale msn-chat
- Gli assets sono stati copiati dal progetto originale

## 🛠️ Tecnologie Utilizzate

- React 18
- Vite
- CSS modules (stili originali MSN)

## 📸 Screenshot

L'applicazione riproduce fedelmente l'aspetto di Windows Live Messenger con:
- Sfondo Vista gradient
- Finestre "Aero Glass" style
- Icone e sprite originali
- Font Tahoma/Segoe UI

## 🔮 Sviluppi Futuri

Per collegare l'applicazione al backend:
1. Sostituire i dati in `mockData.js` con chiamate API
2. Implementare WebSocket per la messaggistica real-time
3. Aggiungere autenticazione JWT
4. Gestire lo stato globale con Context API o Redux
