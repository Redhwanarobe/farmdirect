# FarmDirect – Team Setup Guide (Windows)

Every team member must follow these steps, so that all three of us work with **the same tools and the same versions**.
Do the steps in order. It takes about 30 minutes.

---

## 1. Versions We Use

| Tool | Version | Notes |
|---|---|---|
| Windows | 10 or 11, 64-bit | |
| **Python** | **3.13.17** | Any 3.13.x is fine. Do **not** use 3.14 or 3.15 for this project. |
| pip | comes with Python | Installed automatically with Python |
| **Git** | 2.56 (any recent version) | |
| **VS Code** | latest | |
| Django, Ruff, pdoc | fixed in `requirements.txt` | Installed later **inside the project**, not now |

### VS Code extensions

| Extension | Publisher | Why |
|---|---|---|
| **Python** | Microsoft (blue tick) | Run and debug Python. Also installs Pylance and Python Debugger. |
| **Ruff** | Astral | Checks our coding standard (Report Section 5) |
| **SonarQube for IDE** | SonarSource | Code review tool (Report Section 9) |
| **Django** (optional) | Baptiste Darthenay | Colours Django HTML templates |

Many extensions have similar names. **Always check the publisher.**

---

## 2. Install Python 3.13

1. Open **https://www.python.org/downloads/windows/**
2. Find **"Python 3.13.17"** (do not use the yellow "Python install manager" button and do not use 3.15).
3. Under it, click **"Download Windows installer (64-bit)"**.
4. Open the downloaded file `python-3.13.17-amd64.exe`.
5. On the first screen, **tick both boxes at the bottom**:
   - ☑ Use admin privileges when installing py.exe
   - ☑ **Add python.exe to PATH**  ← most important
6. Click **Install Now**. If Windows asks "Allow changes?", click **Yes**.
7. At the end, click **"Disable path length limit"** if it is shown, then **Close**.

---

## 3. Install Git

1. Open **https://git-scm.com** and click **Download for Windows**.
2. Run the installer and keep clicking **Next** (the default options are fine).
3. Optional: on the "Choosing the default editor" screen, select **"Use Visual Studio Code as Git's default editor"**.

---

## 4. Install VS Code

1. Open **https://code.visualstudio.com** and click **Download for Windows**.
2. On the "Select Additional Tasks" screen, **tick all boxes**, especially:
   - ☑ Add "Open with Code" action
   - ☑ **Add to PATH**
3. Finish the installation.

### Install the extensions

1. Open VS Code and press **Ctrl+Shift+X**.
2. Search for each name in the table in section 1 and click **Install** on the one with the **correct publisher**.
3. Check the **Installed** list at the top of the Extensions panel.

---

## 5. Tell Git Who You Are (once only)

Open **cmd** and run, using **your own name** and **the email of your GitHub account**:

```
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Use the same email as your GitHub account, so that your commits are linked to your profile.
Our report (Section 10 and Section 12) uses these commits to show who did what.

---

## 6. Check Everything Works

Close any open cmd window, open a **new** one, and run:

```
python --version
pip --version
git --version
code --version
```

You should see something like:

```
Python 3.13.17
pip 26.x.x from ...\Python313\... (python 3.13)
git version 2.56.0.windows.2
1.xx.x   (VS Code version)
```

Take a screenshot and post it in our **Discord** setup channel.

---

## 7. Join the GitHub Repository

1. Open the invitation email from GitHub (or the notifications bell on github.com).
2. Click **Accept invitation** for the **farmdirect** repository.

The steps for downloading the project and installing Django will be added here after the project is created.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` says **"not found"** or opens the **Microsoft Store** | Run the Python installer again and tick **"Add python.exe to PATH"**. If it still opens the Store: Windows **Settings → Apps → Advanced app settings → App execution aliases**, and turn **off** `python.exe` and `python3.exe`. Then open a new cmd. |
| `python --version` shows **3.9 or older** | Install Python 3.13.17 as in section 2. |
| `code` is **not recognised** | Reinstall VS Code with **"Add to PATH"** ticked, then open a new cmd. |
| `unknown option` error from Git | Check the spelling: it is `git --version` (two dashes, no extra words). |
| VS Code shows **"Restricted Mode"** | Normal for new folders. When you open our project folder, click **Trust**. |
