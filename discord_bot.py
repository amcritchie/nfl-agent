# Load environment variables FIRST, before any other imports
from dotenv import load_dotenv
load_dotenv()

import os
import discord
from discord.ext import commands
from tools import fetch_nfl_data
from prompts import SYSTEM_PROMPT
from llm import call_llm
import json

# Debug: Print environment variables
print(f"DEBUG - NFL_API_BASE: {os.getenv('NFL_API_BASE')}")
print(f"DEBUG - DISCORD_TOKEN: {os.getenv('DISCORD_TOKEN')[:20]}..." if os.getenv('DISCORD_TOKEN') else "DEBUG - DISCORD_TOKEN: None")
print(f"DEBUG - TARGET_CHANNEL_ID: {os.getenv('TARGET_CHANNEL_ID')}")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))  # Channel where bot should respond

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Target channel ID: {TARGET_CHANNEL_ID}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Only respond in the target channel
    if message.channel.id != TARGET_CHANNEL_ID:
        return

    # Check if message mentions the bot or uses command prefix
    if bot.user.mentioned_in(message) or message.content.startswith('!nfl'):
        # Extract the question (remove bot mention or command prefix)
        question = message.content.replace(f'<@{bot.user.id}>', '').replace('!nfl', '').strip()
        
        if not question:
            await message.channel.send("Please ask me a question about NFL Week 1! For example: 'Who is the Broncos starting LT?'")
            return

        # Show typing indicator
        async with message.channel.typing():
            try:
                # Process the question using your existing agent logic
                answer, sources = await process_nfl_question(question)
                
                # Format the response
                response = f"**Question:** {question}\n\n**Answer:** {answer}\n\n**Sources:** {', '.join(sources)}"
                
                # Split long responses if needed (Discord has 2000 character limit)
                if len(response) > 2000:
                    # Send answer first
                    answer_part = f"**Question:** {question}\n\n**Answer:** {answer}"
                    await message.channel.send(answer_part[:2000])
                    
                    # Send sources separately
                    sources_part = f"**Sources:** {', '.join(sources)}"
                    await message.channel.send(sources_part)
                else:
                    await message.channel.send(response)
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                await message.channel.send(error_msg)
                print(f"Error processing question: {e}")

    # Process commands
    await bot.process_commands(message)

async def process_nfl_question(question):
    """Process NFL questions using your existing agent logic"""
    messages = [
        {"role":"system","content": SYSTEM_PROMPT},
        {"role":"user","content": question}
    ]
    
    print(f"Processing Discord question: {question}")
    
    # Start a conversation loop for data gathering
    conversation_messages = messages.copy()
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        print(f"DEBUG - Iteration {iteration + 1}")
        
        # Get the next action from the LLM
        decision = call_llm(conversation_messages, tools_schema=True)
        print(f"DEBUG - LLM decision: {decision}")
        
        if "tool_call" in decision:
            tc = decision["tool_call"]
            if tc["name"] != "fetch_nfl_data":
                raise ValueError("Unknown tool requested")
            
            # Fetch the data
            tool_result = fetch_nfl_data(**tc["arguments"])
            print(f"DEBUG - Fetched data: {tool_result}")
            
            # Add the tool call and result to the conversation
            conversation_messages.append({
                "role": "assistant",
                "content": f"I'll fetch {tc['arguments']['kind']} data for you.",
                "tool_calls": [{
                    "id": f"call_{iteration}",
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"])
                    }
                }]
            })
            
            conversation_messages.append({
                "role": "tool",
                "tool_call_id": f"call_{iteration}",
                "content": json.dumps(tool_result)
            })
            
            iteration += 1
            
        elif "content" in decision:
            # LLM is ready to synthesize the final answer
            print(f"DEBUG - LLM ready to synthesize: {decision['content']}")
            
            # Ask for final synthesis
            final_messages = conversation_messages + [
                {"role": "user", "content": "Now synthesize a complete answer to the original question using all the data you've gathered. Be comprehensive and cite all sources."}
            ]
            
            synthesis_result = call_llm(final_messages, tools_schema=False)
            
            if "content" in synthesis_result:
                answer = synthesis_result["content"]
                # Extract all source URLs from the conversation
                sources = []
                for msg in conversation_messages:
                    if msg.get("role") == "tool":
                        try:
                            data = json.loads(msg["content"])
                            if "source_url" in data:
                                sources.append(data["source_url"])
                        except:
                            pass
                return answer, sources
            else:
                answer = f"DEBUG: Final synthesis failed. Raw result: {synthesis_result}"
                return answer, []
        
        else:
            # Unexpected response
            answer = f"DEBUG: Unexpected LLM response: {decision}"
            return answer, []
    
    # If we hit max iterations, synthesize what we have
    answer = f"DEBUG: Hit max iterations ({max_iterations}). Synthesizing with available data."
    return answer, []

@bot.command(name='nfl')
async def nfl_command(ctx, *, question):
    """Command to ask NFL questions: !nfl Who is the Broncos starting LT?"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return
    
    async with ctx.channel.typing():
        try:
            answer, sources = await process_nfl_question(question)
            response = f"**Question:** {question}\n\n**Answer:** {answer}\n\n**Sources:** {', '.join(sources)}"
            
            if len(response) > 2000:
                answer_part = f"**Question:** {question}\n\n**Answer:** {answer}"
                await ctx.send(answer_part[:2000])
                
                sources_part = f"**Sources:** {', '.join(sources)}"
                await ctx.send(sources_part)
            else:
                await ctx.send(response)
                
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            await ctx.send(error_msg)

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return
        
    help_text = """
**NFL Week 1 Agent - Discord Bot**

**How to use:**
1. **Mention the bot:** @YourBotName Who is the Broncos starting LT?
2. **Use command:** !nfl Who is the Broncos starting LT?
3. **Get help:** !help

**Example questions:**
- Who is the Broncos starting LT in Week 1?
- What are the Week 1 matchups?
- Compare the starting QBs for the Chiefs and Raiders
- Who are the key players for the Eagles this week?

The bot will automatically fetch relevant data and provide comprehensive answers!
"""
    await ctx.send(help_text)

def run_discord_bot():
    """Run the Discord bot"""
    if not DISCORD_TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables")
        return
    
    if TARGET_CHANNEL_ID == 0:
        print("ERROR: TARGET_CHANNEL_ID not found in environment variables")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Error running Discord bot: {e}")

if __name__ == "__main__":
    run_discord_bot()
