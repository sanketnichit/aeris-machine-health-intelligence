from threading import Event, Thread

from scripts.reliability_smoke import run
from src.api import make_server
from src.monitor_worker import run_worker


def test_concurrent_authenticated_workload(tmp_path):
    database=tmp_path/"telemetry.sqlite3"
    token="test-token-"+"x"*32
    server=make_server(port=0,database=database,token=token)
    server_thread=Thread(target=server.serve_forever,daemon=True)
    stop=Event()
    worker_thread=Thread(target=run_worker,args=(database,1,stop),daemon=True)
    server_thread.start()
    worker_thread.start()
    try:
        result=run(f"http://127.0.0.1:{server.server_port}",token)
        assert result["inserted"]==1
        assert result["duplicates"]==15
        assert result["periodic_freshness_detected"]
        assert result["successful_acknowledgements"]==1
    finally:
        stop.set()
        worker_thread.join(timeout=10)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=10)
    assert not worker_thread.is_alive()
    assert not server_thread.is_alive()
