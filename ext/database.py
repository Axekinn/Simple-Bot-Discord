import asyncio
import logging
import discord
from datetime import datetime
from discord.ext import commands
from pymongo import DESCENDING, MongoClient
from PIL import Image
import os

from config.secrets import MONGO_URI
from ext.audit_log import recursive_object_to_dict

logger = logging.getLogger(name='WGEDLA')

if MONGO_URI:
    log_database = MongoClient(MONGO_URI).get_database()
else:
    log_database = None

async def database_insert_message(message: discord.Message):
    if log_database is None:
        logger.error("Database connection is not established.")
        return

    if message.attachments:
        attachment = message.attachments[0]
        attachment0data = attachment.url + "//FILENAME//" + attachment.filename
        asyncio.create_task(attachmentCacher(attachment, message.id, attachment.filename))
    else:
        attachment0data = ""

    guild_id_str = str(message.guild.id)
    channel_id_str = str(message.channel.id)
    
    # Debugging: Print the state of log_database and guild_id_str only if log_database is not None
    print(f"guild_id_str: {guild_id_str}")
    
    if guild_id_str not in log_database:
        # Handle missing entry
        print(f"Guild ID {guild_id_str} not found in log_database.")
        return
    
    if channel_id_str not in log_database[guild_id_str]:
        # Handle missing entry
        print(f"Channel ID {channel_id_str} not found in log_database[{guild_id_str}].")
        return
    
    doc = {
        'author': str(message.author),
        'author_id': str(message.author.id),
        'created_at': message.created_at,
        'content': message.content,
        'edited_at': message.edited_at,
        'deleted': False,
        'attachment0': str(attachment0data),
    }

    result = log_database[guild_id_str][channel_id_str].insert_one(doc)
    if result.inserted_id is not None and result.acknowledged is True:
        logger.debug(msg=f'Database record insert SUCCESS! Location: {message.guild.id}/{message.channel.id}/{message.id}')
    else:
        logger.critical(msg=f'Database record insert failed! Incident Location: {message.guild.id}/{message.channel.id}/{message.id}')

async def attachmentCacher(attachment: discord.Attachment, message_id: int, filename: str):
    os.makedirs('./AttachmentCache', exist_ok=True)
    
    if attachment.size > 25000000:
        logger.warning(msg=f'Attachment download dropped! Limit Exceeded. ' + f'Filename: {message_id}.{attachment.filename} ' + f'Size: {int(attachment.size / 1048576)}MB ' + f'Type: {attachment.content_type}')
        return
    
    cacheName = str(f'./AttachmentCache/{message_id}.{filename}')
    await attachment.save(fp=cacheName, use_cached=False)
    
    logger.debug(msg=f'Attachment Downloaded! ' + f'Filename: {cacheName} ' + f'Size: {round(float(attachment.size / 1048576), 2)}MB ' + f'Type: {attachment.content_type}')
    if 'image' in attachment.content_type:
        image = Image.open(cacheName)
        image.save(cacheName, optimize=True, quality=10)

def database_insert_audit_log_entry(entry: discord.AuditLogEntry):
    if log_database is None:
        logger.error("Database connection is not established.")
        return

    guild_id_str = str(entry.guild.id)
    
    # Debugging: Print the state of log_database and guild_id_str only if log_database is not None
    print(f"guild_id_str: {guild_id_str}")
    
    if guild_id_str not in log_database:
        print(f"Guild ID {guild_id_str} not found in log_database.")
        return
    
    result = log_database[guild_id_str].audit_log.insert_one(recursive_object_to_dict(entry))
    return result

def database_delete_message(message: discord.Message or classmethod):
    if log_database is None:
        logger.error("Database connection is not established.")
        return

    guild_id_str = str(message.guild.id)
    channel_id_str = str(message.channel.id)

    if guild_id_str not in log_database:
        logger.error(f"Guild ID {guild_id_str} not found in log_database.")
        return

    if channel_id_str not in log_database[guild_id_str]:
        logger.error(f"Channel ID {channel_id_str} not found in log_database[{guild_id_str}].")
        return

    result = log_database[guild_id_str][channel_id_str].update_many({'message_id': str(message.id)}, {'$set': {'deleted': True}})
    if result is None:
        logger.critical(msg=f'Delete database record update failed! Fetched record empty. Incident Location: {message.guild.id}/{message.channel.id}/{message.id}')


    guild_id_str = str(guild_id)
    channel_id_str = str(channel_id)

    if guild_id_str not in log_database:
        logger.error(f"Guild ID {guild_id_str} not found in log_database.")
        return None

    if channel_id_str not in log_database[guild_id_str]:
        logger.error(f"Channel ID {channel_id_str} not found in log_database[{guild_id_str}].")
        return None

    message_doc = log_database[guild_id_str][channel_id_str].find_one({'message_id': str(message_id)}, sort=[('edited_at', DESCENDING)])
    if message_doc is None:
        logger.warning(msg=f'No message found in database for {guild_id}/{channel_id}/{message_id}')
        return None
    return message_doc
