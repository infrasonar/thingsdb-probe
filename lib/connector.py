import asyncio
import time
from thingsdb.client import Client
from libprobe.exceptions import CheckException

_connections: dict[
    tuple[str, str, int],
    tuple[float, asyncio.Lock, Client]] = {}


async def _get_conn(token: str, host: str, port: int):
    key = (token, host, port)
    expire_ts, lock, conn = _connections.get(key, (0.0, asyncio.Lock(), None))
    if conn is None or (time.time() > expire_ts and not lock.locked()):
        if conn:
            try:
                conn.close()
                await conn.wait_closed()
            except Exception:
                pass

        conn = Client()
        await conn.connect(host, port)
        await conn.authenticate(token)
        _connections[key] = time.time() + 900.0, asyncio.Lock(), conn

    return conn, lock


async def get_conn(local_config: dict,
                   asset_name: str) -> tuple[Client, asyncio.Lock]:
    host = local_config.get('host') or asset_name
    port = local_config.get('port', 9200)
    token = local_config.get('token')

    if not isinstance(host, str) or not host:
        raise CheckException('missing or invalid `host` in asset config')
    if not isinstance(port, int) or 0 > port > 65531:
        raise CheckException('invalid `port` in asset config')
    if not isinstance(token, str) or not token:
        raise CheckException('missing or invalid `token` in asset config')

    conn, lock = await _get_conn(token, host, port)
    return conn, lock


async def close_all():
    for expire_ts, lock, conn in _connections.values():
        async with lock:
            try:
                await conn.close_and_wait()
            except Exception:
                pass
