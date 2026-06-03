class HailoRuntime:
    """Placeholder for host-side HailoRT integration."""

    def __init__(self) -> None:
        self.enabled = False

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "note": "Hailo integration will run on Raspberry Pi OS host, not inside Waydroid.",
        }


hailo_runtime = HailoRuntime()
