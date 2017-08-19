from iridescence import *

logger = quick_setup()

logger.debug("Testing logging modes")
logger.info("Auto-destruct mechanism started at {} seconds",
            1972.5)
logger.warning("You have ten seconds to self-destruct")
logger.error("Detonator connection timeout, retrying")


# Nest for a stack trace that actually has a stack
def auto_destruct():
    def send_msg():
        def get_confimation():
            def read_queue():
                raise RuntimeError("Queue empty")
            read_queue()
        try:
            get_confimation()
        except RuntimeError as e:
            raise IOError("Timeout") from e
    send_msg()

try:
    try:
        auto_destruct()
    except Exception as e:
        raise SystemError("Connection failed")
except Exception as e:
    logger.exception("Auto-destruct mechanism failed. "
                     "Nuke activated.")

logger.critical("YOU ARE GOING TO DIE!!!")
logger.info("Any way, back to reality...")
logger.info("Really long " * 20)
logger.info("Another really long " * 20)
logger.info("""Long msg
with paras""")
