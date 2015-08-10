from iridescence import *

logger = quick_setup()

logger.debug("Testing logging modes")
logger.info("Auto-destruct mechanism started at {} seconds",
            1972.5)
logger.warning("You have ten seconds to self-destruct")
logger.error("Detonator connection timeout, retrying")


# Nest for a stack trace that actually has a stack
def auto_destruct():
    raise RuntimeError("Lost connection to detonator")
try:
    auto_destruct()
except Exception as e:
    logger.exception("Auto-destruct mechanism failed. "
                     "Nuke activated.")

logger.critical("YOU ARE GOING TO DIE!!!")
logger.info("Any way, back to reality...")
