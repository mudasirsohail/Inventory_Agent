import asyncio
from agents import Agent, RunConfig, Runner, set_tracing_disabled, OpenAIChatCompletionsModel
from agents import function_tool
from openai import AsyncOpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import pprint
load_dotenv()
MODEL_NAME: str = "gemini-2.0-flash"
API_KEY: str ="AIzaSyBmnk_HlBIVtRbpaC8TqnmuY8TRBeg4cig"
API_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"

set_tracing_disabled(disabled=True)

client: AsyncOpenAI = AsyncOpenAI(api_key=API_KEY, base_url=API_URL)
chat_model: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)
warehouse = {}
class Product(BaseModel):
    name: str
    qty: int

class ModifyProduct(BaseModel):
    name: str
    new_qty: int
def show_inventory():
    """Return a snapshot of current inventory."""
    return dict(warehouse)
@function_tool
def insert_item(product: Product):
    """Insert a product or increase its stock."""
    if product.name in warehouse:
        warehouse[product.name] += product.qty
    else:
        warehouse[product.name] = product.qty
    return {"message": "Item inserted/updated", "inventory": show_inventory()}


@function_tool
def delete_item(product: Product):
    """Delete a product or reduce its stock."""
    if product.name in warehouse:
        warehouse[product.name] -= product.qty
        if warehouse[product.name] <= 0:
            del warehouse[product.name]
        return {"message": "Item removed/adjusted", "inventory": show_inventory()}
    return {"message": "Item not found", "inventory": show_inventory()}


@function_tool
def change_item(product: ModifyProduct):
    """Change stock quantity of a product."""
    if product.name in warehouse:
        warehouse[product.name] = product.new_qty
        return {"message": "Item quantity changed", "inventory": show_inventory()}
    return {"message": "Item not found", "inventory": show_inventory()}
adder = Agent(
    name="Stock Adder",
    instructions="You handle adding products into stock.",
    tools=[insert_item]
)

remover = Agent(
    name="Stock Remover",
    instructions="You handle removing products from stock.",
    tools=[delete_item]
)

changer = Agent(
    name="Stock Updater",
    instructions="You handle changing quantities of products in stock.",
    tools=[change_item]
)
async def main():
    print("\n*** Insert Example ***")
    step1 = await Runner.run(
        adder,
        "Add 15 bananas",
        run_config=RunConfig(model=chat_model)
    )
    pprint.pprint(step1.final_output)

    print("\n*** Remove Example ***")
    step2 = await Runner.run(
        remover,
        "Remove 5 bananas",
        run_config=RunConfig(model=chat_model)
    )
    pprint.pprint(step2.final_output)

    print("\n*** Change Example ***")
    step3 = await Runner.run(
        changer,
        "Update bananas to 50",
        run_config=RunConfig(model=chat_model)
    )
    pprint.pprint(step3.final_output)

    print("\n*** Current Warehouse ***")
    pprint.pprint(warehouse)

def start():
    asyncio.run(main())

if __name__ == "__main__":
    start()
