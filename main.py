import asyncio
import json
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from datetime import datetime

# Configuration file name
CONFIG_FILE = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"accounts": []}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

async def setup_client(account):
    client = TelegramClient(f"session_{account['phone']}", account['api_id'], account['api_hash'])
    await client.start()
    
    if not await client.is_user_authorized():
        print(f"Authorizing {account['phone']}...")
        await client.send_code_request(account['phone'])
        code = input(f"Enter the code received on {account['phone']}: ")
        try:
            await client.sign_in(account['phone'], code)
        except SessionPasswordNeededError:
            password = input("Two-step verification is enabled. Please enter your password: ")
            await client.sign_in(password=password)
    
    return client

async def monitor_channel(client, channel, comment):
    @client.on(events.NewMessage(chats=channel))
    async def auto_comment(event):
        try:
            await asyncio.sleep(2)
            message = event.message
            await client.send_message(
                entity=channel,
                message=comment,
                comment_to=message
            )
            print(f"[{datetime.now()}] Commented on post in {channel}")
        except Exception as e:
            print(f"[{datetime.now()}] Error commenting in {channel}: {str(e)}")

async def main():
    config = load_config()
    
    while True:
        print("\n1. Add new account")
        print("2. Add channel to existing account")
        print("3. Start monitoring")
        print("4. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            account = {
                'phone': input("Enter phone number: "),
                'api_id': int(input("Enter API ID: ")),
                'api_hash': input("Enter API Hash: "),
                'channels': []
            }
            config['accounts'].append(account)
            save_config(config)
            print("Account added successfully!")
        
        elif choice == '2':
            if not config['accounts']:
                print("No accounts found. Please add an account first.")
                continue
            
            for i, account in enumerate(config['accounts']):
                print(f"{i+1}. {account['phone']}")
            
            acc_choice = int(input("Choose account number: ")) - 1
            channel = input("Enter channel username (without @): ")
            comment = input("Enter comment for this channel: ")
            
            config['accounts'][acc_choice]['channels'].append({
                'username': channel,
                'comment': comment
            })
            save_config(config)
            print("Channel added successfully!")
        
        elif choice == '3':
            clients = []
            for account in config['accounts']:
                client = await setup_client(account)
                clients.append(client)
                for channel in account['channels']:
                    await monitor_channel(client, channel['username'], channel['comment'])
            
            print("Monitoring started. Press Ctrl+C to stop.")
            try:
                await asyncio.gather(*(client.run_until_disconnected() for client in clients))
            except KeyboardInterrupt:
                for client in clients:
                    await client.disconnect()
                print("Monitoring stopped.")
        
        elif choice == '4':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main()) "
