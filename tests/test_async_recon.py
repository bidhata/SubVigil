import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
from aioresponses import aioresponses


@pytest.mark.asyncio
async def test_check_subdomain_async_active(enumerator):
    """Active subdomain returns active=True with correct status and IP."""
    sub = "www.example.com"
    semaphore = asyncio.Semaphore(10)

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False):
        with aioresponses() as m:
            m.get('https://www.example.com', status=200,
                  headers={'Server': 'nginx', 'Content-Type': 'text/plain'},
                  body=b'hello')
            connector = aiohttp.TCPConnector(ssl=False)
            timeout_cfg = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout_cfg
            ) as session:
                info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['active'] is True
    assert info['status_code'] == 200
    assert info['ip'] == '1.2.3.4'
    assert info['server'] == 'nginx'


@pytest.mark.asyncio
async def test_check_subdomain_async_no_ip_returns_inactive(enumerator):
    """Subdomain that fails DNS resolution is returned as inactive."""
    sub = "nxdomain.example.com"
    semaphore = asyncio.Semaphore(10)

    with patch.object(enumerator, 'resolve_domain', return_value=None):
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['active'] is False
    assert info['ip'] is None


@pytest.mark.asyncio
async def test_check_subdomain_async_timeout_returns_inactive(enumerator):
    """Connection timeout marks subdomain as inactive."""
    sub = "timeout.example.com"
    semaphore = asyncio.Semaphore(10)

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False):
        with aioresponses() as m:
            m.get('https://timeout.example.com', exception=asyncio.TimeoutError())
            m.get('http://timeout.example.com', exception=asyncio.TimeoutError())
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['active'] is False
    assert info['ip'] == '1.2.3.4'


@pytest.mark.asyncio
async def test_check_subdomain_async_ssh_detected(enumerator):
    """Open port 22 is detected and sets ssh_open=True."""
    sub = "ssh.example.com"
    semaphore = asyncio.Semaphore(10)

    async def mock_open_connection(host, port):
        reader = MagicMock()
        writer = MagicMock()                           # close() is sync on StreamWriter
        writer.wait_closed = AsyncMock(return_value=None)
        return reader, writer

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False), \
         patch('asyncio.open_connection', side_effect=mock_open_connection):
        with aioresponses() as m:
            m.get('https://ssh.example.com', status=200,
                  headers={'Content-Type': 'text/plain'}, body=b'ok')
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                info = await enumerator._check_subdomain_async(sub, session, semaphore)

    assert info['ssh_open'] is True


def test_active_reconnaissance_uses_asyncio_run(enumerator):
    """active_reconnaissance must call asyncio.run (not ThreadPoolExecutor)."""
    import inspect
    src = inspect.getsource(enumerator.__class__.active_reconnaissance)
    assert 'asyncio.run(' in src, "active_reconnaissance must use asyncio.run"


def test_info_lock_exists_on_enumerator(enumerator):
    """SubdomainEnumerator must have a _info_lock threading.Lock attribute."""
    import threading
    assert hasattr(enumerator, '_info_lock'), "_info_lock not found on enumerator"
    assert isinstance(enumerator._info_lock, type(threading.Lock())), \
        "_info_lock must be a threading.Lock"


def test_port_scan_populates_ports(enumerator):
    """Open ports appear in info['ports'] after async recon."""
    enumerator.subdomains = {"test.example.com"}
    enumerator.fast_mode = False
    enumerator.scan_ports = [80, 443]

    async def fake_open_connection(host, port, **kw):
        reader = MagicMock()
        writer = MagicMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        return reader, writer

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False), \
         patch("asyncio.open_connection", side_effect=fake_open_connection), \
         patch("aiohttp.ClientSession") as mock_cs:
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)
        mock_response.status = 200
        mock_response.headers = {"Server": "nginx", "Content-Type": "text/plain"}
        mock_session.get.return_value = mock_response
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=False)
        asyncio.run(enumerator._async_active_recon())

    info = enumerator.subdomain_info.get("test.example.com", {})
    assert sorted(info.get("ports", [])) == [80, 443]


def test_ssh_detected_via_port_scan(enumerator):
    """Port 22 being open sets ssh_open=True."""
    enumerator.subdomains = {"test.example.com"}
    enumerator.fast_mode = False
    enumerator.scan_ports = [22]

    async def fake_open_connection(host, port, **kw):
        reader = MagicMock()
        writer = MagicMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        return reader, writer

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch.object(enumerator, 'check_subdomain_takeover', return_value=False), \
         patch("asyncio.open_connection", side_effect=fake_open_connection), \
         patch("aiohttp.ClientSession") as mock_cs:
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get.side_effect = Exception("no HTTP")
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=False)
        asyncio.run(enumerator._async_active_recon())

    info = enumerator.subdomain_info.get("test.example.com", {})
    assert info.get("ssh_open") is True
    assert 22 in info.get("ports", [])


def test_fast_mode_skips_port_scan(enumerator):
    """In fast_mode, no port connections are attempted."""
    enumerator.subdomains = {"test.example.com"}
    enumerator.fast_mode = True
    enumerator.scan_ports = [22, 80]

    connection_attempts = []

    async def spy_open_connection(host, port, **kw):
        connection_attempts.append(port)
        raise ConnectionRefusedError()

    with patch.object(enumerator, 'resolve_domain', return_value=['1.2.3.4']), \
         patch("asyncio.open_connection", side_effect=spy_open_connection), \
         patch("aiohttp.ClientSession") as mock_cs:
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get.side_effect = Exception("no HTTP")
        mock_cs.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_cs.return_value.__aexit__ = AsyncMock(return_value=False)
        asyncio.run(enumerator._async_active_recon())

    assert connection_attempts == [], "fast_mode should skip all port connections"
