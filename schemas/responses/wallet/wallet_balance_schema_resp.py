from pydantic import BaseModel

class WalletBalanceSchemaResp(BaseModel):
  balance: int

