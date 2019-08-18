# -*- coding: utf-8 -*-
import logging
import os
import shutil
import uuid

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as rsa_padding
from cryptography.hazmat.primitives.ciphers import Cipher, modes, algorithms

from base.utils.zip import ZFile

logger = logging.getLogger(__name__)


def generate_key_file(private_key_path, public_key_path):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption())

    filename = private_key_path
    with open(filename, 'w') as f:
        os.chmod(filename, 0o600)
        f.write(pem)

    public_key = private_key.public_key()
    pem1 = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1)

    filename = public_key_path
    with open(filename, 'w') as f:
        os.chmod(filename, 0o600)
        f.write(pem1)


class AESCrypto(object):
    AES_CBC_IV = (chr(0xd2) + 'g') * 8

    @classmethod
    def encrypt(cls, data, key, mode='cbc'):
        func_name = '{}_encrypt'.format(mode)
        func = getattr(cls, func_name)
        return func(data, key)

    @classmethod
    def decrypt(cls, data, key, mode='cbc'):
        func_name = '{}_decrypt'.format(mode)
        func = getattr(cls, func_name)
        return func(data, key)

    @classmethod
    def cbc_encrypt(cls, data, AES_CBC_KEY):
        if not isinstance(data, bytes):
            data = data.encode()

        cipher = Cipher(algorithms.AES(AES_CBC_KEY),
                        modes.CBC(cls.AES_CBC_IV),
                        backend=default_backend())
        encryptor = cipher.encryptor()

        padded_data = encryptor.update(cls.pkcs7_padding(data))

        return padded_data

    @classmethod
    def cbc_decrypt(cls, data, AES_CBC_KEY):
        if not isinstance(data, bytes):
            data = data.encode()

        cipher = Cipher(algorithms.AES(AES_CBC_KEY),
                        modes.CBC(cls.AES_CBC_IV),
                        backend=default_backend())
        decryptor = cipher.decryptor()

        uppaded_data = cls.pkcs7_unpadding(decryptor.update(data))

        # uppaded_data = uppaded_data.decode()
        return uppaded_data

    @staticmethod
    def pkcs7_padding(data):
        if not isinstance(data, bytes):
            data = data.encode()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        padded_data = padder.update(data) + padder.finalize()

        return padded_data

    @staticmethod
    def pkcs7_unpadding(padded_data):
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data)

        uppadded_data = data + unpadder.finalize()
        return uppadded_data


def encrypt(src_file_name, dst_file_name, aes_key):
    data_file = open(src_file_name, 'rb')
    out_data_file = open(dst_file_name, 'wb')

    data = data_file.read()
    out_data = AESCrypto.encrypt(data, aes_key)
    out_data_file.write(out_data)

    out_data_file.close()
    data_file.close()

    return out_data


def decrypt(src_file_name, dst_file_name, aes_key):
    data_file = open(src_file_name, 'rb')
    out_data_file = open(dst_file_name, 'wb')

    data = data_file.read()
    out_data = AESCrypto.decrypt(data, aes_key)
    out_data_file.write(out_data)

    out_data_file.close()
    data_file.close()

    return out_data


def rsa_encrypt(public_key_file, data):
    key_file = open(public_key_file, 'rb')
    key_data = key_file.read()
    key_file.close()

    public_key = serialization.load_pem_public_key(
        key_data,
        backend=default_backend()
    )

    out_data = public_key.encrypt(
        data,
        rsa_padding.PKCS1v15()
    )
    return out_data


def rsa_decrypt(private_key_file, data):
    key_file = open(private_key_file, 'rb')
    key_data = key_file.read()
    key_file.close()

    private_key = serialization.load_pem_private_key(
        key_data,
        password=None,
        backend=default_backend()
    )

    out_data = private_key.decrypt(
        data,
        rsa_padding.PKCS1v15()
    )

    return out_data


def x_decrypt(src_file, out_file, private_key_file):
    extract_to_path = "/tmp/%s" % str(uuid.uuid4())
    try:
        ZFile(src_file).extract_to(extract_to_path)
    except Exception as e:
        logger.error("extract error msg[%s]", str(e))
        raise e

    aes_key_secret = ""
    aes_key_path = os.path.join(extract_to_path, "aes.key")
    with open(aes_key_path, 'rb') as f:
        aes_key_secret = f.read()

    if len(aes_key_secret) < 1:
        return False

    aes_key = rsa_decrypt(private_key_file, aes_key_secret)
    if len(aes_key) < 1:
        return False

    update_file = os.path.join(extract_to_path, "update.encrypt")

    decrypt(update_file, out_file, aes_key)

    shutil.rmtree(extract_to_path)


def x_encrypt(src_file, out_file, public_key_file):
    aes_key = os.urandom(32)

    # 对文件用aes加密
    aes_encrypt_out_file = "/tmp/update.encrypt"
    encrypt(src_file, aes_encrypt_out_file, aes_key)

    # 对aes密钥用rsa加密
    rsa_aes_key = rsa_encrypt(public_key_file, aes_key)

    aes_key = "/tmp/aes.key"
    with open(aes_key, 'wb') as f:
        f.write(rsa_aes_key)

    # 把两个文件用zip压缩
    encrypt_file_list = [aes_key, aes_encrypt_out_file]
    z = ZFile(out_file, 'w')
    for efile in encrypt_file_list:
        z.addfile(efile, efile[efile.rfind('/') + 1:])
    z.close()

    return aes_key
