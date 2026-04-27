# Kiro Honcho

[中文](./README.md) | [English](./README.en.md) | [Deutsch](./README.de.md)

**Multi-AWS-Konto Kiro/Q Developer Abonnementverwaltungsplattform**

Eine einheitliche Plattform zur Verwaltung von Identity Center-Benutzern und Kiro-Abonnements über mehrere AWS-Konten hinweg — vereinfacht Benutzererstellung, Abonnementzuweisung und Planwechsel.

---

## Warum dieses Projekt?

Wenn Sie AWS Identity Center zur Benutzerverwaltung nutzen und Ihrem Team Kiro (Amazon Q Developer)-Abonnements zuweisen, kennen Sie sicher diese Probleme:

**Manuelle, repetitive Arbeit**
- Ein neues Mitglied hinzufügen erfordert: Benutzer in Identity Center erstellen → auf E-Mail-Aktivierung warten → Kiro-Konsole öffnen → Abonnement zuweisen. Drei Schritte, drei verschiedene Oberflächen.
- 10 Benutzer hinzufügen? 10-mal wiederholen.

**Keine einheitliche Übersicht**
- Identity Center verwaltet nur Benutzer. Die Kiro-Konsole verwaltet nur Abonnements. Die Daten sind getrennt.
- Um herauszufinden, welche Benutzer ihre E-Mail noch nicht bestätigt haben oder welche Abonnements noch „Pending" sind, muss man zwischen Konsolen wechseln und manuell vergleichen.

**Chaos bei mehreren Konten**
- Unternehmen haben oft mehrere AWS-Konten (Produktion, Staging, Partner). Jedes hat sein eigenes Identity Center und Kiro-Abonnements.
- AWS bietet keine kontoübergreifende einheitliche Ansicht.

**Undurchsichtige interne APIs**
- Die Kiro-Abonnementverwaltung verwendet undokumentierte interne APIs (SigV4-signiert). Kein offizieller SDK-Support.
- Die Berechtigungskonfiguration ist komplex — `AmazonQFullAccess` enthält nicht alle erforderlichen Berechtigungen.

**Kiro Honcho löst all das:**
- Eine Oberfläche: Benutzer erstellen → Aktivierungs-E-Mail senden → Abonnement zuweisen, vollständig automatisiert
- Einheitliche Abonnement-Lebenszyklusansicht (E-Mail nicht verifiziert / Ausstehend / Aktiv)
- Multi-AWS-Konto-Unterstützung mit einem Klick zum Wechseln
- CSV-Massenimport mit Echtzeit-Fortschrittsanzeige
- Alle internen API-Aufrufe gekapselt, sofort einsatzbereit

---

## Funktionen

### 🏢 Multi-AWS-Kontoverwaltung
- Mehrere AWS-Konten hinzufügen und zentral verwalten
- Verschlüsselte Anmeldedatenspeicherung (AES-256-GCM)
- Automatische Berechtigungsverifizierung und Identity Center-Verbindungsprüfung
- Automatisch generierte Kiro-Anmelde-URL mit Ein-Klick-Kopieren

### 👥 Vollständiges Benutzer-Lebenszyklusmanagement
- **Benutzer erstellen** → automatisch zu Identity Center hinzufügen → Einladungs-E-Mail senden → sofort Kiro-Abonnement zuweisen
- **CSV-Massenimport** — nur E-Mail erforderlich, Echtzeit-Fortschrittsanzeige
- **Statusverfolgung** — E-Mail nicht verifiziert / Ausstehend / Aktiv (drei Zustände)
- **Benutzer löschen** — Abonnement automatisch kündigen → IC-Benutzer entfernen (keine Auswirkung auf andere Cloud-Ressourcen)

### 📋 Abonnementverwaltung
- Alle aktiven Abonnements anzeigen (nach Konto filterbar)
- Plan wechseln (Pro / Pro+ / Power)
- Abonnement kündigen
- Verlauf gekündigter Abonnements anzeigen (kontoübergreifend)

### 🔄 Automatische Synchronisierung
- Geplante Synchronisierung von AWS (konfigurierbares Intervall)
- Automatische Erkennung des E-Mail-Verifizierungsstatus
- Automatische Bereinigung gelöschter Benutzer und gekündigter Abonnements

### 🔐 Sicherheit
- JWT-Authentifizierung + TOTP MFA (Google Authenticator)
- MFA-Pflicht — muss bei der ersten Anmeldung eingerichtet werden
- Systembenutzer-Verwaltung (nur Administratoren)

### 📱 Responsives Design
- Desktop: Tabellenansicht
- Mobil: Kartenbasiertes vertikales Layout

---

## Schnellstart

> 3 Schritte, 30 Sekunden zum Starten. Verwendet standardmäßig SQLite — keine externe Datenbank erforderlich.

```bash
mkdir kiro-honcho && cd kiro-honcho

# Deployment-Dateien herunterladen
curl -O https://raw.githubusercontent.com/barryxu119/kiro-honcho/dev/docker-compose.deploy.yml
curl -O https://raw.githubusercontent.com/barryxu119/kiro-honcho/dev/.env.example
cp .env.example .env

# Starten
sudo docker compose -f docker-compose.deploy.yml pull
sudo docker compose -f docker-compose.deploy.yml up -d
```

Zugriff unter `http://ihr-server:5025`, Standardzugangsdaten `admin` / `admin123` (MFA-Einrichtung beim ersten Login erforderlich).

Docker-Images:
- `barryxu119/kiro-honcho-backend:latest`
- `barryxu119/kiro-honcho-frontend:latest`

---

## Detaillierte Deployment-Anleitung

### 1. Voraussetzungen

| Element | Anforderung |
|---------|-------------|
| Docker | 24+ |
| Docker Compose | v2+ |
| Datenbank | SQLite (Standard, keine Einrichtung nötig) oder MySQL 8.x |
| AWS-Konto | IAM Identity Center aktiviert, Kiro/Q Developer-Abonnement aktiv, Berechtigungen wie unten konfiguriert |

### 2. AWS IAM-Berechtigungskonfiguration

⚠️ **Wichtig**: Der IAM-Benutzer für jedes AWS-Konto benötigt folgende Berechtigungen:

**Verwaltete Richtlinie:**
- `AWSSSOMasterAccountAdministrator`

**Benutzerdefinierte Inline-Richtlinie (erforderlich):**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "user-subscriptions:*",
                "q:*"
            ],
            "Resource": "*"
        }
    ]
}
```

> `AmazonQFullAccess` enthält NICHT die internen API-Berechtigungen (`q:CreateAssignment`, `q:DeleteAssignment`, `q:UpdateAssignment`, `user-subscriptions:ListUserSubscriptions`). Diese müssen über eine Inline-Richtlinie gewährt werden.

### 3. Deployment-Optionen

#### Option 1: Docker Hub Images (Empfohlen)

Dies ist die Schnellstart-Methode oben. Zum Anpassen `.env` bearbeiten und neu starten:

```bash
vi .env
sudo docker compose -f docker-compose.deploy.yml up -d
```

#### Option 2: Aus Quellcode bauen

```bash
git clone <repo-url>
cd kiro-honcho
cp .env.example .env
# .env bearbeiten

sudo docker compose up -d --build
```

### 4. Verwendungsablauf

1. **AWS-Konto hinzufügen** — AK/SK, SSO-Region, Kiro-Region eingeben
2. **Konto verifizieren** — Verify klicken, um Berechtigungen und Identity Center-Verbindung zu prüfen
3. **Daten synchronisieren** — Sync klicken, um vorhandene Benutzer und Abonnements abzurufen
4. **Benutzer verwalten** — Erstellen / Löschen / Massenimport
5. **Abonnements verwalten** — Plan wechseln / Abonnement kündigen

---

## Umgebungsvariablen

Alle Konfiguration wird über eine einzige `.env`-Datei im Stammverzeichnis verwaltet:

```env
# ===== Datenbank =====
# DB_TYPE: sqlite oder mysql
DB_TYPE=sqlite

# SQLite (Standard, Daten in ./data, automatisch von Docker gemountet)
# SQLITE_PATH=/app/data/kiro_honcho.db

# MySQL (auskommentieren und ausfüllen)
# MYSQL_HOST=ihr-mysql-host
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=ihr-passwort
# MYSQL_DATABASE=kiro_honcho
# DB_SSL_CA=global-bundle.pem

# ===== JWT-Authentifizierung =====
JWT_SECRET_KEY=ihr-geheimer-schluessel-min-32-zeichen
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== Verschlüsselungsschlüssel für AWS-Anmeldedaten =====
# Generieren: python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
APP_ENCRYPTION_KEY=ihr-base64-kodierter-32-byte-schluessel

# ===== Standard-Administrator =====
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123

# ===== Sonstiges =====
CORS_ORIGINS=http://ihre-domain.com
AUTO_SUBSCRIBE_CHECK_INTERVAL=5
DEFAULT_SSO_REGION=us-east-2
DEFAULT_KIRO_REGION=us-east-1
```

---

## Deployment aktualisieren

```bash
# Docker Hub Image-Methode
sudo docker compose -f docker-compose.deploy.yml pull
sudo docker compose -f docker-compose.deploy.yml up -d

# Quellcode-Build-Methode
git pull
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

## Entwicklungsmodus

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend
cd frontend
npm install
npm run dev  # http://localhost:5020
```

---

## Technische Dokumentation

Detaillierte Architektur, API-Design und Datenmodelle finden Sie in [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Lizenz

MIT-Lizenz
