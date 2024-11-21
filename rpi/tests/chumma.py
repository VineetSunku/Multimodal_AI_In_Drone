# import sys
# print(1)
# sys.exit()
# print(2)
import asyncio
func_code = """
async def greet(name):
    print("sleeping")
    await asyncio.sleep(2)
    print(f"Hello, {name}!")
"""
exec(func_code)
asyncio.run(greet("Alice"))