import logging
import inngest

# Create an Inngest client

logger = logging.getLogger(__name__)

inngest_client = inngest.Inngest(
    app_id="social_share",
    logger=logger,
)