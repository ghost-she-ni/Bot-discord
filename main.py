import argparse
import discord
from discord import Client
import json
from logger import Logger
from typing import Any
from dotenv import load_dotenv
import os
import aiohttp
import random
from blagues_api import BlaguesAPI

# Configuration du parser d'arguments
parser = argparse.ArgumentParser(description="Bot Discord")
parser.add_argument('--config', type=str, default='config.json', help='./config.json')
args = parser.parse_args()

# Chargement de la configuration depuis le fichier spécifié
with open(args.config, 'r') as config_file:
    config = json.load(config_file)

load_dotenv()


#TOKENS
token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    raise ValueError("Le token du bot Discord n'a pas été trouvé. Assurez-vous que .env contient une valeur pour DISCORD_BOT_TOKEN.")
blagues_token = os.getenv('BLAGUES_API_TOKEN')
if not blagues_token:
    raise ValueError("La clé API pour blagues-api n'a pas été trouvée. Assurez-vous d'avoir une variable d'environnement 'BLAGUES_API_TOKEN'.")
blagues = BlaguesAPI(blagues_token)
openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
if not openweather_api_key:
    raise ValueError("La clé API pour OpenWeatherMap n'a pas été trouvée. Assurez-vous d'avoir une variable d'environnement 'OPENWEATHER_API_KEY'.")
newsapi_api_key = os.getenv('NEWSAPI_API_KEY')
if not newsapi_api_key:
    raise ValueError("La clé API pour NewsAPI n'a pas été trouvée. Assurez-vous d'avoir une variable d'environnement 'NEWSAPI_API_KEY'.")


command_prefix = config['prefix']
log_config = config['log_config']

# Initialisation du logger avec la configuration chargée
logger = Logger(log_config)


class MyBot(Client):
    def __init__(self, config, prefix):
        super().__init__(intents=discord.Intents.all())
        self.logger = logger
        self.config = config
        self.prefix = prefix

    async def on_ready(self):
        self.logger.infolog(f"{self.user} has connected to Discord!")

    async def on_message(self, message):
        # Ignorer les messages envoyés par le bot lui-même
        if message.author == self.user:
            return
        
        # Commande !help
        if message.content.startswith(f'{self.prefix}help'):
            await self.handle_help(message)

        # Commande !ping
        elif message.content.startswith(f'{self.prefix}ping'):
            await self.handle_ping(message)

        # Commande !echo
        elif message.content.startswith(f'{self.prefix}echo'):
            await self.handle_echo(message, content=message.content[len(self.prefix)+5:])

        #INFORMATIONS
        # Commande !serverinfo
        elif message.content.startswith(f'{self.prefix}serverinfo'):
            await self.handle_serverinfo(message)
        # Commande !userinfo
        elif message.content.startswith(f'{self.prefix}userinfo'):
            await self.handle_userinfo(message)

        #DIVERTISSEMENT
        # Commande !meme
        elif message.content.startswith(f'{self.prefix}meme'):
            await self.handle_meme(message)
        # Commande !jokeEng
        elif message.content.startswith(f'{self.prefix}jokeEng'):
            await self.handle_jokeEng(message)
        # Commande !jokeFr
        elif message.content.startswith(f'{self.prefix}jokeFr'):
            await self.handle_jokeFr(message)

        #EXTERNES
        # Commande !weather
        elif message.content.startswith(f'{self.prefix}weather'):
            location = message.content[len(f'{self.prefix}weather '):].strip()
            if location:
                await self.handle_weather(message, location)
            else:
                await message.channel.send("Veuillez spécifier un lieu pour obtenir. Exemple: '!weather Paris'")
        elif message.content.startswith(f'{self.prefix}news'):
            await self.handle_news(message)

    async def handle_help(self, message):
        help_message = "Liste des commandes : \n"
        help_message += "!help - Affiche ce message.\n"
        help_message += "!ping - Répond 'Pong!'.\n"
        help_message += "!echo <message> - Répète le message.\n"
        help_message += "!serverinfo - Affiche des informations sur le serveur \n"
        help_message += "!userinfo [@utilisateur] - Fournit des informations sur un utilisateur \n"
        help_message += "!meme - Envoie un meme aléatoire \n"
        help_message += "!jokeEng - Partage une blague aléatoire en anglais \n"
        help_message += "!jokeFr - Partage une blague aléatoire en français \n"
        help_message += "!weather <lieu> - Affiche la météo actuelle pour une localisation donnée \n"
        help_message += "!news - Affiche les dernières nouvelles \n"

        await message.channel.send(help_message)

    async def handle_ping(self, message):
        await message.channel.send("Pong!")

    async def handle_echo(self, message, content):
        await message.channel.send(content)

    async def handle_serverinfo(self, message):
        guild = message.guild
        server_info = (
            f"Serveur : {guild.name}\n"
            f"Créé le : {guild.created_at.strftime('%d/%m/%Y')}\n"
            f"Propriétaire : {guild.owner}\n"
            f"Membres : {guild.member_count}\n"
            "Liste des membres :\n"
        )
        members = [member.name for member in guild.members]
        members_list = ", ".join(members)
        #limites de Discord : 2000 caractères max par message
        if len(server_info + members_list) > 2000:
            await message.channel.send(server_info + "La liste des membres est trop longue pour être affichée.")
        else:
            await message.channel.send(server_info + members_list)

    async def handle_userinfo(self, message):
        if message.mentions:
            user = message.mentions[0]
        else:
            await message.channel.send("Veuillez mentionner un utilisateur.")
            return
        
        user_info = (
            f"Nom d'utilisateur : {user.name}\n"
            f"Discriminateur : {user.discriminator}\n"
            f"ID : {user.id}\n"
            f"Créé le : {user.created_at.strftime('%d/%m/%Y à %H:%M:%S')}\n"
        )

        roles = [role.name for role in user.roles[1:]] #Pour exclure @everyone
        roles_list = ", ".join(roles) if roles else "Aucun rôle"

        user_info += f"Rôles : {roles_list}"

        await message.channel.send(user_info)

    async def handle_meme(self, message):
        api_url = "https://api.imgflip.com/get_memes"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data["success"]:
                        memes = data['data']['memes']
                        meme = random.choice(memes)
                        await message.channel.send(meme['url'])
                    else:
                        await message.channel.send("Impossible de charger un meme. Essayez à nouveau plus tard.")
                else:
                    await message.channel.send("Erreur de service de memes. Statut : {resp.status}")

    async def handle_jokeEng(self, message):
        joke_url = "https://v2.jokeapi.dev/joke/Any"
        async with aiohttp.ClientSession() as session:
            async with session.get(joke_url) as resp:
                if resp.status == 200:
                    joke_data = await resp.json()
                    if joke_data["type"] == "single":
                        await message.channel.send(joke_data["joke"])
                    elif joke_data["type"] == "twopart":
                        await message.channel.send(f"{joke_data['setup']}\n{joke_data['delivery']}")

                else:
                    await message.channel.send("Je n'ai pas pu trouver de blague pour le moment. 😞")
                    print(f"Erreur lors de l'accès de JokeAPI: {resp.status}")

    async def handle_jokeFr(self, message):
        try:
            blague = await blagues.random()
            if hasattr(blague, 'answer') and blague.answer:
                await message.channel.send(f"{blague.joke}\n{blague.answer}")
            else: 
                await message.channel.send(blague.joke)
        except Exception as e:
            await message.channel.send("Je n'ai pas réussi à trouver une blague pour le moment. 😞")
            print(f"Une erreur est survenue lors de la récupération de la blague : {e}")
            self.logger.errorlog(f"Erreur dans handle_jokeFr: {e}")

    async def handle_weather(self, message, location):
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': openweather_api_key,
            'units': 'metric',
            'lang': 'fr'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as resp:
                if resp.status == 200:
                    weather_data = await resp.json()
                    description = weather_data['weather'][0]['description']
                    temperature = weather_data['main']['temp']
                    await message.channel.send(f"Météo à {location} : {description}, Température : {temperature}°C")
                else:
                    await message.channel.send("Impossible d'obtenir les informations météorologiques. 😞")

    async def handle_news(self, message):
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            'country': 'fr',
            'apikey': newsapi_api_key,
            'pageSize': 5,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as resp:
                if resp.status == 200:
                    news_data = await resp.json()
                    articles = news_data['articles']
                    news_messages = "Voici les dernières nouvelles : \n"
                    for article in articles:
                        news_piece = f"**{article['title']}**\n{article['description']}\nLire plus: {article['url']}\n\n"
                        if len(news_piece) + len(news_messages) <= 2000:
                            news_messages += news_piece
                        else:
                            await message.channel.send(news_messages)
                            news_messages = news_piece  
                    if news_messages:
                        await message.channel.send(news_messages)
                else:
                    await message.channel.send("Je ne peux pas récupérer les nouvelles en ce moment.")



    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        return await super().on_error(event_method, *args, **kwargs)

if __name__ == "__main__":
    bot = MyBot(config=config, prefix=command_prefix) 
    bot.run(token)


