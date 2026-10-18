"""
Run locally (for example in Termux) to create a Pyrogram session string.
Do not share the resulting string: it grants access to your Telegram account.
"""
import asyncio
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

async def main():
    api_id = int(input("API_ID: ").strip())
    api_hash = input("API_HASH: ").strip()
    async with Client("session_generator", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
        print("\nSESSION_STRING:\n")
        print(await app.export_session_string())
        print("\nKeep this secret. Never paste it into a public GitHub repository.")

if __name__ == "__main__":
    asyncio.run(main())
