# 📰 News Tracker

A simple program for saving the news articles you read (Financial Times, Bloomberg, Reuters, and others), sorting them into sections, and writing down what each one could mean for markets.

## ▶ How to start

| Computer | What to do |
|---|---|
| **Windows** | Double-click **`Start.bat`** |
| **Mac** | Double-click **`Start.command`**. The first time, right-click it and choose **Open**. |
| **Linux** | Run `./start.sh` |

The app opens in your web browser. **Keep the small black window open** while you use it, and close it when you're finished.

> You need Python 3 installed (it's free). You can get it from https://www.python.org/downloads/. On Windows, tick **"Add Python to PATH"** during the install.

## How to use it

1. **Sections** are on the left. Click **+ New section** to add one, for example "China & Asia". To rename, recolour or delete a section, select it and click **✏️ Edit section**.
2. Click **+ Add article** and fill in:
   - Headline, source, link and date
   - **Key points**, one per line (each line becomes a bullet point)
   - **What this could mean for the market**
   - **What this could mean for the global market**
   - **Overall outlook**: Positive, Negative, Neutral or Uncertain
   - Your own notes
3. Click an article to open it and see its full breakdown. Use the search box and filters to find things quickly.

## 💾 Where your information is saved

Every change is saved to your computer straight away. The top bar shows **"All changes saved ✓"**.

- `data/news.json` holds all of your data. The app also keeps a backup copy for each day in `data/backups/` (the last 30 days).
- `My News Files/` has **one readable file per section**, and each file lists that section's articles as bullet points. Click **📁 Open my files** in the app to open this folder.
- **⬇ Backup** downloads a full copy of everything.

Your saved articles are private to your computer and are not uploaded to GitHub (`data/` and `My News Files/` are in `.gitignore`).
