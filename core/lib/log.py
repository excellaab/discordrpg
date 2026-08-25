import logging
import discord

discord.utils.setup_logging(level=logging.INFO, root=True)

class NoTracebackFilter(logging.Filter):
    def filter(self, record):
        if "Attempting a reconnect" in record.getMessage():
            record.exc_info = None 
            record.exc_text = None
        return True
    
botlogger = logging.getLogger("discordrpg")
botlogger.addFilter(NoTracebackFilter())

dblogger = logging.getLogger("database")
dblogger.setLevel(logging.INFO)
