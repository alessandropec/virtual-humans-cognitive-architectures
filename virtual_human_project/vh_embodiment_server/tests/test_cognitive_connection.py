"""Local process ownership, disabled connection and occupied ports."""
import asyncio
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from cognitive_connection import CognitiveConnection
from schemas import Settings
from fastapi import HTTPException


async def main():
    settings = Settings(agent_autostart=False, agent_enabled=False)
    connection = CognitiveConnection(lambda: settings)
    assert not await connection.check()
    try:
        await connection.start()
    except HTTPException as error:
        assert error.status_code == 409
    else:
        raise AssertionError('Disabled connection launched a process')
    settings.agent_enabled = True
    async def disconnected():
        return False
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / 'server.py'
        script.write_text('')
        settings.agent_script = str(script)
        settings.agent_python = sys.executable
        process = MagicMock()
        process.poll.return_value = None
        with patch.object(connection, 'check', disconnected), \
             patch('cognitive_connection.asyncio.open_connection', side_effect=OSError), \
             patch('cognitive_connection.subprocess.Popen', return_value=process) as launch:
            await connection.start()
            await connection.start()
            assert launch.call_count == 1
            assert launch.call_args.args[0][-1] == str(script)
            assert launch.call_args.args[0][0] == sys.executable
            await connection.stop()
            await connection.stop()
            process.terminate.assert_called_once()
        writer = MagicMock()
        async def occupied(*args):
            return None, writer
        async def closed():
            pass
        writer.wait_closed = closed
        with patch.object(connection, 'check', disconnected), \
             patch('cognitive_connection.asyncio.open_connection', occupied), \
             patch('cognitive_connection.subprocess.Popen') as launch:
            try:
                await connection.start()
            except HTTPException as error:
                assert error.status_code == 409 and 'occupied' in error.detail
            else:
                raise AssertionError('Occupied port allowed launch')
            launch.assert_not_called()
    print('PASS disabled connection, single launch, owned-process stop, occupied-port protection')


asyncio.run(main())
