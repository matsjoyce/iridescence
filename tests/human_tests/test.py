from iridescence import *

logger = quick_setup()

logger.debug("Testing logging modes")
logger.info("Auto-destruct mechanism started at {} seconds",
            1972.5)
logger.warning("You have ten seconds to self-destruct")
try:
    def auto_destruct():
        raise RuntimeError("Lost connection to detonator")
    auto_destruct()
except Exception as e:
    logger.error("Auto-destruct mechanism failed. "
                 "Nuke activated.", exc_info=e)
logger.critical("YOU ARE GOING TO DIE!!!")
logger.info("Any way, back to reality...")
