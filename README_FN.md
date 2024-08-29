Explanation

1. Data Structure:

- user_fortnite_data: Stores Fortnite usernames and their stats, organized by time periods.
- leaderboard_channels: Maps leaderboard periods to specific channel IDs for updates.

2. Commands:

- !setfortnite: Sets the Fortnite username for the user. Can be set for a server member using @ or left empty to be set for the poster.
- !setleaderboardchannel: Sets the channel for each leaderboard type (daily, weekly, season, lifetime). Format: !setleaderboardchannel daily 1119424152370159688
- !removefortnite @user : will remove a user from the daily, weekly, season and lifetime leaderboards.
- !rank_br / !rank_zb @user displays season rank info for the specific user.

3. Tasks:

- update_leaderboards: Runs daily to update all leaderboards. It checks if it’s midnight and posts the leaderboard for each period to its respective channel.
- post_leaderboard: Sends the leaderboard for a specific period to the specified channel.
- generate_leaderboard: Creates an embed for the leaderboard of a specific period.


Replace "YOUR_FORTNITE_API_KEY" and "YOUR_DISCORD_BOT_TOKEN" with your actual Fortnite Tracker API key and Discord bot token.

This code allows you to set different channels for each type of leaderboard and ensures that all leaderboards are updated daily at midnight Danish time if there are any changes.