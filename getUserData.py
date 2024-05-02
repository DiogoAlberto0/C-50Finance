from helpers import lookup
from typing import TypedDict
from db import db

class typeHistory(TypedDict):
    id: int
    symbol: str
    shares: int
    day: int
    month: int
    year: int
    hour: int
    minute: int
    operation: str
    total_price: float
    user_id: int

class typePortifolioRegister(TypedDict):
   qtde: int 
   current_price: float 
   total_price: float

class User:
    def __init__(self, id) -> None:
        self.id = id
    
    def getCash(self) -> float:
        cash = db.execute(
            """
            SELECT cash FROM users WHERE id = ?
            """,
            self.id
        )
        return cash[0]["cash"]
    
    def getHistory(self) -> typeHistory:
        history = db.execute(
            """
            SELECT * FROM purchases WHERE user_id = ?
            ORDER BY year, month, day, hour, minute
            """,
            self.id
        )
        return history
        
    def getPortifolio(self) -> dict[str, typePortifolioRegister]:
        portifolio:dict[str, typePortifolioRegister] = {}
        history = self.getHistory()
        for transactions in history:
            if not transactions["symbol"] in portifolio:
                portifolio[transactions["symbol"]] = { 
                    "qtde": 0, 
                    "current_price": lookup(transactions["symbol"])["price"],
                    "total_price": 0,
                }

            currentAction = portifolio[transactions["symbol"]]
            if transactions["operation"] == "buy":
                currentAction["qtde"] += transactions["shares"]
                currentAction["total_price"] += transactions["shares"] * currentAction["current_price"]
            else:
                currentAction["qtde"] -= transactions["shares"]
                currentAction["total_price"] -= transactions["shares"] * currentAction["current_price"]
        
        keysToRemove = []
        for key, value in portifolio.items():
            if value["qtde"] < 1:
                keysToRemove.append(key)
        for key in keysToRemove:
            del portifolio[key]
                
        return portifolio
    
    def getGeneralTotal(self) -> float:        
        portifolio = self.getPortifolio()
        general_total = self.getCash()
        for symbol, shares in portifolio.items():
            general_total += shares["total_price"]
        
        return general_total