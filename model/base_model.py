from pydantic import BaseModel


class CubeResponse(BaseModel):
    respCode: int
    resultMsg: object
