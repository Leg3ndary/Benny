from __future__ import print_function

import json
import googleapiclient.discovery
from httplib2 import Http
from oauth2client import client
from oauth2client import file
from oauth2client import tools
from discord.ext import commands, tasks
import discord
import datetime
import re


def convert(thing):
    """Convert list to a dict [item1, item2, item3, item4] = {item1: item2, item3: item4}"""
    it = iter(thing)
    res_dct = dict(zip(it, it))
    return res_dct


class AnnouncementsDoc:
    """Class for accessing info about the announcements doc"""
    def __init__(self):
        """Initiates with all the info that we need"""
        self.SCOPES = "https://www.googleapis.com/auth/documents.readonly"
        self.DISCOVERY_DOC = "https://docs.googleapis.com/$discovery/rest?version=v1"
        self.DOCUMENT_ID = "1AsAPy6pVsB63S1u2B2PcdgI95FQEWufX-v0_hajAPzs"

    async def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth 2.0 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        store = file.Storage('school/APHS/token.json')
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets('school/APHS/credentials.json', self.SCOPES)
            credentials = tools.run_flow(flow, store)
        return credentials


    async def read_paragraph_element(self, element):
        """Returns the text in the given ParagraphElement.

        Args:
            element: a ParagraphElement from a Google Doc.
        """
        text_run = element.get("textRun")
        
        if not text_run:
            return ""
        return text_run.get("content")


    async def read_strucutural_elements(self, elements):
        """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
        """
        text = ""
        for value in elements:
            if "paragraph" in value:
                elements = value.get("paragraph").get("elements")
                for elem in elements:
                    text += await self.read_paragraph_element(elem)
            elif "table" in value:
                # The text in table cells are in nested Structural Elements and tables may be
                # nested.
                table = value.get("table")
                for row in table.get("tableRows"):
                    cells = row.get("tableCells")
                    for cell in cells:
                        text += await self.read_strucutural_elements(cell.get("content"))
            elif "tableOfContents" in value:
                # The text in the TOC is also in a Structural Element.
                toc = value.get("tableOfContents")
                text += await self.read_strucutural_elements(toc.get("content"))
        return text


    async def save_doc(self):
        """Uses the Docs API to save the document to a txt file"""
        credentials = await self.get_credentials()
        http = credentials.authorize(Http())
        docs_service = googleapiclient.discovery.build(
            "docs", "v1", http=http, discoveryServiceUrl=self.DISCOVERY_DOC
        )
        doc = docs_service.documents().get(documentId=self.DOCUMENT_ID).execute()
        doc_content = doc.get("body").get("content")

        with open("school/APHS/announcements.txt", "w", encoding="utf-8") as file:
            #json.dump(await self.read_strucutural_elements(doc_content), file, indent=4)
            text = await self.read_strucutural_elements(doc_content)
            file.write(text)
            self.text = text


    async def organize_doc(self):
        """Organize the text into a json file (announcements.json)"""
        edited_text = self.text.replace("APHS DAILY ANNOUNCEMENTS\n\n\n\n", "")
        
        edited_text = re.split(r"((?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY) (?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER) \b(?:[1-9]|[12][0-9]|3[01])\b (?:2021|2022))", edited_text)

        del edited_text[0]

        organized_doc = convert(edited_text)

        for item in organized_doc.keys():
            split_a = organized_doc.get(item).split("\n\n")
            del split_a[0]
            del split_a[-1]

            new_a_list = []

            for item_a in split_a:
                new_a_list.append(item_a.replace("\n", ""))
            
            organized_doc[item] = new_a_list

        with open("school/APHS/announcements.json", "w", encoding="utf-8") as file:
            json.dump(organized_doc, file, indent=4)


class AnnouncementsJson:
    """Read from the announcements json document"""
    async def get_latest_day(self) -> list:
        """Get latest days list of announcements"""
        with open("school/APHS/announcements.json", "r", encoding="utf-8") as file:
            latest_json = json.loads(file.read())

        first_key = latest_json.keys()

        a_list = latest_json.get(list(first_key)[0])

        return a_list

    async def get_day(self, day:int) -> list:
        """Get a certain days announcement"""
        with open("school/APHS/announcements.json", "r", encoding="utf-8") as file:
            latest_json = json.loads(file.read())
        # Removing one from the index value
        day -= 1
        keys = list(latest_json.keys)
        return keys[day]

    
    async def get_all(self) -> dict:
        """Get all announcements possible"""
        pass


class WOSSAnnounce:
    """
    Woss Announcements
    """


class School(commands.Cog):
    """School cog"""
    def __init__(self, bot):
        self.bot = bot
        self.adoc = AnnouncementsDoc()
        self.ajson = AnnouncementsJson()
        self.update_announcements.start()

    def cog_unload(self):
        self.update_announcements.cancel()

    @tasks.loop(time=datetime.time(hour=13, minute=30))
    async def update_announcements(self):
        """Update our announcements documents every day at 8:30 est minutes"""
        await self.adoc.save_doc()
        await self.adoc.organize_doc()


    @commands.Cog.listener()
    async def on_ready(self):
        """On ready save the doc to our text file"""
        print("Saving Doc")
        await self.adoc.save_doc()
        print("Doc saved to school/APHS/announcements.txt")
        await self.adoc.organize_doc()
        print("Json saved to school/APHS/announcements.json")

    @commands.group()
    async def aphs(self, ctx):
        """Show todays announcements"""
        if not ctx.invoked_subcommand:
            a_list = await self.ajson.get_latest_day()

            a_formatted = ""

            for announcement in a_list:
                announcements = f"""{a_formatted}\n+ {announcement}"""

            embed = discord.Embed(
                title=f"Todays Announcements",
                description=f"""```diff
{announcements}
```""",
                timestamp=datetime.datetime.utcnow(),
                color=ctx.author.color
            )
            await ctx.send(embed=embed)

    @aphs.command()
    @commands.cooldown(1.0, 10.0, commands.BucketType.channel)
    async def raw(self, ctx):
        """Get the raw files"""
        await ctx.send(file=discord.File('school/APHS/announcements.json'))


def setup(bot):
    bot.add_cog(School(bot))