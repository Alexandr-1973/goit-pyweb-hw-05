import sys
from datetime import datetime, timedelta
import json
import aiohttp
import asyncio
import platform

class HttpError(Exception):
    pass

def need_list_output(responses_list, qty_input_params):
    need_list=[]
    for response_number in responses_list:
        all_currency_dict={}
        exchange_rate_list = response_number["exchangeRate"]
        for currency in exchange_rate_list:
            currency_dict = {currency["currency"]:{'sale' if currency.get("saleRate") else 'saleNB':
                            currency.get("saleRate") or currency.get("saleRateNB"),
                            'purchase' if currency.get("purchaseRate") else 'purchaseNB':
                            currency.get("purchaseRate") or currency.get("purchaseRateNB")}}
            all_currency_dict.update(currency_dict)
        if qty_input_params==2:
            all_currency_dict={key:value for key, value in all_currency_dict.items() if key=="EUR" or key=="USD"}
        need_list.append({response_number["date"]:all_currency_dict})
    return need_list

def verification_input(sys_list):
    text_error = (
        "Command formats:\n"
        "For exchange EUR and USD for n last days:\n"
        "python .\\obligatory_task.py [n<=10]\n"
        "For exchange all currencies for n last days:\n"
        "python .\\obligatory_task.py [n<=10] [all]"
    )
    if (len(sys_list) < 2 or len(sys_list) > 3 or not sys_list[1].isdigit()
        or int(sys_list[1]) > 10 or (len(sys_list) == 3 and sys_list[2] != "all")):
        print(text_error)
        return None
    return sys_list

async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def main(sys_argv_list):
    if not verification_input(sys_argv_list): return
    requests_list= [f'https://api.privatbank.ua/p24api/exchange_rates?date={(datetime.now() - timedelta(days=number_day)).strftime("%d.%m.%Y")}' for number_day in range(int(sys_argv_list[1]))]
    try:
        responses_list = await asyncio.gather(*(request(url) for url in requests_list))
        return need_list_output(responses_list, len(sys_argv_list))
    except HttpError as err:
        print(err)
        return None


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    results=asyncio.run(main(sys.argv))
    for result in [results]:
        print(json.dumps(result, indent=2, ensure_ascii=False))

