# University Discord Bot

A Discord bot designed for university Discord servers, featuring reminder creation and email verification using OTP. The bot enhances student engagement and streamlines verification processes.

## Features
- Create reminders for events and deadlines.
- Verify students via email with an OTP code.
- Role assignment upon successful verification.

## Table of Contents
- [Getting Started](#getting-started)
- [Creating a Discord Bot Application](#creating-a-discord-bot-application)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Hosting](#hosting)
- [License](#license)
- [Credits](#credits)

## Getting Started

Follow these steps to set up the bot locally.

### Creating a Discord Bot Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click on the **New Application** button.
3. Name your application and click **Create**.
4. Navigate to the **Bot** tab and click **Add Bot**.
5. Under the **Token** section, click **Copy** to save your bot's token.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/university-discord-bot.git
   cd university-discord-bot
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Copy the `.env.example` file to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your Discord bot token, MongoDB connection string, email credentials, and other configurations as needed.

### Usage

To run the bot, use the following command:

```bash
python launcher.py
```

Make sure your bot is invited to your Discord server with the correct permissions.

## Hosting

You can host the bot on your own server using PM2. Follow these steps to set it up:

### Steps to Host with PM2

1. **Install PM2** globally if you haven't already:

   ```bash
   npm install -g pm2
   ```

2. **Start the bot** with PM2:

   ```bash
   pm2 start launcher.py --interpreter=python3 --name "university-discord-bot"
   ```

3. **Save the PM2 process list** to start on boot:

   ```bash
   pm2 save
   pm2 startup
   ```

4. **Check PM2 status**:

   ```bash
   pm2 status
   ```

## License

This project is licensed under the [Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/).

## Credits

This bot is inspired by [RoboDanny](https://github.com/Rapptz/RoboDanny), a well-known Discord bot. Thanks to the original authors for their contributions!

