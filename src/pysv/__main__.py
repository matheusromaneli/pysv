import logging
import os
import sys
from contextlib import suppress
from multiprocessing import Process
from pathlib import Path
from threading import Thread

try:
    from uvloop import new_event_loop
except ImportError:
    from asyncio import get_event_loop as new_event_loop

import pysv.c_package as c_pub
from pysv import publisher_async as async_pub
from pysv import subscriber_async as async_sub
from pysv.sv import SamplesSynchronized, SVConfig

logging.basicConfig(format="[%(levelname)7s] %(asctime)s | %(name)20s:%(lineno)4d > %(message)s")
logger = logging.getLogger("pysv")

interface = os.environ["PYSV_INTERFACE"]

loop = new_event_loop()

sv_config = SVConfig(
    # dst and src mac can be written with or without separators
    dst_mac="01:0c:cd:04:00:00", src_mac="0030a7228d5d",
    app_id="4000",  # appid should be a string with a hex number ranging from 4000 to 7FFF
    sv_id="4000",  # svid can be any string of 129 max len
    conf_rev=1,  # int
    smp_sync=SamplesSynchronized.GLOBAL,  # none, local or global
)

sv_config_b = SVConfig(
    # dst and src mac can be written with or without separators
    dst_mac="01:0c:cd:04:00:01", src_mac="0030a7228d5e",
    app_id="4001",  # appid should be a string with a hex number ranging from 4000 to 7FFF
    sv_id="4001",  # svid can be any string of 129 max len
    conf_rev=1,  # int
    smp_sync=SamplesSynchronized.GLOBAL,  # none, local or global
)

if "-ap" in sys.argv:
    try:
        csv_path = Path(sys.argv[2])
    except IndexError:
        csv_path = Path(os.environ["PYSV_CSV_FILE"])
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(async_pub.run(loop, interface, csv_path, sv_config))
elif "-as" in sys.argv:
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(async_sub.run(loop, interface))
elif "-debug" in sys.argv:
    logger.info("Starting c_pub...")
    c_pub.publisher_default(interface, Path(os.environ["PYSV_CSV_FILE"]), sv_config)
    logger.info("Done!")
elif "-thread" in sys.argv:
    sv_a =Thread(target=c_pub.publisher_default, args=(interface, Path(os.environ["PYSV_CSV_FILE"]), sv_config))
    sv_b =Thread(target=c_pub.publisher_default, args=(interface, Path(os.environ["PYSV_CSV_FILE"]), sv_config_b))

    sv_a.start()
    sv_b.start()

    sv_a.join()
    sv_b.join()

elif "-multiprocess" in sys.argv:
    p_sv_a = Process(target=c_pub.publisher_default, args=(interface, Path(os.environ["PYSV_CSV_FILE"]), sv_config))
    p_sv_b = Process(target=c_pub.publisher_default, args=(interface, Path(os.environ["PYSV_CSV_FILE"]), sv_config_b))
    p_sv_a.start()
    p_sv_b.start()

    p_sv_a.join()
    p_sv_b.join()

loop.close()
