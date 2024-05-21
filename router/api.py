import base64
import binascii
import hashlib
import json

import bson
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from fastapi import Request, APIRouter
from fastapi.responses import ORJSONResponse
from hypercorn.config import Config
from hypercorn.logging import Logger
from pydantic import BaseModel
from model.base_model import CubeResponse
from server.database import key_collection

router = APIRouter(prefix="/v1")

_logger = Logger(Config())


@router.get("/", tags=["Encrypt"], response_class=ORJSONResponse)
async def get_ipn_list():
    await _logger.info("API service is running...")
    return ORJSONResponse({"respCode": 200,
            "resultMsg": "This is Encrypt/Decrypt API tools provided by UniCube JSC"})


@router.get("/md5", tags=["Encrypt"])
async def md5(request: Request) -> dict[str, str]:
    await _logger.info(f"md5 function is running ...")
    params = request.query_params
    message = params.get('message')

    if message:
        h = hashlib.md5(message.encode('utf-8'))
        return {'result': h.hexdigest()}
    else:
        return {'result': 'no message'}


@router.get("/sha1", tags=["Encrypt"])
async def sha1(request: Request) -> dict[str, str]:
    await _logger.info(f"sha1 function is running ...")
    params = request.query_params
    message = params['message']
    if message:
        h = hashlib.sha1(message.encode('utf-8'))
        return {'result': h.hexdigest()}
    else:
        return {'result': 'no message'}


@router.get("/rsa/getkey")
async def rsa_key():
    await _logger.info(f"RSA getkey function is running ...")
    # Gen RSA private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption())
    f = open('./private.txt', 'w')
    f.write(pem.decode('utf-8'))  # write ciphertext to file
    f.close()

    # Gen RSA public key
    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1
    )
    f = open('./public.txt', 'w')
    f.write(pem_public.decode('utf-8'))  # write ciphertext to file
    f.close()
    result = await key_collection.insert_one(
        {'public_key': pem_public.decode('utf-8'), 'private_key': pem.decode('utf-8')})
    print(f" {type(result.inserted_id)} - {result.inserted_id}")
    return {'result': {
        'pem_private_key': pem.decode('utf-8'),
        'pem_public_key': pem_public.decode('utf-8'),
        'key_id': str(result.inserted_id)
    }}


@router.get("/rsa/encrypt")
async def rsa_encrypt(request: Request):
    await _logger.info(f"RSA encrypt function is running ...")
    params = request.query_params
    message = str(params['message']).encode('utf-8')
    key_id = str(params['key_id'])
    if message and key_id:
        print(key_id)
        found_keys = await key_collection.find_one({'_id': bson.ObjectId(key_id)})
        print('found_key', found_keys)

        if found_keys:
            print('Found keys ... ')
            # print('public_key', str( found_keys['public_key']))
            public_key = serialization.load_pem_public_key(str(found_keys['public_key']).encode('utf-8'))
            encrypted = public_key.encrypt(message, padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))
            return {"result": encrypted.hex()}
        else:
            with open("public.txt", "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read()
                )
            encrypted = public_key.encrypt(message, padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))

            with open("private.txt", "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None)

            hex_string = encrypted.hex()
            print(hex_string)

            a = b''
            original_message = private_key.decrypt(a.fromhex(hex_string),
                                                   padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))
            print(original_message == message)

            return {"result": encrypted.hex()}
    else:
        return {"result": "Please ensure you provided the 'message' and 'key_id' parameters"}


class DecryptData(BaseModel):
    message: str
    key_id: str


@router.post("/rsa/decrypt")
async def rsa_decrypt(body: DecryptData):
    await _logger.info(f"RSA decrypt function is running ...")
    message = str(body.message) or False
    key_id = str(body.key_id) or False
    if message and key_id:
        message = binascii.unhexlify(str(body.message))
        print(key_id)
        found_keys = await key_collection.find_one({'_id': bson.ObjectId(key_id)})
        print('found_key', found_keys)
        if found_keys:
            private_key = serialization.load_pem_private_key(str(found_keys['private_key']).encode('utf-8'),
                                                             password=None)
            plaintext = private_key.decrypt(
                message,
                padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))
            return {"result": plaintext}
        else:
            with open("private.txt", "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )

            plaintext = private_key.decrypt(
                message,
                padding.OAEP(padding.MGF1(hashes.SHA256()), hashes.SHA256(), None))

            return {"result": plaintext}
    else:
        return {"result": "Please ensure you provided the 'message' and 'key_id' parameters"}


@router.post("/rsa/atom_decrypt")
async def rsa_atom_decrypt(data: DecryptData):
    await _logger.info(f"RSA ATOM decrypt function is running ...")
    # params = request.body()
    message = str(data.message) or ""
    key_id = str(data.key_id) or ""
    if message and key_id:
        # message = base64.b64decode(str(params['message']))
        print(key_id)
        found_keys = await key_collection.find_one({'_id': bson.ObjectId(key_id)})
        print('found_key', found_keys)
        print('message:', message)
        if found_keys:
            private_key = serialization.load_pem_private_key(str(found_keys['private_key']).encode('utf-8'),
                                                             password=None)
            print('message:', private_key)
            plaintext = private_key.decrypt(
                base64.b64decode(message),
                padding.PKCS1v15()

            )
            # plaintext = private_key.decrypt(
            #     message,
            #     padding.PKCS1v15())
            print('plaintext:', plaintext)
            return {"result": json.loads(plaintext)}
        else:
            with open("private.txt", "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )

            plaintext = private_key.decrypt(
                base64.b64decode(message),
                padding.PKCS1v15())

            return {"result for Atom provider": plaintext}
    else:
        return {"result": "Please ensure you provided the 'message' and 'key_id' parameters"}
