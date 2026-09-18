import logging
import os
from collections.abc import Callable

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from documents.models import ExtractedShipmentData

from .exceptions import PortalFormError, PortalTimeoutError, PortalUnavailableError
from .selenium_client import create_chrome_driver

logger = logging.getLogger(__name__)


class PortalClient:
    def __init__(self, base_url: str | None = None, driver_factory: Callable = create_chrome_driver, timeout_seconds: int = 10) -> None:
        self.base_url = base_url or os.getenv("MOCK_PORTAL_URL", "http://localhost:8082")
        self.driver_factory = driver_factory
        self.timeout_seconds = timeout_seconds

    def create_order(self, extraction: ExtractedShipmentData) -> str:
        driver = None
        try:
            driver = self.driver_factory()
            wait = WebDriverWait(driver, self.timeout_seconds)
            driver.get(self.base_url)
            fields = {
                "customer": extraction.customer,
                "containerNumber": extraction.container_number,
                "origin": extraction.origin,
                "destination": extraction.destination,
                "weightKg": str(extraction.weight_kg),
                "deliveryDate": extraction.delivery_date.isoformat(),
            }
            for field_id, value in fields.items():
                element = wait.until(EC.visibility_of_element_located((By.ID, field_id)))
                element.clear()
                element.send_keys(value)
            wait.until(EC.element_to_be_clickable((By.ID, "submitButton"))).click()
            confirmation = wait.until(EC.visibility_of_element_located((By.ID, "confirmation")))
            if confirmation.get_attribute("data-success") != "true":
                raise PortalFormError("ERP portal rejected the order")
            reference = driver.find_element(By.ID, "erpReference").text.strip()
            if not reference:
                raise PortalFormError("ERP portal did not return a reference")
            return reference
        except PortalFormError:
            raise
        except TimeoutException as exc:
            raise PortalTimeoutError("Timed out waiting for the ERP portal") from exc
        except NoSuchElementException as exc:
            raise PortalFormError("ERP portal response is malformed") from exc
        except WebDriverException as exc:
            raise PortalUnavailableError("Unable to reach the ERP portal") from exc
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except WebDriverException:
                    logger.warning("Browser cleanup failed", exc_info=True)
