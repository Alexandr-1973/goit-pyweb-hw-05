import asyncio
import json
import logging
import websockets
import names
from websockets.exceptions import ConnectionClosedOK
import aiofile
import aiopath
import obligatory_task

logging.basicConfig(level=logging.INFO)

class Server:
    clients = set()
    log_file = aiopath.AsyncPath("logs.txt")

    async def register(self, ws):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def log_to_file(self, message: str):
        async with aiofile.AIOFile(self.log_file, "a") as file:
            await file.write(message + "\n")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws):
        async for message in ws:
            if message == "exchange":
                exchange = await obligatory_task.request(f'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5')
                await self.send_to_clients(json.dumps(exchange))
                await self.log_to_file(f"Command {message} done")
            elif message.split(" ")[0]=="exchange" and len(message.split(" "))>1:
                exchange_list = await obligatory_task.main(message.split(" "))
                await self.send_to_clients(json.dumps(exchange_list))
                await self.log_to_file(f"Command {message} done")
            else:
                text_message=f"{ws.name}: {message}"
                await self.send_to_clients(json.dumps(text_message))



async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
