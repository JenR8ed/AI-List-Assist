# Dev Setup — WSL Standard

This project assumes **all development and deploys happen in WSL (Ubuntu)**.  
Windows is only the host OS and UI (terminal, browser, VS Code/Cursor).

## 1. One‑time WSL install

1. Open **PowerShell as Administrator** and run:

   ```powershell
   wsl --install -d Ubuntu
   ```

2. Reboot when prompted, then launch **Ubuntu** from the Start menu.
3. In Ubuntu:

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. Confirm WSL2:

   ```powershell
   wsl -l -v
   ```

   Ubuntu should show `VERSION 2`.

---

## 2. Workspace layout (canonical paths)

All code lives under:

```text
~/workspace/jenr8ed
```

Create once:

```bash
mkdir -p ~/workspace/jenr8ed
cd ~/workspace/jenr8ed
```

Clone repos **inside WSL**:

```bash
git clone https://github.com/JenR8ed/AI-List-Assist.git
git clone https://github.com/<org>/notion-unified-webhook.git
```

Examples:

- `~/workspace/jenr8ed/AI-List-Assist`
- `~/workspace/jenr8ed/notion-unified-webhook`

> ❗ **Never use `/mnt/c/...` as the primary working directory for these repos.**  
> That path is only for quick inspection, not builds or deploys.

---

## 3. Tooling in WSL

### Node & npm (via nvm)

```bash
# Install nvm (if not already installed)
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"

# Install & use Node 20
nvm install 20
nvm alias default 20
nvm use 20
```

### Vercel CLI

```bash
npm install -g vercel
vercel login
```

### Python (if needed)

```bash
sudo apt install -y python3 python3-venv python3-pip
```

---

## 4. Project bootstrap

### AI-List-Assist

```bash
cd ~/workspace/jenr8ed/AI-List-Assist
pwd   # should end in /workspace/jenr8ed/AI-List-Assist
ls    # should show package.json, etc.
npm install
```

### Notion Unified Webhook

```bash
cd ~/workspace/jenr8ed/notion-unified-webhook
pwd   # should end in /workspace/jenr8ed/notion-unified-webhook
ls    # should show api/, package.json, vercel.json, etc.
npm install
```

> ✅ **Rule of thumb**:  
> Only run `npm install` after `pwd` and `ls` show you’re in the repo root and `package.json` is present.

---

## 5. VS Code / Cursor with WSL

### VS Code

1. Install VS Code on Windows.
2. Install the **“WSL”** extension.
3. From Ubuntu:

   ```bash
   cd ~/workspace/jenr8ed/AI-List-Assist
   code .
   ```

VS Code will open in a **Remote – WSL** session and run all tooling inside Linux.

### Cursor

1. Install Cursor on Windows.
2. Open folder via the WSL path:

   ```text
   \\wsl$\Ubuntu\home\<user>\workspace\jenr8ed\AI-List-Assist
   ```

---

## 6. Deploys (Vercel) — from WSL only

Deploy the webhook project from its WSL clone:

```bash
cd ~/workspace/jenr8ed/notion-unified-webhook
vercel deploy --prod --scope jenr8eds-projects
```

> ❗ **Never deploy from Git Bash or a Windows path.**  
> Always use WSL and a `~/workspace/...` path.

---

## 7. Secrets & env vars

- **Do not commit `.env` files.**
- Use **Doppler** or Vercel’s environment variable settings.
- In WSL, access env vars via `doppler run -- …` or `vercel env pull`, never by hardcoding keys.

Example (Doppler → Vercel):

```bash
doppler run --project ai-list-assist --config dev -- \
  sh -c 'vercel env add NOTION_TOKEN production <<< "$NOTION_TOKEN"'
```

---

## 8. “Do this, never that” summary

**Do this:**

- Use Ubuntu/WSL terminal for all dev & deploy.
- Keep repos under `~/workspace/jenr8ed`.
- Confirm `pwd` + `ls` before `npm install` or `vercel deploy`.
- Use VS Code/Cursor via WSL paths.

**Never that:**

- Don’t run `npm`, `vercel`, or `git` from Git Bash on `C:\Users\...`.
- Don’t treat `/mnt/c/...` as the main project location.
- Don’t commit secrets or `.env` into the repo.