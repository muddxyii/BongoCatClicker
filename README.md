# Bongo Cat Manager

> **Fork notice:** This project is a fork of the original [BongoCatClicker](https://github.com/Chiqui89/BongoCatClicker). Big thanks to the original author for the foundation! This fork expands in a different direction with broader automation and management features.

A tool that automatically manages Bongo Cat, including auto-pressing keys and auto-redeeming emojis and accessories.

## Requirements

- Python 3.x
- Bongo Cat (Steam)

## Installation

1. Clone the repo:
   ```
   git clone https://github.com/muddxyii/BongoCatManager.git
   ```
2. Run `RUN.bat` and it will install dependencies and launch the app automatically.

## Features

- **Auto Press** - continuously presses random keys while Bongo Cat is open
- **Auto Redeem** - uses image recognition to find and click the emoji and accessory redeem buttons every 30 minutes. Searches every 5 seconds until both are found, then starts the timer
- **Settings persistence** - toggle states are saved and restored between sessions
- Catppuccin Macchiato theme

## Notes

- Bongo Cat must be open and detected before you can press Start
- Press F8 or click Start to toggle the bot
- Auto Redeem pauses the auto presser briefly while clicking redeem buttons
- Make sure the `icons/` folder is present next to the script
